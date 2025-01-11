import configparser
import os
import shutil


# Reading Configs
config = configparser.ConfigParser()

config.read("config_files/importer_config.ini")
# Setting configuration values
parentDir = config['Telegram']['parent_dir']


if os.path.exists(parentDir):
    print(os.path.exists(parentDir))
    shutil.rmtree(parentDir)

    # os.rmdir(parentDir)