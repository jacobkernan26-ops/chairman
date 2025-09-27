from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random, uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ------------------------
# Models
# ------------------------
class Player:
    def __init__(self,name,position,skill,value):
        self.name=name
        self.position=position
        self.skill=skill
        self.value=value
        self.morale=50
        self.injured=False

class Manager:
    def __init__(self,name,ability,salary):
        self.name=name
        self.ability=ability
        self.salary=salary

class Club:
    def __init__(self,name,budget):
        self.name=name
        self.budget=budget
        self.reputation=50
        self.stadium_capacity=20000
        self.manager=None
        self.players=[]
        self.sponsor_income=50000
        self.ticket_income=0

    def hire_manager(self,manager):
        if self.budget>=manager.salary:
            self.manager=manager
            self.budget-=manager.salary
            return f"Hired {manager.name}!"
        return "Not enough budget!"

    def fire_manager(self):
        if self.manager:
            name=self.manager.name
            self.manager=None
            return f"Fired {name}!"
        return "No manager to fire!"

    def sign_player(self,player):
        if self.budget>=player.value:
            self.players.append(player)
            self.budget-=player.value
            return f"Signed {player.name}!"
        return "Not enough budget!"

    def sell_player(self,player_name):
        for p in self.players:
            if p.name==player_name:
                self.players.remove(p)
                self.budget+=p.value
                return f"Sold {p.name}!"
        return "Player not found!"

    def upgrade_stadium(self,cost,extra_capacity):
        if self.budget>=cost:
            self.stadium_capacity+=extra_capacity
            self.budget-=cost
            return f"Stadium capacity increased to {self.stadium_capacity}"
        return "Not enough budget!"

    def calculate_weekly_income(self):
        self.ticket_income=self.stadium_capacity*random.randint(15,25)
        self.budget+=self.ticket_income+self.sponsor_income
        wages=sum([p.skill*100 for p in self.players])
        if self.manager:
            wages+=self.manager.salary
        self.budget-=wages
        return {"ticket_income":self.ticket_income,"sponsor_income":self.sponsor_income,"wages":wages,"budget":self.budget}

# ------------------------
# League & Matches
# ------------------------
class Match:
    def __init__(self,home,away):
        self.home=home
        self.away=away

    def simulate(self):
        # Injuries
        for p in self.home.players+self.away.players:
            if random.randint(1,50)==1: p.injured=True
        home_score=self.calculate_score(self.home,self.away)
        away_score=self.calculate_score(self.away,self.home)
        # Update morale
        for p in self.home.players+self.away.players:
            if p.injured: p.morale-=10
            else: p.morale=min(100,p.morale+1)
        return home_score,away_score

    def calculate_score(self,club,opponent):
        if len(club.players)==0: return 0
        skill=sum(p.skill for p in club.players if not p.injured)
        morale=sum(p.morale for p in club.players if not p.injured)/len(club.players)
        manager_bonus=club.manager.ability if club.manager else 0
        opponent_defense=sum(p.skill for p in opponent.players if not p.injured)/2
        rand=random.randint(-5,5)
        return max(0,int((skill+morale+manager_bonus)/50 - opponent_defense/100 + rand))

class League:
    def __init__(self,clubs):
        self.clubs=clubs
        self.table={c.name:{"points":0,"played":0,"wins":0,"draws":0,"losses":0} for c in clubs}

    def play_week(self):
        results=[]
        for i in range(len(self.clubs)):
            for j in range(i+1,len(self.clubs)):
                match=Match(self.clubs[i],self.clubs[j])
                h,a=match.simulate()
                results.append({"home":self.clubs[i].name,"away":self.clubs[j].name,"score":f"{h}-{a}"})
                self.update_table(self.clubs[i],self.clubs[j],h,a)
        return results

    def update_table(self,home,away,hscore,ascore):
        hd=self.table[home.name]
        ad=self.table[away.name]
        hd["played"]+=1
        ad["played"]+=1
        if hscore>ascore:
            hd["points"]+=3
            hd["wins"]+=1
            ad["losses"]+=1
        elif hscore<ascore:
            ad["points"]+=3
            ad["wins"]+=1
            hd["losses"]+=1
        else:
            hd["points"]+=1
            ad["points"]+=1
            hd["draws"]+=1
            ad["draws"]+=1

# ------------------------
# Initialize Game
# ------------------------
club_names=["My Club","Rival FC","Eagles","Tigers","Lions","Sharks","Dragons","Wolves","Phoenix","Falcons"]
clubs=[]
for name in club_names:
    c=Club(name,random.randint(500000,1500000))
    for i in range(5):
        c.players.append(Player(f"{name}_P{i+1}","Midfielder",random.randint(50,90),random.randint(40000,100000)))
    c.manager=Manager(f"{name}_M",random.randint(50,90),random.randint(40000,100000))
    clubs.append(c)
league=League(clubs)
my_club=clubs[0]

# Transfer Market Pool
transfer_market=[]

def generate_transfer_market():
    transfer_market.clear()
    for c in clubs[1:]:
        if random.randint(1,2)==1: # 50% chance a player is listed
            p=random.choice(c.players)
            transfer_market.append({"club":c.name,"player":p.name,"skill":p.skill,"value":p.value})

# Board/Fan Events
current_events=[]
pending_sponsor_offer = None
def generate_events():
    global pending_sponsor_offer
    current_events.clear()
    # Random sponsorship offer
    if random.randint(1,3)==1:
        offer=random.randint(50000,200000)
        current_events.append(f"Sponsor offers ${offer} for a one-week deal. Accept?")
        pending_sponsor_offer = offer
    else:
        pending_sponsor_offer = None
    # Fan unrest
    if random.randint(1,4)==1:
        current_events.append("Fans unhappy with team's performance. Morale drops by 5.")
        for p in my_club.players: p.morale=max(0,p.morale-5)

# ------------------------
# Web Frontend
# ------------------------
@app.get("/",response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html>
<head>
<title>FM24 Owner AI + Events</title>
</head>
<body onload=\"loadClub()\">
<h1>FM24 Owner AI + Events</h1>
<div>
    <h3>Club Status</h3>
    Budget: $<span id=\"budget\"></span><br>
    Stadium Capacity: <span id=\"stadium\"></span><br>
    Manager: <span id=\"manager\"></span><br>
    <h3>Players</h3>
    <ul id=\"players\"></ul>
</div>
<div>
    <h3>Transfer Market</h3>
    <div id=\"market\"></div>
</div>
<div>
    <button onclick=\"nextWeek()\">Next Week</button>
    <button onclick=\"signPlayer()\">Manual Transfer (Name, Value)</button>
</div>
<div>
    <h3>Events</h3>
    <div id=\"events\"></div>
</div>
<script>
async function loadClub(){
    let res = await fetch('/club-status');
    let data = await res.json();
    document.getElementById('budget').innerText = data.budget;
    document.getElementById('stadium').innerText = data.stadium_capacity;
    document.getElementById('manager').innerText = data.manager || 'None';
    let list = document.getElementById('players'); list.innerHTML = '';
    data.players.forEach(p => {
        let li = document.createElement('li');
        li.innerText = p.name + ' - Skill: ' + p.skill + (p.injured ? ' (injured)' : '');
        list.appendChild(li);
    });
    let ev = document.getElementById('events'); ev.innerHTML = '';
    data.events.forEach(e => {
        let div = document.createElement('div');
        div.innerText = e;
        if(e.startsWith("Sponsor offers")) {
            let btn = document.createElement('button');
            btn.innerText = "Accept Sponsor Offer";
            btn.onclick = acceptSponsor;
            div.appendChild(btn);
        }
        ev.appendChild(div);
    });
    let tm = document.getElementById('market'); tm.innerHTML = '';
    data.transfer_market.forEach(t => {
        let btn = document.createElement('button');
        btn.innerText = 'Buy ' + t.player + ' (' + t.club + ') $' + t.value;
        btn.onclick = () => buyPlayer(t.player, t.club, t.value);
        tm.appendChild(btn);
    });
}
async function signPlayer(){
    let name = prompt("Player Name:");
    let value = parseInt(prompt("Value:"));
    await fetch('/transfer', {
        method: 'POST',
        headers: {'Content-Type':'application/x-www-form-urlencoded'},
        body: 'player_name=' + encodeURIComponent(name) + '&player_value=' + value
    });
    loadClub();
}
async function buyPlayer(name,club,value){
    await fetch('/transfer', {
        method: 'POST',
        headers: {'Content-Type':'application/x-www-form-urlencoded'},
        body: 'player_name=' + encodeURIComponent(name) + '&player_value=' + value
    });
    loadClub();
}
async function nextWeek(){
    await fetch('/next', {method:'POST'});
    loadClub();
}
async function acceptSponsor(){
    await fetch('/accept-sponsor', {method:'POST'});
    loadClub();
}
</script>
</body>
</html>
"""

@app.get("/club-status")
def club_status():
    # Get my_club data for frontend
    generate_transfer_market()
    return {
        "budget": my_club.budget,
        "stadium_capacity": my_club.stadium_capacity,
        "manager": my_club.manager.name if my_club.manager else None,
        "players": [{"name":p.name,"skill":p.skill,"injured":p.injured} for p in my_club.players],
        "events": current_events.copy(),
        "transfer_market": transfer_market.copy()
    }

@app.post("/transfer")
def transfer(player_name: str = Form(...), player_value: int = Form(...)):
    # Try to sign a new player
    p = Player(player_name,"Midfielder",random.randint(50,90),player_value)
    msg = my_club.sign_player(p)
    return {"msg": msg}

@app.post("/next")
def next_week():
    # Simulate matches, calculate income, and generate events
    league.play_week()
    my_club.calculate_weekly_income()
    generate_events()
    generate_transfer_market()
    return {"msg": "Week advanced."}

@app.post("/accept-sponsor")
def accept_sponsor():
    global pending_sponsor_offer
    if pending_sponsor_offer:
        my_club.budget += pending_sponsor_offer
        current_events.append(f"Sponsor deal accepted! +${pending_sponsor_offer}")
        pending_sponsor_offer = None
    return {"msg": "Sponsor offer accepted."}

if __name__ == "__main__":
    uvicorn.run("fm24_owner_ai_events:app", host="127.0.0.1", port=8000, reload=True)
