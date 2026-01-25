# ---------------------- libraries ---------------------
import json
import time
import sys
import sqlite3
import logging
import threading
import string
import os
import pickle
import math
# ----------------- External libraries ----------------
from datetime import date
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# ---------------------- Globals ----------------------
app = Flask(__name__)
IDs_in_DB = []
current_IDs = []
PWD = os.getcwd()
BlackList = []
with open(os.path.join(PWD, 'sentiment_model.pkl'), 'rb') as f:
    model = pickle.load(f)

# ---------------------- Load Config ------------------
try:
    with open(os.path.join(PWD, 'config.json'), mode='r', encoding="utf-8") as f:
        app_config = json.load(f)
    LOG_LEVEL = str(app_config["LOG_LEVEL"]).upper()
    WEB_IP = str(app_config["WEB_IP"])
    WEB_PORT = int(app_config["WEB_PORT"])
    for item in app_config["BlackList"]:
        BlackList.append(item)

except Exception as e:
    logging.error(f'Failed to load config: {e}')
    sys.exit(1)

# ---------------------- Setup Logging ----------------------
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f"server.log"),
        logging.StreamHandler()
    ]
)

# ---------------------- Backend ----------------------
def load_userID():
    global IDs_in_DB
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_data")
        for userId in cursor.fetchall():
            IDs_in_DB.append(int(userId[0]))

def predict_sentiment(text):
    global model
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(token) for token in tokens]
    return model.classify({token: True for token in tokens})

def Write_DB():
    global current_IDs
    conn = sqlite3.connect('database.db')
    try:
        current_IDs = list(set(current_IDs))
        logging.info("Running Write_DB()")
        for userId in current_IDs:
            BlackList_Count = 0
            evaluation = ""
            Profile_image = ""
            audited = False
            URL = f"https://users.roblox.com/v1/users/{userId}"
            response = requests.get(URL)
            if response.status_code == 200:
                data = response.json()
                user_id = data["id"]
                ban_stat = data["isBanned"]
                user_name = data.get("name")
                displayName = data.get("displayName")
                description = data.get("description")
                description = description.replace("\n"," ")
                sentiment = predict_sentiment(description)
                for item in BlackList:
                    if item in description:
                        BlackList_Count += 1
                if (BlackList_Count > 1) and (sentiment == "Suspicious"):
                    evaluation = f"Auto SUS"
                    audited = True
                conn.execute(
                    'INSERT INTO user_data (id, is_banned, name, displayName, user_description, sentimentAI, audited, evaluation, Profile_image, Blacklist_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (user_id, ban_stat, user_name, displayName, description, sentiment, audited, evaluation, Profile_image, BlackList_Count)
                )
                conn.commit()
            elif response.status_code == 429:
                logging.info("too many requests. Waiting 60 seconds...")
                time.sleep(60)
            else:
                logging.error(f"http error {response.status_code}")
            time.sleep(0.1)
        logging.info(f"Done Writing to DB.")
        conn.close()
        logging.info("Reloading load_userID()")
        load_userID()
    except Exception as e:
        logging.error(f'error updating DB: {e}')
    current_IDs = []
    return

def get_images_from_API():
    logging.debug('[API Get Images] running')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id,  name
        FROM user_data 
        WHERE is_banned = ? AND Profile_image = '' ORDER BY id
        """, (False,)
    )
    for userId in cursor.fetchall():
        userId = int(userId[0])
        url = (f"https://thumbnails.roblox.com/v1/users/avatar?userIds={userId}&size=100x100&format=Png&isCircular=false")
        response = requests.get(url)
        image_url = ""
        if response.status_code == 200:
            temp_img_json = response.json()
            image_url = temp_img_json['data'][0]['imageUrl']
            sleep_time = 1
        elif response.status_code == 429:
            logging.error(f'[API Get Images] Too Many Requests')
            logging.info('[API Get Images] sleeping for 60 seconds')
            sleep_time = 60
        else:
            logging.error(f'[API Get Images] error code: {response.status_code}')
            sleep_time = 0.01
        conn.execute('UPDATE user_data SET Profile_image = ? WHERE id = ?', (image_url, userId))
        conn.commit()
        time.sleep(sleep_time)
    conn.close()
    logging.debug('[API Get Images] Finshed!')
    return

def fix_404_images():
    logging.debug('[fix_404_images] running')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id,  Profile_image
        FROM user_data 
        WHERE is_banned = ? ORDER BY id
        """, (False,)
    )
    for row in cursor.fetchall():
        user_id = row[0]
        Profile_image_url = row[1]
        api_url = (f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=100x100&format=Png&isCircular=false")
        response = requests.get(Profile_image_url)
        if response.status_code == 404:
            new_response = requests.get(api_url)
            if new_response.status_code == 200:
                temp_img_json = response.json()
                image_url = temp_img_json['data'][0]['imageUrl']
                time.sleep(1)
                conn.execute('UPDATE user_data SET Profile_image = ? WHERE id = ?', (image_url, user_id))
        else:
            continue
    conn.close()
    logging.debug('[fix_404_images] Finshed!')
    return

@app.route('/Friend-Finder', methods=['POST'])
def Friend_Finder():
    global IDs_in_DB
    global current_IDs
    current_IDs = list(set(current_IDs))
    data = request.json
    userId = data.get('user_id')
    friends_URL = f"https://friends.roblox.com/v1/users/{userId}/friends"
    response = requests.get(friends_URL)
    if response.status_code == 200:
        friends_data = response.json()
        for member_data in friends_data['data']:
            if int(member_data["id"]) not in IDs_in_DB:
                current_IDs.append(member_data["id"])
    elif response.status_code == 429:
        print("too many requests")
    else:
        print(f"http error: {response.status_code} for {friends_URL}")
    current_IDs = list(set(current_IDs))
    return jsonify(201)

@app.route('/Group-Finder', methods=['POST'])
def Group_Finder():
    global IDs_in_DB
    global current_IDs
    current_IDs = list(set(current_IDs))
    data = request.json
    groupId = data.get('GroupID')
    next_page_cursor = ""
    while next_page_cursor is not None:
        URL = f"https://groups.roblox.com/v1/groups/{groupId}/users?sortOrder=Asc&limit=100&Cursor={next_page_cursor}"
        response = requests.get(URL)
        groups_data = response.json()
        for member_data in groups_data['data']:
            if member_data['user']['userId'] not in IDs_in_DB:
                current_IDs.append(member_data['user']['userId'])
        next_page_cursor = groups_data['nextPageCursor']
    current_IDs = list(set(current_IDs))
    return jsonify(201)

@app.route('/update-DB', methods=['POST'])
def update_db():
    Write_DB()
    return jsonify(200)

@app.route('/User-audit', methods=['POST'])
def User_audit():
    data = request.json
    logging.debug(f'Json recevied from /User-audit: {data}')
    userID = data['UserID']
    value = data['value']
    with sqlite3.connect('database.db') as conn:
        conn.execute('UPDATE user_data SET audited = ? WHERE id = ?', (True, userID))
        conn.execute('UPDATE user_data SET evaluation = ? WHERE id = ?', (value, userID))
        conn.commit()
    return jsonify(200)

@app.route('/update-config', methods=['POST'])
def update_config():
    try:
        data = request.json
        """
        new_config = {
            "WEB_IP": (data.get('WEB_IP') or WEB_IP),
            "WEB_PORT": (data.get('WEB_PORT') or WEB_PORT),
            "LOG_LEVEL": (data.get('LOG_LEVEL') or LOG_LEVEL),
            "BlackList": (data.get('BlackList') or BlackList)
        }
        """
        logging.info(data)

        http_code = 201
    except Exception as e:
        logging.error(f'ERROR! {e}')
        http_code = 500
    return jsonify(http_code)

@app.route('/get-images', methods=['POST'])
def get_images():
    #threading.Thread(target=get_images_from_API, args=(), daemon=True).start()
    get_images_from_API()
    return jsonify(200)

# ---------------------- WEB ----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/About')
def about():
    return render_template('about.html')

@app.route('/admin')
def admin():
    global app_config
    return render_template('admin.html', config=app_config)

@app.route('/analysis')
def analysis():
    users = []
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_description, sentimentAI FROM user_data WHERE user_description IS NOT ''")
        for row in cursor.fetchall():
            temp_json = {
                "USER_ID": row[0],
                "user_description": str(row[1]),
                "Sentiment": str(row[2])
            }
            users.append(temp_json)
    return render_template('analysis.html', users=users)

@app.route('/audited')
def audited():
    users = []
    page = request.args.get('page', 1, type=int)
    ROWS_PER_PAGE = 25
    if page < 1:
        page = 1
    offset = (page - 1) * ROWS_PER_PAGE
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id FROM user_data WHERE is_banned = ? AND audited = ?""", (False,True,)
        )
        total_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT id,  name, displayName, user_description, evaluation, Profile_image
            FROM user_data 
            WHERE is_banned = ? AND audited = ? ORDER BY id LIMIT ? OFFSET ?
            """, (False,True,ROWS_PER_PAGE,offset)
        )
        for row in cursor.fetchall():
            user_id = int(row[0])
            user_name = str(row[1])
            display_name = str(row[2])
            user_description = str(row[3])
            evaluation = str(row[4])
            image_url = str(row[5])
            temp_json = {
                "USER_ID": user_id,
                "user_description": user_description,
                "user_name": user_name,
                "display_name": display_name,
                "evaluation": evaluation,
                "Link": f'https://www.roblox.com/users/{user_id}/profile/',
                "image_url": image_url
            }
            users.append(temp_json)
    total_pages = math.ceil(len(total_rows) / ROWS_PER_PAGE)
    return render_template(
        'audited.html', 
        users=users,
        page=page,
        total_pages=total_pages
    )

@app.route('/dev')
def dev():
    return render_template('dev.html')

@app.route('/dev-payload', methods=['POST'])
def dev_payload():
    data = request.json
    opt = data["opt"]
    payload = data["payload"]
    if opt == "DB":
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(payload)
                result = cursor.fetchall()
                http_code = 200
        except Exception as e:
            result = str(e)
            logging.error(f'dev-payload ERROR! {e}')
            http_code = 500
        return jsonify(http_code, result)

@app.route('/review')
def review():
    users = []
    page = request.args.get('page', 1, type=int)
    ROWS_PER_PAGE = 25
    if page < 1:
        page = 1
    offset = (page - 1) * ROWS_PER_PAGE
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            """ SELECT id FROM user_data WHERE is_banned = ? AND audited = ?""", (False,False,)
        )
        total_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT id,  name, displayName, user_description, Profile_image, sentimentAI
            FROM user_data 
            WHERE is_banned = ? AND audited = ? ORDER BY id LIMIT ? OFFSET ?
            """, (False,False,ROWS_PER_PAGE,offset)
        )
        for row in cursor.fetchall():
            user_id = int(row[0])
            user_name = str(row[1])
            display_name = str(row[2])
            user_description = str(row[3])
            image_url = str(row[4])
            Sentiment = str(row[5])
            temp_json = {   
                "USER_ID": user_id,
                "user_description": user_description,
                "user_name": user_name,
                "display_name": display_name,
                "Sentiment": Sentiment,
                "Link": f'https://www.roblox.com/users/{user_id}/profile/',
                "image_url": image_url
            }
            users.append(temp_json)
    total_pages = math.ceil(len(total_rows) / ROWS_PER_PAGE)
    return render_template(
        'review.html', 
        users=users,
        page=page,
        total_pages=total_pages
    )

@app.route('/stats')
def stats():
    users = []
    page = request.args.get('page', 1, type=int)
    ROWS_PER_PAGE = 25
    if page < 1:
        page = 1
    offset = (page - 1) * ROWS_PER_PAGE

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_data")
        total_rows = len(cursor.fetchall())
        cursor.execute(
            """
            SELECT *
            FROM user_data 
            ORDER BY id LIMIT ? OFFSET ?
            """, (ROWS_PER_PAGE,offset)
        )
        users = cursor.fetchall()
        cursor.execute("SELECT id FROM user_data WHERE is_banned = ?", (True,))
        baned = len(cursor.fetchall())
        cursor.execute("SELECT id FROM user_data WHERE audited = ?", (True,))
        audited_users = cursor.fetchall()
    stats = {
        "total_users": len(users),
        "users_banned": baned,
        "users_audited": len(audited_users) 
    }
    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    return render_template('stats.html', stats=stats, users=users, page=page, total_pages=total_pages)

def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute(
            'CREATE TABLE IF NOT EXISTS user_data (id INTEGER PRIMARY KEY, is_banned BOOL, name TEXT, displayName TEXT, user_description TEXT, sentimentAI TEXT, audited BOOL, evaluation TEXT NULL, Profile_image TEXT NULL, Blacklist_count INT NULL)'
        )
        conn.commit()
    return

def main():
    init_db()
    load_userID()
    time.sleep(0.1)
    app.run(debug=False, host=WEB_IP, port=WEB_PORT)

if __name__ == '__main__':
    main()
