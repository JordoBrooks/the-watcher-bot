import praw
import time

REPLY_MESSAGE = "Thanks for calling me!"

def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        'dogbot',
        user_agent="the_watcher_bot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit

def main():
    reddit = authenticate()
    while True:
        run_bot(reddit)

def run_bot(reddit):
    print("Obtaining comments...")
    for comment in reddit.subreddit("test").comments(limit=25):
        if "The Watcher Bot" in comment.body:
            print("String with keyword found in comment {}".format(comment.id))
            comment.reply(REPLY_MESSAGE)

    print("Sleeping...")
    time.sleep(10)

if __name__ == "__main__":
    main()
