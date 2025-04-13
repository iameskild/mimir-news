import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .agents import Researcher, NewsWriter, call_eleven_labs_api
from .markets import get_recently_closed_markets, get_market_details
from .video import create_video
from .constants import AUDIO_DIR, VIDEO_DIR, IMAGE_DIR
load_dotenv()

logger = logging.getLogger(__name__)


def main():
    """
    Main function to run the Mimir News application.
    """

    markets = get_recently_closed_markets()
    researcher = Researcher()
    news_writer = NewsWriter()
    date_str = datetime.now().strftime("%Y-%m-%d")

    for market_id in markets:
        logger.info(f"Researching market ID: {market_id}") 
        market_details = get_market_details(market_id, raw=False)
        logger.info(f"Market details: {market_details.question}")

        logger.info(f"Researching market: {market_details.question}")
        research_details = researcher.call_llm(market_details)
        logger.info("Research completed")

        logger.info(f"Writing news copy for question: {market_details.question}")
        news_copy = news_writer.call_llm(research_details)
        logger.info("News copy completed")

        logger.info(f"Generating audio for news copy: {news_copy}")
        audio_path = AUDIO_DIR / date_str 
        audio_path.mkdir(parents=True, exist_ok=True)
        audio_path = audio_path / f"news_copy_{market_details.question}.mp3"
        call_eleven_labs_api(news_copy, save_path=audio_path)
        logger.info("Audio generated")

        logger.info(f"Generating video for news copy: {news_copy}")
        video_path = VIDEO_DIR / date_str 
        video_path.mkdir(parents=True, exist_ok=True)
        video_path = video_path / f"video_{market_details.question}.mp4"
        image_dir = IMAGE_DIR / date_str 
        image_dir.mkdir(parents=True, exist_ok=True)
        create_video(market_details, audio_path, image_dir, video_path, headless=False)
        logger.info("Video generated")


if __name__ == "__main__":
    main()
