# CHANGELOG

## Commit fe0b1bcf410588370191d3e1f46d51d949ee368b
+ Static image support!!
+ File type indicator (video, image, gif)
+ Resolution indicator
+ Support for video files that aren't mp4!!
+ More error pop ups (Cache errors, mpvpaper errors)

## Commit 7238d178d65ae601e747facffb887483ddb53e35

### Highlights
+ Error dialogs are now a thing!
+ You can now use a generated file to launch mpvpaper on system startup so your wallpapers will be remembered!

#### Error Handling (Pop Up)
+ Error on empty config (You Must Create The Config Beforehand, will be improved further)
+ Error on failure to create persistence file (~/.config/wallpv/wallpaper.txt)
+ Error on Failure to run ffmpeg for thumbnails

#### QOL
+ File to use in startup for persistence (~/.config/wallpv/wallpaper.txt)