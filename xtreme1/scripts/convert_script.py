import argparse
from xtreme1.exporter.converter import Result
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', type=str, help='zip file path')
    parser.add_argument('-out', type=str, help='The path to save the results')
    parser.add_argument('-rps', type=str, help='The json file in which the response is stored')
    parser.add_argument('--format', type=str, default='json', help='object format(json,coco,voc,labelme)',
                        choices=['coco', 'json', 'voc', 'labelme'])
    args = parser.parse_args()

    src_zip = args.src
    dst_path = args.out
    response = args.rps
    format = args.format

    try:
        anno = Result(src_zipfile=src_zip)
        anno.convert(format=format, export_folder=dst_path)
        code = "OK"
        message = ""
    except Exception as e:
        code = "failed"
        message = str(e)
    with open(response, 'w', encoding='utf-8') as rf:
        json.dump({
            "code": code,
            "message": message
        }, rf, ensure_ascii=False)
