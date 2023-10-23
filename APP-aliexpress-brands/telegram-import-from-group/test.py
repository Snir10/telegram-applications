import configparser
import os

config_file_path = os.path.join("config_files", "news_uploader_config.ini")

c = configparser.ConfigParser()
c.read(config_file_path, encoding='utf-8')

try:
    chat_id = c['Channels']['chat_id']
    print(f"Chat ID: {chat_id}")
except KeyError:
    print("Error: 'Channels' section or 'chat_id' key not found in the configuration.")
    # Handle the error gracefully, e.g., provide a default chat_id or exit the script.
