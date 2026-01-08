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

# Running server

Tested on python 3.11
### Clone repository & create virtual envelopment
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
python3 -m venv .venv
source .venv/bin/activate # on Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```
### Start server
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
