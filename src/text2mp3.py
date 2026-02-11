import edge_tts
import ffmpeg
import asyncio
import re


class Text2mp3:

    async def convert(text,outputfile,voice=edge_tts.constants.DEFAULT_VOICE,
                 rate: str = "+0%",
                 volume: str = "+0%",
                 pitch: str = "+0Hz"):
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate,volume=volume,pitch=pitch,boundary='SentenceBoundary')
        await communicate.save(outputfile)

        # with open(outputfile, "wb") as file:
        #     async for chunk in communicate.stream():
        #         if chunk["type"] == "audio":
        #             file.write(chunk["data"])
