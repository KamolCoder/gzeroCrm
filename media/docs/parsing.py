import json
import time
import requests
from database import create_table, insert_into, delete_row, get_team_name, dve_spiski_bet

create_table()

while True:
    url = 'https://1xbet82.com/LiveFeed/Get1x2_VZip?sports=1&count=50&lng=en&mode=4&country=192&getEmpty=true&noFilterBlockEvent=true'
    html = requests.get(url).json()
    with open('res.json', 'w') as f:
        f.write(json.dumps(html, indent=4))
    with open('res.json') as f:
        res = json.load(f)
        for game in res['Value']:
            team1, team2 = game.get('O1'), game.get('O2')  # ------ TEAM1 & TEAM2
            #     teams = f'{team1} - {team2}'
            liga = game['L']
            stavki = game['E']
            bets = []
            for i in stavki:
                if i["T"] == 1:
                    bets.append(i["C"])
                elif i["T"] == 2:
                    bets.append(i["C"])
                elif i["T"] == 3:
                    bets.append(i["C"])
                else:
                    pass
            if len(bets) > 2:
                    insert_into(liga, team1, team2, bets[0], bets[1], bets[2])
            else:
                insert_into(liga, team1, team2, 0, 0, 0)

        teams_for_kick = get_team_name(team1)
        if teams_for_kick != None:
            delete_row(teams_for_kick)
        else:
            print('delete row otmen')

        finish = dve_spiski_bet(team1)
        if finish != False and finish != None:
            print(f"🏆 {liga}\n\n{team1, team2} \n 🔻{finish[0]} - {finish[1]}\n ______________________")
        else:
            print('Net dannix')
    time.sleep(5)