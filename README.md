# Multiplayer snake game
Multiplayer snake game on btblioeki websockets with support for two client modes: console (cli) and pygame (gui)

# How to
### Clone repository & create virtual envelopment
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
python -m venv .venv
source .venv/bin/activate # on Windows: .\.venv\Scripts\activate
```
### Install dependencies
All:
```
python pip install -r requirements.txt
```
Only server dependencies:
```
python pip install -r server/requirements.txt
```
Only client dependencies:
```
python pip install -r client/requirements.txt
```
### Run server
```
python server --address 0.0.0.0 --port 8090 --server_name "My test server" 
```
Running server options:
```commandline
usage: server [-h] [--address ADDRESS] [--port PORT] [--server_name SERVER_NAME] [--server_desc SERVER_DESC] [--max_players MAX_PLAYERS] [--map_width MAP_WIDTH]
              [--map_height MAP_HEIGHT] [--food_perc FOOD_PERC] [--default_move_timeout DEFAULT_MOVE_TIMEOUT] [--logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```
### Run client
```
python client --name TestPlayer --color green --server
```
Running client options:
```commandline

```


