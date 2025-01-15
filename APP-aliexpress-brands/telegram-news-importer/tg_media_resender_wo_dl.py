import configparser
import json
from time import sleep
import logging
from datetime import datetime
from colorlog import ColoredFormatter
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, rpcerrorlist
from telethon.tl.functions.messages import (GetHistoryRequest)
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)
# CSV File
def print_to_log(msg_id, title, url, ids_obj, img_count, msg_time):
    # LOG Handling
    title = title.strip()[:50]
    title = '{:<15}'.format(title)

    status = '[SUCCESS]'

    logLine = status + '\t' + \
              f'[ID: {msg_id}]  ' \
              f'Title: {title} \t' + \
              'Link:' + url + '\t' + \
              'Image files:' + str(ids_obj) + '\t' + \
              'img count: ' + str(img_count) + '\t' + \
              f'From: {msg_time} \t'

    logger.info(logLine)
def print_welcome_csv_importer():
    print('##########################################################################################')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print('###############\t\tWelcome to NEWS Importer\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tSource Channel ID is = {channel_id}')
    print(f'###############\t\tTarget chat_id is: {chat_id}\t\t\t\t\t\t\t\t##############')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print(f'##########################################################################################\n')
    sleep(0.5)
def logger_init():
    # init logger
    l = logging.getLogger('my_module_name')
    l.setLevel(level=logging.DEBUG)
    LOG_FORMAT = "%(log_color)s %(asctime)s %(levelname)-6s%(reset)s | %(log_color)s%(message)s%(reset)s"

    fh = logging.StreamHandler()
    formatter = ColoredFormatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    l.addHandler(fh)

    fh = logging.FileHandler(f'logs/importer_.log', encoding='utf-8')
    # fh = logging.FileHandler(f'{parent_dir}\\importer_{datetime.now().strftime("%b %d, %H:%M:%S")}.log')

    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    fh.setLevel(logging.DEBUG)
    l.addHandler(fh)

    return l
# Config Handling
def initialConfig():
    # Reading Configs
    config.read("config_files/tg_media_resender_wo_dl.ini")
    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    mobileNum = config['Telegram']['phone']
    username = config['Telegram']['username']
    # Create the client and connect
    Client = TelegramClient(username, api_id, api_hash)
    return [Client, mobileNum]
# Create Folder
async def print_current_import_status(main_msg_id_counter, offset_id, successRate, total_messages):
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {main_msg_id_counter}')
    logger.info(f'Success Rate : {successRate}\n')
async def main():
    await client.start()
    # Ensure you're authorized - was ->    if await client.is_user_authorized() == False: !!!
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    # me = await client.get_me()
    entity = channel_id
    my_channel = await client.get_entity(entity)
    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0
    main_msg_id_counter = 0
    img_counter = 0
    successRate = '0.00%'
    last_main_msg = None
    directory_name = ''
    logger.info(f'Channel ID is = {channel_id}')
    while True:
        await print_current_import_status(main_msg_id_counter, offset_id, successRate, total_messages)
        history = await client(GetHistoryRequest(peer=my_channel, offset_id=offset_id, offset_date=None, add_offset=0, limit=limit, max_id=0, min_id=0, hash=0))
        if not history.messages:
            break
        messages = history.messages
        async def send_media(client, target_chat_id, message):
            msg_id = message.id
            uploaded = str(message.date.strftime("%b %d, %H:%M:%S"))
            if message.media:
                # Check the media type and prepare the input media object
                if hasattr(message.media, 'photo'):
                    logger.info(f"[ID:{msg_id}] Photo detected.")
                    media_to_send = message.media.photo  # Use the photo reference directly
                elif hasattr(message.media, 'document'):
                    logger.info(f"[ID:{msg_id}] Document detected.")
                    media_to_send = message.media.document  # Use the document reference directly
                else:
                    logger.warning(f"[ID:{msg_id}] Unsupported media type, skipping.")
                    return

                # Send the media to the target chat
                await client.send_file(
                    entity=-1002389937591,
                    file=media_to_send,  # Directly use the media object
                    caption=f"Media sent from message ID: {msg_id}",
                )
                logger.info(f"[ID:{msg_id}] Media successfully sent to target chat - uploaded: {uploaded}")
            else:
                logger.warning(f"[ID:{msg_id}] No media found in the message - uploaded: {uploaded}")
        # Main loop to handle messages
        for message in messages:
            try:
                await send_media(client, chat_id, message)
                logger.debug(f"Sleeping {timeout} Sec.")
                sleep(timeout)
            except Exception as e:
                logger.error(f"[ID:{message.id}] Error while sending media: {e}")
                await client.disconnect()


config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]
with client:
    cfg_id = config['Telegram']['importer_last_id']
    timeout = int(config['Telegram']['Timeout'])
    channel_id = config['Telegram']['channel_id']
    chat_id = config['Telegram']['chat_id']



    logger = logger_init()
    print_welcome_csv_importer()
    client.loop.run_until_complete(main())
