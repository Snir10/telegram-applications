import configparser
import errno
import glob
import json
import os
import shutil
import os
from telethon.tl.types import InputMediaDocument, InputMediaPhoto
import os.path
import re
import csv
import subprocess
from time import sleep
import logging
import requests
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
def print_to_log(msg_id, title, url, ids_obj, img_count, msg_time):# LOG Handling
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
def print_welcome_csv_importer(csvFileName):
    print('##########################################################################################')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print('###############\t\tWelcome to NEWS Importer\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tParent folder: \t{parent_dir}\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tCSV file =>\tCSV name: {csvFileName}\t\t\t\t\t\t\t##############')
    print(f'###############\t\tit will FINISH importing until -> ID:{cfg_id}\t\t\t\t\t##############')
    print(f'###############\t\t Channel ID is = {channel_id}')

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
    config.read("config_files/news_importer_config_media_only.ini")
    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    mobileNum = config['Telegram']['phone']
    username = config['Telegram']['username']
    # Create the client and connect
    Client = TelegramClient(username, api_id, api_hash)
    return [Client, mobileNum]
# Create Folder
def createParentDir():
    path = os.path.join(parent_dir)
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            pass
async def print_current_import_status(main_msg_id_counter, offset_id, successRate, total_messages):
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {main_msg_id_counter}')
    logger.info(f'Success Rate : {successRate}\n')
def print_all_msgs_content(messages):
    for msg in messages:
        id = msg.id
        print(f'[ID:{id}]:\t {msg.message}')
def callback(current, total):
    progress = current / total
    bar_length = 40
    bar = '=' * int(bar_length * progress)
    spaces = ' ' * (bar_length - len(bar))
    percent = progress * 100
    totalK = round(total/1000000, 2)
    currentK = round(current/1000000, 2)
    line = f'Downloaded {percent:.2f}% \t{currentK} MByte/s out of {totalK} MByte/s [{bar}{spaces}]'
    print(line)  # Update the line in the console without '\r'
def change_file_name(path, new_name):
    logger.info(f'changing filename PATH:{path} NEW NAME:{new_name} ')
    try:
        # Split the path into directory and file parts
        directory, filename = os.path.split(path)

        # Create the new file path with the specified name and the original extension
        new_path = os.path.join(directory, str(new_name) + os.path.splitext(filename)[1])

        # Rename the file
        os.rename(path, new_path)
    except:
        logger.warning(f'[ID:{new_name}] isnt supported')
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
    ids_obj = []
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
        # print_all_msgs_content(messages)
        for message in messages:
            msg_id = message.id
            if message.media and hasattr(message.media, 'document'):
                document = message.media.document

                file_size = document.size
                totalK = round(file_size / 1000000, 2)
                if file_size > 50000000:
                    logger.warning(f"[ID:{msg_id}] File Size: is more then 50Mb SKIPPING | {totalK}")
                    continue
            else:
                logger.warning(f'no attribute media in this message id : {msg_id} continuing')
                continue
            logger.info(f'[ID:{msg_id}] Downloading media.. ')
            full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)
            change_file_name(full_file_name, msg_id)
            logger.info(f'[ID:{message.id}] Done = file path:{full_file_name} size: {totalK}MBytes')
            logger.debug(f'Sleeping {timeout} Sec ')
            sleep(timeout)
config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]
with client:
    # remove parent if exists
    # subprocess.call("/Users/user/Desktop/github projects/python/telegram-import-from-group/removeParentDir.py",
    #                 shell=True)
    parent_dir = config['Telegram']['parent_dir']
    handle_fd = config['Telegram']['handle_fd']
    csvFile = config['Telegram']['csv']
    cfg_id = config['Telegram']['importer_last_id']
    timeout = int(config['Telegram']['Timeout'])
    channel_id = config['Telegram']['channel_id']
    createParentDir()
    logger = logger_init()
    print_welcome_csv_importer(csvFile)
    client.loop.run_until_complete(main())
