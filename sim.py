from players import *
import pickle
import os
import random
from bases import *

class Simulation():
    def __init__(self, outputFile = "/dev/null"):
    
        ## Connect to the database
        self.conn = connect_mysql()
        
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

        self.outputFile = outputFile
        ## Seed the random number generator using /dev/random
        random.seed()

    
    def get_player_data(self):
        """ Retrieves player data from the retrosheet database, annd creates player objects """
        cursor = self.conn.cursor()
        ## Select all players on the yankees in 2009
        sql = "SELECT * FROM ROSTERS WHERE YEAR_ID >= 2008"
        cursor.execute(sql)
        self.players = cursor.fetchall()

        #This will replace each last name with the player object 
        for player in self.players:
            if player[2] in self.home_lineup+self.away_lineup:
                pickle_file = "player_pickles/"+player[2]+"_batter_2009.pickle"
                if os.path.exists(pickle_file):
                    batter = pickle.load(open(pickle_file,"r"))
                else:
                    batter = Batter(player[2],player[3],player[4],player[8],self.conn,"80405","100000")
                    batter.get_all_at_bats()
                    batter.process_at_bats()
                    pickle_fh = open(pickle_file,"w")
                    pickle.dump(batter,pickle_fh)
                print "Batter:",batter.id,batter.fn,batter.ln,batter.calc_batting_avg()
                if batter.id in self.home_lineup:
                    self.home_lineup[self.home_lineup.index(batter.id)] = batter
                else:
                    self.away_lineup[self.away_lineup.index(batter.id)] = batter

            if player[2] in self.home_pitchers+self.away_pitchers:
                pickle_file = "player_pickles/"+player[2]+"_pitcher_2009.pickle"
                if os.path.exists(pickle_file):
                    pitcher = pickle.load(open(pickle_file,"r"))
                else:
                    pitcher = Pitcher(player[2],player[3],player[4],"PITCHER",self.conn,"70405","100000")
                    pitcher.get_all_batters()
                    pitcher.process_at_bats()
                    pickle_fh = open(pickle_file,"w")
                    pickle.dump(pitcher,pickle_fh)
                if pitcher.id in self.home_pitchers:
                    self.home_pitchers[self.home_pitchers.index(pitcher.id)] = pitcher
                else:
                    self.away_pitchers[self.away_pitchers.index(pitcher.id)] = pitcher

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
        #print "Debug Variables: inning=",self.inning,"home_runs=",self.home_runs,"away_runs=",self.away_runs,"end_game=",self.end_game
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

    def run_sim(self, date="91004"):
        total_home_wins = 0
        total_away_wins = 0
        total_home_runs = 0
        total_away_runs = 0
        num_games = 1000.0
        game_num  = 0

        print "About to run sim: Lineup Info:"
        for batter in self.home_lineup+self.away_lineup:
            print batter
            last_batter_date    = self.find_last_game_date(date, batter)
            print batter.fn,batter.ln,batter.snapshots[last_batter_date].calc_batting_avg(),"in",batter.snapshots[last_batter_date].total_at_bats,"at bats.."
        for pitcher in self.home_pitchers+self.away_pitchers:
            print pitcher
            last_pitcher_date   = self.find_last_game_date(date, pitcher)
            print pitcher.fn,pitcher.ln,pitcher.snapshots[last_pitcher_date].calc_opp_batting_avg(),"after facing",pitcher.snapshots[last_pitcher_date].total_at_bats,"batters"

        while (game_num < num_games):
            self.reset_game()
            while self.end_game == False:
                if self.inning % 1 == 0.0:
                    pitcher = self.home_pitchers[0]
                    batter = self.away_lineup[self.away_batter % 9]
                    last_pitcher_date   = self.find_last_game_date(date, pitcher)
                    last_batter_date    = self.find_last_game_date(date, batter)
                    #print "Batter",batter.snapshots[last_batter_date].total_singles,last_pitcher_date,batter.snapshots.keys()
                    #print "Pithcer",pitcher.snapshots[last_pitcher_date].total_singles,last_batter_date
                    result = self.determine_result(batter.snapshots[last_batter_date],pitcher.snapshots[last_pitcher_date])
                    #print batter.ln,"faces",pitcher.ln,"and gets a",result
                    self.away_batter +=1
                else:
                    pitcher = self.away_pitchers[0]
                    batter = self.home_lineup[self.home_batter % 9]
                    last_pitcher_date   = self.find_last_game_date(date, pitcher)
                    last_batter_date    = self.find_last_game_date(date, batter)
                    result = self.determine_result(batter.snapshots[last_batter_date],pitcher.snapshots[last_pitcher_date])
                    #print batter.ln,"faces",pitcher.ln,"and gets a",result
                    self.home_batter +=1
                if self.outs >= 3 or (self.bases.runs+self.home_runs > self.away_runs and self.inning >= 9.5 and self.inning % 1 != 0.0):
                    self.wrap_up_inning()
                    #print "After the",self.translate_inning(),"the score is:",self.away_team,self.away_runs,self.home_team,self.home_runs
            
            #print "The game ended in",int(self.inning)-1,"innings:",self.away_team,self.away_runs,self.home_team,self.home_runs
            if self.home_runs > self.away_runs:
                total_home_wins += 1
            else:
                total_away_wins += 1
            total_home_runs += self.home_runs
            total_away_runs += self.away_runs


            game_num += 1


        print "Total Statistics:"
        print "Home ("+str(self.home_team)+") Wins:",total_home_wins
        print "Away ("+str(self.away_team)+") Wins:",total_away_wins
        print "Avg Home Runs",total_home_runs/num_games
        print "Avg Away Runs",total_away_runs/num_games
        average_runs = (total_home_runs+total_away_runs)/num_games
        self.outputFile.write(str(date)+","+str(self.away_team)+","+str(self.home_team)+","+str(total_away_wins)+","+str(total_home_wins)+","+str(average_runs)+"\n")
        return (total_away_wins,total_home_wins,average_runs)

    def find_last_game_date(self, date, player):
        """ Returns the last date the player played in a game, before the current date given """
        possible_dates = [int(new_date) for new_date in player.snapshots.keys() if int(new_date) < int(date)]
        if possible_dates != []:
            return str(max(possible_dates))
        else:
            return "0"
         
def main():
    sim = Simulation()

    ## Setup simulation variables. When get_player_data is called, the strings will
    ## be replaced with player objects. 
    sim.year       = "2009"
    sim.home_team       = "BOS"
    sim.home_pitchers   = ["beckj002"]
    sim.home_lineup     = ["ellsj001","pedrd001","martv001","youkk001","ortid001","belta001","camem001","drewj001","scutm001"]

    sim.away_team      = "NYY"
    sim.away_pitchers  = ["sabac001"]
    sim.away_lineup    = ["jeted001","granc001","teixm001","rodra001","posaj001","canor001","johnn001","swisn001","gardb001"]

    sim.get_player_data()
    sim.run_sim()


    

        #print "that batter had a",batter.prob("walk"),"percent chance of a walk"

if __name__ == "__main__":
    main()
