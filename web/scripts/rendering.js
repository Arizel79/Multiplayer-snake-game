function renderGame() {
    if (!gameState.gameState) return;

    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, width, height);

    const center = getVisibleAreaCenter();
    if (!center) return;

    renderGrid(center);

    renderBorders(center);

    renderOtherSnakes(center);
    renderMySnake(center);

    renderFood(center);

    renderUI();
}

function getVisibleAreaCenter() {
    if (!gameState.gameState || !gameState.playerId) return null;

    const mySnake = gameState.gameState.snakes[gameState.playerId];
    if (!mySnake || mySnake.body.length === 0) return null;

    return {
        x: mySnake.body[0].x,
        y: mySnake.body[0].y
    };
}

function renderGrid(center) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;

    const borders = gameState.gameState.map_borders;
    const cellSize = CELL_SIZE;

    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;

    // View zone calc
    const visibleLeft = center.x - Math.floor(width / (2 * cellSize)) - 1;
    const visibleRight = center.x + Math.floor(width / (2 * cellSize)) + 1;
    const visibleTop = center.y - Math.floor(height / (2 * cellSize)) - 1;
    const visibleBottom = center.y + Math.floor(height / (2 * cellSize)) + 1;

    const startX = Math.max(borders[0], visibleLeft);
    const endX = Math.min(borders[2], visibleRight);
    const startY = Math.max(borders[1], visibleTop);
    const endY = Math.min(borders[3], visibleBottom);

    // Grid
    for (let x = startX; x <= endX; x++) {
        for (let y = startY; y <= endY; y++) {
            const screenX = width / 2 + (x - center.x) * cellSize;
            const screenY = height / 2 + (y - center.y) * cellSize;

            if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
                ctx.strokeRect(screenX, screenY, cellSize, cellSize);
            }
        }
    }
}

function renderBorders(center) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;

    const borders = gameState.gameState.map_borders;
    const cellSize = CELL_SIZE;

    ctx.fillStyle = COLORS.border;

    for (let x = borders[0] - 1; x <= borders[2] + 1; x++) {
        let screenX = width / 2 + (x - center.x) * cellSize;
        let screenY = height / 2 + (borders[1] - 1 - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }

        screenY = height / 2 + (borders[3] + 1 - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }
    }

    for (let y = borders[1]; y <= borders[3]; y++) {
        let screenX = width / 2 + (borders[0] - 1 - center.x) * cellSize;
        let screenY = height / 2 + (y - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }

        screenX = width / 2 + (borders[2] + 1 - center.x) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }
    }
}

function renderFood(center) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const cellSize = CELL_SIZE;

    gameState.gameState.food.forEach(food => {
        const screenX = width / 2 + (food.x - center.x) * cellSize;
        const screenY = height / 2 + (food.y - center.y) * cellSize;

        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {

            let size;
            if (food.type === "default") {
                size = cellSize / 6;
            } else if (food.type === "death") {
                size = cellSize / 4;
            } else {
                size = cellSize / 4;
            }

            ctx.beginPath();
            ctx.fillStyle = food.color || COLORS.food;
            ctx.arc(
                screenX + cellSize / 2,
                screenY + cellSize / 2,
                size,
                0,
                Math.PI * 2
            );
            ctx.fill();
        }
    });
}

function renderOtherSnakes(center) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const cellSize = CELL_SIZE;

    Object.entries(gameState.gameState.snakes).forEach(([id, snake]) => {
        if (id === gameState.playerId) return;
        renderSnake(snake, center, false);
    });
}

function renderMySnake(center) {
    if (!gameState.playerId) return;

    const mySnake = gameState.gameState.snakes[gameState.playerId];
    if (!mySnake) return;

    renderSnake(mySnake, center, true);
}



function getColorValue(colorName) {
    if (SNAKE_COLORS_MAP.hasOwnProperty(colorName)) {
        return SNAKE_COLORS_MAP[colorName];
    }
    return colorName;
}

function renderSnake(snake, center, isMe) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const cellSize = CELL_SIZE;

    const headColor = snake.color?.head;
    const bodyColors = snake.color?.body || [];
    const hasCustomColors = bodyColors.length > 0 || headColor;
    const defaultColor = getSnakeColor(snake);

snake.body.forEach((segment, index) => {
    const screenX = width / 2 + (segment.x - center.x) * cellSize;
    const screenY = height / 2 + (segment.y - center.y) * cellSize;

    if (screenX >= -cellSize && screenX <= width + cellSize &&
        screenY >= -cellSize && screenY <= height + cellSize) {

        // Neon light
        if (snake.alive && snake.is_fast) {
            ctx.shadowBlur = 15;
            ctx.shadowColor = getNeonGlowColor(snake, index, defaultColor);

            ctx.globalAlpha = 0.2;
            ctx.fillStyle = getColorValue(getSegmentColor(snake, index, defaultColor, hasCustomColors, headColor, bodyColors));
            ctx.fillRect(screenX - 2, screenY - 2, cellSize + 4, cellSize + 4);

            ctx.globalAlpha = 0.1;
            ctx.fillRect(screenX - 4, screenY - 4, cellSize + 8, cellSize + 8);

            ctx.globalAlpha = 0.001;
            ctx.fillRect(screenX - 6, screenY - 6, cellSize + 12, cellSize + 12);

            ctx.globalAlpha = 1.0;
            ctx.shadowBlur = 0;
        }

        if (!snake.alive) {
            ctx.fillStyle = COLORS.dead;
        } else if (hasCustomColors) {
            if (index === 0) {
                const colorName = headColor || bodyColors[0] || defaultColor;
                ctx.fillStyle = getColorValue(colorName);
            } else {
                const colorIndex = (index - (headColor ? 1 : 0)) % bodyColors.length;
                const colorName = bodyColors[colorIndex] || defaultColor;
                ctx.fillStyle = getColorValue(colorName);
            }
        } else {
            ctx.fillStyle = defaultColor;
        }

        ctx.fillRect(screenX, screenY, cellSize, cellSize);

        if (index === 0 && snake.alive) {
            drawSnakeEyes(ctx, screenX, screenY, cellSize, snake.direction);
        }
    }
});

function getSegmentColor(snake, index, defaultColor, hasCustomColors, headColor, bodyColors) {
    if (!snake.alive) return COLORS.dead;

    if (hasCustomColors) {
        if (index === 0) {
            return headColor || bodyColors[0] || defaultColor;
        } else {
            const colorIndex = (index - (headColor ? 1 : 0)) % bodyColors.length;
            return bodyColors[colorIndex] || defaultColor;
        }
    } else {
        return defaultColor;
    }
}

function getNeonGlowColor(snake, index, defaultColor) {
    if (snake.color?.head || snake.color?.body?.length > 0) {
        const segmentColor = getSegmentColor(snake, index, defaultColor, true, snake.color.head, snake.color.body || []);
        return getColorValue(segmentColor);
    }

    const baseColor = defaultColor.toLowerCase();
    if (baseColor.includes('blue') || baseColor.includes('light_blue') || baseColor.includes('cyan')) {
        return '#00ffff';
    } else if (baseColor.includes('green') || baseColor.includes('lime')) {
        return '#00ff00';
    } else if (baseColor.includes('red') || baseColor.includes('orange')) {
        return '#ff0000';
    } else if (baseColor.includes('yellow')) {
        return '#ffff00';
    } else if (baseColor.includes('violet') || baseColor.includes('magenta')) {
        return '#ff00ff';
    } else {
        return '#ffffff';
    }
}
    // Snake name
    if ((snake.name && snake.alive && snake.body.length > 0) && !isMe) {
        const head = snake.body[0];
        const screenX = width / 2 + (head.x - center.x) * cellSize;
        const screenY = height / 2 + (head.y - center.y) * cellSize;

        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {

            const textColor = headColor || defaultColor;
            ctx.fillStyle = getColorValue(textColor);
            ctx.font = `bold ${Math.max(12, cellSize * 0.7)}px monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';

            const textX = screenX + cellSize / 2;
            const textY = screenY - 5;

            ctx.strokeStyle = 'black';
            ctx.lineWidth = 2;
            ctx.strokeText(snake.name, textX, textY);

            ctx.fillText(snake.name, textX, textY);
        }
    }
}
function drawSnakeEyes(ctx, x, y, size, direction) {
    const eyeSize = size / 8;
    const offset = size / 4;

    ctx.fillStyle = "#000000";

    switch (direction) {
        case "up":
            ctx.beginPath();
            ctx.arc(x + size / 3, y + offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.arc(x + 2 * size / 3, y + offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "down":
            ctx.beginPath();
            ctx.arc(x + size / 3, y + size - offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.arc(x + 2 * size / 3, y + size - offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "left":
            ctx.beginPath();
            ctx.arc(x + offset, y + size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.arc(x + offset, y + 2 * size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "right":
            ctx.beginPath();
            ctx.arc(x + size - offset, y + size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.arc(x + size - offset, y + 2 * size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;
    }
}

function renderUI() {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;

    if (gameState.showDebug) {
        updateDebugInfo();
    }
}

function getSnakeColor(snake) {
    if (!snake.color) return COLORS.white;

    if (snake.color.head) {
        return COLORS[snake.color.head] || COLORS.white;
    }

    return COLORS[snake.color] || COLORS.white;
}

function getPlayerColor(playerId) {
    if (!gameState.gameState || !gameState.gameState.snakes[playerId]) return COLORS.white;

    const snake = gameState.gameState.snakes[playerId];
    return getSnakeColor(snake);
}
