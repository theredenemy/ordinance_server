from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template
from flask import redirect
from flask import send_file
from flask import abort
from flask_apscheduler import APScheduler
from flask import session
from werkzeug.middleware.proxy_fix import ProxyFix
from auth import auth_required, init_auth_db, edit_user, gen_ord_key, add_ord_key, get_db
import auth as au
import os
import threading
from makeConfig import makeConfig
from makeConfig import makeClientConfig
import configHelper
import time
import client
import socket
import sqlite3
import re
import time
import requests
import json
from collections import Counter
config_file = "ORDINANCE.ini"
motd_file = "motd.txt"
ip_bans_file = "ipbans.txt"
client_config_file = "Client.ini"
chat_db = "chat.db"
auth_db = "auth.db"
log_post_requests =  configHelper.read_config(config_file, "ORDINANCE", "log_post_requests", is_bool=True, default_value=False)
log_chat = configHelper.read_config(config_file, "ORDINANCE", "log_chat", is_bool=True, default_value=False)
block_vpn = configHelper.read_config(config_file, "ORDINANCE", "block_vpn", is_bool=True, default_value=False)
ip_list = []
temp_ban_list = []
inputs = []
players = {}
app = Flask(__name__)
scheduler = APScheduler()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1)
if os.path.isfile(client_config_file) == False:
    makeClientConfig()
if os.path.isfile(config_file) == False:
    makeConfig()
def init_chat_db(db):
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS chat (
                        message PRIMARY KEY,
                        cmd TEXT
                     )
                     """)
        
        cursor = conn.cursor()
        cursor.execute('SELECT EXISTS (SELECT 1 FROM chat LIMIT 1)')
        not_empty = cursor.fetchone()[0]

        if not not_empty:
            conn.execute("""INSERT OR IGNORE INTO chat (message, cmd)
                     VALUES ('hello', 'bot_say HELLO {player} {rgb}EFEFEFBREAK')
                     """)
def ban(ip):
    with open(ip_bans_file, 'w', encoding="utf-8", errors='ignore') as f:
        f.write(f"{ip}\n")
        f.close()
    return
def console():
    while True:
        try:
            global players
            cmd = input()
            if cmd == "edit_user".lower():
                print("ENTER USERNAME\n")
                user = input()
                print("ENTER PASSWORD\n")
                password = input()
                edit_user(user, password)
            if cmd == "del_user".lower():
                print("ENTER USERNAME\n")
                user = input()
                if user:
                    print(f"This will delete the user {user} Are you sure you want to do this? (y/n)\n")
                    are_you_sure = input()
                    if are_you_sure == "y".lower():
                        with sqlite3.connect(auth_db) as conn:
                            conn.execute("DELETE FROM users WHERE username = ?", (user,))
                        print(f"User {user} Has Been Deleted...")
            if cmd == "players".lower():
                for steamid, player in players.items():
                    print(steamid, player)
        except Exception as e:
            if type(e).__name__ == "KeyboardInterrupt" or type(e).__name__ == "EOFError":
                print("shutdown\n")
                break

            
init_chat_db(chat_db)
init_auth_db(auth_db)
@scheduler.task("cron", id='clear_ip_list', minute='*')
def clear_ip_list():
    global ip_list
    ip_list = []
@scheduler.task("cron", id='clear_temp_bans', minute='*/5')
def clear_temp_bans():
    global temp_ban_list
    if len(temp_ban_list) > 0:
        print("CLEARED TEMP BANS")
        temp_ban_list = []
scheduler.start()
@app.before_request
def check_ip():
    ip = request.remote_addr
    banlist = []
    db = get_db()
    use_token = False
    log_post_requests =  configHelper.read_config(config_file, "ORDINANCE", "log_post_requests", is_bool=True, default_value=False)
    block_vpn = configHelper.read_config(config_file, "ORDINANCE", "block_vpn", is_bool=True, default_value=False)
    ipinfo = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719")
    data = json.loads(ipinfo.text)
    vpn = bool(data.get("proxy"))
    if request.method == "POST" and log_post_requests:
        if request.is_json:
            post_data = request.get_json()
        else:
            post_data = request.form.to_dict()
        with open("post_data_logs.txt", 'a', encoding="utf-8", errors='ignore') as f:
            f.write(f"{request.remote_addr} : {post_data}\n")
            f.close()
    if os.path.isfile(ip_bans_file):
        file = open(ip_bans_file, 'r', encoding="utf-8", errors='ignore')
        for ip_ban in file.readlines():
            banlist.append(ip_ban.strip())
    key_header = request.headers.get('X-ORD-KEY')
    is_coffee = request.headers.get("X-COFFEE")
    if is_coffee:
        abort(418)
    if key_header:
        ord_key = db.execute('SELECT * FROM tokens WHERE token = ?', (key_header,)).fetchone()
        if ord_key:
            use_token = True
    if ip in banlist and not use_token or ip in temp_ban_list and not use_token or vpn and not use_token and block_vpn:
        print("IP IS BANNED")
        # this song is a banger
        # WAR WITHOUT REASON
        return redirect("https://www.youtube.com/watch?v=Elj4zDLqJvw")
@app.errorhandler(404)
def error_404(e):
    global ip_list
    # STOP TRYING BREAK
    ip = request.remote_addr
    ip_list.append(ip)
    counts = Counter(ip_list)
    if counts[ip] >= 10:
        temp_ban_list.append(ip)
        return "BYEBYE", 200
    return "404 Not Found", 404
@app.errorhandler(405)
def error_405(e):
    global ip_list
    # STOP TRYING BREAK
    ip = request.remote_addr
    ip_list.append(ip)
    counts = Counter(ip_list)
    if counts[ip] >= 10:
        temp_ban_list.append(ip)
        return "BYEBYE", 200
    return "JUST STOP BREAK", 405

@app.route("/")
def main_page():
    if not os.path.isfile(motd_file):
        with open(motd_file, 'w', encoding="utf-8", errors='ignore') as f:
            f.write("ORDINANCE")
            f.close()
    with open(motd_file, 'r', encoding="utf-8", errors='ignore') as f:
        motd = f.read()
        f.close()

    return f"<p>{motd}</p>"
@app.route("/teapot")
def teapot():
    abort(418)
@app.route("/favicon.ico")
def download_icon():
    if os.path.isfile("favicon.ico"):
        return send_file("favicon.ico")
    else:
        abort(404)
@app.route("/getdata", methods=['POST'])
@auth_required
def getdata():
    global players
    json_data = request.json
    player = str(json_data['player'])
    steamid = str(json_data['steamid'])
    print(f"{player}:{steamid} Has Been Put in Server")
    players[steamid] = player
    return jsonify({'message': "RENDER"}), 200

@app.route("/logout")
@auth_required
def logout():
    if au.use_token:
        return "FUCK YOU BREAK", 403
    return "LOGGED OUT", 401
@app.route("/admin")
@auth_required
def admin_panel():
    
    auth = request.authorization
    if au.use_token:
        return "FUCK YOU BREAK", 403
    if auth:
        if auth.username:
            username = auth.username
        else:
            username = "UNKNOWN"
    else:
        username = "UNKNOWN"
    return render_template("admin_panel.html", username=username)
@app.route("/admin/users", methods=['GET', 'POST'])
@auth_required
def users():
    if au.use_token:
        return "FUCK YOU BREAK", 403
    delete_button_trigger = request.args.get("delete")
    if delete_button_trigger:
        with sqlite3.connect(auth_db) as conn:
            conn.execute("DELETE FROM users WHERE username = ?", (delete_button_trigger,))
        return '<script>window.location.href="/admin/users";</script>'
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            edit_user(username, password)
            return '<script>window.location.href="/admin/users";</script>'
    with sqlite3.connect(auth_db) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        rows = cursor.fetchall()
    return render_template("users.html", users=rows)
@app.route("/admin/users/password", methods=['GET', 'POST'])
@auth_required
def change_password_ui():
    if au.use_token:
        return "FUCK YOU BREAK", 403
    username = request.args.get("user")
    if not username:
        return "NO USER", 403
    if request.method == "POST":
        password = request.form.get('password')
        edit_user(username, password)
        return "<script>window.history.go(-2);</script>"
    return render_template("change_password.html", username=username)
@app.route("/admin/tokens", methods=['GET', 'POST'])
@auth_required
def tokens_ui():
    if au.use_token:
        return "FUCK YOU BREAK", 403
    if au.check_users_if_empty():
        return "NO USERS ADDED PLEASE ADD A USER", 403
    delete_button_trigger = request.args.get("delete")
    if delete_button_trigger:
        with sqlite3.connect(auth_db) as conn:
            conn.execute("DELETE FROM tokens WHERE token = ?", (delete_button_trigger,))
        return '<script>window.location.href="/admin/tokens";</script>'
    if request.method == "POST":
        if request.form.get("ADD"):
            ord_key = gen_ord_key()
            add_ord_key(ord_key)
            return '<script>window.location.href="/admin/tokens";</script>'
        else:
            return "NO", 403
    with sqlite3.connect(auth_db) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM tokens")
        rows = cursor.fetchall()
    return render_template("tokens_ui.html", tokens=rows)
@app.route("/admin/set/inputs", methods=['GET', 'POST'])
@auth_required
def redirect_to_ordinance_ui():
    return redirect("/admin/ordinance_ui")
@app.route("/admin/ordinance_ui", methods=['GET', 'POST'])
@auth_required
def ordinance_ui():
    global inputs
    mode = configHelper.read_config(config_file, "ORDINANCE", "mode", default_value="game", is_int=False)
    state = configHelper.read_config(config_file, "ORDINANCE", "state")
    if au.use_token:
        return "FUCK YOU BREAK", 403
    if request.method == 'POST':
        if request.form.get("submit-btn"):
            inputs = request.form.get("inputs").upper().split()
            return '<script>window.location.href="/admin/ordinance_ui";</script>'
        elif request.form.get("submit-btn2"):
            configHelper.set_config(config_file, "ORDINANCE", "mode", request.form.get("mode"))
            return '<script>window.location.href="/admin/ordinance_ui";</script>'
        elif request.form.get("submit-btn3"):
            configHelper.set_config(config_file, "ORDINANCE", "state", request.form.get("state"))
            return '<script>window.location.href="/admin/ordinance_ui";</script>'
        else:
            return "BREAK"
        
    return render_template("ordinance_ui.html", inputs=' '.join(inputs), mode=mode, state=state)
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
    allow_mode_change = configHelper.read_config(config_file, "ORDINANCE", "allow_mode_change", is_bool=True, default_value=True)
    if allow_mode_change:
        mode = str(json_data['mode'])
        configHelper.set_config(config_file, "ORDINANCE", "mode", mode)
        return jsonify({'message': 'done'}), 200
    else:
        return jsonify({'message': 'nope'}), 403
@app.route("/ord/chat/admin", methods=['GET', 'POST'])
@auth_required
def admin_chat_ui():
    if au.use_token:
        return "FUCK YOU BREAK", 403
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
    global players
    json_data = request.json
    player = str(json_data['player'])
    steamid = str(json_data['steamid'])
    message = str(json_data['message']).lower()
    log_chat = configHelper.read_config(config_file, "ORDINANCE", "log_chat", is_bool=True, default_value=False)
    
    print(player, steamid, message)
    if log_chat:
        with open("chat_logs.txt", 'a', encoding="utf-8", errors='ignore') as f:
            ti_c = time.ctime(time.time())
            time_c = time.strptime(ti_c)
            f.write(f"{time.strftime("%Y-%m-%d-%H:%M:%S", time_c)} : {player} {steamid} >> {message}\n")
            f.close()
    cmd = ""
    valid = False
    #time.sleep(1)

    with sqlite3.connect(chat_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message, cmd FROM chat")
        rows = cursor.fetchall()
    for trigger, command in rows:
        if message == trigger:
            valid = True
            cmd = command
            break
        if re.sub(r'[^a-zA-Z0-9 ]', '', message) == trigger:
            valid = True
            cmd = command
            break
        if trigger in message.split():
            valid = True
            cmd = command
            break
    if valid:
        cmd = cmd.replace("{player}", player)
        if steamid in players.keys():
            cmd = cmd.replace("{o_name}", players[steamid])
        else:
            cmd = cmd.replace("{o_name}", "UNKNOWN")
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
    
    port = int(os.environ.get("SERVER_PORT", 5000))
    console_thread = threading.Thread(target=console, daemon=True)
    console_thread.start()
    app.run(host="0.0.0.0", port=port)

