import hashlib
import json
import os
import praw
import re
import requests
import the_watcher_bot.config
import time

REPLY_MESSAGE = "Thanks for calling me!"

MARVEL_API_PUBLIC_KEY = the_watcher_bot.config.marvel_api_public_key
MARVEL_API_PRIVATE_KEY = the_watcher_bot.config.marvel_api_private_key

MARVEL_API_BASE_URL = "https://gateway.marvel.com"
MARVEL_CHAR_URL = "/v1/public/characters"
MARVEL_EVENTS_URL_PREFIX = "/v1/public/characters/"
MARVEL_EVENTS_URL_POSTFIX = "/events"

CHAR_RESULTS_TO_RETURN = 1
EVENT_RESULTS_TO_RETURN = 10

def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        "the_watcher_bot",
        user_agent = "the_watcher_bot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


def build_comment(character, char_url, series_dict):
    return


def fetch_character_info(character):
    # time stamp for use with Marvel API
    ts = time.time()

    # Build md5 hash of ts + publickey + privatekey for use with Marvel API
    md5 = hashlib.md5()
    md5.update(ts + MARVEL_API_PUBLIC_KEY + MARVEL_API_PRIVATE_KEY)
    hash = md5.digest()

    query_dict = {"ts": ts, "hash": hash, "name": character, "limit": CHAR_RESULTS_TO_RETURN}

    # Make request to API
    response = requests.get(MARVEL_CHAR_URL, params=query_dict)

    return response


def fetch_event_info(char_id):
    # time stamp for use with Marvel API
    ts = time.time()

    # Build md5 hash of ts + publickey + privatekey for use with Marvel API
    md5 = hashlib.md5()
    md5.update(ts + MARVEL_API_PUBLIC_KEY + MARVEL_API_PRIVATE_KEY)
    hash = md5.digest()

    url = MARVEL_EVENTS_URL_PREFIX + str(char_id) + MARVEL_EVENTS_URL_POSTFIX

    query_dict = {"ts": ts, "hash": hash, "limit": EVENT_RESULTS_TO_RETURN, "orderBy": "-startDate"}

    # Make request to API
    response = requests.get(url, params=query_dict)

    return response


def handle_request_from_user(character):
    # Make API request to Marvel to get character info (ID, description, etc.)
    response1 = fetch_character_info(character)

    # We set a 1 result limit on the request so the first character ID is the one we want
    id = response1["data"]["results"][0]["id"]

    # Store the url for the character information page
    char_url = response1["data"]["results"][0]["urls"][1]["url"]

    # Make API request to marvel for
    response2 = fetch_event_info(id)

    series_dict = {}

    # Extract the events returned (title and url)
    for i in range(EVENT_RESULTS_TO_RETURN):
        series = response2["data"]["results"][i]["title"]
        url = response2["data"]["results"][i]["urls"][0]["url"]
        series_dict[series] = url

    # Build the comment and return it
    return build_comment(character, char_url, series_dict)


def main():
    reddit = authenticate()
    while True:
        run_bot(reddit)


def run_bot(reddit):
    if not os.path.isfile("comments_replied_to.txt"):
        comments_replied_to = []
    else:
        with open("comments_replied_to.txt", "r") as f:
            comments_replied_to = f.read()
            comments_replied_to = comments_replied_to.split("\n")
            comments_replied_to = list(filter(None, comments_replied_to))

    print("Obtaining comments...")
    subreddit = reddit.subreddit("test")
    for comment in subreddit.comments(limit=25):
        if re.search("the watcher bot:", comment.body, re.IGNORECASE) and comment.id not in comments_replied_to:
            print("String with keyword found in comment {}".format(comment.id))
            comment.reply(REPLY_MESSAGE)
            comments_replied_to.append(comment.id)

    with open("comments_replied_to.txt", "w") as f:
        for comment_id in comments_replied_to:
            f.write(comment_id + "\n")

    print("Sleeping...")
    time.sleep(10)


if __name__ == "__main__":
    main()
