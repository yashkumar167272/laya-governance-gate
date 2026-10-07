import json

from load import load_catalog, load_lineage, load_changes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table_size_band(row_count):
    """Bucket a table's row count into a coarse size band."""
    if row_count is None:
        return "unknown"
    if row_count < 100_000:
        return "small"
    if row_count < 1_000_000:
        return "medium"
    if row_count < 10_000_000:
        return "large"
    return "very_large"


def _change_detail(change):
    """
    Pull the type-specific payload out of a change record.

    - drop_column        -> {}
    - rename_column      -> {"from_name": ..., "to_name": ...}
    - change_type        -> {"from_type": ..., "to_type": ...}
    - make_nullable      -> {}
    - make_not_nullable  -> {}
    """
    ct = change.get("change_type")

    if ct == "rename_column":
        return {
            "from_name": change.get("column"),
            "to_name": change.get("new_name"),
        }
    if ct == "change_type":
        return {
            "from_type": change.get("from_type"),
            "to_type": change.get("to_type"),
        }
    # drop_column, make_nullable, make_not_nullable
    return {}


def _derived_features(consumers, row_count):
    """Precompute summary facts so Laya does not have to."""
    consumer_count = len(consumers)

    has_ml = any(c.get("type") == "ml_model" for c in consumers)
    has_critical = any(c.get("criticality") == "high" for c in consumers)

    # Highest criticality present, using a simple ranking.
    rank = {"low": 1, "medium": 2, "high": 3}
    criticality_max = None
    for c in consumers:
        crit = c.get("criticality")
        if crit in rank:
            if criticality_max is None or rank[crit] > rank[criticality_max]:
                criticality_max = crit

    consumer_type_count = len({c.get("type") for c in consumers})

    return {
        "consumer_count": consumer_count,
        "has_ml_consumer": has_ml,
        "has_critical_consumer": has_critical,
        "criticality_max": criticality_max,
        "consumer_type_count": consumer_type_count,
        "table_size_band": _table_size_band(row_count),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_state(change, catalog, lineage):
    """
    Turn one proposed change plus the catalog and lineage into a single
    self-contained JSON object that Laya will read.
    """
    table = change.get("table")
    column = change.get("column")
    key = f"{table}.{column}"

    # Look up the column in the catalog. Be defensive: if it is missing,
    # return a state with target=None rather than crashing.
    table_meta = catalog.get("tables", {}).get(table)
    column_meta = None
    if table_meta is not None:
        column_meta = table_meta.get("columns", {}).get(column)

    if column_meta is not None:
        target = {
            "table": table,
            "column": column,
            "column_type": column_meta.get("type"),
            "nullable": column_meta.get("nullable"),
            "table_row_count": table_meta.get("row_count"),
            "table_owner": table_meta.get("owner"),
        }
    else:
        target = None

    # Copy the lineage list so the state is self-contained.
    consumers = list(lineage.get(key, []))

    row_count = target["table_row_count"] if target else None

    state = {
        "change_id": change.get("id"),
        "change_type": change.get("change_type"),
        "change_detail": _change_detail(change),
        "target": target,
        "downstream_consumers": consumers,
        "derived_features": _derived_features(consumers, row_count),
    }
    return state


def build_all_states(changes, catalog, lineage):
    """Map build_state over every change."""
    return [build_state(c, catalog, lineage) for c in changes]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _summary_line(state):
    feat = state["derived_features"]
    return (
        f'{state["change_id"]} | '
        f'{state["change_type"]:<17} | '
        f'consumers={feat["consumer_count"]} | '
        f'ml={feat["has_ml_consumer"]} | '
        f'size={feat["table_size_band"]}'
    )


def main():
    catalog = load_catalog()
    lineage = load_lineage()
    changes = load_changes()

    states = build_all_states(changes, catalog, lineage)

    by_id = {s["change_id"]: s for s in states}

    print("State for chg_001 (easy):")
    print(json.dumps(by_id["chg_001"], indent=2))
    print()

    print("State for chg_005 (hard):")
    print(json.dumps(by_id["chg_005"], indent=2))
    print()

    print("All states:")
    for s in states:
        print(_summary_line(s))


if __name__ == "__main__":
    main()