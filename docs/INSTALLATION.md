# Installation et démarrage

[Retour au README](../README.md)

## Télécharger la distribution portable

La distribution cible Windows 10 et 11 en 64 bits. Télécharger
`OSINTGraph-Windows-x64.zip` depuis les fichiers de la dernière release.
Cette page fournit aussi les sources et les empreintes SHA-256.
[Dernière release](https://github.com/Me-K/osint-graph-desktop/releases/latest)

1. Extraire tout le dossier `OSINTGraph` à l'emplacement de votre choix.
2. Ouvrir `OSINTGraph.exe` dans le dossier extrait. Conserver `_internal`
   à côté de l'exécutable.
3. Au premier lancement, choisir l'identifiant et le mot de passe du compte
   administrateur. L'application crée aussi le **Graphe principal**.
4. Se connecter et ouvrir un graphe depuis **Mes graphes**.

Le dossier embarque Python, Qt, le moteur de rendu, SQLite et l'interface.
Après téléchargement, il s'utilise hors ligne sans installer Python,
Node.js, Docker ou Neo4j.
[Guide d'utilisation](UTILISATION.md)

## Mettre à jour ou changer de poste

Fermer l'application puis extraire le dossier complet de la nouvelle version.
Sur le même poste et avec le même dossier de données, le nouveau programme
retrouve les comptes et les graphes existants. Les données sont conservées
séparément du programme.

Pour utiliser le programme sur un autre poste, transférer le ZIP ou le dossier
portable complet. Pour transférer aussi tous les comptes et graphes, créer une
sauvegarde de la base sur le poste d'origine et la restaurer sur le poste
d'arrivée. Un export JSON suffit pour transférer un seul graphe.
[Données et sauvegardes](CONFIGURATION.md)

## Démarrer depuis les sources

Depuis un clone Git, préparer le programme en suivant le guide de
développement. Une fois la compilation terminée, lancer
`dist\OSINTGraph\OSINTGraph.exe` ou `start.bat` à la racine du dépôt.
Le script ouvre en priorité l'exécutable et peut aussi lancer les sources
avec l'environnement Python local et l'interface déjà compilée.
[Construction depuis les sources](DEVELOPPEMENT.md#construire-la-distribution-windows)
