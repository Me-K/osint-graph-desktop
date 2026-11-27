"""Native application entry point. Run with Python or the portable executable."""
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sqlite3
import sys

# Suppress Chromium background services; page requests are also intercepted below.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-background-networking --disable-component-update --disable-domain-reliability "
    "--disable-sync --no-pings"
)
if os.environ.get("OSINT_GRAPH_SOFTWARE_RENDERING") == "1":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " --disable-gpu"

from PySide6.QtCore import QObject, QLockFile, QSaveFile, QIODevice, QUrl, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor
from PySide6.QtWebEngineWidgets import QWebEngineView

from service import AppService
from settings import data_directory, resource_directory


class OfflineRequests(QWebEngineUrlRequestInterceptor):
    # Store the permitted resource directory and initialize the blocked-request counter.
    def __init__(self, web_root, parent=None):
        super().__init__(parent)
        self.web_root = web_root.resolve()
        self.blocked = 0

    # Allow embedded resources and bundled files while blocking remote or out-of-bundle requests.
    def interceptRequest(self, info):
        url = info.requestUrl()
        allowed = url.scheme() in {"qrc", "data", "blob", "about"}
        if url.scheme() == "file" and not url.host():
            allowed = Path(url.toLocalFile()).resolve().is_relative_to(self.web_root)
        if not allowed:
            self.blocked += 1
            info.block(True)


class OfflinePage(QWebEnginePage):
    # Bind the browser page to its profile and permitted application entry file.
    def __init__(self, profile, index_path, parent=None):
        super().__init__(profile, parent)
        self.index_path = index_path.resolve()

    # Restrict page navigation to the bundled entry file and internal about pages.
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        return (url.scheme() == "about" or
                (url.scheme() == "file" and not url.host()
                 and Path(url.toLocalFile()).resolve() == self.index_path))

    # Log JavaScript error locations without recording potentially private page content.
    def javaScriptConsoleMessage(self, level, message, line, source):
        # Do not log arbitrary page content: investigations may contain private notes.
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            logging.warning("Erreur JavaScript dans %s, ligne %s", Path(source).name, line)


class DesktopBridge(QObject):
    response = Signal(str)

    # Connect the Qt bridge to the local API service and initialize session tracking.
    def __init__(self, service, parent):
        super().__init__(parent)
        self.service = service
        self.authorization = ""

    # Decode a WebChannel request, track its authorization, and schedule asynchronous API processing.
    @Slot(str)
    def request(self, raw):
        request_id = None
        try:
            request = json.loads(raw)
            request_id = request["id"]
            if request.get("headers", {}).get("Authorization"):
                self.authorization = request["headers"]["Authorization"]
            future = self.service.submit(request)
            # Forward the finished request to the bridge with its original identifier and route.
            future.add_done_callback(lambda result: self._complete(request_id, request["path"], result))
        except Exception:
            self.response.emit(json.dumps({"id": request_id, "status": 400,
                                           "data": {"detail": "Requête invalide."}}))

    # Forward an API result to JavaScript and update the bridge's login or logout state.
    def _complete(self, request_id, path, future):
        try:
            result = future.result()
            if result["status"] < 400:
                if path == "/auth/login":
                    self.authorization = "Bearer " + result["data"]["token"]
                elif path == "/auth/logout":
                    self.authorization = ""
        except Exception:
            logging.exception("Échec d'une opération locale")
            result = {"status": 500, "data": {"detail": "Opération impossible. Consultez le journal local."}}
        self.response.emit(json.dumps({"id": request_id, **result}, ensure_ascii=False))

    # Validate JSON and save it atomically through a native file dialog, reporting cancellation or errors.
    @Slot(str, str, result=str)
    def saveJson(self, suggested_name, content):
        try:
            json.loads(content)
            filename, _ = QFileDialog.getSaveFileName(self.parent(), "Exporter le graphe",
                                                     Path(suggested_name).name, "Graphe JSON (*.json)")
            if not filename:
                return json.dumps({"saved": False})
            if not filename.lower().endswith(".json"):
                filename += ".json"
            file = QSaveFile(filename)
            data = content.encode("utf-8")
            if (not file.open(QIODevice.OpenModeFlag.WriteOnly) or file.write(data) != len(data)
                    or not file.commit()):
                raise OSError("Écriture du fichier impossible.")
            return json.dumps({"saved": True})
        except Exception as exc:
            return json.dumps({"error": str(exc)})


class MainWindow(QMainWindow):
    # Build the offline browser window, register the Qt bridge, and wire native application menus.
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setWindowTitle("OSINT Graph — Hors ligne")
        self.resize(1480, 960)
        self.setMinimumSize(1000, 680)
        self.view = QWebEngineView(self)
        web_root = resource_directory() / "web"
        self.profile = QWebEngineProfile(self.view)  # off-the-record: no browser profile on disk
        self.interceptor = OfflineRequests(web_root, self.profile)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        # Cancel browser downloads so exports go through the controlled native save dialog.
        self.profile.downloadRequested.connect(lambda download: download.cancel())
        self.page = OfflinePage(self.profile, web_root / "index.html", self.view)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.channel = QWebChannel(self.page)
        self.bridge = DesktopBridge(service, self)
        self.channel.registerObject("desktop", self.bridge)
        self.page.setWebChannel(self.channel)
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)
        self.statusBar().showMessage("Hors ligne  •  Enregistrement automatique sur cet ordinateur")
        menu = self.menuBar().addMenu("Fichier")
        backup = QAction("Sauvegarder toute la base…", self)
        backup.triggered.connect(self.backup_database)
        menu.addAction(backup)
        location = QAction("Emplacement des données…", self)
        # Show the location of the local SQLite database from the File menu.
        location.triggered.connect(lambda: QMessageBox.information(
            self, "Données locales", str(data_directory() / "osint-graph.sqlite3")))
        menu.addAction(location)
        menu.addSeparator()
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        help_menu = self.menuBar().addMenu("Aide")
        about = QAction("À propos", self)
        # Show the application version, license summary, and migration information from the Help menu.
        about.triggered.connect(lambda: QMessageBox.information(self, "OSINT Graph Desktop 1.0.1",
            "Application locale : Python, Qt, SQLite, React et Cytoscape.\n"
            "Importez vos anciens graphes avec les exports JSON de la version web.\n"
            "Les comptes de cette installation sont indépendants de ceux de la version web.\n\n"
            "Licence : utilisation, modification et redistribution gratuites ; vente interdite.\n"
            "Voir LICENSE pour les conditions et THIRD_PARTY.md pour les composants tiers."))
        help_menu.addAction(about)
        self.view.loadFinished.connect(self._loaded)
        self.view.load(QUrl.fromLocalFile(str(web_root / "index.html")))

    # Display a native error dialog when the bundled interface cannot be loaded.
    def _loaded(self, success):
        if not success:
            QMessageBox.critical(self, "Chargement impossible", "Les fichiers de l'interface sont absents ou illisibles.")

    # Verify full-backup permissions and atomically save a consistent SQLite snapshot to a chosen file.
    def backup_database(self):
        try:
            access = self.service.submit({"method": "GET", "path": "/desktop/backup-access",
                "headers": {"Authorization": self.bridge.authorization}}).result(timeout=15)
            if access["status"] != 200:
                QMessageBox.warning(self, "Sauvegarde", access["data"]["detail"])
                return
        except Exception:
            QMessageBox.warning(self, "Sauvegarde", "Impossible de vérifier les droits de la session.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Sauvegarder tous les comptes et graphes",
                                                 "osint-graph-sauvegarde.sqlite3", "Base SQLite (*.sqlite3)")
        if not filename:
            return
        original = data_directory() / "osint-graph.sqlite3"
        destination = Path(filename).resolve()
        if destination == original.resolve():
            QMessageBox.warning(self, "Sauvegarde", "Choisissez un autre fichier que la base en cours d'utilisation.")
            return
        import uuid
        temporary = destination.with_name(destination.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            # SQLite's backup API includes committed WAL changes, unlike a file copy.
            from contextlib import closing
            with closing(sqlite3.connect(original)) as source, closing(sqlite3.connect(temporary)) as target:
                source.backup(target)
            temporary.replace(destination)
            self.statusBar().showMessage("Sauvegarde complète enregistrée.", 8000)
        except Exception as exc:
            QMessageBox.critical(self, "Échec de la sauvegarde", str(exc))
        finally:
            temporary.unlink(missing_ok=True)


# Initialize Qt and logging, enforce one instance per data directory, and manage application startup and shutdown.
def main():
    application = QApplication(sys.argv)
    application.setApplicationName("OSINT Graph")
    application.setOrganizationName("OSINTGraph")
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.WARNING, handlers=[RotatingFileHandler(
        directory / "desktop.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")])
    lock = QLockFile(str(directory / "desktop.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "OSINT Graph", "Une instance utilise déjà ce dossier de données.")
        return 1
    if not (resource_directory() / "web/index.html").is_file():
        QMessageBox.critical(None, "Interface manquante", "Compilez l'interface avec build.ps1 ou utilisez le dossier portable complet.")
        return 1
    service = None
    try:
        service = AppService()
        window = MainWindow(service)
        window.show()
        return application.exec()
    except Exception as exc:
        logging.exception("Démarrage impossible")
        QMessageBox.critical(None, "Démarrage impossible", str(exc))
        return 1
    finally:
        if service:
            service.close()
        lock.unlock()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from self_check import run
        raise SystemExit(run())
    if "--smoke-test" in sys.argv:
        from smoke_check import run
        raise SystemExit(run())
    raise SystemExit(main())
