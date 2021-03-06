import hashlib
import json
import os
import praw
import re
import requests
import config
import time

MARVEL_API_PUBLIC_KEY = config.marvel_api_public_key
MARVEL_API_PRIVATE_KEY = config.marvel_api_private_key

MARVEL_API_BASE_URL = "https://gateway.marvel.com"
MARVEL_CHAR_URL = "/v1/public/characters"
MARVEL_SERIES_URL = "/v1/public/characters/{}/series"

CHAR_RESULTS_TO_RETURN = 1
SERIES_RESULTS_TO_RETURN = 10

GEN_ERR_MSG = "Something went wrong. I cannot see them."

NO_CHAR_ERR_MSG = "Something is wrong. I do not know that person."

def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        "the_watcher_bot",
        user_agent = "the_watcher_bot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


def build_comment(character, char_url, series_dict, attr_text):
    # Escape closing brackets in url for Reddit comment compatibility
    char_url = re.escape(char_url)
    print(char_url)

    comment = ("The character you've requested is [{}]({}).\n\n"
               "You can read more of this character in the following series:\n\n").format(character, char_url)

    for k, v in series_dict.items():
        comment += "* [{}]({})\n".format(k, re.escape(v))

    comment += "\n***\n\n^({})".format(attr_text)

    return comment


def extract_character(comment):
    # Convert comment to lowercase
    comment = comment.lower()

    # Partition the comment around call to "The Watcher Bot:"
    comment_partition = comment.partition("the watcher bot:")

    # Per bot contract, the character is the first word in quotation marks after the bot call
    extracted_character_text = comment_partition[2]
    extracted_character_text = extracted_character_text.strip()
    extracted_character_text = extracted_character_text.split("\"")

    # If our split character text has less than 3 pieces, than the input was invalid.
    # Return empty string
    if len(extracted_character_text) < 3:
        return ""

    character = extracted_character_text[1]

    return character


def fetch_character_info(character):
    # time stamp for use with Marvel API
    ts = time.time()

    # Build md5 hash of ts + publickey + privatekey for use with Marvel API
    hash = generate_hash(ts)

    query_dict = {"apikey": MARVEL_API_PUBLIC_KEY, "ts": ts, "hash": hash, "name": character, "limit": CHAR_RESULTS_TO_RETURN}

    # Make request to API
    response = requests.get(MARVEL_API_BASE_URL + MARVEL_CHAR_URL, params=query_dict)

    return response


def fetch_series_info(char_id):
    # time stamp for use with Marvel API
    ts = time.time()

    # Build md5 hash of ts + publickey + privatekey for use with Marvel API
    hash = generate_hash(ts)

    url = MARVEL_API_BASE_URL + MARVEL_SERIES_URL.format(str(char_id))

    query_dict = {"apikey": MARVEL_API_PUBLIC_KEY, "ts": ts, "hash": hash, "limit": SERIES_RESULTS_TO_RETURN}

    # Make request to API
    response = requests.get(url, params=query_dict)

    return response


def generate_hash(time_stamp):
    # Build md5 hash of ts + publickey + privatekey for use with Marvel API
    md5 = hashlib.md5()
    md5.update((str(time_stamp) + MARVEL_API_PRIVATE_KEY + MARVEL_API_PUBLIC_KEY).encode("utf-8"))
    hash = md5.hexdigest()
    return hash


def handle_request_from_user(character):
    # Make API request to Marvel to get character info (ID, description, etc.)
    response1 = fetch_character_info(character).text
    # Convert response into JSON
    response1 = json.loads(response1)
    print(response1)

    # If the response code isn't 200, something went wrong
    response_code = response1["code"]
    if response_code != 200:
        return GEN_ERR_MSG

    # If 0 characters are returned, then the Marvel API doesn't know who that is
    num_characters_returned = len(response1["data"]["results"])
    if num_characters_returned == 0:
        return NO_CHAR_ERR_MSG

    # We set a 1 result limit on the request so the first character ID is the one we want
    id = response1["data"]["results"][0]["id"]

    # Save the Marvel-official name for bot reply
    name = response1["data"]["results"][0]["name"]

    # Store the url for the character information page
    char_url = response1["data"]["results"][0]["urls"][1]["url"]

    # Store attribution text
    attr_text = response1["attributionText"]

    # Make API request to marvel for series info
    response2 = fetch_series_info(id).text
    # Convert response into JSON
    response2 = json.loads(response2)

    series_dict = {}

    # Extract the series returned (title and url)
    for i in range(SERIES_RESULTS_TO_RETURN):
        print(response2.keys())
        print(response2["status"])
        series = response2["data"]["results"][i]["title"]
        url = response2["data"]["results"][i]["urls"][0]["url"]
        series_dict[series] = url

    # Build the comment and return it
    return build_comment(name, char_url, series_dict, attr_text)


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
            character = extract_character(comment.body)
            print(character)

            bot_reply = handle_request_from_user(character)
            comment.reply(bot_reply)
            comments_replied_to.append(comment.id)

    with open("comments_replied_to.txt", "w") as f:
        for comment_id in comments_replied_to:
            f.write(comment_id + "\n")

    # put bot to sleep for 60 seconds to ensure never exceeding API daily request limit
    print("Sleeping for 1 min...")
    time.sleep(60)


if __name__ == "__main__":
    main()
