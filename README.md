# Multiplayer snake game
Multiplayer snake game writen on python with support for 3 clients: web, console and pygame (gui)

You can play [here](http://protein-gnu.gl.at.ply.gg:34472/game.html)

TO-DO:
- [x] Server
- [x] Console client (ascii graphics)
- [x] GUI client (pygame library)
- [x] Web client (writen on JS)
- [x] Mobile web client (optimize for mobile devices)

See [screenshots](#Screenshots)

#### Web client:
<img width="400" alt="image" src="https://github.com/user-attachments/assets/81801295-ee96-4db3-b9d6-70d0ce11ce7d" />

#### Pygame (GUI) client:
<img width="400" alt="image" src="https://github.com/user-attachments/assets/d2c518b2-3367-42f4-b9f5-d4a54ed92396" />

#### Console client:
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/4db69f3d-ed6b-4dab-9ce2-f843b1358994" />


# Server
Tested on python 3.11
### Clone repository & create virtual envelopment
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
python3 -m venv server/.venv
source server/.venv/bin/activate
pip install -r server/requirements.txt
```
### Run server
```
python3 server --port 8090 
```
`python3 server -h` for server running options

# Client
### Web client:
1. Open `web/game.html` in browser
2. Enter player name, color and server address
3. Click "Play"

### GUI client:
```
python3 client --name TestPlayer --color white;red,green,blue --mode gui
```
### Console client:
```
python3 client --name TestPlayer --color white;red,green,blue --mode cli
```
### How to play
Controls:
* WASD - move snake
* space - move faster
* T - open chat 
* ESC - close chat

Chat commands:
* `.q` - disconnect from server
* `/kill` - kill self

# Screenshots
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/194b622d-94a1-45e5-8cfd-6bbfe53a6858" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/890f35cc-95be-4ade-9bdf-bcfe7379bd0f" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/88f98420-d536-447a-afc7-12a9d4e46c02" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/4db69f3d-ed6b-4dab-9ce2-f843b1358994" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/e787097d-a2e9-402e-a385-9c981dd5cc78" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/6e6bcebb-bb97-4e3d-b126-5bd279e2ea33" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/99d3304b-d8d7-4a70-b36f-77417a08c186" />



