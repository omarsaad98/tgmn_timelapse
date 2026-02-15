"""Test script to manually run a capture."""
import logging
from main import capture_keyframe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("Running manual capture test...")
    capture_keyframe()
    print("Capture complete!")
