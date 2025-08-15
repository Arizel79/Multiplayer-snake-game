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
    grid: "#FF82828",
    background: "#141414",
    text: "#ffffff"
};

// Состояние игры
const gameState = {
    state: "main_menu",
    canvas: null,
    ctx: null,
    socket: null,
    playerId: null,
    playerName: "",
    serverAddress: "",
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
    if (gameState.state == "game") {
        renderGame();
    }
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem("snakeGameSettings")) || {};
    document.getElementById("name-input").value = settings.playerName || "player_web";
    document.getElementById("color-input").value = settings.playerColor || "red,orange,yellow,lime,green,turquoise,cyan,light_blue,blue,violet,magenta";
    document.getElementById("server-input").value = settings.serverAddress || "localhost:8090";
}

function saveSettings() {
    const settings = {
        playerName: gameState.playerName,
        serverColor: gameState.playerColor,
        serverAddress: gameState.serverAddress
    };
    localStorage.setItem("snakeGameSettings", JSON.stringify(settings));
}

// Запуск игры
function startGame() {
    gameState.playerName = document.getElementById("name-input").value.trim();
    gameState.playerColor = document.getElementById("color-input").value.trim();
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

function closeAll() {
    closeAlert();
    closeError();
    closeDeath();
}

function connectToServer() {
    try {
        gameState.state = "connecting";
        showAlert("Connecting", "Server: " + gameState.serverAddress, "Wait...");
        gameState.socket = new WebSocket("ws://" + gameState.serverAddress);
        gameState.state = "game"

        gameState.socket.onopen = () => {
            closeAll();
            console.log("Connected to server");
            gameState.state = "game";

            // Отправляем данные игрока
            gameState.socket.send(JSON.stringify({
                name: gameState.playerName,
                color: gameState.playerColor // Можно добавить выбор цвета
            }));

            // Начинаем игровой цикл
            gameLoop();
        };

        gameState.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        gameState.socket.onclose = () => {
            console.log("Closing socket. State: " + gameState.state);
            if (gameState.state != "connection_error" && gameState.state != "main_menu") {
                closeAll();
                showError("Disconnected", "Server closed the connection", "Press SPACE to return to menu");
                gameState.state = "disconnected";
            }

        };

        gameState.socket.onerror = (error) => {
            gameState.state = "connection_error";
            console.error("WebSocket error:", error);
            showError("Connection Error", `Failed to connect to ${gameState.serverAddress}`, "<button>Close</button>");
        };

    } catch (error) {
        console.error("Unknown connection error:", error);
        showError("Unknown Connection Error", `Invalid server address: ${gameState.serverAddress}`, "Press SPACE to return to menu");
        gameState.state = "connection_error";
    }
}

function handleServerMessage(data) {
    //console.log("New packet:", data);
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
            gameState.state = "death"
            gameState.deathMessage = data.data || "You died";
            showDeathScreen(data);
            break;

        case "connection_error":
            gameState.state = "connection_error"
            showAlert("Connection Error", data.data, "Press SPACE to return to menu");
            break;

        default:
            console.log("Unknown message type:", data.type);
    }
}

// Игровой цикл
function gameLoop() {
    console.log("gameLoop");
    if (gameState.state != "game") {
        console.log("Mainloop closed");
        return
    }

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

    if (gameState.keysPressed["w"] ||  gameState.keysPressed["ц"] || gameState.keysPressed["ArrowUp"]) {
        direction = "up";
    } else if (gameState.keysPressed["s"] || gameState.keysPressed["ы"] ||  gameState.keysPressed["ArrowDown"]) {
        direction = "down";
    } else if (gameState.keysPressed["a"] || gameState.keysPressed["ф"] || gameState.keysPressed["ArrowLeft"]) {
        direction = "left";
    } else if (gameState.keysPressed["d"] ||  gameState.keysPressed["в"] || gameState.keysPressed["ArrowRight"]) {
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
    if (gameState.showChat && event.key !== "Enter" && event.key !== "Escape") {
        return;
    }

    gameState.keysPressed[event.key] = true;
switch (gameState.state) {
    case "game":
        if (event.key == "t") {
            event.preventDefault();
            toggleChat();
        } else if (event.key == "Tab") {
            event.preventDefault();
            toggleTablist();
        } else if (event.key == "Escape") {
            if (gameState.showChat) {
                closeChat();
            } else if (gameState.showTablist) {
                closeTablist();
            }
        }
        break;

    case "main_menu":
        if (event.key == "Enter") {
            startGame();
        }
        break;

    case "death":
        if (event.key == "Enter" || event.key == " ") {
            respawn();
        }
        break;

    case "disconnected":
    case "connection_error":
        if (event.key == "Enter" || event.key == " ") {
            returnToMenu();
        }
        break;
}

// Глобальные горячие клавиши (работают во всех состояниях)
if (event.key == "i") {
    toggleDebugInfo();
}

if (event.key == " ") {
    if (document.getElementById("alert-screen").style.display === "flex") {
        closeAlert();
    }
}
//    switch (event.key) {
//        case "t":
//            if (gameState.state == "game") {
//                event.preventDefault();
//                toggleChat();
//            }
//            break;
//
//        case "Tab":
//            if (gameState.state == "game") {
//                event.preventDefault();
//                toggleTablist();
//            }
//            break;
//
//        case "i":
//            toggleDebugInfo();
//            break;
//
//        case " ":
//            if (document.getElementById("death-screen").style.display === "flex") {
//                respawn();
//            } else if (document.getElementById("alert-screen").style.display === "flex") {
//                closeAlert();
//            }
//            break;
//
//        case "Escape":
//            if (gameState.showChat) {
//                closeChat();
//            } else if (gameState.showTablist) {
//                closeTablist();
//            }
//            break;
//
//        case "Enter":
//            if (gameState.state == "main_menu") {
//                startGame();
//            } else if (gameState.state == "death") {
//                respawn();
//            } else if (gameState.state == "disconnected" || gameState.state == "connection_error") {
//                returnToMenu();
//            }
//
//
//    }
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
    document.getElementById("chat-input").value = "";
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
        message = convertCustomTagsToHtml("<red>[DEATH]</red> " + data.data);
    } else if (data.subtype === "join/left") {
        message = convertCustomTagsToHtml(data.data);
    } else if (data.from_user) {
        const color = getPlayerColor(data.from_user);
        message = convertCustomTagsToHtml(`Player ${data.from_user} : ${data.data}`);
    } else {
        message = convertCustomTagsToHtml(data.data);
    }


    gameState.chatMessages.push(message);
    if (gameState.chatMessages.length > 255) {
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
            <div class="tablist-player-stats">
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
    document.querySelector('#death-screen').style.display = "flex";

    closeChat()

    // Статистика
    if (gameState.gameState && gameState.playerId) {
        const player = gameState.gameState.players[gameState.playerId] || {};
        const snake = gameState.gameState.snakes[gameState.playerId] || {};

//        let statsText = `<div id='player-stats'>Size: ${snake.size || 0}`;
//        statsText += `: ${snake.max_size || 0}\n`;
//        statsText += `Kills: ${player.kills || 0}\n`;
//        statsText += `Deaths: ${player.deaths || 1}</div>`;
        let statsText = `
<div class="player-stats">
    <table class="table-player-stats">
        <thead>
            <tr>
                <th colspan="2">Player stats</th>
            </tr>
        </thead>
        <tbody>
           <tr>
              <td>Size</td>
              <td>${snake.size || 0}</td>
           </tr>
           <tr>
              <td>Max size</td>
              <td>${snake.max_size || 0}</td>
           </tr>
           <tr>
              <td>Kills</td>
              <td>${player.kills || 0}</td>
           </tr>
           <tr>
              <td>Deaths</td>
              <td>${player.deaths || 1}</td>
           </tr>
       </tbody>
      </table>
</div>`;

        document.querySelector("#death-screen .message").innerHTML = convertCustomTagsToHtml(gameState.deathMessage) + statsText;


    }
}

function respawn() {
    if (gameState.socket) {
        console.log("Respawning")
        gameState.socket.send(JSON.stringify({ type: "respawn" }));
        closeAll();
        gameState.state = "game";
        gameLoop();
    }
}

function showAlert(title, message, instruction) {
    closeAll();
    gameState.alertData = { title, message, instruction };
    document.querySelector('#alert-screen .title').textContent = title;
    document.querySelector('#alert-screen .message').textContent = message;
    // document.querySelector('#alert-screen .instruction').textContent = instruction;
    document.querySelector('#alert-screen').style.display = "flex";
}

function showError(title, message) { // Can be XSS injection!!!
    closeAlert();
    gameState.errorData = { title, message};
    document.querySelector('#error-screen .title').textContent = title;
    document.querySelector('#error-screen .message').textContent = message;
    // document.querySelector('#error-screen .button').textContent = ;
    document.querySelector('#error-screen').style.display = "flex";
}

function closeAlert() {
    document.querySelector('#alert-screen').style.display = "none";
}

function closeDeath() {
    document.querySelector('#death-screen').style.display = "none";
}

function closeError() {
    document.querySelector('#error-screen').style.display = "none";
    }


function disconnectFromServer() {
    if (gameState.socket) {
        gameState.socket.close();
        gameState.socket = null;
    }
    gameState.state = "disconnected";
}

function returnToMenu() {

    disconnectFromServer();
    closeAll();
    document.getElementById("main-menu").style.display = "flex";
    document.getElementById("death-screen").style.display = "none";
    document.getElementById("alert-screen").style.display = "none";
    document.getElementById("tablist").style.display = "none";
    document.getElementById("chat-container").style.display = "none";
    gameState.state = "main_menu";
    console.log("Back to main menu")
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

    // Получаем цвета из конфигурации змеи
    const headColor = snake.color?.head;
    const bodyColors = snake.color?.body || [];
    const hasCustomColors = bodyColors.length > 0 || headColor;
    const defaultColor = getSnakeColor(snake);

    snake.body.forEach((segment, index) => {
        const screenX = width / 2 + (segment.x - center.x) * cellSize;
        const screenY = height / 2 + (segment.y - center.y) * cellSize;

        if (screenX >= -cellSize && screenX <= width + cellSize &&
            screenY >= -cellSize && screenY <= height + cellSize) {

            // Устанавливаем цвет сегмента
            if (!snake.alive) {
                ctx.fillStyle = COLORS.dead;
            } else if (hasCustomColors) {
                if (index === 0) {
                    // Цвет головы (если задан, иначе первый цвет из body)
                    const colorName = headColor || bodyColors[0] || defaultColor;
                    ctx.fillStyle = getColorValue(colorName);
                } else {
                    // Циклический выбор цвета тела
                    const colorIndex = (index - (headColor ? 1 : 0)) % bodyColors.length;
                    const colorName = bodyColors[colorIndex] || defaultColor;
                    ctx.fillStyle = getColorValue(colorName);
                }
            } else {
                ctx.fillStyle = defaultColor;
            }

            // Рисуем сегмент
            ctx.fillRect(screenX, screenY, cellSize, cellSize);

            // Рисуем глаза на живой голове
            if (index === 0 && snake.alive) {
                drawSnakeEyes(ctx, screenX, screenY, cellSize, snake.direction);
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

//    // Размер змейки
//    if (gameState.playerId && gameState.gameState.snakes[gameState.playerId]) {
//        const size = gameState.gameState.snakes[gameState.playerId].size || 0;
//        ctx.fillStyle = COLORS.text;
//        ctx.font = "20px Arial";
//        ctx.fillText(`Size: ${size}`, 10, 30);
//    }

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