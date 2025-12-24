from flask import Flask
from flask import request
from flask import jsonify
import os
from makeConfig import makeConfig
import configHelper
config_file = "ORDINANCE.ini"
app = Flask(__name__)
if os.path.isfile(config_file) == False:
    makeConfig()
@app.route("/")
def main_page():
    return "<p>ORDINANCE</p>"

@app.route("/ord/pawn/submit", methods=['POST'])
def pawn_submit():
    json_data = request.json
    
    player = json_data['player']
    timestamp = json_data['timestamp']
    trigger = json_data['trigger']
    print(player, timestamp, trigger)
    configHelper.set_config(config_file, "ORDINANCE", "player", player)
    configHelper.set_config(config_file, "ORDINANCE", "timestamp", timestamp)
    configHelper.set_config(config_file, "ORDINANCE", "trigger", trigger)
    
    return jsonify({'message': 'done'}), 200

@app.route("/ord/input", methods=['POST'])
def ord_input():
    json_data = request.json

    input = json_data['input']
    pawn_name = json_data['pawn_name']

    print(input, pawn_name)

    return jsonify({'message': 'input made'})
if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000)

