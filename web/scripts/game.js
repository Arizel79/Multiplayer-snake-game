

function toggleSpeed(isFast){
    if (gameState.isFast == isFast) {return}
    gameState.isFast = isFast
    if (gameState.socket) {
        gameState.socket.send(JSON.stringify({ type: "is_fast", data: gameState.isFast}));
    }
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

function handleChatInput(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    } else if (event.key === "Escape") {
        toggleChat();
    }
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

function updateChatDisplay() {
    const chatMessagesDiv = document.getElementById("chat-messages");
    chatMessagesDiv.innerHTML = gameState.chatMessages.map(msg =>
        `<div class="chat-message">${msg}</div>`
    ).join("");
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;

    updateLastMessages();
}


function closeChat() {
    gameState.showChat = false;
    document.getElementById("chat-container").style.display = "none";
    document.getElementById("chat-input").value = "";
    showLastMessages();

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

function _addChatMessage(htmlText) {
    gameState.chatMessages.push(htmlText);
    if (gameState.chatMessages.length > 255) {
        gameState.chatMessages.shift();
    }

    updateChatDisplay();
    updateLastMessages();
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


    _addChatMessage(message)
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

function respawn() {
    if (gameState.socket) {
        console.log("Respawning")
        gameState.socket.send(JSON.stringify({ type: "respawn" }));
        closeAll();
        gameState.state = "game";
        gameLoop();
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