#!/usr/bin/env python3
import pymongo
import json
import flask

from flask import Flask, request, jsonify
app = Flask(__name__)
app.debug = False


# reading config file with DB_HOSTNAME and DB_PORT variables
with open(os.path.join(os.path.dirname(__file__),"settings.txt"),"r") as f:
    config = f.readlines()

config_dict = dict(line.strip().split("=") for line in config if not line.startswith("#"))
DB_HOSTNAME=config_dict["DB_HOSTNAME"]
DB_PORT=int(config_dict["DB_PORT"])

try:
    client = pymongo.MongoClient(DB_HOSTNAME, DB_PORT)
except pymongo.errors.ConnectionFailure:
    print("failed to connect to database")
    sys.exit()
db = client["csgo"]
collection = db["csgomatches"]


@app.route('/')
def get_matches():
	result = collection.find().sort([("_id", pymongo.DESCENDING)])
	return jsonify({"matches": list(result)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)