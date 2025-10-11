function initGame() {
    gameState.canvas = document.getElementById("game-canvas");
    gameState.ctx = gameState.canvas.getContext("2d");

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    document.addEventListener('fullscreenchange', resizeCanvas);

    document.getElementById("play-button").addEventListener("click", startGame);

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