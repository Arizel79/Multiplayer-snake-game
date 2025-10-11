function connectToServer() {
    try {
        gameState.state = "connecting";
        showAlert("Connecting", "Server: " + gameState.serverAddress, "Wait...");
        gameState.socket = new WebSocket("ws://" + gameState.serverAddress);
        gameState.state = "game"

        gameState.socket.onopen = () => {
            closeAll();
            console.log("Connected to server");
            _addChatMessage(convertCustomTagsToHtml("connected to " + gameState.serverAddress))
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

        gameState.socket.onclose = (event) => {
            console.log("Closing socket. State: " + gameState.state);

            // Определяем причину отключения
            let reason = "Connection closed";
            if (event.code === 1000) {
                reason = "Normal closure";
            } else if (event.code === 1001) {
                reason = "Server going away";
            } else if (event.code === 1006) {
                reason = "Connection lost";
            }

            if (gameState.state != "connection_error" && gameState.state != "main_menu") {
                onDisconnect(reason);
                showError("Disconnected", "Server closed the connection", "Press SPACE to return to menu");
                gameState.state = "disconnected";
            } else {
                onDisconnect(reason);
            }
        };

        gameState.socket.onerror = (error) => {
            gameState.state = "connection_error";
            console.error("WebSocket error:", error);
            onDisconnect("WebSocket error");
            showError("Connection Error", `Failed to connect to ${gameState.serverAddress}`, "<button>Close</button>");
        };

    } catch (error) {
        console.error("Unknown connection error:", error);
        onDisconnect("Connection failed");
        showError("Unknown connection Error", `Invalid server address: ${gameState.serverAddress}`, "Press SPACE to return to menu");
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