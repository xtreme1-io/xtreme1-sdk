import json
import argparse
import os
from os.path import *
import shutil
from ..exceptions import DisplayException


def list_files(in_path: str, match):
    file_list = []
    for root, _, files in os.walk(in_path):
        for file in files:
            if splitext(file)[-1] in match:
                file_list.append(join(root, file))
    return file_list


def load_json(json_file: str):
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
        json_content = json.loads(content)
    return json_content


def ensure_dir(input_dir):
    if not exists(input_dir):
        os.makedirs(input_dir, exist_ok=True)
    return input_dir


def parse_coco(src, out):
    imgs = list_files(src, ['.jpg', '.png', '.jpeg', '.bmp'])
    coco_file = list_files(src, ['.json'])[0]
    data = load_json(coco_file)
    images = data['images']
    categories = data['categories']
    annotations = data['annotations']
    id_name_mapping = {img['id']: img['file_name'] for img in images}
    id_label_mapping = {label['id']: label['name'] for label in categories}
    if not imgs:
        error = 'The image was not found in the zip package'
    else:
        image_dir = ensure_dir(join(out, 'image'))
        result_dir = ensure_dir(join(out, 'result'))
        for img_file in imgs:
            new_img = join(image_dir, basename(img_file))
            shutil.copyfile(img_file, new_img)
        error = ''
        name_anno_mapping = {}
        for img_id in id_name_mapping.keys():
            name_anno_mapping[id_name_mapping[img_id]] = [x for x in annotations if x['image_id'] == img_id]

        for name, annos in name_anno_mapping.items():
            json_file = join(result_dir, splitext(name)[0] + '.json')
            objects = []
            for anno in annos:
                if anno['bbox']:
                    bbox = anno['bbox']
                    tool_type = 'RECTANGLE'
                    points = [{"x": bbox[0], "y": bbox[1]}, {"x": bbox[0]+bbox[2], "y": bbox[1]+bbox[3]}]
                elif anno['segmentation']:
                    tool_type = 'POLYGON'
                    segment = anno['segmentation']
                    points = [{"x": seg_point[0], "y": seg_point[1]}
                              for seg_point in [segment[i:i+2] for i in range(len(segment))[::2]]]
                elif anno['keypoints']:
                    tool_type = 'POLYLINE'
                    line = anno['keypoints']
                    points = [{"x": key_point[0], "y": key_point[1]}
                              for key_point in [line[i:i + 2] for i in range(len(line))[::3]]]
                else:
                    continue

                obj = {
                    "type": tool_type,
                    "trackName": str(anno['id']),
                    "className": id_label_mapping[anno['category_id']],
                    "contour": points
                }
                objects.append(obj)
            final_json = {
                "sourceType": 'sourceType',
                "sourceName": 'coco',
                "objects": objects
            }
            with open(json_file, 'w', encoding='utf-8') as jf:
                json.dump(final_json, jf)
    return error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', type=str, help='source path')
    parser.add_argument('-out', type=str, help='The path to save the display datas')
    parser.add_argument('-rps', type=str, help='The json file in which the response is stored')
    parser.add_argument('--format', type=str, default='coco', help='object format(coco)', choices=['coco', 'json'])
    args = parser.parse_args()

    src_path = args.src
    dst_path = args.out
    response = args.rps
    format = args.format

    # src_path = r"D:\Desktop\测试脚本\save"
    # dst_path = r"D:\Desktop\测试脚本\save"
    # response = r"D:\Desktop\测试脚本\save\log.json"
    # format = 'coco'

    try:
        if format == 'coco':
            msg = parse_coco(src_path, dst_path)
            if not msg:
                code = "OK"
            else:
                code = 'failed'
            message = msg
        else:
            raise DisplayException(message=f'Do not support this format:<{format}> to display')
    except Exception as e:
        code = "failed"
        message = str(e)
    with open(response, 'w', encoding='utf-8') as rf:
        json.dump({
            "code": code,
            "message": message
        }, rf, ensure_ascii=False)
# main()




