import util
from talk import Sentence, Voice, Voices


import ffmpeg


import asyncio
import copy
import os
import re
import shutil
import subprocess
from datetime import timedelta


class Talk:
    """ スピーチ """

    def create_instance():
        doc: dict = {}
        doc["sentences"] = list()
        return Talk(doc,None,None)

    def __init__(self,doc: dict,voices:Voices,dict_data:dict):
        self.list: list[Sentence]= []
        self.tmp_dir: str= f'/tmp/{util.randomname(10)}'
        self.start_trim_sec = 0.0
        self.end_trim_sec = 0.0
        os.mkdir(self.tmp_dir)
        for yaml_sentences in doc["sentences"]:
            voice_id = list(yaml_sentences.keys())[0]
            voice = copy.copy(voices.list[voice_id])
            if "voice" in yaml_sentences:
                yaml_voice = yaml_sentences["voice"]
                if "volumn" in yaml_voice:
                    voice.voiumn = yaml_voice["volumn"]
            for text in yaml_sentences[voice_id].split('\n'):
                soundtext = text
                if text == '':
                    continue
                if "words" in dict_data:
                    for pattern in dict_data["words"]:
                        replacing = dict_data["words"][pattern]
                        soundtext = re.sub(pattern, f'{replacing}', soundtext)
                self.append(voice, soundtext, text)
        pass

    def append(self,voice:Voice,soundtext:str,text:str):
        self.list.append(Sentence(voice,soundtext,text))
        pass

    def convert_aync (self) :
        for utterance in self.list:
            filename=  f'{self.tmp_dir}/{util.randomname(10)}.mp3'
            utterance.convert_aync(filename)

    def save(self,outfile,srtfile):
        asyncio.run(self.__save__(outfile,srtfile))

    async def __save__(self,outfile,srtfile):
        tmp_outfile = f'{self.tmp_dir}/{util.randomname(10)}.mp3'
        shutil.copy('silent.mp3', outfile)
        i: int = 0
        for utterance in self.list:
            i+=1
            shutil.copy(outfile,tmp_outfile)
            await utterance.task

            # get current info
            probe = ffmpeg.probe(outfile)
            outfile_time = timedelta(seconds=float(probe['format']['duration']))

            # trim
            probe = ffmpeg.probe(utterance.outfile)
            addfile_time = float(probe['format']['duration'])
            tmpAddFile = f'{self.tmp_dir}/{util.randomname(10)}.mp3'
            f1Time = timedelta(seconds=addfile_time-self.end_trim_sec)
            command = [
                "ffmpeg",
                "-i", utterance.outfile,
                "-ss", str(self.start_trim_sec),
                "-to", str(f1Time),
                "-c", "copy",
                tmpAddFile]
            subprocess.run(command)
            shutil.move(tmpAddFile,utterance.outfile)

            with open(f"{self.tmp_dir}/file_list.txt",mode="w", newline='\n') as file:
                file.writelines([f"file '{tmp_outfile}'\n",f"file '{utterance.outfile}'\n"])
            command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", f"{self.tmp_dir}/file_list.txt",
                "-y",
                "-c", "copy",outfile]
            subprocess.run(command)

            # get current info
            probe = ffmpeg.probe(outfile)
            end_time = timedelta(seconds=float(probe['format']['duration']))

            with open(srtfile,mode="a", newline='\n') as srtfilebuf:
                orgtext = re.sub('_','',utterance.originaltext)
                srtfilebuf.writelines(
                    [f"{i}\n",
                    f"{str(util.convertHHmmssfff(outfile_time))} --> {str(util.convertHHmmssfff(end_time))}\n", f"{orgtext}\n", "\n"])