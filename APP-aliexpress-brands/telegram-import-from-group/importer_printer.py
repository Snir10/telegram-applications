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
from bs4 import BeautifulSoup

from aliexpress_api.errors import ApiRequestException
from colorlog import ColoredFormatter
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FileMigrateError
from telethon.tl.functions.messages import (GetHistoryRequest)


# CSV File
def send_msg_to_csv(msgDate, csv_f_name, title, price, link, nextUrl, affiliate_link, msg_id, images, parent, dir_name,
                    msgContent):
    with open(parent + csv_f_name, 'a', encoding='utf-8', newline='') as f:
        data = [msgDate, title, price, link, nextUrl, affiliate_link, msg_id, images, parent + dir_name, msgContent]
        writer = csv.writer(f)
        writer.writerow(data)


def create_csv(path, name):
    with open(path + name, 'x', encoding='utf-8', newline='') as f:
        header = ['uploaded time', 'title', 'price', 'link', 'next url', 'affiliate_link', 'id', 'images', 'path',
                  'msg content']
        writer = csv.writer(f)
        writer.writerow(header)


# Rename and Move
def renameAndMoveFiles(directory_name):
    for item in os.listdir(handle_fd):
        try:
            if item[len(item) - 3:] == 'mp4':
                shutil.move(handle_fd + item, os.path.join(parent_dir, directory_name, item))
            else:
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
    logger.debug(f'title is: {title}')
    # remove_emojis(title)

    logger.debug(f'REMOVE EMOJIES: title is: {title}')
    return title


def getPrice(msg_content):
    try:
        price = str(re.findall(r"\$\d+(?:\.\d+)?|\d+(?:\.\d+)?\$", msg_content))[:-2]
        price = price.split('\\')[0][2::]
        if price.__contains__('€'): logger.warning(f'euro detected: € PRICE: {price}')
        price = price.replace('$', '')
        price = ('%.2f' % float(price))
    except:
        logger.debug('price NOT detected')
        price = ''

    logger.debug(f'price is: {price}')
    return price + '$'


def getURL(msg_content):
    try:
        # logger.warning('before search ')
        url = re.search("(?P<url>https?://\S+)", msg_content).group("url")
        # logger.warning(f'after search url is: \n {url} ')

    except Exception as e:
        logger.warning("Error occurred:", e)
        url = ''
    logger.debug(f'url is: {url}')

    return url


def getNextURL(url):
    if url.startswith('http://sale.dhgate') or url.startswith('https://sale.dhgate'): return 'no next url'
    try:
        logger.debug('trying next url')
        # res = requests.get(url, allow_redirects=True, timeout=20).url.split('?')[0]
        res = requests.get(url, allow_redirects=True, timeout=20).url.split('?')

    except Exception as e:
        logger.warning("Error occurred:", e)
        res = 'no next url'
    logger.debug(f'next url is: {res}')

    return res


def setAffiliateLink(next_url, no_link_recived_cnt):
    try:
        if next_url.startswith('https://s.click.al'):
            resp = aliexpress.get_affiliate_links(next_url, timeout=30)
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
                logger.warning('[ALIEXPRESS Response] not valid for affiliate')

        elif next_url.startswith('https://best.aliexpress.com'):
            affiliate_link = 'BROKEN: best.aliexpress.com'
        else:
            affiliate_link = 'No Ali Express link detected'
            logger.warning(f'Bad link -> {next_url}')
            no_link_recived_cnt += 1
    except ApiRequestException as e:
        print(f"Error: {e}")
        # Handle the error, log, or perform any necessary actions
        # You can choose to continue the loop or break out of it based on your requirements
        continue_loop = True  # Set to True if you want to continue the loop
        if continue_loop:
            return [None, no_link_recived_cnt]  # Returning None or some specific value to indicate the failure
        else:
            raise  # Raise the exception if you don't want to continue the loop

    return [affiliate_link, no_link_recived_cnt]


# LOG Handling
def print_to_log(msg_id, title, price, url, affiliate_link, ids_obj, img_count, msg_time):
    orig_msg = title
    title = title.strip()[:18]
    title = '{:<15}'.format(title)
    if affiliate_link is not None and affiliate_link.startswith('https://s.click.ali'):
        status = '[SUCCESS]'
    else:
        status = '[FAILED]'
        affiliate_link = 'no link received'
    logLine = status + '\t' + \
              f'[ID: {msg_id}]  ' \
              f'From: {msg_time} \t' + \
              f'Title: {title} \t' + \
              'Price:' + price + '\t' + \
              'Link:' + url + '\t' + \
              'Aff_link:' + affiliate_link + '\t' + \
              'Image files:' + str(ids_obj) + '\t' + \
              'img count: ' + str(img_count) + \
              'orig msg:' + str(orig_msg)
    if affiliate_link.startswith('https://s.click.ali'):
        logger.info(logLine)
    else:
        logger.error(logLine)


def print_welcome_csv_importer(csvFileName):
    print('##########################################################################################')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print('###############\t\tWelcome to CSV Importer\t\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tCSV file =>\t{csvFileName}\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tpath =>\t{parent_dir}\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\twill FINISH importing until -> ID:{cfg_id}\t\t\t\t##############')
    print('###############\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t##############')
    print(f'##########################################################################################\n')
    sleep(0.5)


def logger_init():
    def safe_emit(self, record):
        try:
            msg = self.format(record)
            if isinstance(msg, bytes):
                # If the message is a bytes object, decode it using utf-8
                msg = msg.decode('utf-8', errors='replace')
            # Encode the message as ascii and decode it using 'backslashreplace' error handler to handle non-ascii characters
            msg = msg.encode('ascii', errors='backslashreplace').decode('ascii')
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    # init logger
    l = logging.getLogger('my_module_name')
    l.setLevel(level=logging.DEBUG)
    LOG_FORMAT = "%(log_color)s %(asctime)s %(levelname)-6s%(reset)s | %(log_color)s%(message)s%(reset)s"
    fh = logging.StreamHandler()
    formatter = ColoredFormatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    l.addHandler(fh)
    # fh = logging.FileHandler(f'logs/importer_.log', encoding='utf-8')
    fh = logging.FileHandler(f'{parent_dir}\\importer_{datetime.now().strftime("%b%d_%H%M%S")}.log')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    fh.setLevel(logging.DEBUG)
    l.addHandler(fh)

    # Override the emit method of the handler with the safe_emit function
    fh.emit = safe_emit.__get__(fh, logging.StreamHandler)

    return l


# Config Handling
def initialConfig():
    # Reading Configs
    config.read("config_files/importer_config_ZARA.ini")
    # Setting configuration values
    api_id = int(config['Telegram']['api_id'])
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


def msg_to_csv(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id, ids_obj, parentDir,
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
        extension = full_file_name[-3:].lower()  # Extracting the file extension and converting to lowercase
        cases = {
            'mp4': {
                'message': f'[ID:{id}] MP4 Detected {full_file_name}',
                'new_extension': '.mp4'
            },
            'png': {
                'message': f'[ID:{id}] PNG Detected {full_file_name}',
                'new_extension': '.png'
            },
            'jpg': {
                'message': f'[ID:{id}] JPG Detected {full_file_name}',
                'new_extension': '.jpg'
            }
        }
        case = cases.get(extension)
        if case:
            logger.debug(case['message'])
            try:
                os.rename(full_file_name, handle_fd + id + case['new_extension'])
                sleep(1.5)
            except:
                logger.info(
                    f'Failed to convert {extension.upper()} -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
        else:
            try:
                logger.debug(f'[ID:{id}] Unsupported format Detected {full_file_name}')
                # Rename as png by default if format not supported
                os.rename(full_file_name, handle_fd + id + '.png')
            except:
                logger.info(
                    f'Failed to convert unsupported format -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
    except:
        logger.error(f'Couldn\'t rename a file:  {full_file_name}')


def getMsgUploadedDate(message):
    return str(message.date.strftime("%b %d, %H:%M:%S"))


def calc_success_rate(main_msg_id_counter, no_link_received_cnt):
    try:
        affLinkCount = main_msg_id_counter - no_link_received_cnt
        temp = (affLinkCount / main_msg_id_counter) * 100
        return [str(round(temp, 2)) + '%', affLinkCount]
    except:
        logger.error('failed to calculate success rate')
        return 'error'


def callback(current, total):
    pass
    # print('Downloaded', current, 'out of', total,
    #       'bytes: {:.2%}'.format(current / total))


def is_blacklisted(url):
    logger.debug('checking blacklisted ')
    patterns = r'dhgate', r'best.aliexpress' \
                          r'' \
                          r'', r't.me', r'yupoo', r'store', r'lizaon', r'dsquared21', r'/gcp/', r'facebook', r'gmail.com', r'Catalogs', r'support'
    flag = False
    for pattern in patterns:
        match = re.search(pattern, url)
        # logger.debug(f'testing pattern: {pattern} is contain -> {url}')
        if match:
            logger.warning(f'Bad link: pattern:"{pattern}" found on {url}')
            flag = True
    if not flag: logger.debug(f'URL: {url} not blacklisted')
    return flag


def check_product_existence(product_url):
    try:
        # Send a GET request to the product URL
        response = requests.get(product_url)
        # Parse the HTML content of the response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if the page title contains "Page Not Found"
        page_title = soup.title
        logger.debug(f'Page title is: {page_title}')

        if page_title and "Page Not Found" in page_title.text:
            return False  # Product does not exist if the title indicates page not found

        # Check if the div with the specified inner text is present
        not_available_div = soup.find('div', string="מצטערים, המוצר אינו זמין יותר.")
        if not_available_div:
            return False  # Product does not exist if the div with the specified text is found

        return True  # Product exists if neither the title nor the div indicates product not found

    except Exception as e:
        logger.error("Error occurred:", e)
        return False  # Assuming product doesn't exist if an error occurs
        pass


def remove_emojis(text):
    # Emoji ranges (source: https://unicode.org/emoji/charts/full-emoji-list.html)
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # Transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        u"\U00002500-\U00002BEF"  # Chinese/Japanese/Korean characters
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\U0001f525"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


async def main():
    await client.start()
    if not await client.is_user_authorized():  # Ensure you're authorized - was ->    if await client.is_user_authorized() == False: !!!
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    # me = await client.get_me()
    # entity = 'hypeallie'
    entity = 'morashaaa'
    # entity = 'mawymarcas'
    # entity = 'ZAPATILLASTOP1'
    my_channel = await client.get_entity(f'https://t.me/{entity}')
    logger.warning(f'Entity is: https://t.me/{entity}')

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0
    ids_obj = []
    main_msg_id_counter = 0
    img_counter = 0
    page_not_found_count = 0
    no_link_received_cnt = 0
    affLinkCount = 0
    successRate = '0.00%'
    last_main_msg = None
    directory_name = ''
    last_group_id = ''
    grouped_msgs = []

    while True:
        await print_current_import_status(affLinkCount, main_msg_id_counter, no_link_received_cnt, offset_id,
                                          successRate, total_messages, page_not_found_count)
        history = await client(
            GetHistoryRequest(peer=my_channel,
                              offset_id=offset_id,
                              offset_date=None,
                              add_offset=0,
                              limit=limit,
                              max_id=0,
                              min_id=0,
                              hash=0))
        if not history.messages:
            break
        messages = history.messages

        for message in messages:

            user_id = str(message.from_user.id)

            if user_id != '516389439': logger.warning(f'USER MSG: {message.message}')
            sleep(1)
            # if message.message.__contains__('s.click'):
            #     logger.info(f'[ID: {str(message.id)}\t GROUP_ID={message.grouped_id} TEXT={message.message}')
        logger.debug(f'sleeping test timeout in the end')
        sleep(timeout)


# async def remove_handle_fd_files():
async def print_current_import_status(affLinkCount, main_msg_id_counter, no_link_recived_cnt, offset_id, successRate,
                                      total_messages, page_not_found_count):
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {main_msg_id_counter}')
    logger.info(f'Affiliate Links : {affLinkCount}')
    logger.info(f'Failed Links : {no_link_recived_cnt}')
    logger.info(f'Success Rate : {successRate}')
    logger.info(f'Page not Found : {page_not_found_count}\n')


config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]
with client:
    # remove parent if exists


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
