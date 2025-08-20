# Multiplayer snake game
Multiplayer snake game writen on python with support for 3 clients: web, console (cli) and pygame (gui)

[X] Console client (ascii graphics)
[X] GUI client (pygame library)
[X] Web client (writen on JS)

See [screenshots](#Screenshots)

#### Web client:
<img width="400" alt="image" src="https://github.com/user-attachments/assets/81801295-ee96-4db3-b9d6-70d0ce11ce7d" />

#### Pygame (GUI) client:
<img width="400" alt="image" src="https://github.com/user-attachments/assets/d2c518b2-3367-42f4-b9f5-d4a54ed92396" />

#### Console (CLI) client:


# How to
### Clone repository & create virtual envelopment
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
python -m venv .venv
source .venv/bin/activate # on Windows: .\.venv\Scripts\activate
```
### Install dependencies
Tested on python 3.11
```
python pip install -r requirements.txt
```
### Run server
```
python server --address 0.0.0.0 --port 8090 --server_name "My test server" 
```
Running server options:
```
usage: server [-h] [--address ADDRESS] [--port PORT] [--server_name SERVER_NAME] [--server_desc SERVER_DESC] [--max_players MAX_PLAYERS] [--map_width MAP_WIDTH]
              [--map_height MAP_HEIGHT] [--food_perc FOOD_PERC] [--default_move_timeout DEFAULT_MOVE_TIMEOUT] [--logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```
### Run client
#### Web client:
open `web/game.html` in browser

#### GUI client:
```
python client --name TestPlayer --color white;red,green,blue --mode gui
```
#### Console client:
```
python client --name TestPlayer --color white;red,green,blue --mode cli
```
Running console & gui clients options:
```
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
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/194b622d-94a1-45e5-8cfd-6bbfe53a6858" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/890f35cc-95be-4ade-9bdf-bcfe7379bd0f" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/88f98420-d536-447a-afc7-12a9d4e46c02" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/4db69f3d-ed6b-4dab-9ce2-f843b1358994" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/e787097d-a2e9-402e-a385-9c981dd5cc78" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/6e6bcebb-bb97-4e3d-b126-5bd279e2ea33" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/2784f3b1-907b-42aa-aec4-5d9d0ff763ae" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/c9f3a3a9-7aea-4202-99ba-1f0a6120c6bc" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/99d3304b-d8d7-4a70-b36f-77417a08c186" />
<img width="1919" alt="image" src="https://github.com/user-attachments/assets/24fd2cb1-ed20-4d75-9430-83a372685dca" />





