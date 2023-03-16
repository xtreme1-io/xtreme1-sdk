import argparse
from xtreme1.exporter.converter import Result
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src_zip', type=str, help='zip file path')
    parser.add_argument('dst_path', type=str, help='The path to save the results')
    parser.add_argument('--format', type=str, default='json', help='object format(json,coco,voc,labelme)')
    args = parser.parse_args()

    src_zip = args.src_zip
    dst_path = args.dst_path
    format = args.format

    try:
        anno = Result(src_zipfile=src_zip)
        anno.convert(format=format, export_folder=dst_path)
        code = "OK"
        message = ""
    except Exception as e:
        code = "failed"
        message = e
    print(json.dumps({
        "code": code,
        "message": message
    }))
