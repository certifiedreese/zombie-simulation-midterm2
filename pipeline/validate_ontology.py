# ============================================================
# validate_ontology.py - Pipeline step 2: check the ontology
#
# Run from the repo folder:  python pipeline/validate_ontology.py
# Makes sure the rulebook has no mistakes BEFORE the AI sees it.
# ============================================================

import json
import re
import sys

ONTOLOGY_PATH = "ontology/zombie_ontology.json"
PARAM_WORD = re.compile(r"\b[A-Z][A-Z_]{2,}\b")  # words like ZOMBIE_SPEED


def validate(ontology):
    errors = []
    classes = ontology.get("classes", {})
    params = ontology.get("parameters", {})

    # 1) Every parent class must exist
    for name, info in classes.items():
        parent = info.get("parent")
        if parent is not None and parent not in classes:
            errors.append(f"Class '{name}' has unknown parent '{parent}'")

    # 2) Every relation must connect classes that exist,
    #    and only use parameters that are defined
    for rel in ontology.get("relations", []):
        for side in ("from", "to"):
            if rel.get(side) not in classes:
                errors.append(f"Relation '{rel.get('name')}' has unknown '{side}' class '{rel.get(side)}'")
        for word in PARAM_WORD.findall(rel.get("rule", "")):
            if word not in params:
                errors.append(f"Relation '{rel.get('name')}' uses undefined parameter '{word}'")

    # 3) Every parameter must be a number
    for name, value in params.items():
        if not isinstance(value, (int, float)):
            errors.append(f"Parameter '{name}' is not a number")

    # 4) Constraints need a unique id and a rule, and only use defined parameters
    seen = set()
    for c in ontology.get("constraints", []):
        cid = c.get("id")
        if not cid or not c.get("rule"):
            errors.append(f"A constraint is missing an id or a rule: {c}")
        if cid in seen:
            errors.append(f"Duplicate constraint id '{cid}'")
        seen.add(cid)
        for word in PARAM_WORD.findall(c.get("rule", "")):
            if word not in params:
                errors.append(f"Constraint '{cid}' uses undefined parameter '{word}'")

    # 5) Every interface function needs a parameter list
    for name, info in ontology.get("interface", {}).items():
        if not isinstance(info.get("params"), list):
            errors.append(f"Interface function '{name}' has no parameter list")

    return errors


def main():
    with open(ONTOLOGY_PATH) as f:
        ontology = json.load(f)
    errors = validate(ontology)
    if errors:
        print("ONTOLOGY INVALID:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"Ontology OK: {len(ontology['classes'])} classes, "
          f"{len(ontology['relations'])} relations, "
          f"{len(ontology['constraints'])} constraints.")


if __name__ == "__main__":
    main()