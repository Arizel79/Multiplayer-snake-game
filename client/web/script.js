// Основные константы и переменные
const CELL_SIZE = 20;
const COLORS = {
    white: "#ffffff",
    red: "#ff3232",
    orange: "#fc8105",
    yellow: "#ffff32",
    green: "#32ff32",
    lime: "#adf542",
    turquoise: "#05fc9d",
    cyan: "#00ffff",
    light_blue: "#1999ff",
    blue: "#3232ff",
    violet: "#7f00fe",
    magenta: "#ff32ff",
    dead: "#464646",
    border: "#646464",
    food: "#ff3232",
    grid: "#282828",
    background: "#141414",
    text: "#ffffff"
};

// Состояние игры
const gameState = {
    canvas: null,
    ctx: null,
    socket: null,
    playerId: null,
    playerName: "",
    serverAddress: "",
    gameRunning: false,
    showChat: false,
    showTablist: false,
    showDebug: false,
    chatInput: "",
    chatMessages: [],
    gameState: null,
    lastDirection: null,
    keysPressed: {},
    deathMessage: "",
    serverDescription: "Welcome to server!",
    alertData: null
};

// Инициализация игры
function initGame() {
    gameState.canvas = document.getElementById("game-canvas");
    gameState.ctx = gameState.canvas.getContext("2d");

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Обработчики событий
    document.getElementById("play-button").addEventListener("click", startGame);
    document.getElementById("chat-input").addEventListener("keydown", handleChatInput);

    // Глобальные обработчики клавиш
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);

    // Загрузка сохраненных настроек
    loadSettings();
}

function resizeCanvas() {
    gameState.canvas.width = window.innerWidth;
    gameState.canvas.height = window.innerHeight;
    if (gameState.gameRunning) {
        renderGame();
    }
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem("snakeGameSettings")) || {};
    document.getElementById("name-input").value = settings.playerName || "player_web";
    document.getElementById("server-input").value = settings.serverAddress || "localhost:8090";
}

function saveSettings() {
    const settings = {
        playerName: gameState.playerName,
        serverAddress: gameState.serverAddress
    };
    localStorage.setItem("snakeGameSettings", JSON.stringify(settings));
}

// Запуск игры
function startGame() {
    gameState.playerName = document.getElementById("name-input").value.trim();
    gameState.serverAddress = document.getElementById("server-input").value.trim();

    if (!gameState.playerName) {
        alert("Please enter your name");
        return;
    }

    if (!gameState.serverAddress) {
        alert("Please enter server address");
        return;
    }

    saveSettings();

    // Скрываем меню
    document.getElementById("main-menu").style.display = "none";

    // Подключаемся к серверу
    connectToServer();
}

function connectToServer() {
    try {
        gameState.socket = new WebSocket("ws://" + gameState.serverAddress);

        gameState.socket.onopen = () => {
            console.log("Connected to server");
            gameState.gameRunning = true;

            // Отправляем данные игрока
            gameState.socket.send(JSON.stringify({
                name: gameState.playerName,
                color: "green" // Можно добавить выбор цвета
            }));

            // Начинаем игровой цикл
            gameLoop();
        };

        gameState.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        gameState.socket.onclose = () => {
            console.log("Disconnected from server");
            showAlert("Disconnected", "Server closed the connection", "Press SPACE to return to menu");
            gameState.gameRunning = false;
        };

        gameState.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            showAlert("Connection Error", `Failed to connect to ${gameState.serverAddress}`, "Press SPACE to return to menu");
            gameState.gameRunning = false;
        };

    } catch (error) {
        console.error("Connection error:", error);
        showAlert("Connection Error", `Invalid server address: ${gameState.serverAddress}`, "Press SPACE to return to menu");
        gameState.gameRunning = false;
    }
}

function handleServerMessage(data) {
    switch (data.type) {

        case "player_id":
            gameState.playerId = data.player_id;
            break;

        case "game_state":
            gameState.gameState = data;
            break;

        case "chat_message":
            addChatMessage(data);
            break;

        case "set_server_desc":
            gameState.serverDescription = data.data;
            break;

        case "you_died":
            gameState.deathMessage = data.data || "You died";
            showDeathScreen(data);
            break;

        case "connection_error":
            showAlert("Connection Error", data.data, "Press SPACE to return to menu");
            gameState.gameRunning = false;
            break;

        default:
            console.log("Unknown message type:", data.type);
    }
}

// Игровой цикл
function gameLoop() {
    if (!gameState.gameRunning) return;

    // Обработка ввода
    handleMovementInput();

    // Отрисовка
    renderGame();

    // Следующий кадр
    requestAnimationFrame(gameLoop);
}

function handleMovementInput() {
    if (!gameState.socket || !gameState.gameState || !gameState.gameState.snakes[gameState.playerId]?.alive) return;

    let direction = null;

    if (gameState.keysPressed["w"] || gameState.keysPressed["ArrowUp"]) {
        direction = "up";
    } else if (gameState.keysPressed["s"] || gameState.keysPressed["ArrowDown"]) {
        direction = "down";
    } else if (gameState.keysPressed["a"] || gameState.keysPressed["ArrowLeft"]) {
        direction = "left";
    } else if (gameState.keysPressed["d"] || gameState.keysPressed["ArrowRight"]) {
        direction = "right";
    }

    if (direction && direction !== gameState.lastDirection) {
        gameState.socket.send(JSON.stringify({
            type: "direction",
            data: direction
        }));
        gameState.lastDirection = direction;
    }
}

function handleKeyDown(event) {
    // Не обрабатываем, если ввод идет в чат
    if (gameState.showChat && event.key !== "Enter" && event.key !== "Escape") {
        return;
    }

    gameState.keysPressed[event.key] = true;

    switch (event.key) {
        case "t":
            if (gameState.gameRunning) {
                toggleChat();
            }
            break;

        case "Tab":
            if (gameState.gameRunning) {
                event.preventDefault();
                toggleTablist();
            }
            break;

        case "F3":
            toggleDebugInfo();
            break;

        case " ":
            if (document.getElementById("death-screen").style.display === "flex") {
                respawn();
            } else if (document.getElementById("alert-screen").style.display === "flex") {
                closeAlert();
            }
            break;

        case "Escape":
            if (gameState.showChat) {
                closeChat();
            } else if (gameState.showTablist) {
                closeTablist();
            }
            break;
    }
}

function handleKeyUp(event) {
    gameState.keysPressed[event.key] = false;

    // Сбрасываем последнее направление, когда клавиша отпущена
    if (["w", "ArrowUp", "s", "ArrowDown", "a", "ArrowLeft", "d", "ArrowRight"].includes(event.key)) {
        gameState.lastDirection = null;
    }
}

function handleChatInput(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    } else if (event.key === "Escape") {
        closeChat();
    }
}

function toggleChat() {
    gameState.showChat = !gameState.showChat;
    const chatContainer = document.getElementById("chat-container");
    chatContainer.style.display = gameState.showChat ? "block" : "none";

    if (gameState.showChat) {
        document.getElementById("chat-input").focus();
    }
}

function closeChat() {
    gameState.showChat = false;
    document.getElementById("chat-container").style.display = "none";
    document.getElementById("chat-input").value = "";
}

function sendChatMessage() {
    const message = document.getElementById("chat-input").value.trim();
    if (message && gameState.socket) {
        if (message.startsWith(".")) {
            // Обработка команд
            const cmd = message.split(" ")[0];
            if (cmd === ".clear" || cmd === ".cl") {
                gameState.chatMessages = [];
                updateChatDisplay();
            } else if (cmd === ".q" || cmd === ".quit") {
                disconnectFromServer();
                returnToMenu();
            } else if (cmd === "/kill") {
                gameState.socket.send(JSON.stringify({ type: "kill_me" }));
            }
        } else {
            // Обычное сообщение
            gameState.socket.send(JSON.stringify({
                type: "chat_message",
                data: message
            }));
        }

        document.getElementById("chat-input").value = "";
        closeChat();
    }
}

function addChatMessage(data) {
    let message = "";

    if (data.subtype === "death_message") {
        message = `<span style="color: #ff3232">[DEATH]</span> ${escapeHtml(data.data)}`;
    } else if (data.subtype === "join/left") {
        message = escapeHtml(data.data);
    } else if (data.from_user) {
        const color = getPlayerColor(data.from_user);
        message = `<span style="color: ${color}">${escapeHtml(data.from_user)}</span>: ${escapeHtml(data.data)}`;
    } else {
        message = escapeHtml(data.data);
    }

    gameState.chatMessages.push(message);
    if (gameState.chatMessages.length > 100) {
        gameState.chatMessages.shift();
    }

    updateChatDisplay();
}

function updateChatDisplay() {
    const chatMessagesDiv = document.getElementById("chat-messages");
    chatMessagesDiv.innerHTML = gameState.chatMessages.map(msg =>
        `<div class="chat-message">${msg}</div>`
    ).join("");
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}

function toggleTablist() {
    gameState.showTablist = !gameState.showTablist;
    document.getElementById("tablist").style.display = gameState.showTablist ? "block" : "none";

    if (gameState.showTablist && gameState.gameState) {
        updateTablist();
    }
}

function closeTablist() {
    gameState.showTablist = false;
    document.getElementById("tablist").style.display = "none";
}

function updateTablist() {
    if (!gameState.gameState) return;

    const players = gameState.gameState.players;
    const snakes = gameState.gameState.snakes;

    // Информация о сервере
    document.getElementById("server-info").innerHTML = `
        <div>Server: ${escapeHtml(gameState.serverAddress)}</div>
        <div>${escapeHtml(gameState.serverDescription)}</div>
    `;

    // Количество игроков
    const aliveCount = Object.values(players).filter(p => p.alive).length;
    const deadCount = Object.keys(players).length - aliveCount;
    document.getElementById("player-count").innerHTML = `
        Players (${Object.keys(players).length}): Alive: ${aliveCount} | Dead: ${deadCount}
    `;

    // Список игроков
    const playersList = document.getElementById("players-list");
    playersList.innerHTML = "";

    Object.entries(players).forEach(([id, player]) => {
        const snake = snakes[id] || {};
        const color = getPlayerColor(id);

        const playerEntry = document.createElement("div");
        playerEntry.className = "player-entry";
        if (id === gameState.playerId) {
            playerEntry.style.border = "2px solid #6464ff";
            playerEntry.style.padding = "3px";
        }

        playerEntry.innerHTML = `
            <div class="player-name" style="color: ${color}">
                ${escapeHtml(player.name)} (${player.alive ? "Alive" : "Dead"})
            </div>
            <div class="player-stats">
                Size: ${snake.size || 0} | Max: ${snake.max_size || 0} |
                Kills: ${player.kills || 0} | Deaths: ${player.deaths || 0}
            </div>
        `;

        playersList.appendChild(playerEntry);
    });
}

function toggleDebugInfo() {
    gameState.showDebug = !gameState.showDebug;
    document.getElementById("debug-info").style.display = gameState.showDebug ? "block" : "none";

    if (gameState.showDebug) {
        updateDebugInfo();
    }
}

function updateDebugInfo() {
    if (!gameState.gameState) return;

    let debugText = `Player ID: ${gameState.playerId || "unknown"}\n`;
    debugText += `Snakes: ${Object.keys(gameState.gameState.snakes || {}).length}\n`;
    debugText += `Players: ${Object.keys(gameState.gameState.players || {}).length}\n`;
    debugText += `Food: ${(gameState.gameState.food || []).length}`;

    document.getElementById("debug-info").textContent = debugText;
}

function showDeathScreen(data) {
    document.getElementById("death-screen").style.display = "flex";
    document.getElementById("death-message").textContent = gameState.deathMessage;

    // Статистика
    if (gameState.gameState && gameState.playerId) {
        const player = gameState.gameState.players[gameState.playerId] || {};
        const snake = gameState.gameState.snakes[gameState.playerId] || {};

        let statsText = `Size: ${snake.size || 0}\n`;
        statsText += `Max Size: ${snake.max_size || 0}\n`;
        statsText += `Kills: ${player.kills || 0}\n`;
        statsText += `Deaths: ${player.deaths || 1}`;

        document.getElementById("death-stats").textContent = statsText;
    }
}

function respawn() {
    if (gameState.socket) {
        gameState.socket.send(JSON.stringify({ type: "respawn" }));
        document.getElementById("death-screen").style.display = "none";
    }
}

function showAlert(title, message, instruction) {
    gameState.alertData = { title, message, instruction };
    document.getElementById("alert-title").textContent = title;
    document.getElementById("alert-message").textContent = message;
    document.getElementById("alert-instruction").textContent = instruction;
    document.getElementById("alert-screen").style.display = "flex";
}

function closeAlert() {
    document.getElementById("alert-screen").style.display = "none";
    if (gameState.alertData && gameState.alertData.title === "Connection Error") {
        returnToMenu();
    }
}

function disconnectFromServer() {
    if (gameState.socket) {
        gameState.socket.close();
        gameState.socket = null;
    }
    gameState.gameRunning = false;
}

function returnToMenu() {
    disconnectFromServer();
    document.getElementById("main-menu").style.display = "flex";
    document.getElementById("death-screen").style.display = "none";
    document.getElementById("alert-screen").style.display = "none";
    document.getElementById("tablist").style.display = "none";
    document.getElementById("chat-container").style.display = "none";
}

// Отрисовка игры
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

    // Отрисовка еды
    renderFood(center);

    // Отрисовка змеек (сначала других игроков, потом свою)
    renderOtherSnakes(center);
    renderMySnake(center);

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

    ctx.fillStyle = COLORS.food;

    gameState.gameState.food.forEach(food => {
        const screenX = width / 2 + (food.x - center.x) * cellSize;
        const screenY = height / 2 + (food.y - center.y) * cellSize;

        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {
            ctx.beginPath();
            ctx.arc(
                screenX + cellSize / 2,
                screenY + cellSize / 2,
                cellSize / 3,
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

function renderSnake(snake, center, isMe) {
    const ctx = gameState.ctx;
    const canvas = gameState.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const cellSize = CELL_SIZE;

    if (!snake.alive) {
        ctx.fillStyle = COLORS.dead;
    } else {
        // Получаем цвет змейки
        const color = getSnakeColor(snake);
        ctx.fillStyle = color;
    }

    // Отрисовка тела
    snake.body.forEach((segment, index) => {
        const screenX = width / 2 + (segment.x - center.x) * cellSize;
        const screenY = height / 2 + (segment.y - center.y) * cellSize;

        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {

            // Голова
            if (index === 0) {
                // Тело
                ctx.fillRect(screenX, screenY, cellSize, cellSize);

                // Глаза
                if (snake.alive) {
                    drawSnakeEyes(ctx, screenX, screenY, cellSize, snake.direction);
                }
            } else {
                // Тело
                ctx.fillRect(screenX, screenY, cellSize, cellSize);
            }
        }
    });
}

function drawSnakeEyes(ctx, x, y, size, direction) {
    const eyeSize = size / 8;
    const offset = size / 4;

    ctx.fillStyle = "#000000";

    switch (direction) {
        case "up":
            // Левый глаз
            ctx.beginPath();
            ctx.arc(x + size / 3, y + offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            // Правый глаз
            ctx.beginPath();
            ctx.arc(x + 2 * size / 3, y + offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "down":
            // Левый глаз
            ctx.beginPath();
            ctx.arc(x + size / 3, y + size - offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            // Правый глаз
            ctx.beginPath();
            ctx.arc(x + 2 * size / 3, y + size - offset, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "left":
            // Верхний глаз
            ctx.beginPath();
            ctx.arc(x + offset, y + size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            // Нижний глаз
            ctx.beginPath();
            ctx.arc(x + offset, y + 2 * size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();
            break;

        case "right":
            // Верхний глаз
            ctx.beginPath();
            ctx.arc(x + size - offset, y + size / 3, eyeSize, 0, Math.PI * 2);
            ctx.fill();

            // Нижний глаз
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

    // Размер змейки
    if (gameState.playerId && gameState.gameState.snakes[gameState.playerId]) {
        const size = gameState.gameState.snakes[gameState.playerId].size || 0;
        ctx.fillStyle = COLORS.text;
        ctx.font = "20px Arial";
        ctx.fillText(`Size: ${size}`, 10, 30);
    }

    // Обновляем отладочную информацию, если она видима
    if (gameState.showDebug) {
        updateDebugInfo();
    }
}

function getSnakeColor(snake) {
    if (!snake.color) return COLORS.white;

    // Если цвет задан как объект с head/body
    if (snake.color.head) {
        return COLORS[snake.color.head] || COLORS.white;
    }

    // Если цвет задан как строка
    return COLORS[snake.color] || COLORS.white;
}

function getPlayerColor(playerId) {
    if (!gameState.gameState || !gameState.gameState.snakes[playerId]) return COLORS.white;

    const snake = gameState.gameState.snakes[playerId];
    return getSnakeColor(snake);
}

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Запуск игры при загрузке страницы
window.onload = initGame;