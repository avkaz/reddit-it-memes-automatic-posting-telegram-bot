import logging
import schedule
import telebot
import time
import os
from datetime import datetime, timedelta
from config import *
from io import BytesIO


# Initializing bot
bot = telebot.TeleBot('6754766101:AAFilPdvF2WNci6E6g74sC7izSWy63iuN30')

# Defining target channel ID and status channel ID
target_channel_id = '-1002115819190'
status_chat_id = '-1001999613821'
code_review_video_id = '-1002226599559'

# Define constants for time intervals
MORNING_TIMES = [
    convert_to_local_time(8, 45),
]

EVENING_TIMES = [
    convert_to_local_time(15, 45),
    convert_to_local_time(20, 45),
]

# Get the current working directory
current_directory = os.getcwd()

# Specify the subdirectory for media storage (one directory back)
media_subdir = os.path.join(current_directory, '..')

# Construct the full path to the media directory
media_dir = os.path.join(media_subdir, 'media')

# Ensure the directory exists for media storage
if not os.path.exists(media_dir):
    os.makedirs(media_dir)

# Set the maximum number of attempts for posting
MAX_ATTEMPTS = 3

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def post_to_channel():
    try:
        logging.info("Attempting to post to the channel...")
        for attempt in range(1, MAX_ATTEMPTS + 1):
            meme = db_handler.get_meme_to_channel()
            if not meme:
                logging.info("No meme found to post.")
                break
            if post_single_meme(meme):
                break
            logging.warning(f"Error posting current meme (attempt {attempt}/{MAX_ATTEMPTS}). Trying another meme.")
        else:
            logging.error(f"Failed to post meme after {MAX_ATTEMPTS} attempts.")
    except Exception as e:
        logging.error(f"Error posting to channel: {e}")


def post_single_meme(meme):
    try:
        if not (meme.file_id or meme.url):
            logging.warning("Meme has no file_id or URL. Cannot post.")
            mark_to_delete(meme)
            return False

        media = meme.file_id if meme.file_id else download_media_to_channel(meme.url)

        if media:
            caption = meme.my_comment
            send_media_to_channel(media, meme, caption)
            db_handler.mark_as_published(meme.id, True)
            logging.info("Post successful.")
            return True

        logging.warning("Error posting meme: Media not found.")
        mark_to_delete(meme)
        return False
    except Exception as e:
        logging.error(f"Error posting meme: {e}")
        mark_to_delete(meme)
        return False


def send_media_to_channel(media_path, meme, caption=None):
    logging.info("Started sending media to channel")
    try:
        if media_path.lower().endswith(('mp4', 'mov', 'avi')):
            send_method = bot.send_video
        else:
            send_method = bot.send_photo

        if meme.rank == 99999:
            logging.info("Trying to find file in data storage")
            file_data = None
            for attempt in range(3):
                try:
                    blob = bucket.blob(media_path)
                    logging.info(f"Attempt {attempt + 1}: Downloading file from data storage")
                    file_data = blob.download_as_bytes()
                    logging.info("File successfully found and downloaded")
                    break
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        logging.info("Retrying after 3 seconds...")
                        time.sleep(3)
                    else:
                        logging.critical("All attempts to download the file have failed")
                        return

            if file_data:
                if caption:
                    send_method(target_channel_id, BytesIO(file_data), caption=caption)
                else:
                    send_method(target_channel_id, BytesIO(file_data))
                blob.delete()
        else:
            with open(media_path, 'rb') as file:
                if caption:
                    send_method(target_channel_id, file, caption=caption)
                else:
                    send_method(target_channel_id, file)
                send_video_to_dm(media_path)
    except Exception as e:
        logging.error(f"Error sending media to channel: {e}")

def send_video_to_dm(media_path):
    try:
        final_video_path = create_video_with_overlay(media_path)

        with open(final_video_path, 'rb') as file:
            video_bytes = BytesIO(file.read())
            bot.send_video(code_review_video_id, video=video_bytes)

        os.remove(final_video_path)

    except Exception as e:
        logging.error(f"Error sending video to DM: {e}")


def delete_old_memes_from_db():
    try:
        filter_date = datetime.today() - timedelta(days=30)
        unapproved_removed, posted_removed = db_handler.remove_old_memes(filter_date)

        if unapproved_removed > 0:
            logging.info(f"Deleted {unapproved_removed} unapproved memes from the database.")
        else:
            logging.info("No unapproved memes found to delete.")

        if posted_removed > 0:
            logging.info(f"Deleted {posted_removed} posted memes from the database.")
        else:
            logging.info("No posted memes found to delete.")

        bot.send_message(
            chat_id=status_chat_id,
            text=f'Deleting of memes completed successfully. {unapproved_removed} unapproved memes and {posted_removed} posted memes were removed from the database.'
        )
    except Exception as e:
        logging.error(f"Error deleting old memes from the database: {e}")


def schedule_posting():
    logging.info("Started scheduling")
    logging.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    for time_interval in MORNING_TIMES:
        schedule.every().day.at(time_interval).do(post_to_channel).tag('morning')

    for time_interval in EVENING_TIMES:
        schedule.every().day.at(time_interval).do(post_to_channel).tag('evening')

    schedule.every().day.at(convert_to_local_time(3, 00)).do(delete_old_memes_from_db).tag('midnight')

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    schedule_posting()
