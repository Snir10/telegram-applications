import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

logging.basicConfig(level=logging.DEBUG)

scheduler = BackgroundScheduler(jobstores={'default': MemoryJobStore()})
scheduler.start()

def my_job():
    print("Job executed!")

scheduler.add_job(my_job, 'interval', seconds=10, id='my_job')

# scheduler.print_jobs()


# Keep the script running
import time
time.sleep(100)
