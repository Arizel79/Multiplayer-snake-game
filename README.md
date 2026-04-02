# Slyth - Snake game
```commandline
 ____  _       _   _     
/ ___|| |_   _| |_| |__  
\___ \| | | | | __| '_ \ 
 ___) | | |_| | |_| | | |
|____/|_|\__, |\__|_| |_|
         |___/ Slyth
```
Multiplayer snake game written on Python

TO-DO:
- [x] Server
- [x] Web client (written on JS)
- [x] Text chat
- [x] Mobile web client (optimize for mobile devices)
- [x] Leaderboard
- [ ] Reactions (like emoji, when you press num keyboard shows emoji above your snake head)

# Running server
Tested on python 3.11
### Clone repository
```
git clone https://github.com/Arizel79/Multiplayer-snake-game.git
cd Multiplayer-snake-game
```

### Install requirement 
This project uses [UV](https://docs.astral.sh/uv/) for Python package management, but you can also use plain pip.
#### Using UV
```
uv sync
```
#### Using pip
```
python -m venv .venv
source .venv/bin/activate # Windows: .\.venv\Scripts\activate
pip install -e .
```

### Start server
You can edit `config.yaml` to setup server

#### Using UV
```
uv run main.py
```

#### Using pip
```
python main.py
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
