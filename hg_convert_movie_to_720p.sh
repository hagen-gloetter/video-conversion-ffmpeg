#! /bin/bash
# 08.2020
# hagen.gloetter@gmail.com
# convert a movie file to 720p to save HD space

#  https://ntown.at/de/knowledgebase/cuda-gpu-accelerated-h264-h265-hevc-video-encoding-with-ffmpeg/

mkdir 720p
mkdir done

shopt -s nullglob
_self="${0##*/}"
echo "$_self is called"

FFmpeg=$(which ffmpeg)
if [ $? -eq 0 ]; then
    echo "ffmpeg  found"
else
    echo "ffmpeg  NOT found"
    exit 1
fi

function make_ffmpg {
    f="$1"
    time ffmpeg -hide_banner -loglevel error -i "$f" -s hd720 -c:v libx265 -crf 23  "720p/$f" >/dev/null 2>&1 
    mv "$f" "done/$f"

}
N=6
COUNTER=1

for FN in *.mp4 *.wmv *.mov *.mkv
do
    ((i = i % N))
    ((i++ == 0)) && wait
    echo "###########################################################################" 
    echo "############################ $COUNTER Processing $FN ################################" 
    echo "###########################################################################" 
    date
    echo "###########################################################################" 
    # old time ffmpeg -i "$f" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "720p/$f"
    ((COUNTER = COUNTER + 1))
    make_ffmpg "$FN" &
    # time ffmpeg -hwaccel cuvid -c:v h265_cuvid -i "$f"  -c:v h265_nvenc -preset slow -pixel_format cuda -s hd720 -c:a copy -y -hide_banner "720p/$f" 
done
