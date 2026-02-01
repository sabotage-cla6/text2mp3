from collections import namedtuple

class Voice:
    def __init__(self,name):
        self.name: str = name
        self.rate: str = '+0%'
        self.volumn: str = '+0%'
        self.pitch: str = '+0Hz'

class Utterance:
    def __init__(self,voice,soundtext,originaltext):
        self.voice = voice
        self.soundtext = soundtext
        self.originaltext = originaltext
        pass

class Talk:

    def __init__(self):
        self.list: list[Utterance]= []
        pass
    
    def append(self,voice:Voice,soundtext:str,text:str):
        a = Utterance(voice,soundtext,text)
        self.list.append(a)
        pass
