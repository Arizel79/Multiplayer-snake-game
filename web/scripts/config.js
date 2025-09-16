// Основные константы и переменные
const CELL_SIZE = 25;
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
    lastMessages: {
        visible: false,
        timeout: null,
        fadeDuration: 300
    },
    lastDirection: null,
    keysPressed: {},
    deathMessage: "",
    serverDescription: "Welcome to server!",
    alertData: null
};



const default_player_name = "";
const default_server = "192.168.1.25:8090";
const show_menu_server_address_input = true;
const can_user_change_server = true;
