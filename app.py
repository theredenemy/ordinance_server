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
from werkzeug.utils import secure_filename
from auth import auth_required, init_auth_db, edit_user, gen_ord_key, add_ord_key, get_db
import auth as au
import os
import signal
import threading
from makeConfig import makeConfig
from makeConfig import makeClientConfig
import configHelper
import time
import client
import socket
import traceback
import sqlite3
import re
import time
import requests
import json
import paramiko
import UploadFiles
import pathlib
from urllib.parse import urlparse
from collections import Counter

import wave
import numpy as np
from PIL import Image
from srctools.vtf import VTF
import av
import vid2vtf
import shutil
import io
import qrcode
from pyzbar.pyzbar import decode


config_file = "ORDINANCE.ini"
motd_file = "motd.txt"
ip_bans_file = "ipbans.txt"
client_config_file = "Client.ini"
chat_db = "chat.db"
auth_db = "auth.db"
dont_render = False
data_dir = os.path.join(os.getcwd(), "data")
log_post_requests =  configHelper.read_config(config_file, "ORDINANCE", "log_post_requests", is_bool=True, default_value=False)
log_chat = configHelper.read_config(config_file, "ORDINANCE", "log_chat", is_bool=True, default_value=False)
allow_ord_play = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play", is_bool=True, default_value=True)
allow_ord_play_video_download = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play_video_download", is_bool=True, default_value=True)
allow_ord_play_img_playback = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play_img_playback", is_bool=True, default_value=True)
block_vpn = configHelper.read_config(config_file, "ORDINANCE", "block_vpn", is_bool=True, default_value=False)
host = configHelper.read_config(config_file, "sftp", "host", default_value="127.0.0.1")
sftp_port = configHelper.read_config(config_file, "sftp", "port", default_value=21, is_int=True)
user = configHelper.read_config(config_file, "sftp", "user", default_value="fsky")
ssh_keyfile = configHelper.read_config(config_file, "sftp", "key", default_value=os.path.join(os.getcwd(), "ssh_key", "id_rsa"))
ip_list = []
temp_ban_list = []
inputs = []
players = {}
UPLOAD_FOLDER = 'ord_play/render'
ALLOWED_EXTENSIONS = {'dat', 'vtf'}
ALLOWED_VIDEO_DATA_EXTENSIONS = {'mp4'}
app = Flask(__name__)
if not os.path.isdir(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
scheduler = APScheduler()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1)
if os.path.isfile(client_config_file) == False:
    makeClientConfig()
if os.path.isfile(config_file) == False:
    makeConfig()

def is_url(url):
    try:
        url_r = urlparse(url)
        return all([url_r.scheme in ['http', 'https'], url_r.netloc])
    except ValueError:
        return False

def check_data_name(data_str):
    try:
        spilt_data_str = str(data_str).split()
        if spilt_data_str[0] == "PULL_DATA":
            spilt_data_str.remove("PULL_DATA")
            merge_data_str = ' '.join(spilt_data_str)
            return merge_data_str
        else:
            return False
    except IndexError:
        return False

def download_file(url, filename):
    file_data = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(file_data.content)
    return filename

def gen_ssh_key():
    if not os.path.isdir(os.path.join(os.getcwd(), "ssh_key")):
        os.makedirs(os.path.join(os.getcwd(), "ssh_key"))
    
    rsa_key = paramiko.RSAKey.generate(bits=4096)

    rsa_key.write_private_key_file(os.path.join(os.getcwd(), "ssh_key", "id_rsa"))

    public_key = f"{rsa_key.get_name()} {rsa_key.get_base64()}"
    with open(os.path.join(os.getcwd(), "ssh_key", "id_rsa.pub"), 'w') as f:
        f.write(public_key)

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
            if cmd == "gen_ssh_key".lower():
                gen_ssh_key()
            if cmd == "exit".lower():
                print("shutdown\n")
                os._exit(0)
        except Exception as e:
            print(e)
            if type(e).__name__ == "KeyboardInterrupt" or type(e).__name__ == "EOFError":
                print("shutdown\n")
                break
def render_play():
    global dont_render
    global allow_ord_play_img_playback
    global allow_ord_play_video_download
    dont_render = True
    allow_ord_play_video_download = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play_video_download", is_bool=True, default_value=True)
    allow_ord_play_img_playback = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play_img_playback", is_bool=True, default_value=True)
    video_name = None
    file_list = os.listdir(UPLOAD_FOLDER)
    print(file_list)
    view_dir = os.path.join(os.getcwd() ,"view")
    if not os.path.isdir(view_dir):
        os.makedirs(view_dir)
    else:
        shutil.rmtree(view_dir)
        os.makedirs(view_dir)
    for file in file_list:
        try:
            
            img_to_wav = True
            path = os.path.join(UPLOAD_FOLDER, file)
            with open(path, 'rb') as f:
                vtf_img = VTF.read(f)
                vtf_img.load()
            vtf_frame = vtf_img.get(frame=0)
            img = vtf_frame.to_PIL()
            img_a = np.array(img)

            qrs = decode(img)


            
            
            text = None
            if qrs:
                text = qrs[0].data.decode('utf-8')
                
                if text:
                    print("this is a qrcode")
                    print(text)
                    data_name = check_data_name(text) 
                    if is_url(text) and allow_ord_play_video_download:
                        
                        parse_url = urlparse(text)

                        name, ext = os.path.splitext(parse_url.path)
                        basename = os.path.basename(name)
                        print(name, basename, ext)

                        if ext in ['.mp4']:
                            video_name = f"view{ext}"
                            video_name_download = f"view_download{ext}"
                            download_file(text, os.path.join(view_dir, video_name_download))
                            # ffmpeg command :)
                            os.system(f'ffmpeg -y -i {os.path.join(view_dir, video_name_download)} -vf "scale=256:128" -ar 11025 {os.path.join(view_dir, video_name)}')
                            if os.path.isfile(os.path.join(view_dir, video_name)):
                                print("got video")
                                img_to_wav = False
                            else:
                                img_to_wav = True
                            
                        else:
                            img_to_wav = True
                    elif data_name:
                        data_name_dir = os.path.join(data_dir, data_name)
                        data_config = os.path.join(data_name_dir, "data.ini")
                        if os.path.isdir(data_name_dir) and os.path.isfile(data_config):
                            video_data_name = configHelper.read_config(data_config, "data", "video_name")
                            video_data_path = os.path.join(data_name_dir, video_data_name)
                            if os.path.isfile(video_data_path):
                                ext = pathlib.Path(video_data_path).suffix
                                if ext in ['.mp4']:
                                    video_name = f"view{ext}"
                                    os.system(f'ffmpeg -y -i {video_data_path} -vf "scale=256:128" -ar 11025 {os.path.join(view_dir, video_name)}')
                                    img_to_wav = False
                                else:
                                    img_to_wav = True
                            else:
                                img_to_wav = True
                        else:
                            img_to_wav = True


                    else:
                        img_to_wav = True
            else:
                img_to_wav = True
                    

            if img_to_wav and allow_ord_play_img_playback:
                r = img_a[:, :, 0].astype(np.float32)
                g = img_a[:, :, 1].astype(np.float32)
                b = img_a[:, :, 2].astype(np.float32)

                c_channels = r + g + b
                normal_floats = ((c_channels / 768.0) - 0.5) * 2.0

                flat_samples = normal_floats.flatten()

                int16_samples = np.zeros_like(flat_samples, dtype=np.int16)

                negative_mask = flat_samples < 0
                int16_samples[negative_mask] = (flat_samples[negative_mask] * 32768.0).astype(np.int16)
                int16_samples[~negative_mask] = (flat_samples[~negative_mask] * 32767.0).astype(np.int16)
                        
                with wave.open(os.path.join(view_dir, "output.wav"), 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(16 // 8)
                    w.setframerate(22050)
                    w.writeframes(int16_samples.tobytes())
                video_name = "view.mp4"       
                video = av.open(os.path.join(view_dir, video_name), mode='w')
                audio_input = av.open(os.path.join(view_dir, "output.wav"))

                fps = 15        
                v_stream = video.add_stream("libx264", rate=30)
                v_stream.width = img.width
                v_stream.height = img.height
                v_stream.pix_fmt = 'yuv420p'
                in_a_stream = audio_input.streams.audio[0]
                a_stream = video.add_stream("aac", rate=in_a_stream.rate)
                a_stream.layout = 'mono'

                audio_duration = float(in_a_stream.duration * in_a_stream.time_base)
                frames_count = int(audio_duration * fps)

                video_frame = av.VideoFrame.from_image(img)

                for i in range(frames_count):
                    video_frame.pts = i
                    # video_frame.time_base = v_stream.time_base
                    for packet in v_stream.encode(video_frame):
                        video.mux(packet)
                
                for packet in v_stream.encode():
                    video.mux(packet)
                
                resampler = av.AudioResampler(format=a_stream.format, layout=a_stream.layout, rate=a_stream.rate)

                for frame in audio_input.decode(in_a_stream):
                    resampled_frames = resampler.resample(frame)
                    for resampled_frame in resampled_frames:
                        resampled_frame.pts = None
                        for packet in a_stream.encode(resampled_frame):
                            video.mux(packet)
                
                for packet in a_stream.encode():
                    video.mux(packet)
                audio_input.close()
                video.close()
            if not video_name:
                video_name = "view.mp4"
                shutil.copyfile(os.path.join(os.getcwd(), video_name), os.path.join(view_dir, video_name))
            os.remove(path)
            vid2vtf.video_to_vtf(video=os.path.join(view_dir, video_name), fps=15, width=256, height=128, output_filename="view", output_dir=view_dir)
            materials_dir = os.path.join(view_dir, "materials")
            sound_dir = os.path.join(view_dir, "sound")
            UploadFiles.upload_dir(materials_dir, "/tf/materials", host, sftp_port, user, ssh_keyfile)
            UploadFiles.upload_dir(sound_dir, "/tf/sound", host, sftp_port, user, ssh_keyfile)
            UploadFiles.upload_file(os.path.join(view_dir, video_name), "/tf/public", host, sftp_port, user, ssh_keyfile)
            dont_render = False
            break
        except Exception as e:
            traceback.print_exception(e)
            os.remove(path)
            
    dont_render = False
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_DATA_EXTENSIONS            
init_chat_db(chat_db)
init_auth_db(auth_db)
if not os.path.isdir(os.path.join(os.getcwd(), "ssh_key")):
    gen_ssh_key()
if not os.path.isdir(data_dir):
    os.makedirs(data_dir)
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
    try:
        ipinfo = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719")
        data = json.loads(ipinfo.text)
        vpn = bool(data.get("proxy"))
    except Exception as e:
        print(type(e))
        vpn = False
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
@app.route("/admin/video_data", methods=['GET', 'POST'])
@auth_required
def video_data_ui():
    if au.use_token:
        return "FUCK YOU BREAK", 403
    delete_button_trigger = request.args.get("delete")
    downloadqr = request.args.get("downloadqr")
    if delete_button_trigger:
        video_data_dir = os.path.join(data_dir, delete_button_trigger)
        if os.path.isdir(video_data_dir):
            shutil.rmtree(video_data_dir)
        return '<script>window.location.href="/admin/video_data";</script>'
    if downloadqr:
        video_data_dir = os.path.join(data_dir, downloadqr)
        if os.path.isdir(video_data_dir):
            img = qrcode.make(f"PULL_DATA {downloadqr}")
            img_io = io.BytesIO()
            img.save(img_io)
            img_io.seek(0)
            return send_file(img_io, as_attachment=True, download_name=f"{downloadqr}_PULLDATA.png")
        else:
            return "NO DIR"

    if request.method == "POST":
        name = request.form.get('name')
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            video_data_dir = os.path.join(data_dir, name)
            if os.path.isdir(video_data_dir):
                shutil.rmtree(video_data_dir)
                os.makedirs(video_data_dir)
            else:
                os.makedirs(video_data_dir)
            file.save(os.path.join(video_data_dir, filename))
            data_config = os.path.join(video_data_dir, "data.ini")
            configHelper.set_config(data_config, "data", "video_name", filename)
        return '<script>window.location.href="/admin/video_data";</script>'
    video_data_dirs = []
    for path in os.listdir(data_dir):
        video_data_dirs.append(os.path.basename(path))
    return render_template("video_data_ui.html", video_data_dirs=video_data_dirs)
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
@app.route("/ord/play", methods=['POST'])
@auth_required
def ord_play():
    allow_ord_play = configHelper.read_config(config_file, "ORDINANCE", "allow_ord_play", is_bool=True, default_value=True)
    if not allow_ord_play:
        return jsonify({'message': "NO"}), 403
    data = request.get_data()
    filename = secure_filename(request.headers.get("X-FILE-NAME"))
    if filename == '':
        return jsonify({'message': "NO FILE"}), 400
    if data and allowed_file(filename):
        if not os.path.isdir(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
            f.write(data)
        return jsonify({'message': "UPLOAD"}), 200
    else:
        abort(403)

@app.route("/ord/input/render",  methods=['GET'])
@auth_required
def ord_render():
    global inputs
    global dont_render
    state = configHelper.read_config(config_file, "ORDINANCE", "state")
    ip = configHelper.read_config(client_config_file, "Client", "ip", default_value="127.0.0.1", is_int=False)
    port = configHelper.read_config(client_config_file, "Client", "port", default_value=4456, is_int=True)
    ren_inputs = []
    if not os.path.isdir(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if dont_render:
        return jsonify({'message': "NO_INPUT"}), 200
    if state == "dead":
        inputs = []
        return jsonify({'message': "ORD_ERROR"}), 200
    if len(inputs) < 1:
        print("just RENDER")
        if len(os.listdir(UPLOAD_FOLDER)) > 0:
            render_play_thread = threading.Thread(target=render_play, daemon=True)
            render_play_thread.start()
            return jsonify({'message': "RENDER"}), 200                            

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

