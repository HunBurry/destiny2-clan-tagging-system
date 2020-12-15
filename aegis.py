import pydest
import asyncio
import time
import pymongo
import json
import datetime
import warnings
import http.cookies
http.cookies._is_legal_key = lambda _: True

async def main():
    #FUNCTION IP
    warnings.filterwarnings("ignore")
    destiny = pydest.Pydest('<key>');
    client = pymongo.MongoClient("mongodb+srv://<username>:<password>@<cluster>/<dbname>?retryWrites=true&w=majority")
    db = client['tagging-system']
    activityCollection = db['activites'];
    userCollection = db['users'];
    mode_values = {
        4: 10
    }
    
    for profileUsername in userCollection.find({}):
        print("Entering New User: " + profileUsername['username'])

        player = await destiny.api.search_destiny_player(1, profileUsername['username']);
        membershipID = player['Response'][0]['membershipId']
        profile = await destiny.api.get_profile(1, membershipID, [200])
        characters = profile['Response']['characters']['data'].keys()

        for character in characters:
            print("Entering new character...")
            for pageNum in range(4):
                activities = await destiny.api.get_activity_history(1, membershipID, character, count=250, mode=None, page=pageNum);
                #print(activities)
                if 'activities' in activities['Response'].keys():
                    activities = activities['Response']['activities'];
                    for activity in activities:
                        activityID = activity['activityDetails']['instanceId'];
                        post_carnage = await destiny.api.get_post_game_carnage_report(activityID);

                        mode = post_carnage['Response']['activityDetails']['mode'];
                        dateOfCompletion = datetime.datetime.strptime(post_carnage['Response']['period'], '%Y-%m-%dT%H:%M:%SZ')
                        yesterday = datetime.date.today() - datetime.timedelta(days=1);
                        #print(dateOfCompletion);
                        #print(yesterday)

                        if yesterday == dateOfCompletion.date():
                            #print("True")
                            search = activityCollection.find_one({'activityID': activityID});
                            #check if the acitivty was completed or not
                            if search is None:
                                players = [player['player']['destinyUserInfo']['displayName'] for player in post_carnage['Response']['entries']]
                                activityDocument = {
                                    'activityID': activityID,
                                    'players': players,
                                    'type': mode
                                };
                                activityCollection.insert_one(activityDocument)
                                print("Inserted activity...")
                                for num in range(len(players)):
                                    search = userCollection.find_one({'username': players[num]});
                                    if search is not None:
                                        tags = search['tags'];
                                        points = search['points']
                                        tabs = search['tabs'];
                                        for player in players[num:len(players)]:
                                            search2 = userCollection.find_one({'username': player});
                                            if search2 is not None:
                                                tags2 = search2['tags']
                                                tabs2 = search2['tabs']
                                                points2 = search2['points']
                                                if player not in tabs:
                                                    tabs.append(player);
                                                if players[num] not in tabs2:
                                                    tabs2.append(players[num])
                                                if player not in tags.keys():
                                                    tags[player] = [mode];
                                                else:
                                                    if mode not in tags[player]:
                                                        tags[player].append(mode);
                                                if players[num] not in tags2.keys():
                                                    tags[players[num]] = [mode];
                                                else:
                                                    if mode not in tags[players[num]]:
                                                        tags[players[num]].append(mode);
                                                points = points + 10 #mode_values[mode];
                                                points2 = points2 + 10 #mode_values[mode];
                                                userCollection.update_one({'username': player}, {'$set': {'username': player, 'points': points2, 'tabs': tabs2, 'tags': tags2}});
                                                userCollection.update_one({'username': players[num]}, {'$set': {'username': players[num], 'points': points, 'tabs': tabs, 'tags': tags}});
                            else:
                                print("Breaking, activity located...")
                                break;
                        else:
                            print("Breaking, not yesterday...")
                            break; 
                
    await destiny.close()
    time.sleep(1)

if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main());
    print("--- %s seconds ---" % (time.time() - start_time))

#################################################################### Useful Links ##############################################################################

#https://bungie-net.github.io/multi/schema_Destiny-DestinyComponentType.html#schema_Destiny-DestinyComponentType