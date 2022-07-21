import cx_Oracle
import pandas as pd
import requests
from random import *
from tqdm import tqdm

api_key = 'RGAPI-d12d74b8-e085-4a99-b167-f7196531ea67'

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
            df = pd.read_sql(sql=query, con=db)
            return df
        cursor.execute(query)
        return 'success'
    except Exception as ex:
        print(ex)
        
def sql_create():
    db_open()
    query = """
    create table mini_pro(gameId varchar(20), gameDuration number(10), gameVersion varchar(20), participantId varchar(2), teamId varchar(3), championName varchar(20), 
    totalDamageDealt number(5), totalDamageDealtToChampions number(5), totalDamageTaken number(5), teamPosition varchar(10), summonerName varchar(100),
    summonerLevel varchar(4), kills number(3), assists number(3), deaths number(3), summoner1Id varchar(5), summoner2Id varchar(5), item0 varchar(5), 
    item1 varchar(5), item2 varchar(5), item3 varchar(5), item4 varchar(5), item5 varchar(5), item6 varchar(5), totalGold varchar(255))
    """
    sql_execute(query)
    db_close()
    
def sql_insert(x):
    query = (f"insert into mini_pro(gameId, gameDuration, gameVersion, participantId, teamId, championName, totalDamageDealt, totalDamageDealtToChampions, "
            f"totalDamageTaken, teamPosition, summonerName, summonerLevel, kills, assists, deaths, summoner1Id, summoner2Id, item0, "
            f"item1, item2, item3, item4, item5, item6, totalGold) values (\'{x.gameId}\', {x.gameDuration}, \'{x.gameVersion}\', "
            f"\'{x.participantId}\', \'{x.teamId}\', \'{x.championName}\', {x.totalDamageDealt}, {x.totalDamageDealtToChampions}, {x.totalDamageTaken},"
            f"\'{x.teamPosition}\', \'{x.summonerName}\', \'{x.summonerLevel}\', {x.kills}, {x.assists}, {x.deaths}, \'{x.summoner1Id}\', "
            f"\'{x.summoner2Id}\', \'{x.item0}\', \'{x.item1}\', \'{x.item2}\', \'{x.item3}\', \'{x.item4}\', \'{x.item5}\', \'{x.item6}\', "
            f"\'{x.totalGold}\')")
    sql_execute(query)

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

def get_puuid(name):
    try:
        url = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + name + '?api_key=' + api_key
        res = requests.get(url).json()
        return res['puuid']

def get_matchid(puuid, num):
    url = 'https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/' + puuid + '/ids?start=0&count=' + str(
        num) + '&api_key=' + api_key
    res = requests.get(url).json()
    return res

def get_matchs_timelines(matchid):
    tmp = []
    for match in matchid:
        mat = 'https://asia.api.riotgames.com/lol/match/v5/matches/' + match + '?api_key=' + api_key
        res_mat = requests.get(mat).json()
        mat_ti = 'https://asia.api.riotgames.com/lol/match/v5/matches/' + match + '/timeline?api_key=' + api_key
        res_mat_ti = requests.get(mat_ti).json()
        tmp.append([match, res_mat, res_mat_ti])
    return tmp

def get_lst(summonerName_lst):
    tmp = []
    for i in tqdm(summonerName_lst):
        try:
            puuid = get_puuid(i)
        except:
            continue
        matchid = get_matchid(puuid, 5)
        matchs_timelines = get_matchs_timelines(matchid)
        tmp.extend(matchs_timelines)
    return tmp

def divi_lst(tier, division):
    page = randint(1, 20)
    lst = []
    for division in division:
        url = 'https://kr.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/'+tier+'/'+division+'?page='+str(page)+'&api_key='+api_key
        res = requests.get(url).json()
        lst.extend(res)
    return lst

def get_rawData(tier):
    division = ['I', 'II', 'III', 'IV']
    lst = []
    lst.extend(divi_lst(tier, division))
    summonerName_lst = []
    for i in range(len(lst)):
        summonerName_lst.append(lst[i]['summonerName'])
    data = []
    data.extend(get_lst(summonerName_lst))
    df = pd.DataFrame(data, columns = ['gameid', 'matchs', 'timelines'])
    df.drop_duplicates(['gameid'])
    matchs = matchs_lst(df)
    matchs = pd.DataFrame(matchs, columns = ['gameId', 'gameDuration', 'gameVersion', 'participantId', 'teamId', 'championName', 'totalDamageDealt', 
                                            'totalDamageDealtToChampions', 'totalDamageTaken', 'teamPosition', 'summonerName', 'summonerLevel', 
                                            'kills', 'assists', 'deaths', 'summoner1Id', 'summoner2Id', 'item0', 'item1', 'item2', 'item3', 
                                            'item4', 'item5', 'item6'])
    timelines = timelines_lst(df)
    timelines = pd.DataFrame(timelines, columns = ['gameId', 'participantId', 'totalGold'])
    merge_df = pd.merge(matchs, timelines)
    merge_df = merge_df[~merge_df.teamPosition.isna()]
    db_open()
    tqdm.pandas()
    merge_df.progress_apply(lambda x: sql_insert(x), axis = 1)
    tmp = sql_execute('select * from mini_pro')
    db_close()
    return tmp

def matchs_lst(df):
    lst = []
    for i in tqdm(range(len(df))):
        try:
            if df.iloc[i].matchs['info']['gameMode'] == 'CLASSIC':
                for j in range(10):
                    try:
                        tmp = []
                        tmp.append(df.iloc[i].matchs['info']['gameId'])
                        tmp.append(df.iloc[i].matchs['info']['gameDuration'])
                        tmp.append(df.iloc[i].matchs['info']['gameVersion'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['participantId'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['teamId'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['championName'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['totalDamageDealt'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['totalDamageDealtToChampions'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['totalDamageTaken'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['teamPosition'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['summonerName'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['summonerLevel'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['kills'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['assists'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['deaths'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['summoner1Id'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['summoner2Id'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item0'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item1'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item2'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item3'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item4'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item5'])
                        tmp.append(df.iloc[i].matchs['info']['participants'][j]['item6'])
                        lst.append(tmp)
                    except Exception as e:
                        print(e)
        except:
            continue
    return lst

def timelines_lst(df):
    lst = []
    for i in tqdm(range(len(df))):
        for j in range(1, 11):
            try:
                tmp = []
                tmp.append(df.iloc[i].timelines['info']['gameId'])
                tmp.append(df.iloc[i].timelines['info']['participants'][j-1]['participantId'])
                str_tmp = ''
                for k in range(len(df.iloc[i].timelines['info']['frames'])):
                    str_tmp += (str(df.iloc[i].timelines['info']['frames'][k]['participantFrames'][str(j)]['totalGold'])+'|')
                tmp.append(str_tmp)
                lst.append(tmp)
            except Exception as e:
                print(e)
    return lst