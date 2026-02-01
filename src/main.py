import subprocess
import shutil
import re
import asyncio
import ffmpeg
import random
import string
import yaml
import text2mp3
import copy
import argparse
import talk
import os
from pydub import AudioSegment
from datetime import timedelta

CUT_START = 0.12
CUT_SEC = 0.68
tmp_dir = ''

def convertHHmmssfff(time:timedelta):
    totsec = time.total_seconds()
    hh = int(totsec // 3600)
    mm = int((totsec % 3600) // 60)
    ss = int(totsec % 60)
    mi = int((totsec % 1) * 1000)
    return f'{hh:02}:{mm:02}:{ss:02},{mi:03}'


def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return "".join(randlst)

def ConvertYamlToVoiceData(path, worddict) -> talk.Talk:
    voices = {}
    voices_data = talk.Talk()

    dict_data = dict()
    if worddict is not None:
        dict_data = yaml.safe_load(open(worddict))

    with open(path, encoding="utf-8") as f:
        document = yaml.safe_load(f)
        for yaml_voice in document["voices"]:
            voice = talk.Voice(yaml_voice["voice"])
            if "rate" in yaml_voice:
                voice.rate = yaml_voice["rate"]
            if "volumn" in yaml_voice:
                voice.volumn = yaml_voice["volumn"]
            if "pitch" in yaml_voice:
                voice.pitch = yaml_voice["pitch"]
            voices[yaml_voice["id"]] = voice
        for yaml_sentences in document["sentences"]:
            voice_id = list(yaml_sentences.keys())[0]
            voice = copy.copy(voices[voice_id])
            if "voice" in yaml_sentences:
                yaml_voice = yaml_sentences["voice"]
                if "volumn" in yaml_voice:
                    voice.voiumn = yaml_voice["volumn"]

            # text = yaml_sentences[voice_id]
            # if text == '':
            #     continue
            # if "words" in dict_data:
            #     for pattern in dict_data["words"]:
            #         replacing = dict_data["words"][pattern]
            #         text = re.sub(pattern, f'{replacing}', text)
            #         text = re.sub('\r\n', ' ',text)
            #         text = re.sub('\r', ' ',text)
            #         text = re.sub('\n', ' ',text)
            # voices_data.append(voice, text)

            for text in yaml_sentences[voice_id].split('\n'):
                # text = yaml_sentences[voice_id]
                soundtext = text
                if text == '':
                    continue
                if "words" in dict_data:
                    for pattern in dict_data["words"]:
                        replacing = dict_data["words"][pattern]
                        soundtext = re.sub(pattern, f'{replacing}', soundtext)
                voices_data.append(voice, soundtext, text)

    return voices_data

async def main(in_file, out_file, worddict_file):
    """ Main function.

    Args:
        in_file:
        out_file:
        worddict_file:
    """
    voices = {}
    voices_data = talk.Talk()

    if in_file is not None:
        voices_data = ConvertYamlToVoiceData(in_file, worddict_file)
    if out_file is None:
        out_file = f'{in_file}.mp3'

    pathes = []
    tasks = dict()

    i = 0
    for utterance in voices_data.list:
        tmpfile_name = randomname(10)
        i += 1
        tmpfile_path = f"/tmp/{tmp_dir}/{i}_{tmpfile_name}.mp3"
        # tmpfile_path = f"/tmp/{tmpfile_name}.mp3"
        pathes.append(tmpfile_path)
        tasks[tmpfile_path] = (asyncio.create_task(
            text2mp3.Text2mp3.convert(
                utterance.soundtext,
                tmpfile_path,
                voice=utterance.voice.name,
                rate=utterance.voice.rate,
                volume=utterance.voice.volumn,
            )
        ),utterance)

    srcfilePath1 = list(tasks)[0]
    i = 1
    shutil.copy('silent.mp3', out_file)
    srcfilePath1 = 'silent.mp3'

    srtfile =re.sub('\.[^.]+$','.srt',out_file)
    if os.path.isfile(srtfile):
        os.remove(srtfile)
    for tmpFilePath in tasks:
        await tasks[tmpFilePath][0]
        utterance = tasks[tmpFilePath][1]

        probe = ffmpeg.probe(out_file)
        outfile_time = timedelta(seconds=float(probe['format']['duration']))
        tmpOutFile = f"/tmp/{tmp_dir}/{randomname(10)}.mp3"
        shutil.copy(out_file, tmpOutFile)

        for soundtext in utterance.soundtext.split('\r\n'):

            if re.match('^\[silent:(.*)\]$',soundtext):
                silent_sec = re.sub(r'^\[silent:(.*)\]$',r'\1',soundtext)
                command = [
                    'ffmpeg',
                    '-i', tmpOutFile,
                    '-y',
                    '-af', f'apad=pad_dur={silent_sec}',
                    out_file]
                subprocess.run(command)
            else:

                probe = ffmpeg.probe(tmpFilePath)
                addfile_time = float(probe['format']['duration'])
                if addfile_time < CUT_SEC:
                    addfile_time = 0.1
                else:
                    addfile_time = float(addfile_time) - CUT_SEC
                f1Time = timedelta(seconds=addfile_time)

                tmpAddFile = f"/tmp/{tmp_dir}/{randomname(10)}.mp3"
                command = [
                    "ffmpeg",
                    "-i", tmpFilePath,
                    "-ss", str(CUT_START),
                    "-to", str(f1Time),
                    "-c", "copy",
                    tmpAddFile]
                subprocess.run(command)
                # command = [
                #     "ffmpeg",
                #     "-i", tmpFilePath,
                #     "-af", "silenceremove=start_periods=1:start_duration=0:start_silence=0:start_threshold=0",
                #     tmpAddFile]
                # subprocess.run(command)
                # shutil.copy(tmpAddFile,tmpFilePath)
                # command = [
                #     "ffmpeg",
                #     "-y",
                #     "-i", tmpFilePath,
                #     "-af", "silenceremove=stop_periods=0:stop_duration=0:stop_silence=0:stop_threshold=10dB",
                #     tmpAddFile]
                # subprocess.run(command)
                # shutil.copy(tmpAddFile,tmpFilePath)

                with open(f"/tmp/{tmp_dir}/file_list.txt",mode="w", newline='\n') as file:
                    file.writelines([f"file '{tmpOutFile}'\n",f"file '{tmpAddFile}'\n"])
                command = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", f"/tmp/{tmp_dir}/file_list.txt",
                    "-y", 
                    "-c", "copy",out_file]
                subprocess.run(command)
                os.remove(tmpAddFile)

                probe = ffmpeg.probe(out_file)
                end_time = timedelta(seconds=float(probe['format']['duration']))

                with open(srtfile,mode="a", newline='\n') as file:
                    orgtext = re.sub('_','',utterance.originaltext) 
                    file.writelines([f"{i}\n",f"{str(convertHHmmssfff(outfile_time))} --> {str(convertHHmmssfff(end_time))}\n", f"{orgtext}\n", "\n"])
                i += 1

            if os.path.isfile(tmpOutFile):
                os.remove(tmpOutFile)
            if os.path.isfile(tmpFilePath):
                os.remove(tmpFilePath)

        


            # srcfilePath2 = tmpFilePath
        # tmpfile_path = srcfilePath1
        # if srcfilePath1 != srcfilePath2:
        #     tmpfile_path = f"/tmp/{tmp_dir}/{randomname(10)}.mp3"
        #     # aufile1 = AudioSegment.from_mp3(srcfilePath1)
        #     # aufile2 = AudioSegment.from_mp3(srcfilePath2)
        #     # aufile3 = aufile1[:aufile1.duration_seconds - 500] + aufile2
        #     # aufile3.export(tmpfile_path)
        #     # ffmpeg.probe(srcfilePath2)
        #     probe = ffmpeg.probe(srcfilePath1)
        #     srcfileTime1 = float(probe['format']['duration'])
        #     if srcfileTime1 < CUT_SEC:
        #         srcfileTime1 = 0.1
        #     else:
        #         srcfileTime1 = float(srcfileTime1) - CUT_SEC
        #     f1Time = timedelta(seconds=srcfileTime1)

        #     # srcfile2 = ffmpeg.input(srcfilePath2)
        #     # ffmpeg.filter([srcfile1, srcfile2], 'concat', n=2, v=0, a=1).output(tmpfile_path).run()
        #     # ffmpeg.probe(tmpfile_path)
            
        #     command = [
        #         "ffmpeg",
        #         "-i", srcfilePath1,
        #         "-to", str(f1Time),
        #         "-c", "copy",
        #         tmpOutFile]
        #     subprocess.run(command)

        #     with open(f"/tmp/{tmp_dir}/file_list.txt",mode="w", newline='\n') as file:
        #         file.writelines([f"file '{tmpOutFile}'\n",f"file '{srcfilePath2}'\n"])
        #     command = [
        #         "ffmpeg",
        #         "-f", "concat",
        #         "-safe", "0",
        #         "-i", f"/tmp/{tmp_dir}/file_list.txt",
        #         "-c", "copy",tmpfile_path]
        #     subprocess.run(command)


        # shutil.copy(tmpfile_path, out_file)
        # srcfilePath1 = out_file



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="text2mp3", usage="%(prog)s [options]")
    parser.add_argument("-o", "--output", required=False, help='output mp3 file')
    parser.add_argument("-i", "--input", required=False, help='input yaml file')
    parser.add_argument("-vf", "--voice-file", required=False, help='voice yaml file.you can write voice info within input file.')
    parser.add_argument("-d", "--dict", required=False, help='word dictionary yaml')
    args = parser.parse_args()

    tmp_dir = randomname(10)
    os.mkdir(f'/tmp/{tmp_dir}')

    # talk_line = talk.Talk()
    # if args.input is not None:
    #     talk_line = ConvertYamlToVoiceData(args.input,args.dict)

    output = args.output if args.output is not None else os.path.splitext( args.input )[0] + '.mp3';

    asyncio.run(main(args.input, output, args.dict))

    shutil.rmtree(f'/tmp/{tmp_dir}')
