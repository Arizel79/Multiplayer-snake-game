

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