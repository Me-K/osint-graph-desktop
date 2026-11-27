# Développement

[Retour au README](../README.md)

## Organisation des sources

| Fichier ou dossier | Rôle |
| --- | --- |
| `main.py` | Fenêtre Qt, chargement de l'interface, transport WebChannel, dialogues natifs et démarrage. |
| `service.py` | Exécution du service FastAPI dans le processus desktop. |
| `backend.py` | Modèles, routes, sessions, comptes, droits et règles de gestion. |
| `storage.py` | Connexions et transactions SQLite, schéma des personnes et relations. |
| `graph_operations.py` | Requêtes sur les graphes, liens d'entreprise et import/export. |
| `settings.py` | Résolution des dossiers de données et de ressources. |
| `ui/src/main.jsx` | Montage de l'interface, configuration du premier compte et chargement du studio. |
| `ui/src/App.jsx` | Connexion, gestion des graphes, formulaires et visualisation. |
| `ui/src/Home.jsx` et `ui/src/AccountPanels.jsx` | Bibliothèque et écrans des comptes et des droits. |
| `ui/src/desktopApi.js` | Client JavaScript du pont Qt et de l'export natif. |
| `ui/vite.config.js` | Compilation de l'interface dans `web/`. |
| `build.ps1` et `OSINTGraph.spec` | Construction et assemblage de la distribution Windows. |
| `self_check.py` et `smoke_check.py` | Tests fonctionnels et test de la fenêtre Qt. |

## Construire la distribution Windows

Sur le poste de préparation, utiliser Python 3.13 x64 et une version de
Node.js compatible avec Vite 7, par exemple Node.js 22 à partir de 22.12.
La préparation initiale nécessite l'accès aux dépendances Python et npm.
`requirements-lock.txt` et `ui/package-lock.json` fixent les versions.

Depuis la racine du dépôt :

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Le script prépare `.venv/`, compile l'interface, lance les tests
fonctionnels et collecte les notices. PyInstaller fabrique le dossier
`dist\OSINTGraph`, puis le script crée le ZIP Windows et son empreinte
SHA-256. Le dossier portable distribue les guides, la licence et les notices.
[Composants tiers](../THIRD_PARTY.md)

Avec les dépendances installées, reconstruire sans les télécharger :

```powershell
.\build.ps1 -SkipInstall
```

`-SkipUiBuild` réutilise l'interface déjà compilée dans `web/`.
`-NoArchive` produit le dossier portable sans recréer le ZIP.
Les exécutables, ressources compilées, dépendances installées et bases
locales sont exclus de Git.

La distribution fournie cible Windows. Toute adaptation à Linux ou macOS
demande une construction et une validation sur le système concerné.

## Lancer et vérifier les sources

Une fois `.venv/` et `web/` préparés, lancer les sources depuis la racine.

```powershell
.\.venv\Scripts\python.exe main.py
```

Les vérifications utilisent des bases temporaires.

```powershell
.\.venv\Scripts\python.exe self_check.py
.\.venv\Scripts\python.exe main.py --smoke-test --report test-results/ui-source.json
```

Le test fonctionnel vérifie les données, les permissions, la persistance
et les imports atomiques avec les connexions réseau Python interdites.
Le test Qt s'exécute hors écran. Il vérifie notamment la création du
premier compte, l'affichage Cytoscape, les échanges JSON, le blocage des
URL distantes et la sauvegarde SQLite.

L'exécutable accepte `--self-test` et `--smoke-test` avec
`--report chemin.json`. Attendre la fin du processus avant de lire le
rapport. Pour un problème de rendu, essayer le mode logiciel décrit dans
la configuration.
[Configuration](CONFIGURATION.md#variables-denvironnement)

Les résultats de la distribution testée sont consignés à part.
[Vérifications de la distribution](../VALIDATION.md)
