# DARK CARNIVAL RNG ECOLOGY - v3
# 2D/3D toggle, Auto-run, Menus, Roles (Mystic, Skeptic, Fool, Pirate, etc.)
# Consent Kanban, Spiral Die, Seed Bank, No population cap (physics-limited).

import random
import math
import os
import time
import json
from collections import deque

# ==========================================
# CONSTANTS
# ==========================================
MAP_W, MAP_H = 40, 20          # Size of the world grid
MAX_LOG = 15                  # Max number of log lines
DAY_LENGTH_TICKS = 100
POPULATION_SOFT_LIMIT = 200   # For performance, but not enforced

# Relationship Kanban states
REL_INTERESTED = "INTERESTED"
REL_CURIOUS    = "CURIOUS"
REL_WANT       = "WANT"
REL_COMMITTED  = "COMMITTED"
REL_RIVAL      = "RIVAL"

# Stances
STANCE_DORMANT   = "DORMANT"
STANCE_SEEK      = "SEEK"
STANCE_SOCIAL    = "SOCIAL"
STANCE_RELIGIOUS = "HOLY"
STANCE_DRILL     = "DRILL"
STANCE_FLEE      = "FLEE"

# View modes
VIEW_2D = 1
VIEW_3D = 2
VIEW_FEED = 3

# Role probabilities
ROLE_CHANCES = {
    "NORMAL": 0.6,
    "MYSTIC": 0.05,
    "SKEPTIC": 0.1,
    "FOOL": 0.05,
    "PIRATE": 0.05,
    "KID": 0.05,
    "PREDATOR": 0.05,
    "STORYTELLER": 0.03,
    "CHICKEN": 0.02
}

# Flavor modes (for trickster events)
FLAVOR_NORMAL = "NORMAL"
FLAVOR_PUNK   = "PUNK"
FLAVOR_JUFF   = "JUFF"
FLAVOR_NEED   = "NEED"

# ==========================================
# CONSENT KANBAN
# ==========================================
class ConsentKanban:
    def __init__(self):
        self.awareness = "ECLIPSE"
        self.vibe_bias = 0.0
        self.consent_level = 0.0
        self.mode = "SOVEREIGN"
        self.sub_state = None
        self.local_fungi = 0
        self.distant_dms = 0

    def check_consent(self, required_level):
        if self.consent_level >= required_level:
            return True, "Access Granted."
        else:
            self.vibe_bias -= 0.1
            self._evolve_mode()
            return False, "BLOCKED. Glass Door active."

    def interact(self, interaction_type, is_local=True):
        if is_local:
            self.local_fungi += 1
        else:
            self.distant_dms += 1

        # Awareness shifts
        if self.awareness == "ECLIPSE":
            if self.local_fungi > 1 or self.distant_dms > 1:
                self.awareness = "CRESCENT"
        elif self.awareness == "CRESCENT":
            if self.local_fungi > 3:
                self.awareness = "QUARTER"
        elif self.awareness == "QUARTER":
            if self.vibe_bias > 0.2:
                self.awareness = "GIBBOUS"
        elif self.awareness == "GIBBOUS":
            if self.consent_level > 0.7:
                self.awareness = "FULL"

        if interaction_type == "insult":
            self.vibe_bias -= 0.2
        elif interaction_type == "joke":
            self.vibe_bias += 0.1
        elif interaction_type == "hug":
            success, msg = self.check_consent(0.7)
            if not success:
                return f"INTERACTION FAILED: {msg}"
            else:
                self.vibe_bias += 0.2

        if self.vibe_bias > 0.5 and self.awareness in ["GIBBOUS", "FULL"]:
            self.consent_level = min(1.0, self.consent_level + 0.05)

        self._evolve_mode()
        return f"Interaction logged. Vibe: {self.vibe_bias:.2f}"

    def _evolve_mode(self):
        if self.vibe_bias < -0.4:
            self.mode = "RIVAL"
            self.sub_state = "FULL JUFF" if self.vibe_bias < -0.7 else "OL' EVIL EYE"
        elif self.vibe_bias > 0.4:
            self.mode = "HOMIE"
            hist = self.local_fungi + (self.distant_dms * 2)
            self.sub_state = "ADMIRING" if self.awareness == "FULL" and hist > 10 else "FLIRTY"
        else:
            self.mode = "SOVEREIGN"
            self.sub_state = None

# ==========================================
# BIOME
# ==========================================
class Biome:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.nutrients = [[0.5 for _ in range(h)] for _ in range(w)]
        self.water     = [[0.5 for _ in range(h)] for _ in range(w)]
        self.fungi     = [[0.0 for _ in range(h)] for _ in range(w)]
        self.bacteria  = [[0.0 for _ in range(h)] for _ in range(w)]
        self.altitude  = self._generate_altitude(w, h)

    def _generate_altitude(self, w, h):
        grid = [[random.random() for _ in range(h)] for _ in range(w)]
        for _ in range(3):
            new_grid = [[0 for _ in range(h)] for _ in range(w)]
            for x in range(w):
                for y in range(h):
                    s, c = 0, 0
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = x+dx, y+dy
                            if 0 <= nx < w and 0 <= ny < h:
                                s += grid[nx][ny]
                                c += 1
                    new_grid[x][y] = s / c
            grid = new_grid
        return grid

    def is_sea(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.water[x][y] > 0.6

    def is_mountain(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.altitude[x][y] > 0.7

    def tick(self):
        for x in range(self.w):
            for y in range(self.h):
                # rain
                rain = 0.1 if random.random() < 0.01 else 0.01
                if random.random() < 0.05:
                    self.water[x][y] = min(1.0, self.water[x][y] + rain)
                # evaporation
                evap = 0.01
                self.water[x][y] = max(0.0, self.water[x][y] - evap)
                # fungi
                if self.water[x][y] > 0.6:
                    self.fungi[x][y] = min(1.0, self.fungi[x][y] + 0.01)
                # bacteria
                if self.nutrients[x][y] > 0.6:
                    self.bacteria[x][y] = min(1.0, self.bacteria[x][y] + 0.01)
                # balance
                if self.fungi[x][y] > 0.5 and self.bacteria[x][y] > 0.1:
                    self.bacteria[x][y] *= 0.95
                self.nutrients[x][y] *= 0.999
                if self.bacteria[x][y] > 0.5:
                    self.nutrients[x][y] = min(1.0, self.nutrients[x][y] + 0.002)

# ==========================================
# SPIRAL DIE
# ==========================================
def roll_spiral_die(scale, resonance=0.0):
    half = scale / 2.0
    rx = random.uniform(-half, half)
    ry = random.uniform(-half, half)
    rz = random.uniform(-half, half)
    max_dist = math.sqrt(half**2 + half**2 + half**2)
    dist = math.sqrt(rx**2 + ry**2 + rz**2)
    magnitude = dist / max_dist
    magnitude = min(1.0, magnitude + (resonance * 0.2))
    if magnitude < 0.3:
        outcome = "STASIS"
    elif magnitude < 0.6:
        outcome = "DISCOVERY"
    elif magnitude < 0.85:
        outcome = "TREASURE"
    else:
        outcome = "HAZARD"
    return {'magnitude': magnitude, 'outcome': outcome, 'scale': scale}

# ==========================================
# ENTITY
# ==========================================
class Entity:
    def __init__(self, uid, x, y, role=None):
        self.uid = uid
        self.x = x
        self.y = y
        self.role = role if role else self._assign_role()
        self.energy = 60.0
        self.alive = True
        self.bravery = random.uniform(0.3, 0.7)
        self.curiosity = random.uniform(0.3, 0.7)
        self.treasures = 0
        self.consent_kanban = ConsentKanban()
        self.stance = STANCE_DORMANT
        self.memories = deque(maxlen=5)
        self.long_term_memory = []
        self.genes = {
            'aggression': random.random(),
            'curiosity': self.curiosity,
            'social': random.random(),
            'religiosity': random.random()
        }
        # Special traits
        self.foresight_count = 0
        self.belief = 0.0

    def _assign_role(self):
        r = random.random()
        cum = 0.0
        for role, chance in ROLE_CHANCES.items():
            cum += chance
            if r < cum:
                return role
        return "NORMAL"

    def update(self, biome, engine):
        if not self.alive:
            return
        # Metabolism
        self.energy -= 0.1

        # Role-specific behavior
        if self.role == "MYSTIC":
            self._update_mystic(biome, engine)
        elif self.role == "SKEPTIC":
            self._update_skeptic(biome, engine)
        elif self.role == "FOOL":
            self._update_fool(biome, engine)
        elif self.role == "PIRATE":
            self._update_pirate(biome)
        elif self.role == "KID":
            self._update_kid(biome)
        elif self.role == "PREDATOR":
            self._update_predator(biome, engine)
        elif self.role == "STORYTELLER":
            self._update_storyteller(engine)
        elif self.role == "CHICKEN":
            self._update_chicken(biome)
        else:
            self._update_normal(biome)

        self._move(biome)

        if self.energy <= 0:
            self.alive = False
            engine.add_log(f"Entity {self.uid} expired.")

    # Role-specific update methods
    def _update_mystic(self, biome, engine):
        if random.random() < 0.2:  # extra crystal sight
            # scan for crystals (simplified)
            pass
        if random.random() < 0.01:  # foresight
            self.foresight_count += 1
            engine.add_log(f"Mystic {self.uid} has a vision.")

    def _update_skeptic(self, biome, engine):
        if random.random() < 0.025:  # 2.5% foresight
            self.foresight_count += 1
            engine.add_log(f"Skeptic {self.uid} predicts something.")
        # authoritarian influence could be implemented here

    def _update_fool(self, biome, engine):
        if random.random() < 0.33:
            # can access memory
            pass
        else:
            # cannot access, maybe false memory
            pass

    def _update_pirate(self, biome):
        if biome.is_sea(self.x, self.y):
            self.energy += 0.05  # gain energy at sea
        else:
            self.energy -= 0.05

    def _update_kid(self, biome):
        if random.random() < self.curiosity:
            self.curiosity = min(1.0, self.curiosity + 0.001)

    def _update_predator(self, biome, engine):
        # find nearest kid or normal entity and chase
        pass  # simplified

    def _update_storyteller(self, engine):
        if random.random() < 0.01:
            story = random.choice(["Once upon a time...", "The dice rolled...", "In the depths..."])
            engine.add_log(f"Storyteller {self.uid}: {story}")

    def _update_chicken(self, biome):
        self.curiosity = max(0.0, self.curiosity - 0.001)

    def _update_normal(self, biome):
        pass

    def _move(self, biome):
        if self.stance == STANCE_DORMANT:
            return
        dx, dy = 0, 0
        if self.stance == STANCE_SEEK:
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
        elif self.stance == STANCE_FLEE:
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
        elif self.stance == STANCE_SOCIAL:
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
        elif self.stance == STANCE_RELIGIOUS:
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < biome.w and 0 <= ny < biome.h:
            self.x, self.y = nx, ny
            self.energy -= 0.5

    def interact(self, interaction_type, is_local=True):
        return self.consent_kanban.interact(interaction_type, is_local)

# ==========================================
# GAME ENGINE
# ==========================================
class GameEngine:
    def __init__(self):
        self.biome = Biome(MAP_W, MAP_H)
        self.entities = []
        self.log = deque(maxlen=MAX_LOG)
        self.view = VIEW_2D
        self.global_resonance = 0.0
        self.seed_strain = f"NEVILLE-{random.randint(1000,9999)}"
        self.companion = None
        self.tick_count = 0
        # Ensure at least one mystic and two skeptics
        mystic_count = 0
        skeptic_count = 0
        for i in range(20):
            x = random.randint(0, MAP_W-1)
            y = random.randint(0, MAP_H-1)
            if mystic_count < 1:
                role = "MYSTIC"
                mystic_count += 1
            elif skeptic_count < 2:
                role = "SKEPTIC"
                skeptic_count += 1
            else:
                role = None
            self.entities.append(Entity(i, x, y, role))

    def add_log(self, msg):
        self.log.append(msg)

    def tick(self):
        self.tick_count += 1
        self.biome.tick()
        for e in self.entities:
            e.update(self.biome, self)
        if random.random() < 0.05:
            self.trigger_world_event()
        self.entities = [e for e in self.entities if e.alive]

    def trigger_world_event(self):
        roll = roll_spiral_die(8, self.global_resonance)
        desc = f"The {self.seed_strain} strain shimmers..."
        if roll['outcome'] == "HAZARD":
            desc += " A STORM hits! Energy drains."
            for e in self.entities:
                e.energy -= 5
        elif roll['outcome'] == "TREASURE":
            desc += " A GEMSTONE found!"
            target = random.choice(self.entities)
            target.treasures += 1
            target.energy += 10
        elif roll['outcome'] == "DISCOVERY":
            desc += " New lands discovered."
        else:
            desc += " Winds are calm."
        self.add_log(desc)

    def auto_run(self, n):
        for _ in range(n):
            self.tick()
        self.render()
        self.add_log(f"Auto-ran {n} ticks.")

    def export_seed(self, filename=None):
        if not filename:
            filename = f"{self.seed_strain}.seed"
        data = {
            "strain": self.seed_strain,
            "terrain": self.biome.altitude,
            "water": self.biome.water,
            "resonance": self.global_resonance,
            "entities": []
        }
        for e in self.entities:
            e_data = {
                "uid": e.uid,
                "x": e.x, "y": e.y,
                "role": e.role,
                "energy": e.energy,
                "bravery": e.bravery,
                "curiosity": e.curiosity,
                "consent_kanban": {
                    "awareness": e.consent_kanban.awareness,
                    "vibe_bias": e.consent_kanban.vibe_bias,
                    "consent_level": e.consent_kanban.consent_level,
                    "mode": e.consent_kanban.mode,
                    "sub_state": e.consent_kanban.sub_state,
                    "local_fungi": e.consent_kanban.local_fungi,
                    "distant_dms": e.consent_kanban.distant_dms
                }
            }
            data["entities"].append(e_data)
        try:
            with open(filename, 'w') as f:
                json.dump(data, f)
            self.add_log(f"Seed exported: {filename}")
        except Exception as e:
            self.add_log(f"Export failed: {e}")

    def import_seed(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.seed_strain = data["strain"] + "-F2"
            self.biome.altitude = data["terrain"]
            self.biome.water = data["water"]
            self.global_resonance = data["resonance"]
            self.entities = []
            for e_data in data["entities"]:
                e = Entity(e_data["uid"], e_data["x"], e_data["y"], e_data["role"])
                e.energy = e_data["energy"]
                e.bravery = e_data["bravery"]
                e.curiosity = e_data["curiosity"]
                ck = e.consent_kanban
                ck_data = e_data["consent_kanban"]
                ck.awareness = ck_data["awareness"]
                ck.vibe_bias = ck_data["vibe_bias"]
                ck.consent_level = ck_data["consent_level"]
                ck.mode = ck_data["mode"]
                ck.sub_state = ck_data["sub_state"]
                ck.local_fungi = ck_data["local_fungi"]
                ck.distant_dms = ck_data["distant_dms"]
                self.entities.append(e)
            self.add_log(f"Imported strain: {data['strain']}. World mutated.")
        except Exception as e:
            self.add_log(f"Import failed: {e}")

    def render_2d(self):
        buffer = []
        for y in range(self.biome.h):
            row = ""
            for x in range(self.biome.w):
                char = " "
                for e in self.entities:
                    if e.x == x and e.y == y and e.alive:
                        char = e.role[0]
                        if self.companion and e.uid == self.companion.uid:
                            char = "@"
                        break
                if char == " ":
                    if self.biome.is_mountain(x, y):
                        char = "^"
                    elif self.biome.is_sea(x, y):
                        char = "~"
                    else:
                        char = "."
                row += char
            buffer.append(row)
        print("\n".join(buffer))

    def render_3d(self):
        try:
            cols, rows = os.get_terminal_size()
        except:
            cols, rows = 80, 24
        screen_h = rows - 10
        screen_w = cols
        if screen_h <= 0 or screen_w <= 0:
            screen_h, screen_w = 20, 80

        # Camera position
        cam_x = MAP_W / 2
        cam_y = MAP_H / 2
        cam_z = 20

        # Collect points with distance from camera
        points = []
        step = 2  # sample every 2nd tile to reduce clutter
        for x in range(0, self.biome.w, step):
            for y in range(0, self.biome.h, step):
                z = self.biome.altitude[x][y] * 10
                char = "^" if self.biome.is_mountain(x, y) else ("~" if self.biome.is_sea(x, y) else ".")
                dist = math.sqrt((x-cam_x)**2 + (y-cam_y)**2 + (z-cam_z)**2)
                points.append((dist, x, y, z, char, "terrain"))
        for e in self.entities:
            if e.alive:
                z = self.biome.altitude[e.x][e.y] * 10 + 0.5
                char = e.role[0]
                if self.companion and e.uid == self.companion.uid:
                    char = "@"
                dist = math.sqrt((e.x-cam_x)**2 + (e.y-cam_y)**2 + (z-cam_z)**2)
                points.append((dist, e.x, e.y, z, char, "entity"))

        # Sort by distance descending (far to near)
        points.sort(key=lambda p: p[0], reverse=True)

        # Isometric projection
        scale = 2.0
        iso_x = math.cos(math.radians(30)) * scale
        iso_y = math.sin(math.radians(30)) * scale

        # Project all points to get bounds
        proj = []
        for _, x, y, z, char, _ in points:
            sx = (x - y) * iso_x
            sy = (x + y) * iso_y - z
            proj.append((sx, sy, char))

        if proj:
            min_sx = min(p[0] for p in proj)
            max_sx = max(p[0] for p in proj)
            min_sy = min(p[1] for p in proj)
            max_sy = max(p[1] for p in proj)
        else:
            min_sx = max_sx = min_sy = max_sy = 0

        range_x = max_sx - min_sx + 1
        range_y = max_sy - min_sy + 1
        if range_x == 0: range_x = 1
        if range_y == 0: range_y = 1
        scale_x = (screen_w - 1) / range_x
        scale_y = (screen_h - 1) / range_y
        scale = min(scale_x, scale_y)

        offset_x = -min_sx
        offset_y = -min_sy

        # Create buffer
        buffer = [[' ' for _ in range(screen_w)] for _ in range(screen_h)]

        # Place characters
        for sx, sy, char in proj:
            grid_x = int((sx + offset_x) * scale)
            grid_y = int((sy + offset_y) * scale)
            if 0 <= grid_x < screen_w and 0 <= grid_y < screen_h:
                buffer[grid_y][grid_x] = char

        # Print buffer
        for row in buffer:
            print(''.join(row))

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f":: DARK CARNIVAL RNG :: STRAIN: {self.seed_strain}")
        print(f":: TICK: {self.tick_count} :: RESONANCE: {self.global_resonance:.2f} :: ENTITIES: {len(self.entities)}")
        print(f":: VIEW: {'2D' if self.view == VIEW_2D else ('3D' if self.view == VIEW_3D else 'FEED')}")
        print("-" * 60)

        if self.view == VIEW_2D:
            self.render_2d()
        elif self.view == VIEW_3D:
            self.render_3d()
        elif self.view == VIEW_FEED:
            for line in self.log:
                print(line)

        if self.companion:
            e = self.companion
            k = e.consent_kanban
            print(f"\n:: COMPANION :: {e.role} ID:{e.uid}")
            print(f"  Energy: {e.energy:.1f} | Bravery: {e.bravery:.2f} | Curiosity: {e.curiosity:.2f}")
            print(f"  Consent: {k.consent_level*100:.0f}% | Vibe: {k.vibe_bias:.2f} ({k.mode})")

        print("-" * 60)
        print("[Space] Tick | [v] View (2D/3D/Feed) | [a] Auto-run (ticks) | [m] Menu")
        print("[c] Connect Entity | [t] Talk | [h] Hug | [x] Export | [i] Import | [q] Quit")
        print(">> ", end='')

    def menu(self):
        while True:
            print("\n--- MENU ---")
            print("1. Resume")
            print("2. Save Game")
            print("3. Load Game")
            print("4. Quit")
            choice = input("Select: ").strip()
            if choice == '1':
                return True
            elif choice == '2':
                filename = input("Save filename: ")
                self.export_seed(filename)
            elif choice == '3':
                filename = input("Load filename: ")
                self.import_seed(filename)
            elif choice == '4':
                return False
            else:
                print("Invalid choice.")

    def run(self):
        print("Welcome to the Dark Carnival RNG Ecology.")
        while True:
            self.render()
            cmd = input().strip().lower()
            if cmd == 'q':
                break
            elif cmd == ' ':
                self.tick()
            elif cmd == 'v':
                if self.view == VIEW_2D:
                    self.view = VIEW_3D
                elif self.view == VIEW_3D:
                    self.view = VIEW_FEED
                else:
                    self.view = VIEW_2D
            elif cmd == 'a':
                try:
                    n = int(input("How many ticks to auto-run? "))
                    self.auto_run(n)
                except ValueError:
                    self.add_log("Invalid number.")
            elif cmd == 'm':
                if not self.menu():
                    break
            elif cmd == 'c':
                cx, cy = MAP_W//2, MAP_H//2
                alive = [e for e in self.entities if e.alive]
                if alive:
                    nearest = min(alive, key=lambda e: abs(e.x-cx)+abs(e.y-cy))
                    self.companion = nearest
                    self.add_log(f"Connected to {nearest.role} {nearest.uid}.")
                else:
                    self.add_log("No entities alive.")
            elif cmd == 't':
                if self.companion:
                    res = self.companion.interact("joke", is_local=True)
                    self.add_log(f"You TALK to {self.companion.uid}. {res}")
                else:
                    self.add_log("No companion connected.")
            elif cmd == 'h':
                if self.companion:
                    res = self.companion.interact("hug", is_local=True)
                    self.add_log(f"You HUG {self.companion.uid}. {res}")
                else:
                    self.add_log("No companion connected.")
            elif cmd == 'x':
                filename = input("Filename: ")
                self.export_seed(filename)
            elif cmd == 'i':
                filename = input("Filename: ")
                self.import_seed(filename)
            else:
                self.add_log("Unknown command.")

if __name__ == "__main__":
    game = GameEngine()
    game.run()
```