// CLient config
const CELL_SIZE = 20;

const default_player_name = "";
const default_server = "localhost:8090";
const show_menu_server_address_input = true;
const can_user_change_server = true;


const SKINS = [
        "yellow,lime,green,turquoise,green,lime",
        "red,orange,yellow,orange",
        "red", "green", "lime", "blue", "yellow", "magenta", "cyan", "white", "orange",
                             "violet", "turquoise", "light_blue",
        "violet", "magenta",
        "light_blue,turquoise",

        ];

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

// For rendering on canvas
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
