# Slyth - Snake game
```commandline
 ____  _       _   _     
/ ___|| |_   _| |_| |__  
\___ \| | | | | __| '_ \ 
 ___) | | |_| | |_| | | |
|____/|_|\__, |\__|_| |_|
         |___/ Slyth
```
Multiplayer snake game writen on Python

TO-DO:
- [x] Server
- [x] Web client (writen on JS)
- [x] Text chat
- [x] Mobile web client (optimize for mobile devices)
- [x] Leaderboard
- [ ] Reactions (like emoji, when you press num keyboard shows emoji above your snake head)


See [screenshots](#Screenshots)

#### Web client:
<img width="400" alt="image" src="https://github.com/user-attachments/assets/81801295-ee96-4db3-b9d6-70d0ce11ce7d" />

# Server
Tested on python 3.11
### Clone repository & create virtual envelopment
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
python3 -m venv \.venv
source server/.venv/bin/activate # on Windows: .\.venv\Scripts\activate
pip install -r server/requirements.txt
```
### Run server
You can edit `config.yaml` to setup server
```
python3 main.py
```

# Client
### Web client:
1. Open `web/game.html` in browser
2. Enter player name, color and server address
3. Click "Play"

### How to play
Controls:
* WASD - move snake
* space - move faster
* T - open chat 
* ESC - close chat
* TAB - open players list

Chat commands:
* `.q` - disconnect from server
* `/killme` - kill self
* `/kickme` - kick self

# Screenshots
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/194b622d-94a1-45e5-8cfd-6bbfe53a6858" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/890f35cc-95be-4ade-9bdf-bcfe7379bd0f" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/88f98420-d536-447a-afc7-12a9d4e46c02" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/4db69f3d-ed6b-4dab-9ce2-f843b1358994" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/e787097d-a2e9-402e-a385-9c981dd5cc78" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/6e6bcebb-bb97-4e3d-b126-5bd279e2ea33" />
<img width="1920" alt="image" src="https://github.com/user-attachments/assets/99d3304b-d8d7-4a70-b36f-77417a08c186" />



