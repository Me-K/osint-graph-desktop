"""Integration checks, runnable in the source tree and in the portable build."""
from datetime import date, timedelta
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

from service import AppService
from storage import GraphStore

PASSWORD = "Local-Test-123!"


class LocalApplicationTests(unittest.TestCase):
    # Start each integration test with an isolated database, blocked network helpers, and an authenticated administrator.
    def setUp(self):
        import backend
        self.backend = backend
        self.temporary = tempfile.TemporaryDirectory(prefix="osint-desktop-test-")
        self.db_path = Path(self.temporary.name) / "test.sqlite3"
        backend.SECURITY_DB_PATH = self.db_path
        backend.store = GraphStore(self.db_path)
        self.no_dns = patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS interdit"))
        self.no_connection = patch.object(socket, "create_connection", side_effect=AssertionError("Réseau interdit"))
        self.no_dns.start()
        self.no_connection.start()
        self.service = AppService()
        self.token = None
        self.graph_id = backend.DEFAULT_GRAPH_ID
        self.call("POST", "/desktop/setup", {"user_id": "admin", "password": PASSWORD}, graph=False)
        self.token = self.call("POST", "/auth/login", {"user_id": "admin", "password": PASSWORD}, graph=False)["token"]

    # Stop the local service, restore patched network helpers, and remove the temporary test data.
    def tearDown(self):
        self.service.close()
        self.no_dns.stop()
        self.no_connection.stop()
        self.temporary.cleanup()

    # Send an authenticated in-process API request, assert its status, and return its response data.
    def call(self, method, path, data=None, expected=200, graph=True, token=None):
        result = self.service.submit({
            "method": method, "path": path, "data": data,
            "params": {"graph_id": self.graph_id} if graph else {},
            "headers": {"Authorization": f"Bearer {token or self.token}"} if token or self.token else {},
        }).result(timeout=15)
        self.assertEqual(result["status"], expected, result)
        return result["data"]

    # Create a test person in the default graph and return the new identifier.
    def person(self, alias, **extra):
        return self.call("POST", "/persons", {"alias": alias, **extra})["id"]

    # Fetch a JSON snapshot of the test graph for assertions and round-trip imports.
    def export(self):
        return self.call("GET", "/graph/export")

    # Create and sign in a test account after assigning its requested graph role.
    def grant(self, user_id, role):
        self.call("POST", "/admin/accounts", {"user_id": user_id, "password": PASSWORD})
        self.call("POST", f"/graphs/{self.graph_id}/permissions",
                  {"user_id": user_id, "role": role})
        return self.call("POST", "/auth/login", {"user_id": user_id, "password": PASSWORD})["token"]

    # Verify setup cannot repeat, the signed-in identity is returned, and invalid session tokens are rejected.
    def test_first_run_and_login(self):
        self.assertFalse(self.call("GET", "/desktop/status")["setup_required"])
        self.call("POST", "/desktop/setup", {"user_id": "other", "password": PASSWORD}, expected=409)
        self.assertEqual(self.call("GET", "/auth/me")["id"], "admin")
        self.call("GET", "/persons", expected=401, token="invalid")

    # Verify person creation, updates, deletion, date-derived age, and automatic company relationships.
    def test_crud_dates_alias_and_company_links(self):
        first = self.person("Élodie", entreprise="Atelier", date_naissance="1990-01-01", description="Notes éèà")
        second = self.person("Alice", entreprise="Atelier")
        self.call("POST", "/persons", {"alias": "Alice"}, expected=409)
        edges = self.call("GET", "/graph")["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["company"], "Atelier")
        details = self.call("GET", f"/persons/{first}")
        self.assertEqual(details["age"], date.today().year - 1990)
        self.call("PUT", f"/persons/{second}", {"alias": "Alice", "entreprise": "Autre"})
        self.assertEqual(self.call("GET", "/graph")["edges"], [])
        self.assertEqual(self.call("GET", "/companies"), ["Atelier", "Autre"])
        self.call("POST", "/relations", {"from_id": first, "to_id": second, "label": "CONNAIT"})
        self.call("DELETE", f"/persons/{first}")
        self.assertEqual(self.call("GET", "/graph")["edges"], [])
        self.call("GET", f"/persons/{first}", expected=404)

    # Verify invalid dates and incomplete identity data are rejected, and a full name can supply the alias.
    def test_invalid_dates_and_alias(self):
        future = (date.today() + timedelta(days=500)).isoformat()
        cases = [{"nom": "Nom seul"}, {"alias": "a", "date_naissance": "not-a-date"},
                 {"alias": "a", "date_naissance": "2000-01-01", "date_mort": "1999-01-01"},
                 {"alias": "a", "date_naissance": future, "date_mort": future}]
        for data in cases:
            with self.subTest(data=data):
                self.call("POST", "/persons", data, expected=422)
        node = self.call("POST", "/persons", {"nom": "Dupont", "prenom": "Alice"})
        self.assertEqual(node["label"], "Dupont Alice")

    # Verify repeated relationships are deduplicated and invalid endpoints or types are rejected.
    def test_relation_deduplication_and_validation(self):
        a, b = self.person("a"), self.person("b")
        data = {"from_id": a, "to_id": b, "label": "LIEN ` ; ' spécial"}
        first = self.call("POST", "/relations", data)
        self.assertEqual(first["id"], self.call("POST", "/relations", data)["id"])
        self.assertEqual(len(self.call("GET", "/graph")["edges"]), 1)
        self.call("POST", "/relations", {**data, "to_id": a}, expected=422)
        self.call("POST", "/relations", {**data, "to_id": "missing"}, expected=422)

    # Verify read and edit roles are enforced and revoked access takes effect immediately.
    def test_viewer_editor_and_permission_revocation(self):
        viewer = self.grant("viewer", "viewer")
        editor = self.grant("editor", "editor")
        self.call("GET", "/graph", token=viewer)
        self.call("GET", "/graph/export", token=viewer)
        self.call("POST", "/persons", {"alias": "denied"}, token=viewer, expected=403)
        self.call("POST", "/graph/import", {"data": {"persons": [], "relations": []}}, token=viewer, expected=403)
        self.call("GET", f"/graphs/{self.graph_id}/permissions", token=viewer, expected=403)
        self.call("POST", "/persons", {"alias": "allowed"}, token=editor)
        self.call("GET", f"/graphs/{self.graph_id}/permissions", token=editor, expected=403)
        self.call("DELETE", f"/graphs/{self.graph_id}/permissions/viewer")
        self.call("GET", "/graph", token=viewer, expected=404)

    # Verify every graph-permission mutation protects the last graph administrator.
    def test_last_admin_cannot_be_removed_by_any_endpoint(self):
        path = f"/graphs/{self.graph_id}/permissions"
        self.call("DELETE", path + "/admin", expected=400)
        self.call("PUT", path + "/admin", {"role": "viewer"}, expected=400)
        self.call("POST", path, {"user_id": "admin", "role": "viewer"}, expected=400)

    # Verify graph isolation even when imported graphs reuse person identifiers.
    def test_graph_isolation_and_reused_import_ids(self):
        self.person("same-alias")
        snapshot = self.export()
        first_graph = self.graph_id
        viewer = self.grant("viewer", "viewer")
        self.graph_id = self.call("POST", "/graphs", {"name": "Deuxième"})["id"]
        self.call("GET", "/graph", token=viewer, expected=404)
        self.call("POST", "/graph/import", {"data": snapshot})
        imported_id = snapshot["persons"][0]["id"]
        self.call("PUT", f"/persons/{imported_id}", {"alias": "changed"})
        self.graph_id = first_graph
        self.assertEqual(self.export()["persons"][0]["alias"], "same-alias")

    # Verify snapshot round trips, legacy relationship fields, and custom relationship properties.
    def test_export_import_old_format_and_properties(self):
        snapshot = {"persons": [{"id": "legacy-a", "alias": "André", "entreprise": "ACME"},
                                {"id": "legacy-b", "alias": "B", "entreprise": "ACME"}],
                    "relations": [{"source": "legacy-a", "target": "legacy-b", "label": "AMI",
                                   "properties": {"id": "legacy-link", "source_note": "Archive 2020"}},
                                  {"source": "legacy-a", "target": "legacy-b", "label": "MEME_ENTREPRISE"}]}
        self.call("POST", "/graph/import", {"data": snapshot})
        exported = self.export()
        self.assertEqual(len(exported["relations"]), 2)
        self.assertEqual(exported["relations"][0]["properties"]["source_note"], "Archive 2020")
        self.call("POST", "/graph/import", {"data": exported})
        self.assertEqual(len(self.export()["persons"]), 2)

    # Verify a failed replacement import preserves the graph's original persons and relationships.
    def test_failed_replacement_rolls_back_everything(self):
        self.person("Original")
        before = self.export()
        broken = {"persons": [{"id": "a", "alias": "New"}],
                  "relations": [{"source": "a", "target": "missing", "label": "AMI"}]}
        self.call("POST", "/graph/import", {"data": broken}, expected=422)
        self.assertEqual(self.export(), before)
        duplicates = {"persons": [{"id": "a", "alias": "dup"}, {"id": "b", "alias": "dup"}], "relations": []}
        self.call("POST", "/graph/import", {"data": duplicates}, expected=409)
        self.assertEqual(self.export(), before)
        duplicate_ids = {"persons": [{"id": "a"}, {"id": "a"}], "relations": []}
        self.call("POST", "/graph/import", {"data": duplicate_ids}, expected=422)
        self.assertEqual(self.export(), before)

    # Verify merge imports retain existing records and empty replacement imports clear the graph.
    def test_merge_and_empty_replace(self):
        original = self.person("original", description="garder")
        self.call("POST", "/graph/import", {"replace_existing": False, "data": {
            "persons": [{"id": original, "alias": "modifié"}, {"id": "new", "alias": "nouveau"}], "relations": []}})
        self.assertEqual(len(self.export()["persons"]), 2)
        self.assertEqual(self.call("GET", f"/persons/{original}")["description"], "garder")
        self.call("POST", "/graph/import", {"data": {"persons": [], "relations": []}})
        self.assertEqual(self.call("GET", "/graph"), {"nodes": [], "edges": []})

    # Verify accounts and graph data remain available after restarting the local service.
    def test_restart_persists_data_and_accounts(self):
        self.person("Persistante")
        before = self.export()
        self.service.close()
        self.service = AppService()
        self.assertFalse(self.call("GET", "/desktop/status")["setup_required"])
        self.assertEqual(self.export(), before)

    # Verify repeated login failures lock an account and logout invalidates its session token.
    def test_login_lockout_and_logout(self):
        self.grant("locked", "viewer")
        for _ in range(self.backend.LOGIN_MAX_FAILURES):
            self.call("POST", "/auth/login", {"user_id": "locked", "password": "wrong"}, expected=401)
        self.call("POST", "/auth/login", {"user_id": "locked", "password": PASSWORD}, expected=429)
        self.call("POST", "/auth/logout", {})
        self.call("GET", "/auth/me", expected=401)

    # Verify the local service rejects remote URLs and does not expose web documentation endpoints.
    def test_no_remote_transport(self):
        self.call("GET", "https://example.com/", expected=400)
        self.call("GET", "//example.com/", expected=400)
        self.call("GET", "/docs", expected=404)
        self.call("GET", "/openapi.json", expected=404)

    # Verify full database backups require administrator access to every graph.
    def test_full_backup_requires_admin_on_every_graph(self):
        self.assertTrue(self.call("GET", "/desktop/backup-access")["allowed"])
        viewer = self.grant("viewer", "viewer")
        self.call("GET", "/desktop/backup-access", token=viewer, expected=403)
        self.call("POST", "/graphs", {"name": "Privé"}, token=viewer)
        self.call("GET", "/desktop/backup-access", expected=403)
        self.call("GET", "/desktop/backup-access", token="invalid", expected=401)

    # Verify profile edits, current-password checks, and revocation of other sessions after a password change.
    def test_profile_and_password_management(self):
        other_session = self.call("POST", "/auth/login", {"user_id": "admin", "password": PASSWORD})["token"]
        me = self.call("PUT", "/account/profile", {"display_name": "Administratrice locale"})
        self.assertEqual(me["display_name"], "Administratrice locale")
        self.assertTrue(me["is_admin"])
        self.call("PUT", "/account/profile", {"display_name": "x", "is_admin": False}, expected=422)
        self.call("POST", "/account/password", {"current_password": "wrong", "new_password": "Nouveau-Test-456!"}, expected=400)
        self.call("POST", "/account/password", {"current_password": PASSWORD, "new_password": "short"}, expected=422)
        self.call("POST", "/account/password", {"current_password": PASSWORD, "new_password": "Nouveau-Test-456!"})
        self.call("GET", "/auth/me")
        self.call("GET", "/auth/me", token=other_session, expected=401)
        self.call("POST", "/auth/login", {"user_id": "admin", "password": PASSWORD}, expected=401)
        self.call("POST", "/auth/login", {"user_id": "admin", "password": "Nouveau-Test-456!"})

    # Verify graph administration does not grant account administration and new accounts get no graph access automatically.
    def test_account_administration_independent_of_graphs(self):
        account = self.call("POST", "/admin/accounts", {"user_id": "independent", "password": PASSWORD})
        self.assertFalse(account["is_admin"])
        token = self.call("POST", "/auth/login", {"user_id": "independent", "password": PASSWORD})["token"]
        self.assertEqual(self.call("GET", "/graphs", token=token), [])
        graph = self.call("POST", "/graphs", {"name": "Son graphe"}, token=token)
        self.assertEqual(graph["role"], "admin")
        for method, endpoint, payload in [
            ("GET", "/admin/accounts", None),
            ("POST", "/admin/accounts", {"user_id": "intruder", "password": PASSWORD}),
            ("PUT", "/admin/accounts/admin", {"is_admin": False}),
            ("POST", "/admin/accounts/admin/password", {"new_password": PASSWORD}),
            ("POST", "/admin/accounts/admin/unlock", {}),
        ]:
            with self.subTest(endpoint=endpoint, method=method):
                self.call(method, endpoint, payload, token=token, expected=403)
        self.call("POST", f"/graphs/{graph['id']}/permissions", {"user_id": "new-user", "role": "viewer"}, token=token, expected=404)
        self.call("POST", f"/graphs/{graph['id']}/permissions", {"user_id": "admin", "role": "viewer", "password": PASSWORD}, token=token, expected=422)
        self.call("PUT", "/account/profile", {"is_admin": True}, token=token, expected=422)
        self.call("POST", "/admin/accounts", {"user_id": "independent", "password": PASSWORD}, expected=409)

    # Verify account status, password resets, unlocking, and administrator-role changes affect access correctly.
    def test_account_disable_reset_unlock_and_role_changes(self):
        token = self.grant("member", "viewer")
        self.call("PUT", "/admin/accounts/member", {"disabled": True, "display_name": "Membre"})
        self.call("GET", "/auth/me", token=token, expected=401)
        self.call("POST", "/auth/login", {"user_id": "member", "password": PASSWORD}, expected=401)
        self.call("PUT", "/admin/accounts/member", {"disabled": False, "is_admin": True})
        token = self.call("POST", "/auth/login", {"user_id": "member", "password": PASSWORD})["token"]
        self.call("GET", "/admin/accounts", token=token)
        self.call("PUT", "/admin/accounts/member", {"is_admin": False})
        self.call("GET", "/admin/accounts", token=token, expected=403)
        for _ in range(self.backend.LOGIN_MAX_FAILURES):
            self.call("POST", "/auth/login", {"user_id": "member", "password": "wrong"}, expected=401)
        self.assertTrue(next(item for item in self.call("GET", "/admin/accounts") if item["id"] == "member")["locked"])
        self.call("POST", "/admin/accounts/member/unlock", {})
        self.call("POST", "/auth/login", {"user_id": "member", "password": PASSWORD})
        self.call("POST", "/admin/accounts/member/password", {"new_password": "Reset-Local-123!"})
        self.call("GET", "/auth/me", token=token, expected=401)
        self.call("POST", "/auth/login", {"user_id": "member", "password": "Reset-Local-123!"})
        accounts = self.call("GET", "/admin/accounts")
        self.assertNotIn("password_hash", accounts[0])
        self.assertNotIn("password", accounts[0])

    # Verify account edits cannot remove the last active application administrator or orphan a graph.
    def test_last_account_admin_and_graph_admin_are_protected(self):
        self.call("PUT", "/admin/accounts/admin", {"is_admin": False}, expected=400)
        self.call("PUT", "/admin/accounts/admin", {"disabled": True}, expected=400)
        self.call("POST", "/admin/accounts/admin/password", {"new_password": PASSWORD}, expected=400)
        owner = self.grant("owner", "viewer")
        private = self.call("POST", "/graphs", {"name": "À conserver"}, token=owner)
        self.call("PUT", "/admin/accounts/owner", {"disabled": True}, expected=400)
        self.call("POST", f"/graphs/{private['id']}/permissions", {"user_id": "admin", "role": "admin"}, token=owner)
        self.call("PUT", "/admin/accounts/owner", {"disabled": True})
        self.assertEqual(self.call("GET", "/auth/me")["id"], "admin")

    # Verify the legacy migration promotes only the installation account and does not repeat promotion later.
    def test_existing_database_migration_only_promotes_installation_account(self):
        self.grant("another", "admin")
        self.person("À conserver")
        self.service.close()
        with self.backend.get_security_connection() as connection:
            connection.execute("ALTER TABLE users DROP COLUMN is_admin")
        self.service = AppService()
        accounts = {item["id"]: item for item in self.call("GET", "/admin/accounts")}
        self.assertTrue(accounts["admin"]["is_admin"])
        self.assertFalse(accounts["another"]["is_admin"])
        self.assertEqual(self.export()["persons"][0]["alias"], "À conserver")
        self.call("PUT", "/admin/accounts/another", {"is_admin": True})
        self.call("PUT", "/admin/accounts/admin", {"is_admin": False})
        self.service.close()
        self.service = AppService()
        self.assertFalse(self.call("GET", "/auth/me")["is_admin"])
        self.call("GET", "/admin/accounts", expected=403)


# Choose the integration-test report destination from command-line arguments or the default results folder.
def report_path():
    if "--report" in sys.argv:
        return Path(sys.argv[sys.argv.index("--report") + 1]).resolve()
    return Path.cwd() / "test-results/self-test.json"


# Run the backend integration suite, write its JSON report, and return a process exit status.
def run():
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LocalApplicationTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {"success": result.wasSuccessful(), "tests": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors), "output": stream.getvalue()}
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if sys.stdout:
        print(stream.getvalue())
        print(f"Rapport : {path}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run())
