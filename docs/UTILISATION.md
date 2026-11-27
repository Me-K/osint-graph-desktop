# Guide d'utilisation

[Retour au README](../README.md)

## Accueil après connexion

Après le premier lancement, l'application affiche l'écran de connexion.
Les rubriques disponibles sur l'accueil dépendent de vos droits.

| Rubrique | Actions |
| --- | --- |
| **Mes graphes** | Ouvrir, créer ou importer un graphe. |
| **Mon compte** | Modifier le nom affiché ou changer le mot de passe. |
| **Gestion des comptes** | Administrer les comptes locaux avec le rôle d'administrateur de l'application. |
| **Accès aux graphes** | Attribuer et retirer les accès aux graphes que vous administrez. |

Le bouton **Accueil** du studio permet de retrouver ces rubriques. Le créateur
d'un graphe devient administrateur de ce graphe.

## Personnes et relations

Dans le studio, utiliser **Nouvelle personne** pour créer une fiche. Donner
un alias unique dans le graphe, ou renseigner le nom et le prénom pour
générer cet alias. Les dates, l'entreprise et les notes sont facultatives.
L'âge se calcule à partir de la date de naissance jusqu'au décès ou à la
date du jour.

Cliquer sur un nœud pour consulter la fiche. Avec les droits d'édition,
vous pouvez la modifier ou la supprimer. Supprimer une personne retire
également ses liens.

Pour créer une relation orientée, sélectionner une personne source, une
personne cible et un type de lien, par exemple `CONNAIT`. Les personnes qui
partagent une entreprise sont aussi reliées par des liens automatiques
`MEME_ENTREPRISE`.

## Explorer le graphe

Le filtre relationnel permet de rechercher une personne et de limiter la vue
par type de lien, entreprise et profondeur en nombre de liens parcourus.
Les filtres agissent sur l'affichage. **Recentrer** ajuste la vue aux éléments
visibles.

Le zoom par cadre permet de sélectionner une zone. Les flèches du clavier
déplacent la vue et la miniature montre sa position dans le graphe.

## Importer ou exporter un graphe

**Exporter JSON** ouvre la boîte de dialogue de sauvegarde. Le fichier
contient les personnes, leurs identifiants et les relations avec leurs
propriétés. Il peut servir à échanger des graphes avec la version web.

| Action | Effet |
| --- | --- |
| **Importer un graphe** depuis **Mes graphes** | Crée un nouveau graphe à partir du fichier JSON. |
| **Importer JSON** depuis le studio | Remplace le contenu du graphe ouvert après confirmation. |

Un import invalide laisse les données existantes intactes. Les liens
automatiques d'entreprise sont recalculés à l'import.

Pour reprendre les données web, exporter chaque graphe depuis l'interface
web et importer son JSON dans l'application desktop. Recréer ensuite les
comptes depuis **Gestion des comptes**, puis accorder leurs droits depuis
**Accès aux graphes**. Les comptes et mots de passe web ne font pas partie
des fichiers JSON. La base Neo4j web reste indépendante.
[Format d'échange](API.md#format-déchange-json)

## Gérer son compte

Dans **Mon compte**, vous pouvez mettre à jour votre nom affiché. Votre
identifiant de connexion est fixe. Pour changer le mot de passe, saisir le
mot de passe actuel puis le nouveau. Le changement ferme les autres sessions
du compte. Par défaut, le nouveau mot de passe doit comporter au moins dix
caractères et trois catégories parmi minuscules, majuscules, chiffres et
symboles.

## Administrer les comptes et les accès

Le rôle d'administrateur de l'application donne accès à **Gestion des comptes**.
Il permet de créer des comptes, de modifier leur nom ou leur rôle global,
de les désactiver ou réactiver, de les débloquer et de réinitialiser le mot de
passe d'un autre compte. La désactivation conserve les données et les droits,
mais révoque les sessions. L'application protège le dernier administrateur
actif. Un compte qui administre seul un graphe doit avoir un remplaçant
actif sur ce graphe avant de pouvoir être désactivé.

Dans **Accès aux graphes**, les administrateurs d'un graphe peuvent attribuer,
modifier et retirer les droits des comptes existants sur ce graphe.

| Rôle dans le graphe | Droits |
| --- | --- |
| `viewer` | Consulter, filtrer et exporter. |
| `editor` | Consulter et exporter, créer, modifier ou supprimer des personnes, créer des relations et importer. |
| `admin` | Éditer et gérer les accès au graphe. |

Les deux niveaux d'administration sont indépendants. Un compte peut
administrer des graphes sans gérer les comptes, ou gérer les comptes en
conservant uniquement ses propres accès aux graphes.
