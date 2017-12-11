import the_watcher_bot.config
import json
import os
import praw
import re
import requests
import time

REPLY_MESSAGE = "Thanks for calling me!"

MARVEL_API_TOKEN = the_watcher_bot.config.marvel_api_key
MARVEL_API_BASE_URL = "https://gateway.marvel.com"

def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        'the_watcher_bot',
        user_agent="the_watcher_bot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit

def send_marvel_request():


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
