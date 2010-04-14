import MySQLdb
import pickle
import re 
from copy import copy

def connect_mysql(host="localhost",db="retrosheet", un="retrosheet", pw="retrosheet"):
    """ This will connect the the mysql database, and return the connection """
    return MySQLdb.connect(host, un, pw, db)

class Player():


    def __init__(self, player_id, player_ln, player_fn, position, db_connect, start_date, end_date):
        self.start_date             = start_date
        self.end_date               = end_date
        self.last_processed_date    = None

        self.conn    = db_connect

        self.id      = player_id
        self.ln      = player_ln
        self.fn      = player_fn
        ## Override the position if its LF RF or CF, and just make them OF
        if position in ["LF","RF","CF"]:
            position = "OF"
        self.position = position
        
        self.total_at_bats  = 1.0
        ##TODO:: Earned runs/Runs, are close -- but not miscalculated
        self.total_runs     = 0
        self.total_ER       = 0
        self.total_hits     = 0
        self.total_walks    = 0
        self.total_so       = 0
        self.total_hbp      = 0
        self.total_sac_fly  = 0
        self.total_rbi      = 0

        self.total_dp_ops   = 0
        self.total_dp       = 0

        self.total_singles  = 0
        self.total_doubles  = 0
        self.total_triples  = 0
        self.total_home_runs= 0

        self.total_games    = 0

        self.snapshots      = {}

        ## This will load in our mean player stats 
        if self.position != "PITCHER":
            self.mean_player = pickle.load(open("mean_players.pickle","r"))[self.position]
        else:
            self.mean_player = pickle.load(open("mean_pitcher.pickle","r"))

        ## Create a null snapshot of the player..
        self.snapshots["0"] = Snapshot(self)


    def cum_prob(self, type):
        """ This will return the cumulative probabilities, this allows us to
            easily use a random number generator to determine events
        """
        
        prob = self.prob("walk")
        if type == "walk": return prob
        prob += self.prob("single")
        if type == "single": return prob
        prob += self.prob("double")
        if type == "double": return prob
        prob += self.prob("triple")
        if type == "triple": return prob
        prob += self.prob("HR")
        if type == "HR": return prob
        if type == "out": return 1-prob
        return None

    def prob(self, type):
        """ This determines the probability of any single event. We calculate
            the probability by taking the number of times the event happened,
            and dividing it by the total plate appearances of the batter (or pitcher)
        """

        prob = None
        if type == "walk":
            prob = float(self.total_walks)/self.plate_appearances() 
        elif type == "single":
            prob = float(self.total_singles)/self.plate_appearances()
        elif type == "double":
            prob = float(self.total_doubles)/self.plate_appearances()
        elif type == "triple":
            prob = float(self.total_triples)/self.plate_appearances()
        elif type == "HR":
            prob = float(self.total_home_runs)/self.plate_appearances()
        return prob


    def regress_once(self):
        mean_player = self.mean_player

        self.total_games        += (mean_player.total_games/mean_player.total_at_bats)
        self.total_runs         += (mean_player.total_runs/mean_player.total_at_bats)
        self.total_singles      += (mean_player.total_singles/mean_player.total_at_bats)
        self.total_doubles      += (mean_player.total_doubles/mean_player.total_at_bats)
        self.total_triples      += (mean_player.total_triples/mean_player.total_at_bats)
        self.total_home_runs    += (mean_player.total_home_runs/mean_player.total_at_bats)
        self.total_hits         += (mean_player.total_hits/mean_player.total_at_bats)
        self.total_so           += (mean_player.total_so/mean_player.total_at_bats)
        self.total_walks        += (mean_player.total_walks/mean_player.total_at_bats)
        self.total_hbp          += (mean_player.total_hbp/mean_player.total_at_bats)
        self.total_sac_fly      += (mean_player.total_sac_fly/mean_player.total_at_bats)
        self.total_dp_ops       += (mean_player.total_dp_ops/mean_player.total_at_bats)
        self.total_dp           += (mean_player.total_dp/mean_player.total_at_bats)
        self.total_at_bats      += 1

    def plate_appearances(self):
        """ Calculates the number of plate appearances the player had """

        return (self.total_at_bats + self.total_walks + self.total_hbp + self.total_sac_fly)

    def process_at_bats(self, create_snapshots=True, regress_to_mean=True):
        """ Processes through the results from the database, adding each event to our
            player object
        """

        for atbat in self.atbats_raw:
            event       = int(atbat[34])
            event_tx    = str(atbat[29])
            was_atbat   = atbat[36]
            rbis        = int(atbat[43])
            date        = str(atbat[158])

            man_on_first = False
            if str(atbat[26]) != "": man_on_first = True 
             
            if date not in self.snapshots:
                self.total_games    +=1

            self.total_runs += rbis
            if not re.search("\(UR\)",event_tx):
                self.total_ER += rbis    

            if event == 20:
                self.total_singles += 1
            elif event == 21:
                self.total_doubles += 1
            elif event == 22:
                self.total_triples += 1
            elif event == 23:
                self.total_home_runs += 1

            if event in [20,21,22,23]:
                self.total_hits +=1

            if event == 3:
                self.total_so +=1

            if event in [14,15]:
                self.total_walks +=1

            if event == 16:
                self.total_hbp +=1

            ## Sac fly's
            if re.search("SF",event_tx):
                self.total_sac_fly += 1
            
            ## Double plays
            if man_on_first:
                self.total_dp_ops   += 1
            if re.search("LDP",event_tx) or re.search("GDP",event_tx):
                self.total_dp += 1 

            if was_atbat == "T":
                self.total_at_bats +=1

            if create_snapshots:
                self.snapshots[date] = Snapshot(self)
                while self.snapshots[date].total_at_bats < 400 and regress_to_mean:
                    self.snapshots[date].regress_once()
        ## After we have processed the at-bats, clear them from memory
        self.atbats_raw = None

        while (self.total_at_bats < 400 and regress_to_mean):
            self.regress_once()


class Batter(Player):
    """ This extends the Player Object with certain function's individual to a batter """

    def __init__(self, player_id, player_ln=None, player_fn=None, position="X", db_connect=None, start_date="090405", end_date="091001"):
        Player.__init__(self, player_id, player_ln, player_fn, position, db_connect, start_date, end_date)

    def calc_batting_avg(self):
        """ Calculates the batting avg of the batter """
        if self.total_at_bats > 0:
            return (self.total_hits/float(self.total_at_bats))
        else:
            return 0.0

    def calc_total_bases(self):
        """ Calculates total bases """
        return (self.total_singles + (2*self.total_doubles) + (3*self.total_triples) + (4*self.total_home_runs))

    def calc_obp(self):
        """ Calculates On Base Percentage. This determines how often a batter gets on base"""
        top = (self.total_hits + self.total_walks + self.total_hbp)
        bottom = (self.total_at_bats + self.total_walks + self.total_hbp + self.total_sac_fly)
        return float(top)/bottom

    def calc_slg(self):
        """ Calculates the sluggin percentage. (A batter who only hit homeruns would have a SLG of 4"""
        return float(self.calc_total_bases())/self.total_at_bats

    def calc_base_runs(self):
        """ This function will calulate Base Runs (BsR). An estimator developed by david Smyth in the early 1990's """
        A = (self.total_hits + self.total_walks - self.total_home_runs)
        B = (1.4*self.calc_total_bases() - .6*self.total_hits - 3*self.total_home_runs + .1*self.total_walks)*1.02
        C = self.total_at_bats - self.total_hits
        D = self.total_home_runs

        return A*B/(B + C) + D
            
    ##TODO:: Fix regress to MEAN based on player position averages
    def regress_to_mean(self):
        while (self.plate_appearances() < 100):
            return

    def get_all_at_bats(self):
        """ This will retreive all at bats for the player between the start date and the end date """
        cursor = self.conn.cursor()
        ## This will get all at bats in 2009 from the player where it was the final event in the atbat
        sql = "select EVENTS.*,GAMES.GAME_DT FROM EVENTS LEFT JOIN GAMES ON EVENTS.GAME_ID = GAMES.GAME_ID "
        sql +=" WHERE GAMES.GAME_DT > "+self.start_date+" AND GAMES.GAME_DT < "+self.end_date+ " AND EVENTS.BAT_ID='"+self.id+"' AND EVENTS.BAT_EVENT_FL = 'T'" 
        sql +=" ORDER BY GAMES.GAME_DT"
        cursor.execute(sql)
        self.atbats_raw = cursor.fetchall()

class Pitcher(Player):
    """ This extends the Player Object with certain function's individual to a batter """
    def __init__(self, player_id, player_ln=None, player_fn=None, position="PITCHER", db_connect=None, start_date="090405", end_date="091001"):
        Player.__init__(self, player_id, player_ln, player_fn, position, db_connect, start_date, end_date)

    def get_all_batters(self):
        """ This will retreive all batters the pitcher faced between the start date and the end date """
        cursor = self.conn.cursor()
        ## This will get all at bats in 2009 from the player where it was the final event in the atbat
        sql = "select EVENTS.*,GAMES.GAME_DT FROM EVENTS LEFT JOIN GAMES ON EVENTS.GAME_ID = GAMES.GAME_ID "
        sql +=" WHERE GAMES.GAME_DT >= "+self.start_date+" AND GAMES.GAME_DT <= "+self.end_date+" AND EVENTS.PIT_ID='"+self.id+"' AND EVENTS.BAT_EVENT_FL = 'T'" 
        sql +=" ORDER BY GAMES.GAME_DT"
        cursor.execute(sql)
        self.atbats_raw = cursor.fetchall()
    
    def calc_opp_batting_avg(self):
        """ Calculates the batting avg of the opposing batters """
        if self.total_at_bats > 0:
            return (self.total_hits/float(self.total_at_bats))
        else:
            return 0.0


class Snapshot(Pitcher):
    """ This class is used to take a snapshot of a players stats in time, snapshots are added onto
        player objects in a map, and can be accessed by their date. Becuase it is an extention of 
        the pitcher, we can access all the normal functions as if it weren't a snapshot.
    """
    
    def __init__(self, Pitcher):
        self.total_at_bats  = copy(Pitcher.total_at_bats)
        self.total_runs     = copy(Pitcher.total_runs)
        self.total_hits     = copy(Pitcher.total_hits)
        self.total_walks    = copy(Pitcher.total_walks)
        self.total_so       = copy(Pitcher.total_so)
        self.total_hbp      = copy(Pitcher.total_hbp)
        self.total_sac_fly  = copy(Pitcher.total_sac_fly)
        self.total_rbi      = copy(Pitcher.total_rbi)

        self.total_singles  = copy(Pitcher.total_singles)
        self.total_doubles  = copy(Pitcher.total_doubles)
        self.total_triples  = copy(Pitcher.total_triples)
        self.total_home_runs= copy(Pitcher.total_home_runs)
        self.total_dp_ops   = copy(Pitcher.total_dp_ops)
        self.total_dp       = copy(Pitcher.total_dp)

        self.total_games    = copy(Pitcher.total_games)
        if Pitcher.position != "PITCHER":
            self.mean_player    = Pitcher.mean_player
    
    def calc_batting_avg(self):
        """ Calculates the batting avg of the batter """
        if self.total_at_bats > 0:
            return (self.total_hits/float(self.total_at_bats))
        else:
            return 0.0


