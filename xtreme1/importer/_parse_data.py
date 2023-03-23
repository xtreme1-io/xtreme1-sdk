import json
import os
from os.path import *
import shutil
import nanoid


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


def get_names(src_dir):
    name_list = []
    for file in list_files(src_dir, '.json'):
        results = load_json(file)
        for jc in results:
            for obj in jc['objects']:
                trc_name = obj.get('trackName')
                if trc_name is None:
                    continue
                else:
                    name_list.append(trc_name)
    return name_list


def parse_xtreme1(src, dst):
    names = get_names(src)
    name_num = 1
    for file in list_files(src, '.json'):
        results = load_json(file)
        objects = []
        for jc in results:
            for obj in jc['objects']:
                trc_name = obj.get('trackName')
                trc_id = obj.get('trackId')
                class_name = obj.get('className')
                model_class = obj.get('modelClass')
                if trc_name is None:
                    while True:
                        if str(name_num) not in names:
                            break
                        else:
                            name_num += 1
                    name = str(name_num)
                    names.append(name)
                    obj['trackName'] = name
                if trc_id is None:
                    obj['trackId'] = nanoid.generate(size=16)
                if class_name is None:
                    if model_class:
                        obj['className'] = model_class
                objects.append(obj)

        f_json = {
            "sourceType": "EXTERNAL_GROUND_TRUTH",
            "objects": objects
        }
        file_name = '-'.join(splitext(basename(file))[0].split('-')[:-1])
        new_file = join(dst, file_name + '.json')
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(f_json, f)
    return ''


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
                    "contour": {
                        "points": points}
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


