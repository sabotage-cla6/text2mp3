import os
from pathlib import Path
import argparse
import yaml
import speech
import asyncio

CUT_START = 0.12
CUT_SEC = 0.72
tmp_dir = ''

def __validate_args__(args):
    """ 引数チェック """
    if not os.path.isfile(args.input):
        raise FileNotFoundError(f"入力ファルが見つかりません。{args.input}")
    if args.dict is not None:
        if not os.path.isfile(args.dict):
            raise FileNotFoundError(f"辞書ファイルがいつ借りません。{args.dict}")


if __name__ == "__main__":
    """ main proc"""
    # 引数の取得
    parser = argparse.ArgumentParser(prog="text2mp3", usage="%(prog)s [options]")
    parser.add_argument("-o", "--output", required=False, help='output mp3 file')
    parser.add_argument("-s", "--srt", required=False, help='srtfile file')
    parser.add_argument("-i", "--input", required=False, help='input yaml file')
    parser.add_argument("-d", "--dict", required=False, help='word dictionary yaml')
    args = parser.parse_args()
    args.output = args.output if args.output is not None else os.path.splitext( args.input )[0] + '.mp3'
    args.srt = args.srt if args.srt is not None else f'{os.path.splitext(args.output)[0]}.srt'
    
    srtpath = Path(args.srt)
    if srtpath.exists() and srtpath.is_file():
        os.remove( srtpath.absolute() )

    # 引数チェック
    __validate_args__(args)

    print(f'{args.input} -> {args.output}')

    # 辞書の情報の読み込み
    dict_data = dict()
    if args.dict is not None:
        dict_data = yaml.safe_load(open(args.dict))

    with open(args.input, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    # voice 情報の読み込み
    voices: speech.Voices = speech.Voices(doc)

    # text情報の読み込み
    with speech.Talk(doc,voices,dict_data) as talk_datas: 
        talk_datas.start_trim_sec = doc['setting']['cut-start']
        talk_datas.start_trim_sec = talk_datas.start_trim_sec if talk_datas.start_trim_sec is not None else CUT_START
        talk_datas.end_trim_sec = doc['setting']['crlf-interval']
        talk_datas.end_trim_sec = talk_datas.end_trim_sec if talk_datas.end_trim_sec is not None else CUT_SEC   

        # 変換処理
        queue = asyncio.Queue()
        talk_datas.convert_aync()
        talk_datas.save(args.output,args.srt)
