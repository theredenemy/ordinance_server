from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template
from flask import session
from auth import auth_required, init_auth_db, edit_user
import os
from makeConfig import makeConfig
from makeConfig import makeClientConfig
import configHelper
import time
import client
import socket
import sqlite3
config_file = "ORDINANCE.ini"
client_config_file = "Client.ini"
chat_db = "chat.db"
auth_db = "auth.db"
inputs = []
app = Flask(__name__)
if os.path.isfile(client_config_file) == False:
    makeClientConfig()
if os.path.isfile(config_file) == False:
    makeConfig()
def init_chat_db(db):
    if os.path.isfile(db):
        return
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS chat (
                        message PRIMARY KEY,
                        cmd TEXT
                     )
                     """)
        conn.execute("""INSERT OR IGNORE INTO chat (message, cmd)
                     VALUES ('hello', 'bot_say HELLO {player} {rgb}EFEFEFBREAK')
                     """)

@app.route("/")
def main_page():
    return "<p>ORDINANCE</p>"
@app.route("/logout")
@auth_required
def logout():
    return '''<audio controls>
            <source src="data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU5LjI3LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAEluZm8AAAAPAAAABwAAA6sAVVVVVVVVVVVVVVVVVVVxcXFxcXFxcXFxcXFxcY6Ojo6Ojo6Ojo6Ojo6Oqqqqqqqqqqqqqqqqqqqqx8fHx8fHx8fHx8fHx8fj4+Pj4+Pj4+Pj4+Pj4///////////////////AAAAAExhdmM1OS4zNwAAAAAAAAAAAAAAACQELQAAAAAAAAOrELM1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/jIMQAE8KWxxVBKABgZYgKMiCiIQfxgXGP/x/IQjH87+hCEIUPgAAAEJOc5yEbznI385znO///+Q5/+c53//Od//53IQgcDgcFGOHA4Q4oMA+///8QAgo5//+TVVn///pJq/6SjYNN/+MixAwXPBLQAYFoAOmFQvUAsAjIwJcMUYwPw439fUl///HmZUvjCmv8Yx/q9ST0UTL/q/+vHcDKO1LV/pAVx8/v5iBQCT//dFQ1D63/zpg7ZkK6v/yNfJ4ylf/OIkBbbvqHUomHf//A/+MgxAsWVAriXchQApAsrtL+k3FTCMQk5ALyZjXVWU8ehTJRV6EQIZx23stX1nuyqinGnV/+v+kA8L047/2//////uFYKUlOv/nf///+n+rBw7//////coFEWepASSW2B1GFi3+pMA7/4yLEDBe0CtJdR2gCMVk3fRjHPVdJNF60lqTTF0oHtP47wmBf/bSmD6DosxytjiLG7/9qX/hWlOv/ZTf/o////UgHQLubrd/9v/1//2Uj/mZfBZDwQUr/////60wt555VWf////7r1gb/4yDECRWMEtABgWgAtemExtTC2Dkbw1N4cI9zdFP//9k3X4xDf+Ocw/TJU13/6v/r/ug3czAzid/+wFon//WMQLmZbf98xEQv/51CrJgnK//yyumRB53/9RjVQgAAggAU8/2X0qv1if/jIsQNF9N2oFGCaADoWlX+ZDiJoXkWX/gM4FKElJI+SP/6nWSRaJ6v//RYxJULcJ8UkTH//81pPMUB7GRs4nv///5YO01JIllGRssxHrzL////90SRKiW1VP7KMiWK1UxBTUUzLjEwMP/jIMQJAAADSAHAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV" type="audio/mpeg"></source>
          </audio><br>''', 401
@app.route("/admin")
@auth_required
def admin_panel():
    return render_template("admin_panel.html")
@app.route("/ord/info")
def show_info():
    player = configHelper.read_config(config_file, "ORDINANCE", "player", default_value="SERVICE", is_int=False)
    timestamp = configHelper.read_config(config_file, "ORDINANCE", "timestamp", default_value="1230681600", is_int=True)
    date = configHelper.read_config(config_file, "ORDINANCE", "date", default_value="DECEMBER 31TH 2008", is_int=False)
    trigger = configHelper.read_config(config_file, "ORDINANCE", "trigger", default_value="submit", is_int=False)
    team = configHelper.read_config(config_file, "ORDINANCE", "team", default_value="UNKNOWN", is_int=False)
    weapon = configHelper.read_config(config_file, "ORDINANCE", "weapon", default_value="UNKNOWN", is_int=False)
    playerclass = configHelper.read_config(config_file, "ORDINANCE", "playerclass", default_value="UNKNOWN", is_int=False)
    mode = configHelper.read_config(config_file, "ORDINANCE", "mode", default_value="game", is_int=False)
    state = configHelper.read_config(config_file, "ORDINANCE", "state")
    joined_inputs = ' '.join(inputs)
    return jsonify({"player" : player, "timestamp" : timestamp, "date" : date, "trigger" : trigger, "team" : team, "weapon" : weapon, "playerclass" : playerclass, "mode" : mode, "state" : state, "inputs" : joined_inputs}), 200
@app.route("/ord/mode", methods=['POST'])
@auth_required
def set_mode():
    json_data = request.json
    mode = str(json_data['mode'])
    configHelper.set_config(config_file, "ORDINANCE", "mode", mode)
    return jsonify({'message': 'done'}), 200
@app.route("/ord/chat/admin", methods=['GET', 'POST'])
@auth_required
def admin_chat_ui():
    delete_button_trigger = request.args.get("delete")
    if delete_button_trigger:
        with sqlite3.connect(chat_db) as conn:
            conn.execute("DELETE FROM chat WHERE message = ?", (delete_button_trigger,))
        return '<script>window.location.href="/ord/chat/admin";</script>'
    if request.method == "POST":
        message = request.form.get('message')
        cmd = request.form.get('cmd')
        if message and cmd:
            with sqlite3.connect(chat_db) as conn:
                conn.execute("INSERT OR REPLACE INTO chat (message, cmd) VALUES (?, ?)", (message.lower(), cmd))
            return '<script>window.location.href="/ord/chat/admin";</script>'
    with sqlite3.connect(chat_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message, cmd FROM chat")
        rows = cursor.fetchall()
    return render_template("chat_admin_ui.html", commands=rows)

@app.route("/ord/chat/send", methods=['POST'])
@auth_required
def chat_send():
    json_data = request.json
    player = str(json_data['player'])
    steamid = str(json_data['steamid'])
    message = str(json_data['message'])
    print(player, steamid, message)
    cmd = ""
    valid = False
    time.sleep(1)
    with sqlite3.connect(chat_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message, cmd FROM chat")
        rows = cursor.fetchall()
    for trigger, command in rows:
        if message == trigger:
            valid = True
            cmd = command
            break
        if trigger in message.split():
            valid = True
            cmd = command
    if valid:
        cmd = cmd.replace("{player}", player)
        cmd = cmd.replace("{steamid}", steamid)
        cmd = cmd.replace("{rgb}", "\x07")
        cmd = cmd.replace("{default}", "\x01")
        print(cmd)
        return jsonify({"valid" : True, "cmd" : cmd}), 200
    else:
        return jsonify({"valid" : False}), 200
@app.route("/ord/pawn/submit", methods=['POST'])
@auth_required
def pawn_submit():
    
    json_data = request.json
    
    player = json_data['player']
    timestamp = json_data['timestamp']
    date = json_data['date']
    trigger = json_data['trigger']
    team = json_data['team']
    weapon = json_data['weapon']
    playerclass = json_data['playerclass']
    

    print(player, timestamp, date, trigger, team, weapon, playerclass)
    configHelper.set_config(config_file, "ORDINANCE", "player", player)
    configHelper.set_config(config_file, "ORDINANCE", "timestamp", timestamp)
    configHelper.set_config(config_file, "ORDINANCE", "date", date)
    configHelper.set_config(config_file, "ORDINANCE", "trigger", trigger)
    configHelper.set_config(config_file, "ORDINANCE", "team", team)
    configHelper.set_config(config_file, "ORDINANCE", "weapon", weapon)
    configHelper.set_config(config_file, "ORDINANCE", "playerclass", playerclass)
    
    return jsonify({'message': 'done'}), 200
@app.route("/ord/pawn/state", methods=['POST'])
@auth_required
def set_pawn_state():
    json_data = request.json

    state = json_data['state']
    configHelper.set_config(config_file, "ORDINANCE", "state", state)
    return jsonify({'message': 'done'}), 200

@app.route("/ord/input", methods=['POST', 'GET'])
@auth_required
def ord_input():
    global inputs
    if request.method == 'GET':
        joined_inputs = ' '.join(inputs)
        return jsonify({'message': joined_inputs}), 200
    json_data = request.json

    input = str(json_data['input'].upper())
    pawn_name = str(json_data['pawn_name'])

    print(input, pawn_name)

    if input == "BEGIN":
        inputs = []
        print("BEGIN ORDINANCE")
        return jsonify({'message': 'BEGIN ORDINANCE'}), 200
    
    inputs.append(str(input))
    print(inputs)
    return jsonify({'message': inputs}), 200

@app.route("/ord/input/render",  methods=['GET'])
@auth_required
def ord_render():
    global inputs
    state = configHelper.read_config(config_file, "ORDINANCE", "state")
    ip = configHelper.read_config(client_config_file, "Client", "ip", default_value="127.0.0.1", is_int=False)
    port = configHelper.read_config(client_config_file, "Client", "port", default_value=4456, is_int=True)
    ren_inputs = []
    if state == "dead":
        inputs = []
        return jsonify({'message': "ORD_ERROR"}), 200
    if len(inputs) < 1:
        print("just RENDER")
        with open("inputs.txt", 'w', encoding='utf-8', errors='ignore') as f:
            f.write("RENDER")
            f.close
        inputs = []
        sendfile = client.SendFile("inputs.txt", ip, port)
        if not sendfile:
            return jsonify({'message': "NO_INPUT"}), 200
        return jsonify({'message': "RENDER"}), 200
    # Some RENDER CODE
    skip = False
    for i in range(len(inputs)):
        if skip:
            skip = False
            continue
        if i + 1 < len(inputs) and len(inputs[i]) <= 1 and len(inputs[i + 1]) <= 1:
            next = inputs[i + 1]
            ren_inputs.append(f"{inputs[i]}{next}")
            skip = True
        else:
            ren_inputs.append(inputs[i])
    print(ren_inputs)
    with open("inputs.txt", 'w', encoding='utf-8', errors='ignore') as f:
        f.write("\n".join(ren_inputs))
        f.close
    inputs = []
    sendfile = client.SendFile("inputs.txt", ip, port)
    if not sendfile:
        return jsonify({'message': "NO_INPUT"}), 200

    return jsonify({'message': "RENDER"}), 200
if __name__ == '__main__':
    init_chat_db(chat_db)
    init_auth_db(auth_db)
    
    app.run(host="0.0.0.0", port=5000)

