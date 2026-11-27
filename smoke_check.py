"""Exercise the real packaged Qt/React UI using disposable data, off screen."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
from unittest.mock import patch


# Exercise the desktop interface with isolated data and record UI, offline-access, export, and backup checks.
def run():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["OSINT_GRAPH_SOFTWARE_RENDERING"] = "1"
    from PySide6.QtCore import QEventLoop, QTimer, QUrl
    from PySide6.QtWidgets import QApplication, QFileDialog
    from main import MainWindow
    from service import AppService
    from self_check import report_path, PASSWORD

    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {"success": False, "checks": []}
    application = QApplication.instance() or QApplication([])

    # Process Qt events for a short interval so asynchronous UI work can finish during tests.
    def spin(milliseconds=80):
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()

    with tempfile.TemporaryDirectory(prefix="osint-ui-test-") as temporary:
        os.environ["OSINT_GRAPH_DATA_DIR"] = temporary
        service = AppService()
        window = MainWindow(service)
        window.show()

        # Execute JavaScript in the embedded page and wait for its callback result with a timeout.
        def js(script):
            result = []
            # Capture the JavaScript result so the waiting test helper can return it.
            window.page.runJavaScript(script, lambda value: result.append(value))
            deadline = time.monotonic() + 5
            while not result and time.monotonic() < deadline:
                spin()
            if not result:
                raise AssertionError("JavaScript ne répond pas.")
            return result[0]

        # Poll a JavaScript condition until it succeeds, recording the check or reporting a timeout.
        def wait_for(script, description, seconds=15):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if js(script):
                    report["checks"].append(description)
                    return
                spin(100)
            raise AssertionError(description + " : délai dépassé. Page : " + str(js("document.body.innerText"))[:1200])

        # Set an input through its native value setter and dispatch events that update React state.
        def set_input(selector, value):
            js("""(() => {
              const field = document.querySelector(%s);
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(field, %s);
              field.dispatchEvent(new Event('input', { bubbles: true }));
              field.dispatchEvent(new Event('change', { bubbles: true }));
            })()""" % (json.dumps(selector), json.dumps(value)))
            spin()

        # Click the first button whose text matches the requested label in the test page.
        def click_button(text):
            js("Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === %s).click()" % json.dumps(text))

        # Set a dropdown value and dispatch a change event for the React form.
        def set_select(selector, value):
            js("""(() => {
              const field = document.querySelector(%s);
              field.value = %s;
              field.dispatchEvent(new Event('change', {bubbles:true}));
            })()""" % (json.dumps(selector), json.dumps(value)))
            spin()

        try:
            wait_for("!!document.querySelector('[name=user_id]')", "Premier lancement : formulaire natif embarqué")
            set_input('[name=user_id]', 'admin')
            set_input('[name=password]', PASSWORD)
            set_input('[name=confirmation]', PASSWORD)
            js("document.querySelector('form').requestSubmit()")
            wait_for("document.body.innerText.includes('Ouvrir le graphe')", "Création du compte et ouverture de session via Qt")
            wait_for("document.querySelector('nav').innerText.includes('Gestion des comptes') && document.querySelector('nav').innerText.includes('Mon compte')", "Rubriques de compte présentes sur l'accueil administrateur")
            js("window.confirm = () => true")
            click_button('Mon compte')
            wait_for("!!document.querySelector('[data-testid=profile-form]')", "Gestion de son compte hors du studio")
            set_input('[data-testid=profile-form] input[name=display_name]', 'Administrateur local')
            click_button('Enregistrer mon profil')
            wait_for("document.body.innerText.includes('Votre profil a été mis à jour') && document.querySelector('header').innerText.includes('Administrateur local')", "Modification du profil et actualisation de l'accueil")
            admin_password = 'Nouveau-Compte-456!'
            set_input('[data-testid=password-form] input[name=current_password]', PASSWORD)
            set_input('[data-testid=password-form] input[name=new_password]', admin_password)
            set_input('[data-testid=password-form] input[name=confirmation]', admin_password)
            click_button('Changer mon mot de passe')
            wait_for("document.body.innerText.includes('Mot de passe modifié')", "Changement de son mot de passe depuis l'accueil")
            click_button('Gestion des comptes')
            wait_for("!!document.querySelector('[data-testid=account-create-form]')", "Gestion globale accessible sans ouvrir un graphe")
            set_input('[data-testid=account-create-form] input[name=user_id]', 'analyst')
            set_input('[data-testid=account-create-form] input[name=display_name]', 'Analyste test')
            set_input('[data-testid=account-create-form] input[name=password]', PASSWORD)
            set_input('[data-testid=account-create-form] input[name=confirmation]', PASSWORD)
            click_button('Créer le compte')
            wait_for("!!document.querySelector('[data-account-id=analyst]')", "Création d'un utilisateur indépendant des graphes")
            js("document.querySelector('[data-account-id=analyst]').click()")
            wait_for("!!document.querySelector('[data-testid=account-edit-form]')", "Édition d'un compte existant")
            set_select('[data-testid=account-edit-form] select[name=disabled]', 'true')
            click_button('Enregistrer ce compte')
            wait_for("document.querySelector('[data-account-id=analyst]').innerText.includes('Désactivé')", "Désactivation d'un compte depuis l'accueil")
            set_select('[data-testid=account-edit-form] select[name=disabled]', 'false')
            click_button('Enregistrer ce compte')
            wait_for("document.querySelector('[data-account-id=analyst]').innerText.includes('Actif')", "Réactivation d'un compte")
            analyst_password = 'Reset-Analyste-123!'
            set_input('[data-testid=account-reset-form] input[name=new_password]', analyst_password)
            set_input('[data-testid=account-reset-form] input[name=confirmation]', analyst_password)
            click_button('Réinitialiser le mot de passe')
            wait_for("document.body.innerText.includes('Mot de passe réinitialisé')", "Réinitialisation administrative du mot de passe")
            window.view.grab().save(str(path.with_name(path.stem + '-accounts.png')))
            click_button('Accès aux graphes')
            wait_for("!!document.querySelector('[data-testid=graph-access-form]')", "Gestion des accès déplacée hors du studio")
            set_input('[data-testid=graph-access-form] input[name=user_id]', 'analyst')
            click_button('Attribuer un accès')
            wait_for("document.querySelector('.access-list').innerText.includes('analyst')", "Attribution d'un accès à un compte existant")
            click_button('Mes graphes')
            window.view.grab().save(str(path.with_name(path.stem + '-home.png')))
            click_button('Se déconnecter')
            wait_for("!!document.querySelector('input[autocomplete=username]')", "Retour à la connexion")
            set_input('input[autocomplete=username]', 'analyst')
            set_input('input[autocomplete=current-password]', analyst_password)
            click_button('Se connecter')
            wait_for("!!document.querySelector('nav') && document.body.innerText.includes('Ouvrir le graphe')", "Connexion d'un utilisateur standard avec le mot de passe réinitialisé")
            assert not js("document.querySelector('nav').innerText.includes('Gestion des comptes')")
            assert js("document.querySelector('nav').innerText.includes('Mon compte')")
            report['checks'].append("Gestion globale invisible pour un utilisateur standard")
            click_button('Se déconnecter')
            wait_for("!!document.querySelector('input[autocomplete=username]')", "Déconnexion de l'utilisateur standard")
            set_input('input[autocomplete=username]', 'admin')
            set_input('input[autocomplete=current-password]', admin_password)
            click_button('Se connecter')
            wait_for("!!document.querySelector('nav') && document.body.innerText.includes('Ouvrir le graphe')", "Reconnexion de l'administrateur après changement du mot de passe")
            js("Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Ouvrir le graphe')).click()")
            wait_for("!!document.querySelector('input[placeholder=Alias]')", "Ouverture du studio")
            assert not js("!!document.querySelector('[data-testid=account-create-form]') || Array.from(document.querySelectorAll('h2')).some(h => h.textContent.includes('Administration'))")
            report['checks'].append("Aucune gestion de compte dans l'éditeur du graphe")
            for name in ["Alice locale", "Bob local"]:
                set_input('input[placeholder=Alias]', name)
                set_input('input[placeholder="Selectionner ou saisir une entreprise"]', 'Atelier local')
                click_button('Creer')
                wait_for("document.querySelector('input[placeholder=Alias]').value === ''", "Création : " + name)
            cy = "Array.from(document.querySelectorAll('div')).find(d => d._cyreg?.cy)?._cyreg.cy"
            wait_for(f"({cy})?.nodes().length === 2 && ({cy})?.edges().length === 1", "Cytoscape affiche deux personnes et le lien d'entreprise")
            spin(800)
            screenshot = window.view.grab()
            screenshot.save(str(path.with_suffix('.png')))
            pixels = screenshot.toImage()
            colors = {pixels.pixelColor(x, y).rgba() for x in range(0, pixels.width(), 20)
                      for y in range(0, pixels.height(), 20)}
            assert len(colors) > 10, "La fenêtre est blanche malgré le chargement de la page."
            report["checks"].append("Rendu visible vérifié sur la capture de la fenêtre")

            exported = Path(temporary) / "export.json"
            with patch.object(QFileDialog, "getSaveFileName", return_value=(str(exported), "")):
                click_button('Exporter JSON')
                wait_for("document.body.innerText.includes('Export JSON enregistré')", "Export avec dialogue natif et écriture disque")
            snapshot = json.loads(exported.read_text(encoding="utf-8"))
            assert len(snapshot["persons"]) == 2 and len(snapshot["relations"]) == 1

            # Use a real File object, so the production File.text() import path is exercised.
            js("""(() => {
                window.confirm = () => true;
                const transfer = new DataTransfer();
                transfer.items.add(new File([%s], 'export.json', {type:'application/json'}));
                const input = document.querySelector('input[type=file]');
                input.files = transfer.files;
                input.dispatchEvent(new Event('change', {bubbles:true}));
            })()""" % json.dumps(exported.read_text(encoding="utf-8")))
            wait_for("document.body.innerText.includes('Import termine')", "Réimport du format JSON existant dans l'interface")
            wait_for(f"({cy})?.nodes().length === 2", "Graphe visible après import")

            js("fetch('https://example.com/offline-probe').then(() => window.__offline=false).catch(() => window.__offline=true)")
            wait_for("window.__offline === true", "Les requêtes réseau sont bloquées par la politique de contenu")

            class Probe:
                # Create a minimal request object for testing the browser's offline interceptor.
                def __init__(self, url):
                    self.url, self.blocked = QUrl(url), False
                # Expose the simulated request URL using the interface expected by the interceptor.
                def requestUrl(self):
                    return self.url
                # Record whether the interceptor blocks the simulated request.
                def block(self, value):
                    self.blocked = value
            for url in ["https://example.com/", "http://127.0.0.1:8000/", "file://server/share/file", "file:///C:/Windows/win.ini"]:
                probe = Probe(url)
                window.interceptor.interceptRequest(probe)
                assert probe.blocked, url
            report["checks"].append("Interception des URL distantes, loopback, UNC et fichiers hors interface")
            backup = Path(temporary) / "backup.sqlite3"
            with patch.object(QFileDialog, "getSaveFileName", return_value=(str(backup), "")):
                window.backup_database()
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(backup)) as connection:
                assert connection.execute("SELECT count(*) FROM persons").fetchone()[0] == 2
                assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            report["checks"].append("Sauvegarde SQLite complète et intègre")
            report["success"] = True
        except Exception:
            report["error"] = traceback.format_exc()
            window.view.grab().save(str(path.with_suffix('.png')))
        finally:
            service.close()
            window.close()
            # Destroy page before profile and before temporary directory cleanup.
            import shiboken6
            shiboken6.delete(window.page)
            shiboken6.delete(window)
            spin()
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if sys.stdout:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["success"] else 1
