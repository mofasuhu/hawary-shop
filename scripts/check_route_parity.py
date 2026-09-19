"""Verify refactored app routes match the backup monolith (golden snapshot)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SNAPSHOT = os.path.join(os.path.dirname(__file__), "backup_routes_snapshot.json")
BACKUP_APP = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "Hawary_Shop backup before Code Architecture Refactoring",
    "app.py",
)


def backup_routes_from_app_py():
    import re
    with open(BACKUP_APP) as f:
        text = f.read()
    routes = set()
    for m in re.finditer(r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?', text):
        path = m.group(1)
        methods = m.group(2) or "GET"
        methods = tuple(sorted(x.strip().strip("'\"") for x in methods.split(",")))
        routes.add((path, methods))
    for m in re.finditer(r'@api\.route\([\'"]([^\'"]+)[\'"]', text):
        routes.add(("/api" + m.group(1), ("GET",)))
    return routes


def load_snapshot():
    with open(SNAPSHOT) as f:
        data = json.load(f)
    return {(r["path"], tuple(r["methods"])) for r in data}


def current_routes():
    from app import create_app
    app = create_app()
    routes = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = tuple(sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS")))
        routes.add((rule.rule, methods))
    return routes


def main():
    if not os.path.isfile(SNAPSHOT):
        print(f"Missing snapshot: {SNAPSHOT}")
        sys.exit(1)

    current = current_routes()

    if os.path.isfile(BACKUP_APP):
        expected = backup_routes_from_app_py()
        label = "backup app.py"
    elif os.path.isfile(SNAPSHOT):
        expected = load_snapshot()
        label = "golden snapshot"
    else:
        print(f"Missing {BACKUP_APP} and {SNAPSHOT}")
        sys.exit(1)

    only_expected = expected - current
    only_current = current - expected

    if only_expected or only_current:
        print("ROUTE PARITY FAILED")
        if only_expected:
            print("\nMissing from current:")
            for r in sorted(only_expected):
                print(" ", r)
        if only_current:
            print("\nExtra in current:")
            for r in sorted(only_current):
                print(" ", r)
        sys.exit(1)

    print(f"OK: {len(expected)} routes match {label} (path + methods)")
    sys.exit(0)


if __name__ == "__main__":
    main()
