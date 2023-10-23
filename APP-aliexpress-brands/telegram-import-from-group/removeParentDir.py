import os
import shutil

parentDir = '/Users/user/Desktop/Backup/'



if os.path.exists(parentDir):
    print(os.path.exists(parentDir))
    shutil.rmtree(parentDir)

    # os.rmdir(parentDir)