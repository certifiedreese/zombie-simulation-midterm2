# ============================================================
# run_checks.py - Pipeline step 5: check AI-written code
#
# Run from the repo folder:
#     python pipeline/run_checks.py generated/<file>.py
#
# Part A (static):  reads the code and checks it matches the
#                   ontology: classes, parents, functions,
#                   parameter values, standard library only.
# Part B (runtime): runs the code for 100 steps and checks
#                   every constraint (C1-C6) at every step.
# Saves a report to reports/<file>_report.json
# ============================================================

import ast
import importlib.util
import json
import math
import os
import sys
import threading

ONTOLOGY_PATH = "ontology/zombie_ontology.json"
EPS = 1e-6


def load_ontology():
    with open(ONTOLOGY_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------- PART A: STATIC CHECKS (reading the code) ----------
def static_checks(source, ontology):
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [("SYNTAX", False, f"code does not parse: {e}")]
    results = [("SYNTAX", True, "code parses")]

    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    try:
                        consts[t.id] = ast.literal_eval(n.value)
                    except Exception:
                        consts[t.id] = None

    # Every class exists, with the right parent
    for name, info in ontology["classes"].items():
        if name not in classes:
            results.append((f"CLASS {name}", False, "missing"))
            continue
        parent = info["parent"]
        if parent:
            bases = [b.id for b in classes[name].bases if isinstance(b, ast.Name)]
            ok = parent in bases
            results.append((f"CLASS {name}", ok,
                            f"subclass of {parent}" if ok else f"should be a subclass of {parent}, bases are {bases}"))
        else:
            results.append((f"CLASS {name}", True, "defined"))

    # Every interface function exists, with the exact parameter names
    for name, info in ontology["interface"].items():
        if name not in funcs:
            results.append((f"FUNC {name}", False, "missing"))
            continue
        params = [a.arg for a in funcs[name].args.args]
        ok = params == info["params"]
        results.append((f"FUNC {name}", ok,
                        f"params {params}" if ok else f"params {params}, expected {info['params']}"))

    # Every parameter is a constant with the right value
    for name, value in ontology["parameters"].items():
        ok = name in consts and consts[name] == value
        results.append((f"PARAM {name}", ok,
                        f"= {value}" if ok else f"= {consts.get(name, 'missing')}, expected {value}"))

    # Only the Python standard library is used
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods = [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods = [n.module.split(".")[0]]
        else:
            continue
        bad += [m for m in mods if m not in sys.stdlib_module_names]
    results.append(("STDLIB ONLY", not bad, "ok" if not bad else f"non-standard imports: {bad}"))
    return results


# ---------- LOADING THE CODE SAFELY ----------
def load_module(path, timeout=10):
    """Import the file, but give up if it runs forever or waits for input."""
    holder = {}

    def target():
        try:
            spec = importlib.util.spec_from_file_location("generated_module", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            holder["module"] = module
        except BaseException as e:
            holder["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None, "import never finished (the code runs or waits for input when imported)"
    if "error" in holder:
        return None, f"import failed: {holder['error']!r}"
    return holder["module"], None


def all_attributes(ontology, class_name):
    """A class's attributes, including the ones it inherits."""
    classes = ontology["classes"]
    attrs = dict(classes[class_name]["attributes"])
    parent = classes[class_name]["parent"]
    while parent:
        attrs.update(classes[parent]["attributes"])
        parent = classes[parent]["parent"]
    return attrs


# ---------- PART B: RUNTIME CHECKS (running the code) ----------
def runtime_checks(module, ontology):
    P = ontology["parameters"]
    if not all(hasattr(module, f) for f in ontology["interface"]):
        return [("RUNTIME", False, "cannot run the constraint checks: interface functions are missing")]

    def make(seed):
        return module.create_world(width=400, height=300, num_humans=100, num_zombies=10, seed=seed)

    try:
        world = make(1)
    except Exception as e:
        return [("RUNTIME", False, f"create_world failed: {e!r}")]
    results = []

    # Every attribute in the ontology exists on the real objects
    missing = [f"World.{a}" for a in ontology["classes"]["World"]["attributes"] if not hasattr(world, a)]
    for kind, cls in (("humans", "Human"), ("zombies", "Zombie")):
        agents = getattr(world, kind, [])
        if agents:
            missing += [f"{cls}.{a}" for a in all_attributes(ontology, cls) if not hasattr(agents[0], a)]
    results.append(("ATTRIBUTES", not missing, "all present" if not missing else f"missing: {missing}"))

    # count() returns the right numbers
    try:
        c = tuple(module.count(world))
        ok = c == (len(world.humans), len(world.zombies))
        results.append(("COUNT RESULT", ok, f"returned {c}"))
    except Exception as e:
        results.append(("COUNT RESULT", False, f"crashed: {e!r}"))

    # Run 100 steps and check C1-C5 after every step
    first_fail = {cid: None for cid in ("C1", "C2", "C3", "C4", "C5")}

    def note(cid, message):
        if first_fail[cid] is None:
            first_fail[cid] = message

    try:
        start_counts = (len(world.humans), len(world.zombies))
        prev_total = start_counts[0] + start_counts[1]
        prev_zombies = {z.id: (z.x, z.y) for z in world.zombies}
        for s in range(1, 101):
            module.step(world)
            agents = world.humans + world.zombies

            for a in agents:  # C1: inside the world
                if not (-EPS <= a.x <= world.width + EPS and -EPS <= a.y <= world.height + EPS):
                    note("C1", f"step {s}: agent {a.id} is outside the world at ({a.x:.2f}, {a.y:.2f})")
                    break
            for h in world.humans:  # C2: speeds
                if not (P["HUMAN_SPEED_MIN"] - EPS <= h.speed <= P["HUMAN_SPEED_MAX"] + EPS):
                    note("C2", f"human {h.id} has speed {h.speed}")
                    break
            for z in world.zombies:
                if abs(z.speed - P["ZOMBIE_SPEED"]) > EPS:
                    note("C2", f"zombie {z.id} has speed {z.speed}")
                    break
            ids = [a.id for a in agents]  # C3: unique ids
            if len(ids) != len(set(ids)):
                note("C3", f"step {s}: duplicate ids")
            total = len(agents)  # C4: total never goes up
            if total > prev_total:
                note("C4", f"step {s}: agents went from {prev_total} to {total}")
            for z in world.zombies:  # C5: zombies move at most ZOMBIE_SPEED
                if z.id in prev_zombies:
                    px, py = prev_zombies[z.id]
                    moved = math.hypot(z.x - px, z.y - py)
                    if moved > P["ZOMBIE_SPEED"] + EPS:
                        note("C5", f"step {s}: zombie {z.id} moved {moved:.2f}")
                        break
            prev_total = total
            prev_zombies = {z.id: (z.x, z.y) for z in world.zombies}
        end_counts = (len(world.humans), len(world.zombies))
    except Exception as e:
        return results + [("RUNTIME", False, f"step() crashed: {e!r}")]

    for cid, message in first_fail.items():
        results.append((cid, message is None, "ok for 100 steps" if message is None else message))

    # The bites relation actually happens
    results.append(("REL bites", end_counts != start_counts,
                    f"(humans, zombies) went from {start_counts} to {end_counts}"))

    # C6: two worlds with the same seed match (stepped side by side)
    try:
        a, b = make(7), make(7)
        for _ in range(50):
            module.step(a)
            module.step(b)

        def snapshot(w):
            return (sorted((round(h.x, 6), round(h.y, 6)) for h in w.humans),
                    sorted((round(z.x, 6), round(z.y, 6)) for z in w.zombies))

        ok = snapshot(a) == snapshot(b)
        results.append(("C6", ok, "same seed, same results" if ok else "same seed gave different results"))
    except Exception as e:
        results.append(("C6", False, f"crashed: {e!r}"))
    return results


# ---------- MAIN ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline/run_checks.py generated/<file>.py")
        sys.exit(2)
    path = sys.argv[1]
    label = os.path.splitext(os.path.basename(path))[0]
    ontology = load_ontology()
    with open(path, encoding="utf-8") as f:
        source = f.read()

    results = static_checks(source, ontology)
    if results[0][1]:  # only run the code if it parses
        module, error = load_module(path)
        if module is None:
            results.append(("IMPORT", False, error))
        else:
            results.append(("IMPORT", True, "imports cleanly"))
            results += runtime_checks(module, ontology)

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nChecks for {path} (ontology version {ontology['version']})")
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"\nScore: {passed}/{len(results)} checks passed")

    os.makedirs("reports", exist_ok=True)
    report = {"file": path, "ontology_version": ontology["version"],
              "passed": passed, "total": len(results),
              "results": [{"check": n, "passed": ok, "detail": d} for n, ok, d in results]}
    report_path = f"reports/{label}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {report_path}")
    sys.stdout.flush()
    os._exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()