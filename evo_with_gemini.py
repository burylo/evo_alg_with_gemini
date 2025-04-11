import pygame
import random
import math
import numpy as np

# --- Налаштування Pygame та Симуляції ---
pygame.init()
WIDTH, HEIGHT = 1000, 750 # Збільшимо трохи розмір
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Еволюція: Істоти та Хижаки (з Поколіннями)")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 26) # Трохи більший шрифт
INFO_FONT = pygame.font.SysFont(None, 22)

# --- Глобальні Параметри ---
BG_COLOR = (10, 10, 20) # Темно-синій фон
INFO_PANEL_COLOR = (40, 40, 50)
INFO_TEXT_COLOR = (230, 230, 230)
SELECTION_COLOR = (255, 255, 0)
OBSTACLE_COLOR = (100, 100, 100)
PREDATOR_COLOR = (255, 50, 50) # Червоний для хижаків

# --- Параметри Істот ---
INITIAL_CREATURES = 20
MAX_CREATURES = 100
FOOD_COUNT = 50
FOOD_ENERGY = 50
CREATURE_INITIAL_ENERGY = 50
CREATURE_ENERGY_DECAY = 0.15 # Трохи швидше втрачають енергію
CREATURE_MOVE_COST = 0.5
CREATURE_REPRODUCTION_THRESHOLD = 150
CREATURE_REPRODUCTION_COST = 100
CREATURE_MAX_AGE = 50.0 # Секунди
CREATURE_MIN_SPEED, CREATURE_MAX_SPEED = 0.5, 5.0
CREATURE_MIN_SENSE, CREATURE_MAX_SENSE = 10, 100
CREATURE_MUTATION_RATE = 0.15
CREATURE_MUTATION_STRENGTH = 0.5

# --- Параметри Хижаків ---
INITIAL_PREDATORS = 1
MAX_PREDATORS = 15
PREDATOR_INITIAL_ENERGY = 150
PREDATOR_ENERGY_DECAY = 0.12 # Хижаки трохи витриваліші
PREDATOR_MOVE_COST = 0.1 # Рух дорожчий
PREDATOR_REPRODUCTION_THRESHOLD = 250 # Потрібно більше енергії
PREDATOR_REPRODUCTION_COST = 120
PREDATOR_HUNT_ENERGY_GAIN = 100 # Енергія за успішне полювання
PREDATOR_MAX_AGE = 50.0 # Живуть довше
PREDATOR_MIN_SPEED, PREDATOR_MAX_SPEED = 0.5, 5.0 # Трохи швидші
PREDATOR_MIN_SENSE, PREDATOR_MAX_SENSE = 20, 150 # Краще бачать
PREDATOR_MUTATION_RATE = 0.1
PREDATOR_MUTATION_STRENGTH = 0.2

# --- Параметри Світу ---
NUM_OBSTACLES = 10
OBSTACLE_MIN_SIZE = 25
OBSTACLE_MAX_SIZE = 70

# --- Відстеження Поколінь ---
max_creature_generation = 0
max_predator_generation = 0

# --- Класи ---

class Food:
    def __init__(self, obstacles):
        while True:
            self.pos = pygame.Vector2(random.randint(10, WIDTH - 10),
                                      random.randint(10, HEIGHT - 10))
            self.radius = 3
            self.rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius,
                                      self.radius * 2, self.radius * 2)
            collided_with_obstacle = False
            for obs in obstacles:
                if obs.rect.colliderect(self.rect):
                    collided_with_obstacle = True; break
            if not collided_with_obstacle: break
        self.color = (0, 255, 0)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos, self.radius)

class Obstacle:
    def __init__(self):
        size = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE)
        x = random.randint(0, WIDTH - size)
        y = random.randint(0, HEIGHT - size)
        self.rect = pygame.Rect(x, y, size, size)
        self.color = OBSTACLE_COLOR

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Creature:
    def __init__(self, obstacles, pos=None, genes=None, parent_generation=None):
        global max_creature_generation # Дозволяємо змінювати глобальну змінну
        self.obstacles = obstacles
        self.radius = 5
        if pos is None: # Перше покоління або випадковий спавн
             while True:
                self.pos = pygame.Vector2(random.randint(self.radius, WIDTH - self.radius),
                                          random.randint(self.radius, HEIGHT - self.radius))
                temp_rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius*2, self.radius*2)
                if not any(obs.rect.colliderect(temp_rect) for obs in self.obstacles):
                    break
             self.generation = 0 # Початкове покоління
        else: # Нащадок
             self.pos = pygame.Vector2(pos.x + random.uniform(-10, 10), pos.y + random.uniform(-10, 10))
             self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
             self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))
             # Успадкування покоління
             self.generation = parent_generation + 1
             if self.generation > max_creature_generation:
                 max_creature_generation = self.generation


        self.energy = CREATURE_INITIAL_ENERGY
        self.age = 0.0

        if genes is None:
            self.speed_gene = random.uniform(CREATURE_MIN_SPEED, CREATURE_MAX_SPEED)
            self.sense_gene = random.uniform(CREATURE_MIN_SENSE, CREATURE_MAX_SENSE)
        else:
            self.speed_gene = genes['speed']
            self.sense_gene = genes['sense']
            # Мутація
            if random.random() < CREATURE_MUTATION_RATE:
                self.speed_gene += random.uniform(-CREATURE_MUTATION_STRENGTH, CREATURE_MUTATION_STRENGTH) * self.speed_gene
            if random.random() < CREATURE_MUTATION_RATE:
                self.sense_gene += random.uniform(-CREATURE_MUTATION_STRENGTH, CREATURE_MUTATION_STRENGTH) * self.sense_gene

            self.speed_gene = max(CREATURE_MIN_SPEED, min(CREATURE_MAX_SPEED, self.speed_gene))
            self.sense_gene = max(CREATURE_MIN_SENSE, min(CREATURE_MAX_SENSE, self.sense_gene))

        r = int(np.interp(self.speed_gene, [CREATURE_MIN_SPEED, CREATURE_MAX_SPEED], [50, 255]))
        b = int(np.interp(self.sense_gene, [CREATURE_MIN_SENSE, CREATURE_MAX_SENSE], [50, 255]))
        self.color = (r, 50, b)

        self.target_food = None
        self.random_direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() if random.random() > 0 else pygame.Vector2(1,0)
        self.rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        self.is_dead = False # Прапорець смерті

    def find_closest_food(self, food_list):
        closest_food = None
        min_dist_sq = self.sense_gene**2

        for food_item in food_list:
            dist_sq = self.pos.distance_squared_to(food_item.pos)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_food = food_item
        return closest_food

    def move(self, dt):
        direction = pygame.Vector2(0,0)
        if self.target_food and self.target_food in food:
             target_vector = (self.target_food.pos - self.pos)
             dist_to_target = target_vector.length()
             if dist_to_target < self.radius + self.target_food.radius: # Перевіряємо точніше
                 self.target_food = None; direction = pygame.Vector2(0,0)
             elif dist_to_target > 0: direction = target_vector.normalize()
        else:
            self.target_food = None
            if random.random() < 0.05:
                 self.random_direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                 if self.random_direction.length_squared() > 0: self.random_direction.normalize_ip()
            direction = self.random_direction

        move_vector = direction * self.speed_gene * dt * 50
        next_pos = self.pos + move_vector
        self.pos = next_pos # Оновлюємо позицію
        self.rect.center = self.pos # Оновлюємо rect

        # Обмеження по екрану
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))
        self.rect.center = self.pos # Оновлюємо rect ще раз після обмеження

        # Втрата енергії від руху
        if direction.length_squared() > 0:
            self.energy -= CREATURE_MOVE_COST * self.speed_gene * dt

    def update(self, dt, food_list):
        if self.is_dead: return "dead" # Якщо вже позначений як мертвий

        self.age += dt
        if self.age >= CREATURE_MAX_AGE: self.is_dead = True; return "dead"

        for obs in self.obstacles:
             if self.rect.colliderect(obs.rect): self.is_dead = True; return "dead"

        if not self.target_food:
            self.target_food = self.find_closest_food(food_list)

        self.move(dt)
        self.energy -= CREATURE_ENERGY_DECAY * dt

        if self.energy <= 0: self.is_dead = True; return "dead"

        # Розмноження
        if self.energy >= CREATURE_REPRODUCTION_THRESHOLD and len(creatures) < MAX_CREATURES:
            self.energy -= CREATURE_REPRODUCTION_COST
            offspring_genes = {'speed': self.speed_gene, 'sense': self.sense_gene}
            # Передаємо поточне покоління для розрахунку покоління нащадка
            return Creature(self.obstacles, pos=self.pos, genes=offspring_genes, parent_generation=self.generation)

        return None

    def eat(self, food_item):
        if not self.is_dead: # Не можна їсти після смерті
            self.energy += FOOD_ENERGY
            if self.target_food == food_item:
                self.target_food = None

    def draw(self, surface, is_selected=False):
        # Радіус чутливості
        sense_surface = pygame.Surface((self.sense_gene * 2, self.sense_gene * 2), pygame.SRCALPHA)
        pygame.draw.circle(sense_surface, (*self.color, 30), (self.sense_gene, self.sense_gene), int(self.sense_gene))
        surface.blit(sense_surface, self.pos - pygame.Vector2(self.sense_gene, self.sense_gene))
        # Істота
        pygame.draw.circle(surface, self.color, self.pos, self.radius)
        if is_selected:
            pygame.draw.circle(surface, SELECTION_COLOR, self.pos, self.radius + 2, 2)

    def is_clicked(self, mouse_pos):
        return self.pos.distance_squared_to(mouse_pos) <= self.radius**2

# --- КЛАС ХИЖАКА ---
class Predator:
    def __init__(self, obstacles, pos=None, genes=None, parent_generation=None):
        global max_predator_generation # Дозволяємо змінювати глобальну змінну
        self.obstacles = obstacles
        self.radius = 7 # Хижаки трохи більші
        if pos is None: # Перше покоління
            while True:
                self.pos = pygame.Vector2(random.randint(self.radius, WIDTH - self.radius),
                                          random.randint(self.radius, HEIGHT - self.radius))
                temp_rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius*2, self.radius*2)
                if not any(obs.rect.colliderect(temp_rect) for obs in self.obstacles):
                    break
            self.generation = 0
        else: # Нащадок
            self.pos = pygame.Vector2(pos.x + random.uniform(-10, 10), pos.y + random.uniform(-10, 10))
            self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
            self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))
            # Успадкування покоління
            self.generation = parent_generation + 1
            if self.generation > max_predator_generation:
                max_predator_generation = self.generation

        self.energy = PREDATOR_INITIAL_ENERGY
        self.age = 0.0

        if genes is None:
            self.speed_gene = random.uniform(PREDATOR_MIN_SPEED, PREDATOR_MAX_SPEED)
            self.sense_gene = random.uniform(PREDATOR_MIN_SENSE, PREDATOR_MAX_SENSE)
        else:
            self.speed_gene = genes['speed']
            self.sense_gene = genes['sense']
            if random.random() < PREDATOR_MUTATION_RATE:
                self.speed_gene += random.uniform(-PREDATOR_MUTATION_STRENGTH, PREDATOR_MUTATION_STRENGTH) * self.speed_gene
            if random.random() < PREDATOR_MUTATION_RATE:
                 self.sense_gene += random.uniform(-PREDATOR_MUTATION_STRENGTH, PREDATOR_MUTATION_STRENGTH) * self.sense_gene

            self.speed_gene = max(PREDATOR_MIN_SPEED, min(PREDATOR_MAX_SPEED, self.speed_gene))
            self.sense_gene = max(PREDATOR_MIN_SENSE, min(PREDATOR_MAX_SENSE, self.sense_gene))

        self.color = PREDATOR_COLOR
        self.target_creature = None # Ціль - інша істота
        self.random_direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() if random.random() > 0 else pygame.Vector2(1,0)
        self.rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        self.is_dead = False

    def find_closest_prey(self, creature_list):
        """Знаходить найближчу живу істоту в радіусі чутливості."""
        closest_prey = None
        min_dist_sq = self.sense_gene**2

        # Перебираємо тільки живих істот
        for prey in creature_list:
            if not prey.is_dead: # Ігноруємо мертвих
                dist_sq = self.pos.distance_squared_to(prey.pos)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_prey = prey
        return closest_prey

    def move(self, dt):
        direction = pygame.Vector2(0,0)
        # Перевіряємо, чи ціль ще жива
        if self.target_creature and self.target_creature in creatures and not self.target_creature.is_dead:
             target_vector = (self.target_creature.pos - self.pos)
             dist_to_target = target_vector.length()
             # Не зупиняємось при наближенні, бо ціль може втекти
             if dist_to_target > 0: direction = target_vector.normalize()
        else:
            self.target_creature = None # Скидаємо ціль, якщо її немає або вона мертва
            if random.random() < 0.05:
                 self.random_direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                 if self.random_direction.length_squared() > 0: self.random_direction.normalize_ip()
            direction = self.random_direction

        move_vector = direction * self.speed_gene * dt * 50
        next_pos = self.pos + move_vector
        self.pos = next_pos
        self.rect.center = self.pos

        # Обмеження екрану
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))
        self.rect.center = self.pos

        # Втрата енергії від руху
        if direction.length_squared() > 0:
            self.energy -= PREDATOR_MOVE_COST * self.speed_gene * dt

    def update(self, dt, creature_list):
        """Оновлює стан хижака."""
        if self.is_dead: return "dead"

        self.age += dt
        if self.age >= PREDATOR_MAX_AGE: self.is_dead = True; return "dead"

        for obs in self.obstacles:
             if self.rect.colliderect(obs.rect): self.is_dead = True; return "dead"

        # Шукаємо здобич, якщо немає цілі або ціль мертва
        if not self.target_creature or self.target_creature.is_dead:
            self.target_creature = self.find_closest_prey(creature_list)

        self.move(dt)
        self.energy -= PREDATOR_ENERGY_DECAY * dt

        if self.energy <= 0: self.is_dead = True; return "dead" # Смерть від голоду

        # Розмноження
        if self.energy >= PREDATOR_REPRODUCTION_THRESHOLD and len(predators) < MAX_PREDATORS:
            self.energy -= PREDATOR_REPRODUCTION_COST
            offspring_genes = {'speed': self.speed_gene, 'sense': self.sense_gene}
            return Predator(self.obstacles, pos=self.pos, genes=offspring_genes, parent_generation=self.generation)

        return None

    def hunt(self, prey):
        """Хижак атакує здобич."""
        if not self.is_dead and not prey.is_dead:
            prey.is_dead = True # Позначаємо здобич як мертву
            self.energy += PREDATOR_HUNT_ENERGY_GAIN
           #  print(f"Хижак {id(self)} полював на істоту {id(prey)}") # Лог полювання
            if self.target_creature == prey:
                self.target_creature = None # Скидаємо ціль після успішного полювання

    def draw(self, surface, is_selected=False):
         # Радіус чутливості хижака
        sense_surface = pygame.Surface((self.sense_gene * 2, self.sense_gene * 2), pygame.SRCALPHA)
        pygame.draw.circle(sense_surface, (*self.color, 30), (self.sense_gene, self.sense_gene), int(self.sense_gene))
        surface.blit(sense_surface, self.pos - pygame.Vector2(self.sense_gene, self.sense_gene))
        # Хижак
        pygame.draw.circle(surface, self.color, self.pos, self.radius)
        # Малюємо трикутник всередині для позначення напрямку (опціонально)
        # angle = math.atan2(self.random_direction.y, self.random_direction.x)
        # p1 = self.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * self.radius
        # p2 = self.pos + pygame.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * self.radius * 0.6
        # p3 = self.pos + pygame.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * self.radius * 0.6
        # pygame.draw.polygon(surface, (255, 255, 255), [p1, p2, p3])

        if is_selected:
            pygame.draw.circle(surface, SELECTION_COLOR, self.pos, self.radius + 3, 2) # Більше обведення

    def is_clicked(self, mouse_pos):
        return self.pos.distance_squared_to(mouse_pos) <= self.radius**2


# --- Ініціалізація Світу ---
obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
creatures = [Creature(obstacles) for _ in range(INITIAL_CREATURES)]
predators = [Predator(obstacles) for _ in range(INITIAL_PREDATORS)] # Створюємо хижаків
food = [Food(obstacles) for _ in range(FOOD_COUNT)]

selected_agent = None # Тепер може бути Creature або Predator
running = True
paused = False

# --- Головний Цикл ---
while running:
    dt = CLOCK.tick(60) / 1000.0
    # Обмежуємо dt, щоб уникнути "прольоту" при лагах
    dt = min(dt, 0.1)
    mouse_pos = pygame.mouse.get_pos()

    # --- Обробка Подій ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: paused = not paused
            if event.key == pygame.K_f: # Додати їжі
                 for _ in range(20):
                     if len(food) < FOOD_COUNT * 2: food.append(Food(obstacles))
            if event.key == pygame.K_c: # Додати істот
                 for _ in range(5):
                     if len(creatures) < MAX_CREATURES: creatures.append(Creature(obstacles))
            if event.key == pygame.K_p: # Додати хижака
                 if len(predators) < MAX_PREDATORS: predators.append(Predator(obstacles))

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked_agent = None
                # Спочатку перевіряємо хижаків (вони візуально більші/важливіші)
                for predator in reversed(predators):
                    if predator.is_clicked(mouse_pos):
                        clicked_agent = predator; break
                # Якщо не клікнули на хижака, перевіряємо істот
                if not clicked_agent:
                    for creature in reversed(creatures):
                        if creature.is_clicked(mouse_pos):
                            clicked_agent = creature; break
                selected_agent = clicked_agent # Призначаємо або None

    # --- Оновлення Стану (Тільки якщо не пауза) ---
    if not paused:
        new_creatures = []
        creatures_to_remove = []
        new_predators = []
        predators_to_remove = []
        food_to_remove = []

        # 1. Оновлення істот (вік, голод, перешкоди, розмноження)
        for creature in creatures:
            if creature.is_dead: continue # Пропускаємо вже мертвих
            result = creature.update(dt, food)
            if result == "dead": creatures_to_remove.append(creature)
            elif isinstance(result, Creature): new_creatures.append(result)

        # 2. Оновлення хижаків (вік, голод, перешкоди, розмноження)
        for predator in predators:
            if predator.is_dead: continue
            result = predator.update(dt, creatures) # Передаємо список істот для полювання
            if result == "dead": predators_to_remove.append(predator)
            elif isinstance(result, Predator): new_predators.append(result)

        # 3. Полювання (Хижаки атакують Істот)
        for predator in predators:
            if predator.is_dead: continue
            # Перевіряємо зіткнення з усіма живими істотами
            for creature in creatures:
                if not creature.is_dead and predator.rect.colliderect(creature.rect):
                     # Перевірка точніше по радіусу
                     if predator.pos.distance_squared_to(creature.pos) < (predator.radius + creature.radius)**2:
                         predator.hunt(creature) # Хижак полює
                         # Здобич додається до списку на видалення в наступному кроці
                         if creature not in creatures_to_remove:
                              creatures_to_remove.append(creature)
                         # Один укус за кадр для хижака
                         break # Переходимо до наступного хижака

        # 4. Поїдання їжі (Істоти їдять)
        for creature in creatures:
            # Тільки живі істоти можуть їсти
            if creature.is_dead or creature in creatures_to_remove: continue
            for i, food_item in enumerate(food):
                # Використовуємо enumerate для можливості видалення по індексу (хоча тут не використовується)
                if food_item in food_to_remove: continue # Не їмо вже "з'їдену" за цей кадр їжу
                if creature.pos.distance_squared_to(food_item.pos) < (creature.radius + food_item.radius)**2:
                    creature.eat(food_item)
                    food_to_remove.append(food_item)
                    # Додаємо їжу на заміну
                    if len(food) - len(food_to_remove) < FOOD_COUNT * 1.5: # Перевіряємо майбутню кількість
                        food.append(Food(obstacles))
                    break # Одна їжа за кадр для істоти

        # 5. Очищення списків (видалення мертвих та з'їдених)
        # Перебираємо копії списків, щоб безпечно видаляти з оригіналів
        for creature in creatures_to_remove:
            if creature in creatures: creatures.remove(creature)
            if selected_agent == creature: selected_agent = None # Скидаємо вибір, якщо об'єкт помер
        for predator in predators_to_remove:
            if predator in predators: predators.remove(predator)
            if selected_agent == predator: selected_agent = None
        for item in food_to_remove:
           if item in food: food.remove(item)

        # 6. Додавання нових (нащадків)
        creatures.extend(new_creatures)
        predators.extend(new_predators)

        # 7. Обмеження популяцій (видаляємо найслабших, якщо перевищено ліміт)
        for pop_list, max_pop, type_name in [(creatures, MAX_CREATURES, "Creature"), (predators, MAX_PREDATORS, "Predator")]:
            if len(pop_list) > max_pop:
                pop_list.sort(key=lambda x: x.energy) # Сортуємо за енергією (найслабші спочатку)
                removed_count = len(pop_list) - max_pop
                # Перевіряємо, чи обраний агент не серед видалених
                for i in range(removed_count):
                    if pop_list[i] == selected_agent:
                        selected_agent = None; break
                # Залишаємо тільки найкращих
                del pop_list[:removed_count]


        # 8. Додавання їжі, якщо мало
        if len(food) < FOOD_COUNT // 2 and random.random() < 0.1:
             for _ in range(10): food.append(Food(obstacles))

    # --- Малювання ---
    SCREEN.fill(BG_COLOR)
    for obs in obstacles: obs.draw(SCREEN)
    for f in food: f.draw(SCREEN)
    # Малюємо істот
    for creature in creatures:
        creature.draw(SCREEN, is_selected=(creature == selected_agent))
    # Малюємо хижаків (поверх істот)
    for predator in predators:
        predator.draw(SCREEN, is_selected=(predator == selected_agent))

    # --- Статистика та Інфо Панель ---
    # Загальна статистика
    creature_pop_text = FONT.render(f"Істоти: {len(creatures)}/{MAX_CREATURES} (Пок: {max_creature_generation})", True, (50, 200, 50))
    predator_pop_text = FONT.render(f"Хижаки: {len(predators)}/{MAX_PREDATORS} (Пок: {max_predator_generation})", True, PREDATOR_COLOR)
    food_text = FONT.render(f"Їжа: {len(food)}", True, (0, 255, 0))
    SCREEN.blit(creature_pop_text, (10, 10))
    SCREEN.blit(predator_pop_text, (10, 35))
    SCREEN.blit(food_text, (10, 60))

    # Середні показники (якщо є відповідні популяції)
    if creatures:
        avg_c_speed = np.mean([c.speed_gene for c in creatures])
        avg_c_sense = np.mean([c.sense_gene for c in creatures])
        avg_c_age = np.mean([c.age for c in creatures])
        avg_c_speed_text = INFO_FONT.render(f"Іст. ср. шв: {avg_c_speed:.2f}", True, (200, 200, 200))
        avg_c_sense_text = INFO_FONT.render(f"Іст. ср. чут: {avg_c_sense:.1f}", True, (200, 200, 200))
        avg_c_age_text = INFO_FONT.render(f"Іст. ср. вік: {avg_c_age:.1f}с", True, (200, 200, 200))
        SCREEN.blit(avg_c_speed_text, (10, 90))
        SCREEN.blit(avg_c_sense_text, (10, 110))
        SCREEN.blit(avg_c_age_text, (10, 130))
    if predators:
        avg_p_speed = np.mean([p.speed_gene for p in predators])
        avg_p_sense = np.mean([p.sense_gene for p in predators])
        avg_p_age = np.mean([p.age for p in predators])
        avg_p_speed_text = INFO_FONT.render(f"Хиж. ср. шв: {avg_p_speed:.2f}", True, (255, 150, 150))
        avg_p_sense_text = INFO_FONT.render(f"Хиж. ср. чут: {avg_p_sense:.1f}", True, (255, 150, 150))
        avg_p_age_text = INFO_FONT.render(f"Хиж. ср. вік: {avg_p_age:.1f}с", True, (255, 150, 150))
        SCREEN.blit(avg_p_speed_text, (10, 160))
        SCREEN.blit(avg_p_sense_text, (10, 180))
        SCREEN.blit(avg_p_age_text, (10, 200))


    # Інформація про обраного агента
    if selected_agent:
        panel_width = 220
        panel_height = 120 # Збільшуємо для покоління
        panel_x = WIDTH - panel_width - 10
        panel_y = 10
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((*INFO_PANEL_COLOR, 200))
        SCREEN.blit(panel_surface, (panel_x, panel_y))

        # Визначаємо тип агента та відповідні дані
        agent_type_str = ""
        max_age = 0
        if isinstance(selected_agent, Creature):
            agent_type_str = "Істота"
            max_age = CREATURE_MAX_AGE
        elif isinstance(selected_agent, Predator):
            agent_type_str = "Хижак"
            max_age = PREDATOR_MAX_AGE

        type_text = INFO_FONT.render(f"Тип: {agent_type_str}", True, INFO_TEXT_COLOR)
        gen_text = INFO_FONT.render(f"Покоління: {selected_agent.generation}", True, INFO_TEXT_COLOR)
        energy_text = INFO_FONT.render(f"Енергія: {selected_agent.energy:.1f}", True, INFO_TEXT_COLOR)
        speed_text = INFO_FONT.render(f"Ген швидкості: {selected_agent.speed_gene:.2f}", True, INFO_TEXT_COLOR)
        sense_text = INFO_FONT.render(f"Ген чутливості: {selected_agent.sense_gene:.1f}", True, INFO_TEXT_COLOR)
        age_text = INFO_FONT.render(f"Вік: {selected_agent.age:.1f} / {max_age:.0f}с", True, INFO_TEXT_COLOR)

        SCREEN.blit(type_text, (panel_x + 10, panel_y + 10))
        SCREEN.blit(gen_text, (panel_x + 10, panel_y + 30))
        SCREEN.blit(energy_text, (panel_x + 10, panel_y + 50))
        SCREEN.blit(speed_text, (panel_x + 10, panel_y + 70))
        SCREEN.blit(sense_text, (panel_x + 10, panel_y + 90))
        SCREEN.blit(age_text, (panel_x + 10, panel_y + 110))


    if paused:
        pause_text_render = FONT.render("ПАУЗА", True, (255, 0, 0))
        pause_rect = pause_text_render.get_rect(center=(WIDTH // 2, 25))
        SCREEN.blit(pause_text_render, pause_rect)

    pygame.display.flip()

# --- Завершення Pygame ---
pygame.quit()
