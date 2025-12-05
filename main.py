import logging
import subprocess
import os
import time
import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import Settings

logger = logging.getLogger("tgmn-timelapse")

# Global settings instance for timezone
_settings = Settings()
_tz = ZoneInfo(_settings.timezone)

logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def get_capture_time(date: datetime) -> datetime:
    """
    Calculate the capture time for a given date.
    
    Linearly interpolates from 00:00 on January 1st to 00:00 on January 1st of the next year.
    """
    year = date.year
    start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=_tz)
    end_date = datetime(year+1, 1, 1, 0, 0, 0, tzinfo=_tz)
    days_in_year = (end_date - start_date).days
    day_of_year = date.timetuple().tm_yday  # 1-indexed (Jan 1 = 1)

    progress = (day_of_year - 1) / days_in_year

    seconds_in_year = (end_date - start_date).total_seconds()
    seconds_in_day = seconds_in_year / days_in_year
    seconds_to_add_each_day = seconds_in_day / days_in_year

    start_of_day = start_date + timedelta(seconds=progress * seconds_in_year)

    return start_of_day + timedelta(seconds=seconds_to_add_each_day * day_of_year)
    
def capture_keyframe():
    """Download frames from the stream starting at the first keyframe."""
    settings = Settings()

    # Ensure save directory exists
    os.makedirs(settings.save_dir, exist_ok=True)

    # Generate filename pattern with current date
    # %02d will be replaced by ffmpeg with sequential frame numbers (01, 02, etc.)
    filename_pattern = datetime.now(_tz).strftime("%Y-%m-%d_%H-%M-%S") + "_%02d.png"
    filepath_pattern = os.path.join(settings.save_dir, filename_pattern)

    # Use ffmpeg to extract frames from the HLS stream:
    # - select filter: Wait for first keyframe (I-frame), then capture next 4 consecutive frames
    #   - eq(pict_type,I)*eq(selected_n,0): Select first keyframe (when nothing selected yet)
    #   - gt(selected_n,0)*lt(selected_n,5): Select next 4 frames (when 1-4 frames already selected)
    # - vsync vfr: Variable frame rate to avoid frame duplication
    # - frames:v 5: Stop after 5 frames
    select_expr = "(eq(pict_type,I)*eq(selected_n,0))+(gt(selected_n,0)*lt(selected_n,5))"
    cmd = [
        "ffmpeg",
        "-i", settings.tgmn_stream_url,
        "-vf", f"select='{select_expr}'",
        "-vsync", "vfr",
        "-frames:v", "10",
        "-y",
        filepath_pattern,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("[%s] Keyframes saved as %s", datetime.now(_tz), filepath_pattern)
        else:
            logger.info("[%s] Error capturing keyframes: %s", datetime.now(_tz), result.stderr)
    except subprocess.TimeoutExpired:
        logger.info("[%s] Timeout while capturing keyframes", datetime.now(_tz))
    except FileNotFoundError:
        logger.info("[%s] ffmpeg not found. Please install ffmpeg.", datetime.now(_tz))


def print_monthly_capture_times(year: int | None = None):
    """Print the capture time for the first day of every month."""
    if year is None:
        year = datetime.now(_tz).year
    
    logger.info("Capture times for the 1st of each month in %s:", year)
    logger.info("-" * 40)
    
    for month in range(1, 13):
        date = datetime(year, month, 1, tzinfo=_tz)
        capture_time = get_capture_time(date)
        month_name = calendar.month_name[month]
        logger.info("%s 1: %s", month_name, capture_time.strftime('%H:%M:%S'))


def get_next_capture_time() -> datetime:
    """
    Get the next scheduled capture time.
    
    If today's capture time hasn't passed yet, return today's capture time.
    Otherwise, return tomorrow's capture time.
    """
    now = datetime.now(_tz)
    today_capture = get_capture_time(now)
    
    if now < today_capture:
        return today_capture
    else:
        tomorrow = now + timedelta(days=1)
        return get_capture_time(tomorrow)


def main():
    logger.info("Starting timelapse capture service...")
    logger.info("Using timezone: %s", _settings.timezone)
    logger.info("Capture time linearly progresses from 00:00 on Jan 1 to 24:00 on Jan 1 of the next year")
    
    while True:
        next_capture = get_next_capture_time()
        now = datetime.now(_tz)
        
        logger.info("Next capture scheduled for %s", next_capture)
        
        # Sleep until the next capture time
        sleep_seconds = (next_capture - now).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        
        # Capture the keyframe
        capture_keyframe()
        
        # Small delay to ensure we move past the capture time
        time.sleep(1)


if __name__ == "__main__":
    main()
