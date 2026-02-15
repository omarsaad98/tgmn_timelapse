# Create temporary directory for extracted frames
New-Item -ItemType Directory -Force -Path temp_frames | Out-Null

# Extract 6 frames from each TS segment
$tsFiles = Get-ChildItem saved_images/*.ts -ErrorAction SilentlyContinue | Sort-Object Name
if ($tsFiles) {
    Write-Host "Processing $($tsFiles.Count) TS segments..."
    foreach ($file in $tsFiles) {
        $tsFile = $file.FullName
        $baseName = $file.BaseName
        
        # Extract 6 frames from this TS segment
        ffmpeg -i $tsFile -frames:v 6 -q:v 1 "temp_frames/${baseName}_%03d.png" -y 2>&1 | Out-Null
        
        Write-Host "Extracted 6 frames from $($file.Name)"
    }
}

# Copy existing PNG files to temp_frames (for historical data that can't be reacquired)
$pngFiles = Get-ChildItem saved_images/*.png -ErrorAction SilentlyContinue | Sort-Object Name
if ($pngFiles) {
    Write-Host "Copying $($pngFiles.Count) existing PNG files..."
    foreach ($file in $pngFiles) {
        Copy-Item $file.FullName "temp_frames/$($file.Name)"
    }
}

# Create file list for concat
Get-ChildItem temp_frames/*.png | Sort-Object Name | ForEach-Object { "file 'temp_frames/$($_.Name)'" } | Out-File -Encoding ASCII images.txt

# Generate final timelapse video
Write-Host "Generating timelapse video..."
ffmpeg -f concat -safe 0 -r 60 -i images.txt -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p output.mp4 -y

# Clean up temporary frames
Remove-Item temp_frames/*.png
Write-Host "Timelapse generated: output.mp4"
