import MySQLdb

from players import *
import pickle

def connect_mysql(host="localhost",db="retrosheet", un="retrosheet", pw="retrosheet"):
    """ This will connect the the mysql database, and return the connection """
    return MySQLdb.connect(host, un, pw, db)

def main():
        
    pickle_file = open("mean_pitcher.pickle","w")
    conn    = connect_mysql()
    cursor  = conn.cursor()
    sql = "select EVENTS.*,GAMES.GAME_DT,ROSTERS.POS_TX FROM EVENTS LEFT JOIN GAMES ON EVENTS.GAME_ID = GAMES.GAME_ID  LEFT JOIN ROSTERS ON EVENTS.BAT_ID = ROSTERS.PLAYER_ID WHERE GAMES.GAME_DT > 80000 AND GAMES.GAME_DT < 90000 AND EVENTS.BAT_EVENT_FL = 'T' LIMIT 500000"
    mean_pitcher = Pitcher("PITCHER")
    cursor.execute(sql)
    print "Query Finished"
    mean_pitcher.atbats_raw = cursor.fetchall()
    mean_pitcher.process_at_bats(False, False)
    print "The",mean_pitcher.id,"faces batters with an average of",mean_pitcher.calc_opp_batting_avg()

    pickle.dump(mean_pitcher,pickle_file)

main()
