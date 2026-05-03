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


if __name__ == "__main__":
    """ main proc"""
    # 引数の取得
    parser = argparse.ArgumentParser(prog="text2mp3", usage="%(prog)s [options]")
    parser.add_argument("-i", "--input", required=True, help='input yaml file')
    parser.add_argument("-o", "--output", required=False, help='output mp3 file')
    parser.add_argument("-s", "--srt", required=False, help='srtfile file')
    parser.add_argument("-d", "--dict", required=False, help='word dictionary yaml')
    parser.add_argument("-g", "--global_dictionary", required=False, help='word dictionary yaml')
    args = parser.parse_args()
    args.output = args.output if args.output is not None else os.path.splitext( args.input )[0] + '.mp3'
    args.srt = args.srt if args.srt is not None else f'{os.path.splitext(args.output)[0]}.srt'
    
    # １文ごとの音声を保存するフォルダ作成
    outdir = os.path.splitext( args.output )[0]
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    srtpath = Path(args.srt)
    if srtpath.exists() and srtpath.is_file():
        os.remove( srtpath.absolute() )

    # 引数チェック
    __validate_args__(args)

    print(f'{args.input} -> {args.output}')

    # 辞書の情報の読み込み
    dict_data = dict()
    if args.global_dictionary is not None:
        try:
            dict_data = dict_data | yaml.safe_load(open(args.global_dictionary))
        except yaml.YAMLError as e:
            print(f"{args.global_dictionary}の構文エラー:")
            print(e)
    if args.dict is not None:
        try:
            dict_data = dict_data | yaml.safe_load(open(args.dict))
        except yaml.YAMLError as e:
            print(f"{args.dict}の構文エラー:")
            print(e)

    with open(args.input, encoding="utf-8") as f:
        try:
            doc = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"{args.input}の構文エラー:")
            print(e)

    # voice 情報の読み込み
    voices: speech.Voices = speech.Voices(doc['voices'])

    # text情報の読み込み
    with speech.Talk(voices,dict_data,doc['setting']) as talk_datas: 
        talk_datas.set_talk(doc['talk'])

        sem = asyncio.Semaphore(5)
        # 変換処理
        print("音声変換開始")
        asyncio.run(talk_datas.convertall_aync(sem))
        talk_datas.copy(outdir)
        print("行間の間を調整")
        talk_datas.trim()
        print("すべての音声を結合中")
        talk_datas.concat(args.output,args.srt)
