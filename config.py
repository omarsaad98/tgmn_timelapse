from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tgmn_stream_url: str = "https://stream1.vossaskyen.no/bt/Torgallmenningen.stream/playlist.m3u8"
    save_dir: str = "saved_images"
    timezone: str = "Europe/Oslo"
    number_of_frames: int = 12
