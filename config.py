import requests
import pytz
from datetime import datetime, timedelta
from mimetypes import guess_extension
from db_handler import DBHandler
import os
import tempfile
import logging
import firebase_admin
from firebase_admin import credentials, storage
from PIL import Image as PILImage
from PIL import Image, ImageDraw, ImageFont
import subprocess
import shutil 
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get the current working directory
current_directory = os.getcwd()

DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')  
DB_PORT = os.environ.get('DB_PORT')       
DB_NAME = os.environ.get('DB_NAME')

# Construct the PostgreSQL database URL
db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Correct the DBHandler initialization
db_handler = DBHandler(db_url)


#initalalizing firebase
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'codereview-22c86.appspot.com'})

bucket = storage.bucket()


def download_media_to_channel(url):
    try:
        response = requests.get(url)
        content_type = response.headers.get('content-type')

        if response.status_code == 200 and content_type:
            file_extension = guess_extension(content_type.split('/')[1])

            # Use tempfile to generate a unique temporary file name
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as media:
                media.write(response.content)

            return media.name

    except Exception as e:
        logging.error(f"Error downloading media from {url}: {e}")

    return None


def mark_to_delete(message):
    try:
        meme = db_handler.get_meme_to_channel()

        if meme:
            meme_id = meme.id
            db_handler.mark_as_checked(meme_id, True)
            db_handler.mark_as_approved(meme_id, False)

    except Exception as e:
        logging.error(f"Error marking meme to delete: {e}")



def convert_to_local_time(moscow_hour, moscow_minute):
    try:
        # Define the Moscow timezone
        moscow_tz = pytz.timezone('Europe/Moscow')

        # Get the current time in Moscow
        moscow_time = datetime.now(moscow_tz).replace(hour=moscow_hour, minute=moscow_minute, second=0, microsecond=0)

        # Convert Moscow time to local time
        local_tz = pytz.timezone('Europe/Berlin')
        local_time = moscow_time.astimezone(local_tz)

        # Format the local time as string in %H:%M format
        formatted_time = local_time.strftime('%H:%M')

        return formatted_time

    except Exception as e:
        logging.error(f"Error converting to local time: {e}")
        return None

def download_random_video(folder_name='video_generation', output_directory='output_videos/'):
    logging.info('Starting to download video')
    blobs = list(bucket.list_blobs(prefix=folder_name))

    if not blobs:
        logging.error("No files found in the specified folder.")
        return None

    random_video = random.choice(blobs)

    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Construct the full path including filename
    video_filename = os.path.basename(random_video.name)
    destination_path = os.path.join(output_directory, video_filename)

    logging.info(f"Downloading to: {destination_path}")

    try:
        # Download the video file
        random_video.download_to_filename(destination_path)
        logging.info(f"Downloaded {random_video.name} to {destination_path}")
        return destination_path
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None

def preprocess_image(photo_path, output_path, video_width, target_width_percentage):
    with PILImage.open(photo_path) as img:
        original_width, original_height = img.size
        target_width = int(video_width * target_width_percentage)
        aspect_ratio = original_height / original_width
        target_height = int(target_width * aspect_ratio)
        resized_img = img.resize((target_width, target_height), PILImage.LANCZOS)
        resized_img.save(output_path)
        print(f"Preprocessed image dimensions: width={target_width}, height={target_height}")
        return target_width, target_height

def preprocess_icon(icon_path, output_path, video_width, target_width_percentage):
    icon_image = PILImage.open(icon_path)
    target_width = int(video_width * target_width_percentage)
    aspect_ratio = icon_image.height / icon_image.width
    target_height = int(target_width * aspect_ratio)
    resized_icon = icon_image.resize((target_width, target_height), PILImage.LANCZOS)
    resized_icon.save(output_path)

def create_video_with_overlay(meme_path):
    logging.info('Video generation started')

    video_path = download_random_video()
    if video_path is None:
        logging.error("Failed to download a video. Exiting.")
        return None
    
    # Check if ffprobe is available
    if shutil.which('ffprobe') is None:
        logging.error("ffprobe is not installed or not found in PATH.")
        return None

    icon_png_path = 'icons8-telegram-50.png'

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,duration', '-of',
             'csv=p=0', video_path],
            capture_output=True, text=True, check=True)
        video_info = result.stdout.strip().split(',')
        video_width = int(video_info[0])
        video_height = int(video_info[1])
        video_duration = float(video_info[2])
        logging.info(f"Video dimensions: width={video_width}, height={video_height}")
    except Exception as e:
        logging.error(f"Error loading video: {e}")
        return None

    output_directory = 'output_videos/'
    os.makedirs(output_directory, exist_ok=True)

    preprocessed_image_path = os.path.join(output_directory, 'preprocessed_overlay_image.jpg')
    image_width, image_height = preprocess_image(meme_path, preprocessed_image_path, video_width, 0.9)
    logging.info(f"Preprocessed image dimensions: width={image_width}, height={image_height}")

    preprocessed_icon_path = os.path.join(output_directory, 'icon8-telegram.png')
    preprocess_icon(icon_png_path, preprocessed_icon_path, video_width, 0.06)

    font_size = int(video_width * 0.05)
    font_path = "mechanical.otf"

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        logging.warning("Specified font not found. Using default font.")
        font = ImageFont.load_default()

    text = "coode_review"
    text_image = Image.new('RGBA', (video_width, font_size + 20), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    logging.info(f"Text dimensions: width={text_width}, height={text_height}")

    draw.text((0, 0), text, font=font, fill="white")
    text_image_path = os.path.join(output_directory, 'text_overlay.png')
    text_image.save(text_image_path)

    image_x = (video_width - image_width) // 2
    image_y = (video_height - image_height - text_height - 20) // 2
    text_x = (video_width * 0.95) - text_width
    text_y = image_y + image_height + 20
    icon_x = text_x - (video_width * 0.06 + 5)
    icon_y = text_y - (video_height * 0.01)

    final_video_path = os.path.join(output_directory, f"result_{os.path.basename(video_path)}")

    ffmpeg_command = [
        'ffmpeg', '-i', video_path, '-i', preprocessed_image_path, '-i', preprocessed_icon_path, '-i',
        text_image_path,
        '-filter_complex',
        f"[1]scale=w={video_width * 0.9}:h=-1[overlay1];"
        f"[2]scale=w={video_width * 0.06}:h=-1[overlay2];"
        f"[0][overlay1]overlay={image_x}:{image_y}[bg1];"
        f"[bg1][overlay2]overlay={icon_x}:{icon_y}[bg2];"
        f"[bg2][3]overlay={text_x}:{text_y}",
        '-codec:a', 'copy', '-map_metadata', '-1', final_video_path
    ]

    logging.info(f"Running ffmpeg command: {' '.join(ffmpeg_command)}")

    try:
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
        logging.info("Video created successfully!")
        logging.debug(f"ffmpeg stdout: {result.stdout}")
        logging.debug(f"ffmpeg stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error saving video: {e}")
        logging.debug(f"ffmpeg stdout: {e.stdout}")
        logging.debug(f"ffmpeg stderr: {e.stderr}")
        return None

    # Clean up
    for file in [video_path, preprocessed_image_path, preprocessed_icon_path, text_image_path]:
        try:
            os.remove(file)
        except Exception as e:
            logging.warning(f"Error removing file {file}: {e}")

    return final_video_path
