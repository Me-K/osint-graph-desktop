# API interne et format JSON

[Retour au README](../README.md)

L'interface appelle ces routes via Qt WebChannel. Le module `desktopApi.js`
accepte la méthode, le chemin, les données JSON et des options `params` et
`headers`. Le service Python traite les requêtes en mémoire et renvoie un
statut et les données de réponse.
[Trajet d'une requête](ARCHITECTURE.md#trajet-dune-requête)

## Session et premier lancement

| Méthode et route | Fonction |
| --- | --- |
| `GET /desktop/status` | Indiquer si le premier compte doit être créé. |
| `POST /desktop/setup` | Créer le premier compte et son graphe sur une installation vide. |
| `POST /auth/login` | Ouvrir une session et retourner `token`, `expires_at` et `user`. |
| `POST /auth/logout` | Révoquer la session courante. |
| `GET /auth/me` | Lire l'identité et le rôle global du compte connecté. |
| `GET /desktop/backup-access` | Vérifier que la session administre tous les graphes avant une sauvegarde complète. |

La connexion attend `user_id` et `password`. La configuration initiale
accepte aussi `display_name`. Après connexion, les appels protégés
transportent l'en-tête `Authorization: Bearer <token>`.

## Comptes et permissions

Les routes `/account/…` concernent le compte connecté. Les routes
`/admin/accounts…` exigent le rôle d'administrateur de l'application.
Les routes `/graphs/{graph_id}/permissions…` exigent le rôle `admin`
sur le graphe désigné.

| Méthode et route | Fonction |
| --- | --- |
| `PUT /account/profile` | Enregistrer le `display_name`. |
| `POST /account/password` | Changer le mot de passe avec `current_password` et `new_password`. |
| `GET /admin/accounts` | Lister les comptes locaux et leur état. |
| `POST /admin/accounts` | Créer un compte avec `user_id`, `password` et, au besoin, `display_name` et `is_admin`. |
| `PUT /admin/accounts/{user_id}` | Modifier `display_name`, `is_admin` ou `disabled`. |
| `POST /admin/accounts/{user_id}/password` | Réinitialiser le mot de passe d'un autre compte avec `new_password`. |
| `POST /admin/accounts/{user_id}/unlock` | Lever le verrouillage du compte. |
| `GET /graphs/{graph_id}/permissions` | Lister les droits sur le graphe. |
| `POST /graphs/{graph_id}/permissions` | Attribuer un `role` à un `user_id` existant. |
| `PUT /graphs/{graph_id}/permissions/{user_id}` | Changer le `role` du compte sur le graphe. |
| `DELETE /graphs/{graph_id}/permissions/{user_id}` | Retirer l'accès au graphe. |

## Graphes, personnes et relations

Les routes portant la mention `?graph_id=…` exigent l'identifiant du graphe
en paramètre. `editor` inclut les droits de `viewer` et `admin` inclut
les droits de `editor` sur ce graphe.

| Méthode et route | Droit minimal | Fonction |
| --- | --- | --- |
| `GET /graphs` | Session | Lister les graphes accessibles et les rôles associés. |
| `POST /graphs` | Session | Créer un graphe avec `name` et éventuellement `description`. |
| `GET /graph?graph_id=…` | `viewer` | Lire les `nodes` et `edges` pour l'affichage. |
| `GET /persons?graph_id=…` | `viewer` | Lister les nœuds de personnes. |
| `GET /persons/{person_id}?graph_id=…` | `viewer` | Lire la fiche complète d'une personne. |
| `POST /persons?graph_id=…` | `editor` | Créer une personne. |
| `PUT /persons/{person_id}?graph_id=…` | `editor` | Enregistrer les champs de la fiche. |
| `DELETE /persons/{person_id}?graph_id=…` | `editor` | Retirer une personne et ses liens. |
| `GET /companies?graph_id=…` | `viewer` | Lister les entreprises du graphe. |
| `POST /relations?graph_id=…` | `editor` | Créer un lien orienté avec `from_id`, `to_id` et `label`. |
| `GET /graph/export?graph_id=…` | `viewer` | Exporter le contenu complet du graphe. |
| `POST /graph/import?graph_id=…` | `editor` | Remplacer ou fusionner les données du graphe. |

Une fiche accepte `alias`, `nom`, `prenom`, `date_naissance`, `date_mort`,
`entreprise` et `description`. Fournir un alias ou le nom et le prénom.
Les dates utilisent le format `AAAA-MM-JJ`. Les routes vérifient que les
personnes d'une relation appartiennent au graphe ciblé.

## Format d'échange JSON

Le fichier d'export contient les métadonnées du graphe, les personnes et
les liens. Voici un exemple réduit aux champs illustrant sa structure.

```json
{
  "graph": {
    "id": "graphe-source",
    "name": "Exemple",
    "description": null
  },
  "persons": [
    {"id": "personne-a", "alias": "alice"},
    {"id": "personne-b", "alias": "bob"}
  ],
  "relations": [
    {
      "source": "personne-a",
      "target": "personne-b",
      "label": "CONNAIT",
      "properties": {}
    }
  ]
}
```

L'API d'import reçoit ce document dans le champ `data` d'un objet JSON.
Le champ `replace_existing` vaut `true` par défaut et remplace le contenu
du graphe cible. La valeur `false` fusionne ses données. Le graphe de
destination est celui du paramètre `graph_id`. Les liens automatiques
d'entreprise sont recalculés.

La réponse contient `replaced`, `persons_imported` et `relations_imported`.
Les comptes et permissions restent dans la base locale.
[Sauvegarder et restaurer](CONFIGURATION.md#sauvegarder-et-restaurer)
