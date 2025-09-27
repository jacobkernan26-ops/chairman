import random
class Match:
    def __init__(self,home,away):
        self.home=home
        self.away=away

    def simulate(self):
        for p in self.home.players+self.away.players:
            if random.randint(1,50)==1: p.injured=True
        home_score=self.calculate_score(self.home,self.away)
        away_score=self.calculate_score(self.away,self.home)
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
