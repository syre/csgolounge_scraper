#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module containing functions for scraping the matches of CSGOLounge.
"""
import os
import time
import pymongo
import bs4
import requests
import timestring

# reading config file with DB_HOSTNAME and DB_PORT variables
CURRENT_DIR = os.path.join(os.path.dirname(__file__))
with open(os.path.join(CURRENT_DIR, "settings.txt"), "r") as f:
    CONFIG = f.readlines()

CONFIG_DICT = dict(line.strip().split("=") for line in CONFIG if not line.startswith("#"))
DB_HOSTNAME = CONFIG_DICT["DB_HOSTNAME"]
DB_PORT = int(CONFIG_DICT["DB_PORT"])

# initialise database connection
CLIENT = pymongo.MongoClient(DB_HOSTNAME, DB_PORT)

DB = CLIENT["csgo"]
MATCHES = DB["csgomatches"]

CSGOLOUNGE_BASE_URL = "http://csgolounge.com/"


def scrape_all_matches(start_id=7000, time_delay=1):
    """
    Scrapes all completed CSGOLounge matches
    starting at start_id and incrementing
    uses a time_delay to avoid a large number
    of requests within a short time period
    """
    reached_newest = False
    while not reached_newest:
        response = requests.get(CSGOLOUNGE_BASE_URL+"match?m={}".format(start_id))
        start_id += 1
        # TODO - should we retry for X passes?
        if response.status_code != 200:
            print("returned response {}".format(response.status_code))
            continue
        # need extra check because CSGOLounge does not return HTTP 404 on /404 -_-
        if response.url == "https://csgolounge.com/404":
            reached_newest = True
            print("returned page 404")
        # don't include pages that redirect to predict pages
        if response.url.startswith("https://csgolounge.com/predict"):
            print("was predict page")
            continue
        if is_match_with_winner(response):
            match_data = extract_match_data(response)
            MATCHES.save(match_data)
            print(match_data)
        time.sleep(time_delay)
        print("sleeping")


def is_match_with_winner(response):
    """
    Determines if a winner has been found
    or not (and thus completed)
    """
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    box = soup.find("div", {"class": "box-shiny-alt"})

    team_a = box.find_all("span")[0].find("b").text
    team_b = box.find_all("span")[2].find("b").text
    win_str = "(win)"

    return win_str in team_a or win_str in team_b


def extract_match_data(response):
    """
    Extracts the match information from a CSGOLounge
    match site e.g. https://csgolounge.com/match?m=7000
    """
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    box = soup.find("div", {"class": "box-shiny-alt"})
    team_a = box.find_all("span")[0].find("b").text
    team_a_odds = box.find_all("span")[0].find("i").text
    team_b = box.find_all("span")[2].find("b").text
    team_b_odds = box.find_all("span")[2].find("i").text

    full = box.find("div", {"class": "full"})
    reward_boxes = full.find_all("div", {"class": "half"})
    # if noone has played on both teams, no reward can be given
    if team_a_odds == "0%" and team_b_odds == "0%":
        team_a_reward = ""
        team_b_reward = ""
    else:
        print(reward_boxes[0].div.br.contents[0])
        team_a_reward = reward_boxes[0].div.br.contents[0].split("for")[0].strip()
        team_b_reward = reward_boxes[1].div.br.contents[0].split("for")[0].strip()

    if "(win)" in team_a:
        team_a = team_a.replace(" (win)", "")
        winner = team_a
    elif "(win)" in team_b:
        team_b = team_b.replace(" (win)", "")
        winner = team_b

    status_text = ""
    box_children = box.find_all("div", recursive=False)
    if len(list(box_children[1].findChildren())) == 0:
        status_text = box_children[1].text.strip()

    options_boxes = box.find_all("div", {"class": "half"})
    match_type = options_boxes[1].text
    hour = options_boxes[2].text.strip()
    date = options_boxes[2]["title"]
    match_id = int(response.url.split("=")[1])
    timestring_date = timestring.Date("{1} at {0}".format(date, hour[:5]))

    match_data = {"_id": match_id,
                  "match_date": str(timestring_date),
                  "match_link": response.url,
                  "team_a_potential_reward": team_a_reward,
                  "team_b_potential_reward": team_b_reward,
                  "team_a": team_a,
                  "team_b": team_b,
                  "team_a_odd": team_a_odds,
                  "team_b_odd": team_b_odds,
                  "match_type": match_type,
                  "winner": winner,
                  "status_text": status_text}
    return match_data

if __name__ == "__main__":
    scrape_all_matches()
    #latest_match = collection.find().sort("_id", direction=pymongo.DESCENDING).limit(1)[0]
    
