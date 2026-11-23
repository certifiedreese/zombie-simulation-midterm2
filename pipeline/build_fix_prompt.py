# ============================================================
# build_fix_prompt.py - Pipeline step 6: the fix loop
#
# Run from the repo folder:
#     python pipeline/build_fix_prompt.py generated/<file>.py
#
# Reads the checker's report for that file, lists every failed
# check (with the official rule from the ontology), and builds a
# "fix only these problems" prompt for the AI.
# Writes prompts/fix_prompt_<file>.txt
# ============================================================

import json
import os
import sys

ONTOLOGY_PATH = "ontology/zombie_ontology.json"
TEMPLATE_PATH = "prompts/fix_template.txt"


def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline/build_fix_prompt.py generated/<file>.py")
        sys.exit(2)
    path = sys.argv[1]
    label = os.path.splitext(os.path.basename(path))[0]

    with open(ONTOLOGY_PATH, encoding="utf-8") as f:
        ontology = json.load(f)
    with open(f"reports/{label}_report.json", encoding="utf-8") as f:
        report = json.load(f)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    with open(path, encoding="utf-8") as f:
        code = f.read()

    # List every failed check, with the official rule when it's a constraint
    rules = {c["id"]: c["rule"] for c in ontology["constraints"]}
    failures = []
    for r in report["results"]:
        if not r["passed"]:
            line = f"- {r['check']}: {r['detail']}"
            if r["check"] in rules:
                line += f"\n  Rule {r['check']}: {rules[r['check']]}"
            failures.append(line)

    if not failures:
        print("No failed checks, so there is nothing to fix.")
        return

    prompt = (template
              .replace("{failures}", "\n".join(failures))
              .replace("{ontology}", json.dumps(ontology, indent=2))
              .replace("{code}", code))

    out_path = f"prompts/fix_prompt_{label}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Fix prompt written to {out_path} ({len(failures)} failed checks).")


if __name__ == "__main__":
    main()