


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
    lastMessages: {
        visible: false,
        timeout: null,
        fadeDuration: 300
    },
    lastDirection: null,
    keysPressed: {},
    deathMessage: "",
    serverDescription: "Welcome to server!",
    alertData: null,
    isFast: false
};

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

function getRandomSnakeColor() {
    return SKINS[Math.floor(Math.random() * SKINS.length)];
}

function convertCustomTagsToHtml(input) {
    const tagMap = {
        red: (content) => `<span style="color:red">${content}</span>`,
        green: (content) => `<span style="color:green">${content}</span>`,
        yellow: (content) => `<span style="color:yellow">${content}</span>`,
        white: (content) => `<span style="color:white">${content}</span>`,
        magenta: (content) => `<span style="color:magenta">${content}</span>`,
        blue: (content) => `<span style="color:blue">${content}</span>`,
        cyan: (content) => `<span style="color:cyan">${content}</span>`,
        b: (content) => `<b>${content}</b>`,
        d: (content) => `<span style="opacity:0.6">${content}</span>`,
        u: (content) => `<u>${content}</u>`,
    };

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function parseToTree(text) {
        const root = { type: 'root', children: [] };
        const stack = [root];
        let currentText = '';
        let i = 0;

        while (i < text.length) {
            if (text[i] === '<') {
                if (text[i + 1] === '/') {
                    const tagEnd = text.indexOf('>', i + 2);
                    if (tagEnd === -1) {
                        currentText += text[i];
                        i++;
                        continue;
                    }

                    const tagName = text.substring(i + 2, tagEnd);
                    if (stack.length > 1 && stack[stack.length - 1].tag === tagName) {
                        if (currentText) {
                            stack[stack.length - 1].children.push({
                                type: 'text',
                                content: currentText
                            });
                            currentText = '';
                        }
                        stack.pop();
                        i = tagEnd + 1;
                    } else {
                        currentText += text.substring(i, tagEnd + 1);
                        i = tagEnd + 1;
                    }
                }
                else {
                    const tagEnd = text.indexOf('>', i + 1);
                    if (tagEnd === -1) {
                        currentText += text[i];
                        i++;
                        continue;
                    }

                    const tagName = text.substring(i + 1, tagEnd);
                    if (tagMap[tagName]) {
                        if (currentText) {
                            stack[stack.length - 1].children.push({
                                type: 'text',
                                content: currentText
                            });
                            currentText = '';
                        }

                        const node = {
                            type: 'tag',
                            tag: tagName,
                            children: []
                        };
                        stack[stack.length - 1].children.push(node);
                        stack.push(node);
                        i = tagEnd + 1;
                    } else {
                        currentText += text.substring(i, tagEnd + 1);
                        i = tagEnd + 1;
                    }
                }
            } else {
                currentText += text[i];
                i++;
            }
        }

        if (currentText) {
            stack[stack.length - 1].children.push({
                type: 'text',
                content: currentText
            });
        }

        return root;
    }

    function generateHtml(node) {
        if (node.type === 'text') {
            return escapeHtml(node.content);
        }

        if (node.type === 'root') {
            return node.children.map(generateHtml).join('');
        }

        if (node.type === 'tag') {
            const innerHtml = node.children.map(generateHtml).join('');
            return tagMap[node.tag](innerHtml);
        }

        return '';
    }

    const rootNode = parseToTree(input);

    let out = generateHtml(rootNode);
    out = '<span class="custom-html">'+ out +'</span>'
    return out
}

function toggleFullscreen() {
    const elem = document.documentElement;

    if (!document.fullscreenElement) {
        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) { /* Safari */
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) { /* IE11 */
            elem.msRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) { /* Safari */
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { /* IE11 */
            document.msExitFullscreen();
        }
    }
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

// Modal windows

function showHelp() {
    document.getElementById('help-screen').style.display = 'flex';
}

function closeHelp() {
    document.getElementById('help-screen').style.display = 'none';
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


function showDeathScreen(data) {
    closeAll();
    document.querySelector('#death-screen').style.display = "flex";


    if (gameState.gameState && gameState.playerId) {
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

function closeAll() {
    closeAlert();
    closeError();
    closeDeath();
    closeTablist();
    closeChat();
}


function returnToMenu() {
    disconnectFromServer();
    gameState.state = "main_menu";
    document.getElementById("main-menu").style.display = "flex";


    closeAll();
}
