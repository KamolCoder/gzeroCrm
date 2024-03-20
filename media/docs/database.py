import sqlite3


def connect():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    return db, cursor


def create_table():
    db, cursor = connect()
    cursor.execute('''CREATE TABLE IF NOT EXISTS games(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    liga TEXT,
    team1 TEXT,
    team2 TEXT,
    bet1 INTEGER,
    bet2 INTEGER,
    bet3 INTEGER)
    ''')


def insert_into(liga, team1, team2, bet1, bet2, bet3):
    db, cursor = connect()
    cursor.execute('''INSERT INTO games(liga,team1,team2,bet1,bet2,bet3) VALUES (?,?,?,?,?,?)''',
                   (liga, team1, team2, bet1, bet2, bet3))
    db.commit()
    db.close()


def get_team_name(team1):
    db, cursor = connect()
    res = ('''SELECT id,team1 FROM games WHERE team1= ?''')
    cursor.execute(res, [team1])
    i = cursor.fetchall()
    if len(i) > 2:
        return i[0][0]
    else:
        return None


def delete_row(id):
    db, cursor = connect()
    cursor.execute('''DELETE FROM games WHERE id = ?''', (id,))
    db.commit()
    db.close()


def dve_spiski_bet(team1):
    db, cursor = connect()
    res = ('''SELECT * FROM games WHERE team1 = ?''')
    cursor.execute(res, [team1])
    i = cursor.fetchall()
    if i != [] and len(i) > 1:
        bet1 = i[0][4]
        bet2 = i[0][5]
        bet3 = i[0][6]
        bet11 = i[1][4]
        bet12 = i[1][5]
        bet13 = i[1][6]
        if bet1 - bet11 > 0.50:
            return bet1, bet11
        elif bet2 - bet12 > 0.50:
            return bet2, bet12
        elif bet3 - bet13 > 0.50:
            return bet3, bet13
        else:
            return False
