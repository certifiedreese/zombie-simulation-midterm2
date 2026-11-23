# ============================================================
# reference_sim.py - Hand-written reference solution
#
# NOT written by the AI. Used only to prove the checker works:
# a correct program should pass every check.
# ============================================================

import math
import random

VISION_RADIUS = 100
TOUCH_DISTANCE = 13
FIGHT_CHANCE = 0.4
HUMAN_SPEED_MIN = 0.5
HUMAN_SPEED_MAX = 1.4
ZOMBIE_SPEED = 1.5


class Agent:
    def __init__(self, id, x, y, speed):
        self.id = id
        self.x = x
        self.y = y
        self.speed = speed


class Human(Agent):
    def __init__(self, id, x, y, speed, dx, dy):
        super().__init__(id, x, y, speed)
        self.dx = dx
        self.dy = dy


class Zombie(Agent):
    def __init__(self, id, x, y):
        super().__init__(id, x, y, ZOMBIE_SPEED)


class World:
    def __init__(self, width, height, rng):
        self.width = width
        self.height = height
        self.humans = []
        self.zombies = []
        self.frame = 0
        self.rng = rng
        self.next_id = 0

    def new_id(self):
        self.next_id += 1
        return self.next_id


def create_world(width, height, num_humans, num_zombies, seed):
    world = World(width, height, random.Random(seed))
    rng = world.rng
    for _ in range(num_humans):
        speed = rng.uniform(HUMAN_SPEED_MIN, HUMAN_SPEED_MAX)
        angle = rng.uniform(0, 2 * math.pi)
        world.humans.append(Human(world.new_id(), rng.uniform(0, width), rng.uniform(0, height),
                                  speed, math.cos(angle) * speed, math.sin(angle) * speed))
    for _ in range(num_zombies):
        world.zombies.append(Zombie(world.new_id(), rng.uniform(0, width), rng.uniform(0, height)))
    return world


def step(world):
    world.frame += 1

    # Humans move and bounce, and are kept inside the world (C1)
    for h in world.humans:
        h.x += h.dx
        h.y += h.dy
        if h.x < 0 or h.x > world.width:
            h.dx = -h.dx
            h.x = min(max(h.x, 0), world.width)
        if h.y < 0 or h.y > world.height:
            h.dy = -h.dy
            h.y = min(max(h.y, 0), world.height)

    # Zombies chase the nearest human in sight, moving at most ZOMBIE_SPEED (C5)
    for z in world.zombies:
        target, best = None, VISION_RADIUS
        for h in world.humans:
            d = math.hypot(h.x - z.x, h.y - z.y)
            if d < best:
                target, best = h, d
        if target is not None and best > 0:
            move = min(ZOMBIE_SPEED, best)
            z.x += (target.x - z.x) / best * move
            z.y += (target.y - z.y) / best * move

    # Fights: each human and each zombie fights at most once per step
    fought, bitten, destroyed, new_zombies = set(), set(), set(), []
    for z in world.zombies:
        for h in world.humans:
            if h.id in fought:
                continue
            if math.hypot(h.x - z.x, h.y - z.y) < TOUCH_DISTANCE:
                fought.add(h.id)
                if world.rng.random() < FIGHT_CHANCE:
                    destroyed.add(z.id)
                else:
                    bitten.add(h.id)
                    new_zombies.append(Zombie(world.new_id(), h.x, h.y))
                break
    world.humans = [h for h in world.humans if h.id not in bitten]
    world.zombies = [z for z in world.zombies if z.id not in destroyed] + new_zombies


def count(world):
    return (len(world.humans), len(world.zombies))  