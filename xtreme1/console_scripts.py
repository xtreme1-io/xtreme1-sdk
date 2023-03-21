import argparse
import json
from .exporter.converter import Result
from .importer.parser import Parser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, help='export or upload', choices=['export', 'upload'])
    parser.add_argument('-src', type=str, help='source path')
    parser.add_argument('-out', type=str, help='The path to save the results')
    parser.add_argument('--rps', type=str, default=None, help='The json file in which the response is stored')
    parser.add_argument('--format', type=str, default='json', help='object format(json,coco,voc,labelme)',
                        choices=['coco', 'voc', 'labelme', 'xtreme1'])
    args = parser.parse_args()

    mode = args.mode
    src_path = args.src
    dst_path = args.out
    response = args.rps
    format = args.format

    try:
        if mode == 'export':
            anno = Result(src_zipfile=src_path)
            anno.convert(format=format, export_folder=dst_path)

        else:
            data_parser = Parser(source_path=src_path)
            data_parser.parser(format=format, output=dst_path)
        code = "OK"
        message = ""
    except Exception as e:
        code = "ERROR"
        message = str(e)

    rps_data = {
            "code": code,
            "message": message
        }
    if not response:
        print(rps_data)
    else:
        with open(response, 'w', encoding='utf-8') as rf:
            json.dump(rps_data, rf, ensure_ascii=False)


if __name__ == '__main__':
    main()
