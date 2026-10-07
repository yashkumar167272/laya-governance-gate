import json
import os

DATA_DIR = "data"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_catalog():
    """Read the catalog JSON file."""
    path = os.path.join(DATA_DIR, "catalog.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_lineage():
    """Read the lineage JSON file."""
    path = os.path.join(DATA_DIR, "lineage.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_changes():
    """Read the changes JSON Lines file, one JSON object per non-empty line."""
    path = os.path.join(DATA_DIR, "changes.jsonl")
    changes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                changes.append(json.loads(line))
    return changes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def catalog_column_keys(catalog):
    """Return the set of dotted 'table.column' keys from the catalog."""
    keys = set()
    for table, meta in catalog["tables"].items():
        for col in meta["columns"]:
            keys.add(f"{table}.{col}")
    return keys


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------

def sanity_check(catalog, lineage, changes):
    """
    Report four classes of problems:
      1. Catalog columns missing from lineage.
      2. Lineage entries that reference columns not in the catalog.
      3. Changes that reference a column not in the catalog.
      4. Changes that contain forbidden label fields.
    """
    issues = []

    catalog_keys = catalog_column_keys(catalog)
    lineage_keys = set(lineage.keys())

    # 1. Catalog columns missing from lineage
    for key in sorted(catalog_keys - lineage_keys):
        issues.append(f"Catalog column missing from lineage: {key}")

    # 2. Lineage entries not present in the catalog
    for key in sorted(lineage_keys - catalog_keys):
        issues.append(f"Lineage references unknown catalog column: {key}")

    # 3. Change references not present in the catalog
    for change in changes:
        key = f'{change["table"]}.{change["column"]}'
        if key not in catalog_keys:
            issues.append(
                f"Change {change['id']} references unknown column: {key}"
            )

    # 4. Forbidden label fields
    forbidden = {"should_allow", "risk_level", "needs_review"}
    for change in changes:
        for field in forbidden:
            if field in change:
                issues.append(
                    f"Change {change['id']} contains forbidden field: {field}"
                )

    # Output
    if not issues:
        print("OK: no issues found")
    else:
        for issue in issues:
            print(issue)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    try:
        catalog = load_catalog()
        lineage = load_lineage()
        changes = load_changes()

        n_tables = len(catalog["tables"])
        n_columns = sum(
            len(meta["columns"]) for meta in catalog["tables"].values()
        )
        print(f"Tables: {n_tables}")
        print(f"Columns: {n_columns}")
        print(f"Lineage entries: {len(lineage)}")
        print(f"Proposed changes: {len(changes)}")
        print()

        sanity_check(catalog, lineage, changes)
        print()

        if changes:
            print("First change record:")
            print(json.dumps(changes[0], indent=2))

    except FileNotFoundError as e:
        print(f"Error: missing data file -> {e.filename}")


if __name__ == "__main__":
    main()