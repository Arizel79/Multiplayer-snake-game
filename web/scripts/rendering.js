function renderGame() {
    if (!gameState.gameState) return;

    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;

    // Очистка экрана
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, width, height);

    // Получаем координаты центра (голова нашей змейки)
    const center = getVisibleAreaCenter();
    if (!center) return;

    // Отрисовка сетки
    renderGrid(center);

    // Отрисовка границ
    renderBorders(center);

    // Отрисовка змеек (сначала других игроков, потом свою)
    renderOtherSnakes(center);
    renderMySnake(center);

    // Отрисовка еды
    renderFood(center);

    // Отрисовка UI
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

    // Рассчитываем видимую область
    const visibleLeft = center.x - Math.floor(width / (2 * cellSize)) - 1;
    const visibleRight = center.x + Math.floor(width / (2 * cellSize)) + 1;
    const visibleTop = center.y - Math.floor(height / (2 * cellSize)) - 1;
    const visibleBottom = center.y + Math.floor(height / (2 * cellSize)) + 1;

    // Ограничиваем видимую область границами карты
    const startX = Math.max(borders[0], visibleLeft);
    const endX = Math.min(borders[2], visibleRight);
    const startY = Math.max(borders[1], visibleTop);
    const endY = Math.min(borders[3], visibleBottom);

    // Рисуем сетку
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

    // Верхняя и нижняя границы
    for (let x = borders[0] - 1; x <= borders[2] + 1; x++) {
        // Верхняя граница
        let screenX = width / 2 + (x - center.x) * cellSize;
        let screenY = height / 2 + (borders[1] - 1 - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }

        // Нижняя граница
        screenY = height / 2 + (borders[3] + 1 - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }
    }

    // Левая и правая границы (исключая углы, которые уже отрисованы)
    for (let y = borders[1]; y <= borders[3]; y++) {
        // Левая граница
        let screenX = width / 2 + (borders[0] - 1 - center.x) * cellSize;
        let screenY = height / 2 + (y - center.y) * cellSize;
        if (screenX >= 0 && screenX <= width && screenY >= 0 && screenY <= height) {
            ctx.fillRect(screenX, screenY, cellSize, cellSize);
        }

        // Правая граница
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

        // Проверяем видимость пищи на экране
        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {

            // Определяем размер в зависимости от типа
            let size;
            if (food.type === "default") {
                size = cellSize / 6;
            } else if (food.type === "death") {
                size = cellSize / 4;
            } else {
                size = cellSize / 4; // Значение по умолчанию
            }

            // Рисуем элемент
            ctx.beginPath();
            ctx.fillStyle = food.color || COLORS.food; // Используем цвет по умолчанию если не указан
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



// Цветовая карта в формате, понятном для canvas
const SNAKE_COLORS_MAP = {
    "white": "rgb(255, 255, 255)",
    "red": "rgb(255, 50, 50)",
    "orange": "#fc8105",
    "yellow": "rgb(255, 255, 50)",
    "green": "rgb(50, 255, 50)",
    "lime": "#adf542",
    "turquoise": "#05fc9d",
    "cyan": "#00FFFF",
    "light_blue": "#1999ff",
    "blue": "#3232FF",
    "violet": "#7F00FE",
    "magenta": "rgb(255, 50, 255)",
};

function getColorValue(colorName) {
    // Если цвет есть в карте, возвращаем его значение
    if (SNAKE_COLORS_MAP.hasOwnProperty(colorName)) {
        return SNAKE_COLORS_MAP[colorName];
    }
    // Иначе возвращаем как есть (может быть валидным CSS-цветом)
    return colorName;
}

function renderSnake(snake, center, isMe) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const cellSize = CELL_SIZE;

    // Получаем цвета
    const headColor = snake.color?.head;
    const bodyColors = snake.color?.body || [];
    const hasCustomColors = bodyColors.length > 0 || headColor;
    const defaultColor = getSnakeColor(snake);

    // 1. Сначала рисуем ВСЕ сегменты тела (включая голову)
snake.body.forEach((segment, index) => {
    const screenX = width / 2 + (segment.x - center.x) * cellSize;
    const screenY = height / 2 + (segment.y - center.y) * cellSize;

    if (screenX >= -cellSize && screenX <= width + cellSize &&
        screenY >= -cellSize && screenY <= height + cellSize) {

        // Неоновое свечение для быстрой змейки
        if (snake.alive && snake.is_fast) {
            // Рисуем свечение (3 слоя с разной прозрачностью)
            ctx.shadowBlur = 15;
            ctx.shadowColor = getNeonGlowColor(snake, index, defaultColor);

            // Первый слой свечения
            ctx.globalAlpha = 0.2;
            ctx.fillStyle = getColorValue(getSegmentColor(snake, index, defaultColor, hasCustomColors, headColor, bodyColors));
            ctx.fillRect(screenX - 2, screenY - 2, cellSize + 4, cellSize + 4);

            // Второй слой свечения
            ctx.globalAlpha = 0.1;
            ctx.fillRect(screenX - 4, screenY - 4, cellSize + 8, cellSize + 8);

            // Третий слой свечения
            ctx.globalAlpha = 0.001;
            ctx.fillRect(screenX - 6, screenY - 6, cellSize + 12, cellSize + 12);

            // Сбрасываем настройки
            ctx.globalAlpha = 1.0;
            ctx.shadowBlur = 0;
        }

        // Устанавливаем цвет сегмента
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

        // Рисуем сегмент
        ctx.fillRect(screenX, screenY, cellSize, cellSize);

        // Глаза рисуем сразу (они часть головы)
        if (index === 0 && snake.alive) {
            drawSnakeEyes(ctx, screenX, screenY, cellSize, snake.direction);
        }
    }
});

// Вспомогательная функция для получения цвета сегмента
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
    // Если у змейки есть кастомные цвета, используем цвет текущего сегмента
    if (snake.color?.head || snake.color?.body?.length > 0) {
        const segmentColor = getSegmentColor(snake, index, defaultColor, true, snake.color.head, snake.color.body || []);
        return getColorValue(segmentColor);
    }

    // Иначе используем цвет по умолчанию с неоновым оттенком
    const baseColor = defaultColor.toLowerCase();
    if (baseColor.includes('blue') || baseColor.includes('light_blue') || baseColor.includes('cyan')) {
        return '#00ffff'; // Неоновый голубой
    } else if (baseColor.includes('green') || baseColor.includes('lime')) {
        return '#00ff00'; // Неоновый зеленый
    } else if (baseColor.includes('red') || baseColor.includes('orange')) {
        return '#ff0000'; // Неоновый красный
    } else if (baseColor.includes('yellow')) {
        return '#ffff00'; // Неоновый желтый
    } else if (baseColor.includes('violet') || baseColor.includes('magenta')) {
        return '#ff00ff'; // Неоновый пурпурный
    } else {
        return '#ffffff'; // Белый по умолчанию
    }
}

    // 2. Только после отрисовки тела рисуем никнейм ПОВЕРХ всего
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

//    // Размер змейки
//    if (gameState.playerId && gameState.gameState.snakes[gameState.playerId]) {
//        const size = gameState.gameState.snakes[gameState.playerId].size || 0;
//        ctx.fillStyle = COLORS.text;
//        ctx.font = "20px Arial";
//        ctx.fillText(`Size: ${size}`, 10, 30);
//    }

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
