# OSINT Graph Desktop

OSINT Graph Desktop permet de représenter des personnes et leurs relations
dans des graphes interactifs. Il propose une bibliothèque de graphes, des
comptes locaux avec des droits par graphe et des échanges au format JSON.

La distribution portable fonctionne hors ligne sous Windows 10 et 11
(64 bits). La version web est maintenue dans un dépôt distinct.
[OSINT Graph Web](https://github.com/Me-K/osint-graph-web)

## Démarrer

Télécharger le ZIP `OSINTGraph-Windows-x64.zip` dans la dernière release,
extraire le dossier complet, puis ouvrir `OSINTGraph.exe`. Le premier lancement
guide la création du compte administrateur local.
[Dernière release](https://github.com/Me-K/osint-graph-desktop/releases/latest)

## Documentation

| Besoin | Guide |
| --- | --- |
| Télécharger, lancer ou mettre à jour le programme portable | [Installation](docs/INSTALLATION.md) |
| Gérer les graphes, les comptes et les accès, ou importer un graphe web | [Utilisation](docs/UTILISATION.md) |
| Comprendre Python, Qt, React, Cytoscape et SQLite | [Architecture et stack technique](docs/ARCHITECTURE.md) |
| Choisir le dossier des données, sauvegarder et restaurer la base | [Configuration](docs/CONFIGURATION.md) |
| Consulter les routes internes et le format d'échange JSON | [API interne](docs/API.md) |
| Se repérer dans les sources, reconstruire et vérifier le programme | [Développement](docs/DEVELOPPEMENT.md) |

## Licence

La licence personnalisée autorise l'utilisation, la modification et la
redistribution gratuites. Elle interdit la vente du logiciel ou de ses
versions modifiées. Les copies redistribuées conservent les mentions de
copyright et la licence, et les modifications doivent être signalées.
[Texte complet de la licence](LICENSE)

Les composants tiers conservent leurs licences propres.
[Notices des composants tiers](THIRD_PARTY.md)
