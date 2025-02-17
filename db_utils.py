
from datetime import datetime, timedelta

from replit import db


def add_mention(channel_id: str, user_id: str, message_id: str):
    key = f"mention:{channel_id}:{user_id}:{message_id}"
    db[key] = {
        "timestamp": datetime.now().isoformat(),
        "channel_id": channel_id,
        "user_id": user_id,
        "message_id": message_id
    }

def remove_mention(channel_id: str, user_id: str, message_id: str):
    key = f"mention:{channel_id}:{user_id}:{message_id}"
    if key in db:
        del db[key]

def get_old_mentions(days=7):
    old_mentions = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for key in db.prefix("mention:"):
        mention = db[key]
        old_mentions.append(mention)
        continue
        mention_time = datetime.fromisoformat(mention["timestamp"])
        if mention_time < cutoff:
            old_mentions.append(mention)
    return old_mentions

def get_channel_user_mentions(channel_id: str, user_id: str):
    mentions = []
    prefix = f"mention:{channel_id}:{user_id}:"
    for key in db.prefix(prefix):
        mentions.append(db[key])
    return mentions
