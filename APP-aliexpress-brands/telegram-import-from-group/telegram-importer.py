import configparser
import errno
import glob
import json
import os
import shutil
import os.path
import re
import csv
import subprocess
from time import sleep
from aliexpress_api import AliexpressApi, models
import logging
import requests
from datetime import datetime
from colorlog import ColoredFormatter
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)

# CSV File
def send_msg_to_csv(msgDate, csv_f_name, title, price, link, nextUrl, affiliate_link, id, images, parent, dir_name,
                    msgContent):
    with open(parent + csv_f_name, 'a', encoding='UTF8', newline='') as f:
        data = [msgDate, title, price, link, nextUrl, affiliate_link, id, images, parent + dir_name, msgContent]
        writer = csv.writer(f)
        writer.writerow(data)
def create_csv(path, name):
    with open(path + name, 'x', encoding='UTF8', newline='') as f:
        header = ['uploaded time', 'title', 'price', 'link', 'next url', 'affiliate_link', 'id', 'images', 'path',
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
def getTitle(msg_content):
    try:
        title = msg_content.split('-')[0]
    except:
        logger.error(f'problem with title: -> {msg_content}')
        title = 'error'
    return title
def getPrice(msg_content):
    try:
        price = str(re.findall(r"\$\d+(?:\.\d+)?|\d+(?:\.\d+)?\$", msg_content))[:-2]
        price = price.split('\\')[0][2::]
        price = price.replace('$', '')
        # print(price)
        price = ('%.2f' % float(price))
        # print(str(price))
    except:
        logger.debug('price NOT detected')
        price = ''
    return price + '$'
def getURL(msg_content):
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
def setAffiliateLink(next_url, no_link_recived_cnt, aliexpress):
    if next_url.startswith('https://he.aliexpress.com/item/') or next_url.startswith('https://www.aliexpress.us/item'):
        resp = aliexpress.get_affiliate_links(next_url)
        logger.debug(f'AliExpress Response:\t{resp}')
        if hasattr(resp[0], 'promotion_link'):
            if resp[0].promotion_link.startswith('https'):
                affiliate_link = resp[0].promotion_link
            else:
                affiliate_link = 'Failed to convert Ali Express link\t'
                logger.error(resp)
                no_link_recived_cnt += 1
        else:
            affiliate_link = 'no link from AE'
            logger.error('no promotion link received from aliexpress')

    elif next_url.startswith('https://best.aliexpress.com'):
        affiliate_link = 'BROKEN: best.aliexpress.com'
    else:
        affiliate_link = 'No Ali Express link detected'
        logger.warning(f'Bad link -> {next_url}')
        no_link_recived_cnt += 1
    return [affiliate_link, no_link_recived_cnt]
# LOG Handling
def print_to_log(msg_id, title, price, url, affiliate_link, new_file_name, ids_obj, img_count, msg_time):
    title = title.strip()[:18]
    title = '{:<15}'.format(title)
    if affiliate_link.startswith('https://s.click.ali'):
        status = '[SUCCESS]'
    else:
        status = '[FAILED]'
    logLine = status + '\t' + \
              f'[ID: {msg_id}]  ' \
              f'From: {msg_time} \t' + \
              f'Title: {title} \t' + \
              'Price:' + price + '\t' + \
              'Link:' + url + '\t' + \
              'Aff_link:' + affiliate_link + '\t' + \
              'Saved-> ' + new_file_name + '\t' + \
              'Image files:' + str(ids_obj) + '\t' + \
              'img count: ' + str(img_count)
    # f'last_msg: {last_msg[:-1]}'
    if affiliate_link.startswith('https://s.click.ali'):
        logger.info(logLine)
    else:
        logger.error(logLine)
def print_welcome_csv_importer(csvFileName):
    print('##########################################################################################')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print('###############\t\tWelcome to CSV Importer\t\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tCSV file =>\t{csvFileName}\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\twill FINISH importing until -> ID:{cfg_id}\t\t\t\t##############')
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

    fh = logging.FileHandler(f'logs/importer_.log')
    # fh = logging.FileHandler(f'{parent_dir}\\importer_{datetime.now().strftime("%b %d, %H:%M:%S")}.log')

    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    fh.setLevel(logging.DEBUG)
    l.addHandler(fh)

    return l
# Config Handling
def initialConfig():
    # Reading Configs
    config.read("config_files/importer_config.ini")
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
    return AliexpressApi('34061046', '3766ae9cf22b81c88134fb56f71eb03c', models.Language.EN, models.Currency.EUR,
                         'sn2019')
def sendMsgInfoToCSV(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id, ids_obj, parentDir,
                     directory_name, msgContent):
    if os.path.exists(parentDir + csv_file):
        send_msg_to_csv(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id,
                        str(ids_obj), parentDir, directory_name, msgContent)
    else:
        create_csv(parent_dir, csv_file)
        send_msg_to_csv(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id,
                        str(ids_obj), parent_dir, directory_name, msgContent)
def renameImg(full_file_name, id):
    try:
        if full_file_name[len(full_file_name) - 3:] == 'mp4':
            logger.debug(f'mp4 detected {full_file_name}')
            try:
                os.rename(full_file_name, handle_fd + id + '.mp4')
                sleep(1.5) #TODO fix to 1 or 2 to reduce time
            except:
                logger.info(
                    f'Failed to convert MP4 -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
        else:
            try:
                os.rename(full_file_name, handle_fd + id + '.png')
            except:
                logger.info(
                    f'Failed to convert PNG ->full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
    except:
        logger.error(f'couldn\'t rename a file:  {full_file_name}')
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

def callback(current, total):
    print('Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))
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
    entity = 'https://t.me/hypeallie'
    my_channel = await client.get_entity(entity)
    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0
    ids_obj = []
    main_msg_id_counter = 0
    # msg_count = 0
    img_counter = 0
    no_link_received_cnt = 0
    affLinkCount = 0
    successRate = '0.00%'
    last_main_msg = None

    directory_name = ''
    # aliexpress = createAliExpressInstance()

    while True:

        await print_current_import_status(affLinkCount, main_msg_id_counter, no_link_received_cnt, offset_id,
                                          successRate, total_messages)
        history = await client(
            GetHistoryRequest(peer=my_channel, offset_id=offset_id, offset_date=None, add_offset=0, limit=limit,
                              max_id=0, min_id=0, hash=0))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            sleep(timeout)
            all_messages.append(message.to_dict())
            id = str(message.id)
            if id == '538159':
                pass

            if message.message == '':  # PHOTO \ VIDEO only
                logger.debug(f'[ID:{id}] PHOTO \ VIDEO Detected')
                full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)
                img_counter += 1
                ids_obj.append(id)
                renameImg(full_file_name, id)

            else:  # TITLE + PHOTO
                if id == cfg_id:
                    await print_current_import_status(affLinkCount, main_msg_id_counter, no_link_received_cnt,
                                                      offset_id, successRate, total_messages)
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
                    affiliate_link = 'ERROR: line 333'

                    try:
                        title = getTitle(last_main_msg.message)
                        price = getPrice(last_main_msg.message)
                        url = getURL(last_main_msg.message)

                        logger.debug(
                            f'[ID:{id}] TXT + Photo DETECTED => Title: {title} price: {price} URL: {url} images:{ids_obj.__len__()} images = {img_counter}')

                        if url.startswith('http://sale.dhgate'):
                            # FIXED BUG from id : 497669
                            logger.warning('URL is http://sale.dhgate')
                            files = glob.glob(handle_fd)
                            for f in files:
                                os.remove(f)
                                logger.warning(f'Removing {f}')
                            continue
                        logger.info(f'going to set affilate on URL: {url}')
                        next_url = getNextURL(url)
                        # TODO - this step stuck in ID 497679 where URL is URL is http://sale.dhgate


                    except:
                        price = title = url = next_url = 'no val'
                        logger.error('no title price and URL')


                    else:
                        resp = setAffiliateLink(next_url, no_link_received_cnt, aliexpress)
                        affiliate_link = resp[0]
                        no_link_received_cnt = resp[1]

                    cal = calculateSuccessRate(main_msg_id_counter, no_link_received_cnt)
                    successRate = cal[0]
                    affLinkCount = cal[1]
                    sendMsgInfoToCSV(messageTime, csvFile, title, price, url, next_url, affiliate_link, last_id,
                                     str(ids_obj), parent_dir, directory_name, last_main_msg.message)
                    new_file_name = ''
                    img_counter += 1

                    print_to_log(last_id, title, price, url, affiliate_link, new_file_name, ids_obj, img_counter,
                                 messageTime)

                    if ids_obj.__len__() > 10:
                        logger.error(f'IDs OBJ = {ids_obj.__len__()} | Image Counter = {img_counter}')
                    else:
                        logger.warning(f'IDs OBJ = {ids_obj.__len__()} | Image Counter = {img_counter}')

                    ids_obj = []
                    full_file_name = await client.download_media(message.media, parent_dir)
                    renameImg(full_file_name, id)
                    ids_obj.append(id)
                    img_counter = 0
                    last_main_msg = message


                else:  # handle fd empty + txt message = first message
                    logger.debug(
                        f'[ID:{id}][FIRST MSG] TXT + Photo - handle fd empty this should be in the FIRST message ')

                    ids_obj.append(id)
                    last_main_msg = message
                    img_counter = 0
                    # msg_count += 1
                    full_file_name = await client.download_media(message.media, parent_dir)
                    renameImg(full_file_name, id)
                    createItemDirectory('Item_' + id)

            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break


async def print_current_import_status(affLinkCount, main_msg_id_counter, no_link_recived_cnt, offset_id, successRate,
                                      total_messages):
    # print("\n|| Current Offset ID is:", offset_id, "|| Total Messages:", total_messages, "|| Msg counter:",
    #       main_msg_id_counter, '|| Affiliate links', str(affLinkCount), "|| Failed Links:", no_link_recived_cnt, '|| SUCCESS_RATE', str(successRate), '\n')
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {main_msg_id_counter}')
    logger.info(f'Affiliate Links : {affLinkCount}')
    logger.info(f'Failed Links : {no_link_recived_cnt}')
    logger.info(f'Success Rate : {successRate}\n')


config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]
with client:
    # remove parent if exists
    subprocess.call("/Users/user/Desktop/github projects/python/telegram-import-from-group/removeParentDir.py",
                    shell=True)

    parent_dir = config['Telegram']['parent_dir']
    handle_fd = config['Telegram']['handle_fd']
    csvFile = config['Telegram']['csv']
    cfg_id = config['Telegram']['importer_last_id']
    timeout = int(config['Telegram']['Timeout'])

    createParentDir()
    logger = logger_init()
    print_welcome_csv_importer(csvFile)
    createTempImgFolder('Products_Handling')
    aliexpress = createAliExpressInstance()

    client.loop.run_until_complete(main())
