import io
import re
from io import BytesIO
from tkinter import Image

import urllib3
from datetime import datetime
from colorlog import ColoredFormatter

import requests
import configparser
import logging
import random
import os
import pathlib

# from PIL import Image
# from instagrapi import Client
from time import sleep
import json

import bs4
import csv
from urllib.request import urlopen as uReq

# from numpy.core.defchararray import isnumeric

''' ##### Main Functions #####

    main method Scenario
    1. open CSV
    2. print welcome
    3. create list of IDs
    4. iterate between IDs till end.
    4. iterate between IDs till end.

    feature request:
    add to log:
        photo IDs
        fix spaces issues
        add more error logs
        fix counters  '''


# Init methods
def print_welcome_csv_uploader(l):
    logger.info(f'\n##########################################################################################\n' +
                f'###############\t\tWelcome to CSV Uploader\t\t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\t                           \t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tCSV file =>\t{csv_path[11:]}\t\t##############\n' +
                f'###############\t\tItems =>\t{l}\t\t\t\t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\t                           \t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tTelegram Upload Chat => {chat_id}\t\t\t\t\t##############\n' +
                f'###############\t\tInstagram Upload: {instaFlag}\t\t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\t                           \t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tLog Level => {logLevel}\t\tTimeout => {timeout} Seconds\t\t\t##############\n' +
                # f'###############\t\tTimeout => {timeout} Seconds \t\t\t\t\t\t\t\t\t##############\n' +
                f'##########################################################################################\n')


def logger_init():
    log = logging.getLogger('my_module_name')

    if logLevel == 'DEBUG':
        log.setLevel(level=logging.DEBUG)
    else:
        log.setLevel(level=logging.INFO)

    LOG_FORMAT = "%(log_color)s %(asctime)s %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"

    fh = logging.StreamHandler()
    fh.encoding = 'utf-8'

    formatter = ColoredFormatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # fh = logging.FileHandler(f'{src_dir_path}/uploader_{datetime.now().strftime("%b %d, %H-%M-%S")}.log')

    fh = logging.FileHandler(f'logs/importer_.log')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    return log


def insta_init():
    global bot
    if bool(instaFlag) == 'True':
        bot = Client()
        bot.login(username=username, password=password)
        return bot


def open_csv():
    returned_list = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        datareader = csv.reader(csvfile)

        next(datareader)  # Skip the header
        for row in datareader:


            folder_name = 'Item_' + row[6]
            dir_path = src_dir_path + '\\' + folder_name

            images = os.listdir(dir_path)
            images_list = []

            for img in images:
                try:
                    images_list.append(dir_path + '/' + img)
                except:
                    print('could not open this file --> ' + 'folder_path' + '/' + img)
                    pass

            returned_list.append(row)
        return returned_list
    # TODO - there is filter of click links, need to reduce this condition here or in for loop


def get_ids_from_csv():
    with open(csv_path, encoding='utf-8', errors='replace') as file:
        ids = []
        for l in csv.DictReader(file):
            if l['affiliate_link'].__contains__('click.aliexpress'):
                ids.append(str(l['id']))
    return ids

def get_item(csvline):
    t = csvline[1].replace("\n", '')
    p = str(csvline[2])
    l = csvline[5]
    id = csvline[6]
    path = src_dir_path + '\\Item_' + id
    images = os.listdir(path)
    imgs_path_list = []
    for image in images:
        if image[-3:] == 'png':
            imgs_path_list.append(path + '\\' + image)
        elif image[-3:] == 'mp4':
            imgs_path_list.append(path + '\\' + image)
    return [id, t, p, l, path, imgs_path_list]


# Telegram MSG
def createMsgTXT(count):
    count = str(count)
    logger.debug(f'creating a msg with: {title} {price} {link} {count}')
    if count != '0':
        txt = title[:20] + '\t|\t' + \
              price + '\n' + \
              'Orders: ' + count + '\n' + \
              '\nPlz Follow Images Instructions ☝🏻 \n' + \
              '\n\t🫴\t' + \
              link + '\n'

    else:
        txt = title[:20] + '\t|\t' + \
              price + '\n' + \
              '\nPlz Follow Images Instructions ☝🏻 \n' + \
              '\n\t🫴\t' + \
              link + '\n'
    return txt

def getOrders(my_url):
    try:
        uClient = uReq(my_url)
        page_html = uClient.read()
        uClient.close()
        page = bs4.BeautifulSoup(page_html, "html.parser")

        scripts = page.find_all('script')
        for script in scripts:
            txt = script.text
            if txt.__contains__('tradeCount'):
                logger.debug('tradeCount exists! we can print orders')
                match = re.search(r'"formatTradeCount":"([^"]+)"', txt)
                if match:
                    logger.debug(f'match: {match}')

                    formatTradeCount = match.group(1)
                    logger.debug(f'formatTradeCount: {formatTradeCount}')
                    if formatTradeCount == 0:
                        logger.info(f'orders count is 0 - resetting value to ''')
                        formatTradeCount = ''

                    return formatTradeCount
                else:
                    return "None"
            else:
                logger.debug('no valid parameter of orders')

        return orderCount

    except:
        logger.warning(f'no orders count for this product')
        return "no orders"


def get_price(p):
    if p.__contains__('$'):
        try:
            p = p.strip().replace('$', '')
            p = "{:.2f}".format(float(p))  # manipulate price to pure float with 2 decimal digits
        except:
            logger.debug('no valid price')
    return str(p) + dollar



def imagesToMedia(media_files, caption):
    """
        Use this method to send an album of photos or videos. On success, an array of Messages that were sent is returned.
        media_files: list of PIL images or video file paths to send
        caption: caption of media

        reply_to_message_id: If the message is a reply, ID of the original message
        response with sent message
        """
    files = {}
    media = []

    for i, media_file in enumerate(media_files):

        if os.path.isfile(media_file):
            with open(media_file, 'rb') as file:
                if media_file.endswith('.mp4'):
                    name = f'video{i}.mp4'
                    files[name] = file.read()
                    media.append(dict(type='video', media=f'attach://{name}'))
                else:
                    with io.BytesIO() as output:
                        try:
                            image_data = file.read()
                            output.write(image_data)
                            output.seek(0)

                            name = f'photo{i}.png'
                            files[name] = output.read()
                            media.append(dict(type='photo', media=f'attach://{name}'))
                        except Exception as e:
                            print(f'Error processing file {media_file}: {str(e)}')

        else:
            print(f'Invalid media file path: {media_file}')

    if caption is not None:
        media[0]['caption'] = caption

    return [media, files]


def sendMediaGroup(images, caption='new message', reply_to_message_id=None):
    logger.debug(f'sending media group to telegram')
    mediaGroupURL = f'https://api.telegram.org/bot{BOT}/sendMediaGroup'
    l = imagesToMedia(images, caption)
    media = l[0]
    files = l[1]
    response = requests.post(mediaGroupURL, data={'chat_id': chat_id, 'media': json.dumps(media),
                                                  'reply_to_message_id': reply_to_message_id}, files=files,
                             verify=False)
    sleep(int(timeout))
    # TODO - put into sendMediaGroup
    if response.status_code == 429:
        logger.debug(f'ID:{msg_id} [FAILED] with 429 -> RETRYING')
        response = requests.post(mediaGroupURL, data={'chat_id': chat_id, 'media': json.dumps(media),
                                                      'reply_to_message_id': reply_to_message_id}, files=files,
                                 verify=False)
        logger.debug(f'RESPONSE: {response.text}')

    return response


# HTTP STATUSES
def printStatus200(id):
    msg = f'[ID:{id}] [SUCCESS] {successRate}/{errorRate + successRate}\t{title}\t{price}\t{link}\tOrders:{orderCount}\tinsta={instaCounter} images={len(images_path_list)}'
    # Remove non-ASCII characters
    clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg)
    logger.info(clean_msg)


def printStatusUnknown(id):
    msg = f'[ID:{id}] [FAILED] {errorRate}/{errorRate + successRate} {title} {price} {link} ERROR -> status:{resp.status_code} {resp.text}'
    logger.error(msg)  # NOT 200


def printError():
    x = f'[ID:{msg_id}] [FAILED] {noLinkRate}\t{title}\t{price}\t{link}\tlink isn\'t containing s.click\t\t'
    logger.warning(x)


# INSTAGRAM
def uploadInstagramItem(count):
    try:
        text_2 = 'New in Stock'
        logger.debug(f'starting upload to instagram')
        convertedAlbumPathList = convert_folder_items(folder_path)
        re = bot.album_upload(convertedAlbumPathList, caption=text_2, to_story=True, usertags=[], )
        logger.info(re)
        logger.info('post has successfully uploaded to instagram')
        count += 1
    except:
        logger.warning('error -> no instagram post')
    return count


def convertJPG(item):
    im1 = Image.open(item)
    im2 = item[:-3] + 'jpg'
    im1.save(im2)
    return im2


def convert_folder_items(parentDir):
    targetDir = os.listdir(parentDir)
    orderedDir = []
    logger.debug(f'resizing images and converting to JPG')
    for item in targetDir:
        if item[-3:] == 'png':
            jpg_full_path = convertJPG(parentDir + '/' + item)

            image = Image.open(jpg_full_path)
            logger.debug(f'{item}\t image size is: {image.size}')

            image = image.convert("RGB")
            image = image.resize((1080, 1080))
            image.save(jpg_full_path)
            logger.debug(f'{item}\t new image size is: {image.size}')

            orderedDir.append(pathlib.Path(jpg_full_path))
            sleep(1)
            logger.debug(f'Item to add to folder:\t {item}')
    random.shuffle(orderedDir)
    return orderedDir


#
# TODO - not in use
def saveIdToCFG(id):
    config = configparser.RawConfigParser()
    config.read('config_files/uploader_config.ini')
    config.set('Telegram', 'last_uploaded_id', id)
    cfgfile = open('config_files/uploader_config.ini', 'w')
    config.write(cfgfile, space_around_delimiters=False)  # use flag in case you need to avoid white space.
    cfgfile.close()


def validate_last_id(id):
    if id == c['Telegram']['last_uploaded_id']:
        logging.info(f'### arrived to dest ID: {id} ###')
        sleep(10)
        exit(0)



config_file_path = os.path.join("config_files", "uploader_config.ini")
c = configparser.ConfigParser()
c.read(config_file_path, encoding='utf-8')

chat_id = c['Channels']['chat_id']
src_dir_path = c['Telegram']['src_dir_path']
timeout = c['Telegram']['timeout']
username = c['Instagram']['instagram_acc']
password = c['Instagram']['instagram_pass']
instaFlag = c['Instagram']['uploadToInstagram']
logLevel = c['Telegram']['log_level']
BOT = c['Bots']['BOT']


csv_path = src_dir_path + '\\products.csv'

successRate, errorRate, instaCounter, noLinkRate = 0, 0, 0, 0

logger = logger_init()
bot = insta_init()
details = open_csv()
print_welcome_csv_uploader(len(details))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

x = '️🧡🧡💛💚💚🤍🖤💜💙🤎❤️❤️❤️‍‍🔥💓💞❣️️💗💘💝'
dollar = '💲'
vi = '✔'

failed_imported_products_counter = 0

for msg_id in get_ids_from_csv():
    with open(csv_path, encoding='utf-8') as csv_file:
        for line in csv.DictReader(csv_file):
            if line is not None and line['id'] == msg_id and line['affiliate_link'][:3] == 'htt':
                csvLine = get_item(list(line.values()))

                price, link, folder_path, images_path_list, msg_id = csvLine[2], csvLine[3], csvLine[4], csvLine[5], \
                                                                     csvLine[0]

                if link.__contains__('click.aliexpress'):

                    if images_path_list.__len__() > 10 or images_path_list == 1 or csvLine[1].startswith('🆕🌟'):
                        failed_imported_products_counter += 1
                        logger.warning(
                            f'[ID:{msg_id}] {csvLine[1]} count: {images_path_list.__len__()} failed products counter: {failed_imported_products_counter}')
                        continue

                    title = '{:<15}'.format(f'{csvLine[1]} {random.choice(x)}'.strip()[:20])
                    price = get_price(price)
                    orderCount = getOrders(link)
                    msgTxt = createMsgTXT(orderCount)
                    resp = sendMediaGroup(images=images_path_list, caption=msgTxt)

                    if instaFlag == 'True': instaCounter = uploadInstagramItem(instaCounter)
                    if resp.status_code == 200:
                        successRate += 1
                        printStatus200(msg_id)
                    else:  # NOT 200
                        errorRate += 1
                        printStatusUnknown(msg_id)
                else:
                    noLinkRate += 1
                    logger.warning(f"skipping no link line {line['title']}")
                    printError()


'''     FINISH      '''
logger.warning(f'\nFINISHED - Failed Products Counter: {failed_imported_products_counter} Products')
logger.warning(f'\nFINISHED - Successfully uploaded: {successRate} Products')
logger.warning(f'\nFINISHED - Failed to Upload: {errorRate} Products')

logger.info('\nFINISHED - All Products Uploaded Successfully !!!!')
