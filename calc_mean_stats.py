import MySQLdb

from players import *
import pickle

def connect_mysql(host="localhost",db="retrosheet", un="retrosheet", pw="retrosheet"):
    """ This will connect the the mysql database, and return the connection """
    return MySQLdb.connect(host, un, pw, db)

def main():
        
    pickle_file = open("mean_players.pickle","w")
    conn    = connect_mysql()
    cursor  = conn.cursor()
    mean_player_dict = {}
    for pos in ["C","P","1B","2B","3B","SS","OF","X"]:
    #for pos in ["C","P"]:
        mean_player_dict[pos] = Batter(pos)

        print "Processing",pos
        sql = "select EVENTS.*,GAMES.GAME_DT,ROSTERS.POS_TX FROM EVENTS LEFT JOIN GAMES ON EVENTS.GAME_ID = GAMES.GAME_ID  LEFT JOIN ROSTERS ON EVENTS.BAT_ID = ROSTERS.PLAYER_ID WHERE GAMES.GAME_DT > 80000 AND GAMES.GAME_DT < 90000 AND EVENTS.BAT_EVENT_FL = 'T' AND ROSTERS.POS_TX = '"+pos+"' LIMIT 20000"

        cursor.execute(sql)
        print "Query Finished"
        mean_player_dict[pos].atbats_raw = cursor.fetchall()
        mean_player_dict[pos].process_at_bats(False, False)
        print "The",pos,"position bats an average of",mean_player_dict[pos].calc_batting_avg()
    pickle.dump(mean_player_dict,pickle_file)

main()
