import subprocess
import os
import time
import calendar
from datetime import datetime, timedelta

from config import Settings

# Capture time range: linearly from 6am on Jan 1 to 6pm on Dec 31
START_HOUR = 6   # 6:00 AM
END_HOUR = 18    # 6:00 PM


def get_days_in_year(year: int) -> int:
    """Return the number of days in the given year."""
    return 366 if calendar.isleap(year) else 365


def get_capture_time(date: datetime) -> datetime:
    """
    Calculate the capture time for a given date.
    
    Linearly interpolates from 6:00 AM on January 1st to 6:00 PM on December 31st.
    """
    year = date.year
    days_in_year = get_days_in_year(year)
    day_of_year = date.timetuple().tm_yday  # 1-indexed (Jan 1 = 1)
    
    # Calculate progress through the year (0.0 on Jan 1, 1.0 on Dec 31)
    progress = (day_of_year - 1) / (days_in_year - 1)
    
    # Interpolate between start and end hour
    capture_hour = START_HOUR + progress * (END_HOUR - START_HOUR)
    
    # Convert to hours and minutes
    hours = int(capture_hour)
    minutes = int((capture_hour - hours) * 60)
    
    return date.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def capture_keyframe():
    """Download a keyframe from the stream and save it as PNG."""
    settings = Settings()

    # Ensure save directory exists
    os.makedirs(settings.save_dir, exist_ok=True)

    # Generate filename with current date
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
    filepath = os.path.join(settings.save_dir, filename)

    # Use ffmpeg to extract a single keyframe (I-frame) from the HLS stream
    # -skip_frame nokey: Skip all frames except keyframes during decoding
    # -i: Input stream URL
    # -frames:v 1: Output only 1 video frame
    # -y: Overwrite output file without asking
    cmd = [
        "ffmpeg",
        "-skip_frame", "nokey",
        "-i", settings.tgmn_stream_url,
        "-frames:v", "1",
        "-y",
        filepath,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] Keyframe saved as {filepath}")
        else:
            print(f"[{datetime.now()}] Error capturing keyframe: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"[{datetime.now()}] Timeout while capturing keyframe")
    except FileNotFoundError:
        print(f"[{datetime.now()}] ffmpeg not found. Please install ffmpeg.")


def get_next_capture_time() -> datetime:
    """
    Get the next scheduled capture time.
    
    If today's capture time hasn't passed yet, return today's capture time.
    Otherwise, return tomorrow's capture time.
    """
    now = datetime.now()
    today_capture = get_capture_time(now)
    
    if now < today_capture:
        return today_capture
    else:
        tomorrow = now + timedelta(days=1)
        return get_capture_time(tomorrow)


def main():
    print("Starting timelapse capture service...")
    print(f"Capture time linearly progresses from {START_HOUR}:00 on Jan 1 to {END_HOUR}:00 on Dec 31")
    
    while True:
        next_capture = get_next_capture_time()
        now = datetime.now()
        
        print(f"[{now}] Next capture scheduled for {next_capture}")
        
        # Sleep until the next capture time
        sleep_seconds = (next_capture - now).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        
        # Capture the keyframe
        capture_keyframe()
        
        # Small delay to ensure we move past the capture time
        time.sleep(1)


if __name__ == "__main__":
    capture_keyframe()
