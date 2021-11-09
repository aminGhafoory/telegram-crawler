import re, asyncio, configparser, sqlite3
from telethon import TelegramClient
from telethon import events
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from datetime import datetime

# +------------------user credentials-------------------+
config = configparser.ConfigParser()
config.read("config.ini")
api_id = config["user"]["api_id"]
api_hash = config["user"]["api_hash"]
phone_number = config["user"]["phone_number"]

# +-----------------------database-----------------------+
con = sqlite3.connect("links_db.db")
cur = con.cursor()
cur.execute(
    f"""CREATE TABLE IF NOT EXISTS links_table (
                            date TEXT ,
                            link TEXT PRIMARY KEY);"""
)
# +-----------------------------------------------------+
already_joined = [line.rstrip for line in open("already_joined.txt", "r")]
telegram_handle_regex = r"@(?P<handle>\w{5,32})"
telegram_link_regex = r"(?:https?:)?\/\/(?:t(?:elegram)?\.me|telegram\.org)\/joinchat\/(?P<username>[A-z0-9\_]{5,32}?[^\/\s]+)"
url_regex = r"(?P<link>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))"
# +--------------- start telegram client-----------------+
client = TelegramClient("session_db", api_id, api_hash)
client.start(phone=phone_number)

# +-----------auto join private channel/groups-----------+
@client.on(events.NewMessage(pattern=telegram_link_regex))
async def joiner(event):
    target_string = event.message.message
    re_result = re.search(telegram_link_regex, target_string)
    if re_result != None:
        try:
            print(re_result["username"])
            if re_result["username"] not in already_joined:
                await client(ImportChatInviteRequest(re_result["username"]))

        except UserAlreadyParticipantError:
            print("you already joined this chat")
            already_joined.append(re_result["username"])
            with open("already_joined.txt", "a") as f:
                f.write(f'{re_result["username"]}\n')

        except FloodWaitError as err:
            print(err)

        except Exception as err:
            print(err)


# +-----------auto join Public channel/groups-----------+
@client.on(events.NewMessage(pattern=telegram_handle_regex))
async def joiner_2(event):

    target_string = event.message.message
    re_result2 = re.search(telegram_handle_regex, target_string)

    if re_result2 != None:
        try:

            if re_result2["handle"] not in already_joined:
                username = await client.get_entity(re_result2["handle"])
                await client(JoinChannelRequest(username))

        except UserAlreadyParticipantError:
            print("you already joined this chat")
            already_joined.append(re_result2["handle"])
            with open("already_joined.txt", "a") as f:
                f.write(f'{re_result2["handle"]}\n')

        except FloodWaitError as  err:
            print(err)


        except Exception as err:
            print(err)


# main function
@client.on(events.NewMessage())
async def main(event):
    if event.is_channel or event.is_group:
        raw_text = event.message.message
        re_result = re.search(url_regex, raw_text)
        if re_result != None:
            print(re_result["link"])
            time = datetime.now().strftime("%Y-%m-%d")
            data = re_result["link"]
            sql = f"INSERT OR IGNORE INTO links_table VALUES ('{time}','{data}')"
            cur.execute(sql)
            con.commit()


asyncio.get_event_loop().run_forever()
client.run_until_disconnected()
