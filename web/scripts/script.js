function onDisconnect() {
    console.log("onDisconnect")
    _addChatMessage(convertCustomTagsToHtml("disconnected from " + gameState.serverAddress))
}


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

    if (event.key === "Escape") {
        if (document.getElementById("help-screen").style.display === "flex") {
            closeHelp();
            event.preventDefault();
        }
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

function showLastMessages() {
    clearTimeout(gameState.lastMessages.timeout);
    const el = document.getElementById('mini-chat');
    el.style.opacity = '1';
    el.style.display = 'block';
    gameState.lastMessages.visible = true;

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


function disconnectFromServer() {
    if (gameState.socket) {
        gameState.socket.close();
        gameState.socket = null;
    }
    gameState.state = "disconnected";
}

window.onload = initGame;