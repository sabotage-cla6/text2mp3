tgt_dir=/usr/local/text2mp3

python3 -m venv $tgt_dir
cd $tgt_dir
sleep 2
.  ./bin/activate
pip install edge-tts PyYAML ffmpeg-python


