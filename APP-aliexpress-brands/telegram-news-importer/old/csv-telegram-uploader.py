#Imports
from io import BytesIO
from time import sleep
from PIL import Image
from datetime import datetime
from colorlog import ColoredFormatter

import os
import csv
import json
import requests
import configparser
import logging
import random

# def upload_to_group(img , bot, chat_id):
#     file = {'photo': open(img, 'rb')}
#     response = requests.post(
#         'https://api.telegram.org/bot'+bot+'/sendPhoto?chat_id='+chat_id+'',
#         files=file)
#     return response #upload
# def send_message(text, bot, chat_id):
#     utl_req = 'https://api.telegram.org/bot' + bot + '/sendMessage'+'?chat_id=' + chat_id + '&text='+text
#     result = requests.get(utl_req)
#     print(result.text)
def open_csv(csv_path):
    returned_list = []
    with open(csv_path, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        list_iterator = next(iter(datareader))
        for row in datareader:

            item = row[0]
            price = row[1]
            link = row[4]
            folder_name = 'Item_' +row[6]
            folder_path = src_dir_path + folder_name
            id = row[6]

            images = os.listdir(folder_path)
            images_list = []

            for img in images:
                try:
                    images_list.append(folder_path+'/'+img)
                except:
                    print('coould not open this file --> '+'folder_path'+'/'+img)
                    pass

            returned_list.append(row)
        return returned_list
def send_media_group(chat_id, images, folder_path, caption='new message', reply_to_message_id=None):
        """
        Use this method to send an album of photos. On success, an array of Messages that were sent is returned.
        :param chat_id: chat id
        :param images: list of PIL images to send
        :param caption: caption of image
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: response with the sent message
        """
        files = {}
        media = []
        for i, img in enumerate(images):
            with BytesIO() as output:
                try:
                    Image.open(img).save(output, format='PNG')
                    output.seek(0)

                    name = f'photo{i}'
                    files[name] = output.read()
                    # a list of InputMediaPhoto. attach refers to the name of the file in the files dict
                    media.append(dict(type='photo', media=f'attach://{name}'))
                except:
                    logger.warning(f'ERROR: can not open --> {img} \t in {folder_path}')
        media[0]['caption'] = caption

        resp = requests.post(SEND_MEDIA_GROUP, data={'chat_id': chat_id, 'media': json.dumps(media), 'reply_to_message_id': reply_to_message_id}, files=files)
        return resp
def print_upload_response(resp, SUCCESS_RATE, ERROR_RATE, id, title, price, link):

    #time = datetime.now().strftime("%b %d, %H:%M:%S")
    title = title.strip()[:20]
    #make title fixed length
    title = '{:<15}'.format(title)

    # print statuses to logger
    if resp.status_code == 200:
        SUCCESS_RATE += 1
        x = f'[ID:{id}] [SUCCESS]' + ' ' + str(SUCCESS_RATE) + '/' + str(ERROR_RATE + SUCCESS_RATE) + '\t' +\
              title + '\t' +\
              price + '\t' +\
              link
        #print(x)
        logger.info(x)


        #TODO - save id to config #####
        # config = configparser.RawConfigParser()
        # config.read('config.ini')
        # config.set('Telegram', 'last_uploaded_id', id)
        # cfgfile = open('config.ini', 'w')
        # config.write(cfgfile, space_around_delimiters=False)  # use flag in case case you need to avoid white space.
        # cfgfile.close()
        ##########################


    elif resp.status_code == 429:
        ERROR_RATE += 1
        x = '[ERROR CODE:429 - please Retry send ID]' + ' ' +\
            str(SUCCESS_RATE) + '/' + str(ERROR_RATE + SUCCESS_RATE) + '\t' +\
              title + '\t' +\
              price + '\t' +\
              link
        #print(x)
        logger.error(x)

    else:
        ERROR_RATE += 1
        x = f'[ID:{id}]'+'[FAILED]' + \
            str(ERROR_RATE) + ' / ' + str(ERROR_RATE + SUCCESS_RATE) +\
            title + '\t' +\
            price + '\t' +\
            link + '\t' + \
            'ERROR -> ' +\
            'status:' + str(resp.status_code) +\
            +resp.text
        #print(x)
        logger.error(x)
    return SUCCESS_RATE, ERROR_RATE
def get_item(details):
    title = details[1]
    price = str(details[2])
    link = details[5]
    folder_path = src_dir_path + 'Item_' + details[6]
    images = details[7].split(',')
    id = details[6]

    images_path_list = []

    # image path list filler
    for image in images:
        image = image.replace("'", '')
        image = image.replace("[", '')
        image = image.replace("]", '')
        image = image.replace(" ", '')
        images_path_list.append(folder_path + '/' + image + '.png')


    return [id, title, price, link, folder_path, images_path_list]
def validate_last_id(id):
    if id == c['Telegram']['last_uploaded_id']:
        logging.info(f'### arrived to dest ID: {id} ###')
        sleep(10)
        exit(0)
def upload_all_products(details):
    SUCCESS_RATE = 0
    ERROR_RATE = 0

    for i in range(len(details)):

        list_of_product_details = get_item(details[i])

        id = list_of_product_details[0]
        title = list_of_product_details[1]
        price = list_of_product_details[2]
        link = list_of_product_details[3]
        folder_path = list_of_product_details[4]
        images_path_list = list_of_product_details[5]

        validate_last_id(id)

        x = '❤️🧡🧡💛💛💚💚🤍🖤💜💙🤎❤️❤️❤️‍🔥️‍🔥💓💓💞💞❣️❣️💗💘💝'
        dollar = '💲'
        nendh = '🤑💰💵💸💲$﹩＄💲'
        vi = '✔'
        title = title + ' ' + random.choice(x)

        if link.__contains__('click.aliexpress'):
            # manipulate price to pure float with 2 decimal digits
            if price.__contains__('$'):
                try:
                    price = price.strip().replace('$', '')
                    price = "{:.2f}".format(float(price))
                except:
                    print('no valid price')

            price = str(price)+dollar
            # caption text to send
            text = title[:20] + '\n\n' +\
                   price + '\n\n\t👇🏻\t\t\tBuy it now\t\t\t👇🏻\t\t\n' +\
                   link + '\n' +\
                   str(SUCCESS_RATE)+'/'+str(SUCCESS_RATE + ERROR_RATE)

            resp = send_media_group(chat_id=chat_id, images=images_path_list, folder_path=folder_path, caption=text)

            z = print_upload_response(resp, SUCCESS_RATE, ERROR_RATE, id, title, price, link)
            SUCCESS_RATE = z[0]
            ERROR_RATE = z[1]

            timeout = int(c['Telegram']['timeout'])

            sleep(timeout)

        else:
            time = str(datetime.now().strftime("%b %d, %H:%M:%S"))
            ERROR_RATE += 1

            x = f'[ID:{id}]'+'[FAILED]' + str(ERROR_RATE) + ' / ' + str(ERROR_RATE + SUCCESS_RATE) + '\t' +\
                  title + '\t' +\
                  price + '\t' +\
                  link + '\t' +\
                  'link isnt containing s.click' + '\t'
            logger.warning(x)
def print_welcome_csv_uploader(csv_path, len):
    print('##########################################################################################')
    print('###############\t\tWelcome to CSV Uploader\t\t\t\t\t\t\t\t\t##############')
    print(f'###############\t\tCSV file =>\t{csv_path[11:]}\t\t\t\t##############')
    print(f'###############\t\tItems Count =>\t{len}\t\t\t\t\t\t\t\t\t##############')

    print('##########################################################################################\n')
def logger_init():
    # logger = logging.getLogger('my_module_name')
    # logger.setLevel(level=logging.INFO)
    # fh = logging.StreamHandler(sys.stdout)
    # fh_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
    # fh.setFormatter(fh_formatter)
    # logger.addHandler(fh)
    #
    # fh = logging.FileHandler('uploader.log')
    # fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    # fh.setLevel(logging.DEBUG)
    # logger.addHandler(fh)

    logger = logging.getLogger('my_module_name')
    logger.setLevel(level=logging.INFO)
    LOGFORMAT = "%(log_color)s %(asctime)s %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"

    fh = logging.StreamHandler()
    formatter = ColoredFormatter(LOGFORMAT)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    fh = logging.FileHandler('../logs/importer.log')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    return logger
def manipulate_msg_text_for_upload(list_of_product_details, SUCCESS_RATE, ERROR_RATE):


    title = list_of_product_details[1]
    price = list_of_product_details[2]
    link = list_of_product_details[3]
    folder_path = list_of_product_details[4]
    images_path_list = list_of_product_details[5]
    msg_id = list_of_product_details[0]

    x = '️🧡🧡💛💛💚💚🤍🖤💜💙🤎❤️❤️❤️‍🔥️‍🔥💓💓💞💞❣️❣️💗💘💝'
    dollar = '💲'
    vi = '✔'
    title += ' ' + random.choice(x)

    if link.__contains__('click.aliexpress'):
        # manipulate price to pure float with 2 decimal digits
        if price.__contains__('$'):
            try:
                price = price.strip().replace('$', '')
                price = "{:.2f}".format(float(price))
            except:
                print('no valid price')

        price = str(price) + dollar
        # caption text to send
        text = title[:20] + '\n\n' + \
               price + '\n\n\t👇🏻\t\t\tBuy it now\t\t\t👇🏻\t\t\n' + \
               link + '\n' + \
               str(SUCCESS_RATE) + '/' + str(SUCCESS_RATE + ERROR_RATE)

        resp = send_media_group(chat_id=chat_id, images=images_path_list, folder_path=folder_path, caption=text)



        z = print_upload_response(resp, SUCCESS_RATE, ERROR_RATE, msg_id, title, price, link)
        SUCCESS_RATE = z[0]
        ERROR_RATE = z[1]


    else:
        ERROR_RATE += 1
        x = f'ID: {msg_id}' + str(ERROR_RATE) + '/' + str(ERROR_RATE + SUCCESS_RATE) + '\t' + \
            'link isnt containing s.click' + '\t\t' + \
            title + '\t' + \
            price + '\t' + \
            link + '\t'
        logger.warning(x)

    return [SUCCESS_RATE, ERROR_RATE]


def upload_product_by_id(msg_id, SUCCESS_RATE, ERROR_RATE):
    with open(csv_path) as csv_file:
        for line in csv.DictReader(csv_file):

            if line is not None and line['id'] == msg_id:
                values = list(line.values())
                list_of_product_details = get_item(values)

                rates = manipulate_msg_text_for_upload(list_of_product_details, SUCCESS_RATE, ERROR_RATE)
                SUCCESS_RATE = rates[0]
                ERROR_RATE = rates[1]

    return [SUCCESS_RATE, ERROR_RATE]


#start

c = configparser.ConfigParser()
c.read("config_files/news_uploader_config.ini")

logger = logger_init()


bot_id = c['Telegram']['bot_id']
SEND_MEDIA_GROUP = c['Telegram']['media_group']
chat_id = c['Telegram']['chat_id']
src_dir_path = c['Telegram']['src_dir_path']
csv_path = c['Telegram']['products_csv_path']
timeout = c['Telegram']['timeout']

scs_rate = 0
err_rate = 0

#csv to 2d list
details = open_csv(csv_path)


print_welcome_csv_uploader(csv_path, len(details))


#upload_all_products(details)


with open(csv_path) as csv_file:
    list_of_ids = []
    for line in csv.DictReader(csv_file):
        list_of_ids.append(str(line['id']))

for msg_id in list_of_ids:
    rates = upload_product_by_id(msg_id, scs_rate, err_rate)
    #counters update
    scs_rate = rates[0]
    err_rate = rates[1]
    sleep(int(timeout))
