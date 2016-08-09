#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask REST API for showing CSGOLounge matches
"""

import json
import os
import pymongo
from flask import Flask, request, jsonify, make_response, url_for, redirect

app = Flask(__name__)


# reading config file with DB_HOSTNAME and DB_PORT variables
with open(os.path.join(os.path.dirname(__file__), "settings.txt"), "r") as f:
    CONFIG = f.readlines()

CONFIG_DICT = dict(line.strip().split("=") for line in CONFIG if not line.startswith("#"))

DB_HOSTNAME = CONFIG_DICT["DB_HOSTNAME"]
DB_PORT = int(CONFIG_DICT["DB_PORT"])

CLIENT = pymongo.MongoClient(DB_HOSTNAME, DB_PORT)
DB = CLIENT["csgo"]
MATCHES = DB["csgomatches"]


@app.route('/', methods=["GET"])
def index():
    """
    default endpoint
    """
    return redirect(url_for("get_matches"))


@app.route('/matches', methods=["GET"])
def get_matches():
    """
    Returns all matches matching the parameters given
    """
    allowed_fields = ["teama", "teamb", "winner", "completed",
                      "team_a_odd", "team_b_odd"]
    sort_fields = {key: value for key, value in request.args.items() if key in allowed_fields}

    result = MATCHES.find(sort_fields).sort([("_id", pymongo.DESCENDING)])
    return jsonify({"matches": list(result)})


@app.route("/matches/<int:match_id>", methods=["GET"])
def get_match(match_id):
    """
    Returns a single match with specified ID
    """
    result = MATCHES.find({"_id": match_id}).limit(1)[0]
    return jsonify({"match": result})


@app.errorhandler(404)
def page_not_found():
    """
    error handler for 'Not Found'
    returns jsonified error response
    """
    return make_response(jsonify({"error": "Endpoint not found"}), 404)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)
