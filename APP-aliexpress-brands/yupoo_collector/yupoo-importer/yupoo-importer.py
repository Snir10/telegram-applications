import os
import csv
import re
import requests
from urllib.parse import urljoin
from time import sleep
from aliexpress_api import AliexpressApi, models
from colorlog import ColoredFormatter
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from selenium import webdriver
import logging
def logger_init():
    log = logging.getLogger('my_module_name')
    log.setLevel(level=logging.DEBUG)

    LOG_FORMAT = "%(log_color)s %(asctime)s %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"

    fh = logging.StreamHandler()
    formatter = ColoredFormatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    return log
def createAliExpressInstance():
    return AliexpressApi('34061046', '3766ae9cf22b81c88134fb56f71eb03c', models.Language.EN, models.Currency.EUR,
                         'sn2019')
def get_id():
    #TODO - fix return with log 2 options
    match = re.search(pattern, title)
    if match:
        unique_id = match.group()
        log.debug(f'ID: {unique_id}')
        return unique_id
    else:
        log.warning(f'NO ID - title is: {title}')

        return 'no ID'
def setAffiliateLink(next_url, no_link_recived_cnt, link_received_cnt):
    if next_url.__contains__('aliexpress'):
        log.debug(f'sending link to AE {next_url}')

        resp = aliexpress.get_affiliate_links(next_url)

        log.debug(f'Received AliExpress Response:\t{resp}')

        if resp and hasattr(resp[0], 'promotion_link') and resp[0].promotion_link.startswith('https'):
            affiliate_link = resp[0].promotion_link
            link_received_cnt += 1
        else:
            affiliate_link = 'Failed to convert Ali Express link'
            log.debug(f'No Link from AE{resp}')
            no_link_recived_cnt += 1
    else:
        affiliate_link = 'No Ali Express link detected'
        log.warning(f'Bad link -> {next_url}')
        no_link_recived_cnt += 1
    return affiliate_link, no_link_recived_cnt, link_received_cnt
def download_album_images(album_folder, album_url, image_divs):
    images = []

    image_divs = image_divs[:1]

    try:
        log.debug(f"Going to download {len(image_divs)} images")
        for i, image_div in enumerate(image_divs, 1):
            img_tag = image_div.find_element(By.CSS_SELECTOR, 'img')
            image_url = img_tag.get_attribute('src')
            parsed_url = urljoin(album_url, image_url)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                'Referer': album_url}
            image_name = f"image_{i}.png"
            images.append(image_name)
            response = requests.get(parsed_url, headers=headers)
            response.raise_for_status()
            with open(os.path.join(album_folder, image_name), 'wb') as f:
                f.write(response.content)
            log.debug(f"Downloaded image: {album_folder}/{image_name}")
        log.debug(f"all images: {images}")
    except:
        log.warning(f"Something went wrong {id} {link} {title} ")


    return images
def get_link_match(subtitle_content):
    link_match = re.search(r'(https?://\S+)', subtitle_content)
    # log.debug(f'Link match: {link_match}')

    return link_match
def get_price(title):
    try:
        price = re.search(r'\d+(\.\d+)?\$', title).group()
    except:
        price = 'no price'
    log.debug(f'price: {price}')

    return price
def get_image_divs(driver):
    image_divs = driver.find_elements(By.CSS_SELECTOR, 'div.showalbum__children.image__main')
    return image_divs
def get_subtitle_content(driver):
    subtitle_content = driver.find_element(By.CSS_SELECTOR, 'div.showalbumheader__gallerysubtitle.htmlwrap__main').text
    return subtitle_content
def get_title(driver):
    title = driver.find_element(By.CSS_SELECTOR, 'span.showalbumheader__gallerytitle').text
    log.debug(f'Title: {title}')
    return title
def create_album_fd(album_index, dest_fd):
    album_folder = os.path.join(dest_fd, f'album_{album_index}')
    os.makedirs(album_folder, exist_ok=True)
    return album_folder
def get_album_urls():
    log.info(f'Processing URL: {url}')

    log.debug(f"Opening main albums url: {main_urls}")
    driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)
    driver.get(url)
    album_links = driver.find_elements(By.CSS_SELECTOR, 'div.showindex__children a')
    log.info(f"Albums Count: Found {len(album_links)} Albums !")
    album_urls = [album_link.get_attribute('href') for album_link in album_links]
    log.debug(f"Quitting main albums url: {url}")
    driver.quit()
    return album_urls
def print_to_log(id, images, link, price, resp, title, no_link, link_received):
    log.info(
        f"[ID:{id}] [{link_received}/{no_link + link_received}] [IMGs:{len(images)}]  {title} Price: {price} \tlink: {link}\tAff-link: {resp} \tno link counter: {no_link} ")
def link_validation(link_match):
    if link_match:  # if no link at all, or no s.click will continue next item
        log.debug(f'Found link: {link_match}')
        return link_match.group(1)
    else:
        log.warning(f"Moving to next item since val link_match={link_match}")
        return False
def resp_validation(r):
    if not r.startswith('https://s.click.aliexpr'):
        log.warning(r)
        return False
    else:
        return True
def print_counters():
    log.info("Processed all albums.")
    log.info(f"Counter for albums with no link at all: {counter_no_link_at_all}")
    log.info(f"Counter for albums with no link received from AE: {counter_no_link_recivied_from_AE}")
    log.info(f"Counter for valid products: {valid_products_counter}")
def get_pages_count():
    # previous use -
    # main_urls = [f'https://taozi140.x.yupoo.com/albums?page={i}' for i in range(1, 10)]
    # main_urls = ['https://tianlong980120.x.yupoo.com/albums']

    log.info(f'Site ID = {site_id} ')
    log.info(f'Link = {main_url_templete} ')

    d = webdriver.Chrome(options=options, executable_path=chromedriver_path)
    d.get(main_url_templete)
    element = d.find_element(By.CSS_SELECTOR, 'form.pagination__jumpwrap span')
    text = element.text
    match = re.search(r'\d+', text)
    if match:
        number = int(match.group())
        log.warning(f'we found {number} pages')
        d.quit()
        return number
    else:
        log.warning(f'no pages found - {main_url_templete}')
        d.quit()

        return None
# CSV
def create_csv():
    headers = ['ID', 'title', 'price', 'next url', 'aff link', 'album path', 'album items']

    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
def append_to_csv():

    row_data = [id, title, price, link, resp, album_folder, images]
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)
    log.debug('csv updated')




log = logger_init()




# site_id = '767867590'
# site_id = 'aliexpressshop'
site_id = 'zxcasdqwe888'
# site_id = '2621656567'



# pattern = r'TL\d{4}'  # Pattern for "AN" followed by four digits


pattern = r'AN\d{4}'  # Pattern for "AN" followed by four digits

aliexpress = createAliExpressInstance()
options = Options()
options.add_argument('--headless')
chromedriver_path = 'c:\\chromedriver.exe'
service = Service(chromedriver_path)
noLinkCounter, link_received_cnt = 0, 0

counter_no_link_at_all = 0
counter_no_link_recivied_from_AE = 0
valid_products_counter = 0

main_url_templete = f'https://{site_id}.x.yupoo.com/albums?page='

# def extract_hidden_number(string):



# def get_main_urls():



# main_urls = get_main_urls()
pages_count = get_pages_count()
main_urls = [f'{main_url_templete}{i}' for i in range(1, pages_count)]



for index, url in enumerate(main_urls):
    album_urls = get_album_urls()
    destination_folder = f'c:\\try\\{site_id}_page_{index}'
    csv_path = f'c:\\try\\{site_id}_page_{index}.csv'
    create_csv()

    for album_index, album_url in enumerate(album_urls, 1):
        if album_index % 10 == 0:
            log.info(f"Processed {album_index} albums.")
            print_counters()

        driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)
        try:
            driver.get(album_url)
            title = get_title(driver)
            subtitle_content = get_subtitle_content(driver)
            image_divs = get_image_divs(driver)
            id = get_id()
            price = get_price(title)
            link_match = get_link_match(subtitle_content)
            link = link_validation(link_match)

            album_folder, images = 'error', 'error'


            if not link:
                counter_no_link_at_all += 1
                resp = 'no link 2323'

                append_to_csv()
                continue

            resp, no_link_count, link_received_cnt = setAffiliateLink(link, noLinkCounter, link_received_cnt)
            if not resp_validation(resp):
                counter_no_link_recivied_from_AE += 1
                append_to_csv()
                continue

            valid_products_counter += 1

            album_folder = create_album_fd(album_index, destination_folder)
            images = download_album_images(album_folder, album_url, image_divs)
            print_to_log(id, images, link, price, resp, title, no_link_count, link_received_cnt)
            append_to_csv()
        except StaleElementReferenceException:
            log.error(f"Skipping album {album_index} due to stale element reference")
        driver.quit()

    if (index + 1) * 50 >= len(main_urls): print_counters()
