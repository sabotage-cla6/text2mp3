import edge_tts
import copy
import re
import util
import os
import shutil
import subprocess
import asyncio
import ffmpeg
from datetime import timedelta
import tqdm

class Voice:
    """ 声情報 """
    def __init__(self,yaml_voice):
        self.name: str = yaml_voice["voice"]
        self.rate: str = '+0%'
        self.volume: str = '+0%'
        self.pitch: str = '+0Hz'
        if "rate" in yaml_voice:
            self.rate = yaml_voice["rate"]
        if "volume" in yaml_voice:
            self.volume = yaml_voice["volume"]
        if "pitch" in yaml_voice:
            self.pitch = yaml_voice["pitch"]
        pass

class Voices:
    """ 声情報の一覧 """
    def __init__(self):
        self.list: dict[Voice] = {}
        pass

    def __init__(self,voices):
        self.list: dict[Voice] = {}
        for yaml_voice in voices:
            voice = Voice(yaml_voice)
            self.list[yaml_voice["id"]] = voice
        pass

class Utterance:
    """ 発話情報（１文） """
    def __init__(self,voice,soundtext,originaltext,
                 start_trim_sec,end_trim_sec,emptyline_break):
        self.voice: Voice = voice
        self.soundtext: str = soundtext
        self.originaltext: str = originaltext
        self.start_trim_sec = start_trim_sec
        self.end_trim_sec = end_trim_sec
        self.emptyline_break = emptyline_break
        self.task: asyncio.Task = None
        self.outfile = None
        pass
    
    def convert_aync(self,tmp_dir):
        """ mp3変換 """
        self.outfile = f'{tmp_dir}/{util.randomname(10)}.mp3'

        if re.match(r'^<break +time="([^"]*)" */>$',self.soundtext.strip()):
            silent_sec = float(re.sub(r'^<break +time="([^"]*)" */>$',r'\1',self.soundtext.strip()))
            self.soundtext = None
            self.originaltext = ''
            self.task = self.__create_nosound__(silent_sec)
        elif not self.soundtext and 0 < self.emptyline_break:
            self.task = self.__create_nosound__(self.emptyline_break)
        else:
            self.task = self.__convert_aync__(tmp_dir,self.start_trim_sec,self.end_trim_sec)
        pass

    async def __create_nosound__(self,silent_sec):
        command = [
            'ffmpeg',
            '-ar', '48000',
            '-t', f'{silent_sec}',
            '-f', 's16le', '-acodec', 'pcm_s16le', '-ac', '2', '-i', '/dev/zero', '-acodec', 'libmp3lame', '-aq', '4',
            "-loglevel", "error",
            self.outfile]
        subprocess.run(command)

    async def __convert_aync__(self,tmp_dir,start_trim_sec,end_trim_sec):

        communicate = edge_tts.Communicate(
            text=self.soundtext, 
            voice=self.voice.name,
            rate=self.voice.rate,
            volume=self.voice.volume,
            pitch=self.voice.pitch,
            boundary='SentenceBoundary')
        await communicate.save(self.outfile)

        # trim
        probe = ffmpeg.probe(self.outfile)
        addfile_time = float(probe['format']['duration'])
        tmpAddFile = f'{tmp_dir}/{util.randomname(10)}.mp3'
        f1Time = timedelta(seconds=addfile_time-end_trim_sec)
        command = [
            "ffmpeg",
            "-i", self.outfile,
            "-ss", str(start_trim_sec),
            "-to", str(f1Time),
            "-c", "copy",
            "-loglevel", "error",
            tmpAddFile]
        # cmd = f'ffmpeg -c copy -loglevel error  -i {self.outfile} -ss {str(start_trim_sec)} -to {str(f1Time)} {tmpAddFile}'
        subprocess.run(command)
        shutil.move(tmpAddFile,self.outfile)

class Talk:
    """ 会話 """

    def create_instance(): 
        doc: dict = {}
        doc["sentences"] = list()
        return Talk(doc,None,None)
    
    def __init__(self,voices:Voices,dict_data:dict,setting: dict):
        self.list: list[Utterance]= []
        self.tmp_dir: str= f'/tmp/{util.randomname(10)}'
        self.voices = voices
        self.vs_change_dict = dict_data
        self.start_trim_sec = setting['cut-start'] if "cut-start" in setting else 0.0
        self.end_trim_sec = setting['crlf-interval'] if "crlf-interval" in setting else 0.0
        self.emptyline_break = setting['emptyline-break'] if "emptyline-break" in setting else 0.0
        os.mkdir(self.tmp_dir)
        pass
    
    def set_talk(self,talk: dict):
        for yaml_sentences in talk:
            voice_id = list(yaml_sentences.keys())[0]
            voice: Voice = copy.copy(self.voices.list[voice_id])
            if "voice" in yaml_sentences:
                voice.name = yaml_sentences["voice"]
            if "rate" in yaml_sentences:
                voice.rate = yaml_sentences["rate"]
            if "volume" in yaml_sentences:
                voice.volume = yaml_sentences["volume"]
            if "pitch" in yaml_sentences:
                voice.pitch = yaml_sentences["pitch"]
            for text in yaml_sentences[voice_id].split('\n'):
                soundtext = text
                if "words" in self.vs_change_dict:
                    for pattern in self.vs_change_dict["words"]:
                        replacing = self.vs_change_dict["words"][pattern]
                        soundtext = re.sub(pattern, f'{replacing}', soundtext)
                self.append(voice, soundtext, text)
        pass

    def append(self,voice:Voice,soundtext:str,text:str):
        self.list.append(Utterance(voice,soundtext,text,
                            self.start_trim_sec,self.end_trim_sec,self.emptyline_break))
        pass

    def convert_aync (self) :
        """ スピーチの変換を開始します
        save を実行するまではファイルは保存されません。
        """
        for utterance in self.list:
            utterance.convert_aync(self.tmp_dir)

    def save(self,outfile,srtfile):
        """ スピーチをmp3として保存します。

        Args:
            outfile (str): 保存するmp3ファイルの絶対パス
            srtfile (str): 保存する字幕ファイルの絶対パス
        """
        asyncio.run(self.__save__(outfile,srtfile))

    async def __save__(self,outfile,srtfile):
        tmp_outfile = f'{self.tmp_dir}/{util.randomname(10)}.mp3'
        shutil.copy('silent.mp3', outfile)
        for i,utterance in tqdm.tqdm(enumerate(self.list),total=len(self.list),unit="文"):
            shutil.copy(outfile,tmp_outfile)
            await utterance.task

            # get current info
            probe = ffmpeg.probe(outfile)
            outfile_time = timedelta(seconds=float(probe['format']['duration']))

            with open(f"{self.tmp_dir}/file_list.txt",mode="w", newline='\n') as file:
                file.writelines([f"file '{tmp_outfile}'\n",f"file '{utterance.outfile}'\n"])
            command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", f"{self.tmp_dir}/file_list.txt",
                "-y", 
                "-loglevel", "error",
                "-c", "copy",outfile]
            subprocess.run(command, stdout=subprocess.DEVNULL)

            # get current info
            probe = ffmpeg.probe(outfile)
            end_time = timedelta(seconds=float(probe['format']['duration']))

            if srtfile is not None or srtfile != '':
                with open(srtfile,mode="a", newline='\n') as srtfilebuf:
                    orgtext = re.sub('_','',utterance.originaltext) 
                    if orgtext:
                        srtfilebuf.writelines(
                            [f"{i}\n",
                            f"{str(util.convertHHmmssfff(outfile_time))} --> {str(util.convertHHmmssfff(end_time))}\n", f"{orgtext}\n", "\n"])
    
    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        shutil.rmtree(self.tmp_dir,) 
        pass