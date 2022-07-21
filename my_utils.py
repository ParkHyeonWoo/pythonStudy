import cx_Oracle
import pandas as pd
import requests

api_key = 'RGAPI-67d136a0-7d96-4365-b1ae-0c458fce4e41'

def db_open():
    global db
    global cursor
    dsn = cx_Oracle.makedsn('localhost', 1521, 'xe')
    db = cx_Oracle.connect(user='icia', password='1234', dsn=dsn)
    cursor = db.cursor()
    print('db_open!')

def sql_execute(query):
    global db
    global cursor
    try:
        if 'select' in query:
            df = pd.read_sql(sql = query, con = db)
            return df
        cursor.execute(query)
        return 'success'
    except Exception as ex:
        print(ex)

def db_close():
    global db
    global cursor
    try:
        db.commit()
        cursor.close()
        db.close()
        print('db_close!')
    except Exception as ex:
        print(ex)
        
def df_creater(url):
    url = url.replace('(인증키)',api_key).replace('xml','json').replace('/5','/1000')
    req = requests.get(url).json()
    key = list(req.keys())[0]
    data = req[key]['row']
    df = pd.DataFrame(data)
    return df

def get_puuid(name):
    url = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+name+'?api_key='+api_key
    res = requests.get(url).json()
    return res['puuid']

def get_matchid(puuid, num):
    url= 'https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+puuid+'/ids?start=0&count='+str(num)+'&api_key='+api_key
    res = requests.get(url).json()
    return res

def get_matchs_timelines(matchid):
    tmp = []
    for match in matchid:
        mat = 'https://asia.api.riotgames.com/lol/match/v5/matches/'+match+'?api_key='+api_key
        res_mat = requests.get(mat).json()
        mat_ti = 'https://asia.api.riotgames.com/lol/match/v5/matches/'+match+'/timeline?api_key='+api_key
        res_mat_ti = requests.get(mat_ti).json()
        tmp.append([match, res_mat, res_mat_ti])
    return tmp