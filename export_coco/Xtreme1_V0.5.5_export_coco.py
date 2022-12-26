# -*- coding: utf-8 -*-
"""
Script to convert Xtreme1 standard format to coco format for Xtreme1 V0.5.5 image annotation
setup: pip install numpy opencv-python tqdm
usage: python Xtreme1_V0.5.5_export_coco.py <zipfile> <save folder>
"""
import os
import json
import zipfile
import cv2
import numpy as np
import shutil
from tqdm import tqdm
from datetime import datetime
from os.path import join, basename, dirname, splitext, exists


def list_files(in_path: str, match: str):
    file_list = []
    for root, _, files in os.walk(in_path):
        for file in files:
            if splitext(file)[-1] == match:
                file_list.append(join(root, file))
    return file_list


def load_json(json_file: str):
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
        json_content = json.loads(content)
    return json_content


def unzip_file(zip_src: str, dst_dir: str):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        print('This is not zip')


def coco_converter(dst_dir: str, dataset_name: str):
    result_path = join(dst_dir, os.listdir(dst_dir)[0], 'result')
    data_path = join(dst_dir, os.listdir(dst_dir)[0], 'data')
    export_path = join(dst_dir, f'x1 dataset {dataset_name} annotations')
    if not exists(export_path):
        os.mkdir(export_path)
    images = []
    annotation = []
    categorys = []
    category_mapping = {}
    img_id = 0
    object_id = 0
    category_id = 1
    for file in tqdm(list_files(result_path, '.json'), desc='progress'):
        try:
            file_name = basename(file)
            data_file = join(data_path, file_name)
            result_content = load_json(file)
            data_content = load_json(data_file)
            img_width = data_content['width']
            img_height = data_content['height']
            img_url = data_content['imageUrl']
            objects = result_content['objects']
            for obj in objects:
                class_name = obj['className']
                if class_name not in category_mapping.keys():
                    category_mapping[class_name] = category_id
                    category = {
                        "id": category_id,
                        "name": class_name,
                        "supercategory": "",
                        "attributes": {}
                    }
                    categorys.append(category)
                    category_id += 1
                score = obj['modelConfidence']
                tool_type = obj['type']
                if tool_type == 'RECTANGLE':
                    points = obj['contour']['points']
                    xl = []
                    yl = []
                    for point in points:
                        xl.append(point['x'])
                        yl.append(point['y'])
                    x0 = min(xl)
                    y0 = min(yl)
                    width = max(xl)-x0
                    height = max(yl)-y0
                    attributes = {}
                    class_values = obj['classValues']
                    for cv in class_values:
                        attributes[cv['name']] = cv['value']
                    anno = {
                        "id": object_id,
                        "image_id": img_id,
                        "category_id": category_mapping[class_name],
                        "segmentation": [],
                        "score": score,
                        "area": width*height,
                        "bbox": [x0, y0, width, height],
                        "iscrowd": 0,
                        "attributes": attributes
                    }
                    annotation.append(anno)
                    object_id += 1
                elif tool_type == 'POLYGON':
                    segmentation = []
                    coordinate = []
                    points = obj['contour']['points']
                    for point in points:
                        coordinate.append([int(point['x']), int(point['y'])])
                        segmentation.append(point['x'])
                        segmentation.append(point['y'])
                    mask = np.zeros((img_height, img_width), dtype=np.int32)
                    cv2.fillPoly(mask, [np.array(coordinate)], 1)
                    aera = int(np.sum(mask))
                    attributes = {}
                    class_values = obj['classValues']
                    for cv in class_values:
                        attributes[cv['name']] = cv['value']
                    anno = {
                        "id": object_id,
                        "image_id": img_id,
                        "category_id": category_mapping[class_name],
                        "segmentation": segmentation,
                        "score": score,
                        "area": aera,
                        "bbox": [],
                        "iscrowd": 0,
                        "attributes": attributes
                    }
                    annotation.append(anno)
                    object_id += 1
                elif tool_type == 'POLYLINE':
                    keypoints = []
                    points = obj['contour']['points']
                    for point in points:
                        keypoints.append(point['x'])
                        keypoints.append(point['y'])
                        keypoints.append(2)

                    attributes = {}
                    class_values = obj['classValues']
                    for cv in class_values:
                        attributes[cv['name']] = cv['value']
                    anno = {
                        "id": object_id,
                        "image_id": img_id,
                        "category_id": category_mapping[class_name],
                        "segmentation": [],
                        "bbox": [],
                        "keypoints": keypoints,
                        "num_keypoints": len(points),
                        "score": score,
                        "iscrowd": 0
                    }
                    annotation.append(anno)
                    object_id += 1

            one_image = {
                    "id": img_id,
                    "license": 0,
                    "file_name": img_url.split('?')[0].split('/')[-1],
                    "xtreme1_url": img_url,
                    "width": img_width,
                    "height": img_height,
                    "date_captured": None
            }
            images.append(one_image)
            img_id += 1
        except Exception:
            continue

    info = {
        "contributor": "",
        "date_created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description":
            f'Basic AI Xtreme1 dataset {dataset_name} exported to COCO format (https://github.com/basicai/xtreme1)',
        "url": "https://github.com/basicai/xtreme1",
        "year": f"{datetime.utcnow().year}",
        "version": "Basic AI V1.0",
    }

    final_json = {
        "info": info,
        "licenses": [],
        "images": images,
        "annotations": annotation,
        "categories": categorys
    }
    save_json = join(export_path, 'coco_results.json')
    with open(save_json, 'w', encoding='utf-8') as jf:
        json.dump(final_json, jf, indent=1, ensure_ascii=False)
    shutil.rmtree(dirname(result_path))
    print(f"*** coco format results have been saved in {save_json} ***")


def main(zip_src: str, dst_dir: str):
    dataset_name = splitext(basename(zip_src))[0].split('-')[0]
    unzip_file(zip_src, dst_dir)
    coco_converter(dst_dir, dataset_name)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('zip_src', type=str, help='The path of the zip file')
    parser.add_argument('dst_dir', type=str, help='The save folder')
    args = parser.parse_args()

    zip_src = args.zip_src
    dst_dir = args.dst_dir
    if len(os.listdir(dst_dir)):
        input("The save folder needs to be empty, press any key to exit")
    else:
        main(zip_src, dst_dir)
        input("Complete, press any key to exit")




