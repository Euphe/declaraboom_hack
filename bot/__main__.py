import os
import logging
from .bot import create_bot


def configure_logging():
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
def main():
    configure_logging()
    bot = create_bot(os.environ['API_KEY'])

    bot.start()

if __name__ == '__main__':
    main()