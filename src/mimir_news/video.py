import time
import logging
from pathlib import Path

from dotenv import load_dotenv

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing import CompositeVideoClip

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from PIL import Image

from .models import PredictionMarket
from .constants import BACKGROUND_COLOR
load_dotenv()

logger = logging.getLogger(__name__)

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         # logging.FileHandler('video_processing.log'),
#         logging.StreamHandler()  # This will still print to console
#     ]
# )


def capture_embed_screenshot(
    embed_url: str,
    output_path: Path,
    window_size: tuple[int, int] = (1920, 1080),
    headless: bool = True,
):
    """Captures a screenshot of the embedded URL using Selenium."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(embed_url)
        # Wait for the page to load (adjust time as needed)
        time.sleep(3)  
        driver.save_screenshot(output_path)
        logger.info(f"Screenshot saved to {output_path}")
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
    finally:
        driver.quit()

    # resize the image
    im = Image.open(output_path)
    (width, height) = (im.width // 2, im.height // 2)
    im = im.resize((width, height))
    im.save(output_path)


def create_video(
    market: PredictionMarket,
    audio_path: Path,
    image_path: Path,
    video_path: Path,
    headless: bool = True,
):
    """
    Creates a video for the news broadcast with a colored background and centered screenshot.
    
    Args:
        market: PredictionMarket object containing the market details
        audio_path: Path to the audio file
        image_path: Path to the directory containing the screenshot
        video_path: Path to the directory containing the video
    """
    embed_url = market.embed_url
    name = market.question
    image_path = image_path / f"embed_screenshot_{name}.png"
    capture_embed_screenshot(embed_url, image_path, window_size=(880, 500), headless=headless)

    audio_clip = AudioFileClip(audio_path)
    logger.info("Audio clip processed")
 
    background = ColorClip(size=(1080, 1920), color=BACKGROUND_COLOR)
    background.duration = audio_clip.duration
    
    # Load and resize the screenshot
    screenshot = ImageClip(str(image_path))
    logger.info("Screenshot loaded")
    # exit()
    
    # Compose the final video
    video_clip: CompositeVideoClip = CompositeVideoClip([
        background,
        screenshot.with_position(("center", "center")),
    ])
    video_clip.duration = audio_clip.duration
    logger.info("Video clip composed")
    video_clip = video_clip.with_audio(audio_clip)
    logger.info("Video clip with audio")
    
    # Write the final video
    video_clip.write_videofile(video_path, codec='libx264', fps=24)


# if __name__ == "__main__":
    
#     embed_url = "https://manifold.markets/embed/sama/will-trump-reverse-canada-tariffs-b?play=true"
#     screenshot_path = "artifacts/videos/embed_screenshot.png"
#     capture_embed_screenshot(embed_url, screenshot_path, size=(880, 500))

#     videos_path = "artifacts/videos"
#     audio_path = "artifacts/audio_clip.mp3"
#     output_path = "output.mp4"
#     logger.info("Starting video creation")
#     create_video(audio_path, videos_path, output_path)
