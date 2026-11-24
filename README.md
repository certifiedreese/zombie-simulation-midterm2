# AI-Driven Development Pipeline with Ontology – CPS 310 Midterm #2

**Author:** Reese Franklin

## What This Is
A process control pipeline for using AI to write code for my Zombie Game
Simulation. Instead of asking the AI "write me a zombie game" and hoping
for the best, the pipeline:
1. writes down the game's rules in an **ontology** (a machine-readable
   rulebook),
2. builds the AI's prompt **from** the ontology,
3. **automatically checks** the AI's code against the ontology, and
4. sends the AI back to fix **only** what failed.

For the demos, I used a simplified version of the zombie game (no
graphics), as the assignment allows.

## How to Run
Run everything from the repo folder:
```
python pipeline/validate_ontology.py                       # check the ontology
python pipeline/build_prompt.py                            # build the AI prompt
python pipeline/run_checks.py generated/<file>.py          # check AI code
python pipeline/build_fix_prompt.py generated/<file>.py    # build a fix prompt
```

## Files
| File / folder | What it is |
|---|---|
| `ontology/zombie_ontology.json` | The current ontology (version 1.1) |
| `ontology/zombie_ontology_v1.0.json` | The original ontology (version 1.0) |
| `pipeline/validate_ontology.py` | Checks the ontology for mistakes |
| `pipeline/build_prompt.py` | Builds the AI prompt from the ontology |
| `pipeline/run_checks.py` | Checks AI code against the ontology |
| `pipeline/build_fix_prompt.py` | Builds a "fix these failures" prompt |
| `prompts/` | All prompt templates and the prompts actually sent to the AI |
| `generated/` | All code: AI outputs and the hand-written reference |
| `reports/` | Checker reports (JSON) for every code file |
| `DEMO_LOG.md` | Step-by-step record of every demo and its outcome |

## The Ontology
The ontology is the **single source of truth** for the project. It is a
JSON file with five parts:
- **Classes:** the things that exist (Agent, Human, Zombie, World) and the
  attributes each one has. Human and Zombie are kinds of Agent.
- **Relations:** how things interact: a zombie **chases** a human and
  **bites** a human, each with an exact rule.
- **Parameters:** the official numbers (vision 100, touch distance 13,
  fight chance, speeds).
- **Constraints:** rules that must **always** be true, each with an id:
  - C1: every agent stays inside the world
  - C2: every human is slower than every zombie
  - C3: agent ids are unique
  - C4: the total number of agents never increases
  - C5: a zombie moves at most ZOMBIE_SPEED per step
  - C6: the same seed always gives the same results
- **Interface:** the exact function names and parameters the code must
  have (`create_world`, `step`, `count`), so it can be tested
  automatically.

## The Pipeline, Step by Step
| Step | What happens | File |
|---|---|---|
| 1. Define | Write the rules in the ontology | `ontology/zombie_ontology.json` |
| 2. Validate | Check the ontology itself: every class, relation, parameter, and constraint must be consistent | `pipeline/validate_ontology.py` |
| 3. Build prompt | Fill the prompt template with the full ontology | `pipeline/build_prompt.py` |
| 4. Generate | Send the prompt to the AI and save its code, unedited | `generated/` |
| 5. Check | Static checks (names, classes, functions, parameters, standard library) and runtime checks (run 100 steps and test every constraint) | `pipeline/run_checks.py` |
| 6. Fix loop | If anything fails, build a prompt listing only the failures, with their official rules, and send it back to the AI. Repeat step 5. | `pipeline/build_fix_prompt.py` |
| 7. Accept and log | Accept only code that passes every check; save every prompt, output, and report | `DEMO_LOG.md`, `reports/` |

**Change control:** when a requirement changes, the ontology is updated
first and given a new version number. Then the existing code is
re-checked against the new version, and the fix loop brings it up to date.

### Why it is designed this way
- **Rules come first, code second.** The AI never decides what the rules
  are. It only implements them.
- **One source of truth.** The prompt and the checker both read the
  same ontology, so what the AI is told and what it is graded on can
  never drift apart.
- **Check the rulebook before the AI sees it.** A mistake in the ontology
  would become a mistake in the code, so step 2 catches it first.
- **The checker is tested first.** Before grading any AI code, I ran the
  checker on a hand-written correct program (`generated/reference_sim.py`)
  to prove the checker itself is right (25/25).
- **Fixes are targeted.** The fix prompt lists only what failed, so the AI
  doesn't rewrite working code.

## What the Pipeline Controls, and Why It Works

| What is controlled | How the pipeline controls it | Why it works | Naive AI development |
|---|---|---|---|
| **Names and structure** | The prompt gives exact class, attribute, function, and parameter names; the checker verifies them | Code that uses the wrong names is rejected automatically | The AI picks its own names (naive demo: one generic `Actor` class, no Human, Zombie, or World) |
| **Rules and numbers** | Every relation, parameter, and constraint is in the prompt; the checker tests each one | Every rule has an id and a test, so nothing can be silently skipped | The AI invents its own rules (naive demo: a 35% × 50% fight chance instead of 40%) |
| **Scope** | The prompt says "do not add features not in the ontology" | The AI has no room to guess what's wanted | The AI adds unrequested behavior (naive demo: humans run away from zombies) |
| **Correctness** | The checker runs the code for 100 steps and tests C1–C6 at every step | Bugs are found by running the code, not by reading it | Nothing checks the code at all |
| **Testability** | The ontology defines a standard interface | Any AI output can be plugged in and tested the same way | The naive code couldn't even be tested: the constraint checks could not run |
| **Reproducibility** | Constraint C6 requires a seeded random generator | The same seed always gives the same run, so results can be compared | The naive code had no seed, so no two runs match |
| **Change control** | Requirements change in the ontology first, with a version number | Old code is automatically flagged when it no longer matches | A change means re-prompting and hoping nothing else breaks |
| **Fixing errors** | Failures are listed with their rule ids and sent back to the AI | The AI fixes exactly the broken part | You'd have to find and explain each bug by hand |
| **Traceability** | Every prompt, output, and report is saved | Every result can be checked and repeated | Nothing is recorded |

## The Prompts

### Naive prompt (`prompts/naive_prompt.txt`)
```
Write a Python zombie simulation where zombies chase humans and
infect them, and humans can sometimes fight back.
Use only the Python standard library, no graphics.
```

### Generation prompt template (`prompts/generate_template.txt`)
The `{ontology}` placeholder is replaced with the full ontology by
`build_prompt.py`. The finished prompt sent to the AI is saved in
`prompts/generate_prompt.txt`.
```
You are writing Python code for a zombie simulation.
The ONTOLOGY below is the official specification. Follow it exactly.

RULES:
1. Use EXACTLY the class names, attribute names, function names, and
   parameter names in the ontology. Do not rename anything.
2. Human and Zombie must be subclasses of Agent.
3. Define every parameter as a module-level constant with the same
   name and value (for example: ZOMBIE_SPEED = 1.5).
4. Implement every relation rule and every constraint (C1 to C6).
5. In create_world, set world.rng = random.Random(seed), and use ONLY
   world.rng for randomness, so constraint C6 holds.
6. Use only the Python standard library. No graphics, no input(),
   no printing, and no code that runs when the file is imported.
7. Do not add features that are not in the ontology.
8. Reply with ONE complete Python file in a single code block,
   and nothing else.

ONTOLOGY:
{ontology}
```

### Fix prompt template (`prompts/fix_template.txt`)
`build_fix_prompt.py` fills in the failed checks, the ontology, and the
current code. The finished prompt sent to the AI is saved in
`prompts/fix_prompt_pipeline_v1.txt`.
```
The Python file below was written from the ontology, but it FAILED
some automatic checks. Fix ONLY the problems listed. Keep every
name exactly as in the ontology, and keep following all the rules
from before.

FAILED CHECKS:
{failures}

ONTOLOGY:
{ontology}

CURRENT CODE:
{code}

Reply with ONE complete, corrected Python file in a single code
block, and nothing else.
```

## Demos and Results
AI model used: **ChatGPT (GPT-6 Luna)**. The same model was used for
every AI demo, with a new chat for each one. The AI's code was saved
exactly as returned, never edited by hand. Full details are in
`DEMO_LOG.md`.

| Demo | What was tested | Outcome |
|---|---|---|
| 1 | Validator on a broken ontology (`"to": "Humans"`) | Caught: "Relation 'chases' has unknown 'to' class 'Humans'" |
| 2 | Checker on a hand-written correct program | 25/25: the checker is trustworthy |
| 3 | **Naive prompt** | **3/17**: no matching classes, functions, or parameters; constraint checks could not run. The AI also had to ask a question before starting, because the prompt was too vague. |
| 4 | **Pipeline prompt** (same model) | **25/25 on the first try** |
| 5 | Requirement change: FIGHT_CHANCE 0.4 → 0.5 (ontology v1.0 → v1.1) | Old code flagged (24/25, FIGHT_CHANCE failed); the fix prompt was built automatically; the AI's fix passed 25/25 |

### Main result
With the **same AI model**, the naive prompt scored **3/17** and the
pipeline prompt scored **25/25**. When the requirements changed, the
pipeline caught the outdated code automatically and guided the AI to a
fix that passed every check.

## Limitations
- **The checker only tests what it was programmed to test.** A behavior
  with no check (for example, exactly how a zombie picks between two
  equally close humans) could still be wrong.
- **Constraint tests are written by hand.** Each new constraint in the
  ontology needs a matching test in the checker.
- **Small sample:** one AI model, and one run for each prompt. More
  models and repeated runs would make the comparison stronger.
- **Manual copy and paste:** prompts and code are moved between the AI
  chat and the files by hand, since free AI tiers don't offer automatic
  access. The pipeline steps themselves are fully automated scripts.
- **The naive comparison:** the naive prompt didn't know the required
  names, so some failures were expected. That is the point: without a
  shared specification, AI output can't be checked or combined with the
  rest of a project, and the naive code also got the actual rules wrong.