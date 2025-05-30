
# 08.2020
# hagen.gloetter@gmail.com
# convert a flash movie file to 720p MP4 to save HardDisk space

#  https://ntown.at/de/knowledgebase/cuda-gpu-accelerated-h264-h265-hevc-video-encoding-with-ffmpeg/

mkdir 720p
mkdir done
for f in *.flv
do
 echo "###########################################################################" 
 echo "############################ Processing >$f< ################################" 
 echo "###########################################################################" 
# old time ffmpeg -i "$f" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "720p/$f"
cmd="time ffmpeg -i \"$f\" -s hd720 -c:v libx265 -crf 23  \"720p/$f.mp4\" "
echo $cmd
eval $cmd
# time ffmpeg -hwaccel cuvid -c:v h265_cuvid -i "$f"  -c:v h265_nvenc -preset slow -pixel_format cuda -s hd720 -c:a copy -y -hide_banner "720p/$f" 
mv "$f" "done/$f"
done

