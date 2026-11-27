# Configuration, données et sauvegardes

[Retour au README](../README.md)

## Emplacement des données

Sous Windows, le fichier de données est par défaut
`%LOCALAPPDATA%\OSINTGraph\osint-graph.sqlite3`. Le menu
**Fichier > Emplacement des données** affiche son chemin exact.
Les changements sont enregistrés au fil de l'utilisation. Chaque dossier
de données correspond à une installation locale, avec ses graphes, ses
comptes et ses droits. Les données ne sont pas synchronisées entre postes.

Le chemin de base suit `LOCALAPPDATA` sous Windows, `~/Library/Application Support`
sous macOS et `XDG_DATA_HOME` sous Linux (par défaut `~/.local/share`).

Le journal technique `desktop.log` se trouve dans le même dossier.
La base SQLite est stockée sans chiffrement. Les permissions du système
contrôlent l'accès direct à ce fichier.

Sur une ancienne base créée avant l'ajout de la gestion des comptes, la
migration attribue une fois le rôle d'administrateur de l'application au
plus ancien compte actif et conserve les comptes et droits existants.

## Variables d'environnement

Définir les variables dans le terminal avant de lancer le programme.

| Variable | Valeur par défaut | Effet |
| --- | --- | --- |
| `OSINT_GRAPH_DATA_DIR` | `%LOCALAPPDATA%\OSINTGraph` sous Windows | Choisit le dossier de la base, du journal et du verrou d'instance. |
| `OSINT_GRAPH_SOFTWARE_RENDERING` | Non définie | La valeur `1` active le rendu logiciel, utile en cas de fenêtre blanche liée au pilote graphique. |
| `APP_DEFAULT_GRAPH_ID` | `default-main` | Identifiant du premier graphe lors de l'initialisation. |
| `APP_DEFAULT_GRAPH_NAME` | `Graphe principal` | Nom du premier graphe lors de l'initialisation. |
| `APP_PASSWORD_MIN_LENGTH` | `10` | Longueur minimale des nouveaux mots de passe. |
| `APP_LOGIN_MAX_FAILURES` | `5` | Nombre d'échecs avant verrouillage temporaire. |
| `APP_LOGIN_LOCK_MINUTES` | `15` | Durée du verrouillage en minutes. |
| `APP_SESSION_TTL_HOURS` | `12` | Durée de validité d'une nouvelle session en heures. |

Depuis le dossier portable extrait, lancer l'application avec un dossier
de données personnalisé.

```powershell
$env:OSINT_GRAPH_DATA_DIR = 'D:\MesEnquetes\OSINT'
.\OSINTGraph.exe
```

L'application autorise une seule instance par dossier de données.
Les mots de passe sont hachés avec `scrypt` et un sel aléatoire. SQLite
conserve le hash des jetons de session et suit leur expiration et leur
révocation.

## Sauvegarder et restaurer

**Fichier > Sauvegarder toute la base** crée une copie cohérente de SQLite
depuis une session qui administre tous les graphes. La copie contient les
graphes, comptes et permissions de l'installation.

1. Fermer l'application avant de restaurer et conserver une copie du dossier
   de données actuel.
2. Placer le fichier de sauvegarde sous le nom `osint-graph.sqlite3` dans
   le dossier de données. Si des fichiers `-wal` ou `-shm` sont restés après
   un arrêt brutal, restaurer dans un dossier de données vide et utiliser
   `OSINT_GRAPH_DATA_DIR` pour le sélectionner. La sauvegarde disposera ainsi
   de ses propres fichiers de journalisation.
3. Relancer le programme et vérifier les comptes et graphes restaurés.

Pour transférer seulement les personnes et relations d'un graphe, utiliser
l'export JSON du studio.
[Importer ou exporter un graphe](UTILISATION.md#importer-ou-exporter-un-graphe)
