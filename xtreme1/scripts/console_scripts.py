import argparse
from ..exporter.converter import Result
import json
from .display_script import parse_coco
from ..exceptions import DisplayException


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, help='export or upload', choices=['export', 'upload'])
    parser.add_argument('-src', type=str, help='source path')
    parser.add_argument('-out', type=str, help='The path to save the results')
    parser.add_argument('--rps', type=str, default=None, help='The json file in which the response is stored')
    parser.add_argument('--format', type=str, default='json', help='object format(json,coco,voc,labelme)',
                        choices=['coco', 'voc', 'labelme'])
    args = parser.parse_args()

    mode = args.mode
    src_path = args.src
    dst_path = args.out
    response = args.rps
    format = args.format

    if mode == 'export':
        try:
            anno = Result(src_zipfile=src_path)
            anno.convert(format=format, export_folder=dst_path)
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
    else:
        try:
            if format == 'coco':
                msg = parse_coco(src_path, dst_path)
                if not msg:
                    code = "OK"
                else:
                    code = 'ERROR'
                message = msg
            else:
                raise DisplayException(message=f'Do not support this format:<{format}> to display')
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
