#!/usr/bin/env python3
import pymongo
import bs4
import requests
import timestring
import os

def scrape_frontpage_match_urls(base_url):
    response = requests.get(base_url)
    if (response.status_code != 200):
        print("error, HTTP status code not 200")
        return

    soup = bs4.BeautifulSoup(response.text)
    frontpage_matches = soup.find_all("div", {"class": "match"})
    match_urls = []

    for match in frontpage_matches:
        completed_status = False
        
        if "notavailable" in match["class"]:
            completed_status = True
        link = match.find("a")
        if link:
            match_urls.append((link["href"], completed_status))
    return match_urls

def scrape_latest_csgolounge_matches(base_url):
    match_urls = scrape_frontpage_match_urls(base_url)
    matches = []
    for url in match_urls:
        response = requests.get(CSGOLOUNGE_BASE_URL+url[0])
        if (response.status_code != 200):
            print("error, HTTP status code not 200 for url: {}".format(url[0]))
            continue

        soup = bs4.BeautifulSoup(response.text)
        box = soup.find("div", {"class": "box-shiny-alt"})
        team_a = box.find_all("span")[0].find("b").text
        team_a_odds = box.find_all("span")[0].find("i").text
        team_b = box.find_all("span")[2].find("b").text
        team_b_odds = box.find_all("span")[2].find("i").text

        full = box.find("div", {"class": "full"})
        reward_boxes = full.find_all("div",{"class":"half"})
        # if noone has played on both teams, no reward can be given
        if (team_a_odds == "0%" and team_b_odds == "0%"):
            team_a_reward = ""
            team_b_reward = ""
        else:
            print(reward_boxes[0].div.br.contents[0])
            team_a_reward = reward_boxes[0].div.br.contents[0].split("for")[0].strip()
            team_b_reward = reward_boxes[1].div.br.contents[0].split("for")[0].strip()
        
        completed = url[1]
        if ("(win)" in team_a):
            team_a = team_a.replace(" (win)", "")
            winner = team_a
        elif ("(win)" in team_b):
            team_b = team_b.replace(" (win)", "")
            winner = team_b
        else:
            winner = "_NONE_"

        status_text = ""
        box_children = box.find_all("div", recursive=False)
        if len(list(box_children[1].findChildren())) == 0:
            status_text = box_children[1].text.strip()

        options_boxes = box.find_all("div",{"class":"half"})
        BO = options_boxes[1].text
        hour = options_boxes[2].text.strip()
        date = options_boxes[2]["title"]
        match_id = int(url[0].split("=")[1])
        print(match_id)
        timestring_date = timestring.Date("{1} at {0}".format(date, hour[:5]))
        print(BO)
        print(team_a, team_a_odds, team_a_reward, team_b, team_b_odds, team_b_reward, "winner={}".format(winner))
        print("\n")

        match = {"_id": match_id,
             "match_date": str(timestring_date), 
             "match_link": url[0],
             "team_a_potential_reward": team_a_reward,
             "team_b_potential_reward": team_b_reward,
             "team_a": team_a,
             "team_b": team_b,
             "team_a_odd":team_a_odds,
             "team_b_odd": team_b_odds,
             "match_type": BO,
             "winner": winner,
             "completed": completed,
             "status_text": status_text}
        matches.append(match)
    return matches

if __name__ == "__main__":
    # reading config file with DB_HOSTNAME and DB_PORT variables
    with open(os.path.join(os.path.dirname(__file__),"settings.txt"),"r") as f:
        config = f.readlines()

    config_dict = dict(line.strip().split("=") for line in config if not line.startswith("#"))
    DB_HOSTNAME=config_dict["DB_HOSTNAME"]
    DB_PORT=int(config_dict["DB_PORT"])

    CSGOLOUNGE_BASE_URL = "http://csgolounge.com/"

    # initialise database connection
    try:
        client = pymongo.MongoClient(DB_HOSTNAME, DB_PORT)
    except pymongo.errors.ConnectionFailure:
        print("failed to connect to database")
        sys.exit()

    db = client["csgo"]
    collection = db["csgomatches"]
    #latest_match = collection.find().sort("_id", direction=pymongo.DESCENDING).limit(1)[0]
    matches = scrape_latest_csgolounge_matches(CSGOLOUNGE_BASE_URL)
    
    for match in matches:
        collection.save(match)


