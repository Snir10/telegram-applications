import configparser
import errno
import glob
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
    with open(parent +'\\'+ csv_f_name, 'a', encoding='utf-8', newline='') as f:
        data = [msgDate, title, price, link, nextUrl, affiliate_link, msg_id, images, parent +'\\'+ dir_name, msgContent]
        writer = csv.writer(f)
        writer.writerow(data)
def create_csv(path, name):
    path = path + '\\' + name
    with open(path, 'x', encoding='utf-8', newline='') as f:
        header = ['uploaded time', 'title', 'price', 'link', 'next url', 'affiliate_link', 'id', 'images', 'path',
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
# Get Msg TXT
def getTitle(msg_content):

    try:
        title = msg_content.split('-')[0]
        title = re.sub(r'^[💗\s]+|[💗\s]+$', '', title)
        # title = re.sub(r'[^a-zA-Z ]', '', title)
        logger.debug(f'cleaned emoji from title - {title}')

    except:
        logger.error(f'problem with title: -> {msg_content}')
        title = 'error'
    logger.debug(f'title is: {title}')
    # remove_emojis(title)

    # logger.debug(f'REMOVE EMOJIES: title is: {title}')
    return title
def getPrice(next_url):
    # try:
    #     price = str(re.findall(r"\$\d+(?:\.\d+)?|\d+(?:\.\d+)?\$", msg_content))[:-2]
    #     price = price.split('\\')[0][2::]
    #     if price.__contains__('€'): logger.warning(f'euro detected: € PRICE: {price}')
    #     price = price.replace('$', '')
    #     price = ('%.2f' % float(price))
    # except:
    #     logger.debug('price NOT detected')
    price = ''

    try:
        info = aliexpress.get_products_details(next_url)
        logger.debug(info)
        for item in info:
            logger.info("Original Price: %s, Commission Rate: %s", item.target_sale_price, item.commission_rate)
            price = item.target_sale_price + '$'

    except:
        logger.debug(f'no details')
        price = 'no pricee'

    # logger.debug(f'price is: {price}')


    return price
def getURL(msg_content):
    try:
        # logger.warning('before search ')
        #old method
        # url = re.search("(?P<url>https?://\S+)", msg_content).group("url")
        url = re.search(r'(?P<url>https?://\S+)', msg_content).group("url")

        # logger.warning(f'after search url is: \n {url} ')

    except AttributeError:
        logger.warning("Error: AttributeError occurred. The regex pattern didn't match anything. {url}")
        url = ''

    logger.debug(f'url is: {url}')

    return url
def getNextURL(url):
    # if url.startswith('http://sale.dhgate') or url.startswith('https://sale.dhgate') : return 'no next url'
    try:
        logger.debug('trying next url')
        res = requests.get(url).url.split('?')[0]
    except Exception as e:
        logger.warning("Error occurred:", e)
        res = 'no next url'
    logger.debug(f'next url is: {res}')



    return res
def setAffiliateLink(next_url, no_link_recived_cnt):
    try:
        if next_url.startswith('https://he.al') or next_url.startswith('https://www.aliexpress.us'):
            resp = aliexpress.get_affiliate_links(next_url, timeout=30)
            logger.debug(f'AliExpress Response:\t{resp}')
            if hasattr(resp[0], 'promotion_link'):
                if resp[0].promotion_link.startswith('https'):
                    affiliate_link = resp[0].promotion_link
                    # try:
                    #     info = aliexpress.get_products_details(next_url)
                    #     logger.debug(info)
                    #     for item in info:
                    #         logger.info("Original Price: %s, Commission Rate: %s", item.target_sale_price, item.commission_rate)
                    #
                    # except:
                    #     logger.debug(f'no details')
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
def print_to_log(msg_id, p_id,  title, price, url, affiliate_link, ids_obj, img_count, msg_time):
    orig_msg = title
    title = title.strip()[:18]
    title = '{:<15}'.format(title)
    if affiliate_link is not None and affiliate_link.startswith('https://s.click.ali'):
        status = '[SUCCESS]'
    else:
        status = '[FAILED]'
        affiliate_link = 'no link received'
    logLine = status + '\t' + \
              f'[ID: {msg_id}] \t' \
              f'[p_id: {p_id}] \t'\
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
    config.read("config_files/importer_config.ini")
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
    path = parentDir + '\\' + csv_file
    # logger.info(path)
    if os.path.exists(path):
        # logger.info('add msg to existing csv')
        send_msg_to_csv(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id,
                        str(ids_obj), parentDir, directory_name, msgContent)
    else:
        logger.info('creating csv')

        create_csv(parent_dir, csv_file)
        send_msg_to_csv(messageTime, csv_file, title, price, url, next_url, affiliate_link, last_id,
                        str(ids_obj), parent_dir, directory_name, msgContent)

def renameImg(full_file_name, id):
    try:
        if full_file_name[len(full_file_name) - 3:] == 'mp4':
            logger.debug(f'[ID:{id}] MP4 Detected {full_file_name}')
            try:
                os.rename(full_file_name, handle_fd + id + '.mp4')
                sleep(1.5)
            except:
                logger.info(
                    f'Failed to convert MP4 -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
        elif full_file_name[len(full_file_name) - 3:] == 'png':
            logger.debug(f'[ID:{id}] PNG Detected {full_file_name}')
            try:
                os.rename(full_file_name, handle_fd + id + '.png')
                sleep(1.5)
            except:
                logger.info(
                    f'Failed to convert PNG -> full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')

        else:
            try:
                logger.debug(f'[ID:{id}] PNG Detected {full_file_name}')
                os.rename(full_file_name, handle_fd + id + '.png')
            except:
                logger.info(
                    f'Failed to convert PNG ->full_file_name: {full_file_name}, handle_fd: {handle_fd}, id: {id}')
    except:
        logger.error(f'couldn\'t rename a file:  {full_file_name}')
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


def get_product_id(next_url):
    try:
        p_id = int(re.search(r'(\d+)', next_url).group(1))
        logger.info(f'PRODUCT ID: {p_id}')
    except Exception as e:
        logger.warning(f'no p id {e}')
        p_id = 'no p id'
    return p_id


async def main():
    await client.start()
    if not await client.is_user_authorized():     # Ensure you're authorized - was ->    if await client.is_user_authorized() == False: !!!
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    # me = await client.get_me()
    # entity = 'hypeallie'
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
    message_media = []
    main_msg_id_counter = 0
    img_counter = 0
    page_not_found_count = 0
    no_link_received_cnt = 0
    affLinkCount = 0
    successRate = '0.00%'
    last_main_msg = None
    directory_name = ''
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
            #initials for all messages
            all_messages.append(message.to_dict())
            msg_id = str(message.id)

            if hasattr(message, 'grouped_id'): logger.debug(f'[ID:{msg_id}]grouped_id is: {message.grouped_id}')

            if message.message == '':  # PHOTO \ VIDEO only
                img_counter += 1
                ids_obj.append(msg_id)
                try:
                    # logger.debug(f'[{msg_id}] downloading a file')
                    message_media.append(message.media)
                    full_file_name = await client.download_media(message.media, parent_dir, progress_callback=callback)
                    renameImg(full_file_name, msg_id)

                    # logger.debug(f'[{msg_id}] downloading a file')
                except FileMigrateError as e:
                    logger.error(f'[ID: {msg_id}] FileMigrateError continuing exception: {e}')
                    continue


            elif message.message != '' and os.listdir(handle_fd):  # TODO TITLE + PHOTO
                next_url = 'what?'
                title = 'what?'
                price = 'what?'

                print(f'lengh of messages is {message_media.__len__()}')
                message_media = []

                logger.debug(f'OS listdir of handling is: {os.listdir(handle_fd)}')
                main_msg_id_counter += 1 # counts each main product
                last_id = str(last_main_msg.id)
                directory_name = 'Item_' + last_id
                affiliate_link = 'initial value - bug'

                #dir handling and move
                createItemDirectory(directory_name)
                renameAndMoveFiles(directory_name)
                messageTime = getMsgUploadedDate(message)


                p_id = ''

                url = getURL(last_main_msg.message)
                if url != '' and not url.__contains__('dhgate'):
                    next_url = getNextURL(url)
                    if next_url.__contains__('aliexpress'):
                        p_id = get_product_id(next_url)
                        if is_blacklisted(next_url):
                            # await remove_handle_fd_files()
                            files = glob.glob(handle_fd)
                            logger.debug(f'files for remove - {files}')
                            for f in files:
                                # os.remove(f)
                                logger.warning(f'Not Removing but we want to remove this {handle_fd}/{f}')
                            logger.warning(f'continue next item {msg_id}')
                            continue

                        if not check_product_existence(next_url):
                            logger.warning(f'AE product but was deleted by AliExpress ')

                            page_not_found_count += 1
                            img_counter += 1

                            msg_to_csv(messageTime, csvFile, title, price, url, next_url, affiliate_link, last_id,
                                       str(ids_obj), parent_dir, directory_name, last_main_msg.message)
                            print_to_log(last_id,p_id, title, price, url, affiliate_link, ids_obj, img_counter, messageTime)
                            # logger.debug(f'continueing next msg ')
                            continue
                        else: #product exists on ali express
                            logger.debug(f'LINK to ali express {next_url}')
                            affiliate_link, no_link_received_cnt = setAffiliateLink(next_url, no_link_received_cnt)
                            successRate, affLinkCount = calc_success_rate(main_msg_id_counter, no_link_received_cnt)
                else:
                    logger.warning(f'something wrong with URL: {url} -> CONTINUE ')
                    continue


                # logger.debug(f'[ID:{msg_id}] TXT + Photo DETECTED => Title: {title} price: {price} URL: {url} images:{ids_obj.__len__()}')
                title = getTitle(last_main_msg.message)
                price = getPrice(next_url)

                msg_to_csv(messageTime, csvFile, title, price, url, next_url, affiliate_link, last_id,
                           str(ids_obj), parent_dir, directory_name, last_main_msg.message)
                img_counter += 1
                print_to_log(last_id,p_id, title, price, url, affiliate_link, ids_obj, img_counter, messageTime)



                ids_obj = []
                logger.debug(f'[{msg_id}] downloading a file')
                full_file_name = await client.download_media(message.media, parent_dir)
                logger.debug(f'[{msg_id}] downloading a file')
                renameImg(full_file_name, msg_id)
                ids_obj.append(msg_id)
                last_main_msg = message
                img_counter = 0


                #initial value for next round
            else:  #TODO handle fd empty + txt message = first message
                logger.debug(
                    f'[ID:{msg_id}][FIRST MSG] TXT + Photo - handle fd empty this should be in the FIRST message ')
                ids_obj.append(msg_id)
                last_main_msg = message
                img_counter = 0
                logger.debug(f'[{msg_id}] downloading a file')
                message_media.append(message.media)

                full_file_name = await client.download_media(message.media, parent_dir)
                logger.debug(f'[{msg_id}] ACTUALLY NOT THE FIRST MSG')
                renameImg(full_file_name, msg_id)
                createItemDirectory('Item_' + msg_id)


            #POST MESSAGE ACTIONS
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

        logger.debug(f'sleeping test timeout in the end')
        sleep(timeout)


# async def remove_handle_fd_files():



async def print_current_import_status(affLinkCount, main_msg_id_counter, no_link_recived_cnt, offset_id, successRate, total_messages, page_not_found_count):
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
    subprocess.call("C:\\Users\\Home\\PycharmProjects\\telegram-applications\\APP-aliexpress-brands\\telegram-import-from-group\\removeParentDir.py",
                    shell=True)

    parent_dir = config['Telegram']['parent_dir']
    handle_fd = config['Telegram']['handle_fd']
    csvFile = config['Telegram']['csv']
    cfg_id = config['Telegram']['importer_last_id']
    timeout = int(config['Telegram']['Timeout'])
    entity = config['Telegram']['entity']
    createParentDir()
    logger = logger_init()
    print_welcome_csv_importer(csvFile)
    createTempImgFolder('Products_Handling')
    aliexpress = createAliExpressInstance()
    client.loop.run_until_complete(main())
