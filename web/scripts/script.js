
function initGame() {
    gameState.canvas = document.getElementById("game-canvas");
    gameState.ctx = gameState.canvas.getContext("2d");

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    document.addEventListener('fullscreenchange', resizeCanvas);

    document.getElementById("server-input").disabled = !can_user_change_server;
    if (!show_menu_server_address_input) {
        const serverInput = document.getElementById('server-input');
        if (serverInput) {
            serverInput.hidden = true
        }
    }

    document.getElementById("play-button").addEventListener("click", startGame);
    document.getElementById("chat-input").addEventListener("keydown", handleChatInput);

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);

    loadSettings();

}

//function resizeCanvas() {
//    gameState.canvas.width = window.innerWidth;
//    gameState.canvas.height = window.innerHeight;
//    if (gameState.state == "game") {
//        renderGame();
//    }
//}

function resizeCanvas() {
    const canvas = gameState.canvas;
    const container = canvas.parentElement;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    gameState.canvas.width = containerWidth;
    gameState.canvas.height = containerHeight;
    gameState.canvas.top = container.top;
    gameState.canvas.left = container.left;

    if (gameState.state == "game") {
        renderGame();
    }
}

function loadSettings() {
    let json_settings = localStorage.getItem("snakeGameSettings");
    const settings = JSON.parse(json_settings) || {};
    console.log("settings loaded: " + json_settings)
    document.getElementById("name-input").value = settings.playerName || default_player_name;
    document.getElementById("color-input").value = settings.playerColor || getRandomSnakeColor();
    document.getElementById("server-input").value = settings.serverAddress || default_server;
}

function saveSettings() {
    const settings = {
        playerName: gameState.playerName,
        playerColor: gameState.playerColor,
        serverAddress: gameState.serverAddress
    };
    localStorage.setItem("snakeGameSettings", JSON.stringify(settings));
    console.log("settings saved: " + JSON.stringify(settings))
}

function startGame() {
    gameState.playerName = document.getElementById("name-input").value.trim();
    gameState.playerColor = document.getElementById("color-input").value.trim();
    gameState.serverAddress = document.getElementById("server-input").value.trim();

    if (!gameState.playerName) {
        alert("Please enter player name");
        return;
    }

    if (!gameState.serverAddress) {
        alert("Please enter server address");
        return;
    }

    saveSettings();
    document.getElementById("main-menu").style.display = "none";

    connectToServer();
    showLastMessages();
}

function closeAll() {
    closeAlert();
    closeError();
    closeDeath();
    closeTablist();
    closeChat();
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

            gameState.socket.send(JSON.stringify({
                name: gameState.playerName,
                color: gameState.playerColor
            }));

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
function toggleSpeed(isFast){
    if (gameState.isFast == isFast) {return}
    gameState.isFast = isFast
    // console.log("toggleSpeed : set to :", isFast)
    if (gameState.socket) {
        gameState.socket.send(JSON.stringify({ type: "is_fast", data: gameState.isFast}));
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
            updateTablist();
            break;

        case "chat_message":
            addChatMessage(data);
            break;

        case "set_server_desc":
            gameState.serverDescription = data.data;
            break;

        case "you_died":
            console.log("You died: " + data.data)
            gameState.state = "death"
            gameState.direction = null;
            gameState.lastDirection = null
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


function gameLoop() {
    if (gameState.state != "game") {
        return;
    }

    handleMovementInput();

    renderGame();

    requestAnimationFrame(gameLoop);
}

function setDirection(direction) {
   if (direction && direction !== gameState.lastDirection) {

        gameState.socket.send(JSON.stringify({
            type: "direction",
            data: direction
        }));
        gameState.lastDirection = direction;
    }
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
    setDirection(direction);

}

function handleKeyDown(event) {
    if (gameState.showChat && event.key !== "Enter" && event.key !== "Escape") {
        return;
    }
    if ([" ", "z"].includes(event.key)) {
        toggleSpeed(true);
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
                toggleChat();
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

if (event.key == "i") {
    toggleDebugInfo();
}

if (event.key == " ") {
    if (document.getElementById("alert-screen").style.display === "flex") {
        closeAlert();
    }
}
}

function handleKeyUp(event) {
    gameState.keysPressed[event.key] = false;
    if (["w", "ArrowUp", "s", "ArrowDown", "a", "ArrowLeft", "d", "ArrowRight"].includes(event.key)) {
        gameState.lastDirection = null;
    }
    if ([" ", "z"].includes(event.key)) {
        toggleSpeed(false);
    }
}

function handleChatInput(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    } else if (event.key === "Escape") {
        toggleChat();
    }
}

function showLastMessages() {
    clearTimeout(gameState.lastMessages.timeout);
    const el = document.getElementById('mini-chat');
    el.style.opacity = '1';
    el.style.display = 'block';
    gameState.lastMessages.visible = true;

}

function hideLastMessages() {
    const el = document.getElementById('mini-chat');
    el.style.opacity = '0';
    gameState.lastMessages.visible = false;

    setTimeout(() => {
        if (!gameState.lastMessages.visible) {
            el.style.display = 'none';
        }
    }, gameState.lastMessages.fadeDuration);
}

function closeChat() {
    gameState.showChat = false;
    document.getElementById("chat-container").style.display = "none";
    document.getElementById("chat-input").value = "";
    showLastMessages();

}

function updateChatDisplay() {
    const chatMessagesDiv = document.getElementById("chat-messages");
    chatMessagesDiv.innerHTML = gameState.chatMessages.map(msg =>
        `<div class="chat-message">${msg}</div>`
    ).join("");
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;

    updateLastMessages();
}


function toggleChat() {
    gameState.showChat = !gameState.showChat;
    const chatContainer = document.getElementById('chat-container');
    const chatMessages = document.getElementById('chat-messages');

    if (gameState.showChat) {
        chatContainer.style.display = 'block';
        chatContainer.style.opacity = '0';
        chatContainer.style.transition = 'opacity 0.1s ease';

        setTimeout(() => {
            chatContainer.style.opacity = '1';
        }, 100);

        hideLastMessages();

        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            document.getElementById('chat-input').focus();
        }, 50);
    } else {
        chatContainer.style.opacity = '1';
        chatContainer.style.transition = 'opacity 0.1s ease';

        chatContainer.style.opacity = '0';

        setTimeout(() => {
            chatContainer.style.display = 'none';
            showLastMessages();
        }, 100);
    }
}

function sendChatMessage() {
    const message = document.getElementById("chat-input").value.trim();
    if (message && gameState.socket) {
        if (message.startsWith(".")) {
            const cmd = message.split(" ")[0];
            if (cmd === ".clear" || cmd === ".cl") {
                gameState.chatMessages = [];
                updateChatDisplay();
            } else if (cmd === ".q" || cmd === ".quit") {
                    setTimeout(() => {
                        returnToMenu();
                    }, 100);
                    return;
            } else if (cmd === "/kill") {
                gameState.socket.send(JSON.stringify({type: "kill_me"}));
            }
        } else {
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
        message = convertCustomTagsToHtml(`[${data.from_user}] ${data.data}`);
    } else {
        message = convertCustomTagsToHtml(data.data);
    }


    gameState.chatMessages.push(message);
    if (gameState.chatMessages.length > 255) {
        gameState.chatMessages.shift();
    }

    updateChatDisplay();
    updateLastMessages();
}

function updateChatDisplay() {
    const chatMessagesDiv = document.getElementById("chat-messages");
    chatMessagesDiv.innerHTML = gameState.chatMessages.map(msg =>
        `<div class="chat-message">${msg}</div>`
    ).join("");

}

function updateLastMessages() {
    if (!gameState.chatMessages.length) return;

    const container = document.getElementById('mini-chat-messages');
    const messagesToShow = gameState.chatMessages.slice(-5);

    container.innerHTML = messagesToShow.map(msg =>
        `<div class="chat-message">${msg}</div>`
    ).join('');

    // Показываем мини-чат, если чат закрыт
    if (!gameState.showChat) {
        showLastMessages();
    }

    container.scrollIntoView(false);
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
    document.getElementById("your-score-value").innerHTML = gameState.gameState.snakes[gameState.playerId].size || -1;

    const players = gameState.gameState.players;
    const snakes = gameState.gameState.snakes;



    document.getElementById("tablist-title").innerHTML = escapeHtml(gameState.serverAddress);
    document.getElementById("tablist-server-info").innerHTML = `
        <div id="tablist-server-desc">${escapeHtml(gameState.serverDescription)}</div>
    `;

    const aliveCount = Object.values(players).filter(p => p.alive).length;
    const deadCount = Object.keys(players).length - aliveCount;
    document.getElementById("tablist-players-count").innerHTML = `
        All: ${Object.keys(players).length};   Alive: ${aliveCount};   Dead: ${deadCount};
    `;

    const table = document.createElement("table");
    table.className = "tablist-players-table";
    table.innerHTML = `
        <thead>
            <tr>
                <th>Player</th>
                <th>Status</th>
                <th>Size</th>
                <th>Max Size</th>
                <th>Kills</th>
                <th>Deaths</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

    const tbody = table.querySelector("tbody");

    Object.entries(players).forEach(([id, player]) => {
        const snake = snakes[id] || {};
        const color = getPlayerColor(id);
        const isCurrentPlayer = id === gameState.playerId;

        const row = document.createElement("tr");
        if (isCurrentPlayer) {
            row.classList.add("current-player");
        }

        row.innerHTML = `
            <td style="color: ${color}; font-weight: ${isCurrentPlayer ? "bold" : "normal"}">
                ${escapeHtml(player.name)}
            </td>
            <td>
                <span class="status-badge ${player.alive ? "alive" : "dead"}">
                   ${player.alive ? "alive" : "dead"}
                </span>
            </td>
            <td>${snake.size || 0}</td>
            <td>${snake.max_size || 0}</td>
            <td>${player.kills || 0}</td>
            <td>${player.deaths || 0}</td>
        `;

        tbody.appendChild(row);
    });

    const container = document.getElementById("tablist-players-list");
    container.innerHTML = "";
    container.appendChild(table);
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

    closeAll();
    document.querySelector('#death-screen').style.display = "flex";


    if (gameState.gameState && gameState.playerId) {
        console.log(gameState.playerId);
        const player = gameState.gameState.players[gameState.playerId];
        const snake = gameState.gameState.snakes[gameState.playerId];
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
              <td>${data.stats.size}</td>
           </tr>
           <tr>
              <td>Max size</td>
              <td>${data.stats.max_size}</td>
           </tr>
           <tr>
              <td>Kills</td>
              <td>${data.stats.kills}</td>
           </tr>
           <tr>
              <td>Deaths</td>
              <td>${data.stats.deaths}</td>
           </tr>
       </tbody>
      </table>
</div>`;

        // document.querySelector("#death-screen .info-message").innerHTML = "convertCustomTagsToHtml(gameState.deathMessage) + statsText;
         document.querySelector("#death-screen .info-message #death-reason").innerHTML = convertCustomTagsToHtml(gameState.deathMessage);
         document.querySelector("#death-screen .info-message #death-player-stats-table-container").innerHTML = statsText;


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
    document.querySelector('#alert-screen .info-message').textContent = message;
    // document.querySelector('#alert-screen .instruction').textContent = instruction;
    document.querySelector('#alert-screen').style.display = "flex";
}

function showError(title, message) {
    closeAlert();
    gameState.errorData = { title, message};
    document.querySelector('#error-screen .title').textContent = title;
    document.querySelector('#error-screen .info-message').textContent = escapeHtml(message);
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
    console.log("Backing to main menu")
    disconnectFromServer();  // Перенеси этот вызов в самое начало
    gameState.state = "main_menu";  // Затем установи состояние
    document.getElementById("main-menu").style.display = "flex";


    closeAll();
}



window.onload = initGame;