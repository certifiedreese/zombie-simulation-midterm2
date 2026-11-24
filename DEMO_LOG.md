# Demo Log

## Demo 1: Ontology validation
- Correct ontology: Ontology OK: 4 classes, 2 relations, 6 constraints.
- Broken ontology ("to": "Humans"):
  ONTOLOGY INVALID: Relation 'bites' has unknown 'to' class 'Humans'
- Result: the pipeline catches a mistake in the rulebook before
  the AI ever sees it.
  ## Demo 2: Checker verified on a correct reference
- generated/reference_sim.py (hand-written, not AI): 25/25 checks passed
- Result: the checker is trustworthy before we use it to grade AI code.
# Chat GPT-6 Luna Demo 3
- Model: ChatGPT (write the exact model name)
- Prompt: prompts/naive_prompt.txt
- The AI first asked: "Should it run turn by turn in the console or
  advance automatically over time?" I answered: "Advance automatically
  over time."
- Output: generated/naive.py
- Checker result: 3/17 checks passed (reports/naive_report.json)
- What went wrong:
  - No Agent, Human, Zombie, or World classes (one generic Actor class).
  - None of the required functions or parameters.
  - The constraint checks (C1-C6) could not run at all, because the
    code has no standard interface to test.
  - It invented behavior nobody asked for (humans run away) and used
    its own rules (a 35% x 50% fight chance instead of 40%).
  - It uses a small grid, prints to the screen, and has no seed, so
    runs can't be repeated.
## Demo 4: Pipeline AI development
- Model: ChatGPT (same model as Demo 3)
- Prompt: prompts/generate_prompt.txt (built from the ontology)
- Output: generated/pipeline_v1.py
- Checker result: 25/25 checks passed on the first try
  (reports/pipeline_v1_report.json)
- Comparison: the same AI scored 3/17 with the naive prompt and
  25/25 with the pipeline prompt.
  ## Demo 5: Change control and the fix loop
- Requirement change: FIGHT_CHANCE changed from 0.4 to 0.5.
  Ontology updated from version 1.0 to 1.1
  (original saved as ontology/zombie_ontology_v1.0.json).
- Validator: Ontology OK.
- Old code (generated/pipeline_v1.py) checked against v1.1:
  24/25. The checker caught the mismatch:
  [FAIL] PARAM FIGHT_CHANCE: = 0.4, expected 0.5
- Fix prompt built automatically:
  prompts/fix_prompt_pipeline_v1.txt (1 failed check)
- AI's fixed code (generated/pipeline_v2.py): 25/25 checks passed
  (reports/pipeline_v2_report.json)
- Behavior changed as expected: with FIGHT_CHANCE 0.5, after 100 steps
  there were 64 humans and 17 zombies (vs 54 and 28 at 0.4).
- Note: reports/pipeline_v1_report.json now holds the v1.1 check
  (24/25). Its original v1.0 result (25/25) is recorded in Demo 4.