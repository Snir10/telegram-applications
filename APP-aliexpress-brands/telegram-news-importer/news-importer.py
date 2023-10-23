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
def send_msg_to_csv(msgDate, csv_f_name, title, link, nextUrl, id, images, parent, dir_name,
                    msgContent):
    with open(parent + csv_f_name, 'a', encoding='UTF8', newline='') as f:
        data = [msgDate, title, link, nextUrl, id, images, parent + dir_name, msgContent]
        writer = csv.writer(f)
        writer.writerow(data)
def create_csv(path, name):
    with open(path + name, 'x', encoding='UTF8', newline='') as f:
        header = ['uploaded time', 'title', 'link', 'next url', 'id', 'images', 'path',
                  'msg content']
        writer = csv.writer(f)
        writer.writerow(header)
# Rename and Move
def renameAndMoveFiles(directory_name):
    # TODO - IF ITEM IS *.MP4 - to handle it as video.

    for item in os.listdir(handle_fd):
        try:
            if item[len(item) - 3:] == 'mp4':
                logger.debug(f'MOVING: {handle_fd + item} --> {parent_dir + directory_name}')
                # Path(handle_fd + item).rename(parent_dir + directory_name + '/' + item)
                shutil.move(handle_fd + item, os.path.join(parent_dir, directory_name, item))

            else:
                logger.debug(f'MOVING: {handle_fd + item} --> {parent_dir + directory_name}')
                # Path(handle_fd + item).rename(parent_dir + +directory_name + '/' + item)
                shutil.move(handle_fd + item, os.path.join(parent_dir, directory_name, item))




        except:
            logger.error(f'Cannot move from\t {handle_fd + item} to {parent_dir + directory_name}')
# Create Folders
def createItemDirectory(directory_name):
    path = os.path.join(parent_dir, directory_name)
    try:
        os.mkdir(path)
    # fix for file already exists
    except OSError as e:
        if e.errno != errno.EEXIST:
            pass
def createTempImgFolder(param):
    path = os.path.join(parent_dir, param)

    try:
        os.mkdir(path)
    # fix for file already exists
    except OSError as e:
        if e.errno != errno.EEXIST:
            pass
# Get Msg TXT
def get_title(msg_content):
    try:
        title = msg_content.split('-')[0]
    except:
        logger.error(f'problem with title: -> {msg_content}')
        title = 'error'
    return title
def get_url(msg_content):
    try:
        url = re.search("(?P<url>https?://\S+)", msg_content).group("url")
    except:
        url = 'no url detected'
    return url
def getNextURL(url):
    try:
        res = requests.get(url).url.split('?')[0]
    except:
        res = 'no url'
    return res
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
    config.read("config_files/news_importer_config.ini")
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
def createAliExpressInstance():
    pass
    # return AliexpressApi('34061046', '3766ae9cf22b81c88134fb56f71eb03c', models.Language.EN, models.Currency.EUR,
    #                      'sn2019')
def sendMsgInfoToCSV(messageTime, csv_file, title, url, next_url, last_id, ids_obj, parentDir,
                     directory_name, msgContent):
    if os.path.exists(parentDir + csv_file):
        send_msg_to_csv(messageTime, csv_file, title, url, next_url, last_id,
                        str(ids_obj), parentDir, directory_name, msgContent)
    else:
        create_csv(parent_dir, csv_file)
        send_msg_to_csv(messageTime, csv_file, title, url, next_url, last_id,
                        str(ids_obj), parent_dir, directory_name, msgContent)
def renameImg(full_file_name, id):
    try:
        if full_file_name[len(full_file_name) - 3:] == 'mp4':
            logger.debug(f'[ID:{id}]MP4 Detected {full_file_name}')
            try:
                os.rename(full_file_name, handle_fd + id + '.mp4')
                sleep(1.5)
            except:
                logger.info(
                    f'Failed to Convert MP4 -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
        elif full_file_name[len(full_file_name) - 3:] == 'jpg':
            logger.debug(f'[ID:{id}]MP4 Detected {full_file_name}')

            try:
                os.rename(full_file_name, handle_fd + id + '.jpg')
            except:
                logger.info(
                    f'Failed to convert jpg ->full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
        else:
            try:
                os.rename(full_file_name, handle_fd + id + '.png')
            except:
                logger.info(
                    f'Failed to convert PNG ->full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
    except:
        logger.debug(f'couldn\'t rename a file:  {full_file_name}')
def getMsgUploadedDate(message):
    return str(message.date.strftime("%b %d, %H:%M:%S"))
def calculateSuccessRate(main_msg_id_counter, no_link_recived_cnt):
    try:
        affLinkCount = main_msg_id_counter - no_link_recived_cnt
        temp = (affLinkCount / main_msg_id_counter) * 100
        return [str(round(temp, 2)) + '%', affLinkCount]
    except:
        logger.error('failed to calculate success rate')
        return 'error'
async def print_current_import_status(main_msg_id_counter, offset_id, successRate, total_messages):
    # print("\n|| Current Offset ID is:", offset_id, "|| Total Messages:", total_messages, "|| Msg counter:",
    #       main_msg_id_counter, '|| Affiliate links', str(affLinkCount), "|| Failed Links:", no_link_recived_cnt, '|| SUCCESS_RATE', str(successRate), '\n')
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {main_msg_id_counter}')
    logger.info(f'Success Rate : {successRate}\n')


def print_all_msgs_content(messages):
    for msg in messages:
        id = msg.id
        print(f'[ID:{id}]:\t {msg.message}')
# def callback(current, total):
#     print('Downloaded', current, 'out of', total,

#           'bytes: {:.2%}'.format(current / total))

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

        await print_current_import_status(main_msg_id_counter, offset_id,
                                          successRate, total_messages)
        history = await client(
            GetHistoryRequest(peer=my_channel, offset_id=offset_id, offset_date=None, add_offset=0, limit=limit,
                              max_id=0, min_id=0, hash=0))
        if not history.messages:
            break
        messages = history.messages
        print_all_msgs_content(messages)
        for message in messages:
            sleep(timeout)
            all_messages.append(message.to_dict())
            id = str(message.id)


            if message.message == '':  # PHOTO \ VIDEO only
                # logger.info(f'[ID:{id}] PHOTO \ VIDEO Detected')
                #

                try:
                    full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)
                    # if await validate_media_size(message.media):
                    #     full_file_name = await client.download_media(message.media, parent_dir,
                    #                                                  progress_callback=callback)
                    #     # Continue with downloading the media if it's within the size limit
                    # else:
                    #     logger.warning('OOO')
                    #     full_file_name = ''
                    #     # Handle cases where the media size is too large or unsupported

                    img_counter += 1
                    ids_obj.append(id)
                    renameImg(full_file_name, id)
                except rpcerrorlist.FileReferenceExpiredError as e:
                    # Handle the exception if needed, or simply ignore it
                    print(f"Caught FileReferenceExpiredError: {e}")
                    # Continue running the program
                    pass


            else:  # TITLE + PHOTO
                if id == cfg_id:
                    await print_current_import_status(main_msg_id_counter, offset_id, total_messages, successRate)
                    logger.info(f'Finished with ID: {id}')
                    exit(0)
                logger.debug(f'[ID:{id}] TITLE + PHOTO Detected')

                main_msg_id_counter += 1
                if os.listdir(handle_fd):  # TITLE + HANDLING IS NOT EMPTY
                    id = str(message.id)
                    try:
                        last_id = str(last_main_msg.id)
                        directory_name = 'Item_' + last_id


                    except:
                        last_id = 'no last id'
                        logger.warning('no last msg found')
                    createItemDirectory(directory_name)
                    renameAndMoveFiles(directory_name)
                    messageTime = getMsgUploadedDate(message)

                    try:
                        title = get_title(last_main_msg.message)
                        url = get_url(last_main_msg.message)

                        logger.debug(
                            f'[ID:{id}] TXT + Photo DETECTED => Title: {title} URL: {url} images:{ids_obj.__len__()} images = {img_counter}')
                        #TODO to be erased
                        if url.startswith('http://sale.dhgate'):
                            logger.warning('URL is http://sale.dhgate')
                            files = glob.glob(handle_fd)
                            for f in files:
                                os.remove(f)
                                logger.warning(f'Removing {f}')
                            continue
                        next_url = getNextURL(url)



                    except:
                        price = title = url = next_url = 'no val'
                        logger.error('no title price and URL')


                    else:
                        pass

                    #TODO - news add
                    if last_main_msg == None:
                        lastMsg = ''
                    else:
                        lastMsg = last_main_msg.message

                    sendMsgInfoToCSV(messageTime, csvFile, title, url, next_url, last_id,
                                     str(ids_obj), parent_dir, directory_name, lastMsg)
                    new_file_name = ''
                    img_counter += 1

                    print_to_log(last_id, title, url, ids_obj, img_counter,
                                 messageTime)

                    if ids_obj.__len__() > 10:
                        logger.debug(f'IDs OBJ = {ids_obj.__len__()} | Image Counter = {img_counter}')
                    else:
                        logger.debug(f'IDs OBJ = {ids_obj.__len__()} | Image Counter = {img_counter}')

                    ids_obj = []
                    try:
                        full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)
                        #
                        # if await validate_media_size(message.media):
                        #     full_file_name = await client.download_media(message.media, parent_dir,
                        #                                                  progress_callback=callback)
                        # #     # Continue with downloading the media if it's within the size limit
                        # else:
                        #     logger.warning('OOO')

                            # Handle cases where the media size is too large or unsupported
                        renameImg(full_file_name, id)
                        ids_obj.append(id)
                        img_counter = 0
                        last_main_msg = message
                    except rpcerrorlist.FileReferenceExpiredError as e:
                        # Handle the exception if needed, or simply ignore it
                        print(f"Caught FileReferenceExpiredError: {e}")
                        # Continue running the program
                        pass




                else:  # handle fd empty + txt message = first message
                    logger.debug(
                        f'[ID:{id}][FIRST MSG] TXT + Photo - handle fd empty this should be in the FIRST message ')

                    ids_obj.append(id)
                    last_main_msg = message
                    img_counter = 0
                    try:
                        full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)

                        # if await validate_media_size(message.media):
                        #     full_file_name = await client.download_media(message.media, parent_dir,
                        #                                                  progress_callback=callback)
                        #     # Continue with downloading the media if it's within the size limit
                        # else:
                        #     logger.warning('OOO')
                        #     full_file_name = ''

                            # Handle cases where the media size is too large or unsupported
                        renameImg(full_file_name, id)
                        createItemDirectory('Item_' + id)
                    except rpcerrorlist.FileReferenceExpiredError as e:
                        # Handle the exception if needed, or simply ignore it
                        print(f"Caught FileReferenceExpiredError: {e}")
                        # Continue running the program
                        pass
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

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
    createTempImgFolder('Products_Handling')
    aliexpress = createAliExpressInstance()
    client.loop.run_until_complete(main())
