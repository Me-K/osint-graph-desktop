# Composants embarqués

Le fichier [LICENSE](LICENSE) à la racine décrit les droits accordés sur le
code applicatif d'OSINT Graph Desktop. Sa restriction de vente ne remplace pas
les licences des composants tiers et ne restreint pas les droits que ces
licences accordent sur leurs composants respectifs.

Le dossier `licenses` (dans `_internal/licenses` dans la distribution portable)
contient les textes livrés par les dépendances installées et leurs versions.

- Python : https://www.python.org/psf/license/
- Qt / PySide6 / Shiboken : https://doc.qt.io/qtforpython-6/licenses.html
- Qt WebEngine / Chromium : https://doc.qt.io/qt-6/qtwebengine-licensing.html
- FastAPI, Starlette, Pydantic, HTTPX : notices dans `licenses`.
- React, React DOM, Scheduler et Cytoscape : notices dans `licenses`.

Qt est livré sous forme de bibliothèques dynamiques séparées dans `_internal/PySide6`.
Les sources correspondantes de Qt/PySide6 6.11.1 sont disponibles auprès de Qt :
https://download.qt.io/official_releases/qt/6.11/6.11.1/ et
https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.1-src/.
Les avis spécifiques aux composants Chromium sont référencés par Qt dans la
[liste des composants Qt WebEngine](https://doc.qt.io/qt-6/qtwebengine-licensing.html).
Leurs sources accompagnent Qt WebEngine. Les textes GPLv3 et LGPLv3 sont aussi
joints dans `licenses`.

Le code applicatif reprend l'interface et la logique métier de ce dépôt.
