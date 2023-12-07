import io
import re
import urllib3
from colorlog import ColoredFormatter
import requests
import configparser
import logging
import os
from time import sleep
import json
import csv
import os
import io
from PIL import Image
import subprocess
from telegram import InputMediaDocument

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


def print_welcome_csv_uploader():
    logger.info(f'\n##########################################################################################\n' +
                f'###############\t\tWelcome to CSV Uploader\t\t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\t                           \t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tCSV Path =>\t{src_dir_path}\\{csv_path[11:]}\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tItems =>\t{len(details)}\t\t\t\t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\t                           \t\t\t\t\t\t\t\t##############\n' +
                f'###############\t\tTelegram Upload Chat => {chat_id}\t\t\t\t\t##############\n' +
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
def open_csv():
    returned_list = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)  # Skip the header
        for row in datareader:
            folder_name = row[6]
            dir_path = src_dir_path + '\\' + folder_name

            images = os.listdir(folder_name)
            images_list = []
            # sleep(0.5)

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
        for csv_line in csv.DictReader(file):
            ids.append(str(csv_line['id']))
    return ids
def get_item(csvline):
    t = csvline[1].replace("\n", '')
    path = csvline[6]
    images = os.listdir(path)
    imgs_path_list = []
    for image in images:
        if image[-3:] == 'png' or image[-3:] == 'mp4' or image[-3:] == 'jpg':
            imgs_path_list.append(path + '\\' + image)
    return [csvline[4], t, path, imgs_path_list]

    # return csvLines
from PIL import Image
from moviepy.editor import VideoFileClip
import os

def compress_image(input_path, output_path, quality=85):
    try:
        img = Image.open(input_path)
        img.save(output_path, optimize=True, quality=quality)
        logger.info(f'Image compressed')
    except Exception as e:
        logger.error(f'Image compression failed: {str(e)}')

def compress_video(input_path, output_path, crf=23):
    try:
        clip = VideoFileClip(input_path)
        compressed_clip = clip.write_videofile(output_path, codec='libx264', fps=clip.fps, threads=4, preset='medium', bitrate=f'{crf}k')
        logger.info(f'Video compressed')
    except Exception as e:
        logger.error(f'Video compression failed: {str(e)}')

# def imagesToMedia(media_files, caption):
#     files = {}
#     media = []
#
#     for i, media_file in enumerate(media_files):
#         if os.path.isfile(media_file):
#             if media_file.endswith('.mp4'):
#                 compressed_video_path = f'video{i}_compressed.mp4'
#                 compress_video(media_file, compressed_video_path, crf=20)
#                 with open(compressed_video_path, 'rb') as file:
#                     name = f'video{i}.mp4'
#                     files[name] = file.read()
#                     media.append(dict(type='video', media=f'attach://{name}'))
#             else:
#                 compressed_image_path = f'photo{i}_compressed.png'
#                 compress_image(media_file, compressed_image_path, quality=70)
#                 with open(compressed_image_path, 'rb') as file:
#                     name = f'photo{i}.png'
#                     files[name] = file.read()
#                     media.append(dict(type='photo', media=f'attach://{name}'))
#         else:
#             print(f'Invalid media file path: {media_file}')
#
#     if caption is not None:
#         media[0]['caption'] = caption
#
#     return [media, files]

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

def sendMediaGroup(items, reply_to_message_id=None):
    logger.debug(f'Sending media group to telegram to {chat_id}')
    mediaGroupURL = f'https://api.telegram.org/bot{BOT}/sendMediaGroup'
    media, files = imagesToMedia(items, caption)

    # Split the large file into smaller parts
    chunk_size = 50 * 1024 * 1024  # 50MB
    chunks = [media[i:i + chunk_size] for i in range(0, len(media), chunk_size)]

    # Send each chunk as a separate media group itemQA meee




    media_group = []
    for i, chunk in enumerate(chunks):
        media_group.append(InputMediaDocument(media=chunk, caption=f"Part {i + 1}/{len(chunks)}: {caption}"))

    response = requests.post(
        mediaGroupURL,
        data={'chat_id': chat_id, 'media': json.dumps(media), 'reply_to_message_id': reply_to_message_id},
        files=files, verify=False, timeout=300)

    sleep(int(timeout))

    if response.status_code == 429:
        logger.debug(f'ID:{msg_id} [FAILED] with 429 -> RETRYING')
        response = requests.post(
            mediaGroupURL,
            data={'chat_id': chat_id, 'media': json.dumps(media), 'reply_to_message_id': reply_to_message_id},
            files=files, verify=False)
        logger.debug(f'RESPONSE: {response.text}')
    return response

def image_size_validation(paths):
    valid_imgs = []
    total_size = 0
    for file_path in paths:
        # Get the size of the file in bytes
        file_size_bytes = os.path.getsize(file_path)




        # Convert the size to megabytes
        file_size_megabytes = file_size_bytes / (1024 * 1024)
        if file_size_megabytes <= 50:
            # Print the file size in megabytes
            valid_imgs.append(file_path)
            logger.debug(f"File: {file_path}, Size: {file_size_megabytes:.2f} MB")
        else:
            logger.warning(f"REMOVED = File: {file_path}, Size: {file_size_megabytes:.2f} MB")
            continue

        total_size += file_size_megabytes

    return valid_imgs, total_size



# INSTAGRAM
def validate_last_id():
    if id == c['Telegram']['last_uploaded_id']:
        logging.info(f'### arrived to destination ID: {id} ###')
        sleep(10)
        exit(0)
# c = configparser.ConfigParser()
# c.read("config_files'\\'news_uploader_config.ini", encoding='utf-8')
config_file_path = os.path.join("config_files", "news_uploader_config.ini")
c = configparser.ConfigParser()
c.read(config_file_path, encoding='utf-8')

chat_id = c['Channels']['chat_id']
chat_id_2 = c['Channels']['chat_id_2']
src_dir_path = c['Telegram']['src_dir_path']
timeout = c['Telegram']['timeout']
logLevel = c['Telegram']['log_level']
csv_name = c['Telegram']['csv']
BOT = c['Bots']['BOT']
csv_path = src_dir_path + f'\\{csv_name}'

successRate, errorRate, instaCounter, noLinkRate = 0, 0, 0, 0

logger = logger_init()
details = open_csv()
print_welcome_csv_uploader()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

x = '️🧡🧡💛💚💚🤍🖤💜💙🤎❤️❤️❤️‍‍🔥💓💞❣️️💗💘💝'
dollar = '💲'
vi = '✔'
failed_imported_products_counter = 0
caption = 'https://t.me/only_sex_videos_stock\nhttps://t.me/only_girls_videos'

ids = get_ids_from_csv()


with open(csv_path, encoding='utf-8') as csv_file:
    for line in csv.DictReader(csv_file):
        valid_images = []
        csvLine = get_item(list(line.values()))
        folder_path, images_path_list, msg_id = csvLine[2], csvLine[3], csvLine[0]
        if not images_path_list:
            logger.warning(f'[ID:{msg_id}] IMGs path list is {images_path_list} Moving to next ID')
            continue
            #TODO - all 50 mb here must have a solution
        valid_files, total_files_size = image_size_validation(images_path_list)

        if total_files_size > 50:
            logger.warning(f'[ID:{msg_id}] Total size is: {total_files_size} Tring more than 50Mb File')
            continue

        if msg_id.isdigit():
            logger.debug(f'[ID:{msg_id}] IMGs path list is {valid_files} ')
            try:
                resp = sendMediaGroup(items=valid_files)
            except:
                logger.error(f'media group failed ID:{msg_id}')
                resp = 'No Respone'
            if resp.status_code == 200:
                successRate += 1
                msg = f'[ID:{msg_id}] [SUCCESS] {successRate}/{errorRate + successRate}\t\t' \
                      f'images={len(valid_images)}'
                # Remove non-ASCII characters
                clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg)
                logger.info(clean_msg)
            else:  # NOT 200

                errorRate += 1
                msg = f'[ID:{msg_id}] [FAILED] {errorRate}/{errorRate + successRate} ' \
                      f' ERROR -> status:{resp.status_code} {resp.text}'
                logger.error(msg)  # NOT 200
        else:
            noLinkRate += 1
            logger.warning(f"skipping failure item [ID:{id}] Images list: {images_path_list} ")
            x = f'[ID:{msg_id}] [FAILED] {noLinkRate}\t\tlink isn\'t containing s.click\t\t'
            logger.warning(x)

'''     FINISH      '''
logger.warning(f'\nFINISHED - Failed Products Counter: {failed_imported_products_counter} Products')
logger.warning(f'\nFINISHED - Successfully uploaded: {successRate} Products')
logger.warning(f'\nFINISHED - Failed to Upload: {errorRate} Products')
logger.info('\nFINISHED - All Products Uploaded Successfully !!!!')
