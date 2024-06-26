## Installation

1. Create a file `.env` inside `ops` directory and add the following lines to it:
    ```
    OPENAI_API_KEY=<OPENAI_API_KEY>
    TELEGRAM_BOT_TOKEN=<TELEGRAM BOT TOKEN>
    REDIS_HOST=redis (localhost if running locally without docker)
    MODEL_NAME=<model-name eg: gpt-3.5-turbo>
    BHASHINI_KEY=<bhashini-key>
    ```
2. For normal running

    Run the following commands:
    ```
    pip install -r requirements.txt
    ```
    Once the installaton is complete, run the following command to start the bot:
    ```
    python main.py
    ```

3. For docker running
    
    Run the following command to start the bot:
    ```
    docker-compose up
    ```
4. Open Telegram and search for `@YourBotName` and start chatting with the bot.


## Usage

1. To start a conversation with the bot, start having a conversation by saying hey, hello.
2. Start by typing '/start' and then select your language from the dropdown menu.
3. The bot will ask you to describe your details like name, gender, DOB and like
4. Once you have described your details, the bot will create a profile for you.



