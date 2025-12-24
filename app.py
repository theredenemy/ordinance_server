from flask import Flask
from flask import request
from flask import jsonify
import os
from makeConfig import makeConfig
import configHelper
config_file = "ORDINANCE.ini"
inputs = []
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
@app.route("/ord/pawn/state", methods=['POST'])
def set_pawn_state():
    json_data = request.json

    state = json_data['state']
    configHelper.set_config(config_file, "ORDINANCE", "state", state)
    return jsonify({'message': 'done'}), 200

@app.route("/ord/input", methods=['POST'])
def ord_input():
    global inputs
    json_data = request.json

    input = json_data['input']
    pawn_name = json_data['pawn_name']

    print(input, pawn_name)

    if input == "BEGIN":
        inputs = []
        return jsonify({'message': 'BEGIN ORDINANCE'}), 200
    
    inputs.append(input)
    print(inputs)
    return jsonify({'message': inputs}), 200

@app.route("/ord/input/render",  methods=['GET'])
def ord_render():
    global inputs
    state = configHelper.read_config(config_file, "ORDINANCE", "state")
    if state == "dead":
        return jsonify({'message': "ORD_ERROR"}), 200
    if len(inputs) < 1:
        print("just RENDER")
        return jsonify({'message': "RENDER"}), 200
    # Some RENDER CODE
    for input in enumerate(inputs):
        print(input)
    print(inputs)

    return jsonify({'message': "RENDER"}), 200
if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000)

