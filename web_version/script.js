// --- DOM Елементи ---
const canvas = document.getElementById('simulationCanvas');
const ctx = canvas.getContext('2d');

// Кнопки
const pauseBtn = document.getElementById('pauseBtn');
const addFoodBtn = document.getElementById('addFoodBtn');
const addCreatureBtn = document.getElementById('addCreatureBtn');
const addPredatorBtn = document.getElementById('addPredatorBtn');
const saveStateBtn = document.getElementById('saveStateBtn');
const loadStateBtn = document.getElementById('loadStateBtn');
const resetStateBtn = document.getElementById('resetStateBtn');

// Статистика (spans)
const simTimeSpan = document.getElementById('simTime');
const creatureCountSpan = document.getElementById('creatureCount');
const maxCreatureCountSpan = document.getElementById('maxCreatureCount');
const maxCreatureGenSpan = document.getElementById('maxCreatureGen');
const predatorCountSpan = document.getElementById('predatorCount');
const maxPredatorCountSpan = document.getElementById('maxPredatorCount');
const maxPredatorGenSpan = document.getElementById('maxPredatorGen');
const foodCountSpan = document.getElementById('foodCount');
const avgCreatureSpeedSpan = document.getElementById('avgCreatureSpeed');
const avgCreatureSenseSpan = document.getElementById('avgCreatureSense');
const avgPredatorSpeedSpan = document.getElementById('avgPredatorSpeed');
const avgPredatorSenseSpan = document.getElementById('avgPredatorSense');

// Інфо панель
const selectedAgentDetailsDiv = document.getElementById('selectedAgentDetails');

// --- Глобальні Налаштування Симуляції ---
const WIDTH = 800; // Ширина канви
const HEIGHT = 600; // Висота канви
canvas.width = WIDTH;
canvas.height = HEIGHT;

// --- Параметри (аналогічно до Python версії, налаштувати!) ---
const BG_COLOR = '#0a0a14';
const FOOD_COLOR = '#00FF00';
const OBSTACLE_COLOR = '#646464';
const PREDATOR_COLOR = '#FF3232';
const CREATURE_BASE_COLOR_G = 50;
const SELECTION_COLOR = '#FFFF00';

// Істоти
const INITIAL_CREATURES = 20; // Менше для старту
const MAX_CREATURES = 100;
const FOOD_COUNT = 100;
const FOOD_ENERGY = 100;
const CREATURE_RADIUS = 8;
const CREATURE_INITIAL_ENERGY = 100;
const CREATURE_ENERGY_DECAY = 0.15;
const CREATURE_MOVE_COST = 0.5;
const CREATURE_REPRODUCTION_THRESHOLD = 100;
const CREATURE_REPRODUCTION_READY_THRESHOLD = 100;
const CREATURE_REPRODUCTION_COST = 100;
const CREATURE_MATING_COOLDOWN = 1.0;
const CREATURE_MAX_AGE = 50.0;
const CREATURE_MIN_SPEED = 0.5;
const CREATURE_MAX_SPEED = 5.0; // Трохи повільніше для веб
const CREATURE_MIN_SENSE = 10;
const CREATURE_MAX_SENSE = 100;
const CREATURE_MUTATION_RATE = 0.5;
const CREATURE_MUTATION_STRENGTH = 0.5;
const CREATURE_MATING_RANGE = 15;
const CREATURE_SEPARATION_RADIUS = 15;
const CREATURE_SEPARATION_FORCE = 1.5;

// Хижаки
const INITIAL_PREDATORS = 3;
const MAX_PREDATORS = 15;
const PREDATOR_RADIUS = 10;
const PREDATOR_INITIAL_ENERGY = 150;
const PREDATOR_ENERGY_DECAY = 0.12;
const PREDATOR_MOVE_COST = 0.5;
const PREDATOR_REPRODUCTION_THRESHOLD = 250;
const PREDATOR_REPRODUCTION_READY_THRESHOLD = 200;
const PREDATOR_REPRODUCTION_COST = 120;
const PREDATOR_MATING_COOLDOWN = 5.0; // Використовується для асексуального
const PREDATOR_HUNT_ENERGY_GAIN = 120;
const PREDATOR_MAX_AGE = 50.0;
const PREDATOR_MIN_SPEED = 0.8;
const PREDATOR_MAX_SPEED = 5;
const PREDATOR_MIN_SENSE = 20;
const PREDATOR_MAX_SENSE = 150;
const PREDATOR_MUTATION_RATE = 0.1;
const PREDATOR_MUTATION_STRENGTH = 0.2;
const PREDATOR_SEPARATION_RADIUS = 18;
const PREDATOR_SEPARATION_FORCE = 0.5;

// Світ
const NUM_OBSTACLES = 5;
const OBSTACLE_MIN_SIZE = 20;
const OBSTACLE_MAX_SIZE = 60;

// --- Глобальні Змінні Стану ---
let creatures = [];
let predators = [];
let food = [];
let obstacles = [];
let maxCreatureGeneration = 0;
let maxPredatorGeneration = 0;
let simulationTime = 0.0;
let paused = false;
let selectedAgent = null;
let lastTimestamp = 0; // Для розрахунку deltaTime

// Списки для графіків (не використовуються активно в цьому прикладі, але можна додати)
let history = [];
const LOG_INTERVAL = 1.0; // Секунди
let lastLogTime = -LOG_INTERVAL;

// --- Допоміжний Клас Вектора ---
class Vec2 {
    constructor(x = 0, y = 0) {
        this.x = x;
        this.y = y;
    }

    set(x, y) {
        this.x = x;
        this.y = y;
        return this;
    }

    add(v) {
        this.x += v.x;
        this.y += v.y;
        return this;
    }

    sub(v) {
        this.x -= v.x;
        this.y -= v.y;
        return this;
    }

    mult(scalar) {
        this.x *= scalar;
        this.y *= scalar;
        return this;
    }

    div(scalar) {
        if (scalar !== 0) {
            this.x /= scalar;
            this.y /= scalar;
        } else {
            this.x = 0;
            this.y = 0;
        }
        return this;
    }

    magSq() {
        return this.x * this.x + this.y * this.y;
    }

    mag() {
        return Math.sqrt(this.magSq());
    }

    normalize() {
        const len = this.mag();
        if (len > 0) {
            this.div(len);
        }
        return this;
    }

    static sub(v1, v2) {
        return new Vec2(v1.x - v2.x, v1.y - v2.y);
    }

    static distSq(v1, v2) {
        const dx = v1.x - v2.x;
        const dy = v1.y - v2.y;
        return dx * dx + dy * dy;
    }

    // Метод для серіалізації (для localStorage)
    toJSON() {
        return { x: this.x, y: this.y };
    }

    // Метод для десеріалізації
    static fromJSON(obj) {
        return new Vec2(obj.x, obj.y);
    }
}

// --- Допоміжні Функції ---
function clamp(value, min, max) {
    return Math.max(min, Math.min(value, max));
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

function map(value, inMin, inMax, outMin, outMax) {
    // Обмежити значення вхідним діапазоном
    value = clamp(value, inMin, inMax);
    const rangeIn = inMax - inMin;
    if (rangeIn === 0) return outMin; // Уникнення ділення на нуль
    const normalized = (value - inMin) / rangeIn;
    return outMin + normalized * (outMax - out_min); // Помилка була тут, виправлено
}


function random(min, max) {
    if (max === undefined) { // Тільки одна межа -> від 0 до min
        max = min;
        min = 0;
    }
    if (min === undefined) { // Немає меж -> від 0 до 1 (дробове)
        return Math.random();
    }
    // Ціле число від min до max включно
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min, max) {
     if (max === undefined) {
         max = min;
         min = 0;
     }
     return Math.random() * (max - min) + min;
}


// Конвертація RGB в 16-бітний колір (приблизно, для відображення може бути достатньо CSS кольорів)
// Або можна використовувати рядкові кольори CSS '#RRGGBB'
function colorToCSS(r, g, b) {
    r = clamp(Math.round(r), 0, 255);
    g = clamp(Math.round(g), 0, 255);
    b = clamp(Math.round(b), 0, 255);
    return `rgb(${r},${g},${b})`;
}

// Схрещування генів
function crossoverGenes(genes1, genes2) {
    const childGenes = {};
    childGenes.speed = random() < 0.5 ? genes1.speed : genes2.speed;
    childGenes.sense = random() < 0.5 ? genes1.sense : genes2.sense;
    // Додати інші гени, якщо потрібно
    return childGenes;
}

// --- Класи ---

class Food {
    constructor() {
        this.radius = 3; // Маленька їжа
        this.pos = new Vec2(random(this.radius, WIDTH - this.radius), random(this.radius, HEIGHT - 5));
        // Перевірка на перешкоди при створенні (опціонально, може сповільнити ініціалізацію)
        let attempts = 0;
        while (obstacles.some(obs => obs.contains(this.pos)) && attempts < 50) {
            this.pos.set(random(this.radius, WIDTH - this.radius), random(this.radius, HEIGHT - this.radius));
            attempts++;
        }
    }

    draw(ctx) {
        ctx.fillStyle = FOOD_COLOR;
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
    }

    // Для збереження/завантаження
    toJSON() {
        return { pos: this.pos.toJSON(), radius: this.radius };
    }
    static fromJSON(data) {
        const f = new Food();
        f.pos = Vec2.fromJSON(data.pos);
        f.radius = data.radius;
        return f;
    }
}

class Obstacle {
    constructor() {
        const size = random(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE);
        this.x = random(0, WIDTH - size);
        this.y = random(0, HEIGHT - size);
        this.width = size;
        this.height = size;
    }

    draw(ctx) {
        ctx.fillStyle = OBSTACLE_COLOR;
        ctx.fillRect(this.x, this.y, this.width, this.height);
    }

    // Перевірка, чи точка всередині прямокутника
    contains(point) {
        return point.x >= this.x && point.x <= this.x + this.width &&
               point.y >= this.y && point.y <= this.y + this.height;
    }
     // Перевірка зіткнення з колом (агентом)
    collidesWithCircle(circlePos, circleRadius) {
        // Знаходимо найближчу точку на прямокутнику до центру кола
        const closestX = clamp(circlePos.x, this.x, this.x + this.width);
        const closestY = clamp(circlePos.y, this.y, this.y + this.height);
        // Перевіряємо квадрат відстані
        return Vec2.distSq(circlePos, new Vec2(closestX, closestY)) < circleRadius * circleRadius;
    }


    toJSON() {
        return { x: this.x, y: this.y, width: this.width, height: this.height };
    }
    static fromJSON(data) {
        const o = new Obstacle();
        o.x = data.x; o.y = data.y; o.width = data.width; o.height = data.height;
        return o;
    }
}

// Базовий клас Агента
class Agent {
    constructor(x, y, radius, color, initialEnergy, maxAge, genes, generation = 0) {
        this.pos = new Vec2(x, y);
        this.radius = radius;
        this.color = color; // Буде встановлено в дочірньому класі
        this.initialEnergy = initialEnergy; // Збережемо для скидання
        this.energy = initialEnergy;
        this.maxAge = maxAge;
        this.age = 0;
        this.generation = generation;
        this.isDead = false;
        this.direction = new Vec2(randomFloat(-1, 1), randomFloat(-1, 1)).normalize();
        this.genes = genes; // Об'єкт { speed: ..., sense: ... }

        this.readyToMate = false;
        this.matingCooldownTimer = 0;
        this.matingPartner = null; // Об'єкт партнера
        this.targetPartner = null; // Об'єкт цільового партнера
    }

    // Абстрактні методи (які мають бути реалізовані в дочірніх класах)
    getEnergyDecayRate() { throw new Error("Method 'getEnergyDecayRate()' must be implemented."); }
    getMoveCost() { throw new Error("Method 'getMoveCost()' must be implemented."); }
    getReproductionReadyThreshold() { throw new Error("Method 'getReproductionReadyThreshold()' must be implemented."); }
    getMatingCooldown() { throw new Error("Method 'getMatingCooldown()' must be implemented."); }
    getSeparationRadiusSq() { throw new Error("Method 'getSeparationRadiusSq()' must be implemented."); }
    getSeparationForce() { throw new Error("Method 'getSeparationForce()' must be implemented."); }
    getMutationRate() { throw new Error("Method 'getMutationRate()' must be implemented."); }
    getMutationStrength() { throw new Error("Method 'getMutationStrength()' must be implemented."); }
    getMinSpeed() { throw new Error("Method 'getMinSpeed()' must be implemented."); }
    getMaxSpeed() { throw new Error("Method 'getMaxSpeed()' must be implemented."); }
    getMinSense() { throw new Error("Method 'getMinSense()' must be implemented."); }
    getMaxSense() { throw new Error("Method 'getMaxSense()' must be implemented."); }
    // Метод для створення нащадка (щоб уникнути дублювання)
    createOffspring(partner, childGenes) { throw new Error("Method 'createOffspring()' must be implemented."); }


    updateBasicState(dt) {
        if (this.isDead) return true;
        this.age += dt;
        this.energy -= this.getEnergyDecayRate() * dt;

        if (this.matingCooldownTimer > 0) {
            this.matingCooldownTimer -= dt;
            this.readyToMate = false;
        } else if (this.energy >= this.getReproductionReadyThreshold()) {
            this.readyToMate = true;
        } else {
            this.readyToMate = false;
        }

        if (this.energy <= 0 || this.age >= this.maxAge) {
            this.isDead = true;
            return true;
        }
        return false;
    }

    checkObstacleCollision(obstacles) {
        if (this.isDead) return false;
        for (const obs of obstacles) {
            if (obs.collidesWithCircle(this.pos, this.radius)) {
                this.isDead = true;
                return true;
            }
        }
        return false;
    }

     applyMovement(dt, moveDirection, currentSpeed, energyCostMultiplier = 1.0) {
        if (this.isDead || moveDirection.magSq() === 0) return;

        const moveVector = new Vec2(moveDirection.x, moveDirection.y).mult(currentSpeed * dt * 10); // Множник швидкості підібрати!
        this.pos.add(moveVector);

        // Обмеження екраном
        this.pos.x = clamp(this.pos.x, this.radius, WIDTH - this.radius);
        this.pos.y = clamp(this.pos.y, this.radius, HEIGHT - this.radius);

        // Витрати енергії
        const energyCost = this.getMoveCost() * currentSpeed * energyCostMultiplier * dt;
        this.energy -= energyCost;
    }

    // Допоміжна функція для пошуку найближчого агента
    findClosestAgent(agentList, senseRadiusSq, filterFn = null) {
        let closestAgent = null;
        let min_dist_sq = senseRadiusSq;

        for (const agent of agentList) {
            if (agent === this || agent.isDead) continue;
            // Застосовуємо додатковий фільтр, якщо він є
            if (filterFn && !filterFn(agent)) continue;

            const dSq = Vec2.distSq(this.pos, agent.pos);
            if (dSq < min_dist_sq) {
                min_dist_sq = dSq;
                closestAgent = agent;
            }
        }
        return { agent: closestAgent, distSq: min_dist_sq };
    }

    // Розрахунок вектора separation
    calculateSeparation(agentList) {
        let steer = new Vec2();
        let count = 0;
        const separationRadiusSq = this.getSeparationRadiusSq();

        for (const other of agentList) {
            if (other !== this && !other.is_dead) {
                const dSq = Vec2.distSq(this.pos, other.pos);
                if (dSq > 0 && dSq < separationRadiusSq) {
                    let diff = Vec2.sub(this.pos, other.pos);
                    diff.normalize();
                    diff.div(Math.sqrt(dSq) || 1); // Вага обернено пропорційна відстані
                    steer.add(diff);
                    count++;
                }
            }
        }
        if (count > 0) {
            steer.div(count);
            steer.normalize();
            steer.mult(this.getSeparationForce());
        }
        return steer;
    }
    
    calculateWallAvoidance() {
        const avoidanceMargin = this.radius + 15; // Відстань від стіни, на якій починаємо реагувати
        const avoidanceForce = 1.5; // Сила відштовхування
        let steer = new Vec2();

        if (this.pos.x < avoidanceMargin) {
            steer.x = 1; // Рухатись праворуч
        } else if (this.pos.x > WIDTH - avoidanceMargin) {
            steer.x = -1; // Рухатись ліворуч
        }

        if (this.pos.y < avoidanceMargin) {
            steer.y = 1; // Рухатись вниз
        } else if (this.pos.y > HEIGHT - avoidanceMargin) {
            steer.y = -1; // Рухатись вгору
        }

        if (steer.magSq() > 0) {
            steer.normalize();
            steer.mult(avoidanceForce);
        }
        return steer;
    }

    draw(ctx) {
        if (this.isDead) return;
        // --- Малювання радіусу чутливості (Sense Radius) ---
        const senseRadiusVal = this.genes.sense;
        if (senseRadiusVal > 0) {
            ctx.strokeStyle = `rgba(${this.color === PREDATOR_COLOR ? '255, 80, 80' : '100, 100, 255'}, 0.15)`; // Червонуватий для хижака, синюватий для істоти
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(this.pos.x, this.pos.y, senseRadiusVal, 0, Math.PI * 2);
            ctx.stroke();
        }
        // ---------------------------------------------------
        // Малювання агента
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fill();

        // Малювання радіусу чутливості (опціонально, може гальмувати)
        // ctx.strokeStyle = 'rgba(100, 100, 255, 0.2)';
        // ctx.lineWidth = 1;
        // ctx.beginPath();
        // ctx.arc(this.pos.x, this.pos.y, Math.sqrt(this.genes.sense * this.genes.sense), 0, Math.PI * 2); // Помилка: був квадрат
        // ctx.stroke();


        // Підсвічування
        if (this === selectedAgent) {
            ctx.strokeStyle = SELECTION_COLOR;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(this.pos.x, this.pos.y, this.radius + 3, 0, Math.PI * 2);
            ctx.stroke();
        }
    }

    isClicked(clickPos) {
        return !this.isDead && Vec2.distSq(this.pos, clickPos) <= this.radius * this.radius;
    }

     // Метод для збереження стану (збирає дані для JSON)
    toJSON() {
        return {
            type: this.constructor.name, // Зберігаємо тип класу
            x: this.pos.x,
            y: this.pos.y,
            radius: this.radius,
            color: this.color, // Зберігаємо колір (хоча він залежить від генів)
            energy: this.energy,
            maxAge: this.maxAge,
            age: this.age,
            generation: this.generation,
            isDead: this.isDead,
            direction: this.direction.toJSON(),
            genes: { ...this.genes }, // Копія генів
            readyToMate: this.readyToMate,
            matingCooldownTimer: this.matingCooldownTimer,
            // Не зберігаємо target/partner посилання
        };
    }

    // Метод для відновлення стану з даних JSON
    // Викликається в загальній функції loadState
    restoreState(data) {
         this.pos = new Vec2(data.x, data.y);
         this.radius = data.radius;
         this.color = data.color;
         this.energy = data.energy;
         this.maxAge = data.maxAge;
         this.age = data.age;
         this.generation = data.generation;
         this.isDead = data.isDead;
         this.direction = Vec2.fromJSON(data.direction || {x:0, y:0}); // Обробка можливої відсутності
         this.genes = { ...data.genes }; // Відновлюємо гени
         this.readyToMate = data.readyToMate;
         this.matingCooldownTimer = data.matingCooldownTimer;
         // Важливо: Колір може потребувати оновлення на основі генів
         if (typeof this.updateColor === 'function') {
             this.updateColor();
         }
    }
    // Розрахунок вектора уникнення стін
    calculateWallAvoidance() {
        const avoidanceMargin = this.radius+1; // Відстань від стіни, на якій починаємо реагувати
        const avoidanceForce = 1.5; // Сила відштовхування
        let steer = new Vec2();

        if (this.pos.x < avoidanceMargin) {
            steer.x = 1; // Рухатись праворуч
        } else if (this.pos.x > WIDTH - avoidanceMargin) {
            steer.x = -1; // Рухатись ліворуч
        }

        if (this.pos.y < avoidanceMargin) {
            steer.y = 1; // Рухатись вниз
        } else if (this.pos.y > HEIGHT - avoidanceMargin) {
            steer.y = -1; // Рухатись вгору
        }

        if (steer.magSq() > 0) {
            steer.normalize();
            steer.mult(avoidanceForce);
        }
        return steer;
    }
}

// Клас Істоти
class Creature extends Agent {
    constructor(x, y, genes = null, generation = 0) {
        const initialGenes = genes || {
             speed: randomFloat(CREATURE_MIN_SPEED, CREATURE_MAX_SPEED),
             sense: randomFloat(CREATURE_MIN_SENSE, CREATURE_MAX_SENSE)
        };
        super(x, y, CREATURE_RADIUS, '#FFFFFF', CREATURE_INITIAL_ENERGY, CREATURE_MAX_AGE, initialGenes, generation);
        this.updateColor(); // Встановлюємо колір на основі генів
        this.targetFood = null; // Об'єкт їжі
    }

    // Реалізація абстрактних методів
    getEnergyDecayRate() { return CREATURE_ENERGY_DECAY; }
    getMoveCost() { return CREATURE_MOVE_COST; }
    getReproductionReadyThreshold() { return CREATURE_REPRODUCTION_READY_THRESHOLD; }
    getMatingCooldown() { return CREATURE_MATING_COOLDOWN; }
    getSeparationRadiusSq() { return CREATURE_SEPARATION_RADIUS * CREATURE_SEPARATION_RADIUS; }
    getSeparationForce() { return CREATURE_SEPARATION_FORCE; }
    getMutationRate() { return CREATURE_MUTATION_RATE; }
    getMutationStrength() { return CREATURE_MUTATION_STRENGTH; }
    getMinSpeed() { return CREATURE_MIN_SPEED; }
    getMaxSpeed() { return CREATURE_MAX_SPEED; }
    getMinSense() { return CREATURE_MIN_SENSE; }
    getMaxSense() { return CREATURE_MAX_SENSE; }

     // Метод для створення нащадка
     createOffspring(partner, childGenes) {
         // Мутація застосовується тут
         const mutatedGenes = { ...childGenes };
         if (random() < this.getMutationRate()) {
             const mutation = (random() * 2 - 1) * this.getMutationStrength() * mutatedGenes.speed;
             mutatedGenes.speed = clamp(mutatedGenes.speed + mutation, this.getMinSpeed(), this.getMaxSpeed());
         }
         if (random() < this.getMutationRate()) {
             const mutation = (random() * 2 - 1) * this.getMutationStrength() * mutatedGenes.sense;
             mutatedGenes.sense = clamp(mutatedGenes.sense + mutation, this.getMinSense(), this.getMaxSense());
         }
         // Створюємо нового агента біля одного з батьків
         const offspring = new Creature(this.pos.x + random(-5, 5), this.pos.y + random(-5, 5), mutatedGenes, this.generation + 1);
         return offspring;
     }


    updateColor() {
        const r = lerp(50, 255, (this.genes.speed - CREATURE_MIN_SPEED) / (CREATURE_MAX_SPEED - CREATURE_MIN_SPEED || 1));
        const b = lerp(50, 255, (this.genes.sense - CREATURE_MIN_SENSE) / (CREATURE_MAX_SENSE - CREATURE_MIN_SENSE || 1));
        this.color = colorToCSS(r, CREATURE_BASE_COLOR_G, b);
    }

    update(dt, foodList, creatureList, predators) {
        if (this.updateBasicState(dt)) return;
        if (this.checkObstacleCollision(obstacles)) return;

        let moveDirection = new Vec2();
        let currentSpeed = this.genes.speed;
        let energyMult = 1.0;
        let evading = false;
        let matingAttempt = false;
        let seekingFood = false;

        const senseRadiusSq = this.genes.sense * this.genes.sense;

        // 1. Ухилення
        const { agent: closestPredator } = this.findClosestAgent(predators, senseRadiusSq);
        if (closestPredator) {
            let evadeVector = Vec2.sub(this.pos, closestPredator.pos);
            moveDirection = evadeVector.normalize();
            currentSpeed *= 1.2;
            energyMult = 1.5;
            evading = true;
            this.targetFood = null; this.targetPartner = null; this.matingPartner = null;
        }

        // 2. Розмноження
        if (!evading && this.readyToMate) {
             // Логіка пошуку партнера та спарювання...
             if (this.matingPartner && !this.matingPartner.is_dead && this.matingPartner.readyToMate) {
                 const partnerDistSq = Vec2.distSq(this.pos, this.matingPartner.pos);
                 if (partnerDistSq < CREATURE_MATING_RANGE * CREATURE_MATING_RANGE) {
                     // Спарювання
                     if (Math.random() < 0.5) { // Щоб уникнути подвійного створення
                         const childGenes = crossoverGenes(this.genes, this.matingPartner.genes);
                         const offspring = this.createOffspring(this.matingPartner, childGenes);
                         creaturesToAdd.push(offspring); // Додаємо в тимчасовий список
                         maxCreatureGeneration = Math.max(maxCreatureGeneration, offspring.generation);
                     }
                     this.matingCooldownTimer = this.getMatingCooldown();
                     this.matingPartner.matingCooldownTimer = this.matingPartner.getMatingCooldown();
                     this.readyToMate = false;
                     this.matingPartner.readyToMate = false;
                     this.matingPartner.matingPartner = null;
                     this.matingPartner = null;
                     matingAttempt = true;
                     moveDirection.set(0, 0); // Зупинитися після спарювання
                 } else if (partnerDistSq < senseRadiusSq) {
                     moveDirection = Vec2.sub(this.matingPartner.pos, this.pos).normalize();
                     matingAttempt = true;
                 } else {
                     this.matingPartner.matingPartner = null; // Скасовуємо зв'язок
                     this.matingPartner = null;
                 }
             } else {
                 // Шукаємо нового
                 this.matingPartner = null;
                 const { agent: closestPartner } = this.findClosestAgent(
                     creatureList,
                     senseRadiusSq,
                     (c) => c !== this && c.readyToMate && !c.matingPartner // Шукаємо вільних і готових
                 );
                 if (closestPartner) {
                     this.targetPartner = closestPartner; // Запам'ятали ціль
                     // Спроба "домовитись"
                     if (!closestPartner.matingPartner || closestPartner.targetPartner === this) {
                         this.matingPartner = closestPartner;
                         closestPartner.matingPartner = this; // Взаємно
                         moveDirection = Vec2.sub(this.targetPartner.pos, this.pos).normalize();
                         matingAttempt = true;
                     } else { this.targetPartner = null; } // Не вдалося
                 } else { this.targetPartner = null; }
             }
        }


        // 3. Пошук їжі
        if (!evading && !matingAttempt) {
             if (this.targetFood && foodList.includes(this.targetFood)) { // Перевірка чи ціль ще існує
                 const foodDistSq = Vec2.distSq(this.pos, this.targetFood.pos);
                 if (foodDistSq < (this.radius + this.targetFood.radius)**2) {
                     this.eat(this.targetFood); // Їмо
                     this.targetFood = null; // Скидаємо ціль
                 } else if (foodDistSq < senseRadiusSq) {
                     moveDirection = Vec2.sub(this.targetFood.pos, this.pos).normalize();
                     seekingFood = true;
                 } else { this.targetFood = null; } // Занадто далеко
             } else {
                 // Шукаємо нову їжу
                 this.targetFood = null;
                 const { agent: closestFood } = this.findClosestAgent(foodList, senseRadiusSq);
                 if (closestFood) {
                     this.targetFood = closestFood;
                     moveDirection = Vec2.sub(this.targetFood.pos, this.pos).normalize();
                     seekingFood = true;
                 }
             }
        }


        // 4. Separation
        const separationVector = this.calculateSeparation(creatureList);
        if (separationVector.magSq() > 0) {
             if (moveDirection.magSq() > 0) {
                  // Змішуємо напрямки
                  moveDirection.add(separationVector.mult(0.5)).normalize(); // Просте додавання
             } else {
                  moveDirection = separationVector; // Separation стає основним рухом
             }
        }


        // 5. Випадковий рух
        if (!evading && !matingAttempt && !seekingFood && moveDirection.magSq() === 0) {
             if (random() < 0.05) { // Змінюємо напрямок
                  this.direction.set(randomFloat(-1, 1), randomFloat(-1, 1)).normalize();
             }
             if (this.direction.magSq() === 0) { // Якщо напрямок нульовий
                 this.direction.set(randomFloat(-1, 1), randomFloat(-1, 1)).normalize();
             }
             moveDirection = this.direction;
        }

        const wallAvoidanceVector = this.calculateWallAvoidance();
        if (wallAvoidanceVector.magSq() > 0) {
             // Якщо є рух, змішуємо, інакше цей вектор стає основним
             if (moveDirection.magSq() > 0) {
                 // Додаємо з вагою (наприклад, вага стіни більша)
                 moveDirection.add(wallAvoidanceVector.mult(1.0)).normalize(); // Вага 1.0 для сили стіни
             } else {
                 moveDirection = wallAvoidanceVector;
             }
             // Можливо, скинути інші цілі, якщо активно уникаємо стіну?
             this.targetFood = null; // Для Creature
             this.targetPartner = null; // Для Creature
             this.matingPartner = null; // Для Creature
             this.targetCreature = null; // Для Predator
        }

        // 5. Випадковий рух (якщо все ще немає напрямку)
        if (moveDirection.magSq() === 0 /* && !evading && !matingAttempt && !seekingFood/Prey */) {
            // ... (логіка випадкового руху) ...
        }

        this.applyMovement(dt, moveDirection, currentSpeed, energyMult);
    }

    eat(foodItem) {
        if (!this.isDead) {
            this.energy += FOOD_ENERGY;
            // Позначаємо їжу для видалення глобально
            if (!foodToRemove.includes(foodItem)) {
                foodToRemove.push(foodItem);
            }
            if (this.targetFood === foodItem) {
                this.targetFood = null;
            }
        }
    }
}


// Клас Хижака
class Predator extends Agent {
    constructor(x, y, genes = null, generation = 0) {
        const initialGenes = genes || {
            speed: randomFloat(PREDATOR_MIN_SPEED, PREDATOR_MAX_SPEED),
            sense: randomFloat(PREDATOR_MIN_SENSE, PREDATOR_MAX_SENSE)
        };
        super(x, y, PREDATOR_RADIUS, PREDATOR_COLOR, PREDATOR_INITIAL_ENERGY, PREDATOR_MAX_AGE, initialGenes, generation);
        this.targetCreature = null; // Об'єкт істоти
    }

    // Реалізація абстрактних методів
    getEnergyDecayRate() { return PREDATOR_ENERGY_DECAY; }
    getMoveCost() { return PREDATOR_MOVE_COST; }
    getReproductionReadyThreshold() { return PREDATOR_REPRODUCTION_READY_THRESHOLD; }
    getMatingCooldown() { return PREDATOR_MATING_COOLDOWN; }
    getSeparationRadiusSq() { return PREDATOR_SEPARATION_RADIUS * PREDATOR_SEPARATION_RADIUS; }
    getSeparationForce() { return PREDATOR_SEPARATION_FORCE; }
    getMutationRate() { return PREDATOR_MUTATION_RATE; }
    getMutationStrength() { return PREDATOR_MUTATION_STRENGTH; }
    getMinSpeed() { return PREDATOR_MIN_SPEED; }
    getMaxSpeed() { return PREDATOR_MAX_SPEED; }
    getMinSense() { return PREDATOR_MIN_SENSE; }
    getMaxSense() { return PREDATOR_MAX_SENSE; }

    // Метод для створення нащадка (асексуально)
    createOffspring(partner, childGenes) { // partner ігнорується
        const mutatedGenes = { ...childGenes }; // Використовуємо передані гени (які є копією батьківських)
        if (random() < this.getMutationRate()) {
            const mutation = (random() * 2 - 1) * this.getMutationStrength() * mutatedGenes.speed;
            mutatedGenes.speed = clamp(mutatedGenes.speed + mutation, this.getMinSpeed(), this.getMaxSpeed());
        }
        if (random() < this.getMutationRate()) {
            const mutation = (random() * 2 - 1) * this.getMutationStrength() * mutatedGenes.sense;
            mutatedGenes.sense = clamp(mutatedGenes.sense + mutation, this.getMinSense(), this.getMaxSense());
        }
        const offspring = new Predator(this.pos.x + random(-5, 5), this.pos.y + random(-5, 5), mutatedGenes, this.generation + 1);
        return offspring;
    }

    update(dt, creatureList, predators) {
        if (this.updateBasicState(dt)) return;
        if (this.checkObstacleCollision(obstacles)) return;

        let moveDirection = new Vec2();
        let currentSpeed = this.genes.speed;
        let seekingPrey = false;
        const senseRadiusSq = this.genes.sense * this.genes.sense;

        // 1. Пошук / Переслідування здобичі
        let currentTargetValid = false;
        if (this.targetCreature && creatureList.includes(this.targetCreature) && !this.targetCreature.is_dead) {
            const preyDistSq = Vec2.distSq(this.pos, this.targetCreature.pos);
            if (preyDistSq < senseRadiusSq) {
                moveDirection = Vec2.sub(this.targetCreature.pos, this.pos).normalize();
                seekingPrey = true;
                currentTargetValid = true;
                // Перевірка полювання
                if (preyDistSq < (this.radius + this.targetCreature.radius)**2) {
                    this.hunt(this.targetCreature);
                    this.targetCreature = null; // Шукаємо нову
                    seekingPrey = false;
                    currentTargetValid = false;
                }
            } else { this.targetCreature = null; } // Здобич втекла
        } else { this.targetCreature = null; } // Ціль недійсна

        if (!currentTargetValid) {
            const { agent: closestPrey } = this.findClosestAgent(
                creatureList,
                senseRadiusSq,
                (c) => !c.is_dead // Шукаємо тільки живих
            );
            if (closestPrey) {
                this.targetCreature = closestPrey;
                moveDirection = Vec2.sub(this.targetCreature.pos, this.pos).normalize();
                seekingPrey = true;
            }
        }

        // 2. Separation
        const separationVector = this.calculateSeparation(predators);
         if (separationVector.magSq() > 0) {
             if (moveDirection.magSq() > 0) {
                  moveDirection.add(separationVector.mult(0.5)).normalize();
             } else {
                  moveDirection = separationVector;
             }
        }


        // 3. Випадковий рух
        if (!seekingPrey && moveDirection.magSq() === 0) {
            if (random() < 0.05) {
                this.direction.set(randomFloat(-1, 1), randomFloat(-1, 1)).normalize();
            }
             if (this.direction.magSq() === 0) {
                 this.direction.set(randomFloat(-1, 1), randomFloat(-1, 1)).normalize();
             }
            moveDirection = this.direction;
        }
        const wallAvoidanceVector = this.calculateWallAvoidance();
        if (wallAvoidanceVector.magSq() > 0) {
             // Якщо є рух, змішуємо, інакше цей вектор стає основним
             if (moveDirection.magSq() > 0) {
                 // Додаємо з вагою (наприклад, вага стіни більша)
                 moveDirection.add(wallAvoidanceVector.mult(1.0)).normalize(); // Вага 1.0 для сили стіни
             } else {
                 moveDirection = wallAvoidanceVector;
             }
             // Можливо, скинути інші цілі, якщо активно уникаємо стіну?
             this.targetFood = null; // Для Creature
             this.targetPartner = null; // Для Creature
             this.matingPartner = null; // Для Creature
             this.targetCreature = null; // Для Predator
        }
        this.applyMovement(dt, moveDirection, currentSpeed);

        // Асексуальне Розмноження Хижаків
        if (this.readyToMate && predators.length < MAX_PREDATORS) {
            this.energy -= PREDATOR_REPRODUCTION_COST;
            // Гени просто копіюються
            const offspring = this.createOffspring(null, this.genes);
            predatorsToAdd.push(offspring);
            maxPredatorGeneration = Math.max(maxPredatorGeneration, offspring.generation);
            this.matingCooldownTimer = this.getMatingCooldown();
            this.readyToMate = false;
        }
    }

     hunt(prey) {
        if (!this.isDead && !prey.is_dead) {
            prey.is_dead = true;
            this.energy += PREDATOR_HUNT_ENERGY_GAIN;
            // Позначаємо здобич для видалення глобально
            if (!creaturesToRemove.includes(prey)) {
                creaturesToRemove.push(prey);
            }
            // console.log(`Predator ${this.generation}-${Math.round(this.pos.x)} hunted creature ${prey.generation}-${Math.round(prey.pos.x)}`);
            if (this.targetCreature === prey) {
                this.targetCreature = null;
            }
        }
    }
}


// --- Глобальні Списки Додавання/Видалення ---
let creaturesToAdd = [];
let predatorsToAdd = [];
let foodToRemove = [];
let creaturesToRemove = [];
let predatorsToRemove = [];


// --- Функції Ініціалізації та Скидання ---
function initSimulation() {
    creatures = [];
    predators = [];
    food = [];
    obstacles = [];
    maxCreatureGeneration = 0;
    maxPredatorGeneration = 0;
    simulationTime = 0.0;
    paused = false;
    selectedAgent = null;
    lastTimestamp = 0;
    history = [];
    lastLogTime = -LOG_INTERVAL;
    creaturesToAdd = [];
    predatorsToAdd = [];
    foodToRemove = [];
    creaturesToRemove = [];
    predatorsToRemove = [];


    // Створення перешкод
    for (let i = 0; i < NUM_OBSTACLES; i++) {
        obstacles.push(new Obstacle());
    }
    // Створення їжі
    for (let i = 0; i < FOOD_COUNT; i++) {
        food.push(new Food()); // Передаємо obstacles, якщо потрібно перевіряти при спавні
    }
    // Створення істот
    for (let i = 0; i < INITIAL_CREATURES; i++) {
        creatures.push(new Creature(random(CREATURE_RADIUS, WIDTH - CREATURE_RADIUS), random(CREATURE_RADIUS, HEIGHT - CREATURE_RADIUS)));
    }
    // Створення хижаків
    for (let i = 0; i < INITIAL_PREDATORS; i++) {
        predators.push(new Predator(random(PREDATOR_RADIUS, WIDTH - PREDATOR_RADIUS), random(PREDATOR_RADIUS, HEIGHT - PREDATOR_RADIUS)));
    }

    updateUI(); // Оновити UI початковими значеннями
    console.log("Simulation Initialized/Reset.");
}

function resetSimulation() {
    if (confirm("Скинути симуляцію та почати заново?")) {
        initSimulation();
        // Можливо, також очистити localStorage?
        // localStorage.removeItem('evolutionSimSave');
    }
}


// --- Функції Оновлення Світу ---
function updateWorld(dt) {
    creaturesToAdd = [];
    predatorsToAdd = [];
    foodToRemove = [];
    creaturesToRemove = [];
    predatorsToRemove = [];

    // 1. Оновлення істот
    for (const creature of creatures) {
        creature.update(dt, food, creatures, predators); // Помилка тут, має бути predators
    }


    // 2. Оновлення хижаків
    for (const predator of predators) {
        predator.update(dt, creatures, predators);
    }

    // 3. Видалення (використовуємо глобальні списки, заповнені в методах eat/hunt/update)
    food = food.filter(f => !foodToRemove.includes(f));
    // Збираємо індекси або об'єкти для видалення істот
    const initialCreatureCount = creatures.length; // Для логування
    creatures.forEach(c => {
        if (c.isDead && !creaturesToRemove.includes(c)) {
            creaturesToRemove.push(c); // Додаємо мертвих до списку на видалення
        }
    });
    creatures = creatures.filter(c => !creaturesToRemove.includes(c)); // Видаляємо тих, хто в списку
    // Перевіряємо ще раз на isDead для надійності
    creatures = creatures.filter(c => !c.isDead);
    if(creatures.length !== initialCreatureCount) {
        // console.log(`Creatures removed: ${initialCreatureCount - creatures.length}. New count: ${creatures.length}`); // Debug log
    }


    // Збираємо індекси або об'єкти для видалення хижаків
    const initialPredatorCount = predators.length; // Для логування
    predators.forEach(p => {
        if (p.isDead && !predatorsToRemove.includes(p)) {
            predatorsToRemove.push(p);
        }
    });
    predators = predators.filter(p => !predatorsToRemove.includes(p));
    predators = predators.filter(p => !p.isDead);
     if(predators.length !== initialPredatorCount) {
        // console.log(`Predators removed: ${initialPredatorCount - predators.length}. New count: ${predators.length}`); // Debug log
    }
    // creatures = creatures.filter(c => !creaturesToRemove.includes(c) && !c.is_dead);
    // predators = predators.filter(p => !predatorsToRemove.includes(p) && !p.is_dead);
    //  // Додаткова перевірка на is_dead після оновлення
    // creatures = creatures.filter(c => !c.is_dead);
    // predators = predators.filter(p => !p.is_dead);


    // 4. Додавання нащадків
    creatures.push(...creaturesToAdd);
    predators.push(...predatorsToAdd);

    // 5. Обмеження популяцій
    if (creatures.length > MAX_CREATURES) {
        creatures.sort((a, b) => a.energy - b.energy); // Сортуємо за енергією
        const removed = creatures.splice(0, creatures.length - MAX_CREATURES);
        if (removed.includes(selectedAgent)) selectedAgent = null; // Скидаємо вибір, якщо видалили
    }
     if (predators.length > MAX_PREDATORS) {
        predators.sort((a, b) => a.energy - b.energy);
        const removed = predators.splice(0, predators.length - MAX_PREDATORS);
        if (removed.includes(selectedAgent)) selectedAgent = null;
    }


    // 6. Додавання їжі
    if (food.length < FOOD_COUNT * 0.7) {
        for (let i = 0; i < 5; i++) {
             if(food.length < FOOD_COUNT * 1.2) food.push(new Food());
        }
    }

     // 7. Запис статистики для графіків
    if (simulationTime - lastLogTime >= LOG_INTERVAL) {
        lastLogTime = simulationTime;
        const stats = {
            time: simulationTime,
            creaturePop: creatures.length,
            predatorPop: predators.length,
            avgCSpeed: creatures.length > 0 ? creatures.reduce((sum, c) => sum + c.genes.speed, 0) / creatures.length : 0,
            avgCSense: creatures.length > 0 ? creatures.reduce((sum, c) => sum + c.genes.sense, 0) / creatures.length : 0,
            avgPSpeed: predators.length > 0 ? predators.reduce((sum, p) => sum + p.genes.speed, 0) / predators.length : 0,
            avgPSense: predators.length > 0 ? predators.reduce((sum, p) => sum + p.genes.sense, 0) / predators.length : 0,
        };
        history.push(stats);
        // console.log("Logged stats:", stats); // Відлагодження
    }

}

// --- Функції Малювання ---
function drawWorld(ctx) {
    // Очищення канви
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Малювання перешкод
    for (const obs of obstacles) {
        obs.draw(ctx);
    }
    // Малювання їжі
    for (const f of food) {
        f.draw(ctx);
    }
    // Малювання істот
    for (const c of creatures) {
        c.draw(ctx);
    }
    // Малювання хижаків
    for (const p of predators) {
        p.draw(ctx);
    }

    // Позначення обраного агента (малюємо ще раз зверху)
    if (selectedAgent) {
        selectedAgent.draw(ctx); // Викличе draw з підсвічуванням
    }
}

// --- Оновлення UI ---
function updateUI() {
    simTimeSpan.textContent = simulationTime.toFixed(1);
    creatureCountSpan.textContent = creatures.length;
    maxCreatureCountSpan.textContent = MAX_CREATURES;
    maxCreatureGenSpan.textContent = maxCreatureGeneration;
    predatorCountSpan.textContent = predators.length;
    maxPredatorCountSpan.textContent = MAX_PREDATORS;
    maxPredatorGenSpan.textContent = maxPredatorGeneration;
    foodCountSpan.textContent = food.length;

    avgCreatureSpeedSpan.textContent = history.length > 0 ? history[history.length-1].avgCSpeed.toFixed(2) : '0.00';
    avgCreatureSenseSpan.textContent = history.length > 0 ? history[history.length-1].avgCSense.toFixed(1) : '0.0';
    avgPredatorSpeedSpan.textContent = history.length > 0 ? history[history.length-1].avgPSpeed.toFixed(2) : '0.00';
    avgPredatorSenseSpan.textContent = history.length > 0 ? history[history.length-1].avgPSense.toFixed(1) : '0.0';


    // Оновлення інфо панелі обраного агента
    if (selectedAgent && !selectedAgent.is_dead) {
         const agentType = selectedAgent instanceof Creature ? "Істота" : "Хижак";
         selectedAgentDetailsDiv.innerHTML = `
            <p><strong>Тип:</strong> ${agentType}</p>
            <p><strong>Покоління:</strong> ${selectedAgent.generation}</p>
            <p><strong>Енергія:</strong> ${selectedAgent.energy.toFixed(1)}</p>
            <p><strong>Вік:</strong> ${selectedAgent.age.toFixed(1)} / ${selectedAgent.maxAge.toFixed(0)}с</p>
            <p><strong>Швидкість:</strong> ${selectedAgent.genes.speed.toFixed(2)}</p>
            <p><strong>Чутливість:</strong> ${selectedAgent.genes.sense.toFixed(1)}</p>
            <p><strong>Готовий спар.:</strong> ${selectedAgent.readyToMate ? 'Так' : 'Ні'}</p>
            <p><strong>Кулдаун:</strong> ${selectedAgent.matingCooldownTimer.toFixed(1)}с</p>
        `;
    } else {
        selectedAgentDetailsDiv.innerHTML = '<p>Клікніть на агента...</p>';
        if (selectedAgent && selectedAgent.is_dead) selectedAgent = null; // Скидаємо вибір, якщо мертвий
    }
}

// --- Головний Цикл ---
function gameLoop(timestamp) {
    const deltaTime = (timestamp - lastTimestamp) / 1000 || 0; // в секундах
    lastTimestamp = timestamp;

    // Обмежуємо deltaTime для стабільності
    const dt = Math.min(deltaTime, 0.1); // Максимум 10 FPS логіки

    if (!paused) {
        simulationTime += dt;
        updateWorld(dt);
    }

    drawWorld(ctx);
    updateUI();

    requestAnimationFrame(gameLoop); // Наступний кадр
}

// --- Обробники Подій ---
function setupEventListeners() {
    pauseBtn.addEventListener('click', () => {
        paused = !paused;
        pauseBtn.textContent = paused ? 'Продовжити' : 'Пауза';
        console.log(paused ? "Simulation Paused" : "Simulation Resumed");
    });

    addFoodBtn.addEventListener('click', () => {
        for (let i = 0; i < 15; i++) {
             if (food.length < FOOD_COUNT * 2) food.push(new Food());
        }
        console.log("Added food");
    });

    addCreatureBtn.addEventListener('click', () => {
         for (let i = 0; i < 5; i++) {
             if (creatures.length < MAX_CREATURES) {
                  creatures.push(new Creature(random(CREATURE_RADIUS, WIDTH - CREATURE_RADIUS), random(CREATURE_RADIUS, HEIGHT - CREATURE_RADIUS)));
             }
         }
         console.log("Added creatures");
    });

     addPredatorBtn.addEventListener('click', () => {
         if (predators.length < MAX_PREDATORS) {
             predators.push(new Predator(random(PREDATOR_RADIUS, WIDTH - PREDATOR_RADIUS), random(PREDATOR_RADIUS, HEIGHT - PREDATOR_RADIUS)));
             console.log("Added predator");
         }
    });


    saveStateBtn.addEventListener('click', saveState);
    loadStateBtn.addEventListener('click', loadState);
    resetStateBtn.addEventListener('click', resetSimulation);


    // Клік на канві для вибору агента
    canvas.addEventListener('click', (event) => {
        const rect = canvas.getBoundingClientRect();
        const clickPos = new Vec2(
            event.clientX - rect.left,
            event.clientY - rect.top
        );

        let foundAgent = null;
        // Спочатку шукаємо хижаків
        for (let i = predators.length - 1; i >= 0; i--) {
             if (predators[i].isClicked(clickPos)) {
                 foundAgent = predators[i];
                 break;
             }
        }
        // Потім істот, якщо хижака не знайдено
        if (!foundAgent) {
             for (let i = creatures.length - 1; i >= 0; i--) {
                  if (creatures[i].isClicked(clickPos)) {
                      foundAgent = creatures[i];
                      break;
                  }
             }
        }
        selectedAgent = foundAgent;
        console.log("Selected agent:", selectedAgent);
        updateUI(); // Оновити інфо панель одразу
    });
}

// --- Збереження / Завантаження (localStorage) ---

function saveState() {
    if (paused) { // Зберігаємо тільки якщо на паузі, щоб уникнути збереження некоректного стану
        try {
            const state = {
                creaturesData: creatures.map(c => c.toJSON()),
                predatorsData: predators.map(p => p.toJSON()),
                foodData: food.map(f => f.toJSON()),
                obstacleData: obstacles.map(o => o.toJSON()), // Зберігаємо дані перешкод
                maxCreatureGeneration,
                maxPredatorGeneration,
                simulationTime,
                history // Зберігаємо історію для графіків
            };
            localStorage.setItem('evolutionSimSave', JSON.stringify(state));
            console.log("Simulation state saved to localStorage.");
            alert("Стан симуляції збережено!");
        } catch (error) {
            console.error("Error saving state:", error);
            alert("Помилка збереження стану. Див. консоль.");
        }
    } else {
        alert("Будь ласка, поставте симуляцію на паузу перед збереженням.");
    }
}

function loadState() {
     if (!paused) {
         if (!confirm("Симуляція не на паузі. Завантаження може призвести до несподіванок. Продовжити?")) {
             return;
         }
     }
    try {
        const savedState = localStorage.getItem('evolutionSimSave');
        if (savedState) {
            const state = JSON.parse(savedState);

            // Очищаємо поточні списки
            creatures = [];
            predators = [];
            food = [];
            obstacles = [];

            // Відновлюємо перешкоди
             if (state.obstacleData) {
                 obstacles = state.obstacleData.map(data => Obstacle.fromJSON(data));
             } else { // Якщо дані перешкод не збереглися, генеруємо стандартні
                 for (let i = 0; i < NUM_OBSTACLES; i++) { obstacles.push(new Obstacle()); }
             }


            // Відновлюємо їжу
            if (state.foodData) {
                food = state.foodData.map(data => Food.fromJSON(data));
            }

            // Відновлюємо істот
            if (state.creaturesData) {
                 creatures = state.creaturesData.map(data => {
                     const c = new Creature(0, 0); // Створюємо тимчасовий об'єкт
                     c.restoreState(data); // Відновлюємо стан
                     return c;
                 });
            }

            // Відновлюємо хижаків
            if (state.predatorsData) {
                 predators = state.predatorsData.map(data => {
                     const p = new Predator(0, 0);
                     p.restoreState(data);
                     return p;
                 });
            }


            // Відновлюємо глобальні змінні
            maxCreatureGeneration = state.maxCreatureGeneration || 0;
            maxPredatorGeneration = state.maxPredatorGeneration || 0;
            simulationTime = state.simulationTime || 0.0;
            history = state.history || []; // Відновлюємо історію
            lastLogTime = history.length > 0 ? history[history.length - 1].time : -LOG_INTERVAL; // Оновлюємо час останнього логу

            selectedAgent = null; // Скидаємо вибір

            updateUI(); // Оновлюємо інтерфейс
            console.log("Simulation state loaded from localStorage.");
            alert("Стан симуляції завантажено.");
        } else {
            alert("Збережений стан не знайдено.");
        }
    } catch (error) {
        console.error("Error loading state:", error);
        alert("Помилка завантаження стану. Можливо, збережені дані пошкоджені. Скидання симуляції.");
        resetSimulation(); // Скидаємо симуляцію при помилці
    }
}


// --- Старт Симуляції ---
initSimulation();       // Ініціалізація початкового стану
setupEventListeners(); // Налаштування обробників подій
requestAnimationFrame(gameLoop); // Запуск головного циклу