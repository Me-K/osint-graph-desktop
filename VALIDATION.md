# Vérifications de la distribution Windows

Vérifié le 28 septembre 2026 sur Windows 11 x64, Python 3.13.1 et Node.js 25.2.0.

- Construction Vite réussie et ressources HTML/JS/CSS embarquées.
- 19 tests d'intégration réussis dans les sources **et dans OSINTGraph.exe**.
- Gestion du profil, changement de mot de passe, création et édition de compte,
  désactivation/réactivation et réinitialisation du mot de passe testés dans
  l'interface. Rubriques d'administration absentes pour un utilisateur standard.
- Migration d'une ancienne base, séparation des rôles, révocation des sessions
  et protection du dernier administrateur couvertes par les tests métier.
- Test de la vraie interface Qt réussi avec l'exécutable : création du premier
  compte, connexion, ouverture d'un graphe, création de deux personnes, lien
  automatique d'entreprise, présence des nœuds Cytoscape et rendu visible.
- Export par dialogue natif, réimport JSON et sauvegarde SQLite vérifiés.
- Blocage des requêtes HTTP/HTTPS, loopback, chemins UNC et fichiers hors de
  l'interface vérifié. Les tests métier interdisent DNS et connexions Python.
- Intégrité de la sauvegarde vérifiée avec `PRAGMA integrity_check`.

Rapports détaillés : `test-results/self-test.json`,
`test-results/exe-self-test.json`, `test-results/exe-ui.json`.
Capture du programme compilé : `test-results/exe-ui.png`.
Accueil : `test-results/exe-ui-home.png` ; comptes : `test-results/exe-ui-accounts.png`.

Les tests graphiques s'exécutent hors écran avec le rendu logiciel, sur des
données temporaires. Aucune donnée d'enquête réelle n'a été importée. La base
Neo4j de la version web n'a pas été consultée ou migrée automatiquement.
Le programme n'a pas été testé sur une deuxième machine ni sur Linux/macOS.
