from sim import *
import MySQLdb
import re 

def connect_mysql(host="localhost",db="retrosheet", un="retrosheet", pw="retrosheet"):
    """ This will connect the the mysql database, and return the connection """
    return MySQLdb.connect(host, un, pw, db)

def main():
        
    conn    = connect_mysql()
    cursor  = conn.cursor()

    team = "PHI"
    ## This will get all the games for the team from 2009
    sql = "SELECT * FROM GAMES WHERE GAME_DT >= 90500 AND GAME_DT <= 91200"
    sql +=" ORDER BY GAMES.GAME_DT"
    cursor.execute(sql)
    games = cursor.fetchall() 

    overall_score = 0
    
    outputFile = open("2009_season_rest.csv", "w")

    for game in games:
        print game
        print game[1]
        away_pitcher = game[10]
        home_pitcher = game[11]

        away_batter1    = game[46]
        away_batter2    = game[48]
        away_batter3    = game[50]
        away_batter4    = game[52]
        away_batter5    = game[54]
        away_batter6    = game[56]
        away_batter7    = game[58]
        away_batter8    = game[60]
        away_batter9    = game[62]

        home_batter1    = game[64]
        home_batter2    = game[66]
        home_batter3    = game[68]
        home_batter4    = game[70]
        home_batter5    = game[72]
        home_batter6    = game[74]
        home_batter7    = game[76]
        home_batter8    = game[78]
        home_batter9    = game[80]
        
        date = game[1]

        away_score = game[34]
        home_score = game[35]


        sim = Simulation(outputFile)
        sim.year = "2009"
        sim.home_team   = game[8]
        print sim.home_team
        sim.home_pitchers   = [home_pitcher]
        print sim.home_pitchers
        #sim.home_pitchers   = ["myerb001"]
        sim.home_lineup     = [home_batter1,home_batter2,home_batter3,home_batter4,home_batter5,home_batter6,home_batter7,home_batter8,home_batter9]
        #sim.home_lineup     = ["rollj001","wertj001","utlec001","howar001","ibanr001","victs001","felip001","ruizc001","myerb001"]

        sim.away_team      = game[7]
        sim.away_pitchers   = [away_pitcher]
        #sim.away_pitchers  = ["lowed001"]
        sim.away_lineup     = [away_batter1,away_batter2,away_batter3,away_batter4,away_batter5,away_batter6,away_batter7,away_batter8,away_batter9]
        #sim.away_lineup    = ["johnk003","escoy001","jonec004","mccab002","andeg001","franj004","kotcc001","schaj002","lowed001"]
    
        sim.get_player_data()
        print "Running sim for",date
        away_perc,home_perc,sim_total = sim.run_sim(date)

        total = away_score+home_score
        
        ## Figure out the real winner
        real_winner = sim.home_team
        if away_score > home_score:
            real_winner = sim.away_team
        ## Figure out the sim winner
        sim_winner  = sim.home_team
        if away_perc > home_perc:
            sim_winner = sim.away_team


        if sim_winner == real_winner:
            overall_score += 1
        else:
            overall_score -= 1
        print "The overall score is:",overall_score


main()
