import pygame
import random
import math
import numpy as np
import pickle # Для збереження/завантаження
import time   # Для логування часу
from abc import ABC, abstractmethod # <--- Імпортуємо необхідне для абстрактних класів

# --- Налаштування Pygame та Симуляції ---
pygame.init()
WIDTH, HEIGHT = 1000, 750
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Розширена Еволюційна Симуляція (Pygame)")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 26)
INFO_FONT = pygame.font.SysFont(None, 22)

# --- Глобальні Параметри ---
BG_COLOR = (10, 10, 20)
INFO_PANEL_COLOR = (40, 40, 50)
INFO_TEXT_COLOR = (230, 230, 230)
SELECTION_COLOR = (255, 255, 0)
OBSTACLE_COLOR = (100, 100, 100)
PREDATOR_COLOR = (255, 50, 50)
FOOD_COLOR = (0, 255, 0)
CREATURE_BASE_COLOR_G = 50 # <--- Визначено тут

# --- Параметри Істот ---
INITIAL_CREATURES = 20
MAX_CREATURES = 100
FOOD_COUNT = 100
FOOD_ENERGY = 100
CREATURE_INITIAL_ENERGY = 100
CREATURE_ENERGY_DECAY = 0.15
CREATURE_MOVE_COST = 0.5
CREATURE_REPRODUCTION_THRESHOLD = 100
CREATURE_REPRODUCTION_READY_THRESHOLD = 100
CREATURE_REPRODUCTION_COST = 100
CREATURE_MATING_COOLDOWN = 1.0
CREATURE_MAX_AGE = 50.0
CREATURE_MIN_SPEED, CREATURE_MAX_SPEED = 0.5, 7.0
CREATURE_MIN_SENSE, CREATURE_MAX_SENSE = 10, 100
CREATURE_MUTATION_RATE = 0.5
CREATURE_MUTATION_STRENGTH = 0.5
CREATURE_MATING_RANGE = 15
CREATURE_SEPARATION_RADIUS = 12
CREATURE_SEPARATION_FORCE = 1.5
CREATURE_RADIUS = 5 # <--- Визначено тут

# --- Параметри Хижаків ---
INITIAL_PREDATORS = 3
MAX_PREDATORS = 15
PREDATOR_INITIAL_ENERGY = 150
PREDATOR_ENERGY_DECAY = 0.12
PREDATOR_MOVE_COST = 0.1
PREDATOR_REPRODUCTION_THRESHOLD = 250
PREDATOR_REPRODUCTION_READY_THRESHOLD = 200
PREDATOR_REPRODUCTION_COST = 120
PREDATOR_MATING_COOLDOWN = 8.0
PREDATOR_HUNT_ENERGY_GAIN = 120
PREDATOR_MAX_AGE = 50.0
PREDATOR_MIN_SPEED, PREDATOR_MAX_SPEED = 0.5, 5.0
PREDATOR_MIN_SENSE, PREDATOR_MAX_SENSE = 20, 150
PREDATOR_MUTATION_RATE = 0.1
PREDATOR_MUTATION_STRENGTH = 0.2
PREDATOR_SEPARATION_RADIUS = 18
PREDATOR_SEPARATION_FORCE = 0.5
PREDATOR_RADIUS = 7 # <--- Визначено тут

# --- Параметри Світу ---
NUM_OBSTACLES = 5
OBSTACLE_MIN_SIZE = 25
OBSTACLE_MAX_SIZE = 50

# --- Відстеження Поколінь та Статистика ---
max_creature_generation = 0
max_predator_generation = 0
history_time = []
history_creature_pop = []
history_predator_pop = []
history_avg_creature_speed = []
history_avg_creature_sense = []
history_avg_predator_speed = []
history_avg_predator_sense = []
simulation_time = 0.0
log_interval = 1.0
last_log_time = -log_interval

# --- Допоміжні Функції ---
# ... (distance_sq, normalize_vec, clamp, crossover_genes залишаються без змін) ...
def distance_sq(p1, p2):
    return (p1 - p2).length_squared()

def normalize_vec(vec):
    if vec.length_squared() > 0:
        try:
            return vec.normalize()
        except ValueError: # Може виникнути, якщо довжина дуже близька до нуля
             return pygame.Vector2(0, 0)
    return pygame.Vector2(0, 0)

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def crossover_genes(genes1, genes2):
    child_genes = {}
    child_genes['speed'] = genes1['speed'] if random.random() < 0.5 else genes2['speed']
    child_genes['sense'] = genes1['sense'] if random.random() < 0.5 else genes2['sense']
    return child_genes

# --- Класи ---

class Food:
    def __init__(self, obstacles):
        self.radius = 3
        while True:
            # Використовуємо глобальні константи
            self.pos = pygame.Vector2(random.randint(self.radius, WIDTH - self.radius),
                                      random.randint(self.radius, HEIGHT - self.radius))
            self.rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius,
                                      self.radius * 2, self.radius * 2)
            if not obstacles or not any(obs.rect.colliderect(self.rect) for obs in obstacles):
                break
        self.color = FOOD_COLOR

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos, self.radius)

class Obstacle:
    def __init__(self):
        size = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE)
        # Використовуємо глобальні константи
        x = random.randint(0, WIDTH - size)
        y = random.randint(0, HEIGHT - size)
        self.rect = pygame.Rect(x, y, size, size)
        self.color = OBSTACLE_COLOR

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# --- БАЗОВИЙ КЛАС АГЕНТА ---
class Agent(ABC): # <--- Успадковуємо від ABC
    def __init__(self, x, y, radius, color, initial_energy, max_age, min_speed, max_speed, min_sense, max_sense, generation=0):
        self.pos = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.energy = initial_energy
        self.max_age = max_age
        self.age = 0.0
        self.generation = generation
        self.is_dead = False
        # Використовуємо self.radius, який вже встановлено
        self.rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        self.direction = normalize_vec(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)))

        self.genes = {
            'speed': random.uniform(min_speed, max_speed),
            'sense': random.uniform(min_sense, max_sense)
        }
        self.min_speed, self.max_speed = min_speed, max_speed
        self.min_sense, self.max_sense = min_sense, max_sense

        self.ready_to_mate = False
        self.mating_cooldown_timer = 0.0

    def update_basic_state(self, dt):
        if self.is_dead: return True
        self.age += dt
        self.energy -= self.get_energy_decay_rate() * dt

        if self.mating_cooldown_timer > 0:
            self.mating_cooldown_timer -= dt
            self.ready_to_mate = False
        elif self.energy >= self.get_reproduction_ready_threshold():
             self.ready_to_mate = True
        else:
             self.ready_to_mate = False

        if self.energy <= 0 or self.age >= self.max_age:
            self.is_dead = True
            return True
        return False

    def check_obstacle_collision(self, obstacles):
        if self.is_dead: return False
        if not obstacles: return False # Додано перевірку на випадок відсутності перешкод
        for obs in obstacles:
            if self.rect.colliderect(obs.rect):
                self.is_dead = True
                return True
        return False

    def apply_movement(self, dt, move_direction, current_speed, energy_cost_multiplier=1.0):
        if self.is_dead or move_direction.length_squared() == 0: return

        move_vector = move_direction * current_speed * dt * 50
        self.pos += move_vector
        # Використовуємо self.radius
        self.rect.center = self.pos

        # Використовуємо глобальні константи
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)
        self.rect.center = self.pos

        energy_cost = self.get_move_cost() * current_speed * energy_cost_multiplier * dt
        self.energy -= energy_cost

    # --- Використання @abstractmethod ---
    @abstractmethod
    def get_energy_decay_rate(self):
        pass # Видалено недійсне ключове слово 'abstract'

    @abstractmethod
    def get_move_cost(self):
        pass # Видалено недійсне ключове слово 'abstract'

    @abstractmethod
    def get_reproduction_ready_threshold(self):
        pass # Видалено недійсне ключове слово 'abstract'
    # -----------------------------------

    def draw(self, surface, is_selected=False):
        if self.is_dead: return
        sense_radius_val = self.genes['sense']
        # Запобігання помилки, якщо радіус = 0
        if sense_radius_val > 0:
            sense_surface = pygame.Surface((sense_radius_val * 2, sense_radius_val * 2), pygame.SRCALPHA)
            pygame.draw.circle(sense_surface, (*self.color[:3], 30), (sense_radius_val, sense_radius_val), int(sense_radius_val)) # Використовуємо перші 3 компоненти кольору
            try:
                surface.blit(sense_surface, self.pos - pygame.Vector2(sense_radius_val, sense_radius_val))
            except TypeError: # Може виникнути, якщо pos має невірний тип під час ініціалізації
                 pass

        pygame.draw.circle(surface, self.color, self.pos, self.radius)
        if is_selected:
            pygame.draw.circle(surface, SELECTION_COLOR, self.pos, self.radius + 2 + (self.radius // 3), 2)

    def is_clicked(self, mouse_pos):
        # Додано перевірку на тип mouse_pos
        if not isinstance(mouse_pos, pygame.Vector2):
             try:
                 mouse_pos = pygame.Vector2(mouse_pos)
             except: return False # Не вдалося конвертувати
        return not self.is_dead and distance_sq(self.pos, mouse_pos) <= self.radius**2

# --- КЛАС ІСТОТИ ---
class Creature(Agent):
    def __init__(self, obstacles, pos=None, genes=None, parent_generation=None):
        # Використовуємо глобальні константи
        super().__init__(pos.x if pos else random.uniform(CREATURE_RADIUS, WIDTH - CREATURE_RADIUS),
                         pos.y if pos else random.uniform(CREATURE_RADIUS, HEIGHT - CREATURE_RADIUS),
                         CREATURE_RADIUS, # Передаємо радіус
                         (0,0,0), # Тимчасовий колір
                         CREATURE_INITIAL_ENERGY, CREATURE_MAX_AGE,
                         CREATURE_MIN_SPEED, CREATURE_MAX_SPEED,
                         CREATURE_MIN_SENSE, CREATURE_MAX_SENSE,
                         parent_generation + 1 if parent_generation is not None else 0)

        self.obstacles = obstacles

        if genes:
            self.genes = genes
            if random.random() < CREATURE_MUTATION_RATE:
                mutation = (random.random() * 2 - 1) * CREATURE_MUTATION_STRENGTH * self.genes['speed']
                self.genes['speed'] = clamp(self.genes['speed'] + mutation, self.min_speed, self.max_speed)
            if random.random() < CREATURE_MUTATION_RATE:
                 mutation = (random.random() * 2 - 1) * CREATURE_MUTATION_STRENGTH * self.genes['sense']
                 self.genes['sense'] = clamp(self.genes['sense'] + mutation, self.min_sense, self.max_sense)

        if pos is None:
             while True:
                # Використовуємо self.radius, встановлений у super().__init__
                self.pos = pygame.Vector2(random.randint(self.radius, WIDTH - self.radius),
                                          random.randint(self.radius, HEIGHT - self.radius))
                self.rect.center = self.pos
                if not obstacles or not any(obs.rect.colliderect(self.rect) for obs in self.obstacles):
                    break
        else:
             self.pos = pygame.Vector2(pos.x + random.uniform(-10, 10), pos.y + random.uniform(-10, 10))
             self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
             self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)
             self.rect.center = self.pos

        self.update_color()

        self.target_food_obj = None
        self.target_partner = None
        self.mating_partner = None

    def update_color(self):
        r = int(np.interp(self.genes['speed'], [self.min_speed, self.max_speed], [50, 255]))
        b = int(np.interp(self.genes['sense'], [self.min_sense, self.max_sense], [50, 255]))
        # Використовуємо глобальну константу CREATURE_BASE_COLOR_G
        self.color = (clamp(r,0,255), CREATURE_BASE_COLOR_G, clamp(b,0,255))

    # --- Реалізація абстрактних методів ---
    def get_energy_decay_rate(self): return CREATURE_ENERGY_DECAY
    def get_move_cost(self): return CREATURE_MOVE_COST
    def get_reproduction_ready_threshold(self): return CREATURE_REPRODUCTION_READY_THRESHOLD
    # ------------------------------------

    def update(self, dt, food_list, creature_list, predator_list):
        if self.update_basic_state(dt): return
        if self.check_obstacle_collision(self.obstacles): return

        sense_radius_sq = self.genes['sense']**2
        move_direction = pygame.Vector2(0, 0)
        current_speed = self.genes['speed']
        energy_mult = 1.0
        evading = False
        mating_attempt = False

        # 1. Ухилення від хижаків
        closest_predator, predator_dist_sq = self.find_closest_agent(predator_list, sense_radius_sq)
        if closest_predator:
            evade_vector = self.pos - closest_predator.pos
            if evade_vector.length_squared() > 0:
                move_direction = normalize_vec(evade_vector)
                current_speed *= 1.2
                energy_mult = 1.5
                evading = True
                self.target_food_obj = None
                self.target_partner = None
                self.mating_partner = None

        # 2. Пошук партнера / Спарювання
        if not evading and self.ready_to_mate:
            if self.mating_partner and not self.mating_partner.is_dead and self.mating_partner.ready_to_mate:
                 partner_dist_sq = distance_sq(self.pos, self.mating_partner.pos)
                 if partner_dist_sq < CREATURE_MATING_RANGE**2:
                     if id(self) < id(self.mating_partner):
                        child_genes = crossover_genes(self.genes, self.mating_partner.genes)
                        request_reproduction(self, self.mating_partner, child_genes)
                     self.mating_cooldown_timer = CREATURE_MATING_COOLDOWN
                     self.mating_partner.mating_cooldown_timer = CREATURE_MATING_COOLDOWN
                     self.ready_to_mate = False
                     self.mating_partner.ready_to_mate = False
                     self.mating_partner.mating_partner = None
                     self.mating_partner = None
                     mating_attempt = True
                     move_direction = pygame.Vector2(0, 0)
                 elif partner_dist_sq < sense_radius_sq:
                      target_vector = self.mating_partner.pos - self.pos
                      move_direction = normalize_vec(target_vector)
                      mating_attempt = True
                 else:
                      self.mating_partner = None
            else:
                self.mating_partner = None
                # Шукаємо лише серед тих, хто теж шукає або не має партнера
                potential_partners = [c for c in creature_list if c != self and c.ready_to_mate and (not c.mating_partner or c.mating_partner == self)]
                closest_partner, partner_dist_sq = self.find_closest_agent(potential_partners, sense_radius_sq)

                if closest_partner:
                    self.target_partner = closest_partner
                    # Спробуємо "домовитись" про спарювання
                    # Якщо інший теж шукає або не має цілі кращої
                    if not closest_partner.mating_partner or closest_partner.target_partner == self:
                         self.mating_partner = closest_partner
                         closest_partner.mating_partner = self # Взаємне призначення
                         target_vector = self.target_partner.pos - self.pos
                         move_direction = normalize_vec(target_vector)
                         mating_attempt = True
                    else: # Партнер зайнятий
                        self.target_partner = None

                else:
                    self.target_partner = None

        # 3. Пошук їжі
        if not evading and not mating_attempt:
            if self.target_food_obj and self.target_food_obj in food_list:
                food_dist_sq = distance_sq(self.pos, self.target_food_obj.pos)
                # Використовуємо радіус поточного агента self.radius
                if food_dist_sq < (self.radius + self.target_food_obj.radius)**2:
                    self.eat(self.target_food_obj)
                    self.target_food_obj = None
                elif food_dist_sq < sense_radius_sq:
                     target_vector = self.target_food_obj.pos - self.pos
                     move_direction = normalize_vec(target_vector)
                else:
                    self.target_food_obj = None
            else:
                self.target_food_obj = None
                # Перевіряємо, чи список їжі не порожній
                if food_list:
                     closest_food, food_dist_sq = self.find_closest_agent(food_list, sense_radius_sq)
                     if closest_food:
                         self.target_food_obj = closest_food
                         target_vector = self.target_food_obj.pos - self.pos
                         move_direction = normalize_vec(target_vector)

        # 4. Уникнення скупчення (Separation)
        separation_vector = pygame.Vector2(0, 0)
        neighbors_count = 0
        if creature_list: # Перевіряємо, чи список істот не порожній
             for other in creature_list:
                 if other != self and not other.is_dead:
                     dist_sq = distance_sq(self.pos, other.pos)
                     if 0 < dist_sq < CREATURE_SEPARATION_RADIUS**2:
                         diff = self.pos - other.pos
                         # Вага обернено пропорційна квадрату відстані
                         separation_vector += diff / max(dist_sq, 0.1) # Уникаємо ділення на нуль
                         neighbors_count += 1
        if neighbors_count > 0:
             separation_vector /= neighbors_count
             separation_vector = normalize_vec(separation_vector)
             if move_direction.length_squared() > 0:
                  # Змішуємо напрямки, можливо, зважено
                  combined_direction = move_direction * 0.8 + separation_vector * CREATURE_SEPARATION_FORCE * 0.5
                  move_direction = normalize_vec(combined_direction)
             else:
                  move_direction = separation_vector

        # 5. Випадковий рух
        if not evading and not mating_attempt and not self.target_food_obj and move_direction.length_squared() == 0:
            if random.random() < 0.05:
                self.direction = normalize_vec(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)))
            if self.direction.length_squared() == 0:
                 self.direction = normalize_vec(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)))
            move_direction = self.direction

        self.apply_movement(dt, move_direction, current_speed, energy_mult)

    def find_closest_agent(self, agent_list, sense_radius_sq):
        closest_agent = None
        min_dist_sq = sense_radius_sq
        if not agent_list: return None, sense_radius_sq # Повертаємо None, якщо список порожній

        for agent in agent_list:
            if agent == self: continue
            if hasattr(agent, 'is_dead') and agent.is_dead: continue
            d_sq = distance_sq(self.pos, agent.pos)
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest_agent = agent
        return closest_agent, min_dist_sq

    def eat(self, food_item):
        if not self.is_dead:
            self.energy += FOOD_ENERGY
            if food_item not in food_to_remove_global:
                 food_to_remove_global.append(food_item)
            if self.target_food_obj == food_item:
                self.target_food_obj = None

# --- КЛАС ХИЖАКА ---
class Predator(Agent):
    def __init__(self, obstacles, pos=None, genes=None, parent_generation=None):
         # Використовуємо глобальні константи
         super().__init__(pos.x if pos else random.uniform(PREDATOR_RADIUS, WIDTH - PREDATOR_RADIUS),
                         pos.y if pos else random.uniform(PREDATOR_RADIUS, HEIGHT - PREDATOR_RADIUS),
                         PREDATOR_RADIUS, # Передаємо радіус
                         PREDATOR_COLOR,
                         PREDATOR_INITIAL_ENERGY, PREDATOR_MAX_AGE,
                         PREDATOR_MIN_SPEED, PREDATOR_MAX_SPEED,
                         PREDATOR_MIN_SENSE, PREDATOR_MAX_SENSE,
                         parent_generation + 1 if parent_generation is not None else 0)

         self.obstacles = obstacles

         if genes:
            self.genes = genes
            if random.random() < PREDATOR_MUTATION_RATE:
                mutation = (random.random() * 2 - 1) * PREDATOR_MUTATION_STRENGTH * self.genes['speed']
                self.genes['speed'] = clamp(self.genes['speed'] + mutation, self.min_speed, self.max_speed)
            if random.random() < PREDATOR_MUTATION_RATE:
                 mutation = (random.random() * 2 - 1) * PREDATOR_MUTATION_STRENGTH * self.genes['sense']
                 self.genes['sense'] = clamp(self.genes['sense'] + mutation, self.min_sense, self.max_sense)

         if pos is None:
              while True:
                 # Використовуємо self.radius, встановлений у super().__init__
                 self.pos = pygame.Vector2(random.randint(self.radius, WIDTH - self.radius),
                                           random.randint(self.radius, HEIGHT - self.radius))
                 self.rect.center = self.pos
                 if not obstacles or not any(obs.rect.colliderect(self.rect) for obs in self.obstacles):
                     break
         else:
             self.pos = pygame.Vector2(pos.x + random.uniform(-10, 10), pos.y + random.uniform(-10, 10))
             self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
             self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)
             self.rect.center = self.pos

         self.target_creature = None

    # --- Реалізація абстрактних методів ---
    def get_energy_decay_rate(self): return PREDATOR_ENERGY_DECAY
    def get_move_cost(self): return PREDATOR_MOVE_COST
    def get_reproduction_ready_threshold(self): return PREDATOR_REPRODUCTION_READY_THRESHOLD
    # ------------------------------------

    def update(self, dt, creature_list, predator_list):
        if self.update_basic_state(dt): return
        if self.check_obstacle_collision(self.obstacles): return

        sense_radius_sq = self.genes['sense']**2
        move_direction = pygame.Vector2(0, 0)
        current_speed = self.genes['speed']
        prey_found = False

        # 1. Пошук здобичі
        current_target_valid = False
        if self.target_creature and self.target_creature in creature_list and not self.target_creature.is_dead:
             dist_sq = distance_sq(self.pos, self.target_creature.pos)
             if dist_sq < sense_radius_sq:
                 target_vector = self.target_creature.pos - self.pos
                 move_direction = normalize_vec(target_vector)
                 prey_found = True
                 current_target_valid = True
                 # Перевірка "укусу"
                 if dist_sq < (self.radius + self.target_creature.radius)**2:
                     self.hunt(self.target_creature)
                     self.target_creature = None
                     prey_found = False # Зупиняємо рух до цілі
                     current_target_valid = False
             else:
                  self.target_creature = None # Здобич втекла
        else:
             self.target_creature = None

        if not current_target_valid:
             # Шукаємо нову здобич, тільки якщо список істот не порожній
             if creature_list:
                 closest_prey, prey_dist_sq = self.find_closest_agent(
                     [c for c in creature_list if not c.is_dead],
                     sense_radius_sq
                 )
                 if closest_prey:
                     self.target_creature = closest_prey
                     target_vector = self.target_creature.pos - self.pos
                     move_direction = normalize_vec(target_vector)
                     prey_found = True

        # 2. Уникнення скупчення хижаків
        separation_vector = pygame.Vector2(0, 0)
        neighbors_count = 0
        if predator_list: # Перевірка, чи список не порожній
             for other in predator_list:
                 if other != self and not other.is_dead:
                     dist_sq = distance_sq(self.pos, other.pos)
                     if 0 < dist_sq < PREDATOR_SEPARATION_RADIUS**2:
                         diff = self.pos - other.pos
                         separation_vector += diff / max(dist_sq, 0.1)
                         neighbors_count += 1
        if neighbors_count > 0:
             separation_vector /= neighbors_count
             separation_vector = normalize_vec(separation_vector)
             if move_direction.length_squared() > 0:
                  combined_direction = move_direction * 0.8 + separation_vector * PREDATOR_SEPARATION_FORCE * 0.5
                  move_direction = normalize_vec(combined_direction)
             else:
                  move_direction = separation_vector

        # 3. Випадковий рух
        if not prey_found and move_direction.length_squared() == 0:
            if random.random() < 0.05:
                self.direction = normalize_vec(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)))
            if self.direction.length_squared() == 0:
                 self.direction = normalize_vec(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)))
            move_direction = self.direction

        self.apply_movement(dt, move_direction, current_speed)

        # Розмноження Хижаків (Асексуальне)
        if self.ready_to_mate and len(predators) < MAX_PREDATORS: # Використовуємо ready_to_mate, хоч і асексуальне
            self.energy -= PREDATOR_REPRODUCTION_COST
            child_genes = {'speed': self.genes['speed'], 'sense': self.genes['sense']}
            request_reproduction(self, None, child_genes)
            self.mating_cooldown_timer = PREDATOR_MATING_COOLDOWN
            self.ready_to_mate = False


    def find_closest_agent(self, agent_list, sense_radius_sq):
        closest_agent = None
        min_dist_sq = sense_radius_sq
        if not agent_list: return None, sense_radius_sq

        for agent in agent_list:
            # Хижак ігнорує мертвих, але не себе (себе виключаємо в Creature)
            if hasattr(agent, 'is_dead') and agent.is_dead: continue
            d_sq = distance_sq(self.pos, agent.pos)
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest_agent = agent
        return closest_agent, min_dist_sq

    def hunt(self, prey):
        if not self.is_dead and not prey.is_dead:
            prey.is_dead = True
            self.energy += PREDATOR_HUNT_ENERGY_GAIN
            if prey not in creatures_to_remove_global:
                 creatures_to_remove_global.append(prey)
            # print(f"Хижак {id(self)} полював на істоту {id(prey)}")


# --- Глобальні Списки та Об'єкти ---
# Ініціалізуємо порожніми перед спробою завантаження
obstacles = []
creatures = []
predators = []
food_list = []

creatures_to_remove_global = []
predators_to_remove_global = []
food_to_remove_global = []
creatures_to_add_global = []
predators_to_add_global = []

selected_agent = None
running = True
paused = False

# --- Функція для Запиту на Розмноження ---
def request_reproduction(parent1, parent2, child_genes):
    global max_creature_generation, max_predator_generation

    if isinstance(parent1, Creature):
        # Перевіряємо ліміт з урахуванням тих, що будуть додані
        if len(creatures) + len(creatures_to_add_global) < MAX_CREATURES:
            parent_gen = parent1.generation
            # Передаємо obstacles при створенні
            new_creature = Creature(obstacles, pos=parent1.pos, genes=child_genes, parent_generation=parent_gen)
            creatures_to_add_global.append(new_creature)
            max_creature_generation = max(max_creature_generation, new_creature.generation)
    elif isinstance(parent1, Predator):
         if len(predators) + len(predators_to_add_global) < MAX_PREDATORS:
            parent_gen = parent1.generation
            # Передаємо obstacles при створенні
            new_predator = Predator(obstacles, pos=parent1.pos, genes=child_genes, parent_generation=parent_gen)
            predators_to_add_global.append(new_predator)
            max_predator_generation = max(max_predator_generation, new_predator.generation)


# --- Функції Збереження/Завантаження ---
# ... (залишаються практично без змін, але тепер використовують vars()) ...
def save_simulation_state(filename="evolution_sim_save.pkl"):
    # Додамо try-except для vars, якщо об'єкт ще не повністю ініціалізований
    def get_vars_safe(obj):
        try: return vars(obj)
        except TypeError: return {}

    state_data = {
        'creatures': [get_vars_safe(c) for c in creatures],
        'predators': [get_vars_safe(p) for p in predators],
        'food_list': [get_vars_safe(f) for f in food_list],
        'obstacles_rects': [obs.rect for obs in obstacles if hasattr(obs, 'rect')],
        'max_creature_generation': max_creature_generation,
        'max_predator_generation': max_predator_generation,
        'simulation_time': simulation_time,
        'history_time': history_time,
        'history_creature_pop': history_creature_pop,
        'history_predator_pop': history_predator_pop,
        'history_avg_creature_speed': history_avg_creature_speed,
        'history_avg_creature_sense': history_avg_creature_sense,
        'history_avg_predator_speed': history_avg_predator_speed,
        'history_avg_predator_sense': history_avg_predator_sense,
        'last_log_time': last_log_time,
    }
    try:
        with open(filename, 'wb') as f:
            pickle.dump(state_data, f)
        print(f"Стан симуляції збережено у {filename}")
    except Exception as e:
        print(f"Помилка збереження стану: {e}")

def load_simulation_state(filename="evolution_sim_save.pkl"):
    global creatures, predators, food_list, obstacles
    global max_creature_generation, max_predator_generation, simulation_time
    global history_time, history_creature_pop, history_predator_pop
    global history_avg_creature_speed, history_avg_creature_sense
    global history_avg_predator_speed, history_avg_predator_sense, last_log_time

    print(f"Спроба завантаження стану з {filename}...") # Відлагодження

    try:
        with open(filename, 'rb') as f:
            state_data = pickle.load(f)

        # --- Відновлення Об'єктів ---
        print("Відновлення перешкод...")
        obstacles = []
        saved_obstacle_rects = state_data.get('obstacles_rects', [])
        if saved_obstacle_rects:
             for rect_data in saved_obstacle_rects:
                 try:
                     obs = Obstacle()
                     if isinstance(rect_data, (pygame.Rect, tuple, list)) and len(rect_data) == 4:
                          obs.rect = pygame.Rect(rect_data)
                          obstacles.append(obs)
                     else: print(f"  Пропущено невірні дані перешкоди: {rect_data}")
                 except Exception as e: print(f"  Помилка відновлення перешкоди: {e}")
        else: # Якщо не зберегли перешкоди, створюємо стандартні
             print("  Перешкоди не знайдено у збереженні, створення стандартних...")
             obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
        print(f"  Відновлено/Створено {len(obstacles)} перешкод.")


        print("Відновлення їжі...")
        food_list = []
        saved_food = state_data.get('food_list', [])
        for i, food_data in enumerate(saved_food):
            try:
                # Створюємо об'єкт Food, передаючи obstacles
                f = Food(obstacles)
                # Встановлюємо позицію зі збережених даних
                pos_data = food_data.get('pos', (0,0))
                if isinstance(pos_data, (tuple, list, pygame.Vector2)):
                     f.pos = pygame.Vector2(pos_data)
                     f.rect.center = f.pos # Оновлюємо rect
                     food_list.append(f)
                else: print(f"  Пропущено невірні дані позиції для їжі {i}: {pos_data}")
            except Exception as e: print(f"  Помилка відновлення їжі {i}: {e}")
        print(f"  Відновлено {len(food_list)} одиниць їжі.")


        print("Відновлення істот...")
        creatures = []
        saved_creatures = state_data.get('creatures', [])
        for i, creature_data in enumerate(saved_creatures):
            try:
                # 1. Створюємо об'єкт (конструктор встановить випадкову позицію)
                c = Creature(obstacles)
                final_pos = None # Для збереження відновленої позиції

                # 2. Встановлюємо атрибути зі збережених даних
                for key, value in creature_data.items():
                    if key == 'pos':
                        # Зберігаємо позицію, але ще не встановлюємо остаточно
                        if isinstance(value, (tuple, list, pygame.Vector2)):
                             final_pos = pygame.Vector2(value)
                             # print(f"  Істота {i}: Знайдено позицію {final_pos}") # Відлагодження
                        else: print(f"  Істота {i}: Невірний тип для 'pos': {value}")
                    elif key == 'direction':
                         setattr(c, key, pygame.Vector2(value) if isinstance(value, (tuple, list, pygame.Vector2)) else pygame.Vector2(0,0) )
                    elif key in ['rect', 'obstacles', 'target_food_obj', 'target_partner', 'mating_partner']:
                         # Ігноруємо атрибути, які не потрібно/не можна відновлювати напряму
                         pass
                    elif hasattr(c, key):
                         try: # Додаємо try-except для setattr
                             setattr(c, key, value)
                         except Exception as e_set: print(f"  Істота {i}: Помилка setattr для {key}={value}: {e_set}")

                # 3. Встановлюємо фінальну позицію (якщо вона була знайдена)
                if final_pos is not None:
                    c.pos = final_pos
                else:
                    # Якщо позиція не завантажилась, залишаємо випадкову з конструктора,
                    # але виводимо попередження
                    print(f"  ПОПЕРЕДЖЕННЯ: Істота {i}: Позиція не завантажена, використано випадкову: {c.pos}")

                # 4. Оновлюємо rect та колір на основі фінальних даних
                c.rect.center = c.pos
                c.update_color()
                creatures.append(c)
            except Exception as e: print(f"  Критична помилка відновлення істоти {i}: {e}")
        print(f"  Відновлено {len(creatures)} істот.")


        # Відновлення хижаків (аналогічно до істот)
        print("Відновлення хижаків...")
        predators = []
        saved_predators = state_data.get('predators', [])
        for i, predator_data in enumerate(saved_predators):
             try:
                 p = Predator(obstacles)
                 final_pos = None
                 for key, value in predator_data.items():
                     if key == 'pos':
                          if isinstance(value, (tuple, list, pygame.Vector2)):
                              final_pos = pygame.Vector2(value)
                          else: print(f"  Хижак {i}: Невірний тип для 'pos': {value}")
                     elif key == 'direction':
                          setattr(p, key, pygame.Vector2(value) if isinstance(value, (tuple, list, pygame.Vector2)) else pygame.Vector2(0,0) )
                     elif key in ['rect', 'obstacles', 'target_creature']: pass
                     elif hasattr(p, key):
                          try: setattr(p, key, value)
                          except Exception as e_set: print(f"  Хижак {i}: Помилка setattr для {key}={value}: {e_set}")

                 if final_pos is not None:
                     p.pos = final_pos
                 else:
                     print(f"  ПОПЕРЕДЖЕННЯ: Хижак {i}: Позиція не завантажена, використано випадкову: {p.pos}")

                 p.rect.center = p.pos
                 predators.append(p)
             except Exception as e: print(f"  Критична помилка відновлення хижака {i}: {e}")
        print(f"  Відновлено {len(predators)} хижаків.")


        # Відновлення глобальних змінних та історії
        print("Відновлення глобальних параметрів та історії...")
        max_creature_generation = state_data.get('max_creature_generation', 0)
        max_predator_generation = state_data.get('max_predator_generation', 0)
        simulation_time = state_data.get('simulation_time', 0.0)
        history_time = state_data.get('history_time', [])
        history_creature_pop = state_data.get('history_creature_pop', [])
        history_predator_pop = state_data.get('history_predator_pop', [])
        history_avg_creature_speed = state_data.get('history_avg_creature_speed', [])
        history_avg_creature_sense = state_data.get('history_avg_creature_sense', [])
        history_avg_predator_speed = state_data.get('history_avg_predator_speed', [])
        history_avg_predator_sense = state_data.get('history_avg_predator_sense', [])
        last_log_time = state_data.get('last_log_time', -log_interval)
        print("  Глобальні параметри та історія відновлені.")

        print(f"Стан симуляції успішно завантажено з {filename}")
        # Очищаємо тимчасові списки додавання/видалення
        creatures_to_remove_global.clear()
        predators_to_remove_global.clear()
        food_to_remove_global.clear()
        creatures_to_add_global.clear()
        predators_to_add_global.clear()
        # Скидаємо вибір
        global selected_agent
        selected_agent = None

        return True

    except FileNotFoundError:
        print(f"Файл збереження {filename} не знайдено. Початок нової симуляції.")
        # Ініціалізуємо стандартні значення
        obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
        creatures = [Creature(obstacles) for _ in range(INITIAL_CREATURES)]
        predators = [Predator(obstacles) for _ in range(INITIAL_PREDATORS)]
        food_list = [Food(obstacles) for _ in range(FOOD_COUNT)]
        max_creature_generation = 0
        max_predator_generation = 0
        simulation_time = 0.0
        history_time.clear(); history_creature_pop.clear(); history_predator_pop.clear()
        history_avg_creature_speed.clear(); history_avg_creature_sense.clear()
        history_avg_predator_speed.clear(); history_avg_predator_sense.clear()
        last_log_time = -log_interval
        selected_agent = None
        return False
    except Exception as e:
        print(f"Критична помилка завантаження стану: {e}")
        # Скидаємо до стандартних значень
        obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
        creatures = [Creature(obstacles) for _ in range(INITIAL_CREATURES)]
        predators = [Predator(obstacles) for _ in range(INITIAL_PREDATORS)]
        food_list = [Food(obstacles) for _ in range(FOOD_COUNT)]
        # Скинути інші глобальні змінні...
        max_creature_generation = 0; max_predator_generation = 0; simulation_time = 0.0; last_log_time = -log_interval; history_time.clear(); # і т.д.
        selected_agent = None
        return False

# --- Функція Побудови Графіків ---
# ... (залишається без змін) ...
def plot_simulation_data():
    if not history_time:
        print("Немає даних для побудови графіків.")
        return
    try:
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

        axs[0].plot(history_time, history_creature_pop, label="Істоти", color='blue')
        axs[0].plot(history_time, history_predator_pop, label="Хижаки", color='red')
        axs[0].set_ylabel("Популяція")
        axs[0].set_title("Динаміка Популяцій")
        axs[0].legend()
        axs[0].grid(True)

        axs[1].plot(history_time, history_avg_creature_speed, label="Ср. Шв. Істот", color='cyan')
        axs[1].plot(history_time, history_avg_predator_speed, label="Ср. Шв. Хижаків", color='magenta')
        axs[1].set_ylabel("Середня Швидкість")
        axs[1].set_title("Динаміка Середньої Швидкості")
        axs[1].legend()
        axs[1].grid(True)

        axs[2].plot(history_time, history_avg_creature_sense, label="Ср. Чут. Істот", color='lightblue')
        axs[2].plot(history_time, history_avg_predator_sense, label="Ср. Чут. Хижаків", color='pink')
        axs[2].set_xlabel("Час Симуляції (с)")
        axs[2].set_ylabel("Середня Чутливість")
        axs[2].set_title("Динаміка Середньої Чутливості")
        axs[2].legend()
        axs[2].grid(True)

        plt.tight_layout()
        plt.show()

    except ImportError:
        print("\nДля побудови графіків потрібна бібліотека matplotlib.")
        print("Встановіть її: pip install matplotlib")
    except Exception as e:
        print(f"\nПомилка при побудові графіків: {e}")

# --- ГОЛОВНИЙ ЦИКЛ ---
load_simulation_state() # Спробувати завантажити стан на початку

while running:
    # ... (решта головного циклу залишається практично без змін) ...
    dt = CLOCK.tick(60) / 1000.0
    dt = clamp(dt, 0.005, 0.1)
    mouse_pos_tuple = pygame.mouse.get_pos() # Отримуємо як кортеж
    try:
        # Конвертуємо в Vector2 для використання у функціях
        mouse_pos = pygame.Vector2(mouse_pos_tuple)
    except TypeError:
         mouse_pos = pygame.Vector2(0,0) # За замовчуванням, якщо позиція некоректна

    # --- Обробка Подій ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: paused = not paused
            if event.key == pygame.K_f:
                 for _ in range(20):
                     if len(food_list) < FOOD_COUNT * 2: food_list.append(Food(obstacles))
            if event.key == pygame.K_c:
                 for _ in range(5):
                     if len(creatures) < MAX_CREATURES: creatures.append(Creature(obstacles))
            if event.key == pygame.K_p:
                 if len(predators) < MAX_PREDATORS: predators.append(Predator(obstacles))
            if event.key == pygame.K_s: save_simulation_state()
            if event.key == pygame.K_l: load_simulation_state()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked_agent = None
                # Спочатку перевіряємо хижаків
                for agent in reversed(predators): # reversed може не працювати з пустим списком напряму
                    if agent.is_clicked(mouse_pos):
                        clicked_agent = agent; break
                # Потім істот
                if not clicked_agent:
                    for agent in reversed(creatures):
                         if agent.is_clicked(mouse_pos):
                             clicked_agent = agent; break
                selected_agent = clicked_agent

    # --- Очищення Глобальних Списків Змін ---
    creatures_to_remove_global.clear()
    predators_to_remove_global.clear()
    food_to_remove_global.clear()
    creatures_to_add_global.clear()
    predators_to_add_global.clear()

    # --- Оновлення Стану ---
    if not paused:
        simulation_time += dt

        # Оновлення Істот
        for creature in creatures:
            creature.update(dt, food_list, creatures, predators)
            if creature.is_dead and creature not in creatures_to_remove_global:
                 creatures_to_remove_global.append(creature)

        # Оновлення Хижаків
        for predator in predators:
            predator.update(dt, creatures, predators)
            if predator.is_dead and predator not in predators_to_remove_global:
                 predators_to_remove_global.append(predator)

        # Видалення мертвих/з'їдених
        for item in food_to_remove_global:
            if item in food_list: food_list.remove(item)
        for agent in creatures_to_remove_global:
            if agent in creatures: creatures.remove(agent)
            if selected_agent == agent: selected_agent = None
        for agent in predators_to_remove_global:
            if agent in predators: predators.remove(agent)
            if selected_agent == agent: selected_agent = None

        # Додавання нових
        creatures.extend(creatures_to_add_global)
        predators.extend(predators_to_add_global)

        # Обмеження популяцій
        for pop_list, max_pop in [(creatures, MAX_CREATURES), (predators, MAX_PREDATORS)]:
            if len(pop_list) > max_pop:
                try: # Додаємо try-except на випадок помилки сортування, якщо об'єкти некоректні
                     pop_list.sort(key=lambda x: x.energy if hasattr(x, 'energy') else 0)
                     num_to_remove = len(pop_list) - max_pop
                     # Перевіряємо, чи видаляється обраний агент
                     for i in range(num_to_remove):
                         if pop_list[i] == selected_agent:
                             selected_agent = None
                             break # Досить перевіряти, якщо знайшли
                     del pop_list[:num_to_remove]
                except AttributeError as e:
                     print(f"Помилка сортування при обмеженні популяції: {e}")


        # Додавання їжі
        if len(food_list) < FOOD_COUNT // 2 and random.random() < 0.05:
             for _ in range(10):
                 if len(food_list) < FOOD_COUNT * 1.5 : food_list.append(Food(obstacles))

        # --- Запис статистики для графіків ---
        if simulation_time - last_log_time >= log_interval:
            last_log_time = simulation_time
            history_time.append(simulation_time)
            history_creature_pop.append(len(creatures))
            history_predator_pop.append(len(predators))
            try: # Додаємо try-except на випадок пустої популяції або некоректних даних
                history_avg_creature_speed.append(np.mean([c.genes['speed'] for c in creatures]) if creatures else 0)
                history_avg_creature_sense.append(np.mean([c.genes['sense'] for c in creatures]) if creatures else 0)
                history_avg_predator_speed.append(np.mean([p.genes['speed'] for p in predators]) if predators else 0)
                history_avg_predator_sense.append(np.mean([p.genes['sense'] for p in predators]) if predators else 0)
            except Exception as e:
                 print(f"Помилка при розрахунку середніх значень генів: {e}")
                 # Додаємо нулі або None, щоб не зламати графіки
                 history_avg_creature_speed.append(0)
                 history_avg_creature_sense.append(0)
                 history_avg_predator_speed.append(0)
                 history_avg_predator_sense.append(0)
        # ------------------------------------


    # --- Малювання ---
    SCREEN.fill(BG_COLOR)
    if obstacles: # Малюємо, тільки якщо є
        for obs in obstacles: obs.draw(SCREEN)
    if food_list:
        for f in food_list: f.draw(SCREEN)

    agents_to_draw = creatures + predators
    # Використовуємо копію списку для безпечної ітерації, якщо він може змінюватись
    for agent in list(agents_to_draw):
        try: # Додаємо try-except на випадок, якщо агент некоректний
             if agent != selected_agent:
                  agent.draw(SCREEN, is_selected=False)
        except AttributeError as e:
            print(f"Помилка малювання агента (не вибраного): {e}")

    if selected_agent:
         try:
             selected_agent.draw(SCREEN, is_selected=True)
         except AttributeError as e:
             print(f"Помилка малювання вибраного агента: {e}")


    # --- Статистика та Інфо Панель ---
    # ... (код відображення статистики та інфо панелі залишається майже без змін) ...
    # Загальна статистика
    creature_pop_text = FONT.render(f"Істоти: {len(creatures)}/{MAX_CREATURES} (Пок: {max_creature_generation})", True, (50, 200, 50))
    predator_pop_text = FONT.render(f"Хижаки: {len(predators)}/{MAX_PREDATORS} (Пок: {max_predator_generation})", True, PREDATOR_COLOR)
    food_text = FONT.render(f"Їжа: {len(food_list)}", True, FOOD_COLOR)
    time_text = FONT.render(f"Час: {simulation_time:.1f}с", True, (200, 200, 200))
    SCREEN.blit(creature_pop_text, (10, 10))
    SCREEN.blit(predator_pop_text, (10, 35))
    SCREEN.blit(food_text, (10, 60))
    SCREEN.blit(time_text, (10, 85))

    # Інформація про обраного агента
    if selected_agent and hasattr(selected_agent, 'genes'): # Перевірка наявності атрибутів
        panel_width = 230
        panel_height = 160
        panel_x = WIDTH - panel_width - 10
        panel_y = 10
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((*INFO_PANEL_COLOR, 200))
        SCREEN.blit(panel_surface, (panel_x, panel_y))

        agent_type_str = "Істота" if isinstance(selected_agent, Creature) else "Хижак"
        max_age = selected_agent.max_age if hasattr(selected_agent, 'max_age') else 0

        lines = [
            f"Тип: {agent_type_str}",
            f"Покоління: {getattr(selected_agent, 'generation', '?')}",
            f"Енергія: {getattr(selected_agent, 'energy', 0):.1f}",
            f"Вік: {getattr(selected_agent, 'age', 0):.1f} / {max_age:.0f}с",
            f"Швидкість: {selected_agent.genes.get('speed', 0):.2f}",
            f"Чутливість: {selected_agent.genes.get('sense', 0):.1f}",
            f"Готовий спар.: {'Так' if getattr(selected_agent, 'ready_to_mate', False) else 'Ні'}",
            f"Кулдаун: {getattr(selected_agent, 'mating_cooldown_timer', 0):.1f}с"
        ]

        for i, line in enumerate(lines):
            try:
                text_surf = INFO_FONT.render(line, True, INFO_TEXT_COLOR)
                SCREEN.blit(text_surf, (panel_x + 10, panel_y + 5 + i * 20))
            except pygame.error as e: print(f"Помилка рендерингу тексту інфо-панелі: {e}")


    if paused:
        pause_text_render = FONT.render("ПАУЗА", True, (255, 0, 0))
        pause_rect = pause_text_render.get_rect(center=(WIDTH // 2, 25))
        SCREEN.blit(pause_text_render, pause_rect)

    pygame.display.flip()

# --- Завершення Pygame та Побудова Графіків ---
pygame.quit()
print("Завершення симуляції...")
plot_simulation_data()
print("Програма завершена.")