import random
import time

# Adjust these settings to change the simulation.
WIDTH = 28
HEIGHT = 14
STARTING_HUMANS = 18
STARTING_ZOMBIES = 3
MAX_TURNS = 300
SECONDS_PER_TURN = 0.25


class Actor:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def distance(a, b):
    return abs(a.x - b.x) + abs(a.y - b.y)


def valid_moves(actor):
    """Return positions the actor can move to, including staying still."""
    return [
        (x, y)
        for x, y in [
            (actor.x, actor.y),
            (actor.x + 1, actor.y),
            (actor.x - 1, actor.y),
            (actor.x, actor.y + 1),
            (actor.x, actor.y - 1),
        ]
        if 0 <= x < WIDTH and 0 <= y < HEIGHT
    ]


def move_human(human, zombies):
    """Move away from the nearest zombie, with random tie-breaking."""
    if not zombies:
        return

    moves = valid_moves(human)
    best_distance = max(
        min(abs(x - z.x) + abs(y - z.y) for z in zombies)
        for x, y in moves
    )
    choices = [
        (x, y)
        for x, y in moves
        if min(abs(x - z.x) + abs(y - z.y) for z in zombies) == best_distance
    ]
    human.x, human.y = random.choice(choices)


def move_zombie(zombie, humans):
    """Move one step toward the nearest human."""
    if not humans:
        return

    target = min(humans, key=lambda human: distance(zombie, human))
    moves = valid_moves(zombie)
    best_distance = min(
        abs(x - target.x) + abs(y - target.y) for x, y in moves
    )
    choices = [
        (x, y)
        for x, y in moves
        if abs(x - target.x) + abs(y - target.y) == best_distance
    ]
    zombie.x, zombie.y = random.choice(choices)


def draw(humans, zombies, turn, infected_count):
    grid = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]

    for actor, symbol in [(h, "H") for h in humans] + [(z, "Z") for z in zombies]:
        current = grid[actor.y][actor.x]
        grid[actor.y][actor.x] = symbol if current == "." else "@"

    print("\033[2J\033[H", end="")  # Clear and redraw in most terminals.
    print(f"Turn: {turn}   Humans: {len(humans)}   Zombies: {len(zombies)}   Infected: {infected_count}")
    print("+" + "-" * WIDTH + "+")
    for row in grid:
        print("|" + "".join(row) + "|")
    print("+" + "-" * WIDTH + "+")
    print("H = human   Z = zombie   @ = overlapping actors")


def run_simulation():
    humans = [
        Actor(random.randrange(WIDTH), random.randrange(HEIGHT))
        for _ in range(STARTING_HUMANS)
    ]
    zombies = [
        Actor(random.randrange(WIDTH), random.randrange(HEIGHT))
        for _ in range(STARTING_ZOMBIES)
    ]
    infected_count = 0

    for turn in range(1, MAX_TURNS + 1):
        # Humans sometimes attack a zombie in the same or an adjacent cell.
        for human in list(humans):
            nearby = [z for z in zombies if distance(human, z) <= 1]
            if nearby and random.random() < 0.35:
                target = min(nearby, key=lambda z: distance(human, z))
                if random.random() < 0.50:
                    zombies.remove(target)
                continue
            move_human(human, zombies)

        # Zombies pursue humans. A human caught on the same cell is infected.
        for zombie in list(zombies):
            if not humans:
                break
            move_zombie(zombie, humans)
            caught = next(
                (human for human in humans if human.x == zombie.x and human.y == zombie.y),
                None,
            )
            if caught is not None:
                humans.remove(caught)
                zombies.append(Actor(caught.x, caught.y))
                infected_count += 1

        draw(humans, zombies, turn, infected_count)

        if not humans or not zombies:
            break
        time.sleep(SECONDS_PER_TURN)

    if not humans:
        print("The zombies have infected everyone!")
    elif not zombies:
        print("The humans defeated all the zombies!")
    else:
        print(f"Simulation stopped after {MAX_TURNS} turns.")


if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
