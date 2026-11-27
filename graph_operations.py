"""Graph operations on SQLite. Business validation lives in backend.py."""
import json
import sqlite3
import uuid

from fastapi import HTTPException

AUTO_COMPANY_RELATION_TYPE = "MEME_ENTREPRISE"
PERSON_FIELDS = ("alias", "nom", "prenom", "date_naissance", "date_mort", "age", "entreprise", "description")


# Retrieve a person by identifier within the requested graph.
def get_person_by_id(tx, graph_id, person_id):
    row = tx.execute("SELECT * FROM persons WHERE graph_id=? AND id=?", (graph_id, person_id)).fetchone()
    return dict(row) if row else None


# Read all person records in a graph, ordered by alias, name, or identifier.
def list_person_records(tx, graph_id):
    return [dict(row) for row in tx.execute(
        "SELECT * FROM persons WHERE graph_id=? ORDER BY coalesce(alias, nom, id)", (graph_id,)
    )]


# Insert a person into SQLite and translate duplicate graph aliases into a conflict response.
def create_person(tx, graph_id, *values):
    person_id = str(uuid.uuid4())
    try:
        tx.execute(
            "INSERT INTO persons(graph_id,id,alias,nom,prenom,date_naissance,date_mort,age,entreprise,description) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)", (graph_id, person_id, *values)
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "Une personne avec cet alias existe déjà dans ce graphe.") from exc
    return get_person_by_id(tx, graph_id, person_id)


# Update a graph-scoped person in SQLite and reject aliases already used in that graph.
def update_person_by_id(tx, graph_id, person_id, *values):
    try:
        tx.execute(
            "UPDATE persons SET alias=?,nom=?,prenom=?,date_naissance=?,date_mort=?,age=?,entreprise=?,description=? "
            "WHERE graph_id=? AND id=?", (*values, graph_id, person_id)
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "Une autre personne utilise déjà cet alias.") from exc
    return get_person_by_id(tx, graph_id, person_id)


# Delete a person and their relationships within the graph, reporting whether a record was removed.
def delete_person_by_id(tx, graph_id, person_id):
    return tx.execute("DELETE FROM persons WHERE graph_id=? AND id=?", (graph_id, person_id)).rowcount > 0


# Return the distinct nonempty company names present in a graph.
def list_companies(tx, graph_id):
    return [row[0] for row in tx.execute(
        "SELECT DISTINCT entreprise FROM persons WHERE graph_id=? AND entreprise IS NOT NULL "
        "AND trim(entreprise)<>'' ORDER BY entreprise", (graph_id,)
    )]


# Validate graph membership and upsert a directed relationship, merging its stored JSON properties.
def create_relation(tx, graph_id, from_id, to_id, label, properties=None):
    if from_id == to_id:
        raise HTTPException(422, "Choisissez deux personnes différentes.")
    if not get_person_by_id(tx, graph_id, from_id) or not get_person_by_id(tx, graph_id, to_id):
        raise HTTPException(422, "Une relation référence une personne absente du graphe.")
    existing = tx.execute(
        "SELECT * FROM relations WHERE graph_id=? AND source=? AND target=? AND label=?",
        (graph_id, from_id, to_id, label),
    ).fetchone()
    props = json.loads(existing["properties"]) if existing else {}
    props.update(properties or {})
    relation_id = str(props.get("id") or (existing["id"] if existing else uuid.uuid4()))
    props.update(id=relation_id, graph_id=graph_id)
    try:
        tx.execute(
            "INSERT INTO relations(graph_id,id,source,target,label,properties) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(graph_id,source,target,label) DO UPDATE SET id=excluded.id,properties=excluded.properties",
            (graph_id, relation_id, from_id, to_id, label, json.dumps(props, ensure_ascii=False)),
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "Identifiant de relation déjà utilisé dans ce graphe.") from exc
    return {"id": relation_id, "source": from_id, "target": to_id, "type": label}


# Refresh automatic same-company relationships for one person after their company changes.
def sync_same_company_links(tx, graph_id, person_id):
    tx.execute("DELETE FROM relations WHERE graph_id=? AND label=? AND (source=? OR target=?)",
               (graph_id, AUTO_COMPANY_RELATION_TYPE, person_id, person_id))
    person = get_person_by_id(tx, graph_id, person_id)
    if not person or not person["entreprise"]:
        return
    others = tx.execute("SELECT id FROM persons WHERE graph_id=? AND entreprise=? AND id<>?",
                        (graph_id, person["entreprise"], person_id)).fetchall()
    for other in others:
        source, target = sorted((person_id, other["id"]))
        create_relation(tx, graph_id, source, target, AUTO_COMPANY_RELATION_TYPE,
                        {"auto": True, "company": person["entreprise"]})


# Recreate all automatic same-company relationships in a graph from current person records.
def rebuild_same_company_links(tx, graph_id):
    tx.execute("DELETE FROM relations WHERE graph_id=? AND label=?", (graph_id, AUTO_COMPANY_RELATION_TYPE))
    pairs = tx.execute(
        "SELECT a.id AS source,b.id AS target,a.entreprise FROM persons a JOIN persons b "
        "ON a.graph_id=b.graph_id AND a.entreprise=b.entreprise AND a.id<b.id "
        "WHERE a.graph_id=? AND a.entreprise IS NOT NULL AND trim(a.entreprise)<>''", (graph_id,)
    ).fetchall()
    for pair in pairs:
        create_relation(tx, graph_id, pair["source"], pair["target"], AUTO_COMPANY_RELATION_TYPE,
                        {"auto": True, "company": pair["entreprise"]})


# Read a graph's persons and relationships, decoding stored relationship properties for export.
def export_records(tx, graph_id):
    persons = list_person_records(tx, graph_id)
    relations = [
        {"source": row["source"], "target": row["target"], "label": row["label"],
         "properties": json.loads(row["properties"])}
        for row in tx.execute("SELECT * FROM relations WHERE graph_id=? ORDER BY label,source,target", (graph_id,))
    ]
    return persons, relations


# Merge or replace a graph's records in the current transaction and rebuild automatic company links.
def import_graph_snapshot(tx, graph_id, persons, relations, replace_existing):
    ids = [person["id"] for person in persons]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Le fichier contient des identifiants de personnes en double.")
    if replace_existing:
        tx.execute("DELETE FROM persons WHERE graph_id=?", (graph_id,))
    # Any failure rolls the entire import back, including replacement of existing data.
    for person in persons:
        existing = get_person_by_id(tx, graph_id, person["id"]) or {}
        values = {**existing, **person}
        try:
            tx.execute(
                "INSERT INTO persons(graph_id,id,alias,nom,prenom,date_naissance,date_mort,age,entreprise,description) "
                "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(graph_id,id) DO UPDATE SET "
                "alias=excluded.alias,nom=excluded.nom,prenom=excluded.prenom,date_naissance=excluded.date_naissance,"
                "date_mort=excluded.date_mort,age=excluded.age,entreprise=excluded.entreprise,description=excluded.description",
                (graph_id, person["id"], *(values.get(field) for field in PERSON_FIELDS)),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Import annulé : plusieurs personnes utilisent le même alias.") from exc
    available_ids = {row[0] for row in tx.execute("SELECT id FROM persons WHERE graph_id=?", (graph_id,))}
    imported_links = set()
    for relation in relations:
        if relation["source"] not in available_ids or relation["target"] not in available_ids:
            raise HTTPException(422, "Import annulé : un lien référence une personne absente du graphe.")
        if relation["source"] == relation["target"]:
            raise HTTPException(422, "Import annulé : un lien relie une personne à elle-même.")
        if relation["label"] == AUTO_COMPANY_RELATION_TYPE:
            continue
        create_relation(tx, graph_id, relation["source"], relation["target"], relation["label"], relation["properties"])
        imported_links.add((relation["source"], relation["target"], relation["label"]))
    rebuild_same_company_links(tx, graph_id)
    return {"persons_imported": len(persons), "relations_imported": len(imported_links)}
