import base64
import os.path
import configparser
import errno
from urllib.request import urlopen as uReq
from urllib.parse import urlparse, parse_qs, unquote
import os
import shutil
import os.path
import csv
import subprocess
from time import sleep
import re
import bs4
from telegram.ext import Updater
from aliexpress_api import AliexpressApi, models
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from colorlog import ColoredFormatter
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
import requests

# CSV File
def send_msg_to_csv(msgDate,p_id, csv_f_name, title, price, link, nextUrl, affiliate_link, msg_id, images, parent, dir_name, msgContent):
    def safe_encode(val):
        if isinstance(val, str):
            # If the value is a string, encode it as UTF-8
            return val.encode('utf-8').decode('utf-8')
        return val

    with open(parent + csv_f_name, 'a', encoding='utf-8', newline='') as csv_file:
        # Encode each value in the data list using the safe_encode function
        data = [safe_encode(val) for val in [msgDate, title, price,p_id, link, nextUrl, affiliate_link, msg_id, images, parent + dir_name, msgContent]]
        writer = csv.writer(csv_file)
        writer.writerow(data)


def monitor_string(text):
    logger.debug(f'previous title is: {text}')

    # Define the dictionary with special words and their options
    special_words = {
        'APPLE': ['APPLE', 'איירפודס'],
        'ZARA': ['ZARA', 'זארה'],
        'ALO': ['ALO', 'alo'],
        'LULULEMON': ['LULULEMON', 'LULU'],
        'MASSIMO': ['MASSIMO'],
        'celine': ['celine'],
        'ADIDAS': ['ADIDAS'],
        'ZARA_': ['TRF'],
        'FRED': ['FRED'],
        'PUMA': ['PUMA'],
        'MONCLER': ['MONCLER'],
        'GUCCI': ['GUCCI'],
        'PRADA': ['PRADA'],
        'LV': ['לואי']}
# Add more special words and their options as needed


    # Iterate over each special word
    for key, options in special_words.items():
        # Iterate over each option for the special word
        for option in options:
            # Search for the option in the text
            if re.search(option, text, re.IGNORECASE):
                # If the option is found, return the corresponding key
                logger.info(f"Special word '{key}' found in the text.")
                return key
            # else:
                # logger.debug("No special words found in the text.")
    # If no match is found, return None
    return None

def create_csv(path, name):
    with open(path + name, 'x', newline='') as f:
        header = ['uploaded time', 'title', 'price', 'product id' ,'link', 'next url', 'affiliate_link', 'id', 'images', 'path',
                  'msg content']
        writer = csv.writer(f)
        writer.writerow(header)
# Rename and Move
def renameAndMoveFiles(directory_name):
    for item in os.listdir(handle_fd):
        try:
            if item[len(item) - 3:] == 'mp4': shutil.move(handle_fd + item, os.path.join(parent_dir, directory_name, item))
            else: shutil.move(handle_fd + item, os.path.join(parent_dir, directory_name, item))
        except: logger.error(f'Cannot move from\t {handle_fd + item} to {parent_dir + directory_name}')
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
def get_orig_price(my_url):
    try:
        uClient = uReq(my_url)
        page_html = uClient.read()
        uClient.close()
        page = bs4.BeautifulSoup(page_html, "html.parser")
        p = 'initial price'
        scripts = page.find_all('script')
        for script in scripts:
            txt = script.text

            m = re.search(r'"ogTitle":"([^"]+)"', txt)

            if m:
                og_title = m.group(1)

                # Now, extract the price from the ogTitle
                # Assuming the price format is "number currency_symbol"
                # Here, we're assuming that the price appears before the currency symbol
                price_match = re.search(r'(\d+(\.\d+)?)\s*₪', og_title)

                if price_match:
                    p = float(price_match.group(1))
                    logger.debug(f"Product price in page is: {p} in dollar {int(p/3.8)}")
                else:
                    print("Price not found in the ogTitle.")
    except:
        print("couldnt get price from page")
        p = 'error'

    return p
# Get Msg TXT
def getTitle(msg_content):
    try:
        match = re.search(r'\b[A-Za-z]+\b', msg_content)
        title = match.group() if match else None
        logger.debug(f'title is: {title}')
    except:
        title = 'no title'
    return title

def getPrice(next_url):
    price = ''
    try:
        info = aliexpress.get_products_details(next_url)
        logger.debug(info)
        for item in info:

            com = item.commission_rate
            i_price = item.target_sale_price
            logger.info("Original Price: %s, Commission Rate: %s", i_price, com)
            if item.target_sale_price:
                price = item.target_sale_price
            else:
                price = None

    except Exception as e:
        logger.debug(f'{e}')
        price = 'failed'

    return price
def getURL(msg_content):
    try:
        # logger.warning('before search ')
        url = re.search("(?P<url>https?://\S+)", msg_content).group("url")
        # logger.warning(f'after search url is: \n {url} ')

    except AttributeError:
        logger.warning(f"Error: AttributeError occurred. The regex pattern didn't match URL. {msg_content}")
        url = ''


    # # Provided string
    # provided_string = "https://s.click.aliexpress.com/e/_olT8f4wקישור"
    #
    # # Regular expression pattern to match the URL
    # url_pattern = r"https?://\S+"
    #
    # # Use re.search() to find the first occurrence of the URL in the string
    # match = re.search(url_pattern, url)
    #
    # if match:
    #     # Extract the URL from the match
    #     url = match.group(0)
    #     print(url)
    # else:
    #     print("No URL found in the provided string.")
    #
    # logger.debug(f'url is: {url}')

    return url
def getNextURL(url):
    if url.startswith('http://sale.dhgate') or \
            url.startswith('https://sale.dhgate') or \
                url == '':

            return 'no next url'
    try:
        if not url.startswith('https://s.click.aliexpress'):
            res = requests.get(url, allow_redirects=True, timeout=20).url.split('?')
        else:
            res = requests.get(url, allow_redirects=True, timeout=20).url

    except Exception as e:
        logger.warning("Error occurred:", e)
        res = 'no next url'

    # print(res)

    if isinstance(res, list):
        logger.debug(f'problem {res}')
        res = res[0]
        logger.debug(f'problem fixed {res}')
    #decode to simple url
    if res.startswith('https://star.aliexpr'):
        parsed_url = urlparse(res)
        query_params = parse_qs(parsed_url.query)
        redirect_url_encoded = query_params.get('redirectUrl', [''])[0]
        redirect_url_decoded = unquote(redirect_url_encoded)
        res = redirect_url_decoded
        clean_url = res.split('?')[0]
        res = clean_url
    logger.debug(f'next url is: {res}')

    if not res.__contains__('aliexpress'):
        logger.warning(f'next url response is not contain aliexpress string')
        res = 'no ali express link'



    return res
def setAffiliateLink(next_url, counters):
    affiliate_link = 'no link from AE'

    if next_url.__contains__('aliexpress'):
        resp = aliexpress.get_affiliate_links(next_url, timeout=30)
        logger.debug(f'AliExpress Response:\t{resp}')
        if hasattr(resp[0], 'promotion_link'):
            # if resp[0].promotion_link.startswith('https'):
            affiliate_link = resp[0].promotion_link
            counters['c_aff_links'] += 1

        else:
            affiliate_link = 'no promotion link in response\t'
            counters['c_no_link_ae'] += 1
            logger.error(resp)
            logger.error('[ALIEXPRESS Response] not valid for affiliate')

    return affiliate_link
# LOG Handling
def print_to_log(msg_id, p_id, title, price, url, affiliate_link, ids_obj, msg_time):
    orig_msg = title

    try:
        title = title.strip()[:18]
        title = '{:<15}'.format(title)

    except:
        title = 'no title'

    if affiliate_link is not None and affiliate_link.startswith('https://s.click.ali'):
        status = '[SUCCESS]'
    else:
        status = '[FAILED]'
        affiliate_link = 'no link received'


    logLine = f'{status }\t[ID:{msg_id}] "{title}" {price}$ [p_id: {p_id}] OG_URL: {url} Affiliated: {affiliate_link} [From:{msg_time}] Image files: + {str(ids_obj)}orig msg: + {str(orig_msg)}'

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
                         'zara')

def renameImg(full_file_name, new_id):


    try:
        # Split the full file path into directory path and file name
        directory, filename = os.path.split(full_file_name)

        # Split the filename into name and extension
        name, extension = os.path.splitext(filename)

        # Construct the new file name with the provided ID and original extension
        new_filename = f"{new_id}{extension}"

        # Construct the new full file path
        new_full_file_path = os.path.join(directory, new_filename)

        return new_full_file_path
    except:
        logger.error(f'Couldn\'t rename a file:  {full_file_name}')
        return None
def getMsgUploadedDate(message):
    return str(message.date.strftime("%b %d, %H:%M:%S"))
def calc_success_rate(c_main_items, no_link_received_cnt):
    try:
        affLinkCount = c_main_items - no_link_received_cnt
        temp = (affLinkCount / c_main_items) * 100
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
                          r'',r't.me', r'yupoo',r'store',r'lizaon',r'dsquared21',r'/gcp/',r'facebook', r'gmail.com', r'Catalogs', r'support'
    flag = False
    for pattern in patterns:
        match = re.search(pattern, url)
        # logger.debug(f'testing pattern: {pattern} is contain -> {url}')
        if match:
            logger.warning(f'Bad link: pattern:"{pattern}" found on {url}')
            flag = True
    if not flag: logger.debug(f'URL: {url} not blacklisted')
    return flag
def check_product_existence(product_url, counters):
    try:
        # Send a GET request to the product URL
        response = requests.get(product_url)
        # Parse the HTML content of the response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if the page title contains "Page Not Found"
        page_title = soup.title
        logger.debug(f'Page title is: {page_title}')
        if page_title is None:
            logger.debug(f'Page title is: None Assumi   ng its valid for aff')

        if page_title and "Page Not Found" in page_title.text:
            counters['c_not_found'] += 1
            return False  # Product does not exist if the title indicates page not found

        # Check if the div with the specified inner text is present
        not_available_div = soup.find('div', string="מצטערים, המוצר אינו זמין יותר.")
        if not_available_div:
            logger.warning(f'GOT מצטערים, המוצר אינו זמין יותר.')

            counters['c_not_found'] += 1
            return False  # Product does not exist if the div with the specified text is found

        return True  # Product exists if neither the title nor the div indicates product not found

    except Exception as e:
        logger.error("Error occurred:", e)
        counters['c_not_found'] += 1

        return False  # Assuming product doesn't exist if an error occurs
        pass
def get_product_id(next_url):
    try:
        p_id = int(re.search(r'(\d+)', next_url).group(1))
        logger.info(f'PRODUCT ID: {p_id}')
    except Exception as e:
        logger.warning(f'no p id {e}')
        p_id = 'no p id'
    return p_id


def try_send_media_without_saving(msg):
    print(msg.photo.file_reference)
    file_reference_bytes = msg.photo.file_reference
    file_reference_str = base64.b64encode(file_reference_bytes).decode('utf-8')
    caption = "Your caption here"
    TARGET_CHAT_ID = '-1001885191160'

    # context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=file_reference_str, caption=caption)

    sleep(1)

async def treat_all_media_group(grouped_msgs, counters):
    ids_obj = []
    msg = {}
    counters['c_main_items'] += 1
    if grouped_msgs[0].grouped_id == None:
        logger.debug(f'[ID:{grouped_msgs[0].id}] Group of None - continuing \n {grouped_msgs[0].grouped_id}')
        return False
    m_msg = None
    for msg in grouped_msgs:
        if msg.message != '':
            m_msg = msg
    if not m_msg:
        logger.warning(f'[ID:{grouped_msgs[0].id}] no m_msg in and media group is without a cation {grouped_msgs[0].grouped_id}')
        return
    if not m_msg:
        logger.warning(f'NO main mesage found in grouped : {msg.grouped_id}')
        return
    url = getURL(m_msg.message)
    if url == '' or url.__contains__('dhgate'):
        logger.warning(f'[ID:{m_msg.id}]URL is EMPTY - URL:{url} | returning')
        return
    next_url = getNextURL(url)
    p_id = get_product_id(next_url)
    new_url = f'https://he.aliexpress.com/item/{p_id}.html'


    if not next_url.__contains__('item'):
        logger.warning(f'next url doesn\'t contain item CONTINUE')
        return
    if not check_product_existence(url, counters):
        logger.warning(f'AE product but was deleted by AliExpress RETURNing')
        return
    else:
        logger.debug(f'link to ali express {new_url}')
        affiliate_link = setAffiliateLink(new_url, counters)
        price = getPrice(new_url)
        # successRate, affLinkCount = calc_success_rate(main_msg_id_counter, no_link_received_cnt)

    for msg in grouped_msgs:
        full_file_name = await client.download_media(msg.media, handle_fd, progress_callback=callback)
        renameImg(full_file_name, msg.id)
        ids_obj.append(msg.id)
    directory_name = 'ID_' + str(m_msg.id)
    # dir handling and move
    logger.debug(f'Valid message starting work on item')
    createItemDirectory(directory_name)
    renameAndMoveFiles(directory_name)
    messageTime = getMsgUploadedDate(m_msg)


    title = getTitle(m_msg.message)
    known_title = monitor_string(msg.message)

    if known_title:
        logger.info(f' title changed from {title} => {known_title}')
        title = known_title

    send_msg_to_csv(messageTime, p_id, csvFile, title, price, url, next_url, affiliate_link, m_msg.id,
                    str(ids_obj), parent_dir, directory_name, m_msg.message)
    print_to_log(m_msg.id,p_id, title, price, url, affiliate_link, ids_obj, messageTime)



def sender():
    TOKEN = '6465658634:AAE_ypyOvquENddt0_RS0y5vB8yYa8-HWtE'
    updater = Updater(TOKEN, use_context=True)
    updater.start_polling()
    updater.idle()


def check_id_in_csv(message, reader):
    flag = False
    for row in reader:
        if message.id == row['id']:
            logging.warning(f'[ID: {message.id}] EXISTS in csv!!')
            flag = True
    return flag

async def main():
    await client.start()
    if not await client.is_user_authorized():     # Ensure you're authorized - was ->    if await client.is_user_authorized() == False: !!!
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    # me = await client.get_me()
    entity = config['Telegram']['entity']
    my_channel = await client.get_entity(f'https://t.me/{entity}')
    logger.warning(f'Entity is: https://t.me/{entity}')

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0

    successRate = '0.00%'
    last_group_id = ''
    grouped_msgs = []

    # Initialize counters as a dictionary with specified keys
    counters = {
        'c_no_link_at_all': 0,
        'c_aff_links': 0,
        'c_no_link_ae': 0,
        'c_main_items': 0,
        'c_not_found': 0,
        'c_total_msgs': 0
    }

    create_csv(parent_dir, csvFile)


    while True:
        await print_current_import_status(counters['c_aff_links'], counters['c_main_items'], counters['c_no_link_ae'], offset_id,
                                          successRate, total_messages, counters['c_not_found'])
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

        # sender()
        # with open('E://Telegram_TEST//products.csv', newline='') as csvfile:
        #     reader = csv.DictReader(csvfile)

        for message in messages:
                #initials for all messages
                all_messages.append(message.to_dict())
                if last_group_id == '':
                    logger.debug(f'[ID:{message.id}] FIRST MSG grouped to msg_group={message.grouped_id} MSG_TXT: {message.message}')
                    grouped_msgs.append(message)
                    last_group_id = message.grouped_id
                    continue
                elif last_group_id == message.grouped_id:
                    grouped_msgs.append(message)
                    logger.debug(f'[ID:{message.id}] grouped to msg_group={message.grouped_id} MSG_TXT: {message.message}')
                    continue
                elif last_group_id != message.grouped_id:
                        last_group_id = message.grouped_id
                        await treat_all_media_group(grouped_msgs, counters)
                        sleep(timeout)
                        grouped_msgs = [message]
                #POST MESSAGE ACTIONS
                offset_id = messages[len(messages) - 1].id
                total_messages = len(all_messages)
                if total_count_limit != 0 and total_messages >= total_count_limit:
                    break
        logger.debug(f'sleeping test timeout in the end')
        sleep(timeout)

# async def remove_handle_fd_files():
async def print_current_import_status(c_aff_links, c_main_items, c_no_link_ae, offset_id, successRate, total_messages, c_not_found):
    logger.info(f'Current Offset ID: {offset_id}')
    logger.info(f'Total Messages Received : {total_messages}')
    logger.info(f'Message Counter : {c_main_items}')
    logger.info(f'Affiliate Links : {c_aff_links}')
    logger.info(f'Failed Links : {c_no_link_ae}')
    logger.info(f'Success Rate : {successRate}')
    logger.info(f'Page not Found : {c_not_found}\n')

config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]
with client:
    # remove parent if exists
    subprocess.call("C:\\Users\\Home\\PycharmProjects\\telegram-applications\\APP-aliexpress-brands\\telegram-import-from-group\\removeParentDir_ZARA.py",
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
                         'zara')


config = configparser.ConfigParser()
auth = initialConfig()
client = auth[0]
phone = auth[1]



with client:
    # remove parent if exists
    subprocess.call("C:\\Users\\Home\\PycharmProjects\\telegram-applications\\APP-aliexpress-brands\\telegram-import-from-group\\removeParentDir_ZARA.py",
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



