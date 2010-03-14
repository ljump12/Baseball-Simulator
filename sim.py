from players import *
import random
from bases import *

class Simulation():
    def __init__(self):
    
        ## Connect to the database
        self.conn = connect_mysql()
        
        ## Setup simulation variables. When get_player_data is called, the strings will
        ## be replaced with player objects. 
        self.year       = "2009"
        self.home_team       = "PHI"
        self.home_pitchers   = ["Hamels","Park","Lidge"]
        self.home_lineup     = ["Rollins","Victorino","Utley","Howard","Werth","Ibanez","Feliz","Ruiz","Happ"]

        self.away_team      = "ATL"
        self.away_pitchers  = ["Hanson"]
        self.away_lineup    = ["McLouth","Prado","Jones","Diaz","Anderson","Infante","Ross","Conrad","Hanson"]

        #self.away_team      = "HOU"
        #self.away_pitchers  = ["Lopez"]
        #self.away_lineup    = ["Matsui","Tejada","Berkman","Lee","Pence","Keppinger","Michaels","Towles","Lopez"]
        
        #self.away_team       = "NYA"
        #self.away_pitchers   = ["Pettitte","Hughes","Marte"]
        #self.away_lineup     = ["Jeter","Damon","Teixeira","Rodriguez","Posada","Matsui","Cano","Swisher","Cabrera"]

        ## Initialize game settings
        self.bases = Bases()
        self.home_runs  = 0
        self.away_runs  = 0
        self.home_hits  = 0
        self.away_hits  = 0
        self.outs       = 0
        self.inning     = 1
        self.end_game   = False
        self.home_batter    = 0
        self.away_batter    = 0

    
    def get_player_data(self):
        """ Retrieves player data from the retrosheet database, annd creates player objects """
        cursor = self.conn.cursor()
        ## Select all players on the yankees in 2009
        sql = "SELECT * FROM ROSTERS WHERE YEAR_ID = "+self.year+" AND TEAM_ID = '"+self.away_team+"'"
        cursor.execute(sql)
        self.away_players = cursor.fetchall()

        ## Select all players on the phillies in 2009
        sql = "SELECT * FROM ROSTERS WHERE YEAR_ID = "+self.year+" AND TEAM_ID = '"+self.home_team+"'"
        cursor.execute(sql)
        self.home_players = cursor.fetchall()

        #This will replace each last name with the player object 
        for player in self.home_players+self.away_players:
            if player[3] in self.home_lineup+self.away_lineup:
                batter = Batter(player[2],player[3],player[4],self.conn)
                batter.get_all_at_bats()
                batter.process_at_bats()
                print "Batter:",batter.id,batter.fn,batter.ln,batter.calc_batting_avg()
                if batter.ln in self.home_lineup:
                    self.home_lineup[self.home_lineup.index(batter.ln)] = batter
                else:
                    self.away_lineup[self.away_lineup.index(batter.ln)] = batter

            if player[3] in self.home_pitchers+self.away_pitchers:
                pitcher = Pitcher(player[2],player[3],player[4],self.conn)
                pitcher.get_all_batters()
                pitcher.process_at_bats()
                if pitcher.ln in self.home_pitchers:
                    self.home_pitchers[self.home_pitchers.index(pitcher.ln)] = pitcher
                else:
                    self.away_pitchers[self.away_pitchers.index(pitcher.ln)] = pitcher

    def determine_result(self, batter, pitcher):
        ##TODO:: ADD MORE
        r_num = random.random()
        if r_num < self.calc_cum_prob(batter,pitcher,"walk"):
            self.bases.process_event(batter,"walk")
            return "walk",self.calc_prob(batter,pitcher,"walk")
        elif r_num >= self.calc_cum_prob(batter,pitcher,"walk") and r_num < self.calc_cum_prob(batter,pitcher,"single"):
            self.bases.process_event(batter,"single")
            return "single",self.calc_prob(batter,pitcher,"single")
        elif r_num >= self.calc_cum_prob(batter,pitcher,"single") and r_num < self.calc_cum_prob(batter,pitcher,"double"):
            self.bases.process_event(batter,"double")
            return "double",self.calc_prob(batter,pitcher,"double")
        elif r_num >= self.calc_cum_prob(batter,pitcher,"double") and r_num < self.calc_cum_prob(batter,pitcher,"triple"):
            self.bases.process_event(batter,"triple")
            return "triple",self.calc_prob(batter,pitcher,"triple")
        elif r_num >= self.calc_cum_prob(batter,pitcher,"triple") and r_num < self.calc_cum_prob(batter,pitcher,"HR"):
            self.bases.process_event(batter,"HR")
            return "HR",self.calc_prob(batter,pitcher,"HR")
        elif r_num >= self.calc_cum_prob(batter,pitcher,"HR") and r_num < 1:
            self.outs += 1
            return "out",self.calc_prob(batter,pitcher,"out")
        else:
            #print "Random_Number:",r_num
            raise Exception

    def calc_prob(self, batter, pitcher, type):
        """ This is calculated as battersProb * PitchersProb/LeagueProb"""

        if type == "walk":      return batter.prob("walk") * (pitcher.prob("walk") / .0837)
        if type == "single":    return batter.prob("single") * (pitcher.prob("single") / .1559)
        if type == "double":    return batter.prob("double") * (pitcher.prob("double") / .0385)
        if type == "triple":    return batter.prob("triple") * (pitcher.prob("triple") / .0054)
        if type == "HR":        return batter.prob("HR") * (pitcher.prob("HR") / .0193)
        if type == "out":       return 1-self.calc_cum_prob(batter,pitcher,"HR")

    def calc_cum_prob(self, batter, pitcher, type):
        """ This will return the combined cumlative probabilities """
        prob = self.calc_prob(batter,pitcher,"walk")
        if type == "walk": return prob
        prob += self.calc_prob(batter,pitcher,"single")
        if type == "single": return prob
        prob += self.calc_prob(batter,pitcher,"double")
        if type == "double": return prob
        prob += self.calc_prob(batter,pitcher,"triple")
        if type == "triple": return prob
        prob += self.calc_prob(batter,pitcher,"HR")
        if type == "HR": return prob
        if type == "out": return 1
        return None

    def wrap_up_inning(self):
        
        #print "The inning ("+str(self.inning)+") is over, Runs Scored=", self.bases.runs

        ## Determine wether to credit the runs to the hometeam or awayteam
        if self.inning % 1 == 0.0:
            self.away_runs  += self.bases.runs
        else:
            self.home_runs  += self.bases.runs

        ## Check whether it's the end of the game
        print "Debug Variables: inning=",self.inning,"home_runs=",self.home_runs,"away_runs=",self.away_runs,"end_game=",self.end_game
        if (self.inning == 9 and self.home_runs > self.away_runs) or (self.inning > 9 and self.inning % 1 != 0.0 and self.home_runs != self.away_runs):
            self.end_game = True
        ## Reset the bases and outs for the next inning
        else:
            self.outs   = 0
            self.bases  = Bases()      
        self.inning += .5

    def reset_game(self):
        self.bases = Bases()
        self.home_runs  = 0
        self.away_runs  = 0
        self.home_hits  = 0
        self.away_hits  = 0
        self.outs       = 0
        self.inning     = 1
        self.end_game   = False
        self.home_batter    = 0
        self.away_batter    = 0

    def translate_inning(self):
        was_inning = self.inning -.5
        if was_inning % 1 == 0.0:
            half = "top"
        else: 
            half = "bottom"

        if int(was_inning) == 1:
            return half+" of the 1st"
        elif int(was_inning) == 2:
            return half+" of the 2nd"
        elif int(was_inning) == 3:
            return half+" of the 3rd"
        elif int(was_inning) >= 4:
            return half+" of the "+str(int(was_inning))+"th"

def main():
    sim = Simulation()
    sim.get_player_data()



    total_home_wins = 0
    total_away_wins = 0
    total_home_runs = 0
    total_away_runs = 0
    num_games = 1000.0
    game_num  = 0
    



    while (game_num < num_games):
        sim.reset_game()
        while sim.end_game == False:
            if sim.inning % 1 == 0.0:
                pitcher = sim.home_pitchers[0]
                batter = sim.away_lineup[sim.away_batter % 9]
                result = sim.determine_result(batter,pitcher)
                print batter.ln,"faces",pitcher.ln,"and gets a",result
                sim.away_batter +=1
            else:
                pitcher = sim.away_pitchers[0]
                batter = sim.home_lineup[sim.home_batter % 9]
                result = sim.determine_result(batter,pitcher)
                print batter.ln,"faces",pitcher.ln,"and gets a",result
                sim.home_batter +=1
            if sim.outs >= 3 or (sim.bases.runs+sim.home_runs > sim.away_runs and sim.inning >= 9.5 and sim.inning % 1 != 0.0):
                sim.wrap_up_inning()
                print "After the",sim.translate_inning(),"the score is:",sim.away_team,sim.away_runs,sim.home_team,sim.home_runs
        
        print "The game ended in",int(sim.inning)-1,"innings:",sim.away_team,sim.away_runs,sim.home_team,sim.home_runs
        if sim.home_runs > sim.away_runs:
            total_home_wins += 1
        else:
            total_away_wins += 1
        total_home_runs += sim.home_runs
        total_away_runs += sim.away_runs


        game_num += 1


    print "Total Statistics:"
    print "Home ("+str(sim.home_team)+") Wins:",total_home_wins
    print "Away ("+str(sim.away_team)+") Wins:",total_away_wins
    print "Avg Home Runs",total_home_runs/num_games
    print "Avg Away Runs",total_away_runs/num_games


        #print "that batter had a",batter.prob("walk"),"percent chance of a walk"

if __name__ == "__main__":
    main()
