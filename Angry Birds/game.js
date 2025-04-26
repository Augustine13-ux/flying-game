// Game constants
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const GRAVITY = 0.5;
const BIRD_RADIUS = 20;
const BLOCK_WIDTH = 40;
const BLOCK_HEIGHT = 200;
const SLINGSHOT_X = 100;
const SLINGSHOT_Y = CANVAS_HEIGHT - 100;
const MAX_POWER = 30;
const CATAPULT_ARM_LENGTH = 150;
const CATAPULT_BASE_WIDTH = 40;
const CATAPULT_BASE_HEIGHT = 60;
const MAX_PULL_DISTANCE = 200;
const MIN_ANGLE = -Math.PI / 2; // -90 degrees
const MAX_ANGLE = 0; // 0 degrees

// Get canvas and context
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

// Game state
let score = 0;
let level = 1;
let birds = [];
let blocks = [];
let currentBird = null;
let power = 0;
let maxPower = 0;
let charging = false;
let particles = [];
let catapultAngle = 0;
let catapultArmAngle = 0;
let dragging = false;
let startPos = { x: 0, y: 0 };
let endPos = { x: 0, y: 0 };
let pullDistance = 0;
let aimAngle = -Math.PI / 4; // Default 45 degrees upward

// Particle class for effects
class Particle {
    constructor(x, y, color) {
        this.x = x;
        this.y = y;
        this.color = color;
        this.size = Math.random() * 3 + 2;
        this.speedX = (Math.random() - 0.5) * 8;
        this.speedY = (Math.random() - 0.5) * 8;
        this.life = 1;
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.life -= 0.02;
    }

    draw() {
        ctx.globalAlpha = this.life;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.globalAlpha = 1;
    }
}

// Bird class
class Bird {
    constructor(x, y, type = 'red') {
        this.x = x;
        this.y = y;
        this.type = type;
        this.radius = BIRD_RADIUS;
        this.velocity = { x: 0, y: 0 };
        this.launched = false;
        this.specialUsed = false;
        this.rotation = 0;
        this.color = type === 'red' ? '#ff0000' : 
                    type === 'yellow' ? '#ffff00' : 
                    type === 'blue' ? '#0000ff' : '#000000';
        this.trail = [];
    }

    draw() {
        // Draw trail
        for (let i = 0; i < this.trail.length; i++) {
            const alpha = i / this.trail.length;
            ctx.beginPath();
            ctx.arc(this.trail[i].x, this.trail[i].y, this.radius * 0.8, 0, Math.PI * 2);
            ctx.fillStyle = this.color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
            ctx.fill();
            ctx.closePath();
        }

        // Save context for rotation
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);

        // Draw body
        ctx.beginPath();
        ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.closePath();

        // Draw eyes
        ctx.beginPath();
        ctx.arc(5, -5, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'white';
        ctx.fill();
        ctx.closePath();

        ctx.beginPath();
        ctx.arc(5, -5, 2, 0, Math.PI * 2);
        ctx.fillStyle = 'black';
        ctx.fill();
        ctx.closePath();

        // Draw beak
        ctx.beginPath();
        ctx.moveTo(10, 0);
        ctx.lineTo(20, 0);
        ctx.lineTo(10, 5);
        ctx.fillStyle = '#FFA500';
        ctx.fill();
        ctx.closePath();

        ctx.restore();
    }

    update() {
        if (this.launched) {
            // Update trail
            this.trail.unshift({ x: this.x, y: this.y });
            if (this.trail.length > 10) this.trail.pop();

            // Update position and rotation
            this.velocity.y += GRAVITY;
            this.x += this.velocity.x;
            this.y += this.velocity.y;
            this.rotation = Math.atan2(this.velocity.y, this.velocity.x);

            // Add particles
            if (Math.random() < 0.3) {
                particles.push(new Particle(this.x, this.y, this.color));
            }
        }
    }

    launch(power, angle) {
        if (!this.launched) {
            this.launched = true;
            this.velocity.x = power * Math.cos(angle);
            this.velocity.y = -power * Math.sin(angle);
            // Add launch particles
            for (let i = 0; i < 20; i++) {
                particles.push(new Particle(this.x, this.y, this.color));
            }
        }
    }

    useSpecial() {
        if (this.launched && !this.specialUsed) {
            if (this.type === 'yellow') {
                this.velocity.x *= 1.5;
                this.velocity.y *= 1.5;
                // Add boost particles
                for (let i = 0; i < 30; i++) {
                    particles.push(new Particle(this.x, this.y, '#ffff00'));
                }
            } else if (this.type === 'blue') {
                const newBirds = [
                    new Bird(this.x, this.y, 'blue'),
                    new Bird(this.x, this.y, 'blue')
                ];
                newBirds[0].velocity = { x: this.velocity.x + 5, y: this.velocity.y };
                newBirds[1].velocity = { x: this.velocity.x - 5, y: this.velocity.y };
                birds.push(...newBirds);
                // Add split particles
                for (let i = 0; i < 40; i++) {
                    particles.push(new Particle(this.x, this.y, '#0000ff'));
                }
            } else if (this.type === 'black') {
                blocks.forEach(block => {
                    const dx = block.x - this.x;
                    const dy = block.y - this.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 100) {
                        block.health -= 50;
                        // Add explosion particles
                        for (let i = 0; i < 20; i++) {
                            particles.push(new Particle(block.x, block.y, '#000000'));
                        }
                    }
                });
            }
            this.specialUsed = true;
        }
    }
}

// Block class
class Block {
    constructor(x, y, type = 'wood') {
        this.x = x;
        this.y = y;
        this.type = type;
        this.width = BLOCK_WIDTH;
        this.height = BLOCK_HEIGHT;
        this.health = type === 'wood' ? 100 : type === 'stone' ? 200 : 50;
        this.destroyed = false;
        this.color = type === 'wood' ? '#8B4513' : 
                    type === 'stone' ? '#808080' : '#00ff00';
        this.rotation = 0;
    }

    draw() {
        if (!this.destroyed) {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);

            // Draw block
            ctx.fillStyle = this.color;
            ctx.fillRect(-this.width/2, -this.height/2, this.width, this.height);

            // Draw wood grain or stone texture
            if (this.type === 'wood') {
                ctx.strokeStyle = '#654321';
                for (let i = 0; i < 5; i++) {
                    ctx.beginPath();
                    ctx.moveTo(-this.width/2, -this.height/2 + i * this.height/5);
                    ctx.lineTo(this.width/2, -this.height/2 + i * this.height/5);
                    ctx.stroke();
                }
            } else if (this.type === 'stone') {
                ctx.strokeStyle = '#404040';
                for (let i = 0; i < 3; i++) {
                    for (let j = 0; j < 3; j++) {
                        ctx.strokeRect(
                            -this.width/2 + i * this.width/3,
                            -this.height/2 + j * this.height/3,
                            this.width/3,
                            this.height/3
                        );
                    }
                }
            }

            ctx.restore();

            // Draw health bar
            const healthWidth = (this.health / 100) * this.width;
            ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
            ctx.fillRect(this.x - this.width/2, this.y - this.height/2 - 5, this.width, 3);
            ctx.fillStyle = 'rgba(0, 255, 0, 0.5)';
            ctx.fillRect(this.x - this.width/2, this.y - this.height/2 - 5, healthWidth, 3);
        }
    }
}

// Create level
function createLevel(levelNum) {
    blocks = [];
    if (levelNum === 1) {
        blocks = [
            new Block(600, CANVAS_HEIGHT - 100, 'wood'),
            new Block(700, CANVAS_HEIGHT - 100, 'wood'),
            new Block(650, CANVAS_HEIGHT - 200, 'wood')
        ];
    } else if (levelNum === 2) {
        blocks = [
            new Block(600, CANVAS_HEIGHT - 100, 'stone'),
            new Block(700, CANVAS_HEIGHT - 100, 'wood'),
            new Block(650, CANVAS_HEIGHT - 200, 'wood'),
            new Block(600, CANVAS_HEIGHT - 300, 'wood')
        ];
    }
}

// Initialize game
function init() {
    birds = [new Bird(SLINGSHOT_X + CATAPULT_ARM_LENGTH, CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT, 'red')];
    createLevel(level);
    updateUI();
}

// Update UI
function updateUI() {
    document.getElementById('score').textContent = `Score: ${score}`;
    document.getElementById('level').textContent = `Level: ${level}`;
    document.getElementById('birds').textContent = `Birds: ${birds.length}`;
}

// Check collisions
function checkCollisions() {
    birds.forEach(bird => {
        if (bird.launched) {
            blocks.forEach(block => {
                if (!block.destroyed) {
                    const dx = bird.x - block.x;
                    const dy = bird.y - block.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < BIRD_RADIUS + block.width/2) {
                        block.health -= 50;
                        block.rotation += Math.random() * 0.2 - 0.1;
                        if (block.health <= 0) {
                            block.destroyed = true;
                            score += 100;
                            updateUI();
                            // Add destruction particles
                            for (let i = 0; i < 30; i++) {
                                particles.push(new Particle(block.x, block.y, block.color));
                            }
                        }
                    }
                }
            });
        }
    });
}

// Check level complete
function checkLevelComplete() {
    return blocks.every(block => block.destroyed);
}

// Next level
function nextLevel() {
    level++;
    score += 1000;
    createLevel(level);
    birds = [new Bird(SLINGSHOT_X + CATAPULT_ARM_LENGTH, CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT, 'red')];
    updateUI();
}

// Draw catapult
function drawCatapult() {
    // Draw base
    ctx.fillStyle = '#8B4513';
    ctx.fillRect(SLINGSHOT_X - CATAPULT_BASE_WIDTH/2, 
                CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT, 
                CATAPULT_BASE_WIDTH, 
                CATAPULT_BASE_HEIGHT);

    // Draw arm
    ctx.save();
    ctx.translate(SLINGSHOT_X, CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT);
    ctx.rotate(aimAngle);
    
    // Draw arm
    ctx.fillStyle = '#654321';
    ctx.fillRect(-pullDistance, -10, CATAPULT_ARM_LENGTH, 20);
    
    // Draw bucket
    ctx.beginPath();
    ctx.arc(CATAPULT_ARM_LENGTH - pullDistance, 0, 30, 0, Math.PI * 2);
    ctx.fillStyle = '#8B4513';
    ctx.fill();
    ctx.closePath();
    
    ctx.restore();

    // Draw aim line
    if (!birds[0].launched) {
        ctx.beginPath();
        ctx.moveTo(SLINGSHOT_X, CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT);
        ctx.lineTo(
            SLINGSHOT_X + Math.cos(aimAngle) * 200,
            CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT + Math.sin(aimAngle) * 200
        );
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.setLineDash([5, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // Draw power meter if dragging
    if (dragging) {
        const powerWidth = (pullDistance / MAX_PULL_DISTANCE) * 100;
        
        // Draw power meter background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(10, 10, 104, 24);
        
        // Draw power meter
        const powerGradient = ctx.createLinearGradient(12, 12, 12 + powerWidth, 12);
        powerGradient.addColorStop(0, '#00ff00');
        powerGradient.addColorStop(0.5, '#ffff00');
        powerGradient.addColorStop(1, '#ff0000');
        ctx.fillStyle = powerGradient;
        ctx.fillRect(12, 12, powerWidth, 20);
    }
}

// Game loop
function gameLoop() {
    // Clear canvas
    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Draw background
    const gradient = ctx.createLinearGradient(0, 0, 0, CANVAS_HEIGHT);
    gradient.addColorStop(0, '#87CEEB');
    gradient.addColorStop(1, '#E0F7FF');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Draw ground
    const groundGradient = ctx.createLinearGradient(0, CANVAS_HEIGHT - 50, 0, CANVAS_HEIGHT);
    groundGradient.addColorStop(0, '#228B22');
    groundGradient.addColorStop(1, '#006400');
    ctx.fillStyle = groundGradient;
    ctx.fillRect(0, CANVAS_HEIGHT - 50, CANVAS_WIDTH, 50);

    // Draw clouds
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    for (let i = 0; i < 5; i++) {
        const x = (i * 200 + Math.sin(Date.now() / 2000 + i) * 20) % CANVAS_WIDTH;
        const y = 50 + i * 40;
        ctx.beginPath();
        ctx.arc(x, y, 30, 0, Math.PI * 2);
        ctx.arc(x + 25, y - 10, 25, 0, Math.PI * 2);
        ctx.arc(x + 25, y + 10, 25, 0, Math.PI * 2);
        ctx.arc(x + 50, y, 30, 0, Math.PI * 2);
        ctx.fill();
    }

    // Draw catapult
    drawCatapult();

    // Update and draw particles
    particles = particles.filter(particle => particle.life > 0);
    particles.forEach(particle => {
        particle.update();
        particle.draw();
    });

    // Update and draw birds
    birds.forEach(bird => {
        bird.update();
        bird.draw();
    });

    // Draw blocks
    blocks.forEach(block => block.draw());

    // Check collisions
    checkCollisions();

    // Check if current bird is out of bounds or stopped
    if (birds.length > 0 && birds[0].launched) {
        const bird = birds[0];
        if (bird.x > CANVAS_WIDTH || bird.y > CANVAS_HEIGHT || 
            (Math.abs(bird.velocity.x) < 0.1 && Math.abs(bird.velocity.y) < 0.1 && bird.y > CANVAS_HEIGHT - 100)) {
            birds.shift();
            if (birds.length === 0) {
                if (checkLevelComplete()) {
                    nextLevel();
                } else {
                    birds = [new Bird(SLINGSHOT_X + CATAPULT_ARM_LENGTH, CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT, 'red')];
                }
            }
        }
    }

    requestAnimationFrame(gameLoop);
}

// Event listeners
canvas.addEventListener('mousedown', (e) => {
    if (birds.length > 0 && !birds[0].launched) {
        const bird = birds[0];
        const dx = e.offsetX - bird.x;
        const dy = e.offsetY - bird.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < BIRD_RADIUS * 2) {
            dragging = true;
            startPos = { x: e.offsetX, y: e.offsetY };
            endPos = { x: e.offsetX, y: e.offsetY };
        }
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (dragging) {
        endPos = { x: e.offsetX, y: e.offsetY };
        
        // Calculate pull distance (only horizontal)
        pullDistance = Math.min(Math.max(0, startPos.x - endPos.x), MAX_PULL_DISTANCE);
        
        // Calculate aim angle based on mouse position
        const dx = e.offsetX - SLINGSHOT_X;
        const dy = e.offsetY - (CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT);
        aimAngle = Math.max(MIN_ANGLE, Math.min(MAX_ANGLE, Math.atan2(dy, dx)));
        
        // Update bird position
        if (birds.length > 0) {
            const bird = birds[0];
            bird.x = SLINGSHOT_X + Math.cos(aimAngle) * (CATAPULT_ARM_LENGTH - pullDistance);
            bird.y = (CANVAS_HEIGHT - CATAPULT_BASE_HEIGHT) + Math.sin(aimAngle) * (CATAPULT_ARM_LENGTH - pullDistance);
        }
    }
});

canvas.addEventListener('mouseup', (e) => {
    if (dragging) {
        dragging = false;
    }
});

document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && birds.length > 0 && !birds[0].launched) {
        const bird = birds[0];
        const power = (pullDistance / MAX_PULL_DISTANCE) * MAX_POWER;
        bird.launch(power, aimAngle);
        pullDistance = 0;
    }
});

// Start game
init();
gameLoop(); 