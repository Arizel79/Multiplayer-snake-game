# Multiplayer snake game
Multiplayer snake game on websockets with support for two client modes: console (cli) and pygame (gui)
<img width="960" height="1030" alt="image" src="https://github.com/user-attachments/assets/d2c518b2-3367-42f4-b9f5-d4a54ed92396" />

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
GUI mode:
```
python client --name TestPlayer --color white;red,green,blue --mode gui
```
Console mode:
```
python client --name TestPlayer --color white;red,green,blue --server --mode cli
```
Running client options:
```commandline
  --mode {cli,gui}, -m {cli,gui}
                        Game mode 
  --name NAME, --n NAME
                        Snake name
  --color COLOR, --c COLOR
                        Snake color
  --server SERVER, --s SERVER
                        Server address
  --log_lvl {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Level of logging
  --interactive, --i    Enable interactive prompting (default: False)
```
Colors (--color argument):
```
red,orange,yellow,lime,green,turquoise,cyan,light_blue,blue,violet,magenta
```
# Screenshots
<img width="943" height="1014" alt="image" src="https://github.com/user-attachments/assets/4db69f3d-ed6b-4dab-9ce2-f843b1358994" />
<img width="1001" height="790" alt="image" src="https://github.com/user-attachments/assets/e787097d-a2e9-402e-a385-9c981dd5cc78" />
<img width="1920" height="1028" alt="image" src="https://github.com/user-attachments/assets/6e6bcebb-bb97-4e3d-b126-5bd279e2ea33" />
<img width="1001" height="790" alt="image" src="https://github.com/user-attachments/assets/2784f3b1-907b-42aa-aec4-5d9d0ff763ae" />
<img width="959" height="1030" alt="image" src="https://github.com/user-attachments/assets/c9f3a3a9-7aea-4202-99ba-1f0a6120c6bc" />


