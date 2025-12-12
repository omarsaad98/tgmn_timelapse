Get-ChildItem saved_images/*.png | ForEach-Object { "file 'saved_images/$($_.Name)'" } | Out-File -Encoding ASCII images.txt
ffmpeg -f concat -safe 0 -r 24 -i images.txt -c:v libx265 -crf 18 -pix_fmt yuv420p output.mp4 -y
