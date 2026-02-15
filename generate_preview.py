"""
Generate preview timelapse by streaming frames directly to ffmpeg.
No temporary files created - everything is piped through memory.
"""
import subprocess
import os
from pathlib import Path
from config import Settings

def get_sorted_files(directory, extension):
    """Get sorted list of files with given extension."""
    path = Path(directory)
    return sorted(path.glob(f"*.{extension}"))

def main():
    settings = Settings()
    save_dir = Path(settings.save_dir)
    
    # Get all source files sorted chronologically
    ts_files = get_sorted_files(save_dir, "ts")
    png_files = get_sorted_files(save_dir, "png")
    
    total_frames = len(ts_files) * settings.number_of_frames + len(png_files)
    
    if total_frames == 0:
        print("No files to process")
        return
    
    print(f"Found {len(ts_files)} TS files and {len(png_files)} PNG files")
    print(f"Total frames: {total_frames}")
    print(f"Preview duration: {total_frames / 60:.2f} seconds at 60fps")
    print()
    
    # Start ffmpeg process that reads frames from stdin
    # Using rawvideo format piped from stdin
    output_file = "output.mp4"
    
    # Get frame dimensions from first available file
    if ts_files:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(ts_files[0])
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        width, height = result.stdout.strip().split(',')
    elif png_files:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(png_files[0])
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        width, height = result.stdout.strip().split(',')
    else:
        print("No source files found")
        return
    
    print(f"Frame size: {width}x{height}")
    print(f"Encoding to {output_file}...")
    print()
    
    # Start ffmpeg encoder process
    encoder = subprocess.Popen([
        "ffmpeg",
        "-f", "image2pipe",
        "-framerate", "60",
        "-i", "-",  # Read from stdin
        "-c:v", "libx264",
        "-preset", "veryslow",
        "-crf", "10",
        "-pix_fmt", "yuv420p",
        "-y",
        output_file
    ], stdin=subprocess.PIPE)
    
    frame_count = 0
    
    # Process TS files - extract 6 frames from each
    for ts_file in ts_files:
        print(f"Processing {ts_file.name} (6 frames)...", end=" ")
        
        # Extract 6 frames and pipe to encoder
        extractor = subprocess.Popen([
            "ffmpeg",
            "-i", str(ts_file),
            "-frames:v", str(settings.number_of_frames),
            "-f", "image2pipe",
            "-c:v", "png",
            "-"
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        # Pipe frames to encoder
        for line in extractor.stdout:
            encoder.stdin.write(line)
        
        extractor.wait()
        frame_count += settings.number_of_frames
        print(f"✓ ({frame_count}/{total_frames})")
    
    # Process PNG files
    if png_files:
        print(f"Processing {len(png_files)} PNG files...", end=" ")
        for png_file in png_files:
            # Read PNG and pipe to encoder
            with open(png_file, 'rb') as f:
                encoder.stdin.write(f.read())
            frame_count += 1
        print(f"✓ ({frame_count}/{total_frames})")
    
    # Close stdin to signal end of input
    encoder.stdin.close()
    encoder.wait()
    
    print()
    if encoder.returncode == 0:
        output_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Success! Generated {output_file} ({output_size:.2f} MB)")
    else:
        print("Error: Encoding failed")

if __name__ == "__main__":
    main()
