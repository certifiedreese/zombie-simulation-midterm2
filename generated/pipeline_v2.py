import math
import random
from dataclasses import dataclass, field


VISION_RADIUS = 100
TOUCH_DISTANCE = 13
FIGHT_CHANCE = 0.5
HUMAN_SPEED_MIN = 0.5
HUMAN_SPEED_MAX = 1.4
ZOMBIE_SPEED = 1.5


@dataclass
class Agent:
    id: int
    x: float
    y: float
    speed: float


@dataclass
class Human(Agent):
    dx: float
    dy: float


@dataclass
class Zombie(Agent):
    pass


@dataclass
class World:
    width: float
    height: float
    humans: list[Human] = field(default_factory=list)
    zombies: list[Zombie] = field(default_factory=list)
    frame: int = 0
    rng: random.Random = field(default_factory=random.Random)


def create_world(width, height, num_humans, num_zombies, seed):
    world = World(
        width=float(width),
        height=float(height),
        rng=random.Random(seed),
    )

    agent_id = 0

    for _ in range(num_humans):
        angle = world.rng.uniform(0.0, 2.0 * math.pi)
        world.humans.append(
            Human(
                id=agent_id,
                x=world.rng.uniform(0.0, world.width),
                y=world.rng.uniform(0.0, world.height),
                speed=world.rng.uniform(HUMAN_SPEED_MIN, HUMAN_SPEED_MAX),
                dx=math.cos(angle),
                dy=math.sin(angle),
            )
        )
        agent_id += 1

    for _ in range(num_zombies):
        world.zombies.append(
            Zombie(
                id=agent_id,
                x=world.rng.uniform(0.0, world.width),
                y=world.rng.uniform(0.0, world.height),
                speed=ZOMBIE_SPEED,
            )
        )
        agent_id += 1

    return world


def step(world):
    for human in world.humans:
        human.x += human.dx * human.speed
        human.y += human.dy * human.speed

        if world.width <= 0.0:
            human.x = 0.0
            human.dx = 0.0
        else:
            while human.x < 0.0 or human.x > world.width:
                if human.x < 0.0:
                    human.x = -human.x
                    human.dx = -human.dx
                elif human.x > world.width:
                    human.x = 2.0 * world.width - human.x
                    human.dx = -human.dx

        if world.height <= 0.0:
            human.y = 0.0
            human.dy = 0.0
        else:
            while human.y < 0.0 or human.y > world.height:
                if human.y < 0.0:
                    human.y = -human.y
                    human.dy = -human.dy
                elif human.y > world.height:
                    human.y = 2.0 * world.height - human.y
                    human.dy = -human.dy

    for zombie in world.zombies:
        zombie.speed = ZOMBIE_SPEED
        nearest_human = None
        nearest_distance_squared = VISION_RADIUS * VISION_RADIUS

        for human in world.humans:
            dx = human.x - zombie.x
            dy = human.y - zombie.y
            distance_squared = dx * dx + dy * dy
            if distance_squared <= nearest_distance_squared:
                if (
                    nearest_human is None
                    or distance_squared < nearest_distance_squared
                ):
                    nearest_human = human
                    nearest_distance_squared = distance_squared

        if nearest_human is not None:
            dx = nearest_human.x - zombie.x
            dy = nearest_human.y - zombie.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0.0:
                movement = min(ZOMBIE_SPEED, distance)
                zombie.x += dx / distance * movement
                zombie.y += dy / distance * movement

        zombie.x = min(max(zombie.x, 0.0), world.width)
        zombie.y = min(max(zombie.y, 0.0), world.height)

    humans_who_fought = set()
    zombies_to_remove = set()
    humans_to_remove = set()
    new_zombies = []

    for zombie in list(world.zombies):
        nearest_human = None
        nearest_distance_squared = TOUCH_DISTANCE * TOUCH_DISTANCE

        for human in world.humans:
            if human.id in humans_who_fought:
                continue

            dx = human.x - zombie.x
            dy = human.y - zombie.y
            distance_squared = dx * dx + dy * dy

            if distance_squared < nearest_distance_squared:
                nearest_human = human
                nearest_distance_squared = distance_squared

        if nearest_human is None:
            continue

        humans_who_fought.add(nearest_human.id)

        if world.rng.random() < FIGHT_CHANCE:
            zombies_to_remove.add(zombie.id)
        else:
            humans_to_remove.add(nearest_human.id)
            existing_ids = [
                agent.id for agent in world.humans + world.zombies
            ]
            existing_ids.extend(agent.id for agent in new_zombies)
            new_id = max(existing_ids, default=-1) + 1
            new_zombies.append(
                Zombie(
                    id=new_id,
                    x=nearest_human.x,
                    y=nearest_human.y,
                    speed=ZOMBIE_SPEED,
                )
            )

    world.humans = [
        human
        for human in world.humans
        if human.id not in humans_to_remove
    ]
    world.zombies = [
        zombie
        for zombie in world.zombies
        if zombie.id not in zombies_to_remove
    ]
    world.zombies.extend(new_zombies)

    for human in world.humans:
        human.x = min(max(human.x, 0.0), world.width)
        human.y = min(max(human.y, 0.0), world.height)

    for zombie in world.zombies:
        zombie.x = min(max(zombie.x, 0.0), world.width)
        zombie.y = min(max(zombie.y, 0.0), world.height)
        zombie.speed = ZOMBIE_SPEED

    world.frame += 1


def count(world):
    return len(world.humans), len(world.zombies)
