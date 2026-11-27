# OSINT Graph Desktop

Version de bureau autonome et hors ligne d'OSINT Graph. Ce dépôt contient
l'application Python et son interface dans `ui/`. La version web est maintenue
séparément dans le dépôt `osint-graph-web`.

## Licence du code applicatif

Le code de l'application est distribué sous la licence personnalisée
[OSINT Graph Desktop — Free Redistribution, No Sale License](LICENSE).

- Utiliser, étudier, modifier et redistribuer gratuitement le logiciel est
  autorisé, y compris au sein d'une entreprise.
- Vendre le logiciel ou une version modifiée, facturer sa licence ou imposer
  un paiement pour obtenir une copie est interdit.
- Les copies redistribuées doivent conserver la licence et les mentions de
  copyright. Les versions modifiées doivent être identifiées comme telles.
- Les prestations distinctes de support, formation, installation ou
  développement peuvent être facturées si elles ne constituent pas un achat
  obligatoire pour obtenir le logiciel distribué ou exercer les droits accordés.
- Les modifications privées n'ont pas à être publiées. Le dépôt GitHub est
  public ; la licence permet aux destinataires de partager gratuitement leurs
  copies conformément à ses conditions.

L'interdiction de vente signifie qu'il ne s'agit pas d'une licence open source
au sens de l'[Open Source Initiative](https://opensource.org/osd).
Ce résumé ne remplace pas le texte de [LICENSE](LICENSE).
Les dépendances conservent leurs licences propres, décrites dans
[THIRD_PARTY.md](THIRD_PARTY.md).

## Démarrer sous Windows

La [dernière release GitHub](https://github.com/Me-K/osint-graph-desktop/releases/latest)
propose le ZIP portable Windows, les sources et leurs empreintes SHA-256.

Double-cliquer sur **`start.bat`** dans ce dossier, ou directement sur
**`dist/OSINTGraph/OSINTGraph.exe`**.

Après un clonage Git, construire d'abord le programme en suivant
[Reconstruire depuis les sources](#reconstruire-depuis-les-sources).
Les exécutables, dépendances installées et données locales sont exclus de Git.

Au premier lancement, choisir l'identifiant et le mot de passe du compte
administrateur. Les lancements suivants affichent l'écran de connexion.
Ouvrir ensuite « Graphe principal », ou créer un nouveau graphe.

L'accueil après connexion comporte quatre rubriques :

- **Mes graphes** : ouvrir, créer et importer un graphe.
- **Mon compte** : modifier son nom affiché et son mot de passe, après saisie du
  mot de passe actuel. Les autres sessions sont fermées après le changement.
- **Gestion des comptes**, pour les administrateurs de l'application : créer
  un compte sans l'associer à un graphe, modifier son nom et son rôle, le
  désactiver/réactiver, le débloquer ou réinitialiser son mot de passe.
- **Accès aux graphes**, pour les administrateurs d'au moins un graphe :
  attribuer, modifier et retirer les droits des comptes existants.

Ces réglages sont entièrement séparés du studio de graphe. Le bouton **Accueil**
du studio permet d'y revenir. L'identifiant de connexion reste fixe.

Le rôle d'**administrateur des comptes** est distinct du rôle d'administrateur
d'un graphe : créer un graphe ne permet pas d'administrer les utilisateurs.
Un administrateur des comptes n'obtient pas automatiquement accès aux graphes
des autres utilisateurs. La désactivation conserve les données et les droits,
mais ferme les sessions du compte ; le dernier administrateur actif est protégé.
Un compte administrant seul un graphe doit d'abord lui attribuer un autre
administrateur avant de pouvoir être désactivé.

Au premier lancement après cette mise à jour, les comptes existants sont
conservés et le premier compte actif créé à l'installation reçoit le rôle
d'administrateur des comptes. Cette migration n'est effectuée qu'une fois.

Le dossier portable `dist/OSINTGraph/` contient Python, Qt, le moteur de rendu,
SQLite et l'interface compilée. Il fonctionne **sans Internet, sans Docker,
sans installation de Python/Node.js et sans serveur à démarrer**.
Windows 10/11 64 bits est la cible de cette distribution.

Pour un autre ordinateur : copier **tout** le dossier `dist/OSINTGraph/`, ou
extraire `dist/OSINTGraph-Windows-x64.zip`, puis lancer `OSINTGraph.exe`.
L'exécutable seul ne suffit pas : conserver `_internal` à côté de lui.

## Fonctions reprises

- Comptes locaux, mots de passe hachés, sessions et verrouillage après échecs.
- Plusieurs graphes et permissions de lecture, modification et administration.
- Création, modification et suppression des personnes ; dates, âge, notes,
  entreprises et liens automatiques entre personnes de la même entreprise.
- Relations orientées, recherche et filtres par personne, type, entreprise et
  profondeur ; zoom, déplacement au clavier, sélection de zone, mini-carte.
- Import/export JSON compatible avec la version web ; remplacement ou fusion
  via le service interne. L'interface propose le remplacement et l'import dans
  un nouveau graphe. Un import invalide ne remplace aucune donnée existante.
- Export par boîte de dialogue Windows et sauvegarde complète de la base.

Les comptes et droits concernent les utilisateurs de **cette installation**.
Il n'y a pas de synchronisation entre ordinateurs ni de collecte sur Internet.

## Reprendre les données de la version web

1. Dans la version web existante, ouvrir chaque graphe puis **Exporter JSON**.
2. Dans la version de bureau, utiliser **Importer un graphe** depuis la
   bibliothèque pour créer un graphe, ou **Importer JSON** dans un graphe ouvert
   pour le remplacer après confirmation.
3. Recréer les utilisateurs depuis **Gestion des comptes**, puis attribuer les
   permissions depuis **Accès aux graphes**, sur l'accueil.

Les exports transportent les personnes, leurs identifiants et les relations avec
leurs propriétés. Les liens d'entreprise sont recalculés. Les comptes et mots
de passe de la version web ne sont pas inclus dans ces exports.
La base Neo4j existante n'est ni déplacée ni modifiée par cette application.

## Données et sauvegardes

Par défaut : `%LOCALAPPDATA%\OSINTGraph\osint-graph.sqlite3`.
Le menu **Fichier > Emplacement des données** affiche le chemin exact.
Les changements sont enregistrés immédiatement. Les données sont indépendantes
du dossier du programme : une mise à jour de celui-ci conserve les graphes.

**Fichier > Sauvegarder toute la base** crée une sauvegarde cohérente contenant
tous les graphes, comptes et permissions, même pendant l'utilisation.
Cette fonction demande une session administratrice sur tous les graphes.
Pour restaurer : fermer l'application, conserver une copie de la base actuelle,
puis remplacer `osint-graph.sqlite3` par la sauvegarde. Restaurer dans un dossier
de données vide si des fichiers `-wal` ou `-shm` subsistent après un arrêt brutal,
afin de ne pas associer une ancienne sauvegarde à un journal différent.

Un dossier spécifique peut être choisi avant le lancement :

```powershell
$env:OSINT_GRAPH_DATA_DIR = 'D:\MesEnquetes\OSINT'
.\dist\OSINTGraph\OSINTGraph.exe
```

La base SQLite n'est pas chiffrée. Les droits applicatifs ne remplacent pas les
permissions du système sur les fichiers. Le journal technique `desktop.log`
se trouve dans le même dossier et ne journalise pas les requêtes ni leurs données.

## Architecture

```text
Fenêtre Qt / React / Cytoscape (ressources locales)
               | QWebChannel, communication interne
     Python / FastAPI appelé en mémoire (ASGITransport)
               | requêtes SQL et transactions
       SQLite : graphes + comptes + permissions
```

Aucun port HTTP n'est ouvert. HTTPX sert uniquement à adapter les requêtes vers
FastAPI en mémoire, sans socket HTTP ni résolution DNS. L'interface ne contient
ni CDN ni police distante. Une politique de contenu et un intercepteur Qt
bloquent les URL réseau, y compris localhost. Les outils de développement et
les documentations Swagger distantes ne sont pas nécessaires.

Références techniques :
[WebChannel](https://doc.qt.io/qtforpython-6/overviews/qtwebchannel-javascript.html),
[interception Qt](https://doc.qt.io/qt-6/qwebengineurlrequestinterceptor.html),
[déploiement Qt WebEngine](https://doc.qt.io/qt-6/qtwebengine-deploying.html).

## Reconstruire depuis les sources

Sur le poste de préparation : Python 3.13 x64 et Node.js 22.12 ou ultérieur
(voir `ui/node_modules/vite/package.json` pour les contraintes exactes). L'accès Internet
sert uniquement à installer les dépendances de construction la première fois.

Depuis la racine du dépôt `osint-graph-desktop` :

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

`requirements-lock.txt` et `ui/package-lock.json` fixent les dépendances.
Le script installe l'environnement isolé, compile l'interface, exécute les tests,
collecte les notices puis fabrique la distribution portable et son ZIP.
Pour reconstruire sans téléchargement avec les dépendances déjà installées :

```powershell
.\build.ps1 -SkipInstall
```

`-SkipUiBuild` réutilise `web/` et `-NoArchive` évite de refaire le ZIP.
Pour démarrer directement les sources : `.\.venv\Scripts\python.exe main.py`.

Les sources sont adaptables à Linux/macOS avec Qt, mais les exécutables doivent
être construits et testés sur chaque système. Seule la distribution Windows est
fournie ici.

## Vérification et diagnostic

```powershell
.\.venv\Scripts\python.exe self_check.py
.\.venv\Scripts\python.exe main.py --smoke-test --report test-results/ui-source.json
```

Le premier vérifie les données, droits, imports atomiques et la persistance avec
DNS/connexions réseau Python interdits. Le second teste la vraie interface Qt
hors écran : premier compte, création de personnes, rendu Cytoscape, import/export,
blocage des URL distantes et sauvegarde SQLite. Ces tests utilisent exclusivement
des bases temporaires ; ils ne touchent pas aux enquêtes de l'utilisateur.

Les mêmes vérifications existent dans l'exécutable : `--self-test` et
`--smoke-test`, avec `--report chemin.json`. Comme il s'agit d'un programme sans
console, attendre la fin du processus avant de lire le rapport.

En cas de fenêtre blanche liée au pilote graphique, activer le rendu logiciel :

```powershell
$env:OSINT_GRAPH_SOFTWARE_RENDERING = '1'
.\dist\OSINTGraph\OSINTGraph.exe
```

Les notices des composants embarqués sont dans [THIRD_PARTY.md](THIRD_PARTY.md).
