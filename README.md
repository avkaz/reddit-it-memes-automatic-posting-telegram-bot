# Automatic Telegram Posting Bot

This bot is part of a larger project, the main repository for which can be found [here](<https://github.com/avkaz/code_review/tree/main>).  
This bot automates meme posting on Telegram. It retrieves memes from a PostgreSQL database and posts them to Telegram channels.  It also handles status updates, video creation, and meme cleanup.

## Features

*   **Meme Posting:** Posts memes from the database to a main channel and two supporting channels.
*   **Status Updates:** Sends status updates to a designated channel.
*   **Video Creation:** Creates videos for TikTok and Instagram by adding memes to stylized backgrounds, incorporating music, and sending the finished videos to a third channel.
*   **Database Cleanup:** Deletes posted memes from the database after they have been uploaded.
*   **Preferred Posting Time:** Set your preferred time for posting memes.

## Setup

Follow these steps to set up and run the bot:

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/avkaz/reddit-it-memes-automatic-posting-telegram-bot.git)
    cd your-repository
    ```

2.  **Get a Telegram Bot Token:**
    *   Create a bot using BotFather and obtain the bot token.
    *   In `main.py`, replace `'your_telegram_bot_token'` with your actual bot token:

    ```python
    bot = telebot.TeleBot('your_telegram_bot_token')
    ```

3.  **Set Channel IDs:**
    *   Define three Telegram channel IDs in `main.py`:
        *   `target_channel_id`: Main channel for posting memes.
        *   `status_chat_id`: Channel for posting status updates.
        *   `code_review_video_id`: Channel for posting videos.
    *   Replace the placeholder IDs in `main.py` with your channel IDs:

    ```python
    target_channel_id = '-1002115819190'  # Main channel for posting memes
    status_chat_id = '-1001999613821'     # Channel for posting status updates
    code_review_video_id = '-1002226599559'  # Channel for posting videos
    ```

    *   To get these IDs, have your bot send messages to the respective channels and then check the bot's logs.
    *   Dont forget to give your bot acess rights to post in these chanels

4.  **Firebase API Key:**
    *   Obtain your Firebase API key from the Firebase Console.
    *   Save the key as `key.json` and place it in the project's main directory.
    *   **Important:** Add `key.json` to your `.gitignore` file to prevent it from being committed to version control.

5.  **Set Preferred Posting Time:**
    *   In `main.py`, locate the scheduling section and set your preferred posting time:

    ```python
    # Define constants for time intervals
    MORNING_TIMES = [
        convert_to_local_time(8, 45),
    ]
    
    EVENING_TIMES = [
        convert_to_local_time(15, 45),
        convert_to_local_time(20, 45),
    ]
    ```


6.  **Docker Setup:**

    *   **Install Docker and Docker Compose:** If you don't have Docker installed, follow the instructions on the [official Docker website](https://www.docker.com/).  For Docker Compose, you can usually use:

    ```bash
    sudo apt install docker-compose  # Example for Debian/Ubuntu
    ```

    *   **Build the Docker image:**

    ```bash
    docker-compose build
    ```

    *   **Run the Docker container:**

    ```bash
    docker-compose up
    ```

    *   **Stop the Docker container:**

    ```bash
    docker-compose down
    ```

## Main Repository

*   Main Project Repository: <https://github.com/avkaz/code_review/tree/main>
