function connectToServer() {
    try {
        console.log("Connecting to server " + gameState.serverAddress + "...");
        gameState.state = "connecting";
        showAlert("Connecting", "Server: " + gameState.serverAddress, "Wait...");
        gameState.socket = new WebSocket("ws://" + gameState.serverAddress);


        gameState.socket.onopen = () => {
            closeAll();
            console.log("Connected to server: " + gameState.serverAddress);
            _addChatMessage(convertCustomTagsToHtml("Connected to " + gameState.serverAddress))
            gameState.state = "game";

            gameState.socket.send(JSON.stringify({
                name: gameState.playerName,
                color: gameState.playerColor,
                slyth_game: true
            }));

            gameLoop();

        };

        gameState.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        gameState.socket.onclose = (event) => {
            _addChatMessage("Disconnected from " + gameState.serverAddress);
            console.log("Socket closed. Code:", event.code, "Reason:", event.reason, "Was clean:", event.wasClean);

            let reason = "Connection closed";
            let errorCode = event.code;

            if (event.code === 1000) {
                reason = "Normal closure";
            } else if (event.code === 1001) {
                reason = "Server going away";
            } else if (event.code === 1006) {
                reason = "Connection lost";
            } else if (event.code === 1002) {
                reason = "Protocol error";
            } else if (event.code === 1003) {
                reason = "Unsupported data";
            } else if (event.code === 1005) {
                reason = "No status received";
            } else if (event.code === 1007) {
                reason = "Invalid frame payload data";
            } else if (event.code === 1008) {
                reason = "Policy violation";
            } else if (event.code === 1009) {
                reason = "Message too big";
            } else if (event.code === 1010) {
                reason = "Missing extension";
            } else if (event.code === 1011) {
                reason = "Internal server error";
            } else if (event.code === 1012) {
                reason = "Service restart";
            } else if (event.code === 1013) {
                reason = "Try again later";
            } else if (event.code === 1015) {
                reason = "TLS handshake failed";
            }

            if (!event.wasClean) {
                reason += " (unclean disconnect)";
            }

            if (event.reason) {
                reason += `  ${event.reason}`;
            }

             if (gameState.state != "connection_error") {
                onDisconnect(reason);
                showDisconnectWindow("Disconnected", reason, errorCode);

                gameState.state = "disconnected";
                }
        };

        gameState.socket.onerror = (error) => {
            console.error("WebSocket error:", error);

            let reason = "WebSocket error";
            let errorCode = "UNKNOWN_ERROR";

            if (error instanceof error) {
                reason = error.message;
                errorCode = error.code;
            } else if (error.type) {
                reason = `Error type: ${error.type}`;
            }

            if (gameState.state != "connection_error") {
                showDisconnectWindow("Connection Error", reason, errorCode);
                onDisconnect(reason);
                gameState.state = "connection_error";
            }
        };

    } catch (error) {
        console.error("Unknown connection error:", error);

        let reason = "Connection failed";
        let errorCode = "INITIALIZATION_ERROR";

        if (error instanceof Error) {
            reason = error.message;
        }

        if (gameState.state != "connection_error") {
                    showDisconnectWindow("Connection Error", reason, errorCode);
                    onDisconnect(reason);
                    gameState.state = "connection_error";
        }

    }

}

function showDisconnectWindow(title, message, errorCode = null) {
    let details = message;

    if (errorCode) {
        details += `. Error code: ${errorCode}`;
    }

    showError(title, details, false);
}

function handleServerMessage(data) {
console.log(data)
    switch (data.type) {

        case "player_id":
            gameState.playerId = data.player_id;
            break;

        case "game_state":
            gameState.gameState = data;
            updateTablist();

            updateLeaderboard();
            break;

        case "chat_message":
            addChatMessage(data);
            break;

        case "set_server_desc":
            gameState.serverDescription = data.data;
            break;

        case "set_map_borders":
            gameState.map_borders = data.data;
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
            console.log("server send connection_error: " + data.data)
            showDisconnectWindow("Connection Error", data.data, "SERVER_SEND_ERROR");
            gameState.state = "connection_error"
            break;

        default:
            console.log("Unknown message type:", data.type);
    }
}

function onDisconnect(reason) {
    console.log("Disconnected. Reason:", reason);

    if (gameState.socket) {
        gameState.socket.onopen = null;
        gameState.socket.onmessage = null;
        gameState.socket.onclose = null;
        gameState.socket.onerror = null;

        if (gameState.socket.readyState === WebSocket.OPEN ||
            gameState.socket.readyState === WebSocket.CONNECTING) {
            try {
                gameState.socket.close(1000, "Client disconnected");
            } catch (e) {
                console.error("Error closing socket:", e);
            }
        }

        gameState.socket = null;
    }

    if (gameState.gameLoopId) {
        cancelAnimationFrame(gameState.gameLoopId);
        gameState.gameLoopId = null;
    }
}