import os
import random
from shutil import copyfile
import math
import shutil
import re
def round_robin(units, sets = None):
    """ Generates a schedule of "fair" pairings from a list of units """
    count = len(units)
    sets = sets or (count - 1)
    half = int(count / 2)
    print(half)
    print("------")
    print(units)
    for turn in range(sets):
        left = units[:half]
        right = units[count - half - 1 + 1:][::-1]
        pairings = zip(left, right)
        if turn % 2 == 1:
            pairings = [(y, x) for (x, y) in pairings]
        units.insert(1, units.pop())
        yield pairings

def list_cha():
    cha = []
    path = r'D:\H\Division 1'
    dirs = os.listdir( path )
    for file in dirs:
       cha.append(file)
    try:
        cha.remove("Thumbs.db")
    except:
        print("none")
    return cha

#create league fixture with pic
def create_league():
    name_count = {}
    name_random = {}
    list_character = list_cha()
    random.shuffle(list_character)

    for name in list_character:
        print(name)
        name_count[name] = 0
        name_random[name] = random.sample(range(1, 51), 50)+random.sample(range(1, 51), 8)
    print(name_random)
    print(name_count)
        
    league = list(round_robin(list_character, sets = len(list_character) * 2 - 2))
    week = 1
    path = r'D:\H\League'
    for a in league:
        week_text = "week {}".format(week)
        os.makedirs(path+"\\"+week_text)

        match_time = random.sample(range(1, 16), 15)
        match_time_index = 0
        for b in a:
            match = ""

            m1 = ""
            m2 = ""
            m1_name = ""
            m2_name = ""
            
            for c in b:
                if match != "":
                    match = match + " VS "
                    m2 = 'LeaguePIC_'+str(name_random[c][name_count[c]])
                    m2_name = c
                    
                else:

                    print(c)
                    print(name_count[c])
                    m1 = 'LeaguePIC_'+str(name_random[c][name_count[c]])
                    m1_name = c

                name_count[c] = name_count[c]+1
                match = match+c

            full_match_name = str(match_time[match_time_index])+". "+match
                
            os.makedirs(path+"\\"+week_text+"\\"+full_match_name)
            file_type_1 = ".jpg"
            if os.path.exists(r'D:\H\PIC\\'+m1_name+"\\"+m1+".jpg"):
                file_type_1 = ".jpg"
            if os.path.exists(r'D:\H\PIC\\'+m1_name+"\\"+m1+".gif"):
                file_type_1 = ".gif"
            if os.path.exists(r'D:\H\PIC\\'+m1_name+"\\"+m1+".png"):
                file_type_1 = ".png"
            if os.path.exists(r'D:\H\PIC\\'+m1_name+"\\"+m1+".jpeg"):
                file_type_1 = ".jpeg"
            if os.path.exists(r'D:\H\PIC\\'+m1_name+"\\"+m1+".bmp"):
                file_type_1 = ".bmp"

            file_type_2 = ".jpg"
            if os.path.exists(r'D:\H\PIC\\'+m2_name+"\\"+m2+".jpg"):
                file_type_2 = ".jpg"
            if os.path.exists(r'D:\H\PIC\\'+m2_name+"\\"+m2+".gif"):
                file_type_2 = ".gif"
            if os.path.exists(r'D:\H\PIC\\'+m2_name+"\\"+m2+".png"):
                file_type_2 = ".png"
            if os.path.exists(r'D:\H\PIC\\'+m2_name+"\\"+m2+".jpeg"):
                file_type_2 = ".jpeg"
            if os.path.exists(r'D:\H\PIC\\'+m2_name+"\\"+m2+".bmp"):
                file_type_2 = ".bmp"
                
                
            copyfile(r'D:\H\PIC\\'+m1_name+"\\"+m1+file_type_1, path+"\\"+week_text+"\\"+full_match_name+'\\'+m1+file_type_1)
            copyfile(r'D:\H\PIC\\'+m2_name+"\\"+m2+file_type_2, path+"\\"+week_text+"\\"+full_match_name+'\\'+m2+"(A)"+file_type_2)
            match_time_index = match_time_index+1
        
        week = week+1
        
#rename character pic before start league
def pic_rename():
    list_character = list_cha()
    path = r'D:\H\PIC'
    
    for name in list_character:
        dirs = os.listdir( path+"\\"+name)
        i=0
        for file in dirs:
            if file !="Thumbs.db":
                i=i+1
                try:
                    os.rename(path+"\\"+name+"\\"+file, path+"\\"+name+"\\"+"LeaguePIC_{}.jpg".format(i))
                except:
                    print(path+"\\"+name+"\\"+file)


#calculate rank per week
def rank_cal(week):
    path = r'D:\H\League'
    list_character = list_cha()

    name_data = {}
    
    for name in list_character:
        name_data[name] = {}
        name_data[name]['point'] = 0
        name_data[name]['g1'] = 0
        name_data[name]['g2'] = 0
        name_data[name]['g3'] = 0
        name_data[name]['W'] = 0
        name_data[name]['T'] = 0
        name_data[name]['L'] = 0
        
    i = 1
    while i<= week:
        week_text = "week {}".format(i)
        week_path = path+"\\"+week_text
        dirs = os.listdir( week_path )
        
        for file_full in dirs:
            file_split = file_full.split(". ")
            if len(file_split) > 2:
                file = ""
                fi = 0
                for f in file_split:
                    if fi == 0:
                        fi +=1
                        continue
                    file = file + ". " + f
                    fi +=1
            else:
                file = file_split[1]
            for name in list_character:
                if name in file:
                    m = file.find(name)+len(name)
                    if file.find(name) < file.find("-"):
                        if file[m] == " ":
                            check = True
                        else:
                            check = False
                    else:
                        try:
                            last = file[m]
                            check = False
                        except:
                            check = True

                    if check:

                        # match_result = file.split("-")
                        print(file)
                        match_result = file.split("-")
                        print(match_result)
                        match_result = re.split(r"(?<=\d)-(?=\d)", file)
                        print(match_result)
                        if int(match_result[0][len(match_result[0])-1]) > int(match_result[1][0]):                        
                            
                            if name in match_result[0]:
                                name_data[name]['g1'] = name_data[name]['g1']+int(match_result[0][len(match_result[0])-1])
                                name_data[name]['g2'] = name_data[name]['g2']+int(match_result[1][0])
                                name_data[name]['point'] = name_data[name]['point']+3
                                name_data[name]['W'] = name_data[name]['W']+1
                            else:
                                name_data[name]['g1'] = name_data[name]['g1']+int(match_result[1][0])
                                name_data[name]['g2'] = name_data[name]['g2']+int(match_result[0][len(match_result[0])-1])
                                name_data[name]['L'] = name_data[name]['L']+1
                                
                                                            
                        elif int(match_result[0][len(match_result[0])-1]) == int(match_result[1][0]):
                            name_data[name]['g1'] = name_data[name]['g1']+int(match_result[0][len(match_result[0])-1])
                            name_data[name]['g2'] = name_data[name]['g2']+int(match_result[1][0])
                            name_data[name]['point'] = name_data[name]['point']+1
                            name_data[name]['T'] = name_data[name]['T']+1

                        elif int(match_result[0][len(match_result[0])-1]) < int(match_result[1][0]):
                            if name in match_result[1]:
                                name_data[name]['point'] = name_data[name]['point']+3
                                name_data[name]['W'] = name_data[name]['W']+1
                                name_data[name]['g1'] = name_data[name]['g1']+int(match_result[1][0])
                                name_data[name]['g2'] = name_data[name]['g2']+int(match_result[0][len(match_result[0])-1])
                            else:
                                name_data[name]['g1'] = name_data[name]['g1']+int(match_result[0][len(match_result[0])-1])
                                name_data[name]['g2'] = name_data[name]['g2']+int(match_result[1][0])
                                name_data[name]['L'] = name_data[name]['L']+1
                            
                        
        i = i+1

    data_list = []
    new_datalist = []
    for data in name_data.keys():
        if len(data_list) == 0:
            data_list.append(data)
        else:
            current_point = name_data[data]['point']
            i = 0
            for d in data_list:
                list_point = name_data[d]['point']
                if current_point > list_point:
                    print("higher")
                    j = 0
                    for d2 in data_list:
                        if j == i:
                            new_datalist.append(data)
                        new_datalist.append(d2)
                        j = j+1
                    break;    

                elif current_point == list_point:
                    current_gd = name_data[data]['g1']-name_data[data]['g2']
                    list_gd = name_data[d]['g1']-name_data[d]['g2']
                    if current_gd > list_gd:
                        j = 0
                        for d2 in data_list:
                            if j == i:
                                new_datalist.append(data)
                            new_datalist.append(d2)
                            j = j+1
                        break;
                    elif current_gd == list_gd:
                        if name_data[data]['g1'] > name_data[d]['g1']:
                            j = 0
                            for d2 in data_list:
                                if j == i:
                                    new_datalist.append(data)
                                new_datalist.append(d2)
                                j = j+1
                            break;
                        else:
                            if i == len(data_list)-1:
                                new_datalist = data_list
                                new_datalist.append(data)
                                break;
                            
                    else:
                        if i == len(data_list)-1:
                            new_datalist = data_list
                            new_datalist.append(data)
                            break;
                            

                elif current_point < list_point:
                    if i == len(data_list)-1:
                        new_datalist = data_list
                        new_datalist.append(data)
                        break;
                
                                    
                i = i+1
                
            data_list = new_datalist
            new_datalist = []
            
            
    path = r'D:\H\Division 1'
    dirs = os.listdir( path )
    c = 1
    for name in data_list:
        for file in dirs:
            if name in file:
                m = file.find(name)+len(name)
                try:
                    print(file)
                    print(file[m])
                    if file[m] == " ":
                        check = True
                    else:
                        check = False
                except:
                    check = True

                if check:
                    sc = name_data[name]['g1'] - name_data[name]['g2']
                    if sc > 0:
                        sc = '+'+str(sc)

                    elif sc < 0:
                        sc = '-'+str(abs(sc))
                    else:
                        sc = str(sc)

                    stat = "[{}W-{}T-{}L]".format(name_data[name]['W'],name_data[name]['T'],name_data[name]['L'])

                    title = str(c)+". "+name+" ["+str(name_data[name]['point'])+"pt] ["+str(name_data[name]['g1'])+"-"+str(name_data[name]['g2'])+"="+sc+"] "+stat
                    print(path+"\\"+file, path+"\\"+title)
                    os.rename(path+"\\"+file, path+"\\"+title)
        c = c+1

    return name_data
                            
                      
def world_cal():
    champ_fa_rew = 10
    champ_league_cup_rew = 5
    champ_uefa_rew = 30
    champ_uefa_cup_rew = 15
    stat_high_score_rew = 20
    stat_less_concede_rew = 20
    stat_high_dif_rew = 20
    rank = {
        1:266,
        2:64,
        3:62,
        4:60,
        5:58,
        6:56,
        7:54,
        8:52,
        9:36,
        10:34,
        11:32,
        12:30,
        13:28,
        14:26,
        15:24,
        16:22,
        17:14,
        18:13,
        19:12,
        20:11,
        21:10,
        22:9,
        23:8,
        24:7,
        25:6,
        26:5,
        27:4,
        28:3,
        29:2,
        30:1        
    }

    path = r'D:\H\World Rank'
    dirs = os.listdir( path )
    for file in dirs:
        os.remove(path+"\\"+file)

    index = {}
    path = r'D:\H\World Index'
    dirs = os.listdir( path )
    for file in dirs:
        if file == "Thumbs.db":
            continue
        index[file.replace(".jpg","")] = 0

    path = r'D:\H\History'
    dirs = os.listdir( path )
    for season in dirs:
        print(season)
        if season == "Thumbs.db":
            continue
        path_season_champ_fa = path + "\\"+season + "\\" + "[Champion] FA Cup"
        path_season_champ_league_cup = path + "\\"+season + "\\" + "[Champion] League Cup"
        path_season_champ_uefa = path + "\\"+season + "\\" + "[Champion] Uefa Champions League"
        path_season_champ_uefa_cup = path + "\\"+season + "\\" + "[Champion] Uefa Cup"
        path_season_stat_high_score = path + "\\"+season + "\\" + "[Stat] Highest Difference"
        path_season_stat_less_concede = path + "\\"+season + "\\" + "[Stat] Less Concede"
        path_season_stat_high_dif = path + "\\"+season + "\\" + "[Stat] Most Score"
        path_season_league = path + "\\"+season + "\\" + "[Champion] League"

        # a = os.listdir( path_season_champ_fa )

        a = [fi for fi in os.listdir(path_season_champ_fa) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # a.remove("folder.jpg")
        index[a[0].replace(".jpg","")] += champ_fa_rew

        # b = os.listdir( path_season_champ_league_cup )
        b = [fi for fi in os.listdir(path_season_champ_league_cup) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # b.remove("folder.jpg")
        index[b[0].replace(".jpg","")] += champ_league_cup_rew

        # c = os.listdir( path_season_champ_uefa )
        c = [fi for fi in os.listdir(path_season_champ_uefa) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # c.remove("folder.jpg")
        index[c[0].replace(".jpg","")] += champ_uefa_rew

        # d = os.listdir( path_season_champ_uefa_cup )
        d = [fi for fi in os.listdir(path_season_champ_uefa_cup) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # d.remove("folder.jpg")
        index[d[0].replace(".jpg","")] += champ_uefa_cup_rew

        # e = os.listdir( path_season_stat_high_score )
        e = [fi for fi in os.listdir(path_season_stat_high_score) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # e.remove("folder.jpg")
        index[e[0].replace(".jpg","")] += stat_high_score_rew

        # f = os.listdir( path_season_stat_less_concede )
        f = [fi for fi in os.listdir(path_season_stat_less_concede) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # f.remove("folder.jpg")
        index[f[0].replace(".jpg","")] += stat_less_concede_rew

        # g = os.listdir( path_season_stat_high_dif )
        g = [fi for fi in os.listdir(path_season_stat_high_dif) if fi.endswith(".jpg") and fi != "folder.jpg"]
        # g.remove("folder.jpg")
        index[g[0].replace(".jpg","")] += stat_high_dif_rew

        league_dirs = [
            d for d in os.listdir(path_season_league)
            if os.path.isdir(os.path.join(path_season_league, d))
        ]
        for ranking in league_dirs:
            if ranking == "Thumbs.db" or ranking == "folder.jpg" or ranking == "folder.jpg":
                continue
            rank_season =int(ranking.split("[")[0].split(".")[0])
            if len(ranking.split("[")[0].split(".")) > 2:
                name = ranking.split("[")[0].split(".")[1]+"."+ranking.split("[")[0].split(".")[2]
                name = name.strip()
            else:
                name = ranking.split("[")[0].split(".")[1].strip()
            index[name] += rank[rank_season]

    list_str = []
    for k in index:
        if not list_str:
            list_str.append({"name":k,"value":index[k]})
        else:
            flag = False
            for i in list_str:
                print(i)
                if i['value'] > index[k]:
                    continue
                else:
                    list_str.insert(list_str.index(i), {"name":k,"value":index[k]})
                    flag = True
                    break
            if not flag:
                list_str.append({"name":k,"value":index[k]})

    print(list_str)

    # list_str.sort(reverse=True)
    c=1
    for k in list_str:
        shutil.copytree('D:\\H\\World Index\\{}'.format(k['name']), 'D:\\H\\World Rank\\{}. {} [{}]'.format(c,k['name'],k['value']))
        c +=1

world_cal()



                
        
