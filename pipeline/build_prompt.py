# ============================================================
# build_prompt.py - Pipeline step 3: build the prompt from the ontology
#
# Run from the repo folder:  python pipeline/build_prompt.py
# Fills the template with the ontology, so the AI always gets
# the exact, official rules. Writes prompts/generate_prompt.txt.
# ============================================================

import json

ONTOLOGY_PATH = "ontology/zombie_ontology.json"
TEMPLATE_PATH = "prompts/generate_template.txt"
OUTPUT_PATH = "prompts/generate_prompt.txt"


def main():
    with open(ONTOLOGY_PATH, encoding="utf-8") as f:
        ontology = json.load(f)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    prompt = template.replace("{ontology}", json.dumps(ontology, indent=2))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Prompt written to {OUTPUT_PATH} "
          f"({len(prompt)} characters, ontology version {ontology['version']}).")


if __name__ == "__main__":
    main()