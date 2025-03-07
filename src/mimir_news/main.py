from dotenv import load_dotenv
import logging

from .agents import Researcher, NewsWriter, call_eleven_labs_api
from .markets import get_recently_closed_markets

load_dotenv()

logger = logging.getLogger(__name__)


def main():
    """
    Main function to run the Mimir News application.
    """

    markets = get_recently_closed_markets()
    researcher = Researcher()
    news_writer = NewsWriter()

    news_copies = []

    for market in markets:
        question = market.question
        logger.info(f"Researching question: {question}")
        research_details = researcher.call_llm(market)
        logger.info("Research completed")
        logger.info(f"Writing news copy for question: {question}")
        news_copy = news_writer.call_llm(research_details)
        news_copies.append(news_copy)
        logger.info("News copy completed")

    logger.info(f"Generating audio for news copy: {news_copy}")
    call_eleven_labs_api(news_copy, save_path=f"news_copy_{question}.mp3")
    logger.info("Audio generated")


if __name__ == "__main__":
    main()
