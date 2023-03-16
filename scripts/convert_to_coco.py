import argparse
from xtreme1.exporter.converter import Result
import json


def main(src_zip, dst_path):
    try:
        anno = Result(src_zipfile=src_zip, export_folder=dst_path)
        anno.to_coco()
        code = "OK"
        message = ""
    except Exception as e:
        code = "failed"
        message = e
    print(json.dumps({
        "code": code,
        "message": message
    }))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src_zip', type=str)
    parser.add_argument('dst_path', type=str)
    args = parser.parse_args()

    src_zip = args.src_zip
    dst_path = args.dst_path

    main(src_zip, dst_path)
