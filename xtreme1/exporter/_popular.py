import os
import json
import base64
import warnings
import numpy as np
import math
import requests
from rich.progress import track
from datetime import datetime
from os.path import *
from xml.dom.minidom import Document
from .._version import __version__
from ..exceptions import ConverterException
from xtreme1._others import groupby


def _get_label(obj):
    if 'className' in obj.keys():
        label0 = obj['className']
        if label0:
            label = label0
        else:
            label = 'null'
    elif 'modelClass' in obj.keys():
        label0 = obj['modelClass']
        if label0:
            label = label0
        else:
            label = 'null'
    else:
        label = str('null')
    return label


def polygon_area(x, y):
    area = 0
    n = len(x)
    for i in range(n):
        j = (i + 1) % n
        area += x[i] * y[j]
        area -= x[j] * y[i]

    area = abs(area) / 2.0
    return round(area)


def ensure_dir(input_dir):
    if not exists(input_dir):
        os.makedirs(input_dir, exist_ok=True)
    return input_dir


def _to_coco(annotation: list, dataset_name: str, export_folder: str):
    images = []
    annotations = []
    categorys = []
    category_mapping = {}
    img_id = 0
    object_id = 0
    category_id = 1
    for anno in track(annotation, description='progress'):
        try:
            img_width = anno['data']['width']
            img_height = anno['data']['height']
            img_url = anno['data']['imageUrl']
            result = anno['result']
            if not result:
                continue
            else:
                objects = result['objects']
                for obj in objects:
                    label = _get_label(obj)
                    if label not in category_mapping.keys():
                        category_mapping[label] = category_id
                        category = {
                            "id": category_id,
                            "name": label,
                            "supercategory": "",
                            "attributes": {}
                        }
                        categorys.append(category)
                        category_id += 1

                    tool_type = obj['type']
                    points = obj['contour']['points']
                    if tool_type in ['RECTANGLE', 'BOUNDING_BOX']:
                        xl = [round(x['x']) for x in points]
                        yl = [round(y['y']) for y in points]
                        x0 = min(xl)
                        y0 = min(yl)
                        width = max(xl) - x0
                        height = max(yl) - y0
                        new_anno = {
                            "id": object_id,
                            "image_id": img_id,
                            "category_id": category_mapping[label],
                            "segmentation": [],
                            "area": width * height,
                            "bbox": [x0, y0, width, height],
                            "iscrowd": 0
                        }
                    elif tool_type == 'POLYGON':
                        segmentation = []
                        px = []
                        py = []
                        for point in points:
                            px.append(point['x'])
                            py.append(point['y'])
                            segmentation.append(round(point['x']))
                            segmentation.append(round(point['y']))
                        aera = polygon_area(px, py)
                        new_anno = {
                            "id": object_id,
                            "image_id": img_id,
                            "category_id": category_mapping[label],
                            "segmentation": segmentation,
                            "area": aera,
                            "bbox": [],
                            "iscrowd": 0
                        }
                    elif tool_type == 'POLYLINE':
                        keypoints = []
                        for point in points:
                            keypoints.append(round(point['x']))
                            keypoints.append(round(point['y']))
                            keypoints.append(2)
                        new_anno = {
                            "id": object_id,
                            "image_id": img_id,
                            "category_id": category_mapping[label],
                            "segmentation": [],
                            "bbox": [],
                            "keypoints": keypoints,
                            "num_keypoints": len(points),
                            "iscrowd": 0
                        }
                    else:
                        continue
                    attributes = {}
                    class_values = obj['classValues']
                    if class_values:
                        for cv in class_values:
                            attributes[cv['name']] = cv['value']
                    if attributes:
                        new_anno['attributes'] = attributes
                    if 'modelConfidence' in obj.keys():
                        new_anno['score'] = obj['modelConfidence']
                    annotations.append(new_anno)
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
            raise ConverterException

    info = {
        "contributor": "",
        "date_created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description":
            f'Basic AI Xtreme1 dataset {dataset_name} exported to COCO format (https://github.com/basicai/xtreme1)',
        "url": "https://github.com/basicai/xtreme1",
        "year": f"{datetime.utcnow().year}",
        "version": __version__,
    }

    anno_json = {
        "info": info,
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": categorys
    }
    save_json = join(export_folder, f'{dataset_name}_coco.json')
    with open(save_json, 'w', encoding='utf-8') as jf:
        json.dump(anno_json, jf, indent=1, ensure_ascii=False)


def _to_voc(annotation: list, export_folder: str):
    for anno in track(annotation, description='progress'):
        try:
            file_name = anno['data'].get('name')
            xml_file = join(export_folder, file_name + '.xml')
            img_width = anno['data']['width']
            img_height = anno['data']['height']
            img_url = anno['data']['imageUrl']
            result = anno['result']
            if not result:
                continue
            else:
                objects = result['objects']

                doc = Document()
                root = doc.createElement('annotation')
                doc.appendChild(root)

                _folder = doc.createElement('folder')
                root.appendChild(_folder)
                folder_text = doc.createTextNode(img_url.split('?')[0].split('/')[-1])
                _folder.appendChild(folder_text)

                filename = doc.createElement('filename')
                root.appendChild(filename)
                filename_text = doc.createTextNode(img_url.split('?')[0].split('/')[-1])
                filename.appendChild(filename_text)

                source = doc.createElement('source')
                root.appendChild(source)
                database = doc.createElement('database')
                source.appendChild(database)
                database_text = doc.createTextNode('Unknown')
                database.appendChild(database_text)

                size = doc.createElement('size')
                root.appendChild(size)

                _width = doc.createElement('width')
                size.appendChild(_width)
                width_text = doc.createTextNode(str(img_width))
                _width.appendChild(width_text)

                _height = doc.createElement('height')
                size.appendChild(_height)
                height_text = doc.createTextNode(str(img_height))
                _height.appendChild(height_text)

                depth = doc.createElement('depth')
                size.appendChild(depth)
                depth_text = doc.createTextNode('3')
                depth.appendChild(depth_text)

                segmented = doc.createElement('segmented')
                root.appendChild(segmented)
                segmented_text = doc.createTextNode('0')
                segmented.appendChild(segmented_text)

                for obj in objects:
                    label = _get_label(obj)
                    points = obj['contour']['points']
                    points_x = [round(x['x']) for x in points]
                    points_y = [round(y['y']) for y in points]

                    tool_type = obj['type']
                    if tool_type in ['RECTANGLE', 'BOUNDING_BOX']:

                        _object = doc.createElement('object')
                        root.appendChild(_object)

                        sup_cate = doc.createElement('supercategory')
                        _object.appendChild(sup_cate)
                        sup_cate_text = doc.createTextNode('')
                        sup_cate.appendChild(sup_cate_text)

                        _name = doc.createElement('name')
                        _object.appendChild(_name)
                        name_text = doc.createTextNode(label)
                        _name.appendChild(name_text)

                        _pose = doc.createElement('pose')
                        _object.appendChild(_pose)
                        pose_text = doc.createTextNode('Unspecified')
                        _pose.appendChild(pose_text)

                        _truncated = doc.createElement('truncated')
                        _object.appendChild(_truncated)
                        truncated_text = doc.createTextNode('0')
                        _truncated.appendChild(truncated_text)

                        _difficult = doc.createElement('difficult')
                        _object.appendChild(_difficult)
                        difficult_text = doc.createTextNode('0')
                        _difficult.appendChild(difficult_text)

                        class_values = obj['classValues']
                        for cv in class_values:
                            _attrk = doc.createElement(cv['name'])
                            _object.appendChild(_attrk)
                            _attrv_text = doc.createTextNode(cv['value'])
                            _attrk.appendChild(_attrv_text)

                        _bndbox = doc.createElement('bndbox')
                        _object.appendChild(_bndbox)

                        xmin = doc.createElement('xmin')
                        _bndbox.appendChild(xmin)
                        xmin_text = doc.createTextNode(str(min(points_x)))
                        xmin.appendChild(xmin_text)

                        ymin = doc.createElement('ymin')
                        _bndbox.appendChild(ymin)
                        ymin_text = doc.createTextNode(str(min(points_y)))
                        ymin.appendChild(ymin_text)

                        xmax = doc.createElement('xmax')
                        _bndbox.appendChild(xmax)
                        xmax_text = doc.createTextNode(str(max(points_x)))
                        xmax.appendChild(xmax_text)

                        ymax = doc.createElement('ymax')
                        _bndbox.appendChild(ymax)
                        ymax_text = doc.createTextNode(str(max(points_y)))
                        ymax.appendChild(ymax_text)

                    else:
                        warnings.warn(
                            message=f"This format not support {tool_type}")
                        continue

                with open(xml_file, 'wb+') as xml_file:
                    xml_file.write(doc.toprettyxml(encoding='utf-8'))


        except Exception:
            raise ConverterException


def _to_yolo(annotation: list, dataset_name: str, export_folder: str):
    pass


def _to_labelme(annotation: list, export_folder: str):
    type_mapping = {
        "RECTANGLE": 'rectangle',
        "POLYGON": 'polygon',
        "POLYLINE": 'polyline'
    }
    for anno in track(annotation, description='progress'):
        try:
            file_name = anno['data'].get('name')
            json_file = join(export_folder, file_name + '.json')
            annotations = []
            img_width = anno['data']['width']
            img_height = anno['data']['height']
            img_url = anno['data']['imageUrl']
            rps = requests.get(img_url)
            img_f_base64 = base64.b64encode(rps.content)
            img_data = img_f_base64.decode()
            result = anno['result']
            if not result:
                continue
            else:
                objects = result['objects']
                for obj in objects:
                    label = _get_label(obj)
                    points = []
                    points_x = []
                    points_y = []
                    for point in obj['contour']['points']:
                        points.append([round(point['x']), round(point['y'])])
                        points_x.append(round(point['x']))
                        points_y.append(round(point['y']))

                    tool_type = obj['type']
                    if tool_type == 'RECTANGLE':
                        coordinate = [[min(points_x), min(points_y)], [max(points_x), min(points_y)],
                                      [max(points_x), max(points_y)], [min(points_x), max(points_y)]]
                    else:
                        coordinate = points
                    attributes = {}
                    class_values = obj['classValues']
                    for cv in class_values:
                        attributes[cv['name']] = cv['value']

                    new_anno = {
                        "label": label,
                        "points": coordinate,
                        "group_id": None,
                        "shape_type": type_mapping[tool_type],
                        "flags": {}
                    }
                    if attributes:
                        new_anno['attributes'] = attributes
                    annotations.append(new_anno)
                anno_json = {
                    "version": "5.0.1",
                    "flags": {},
                    "shapes": annotations,
                    "imagePath": img_url.split('?')[0].split('/')[-1],
                    "imageData": img_data,
                    "imageHeight": img_height,
                    "imageWidth": img_width
                }
                with open(json_file, 'w', encoding='utf-8') as nf:
                    json.dump(anno_json, nf, indent=1, ensure_ascii=False)

        except Exception:
            raise ConverterException


def alpha_in_pi(a):
    pi = math.pi
    return a - math.floor((a + pi) / (2 * pi)) * 2 * pi


def gen_alpha(rz, ext_matrix, lidar_center):
    lidar_center = np.hstack((lidar_center, np.array([1])))

    cam_point = ext_matrix @ np.array([np.cos(rz), np.sin(rz), 0, 1])
    cam_point_0 = ext_matrix @ np.array([0, 0, 0, 1])
    ry = -1 * (alpha_in_pi(np.arctan2(cam_point[2] - cam_point_0[2], cam_point[0] - cam_point_0[0])))
    cam_center = ext_matrix @ lidar_center.T
    theta = alpha_in_pi(np.arctan2(cam_center[0], cam_center[2]))
    alpha = ry - theta
    return ry, alpha


def find_attr(data_list, target_key):
    attrs_map = {x['name']: x['value'] for x in data_list}
    return eval(attrs_map.get(target_key, '0'))


def _to_kitti(annotation: list, export_folder: str):
    for anno in track(annotation, description='progress'):
        data_info = anno['data']
        file_name = data_info.get('name')
        anno_objects = anno['result'].get('objects')
        if anno_objects:
            config_url = data_info['cameraConfig']['url']
            cam_param = requests.get(config_url).json()
            obj_rect = {f"{x['trackId']}-{x['contour']['viewIndex']}": x for x in anno_objects if
                        x['type'] == '2D_RECT'}
            obj_3d = {x['trackId']: x for x in anno_objects if x['type'] == '3D_BOX'}
            for rect in obj_rect.values():
                cam_index = rect['contour']['viewIndex']
                ext_matrix = np.array(cam_param[cam_index]['camera_external']).reshape(4, 4)
                label = rect['className']

                try:
                    truncated = find_attr(rect['classValues'], 'truncated')
                    occluded = find_attr(rect['classValues'], 'occluded')
                except Exception:
                    truncated = "%.2f" % 0
                    occluded = 0

                x_list = []
                y_list = []
                for one_point in rect['contour']['points']:
                    x_list.append(one_point['x'])
                    y_list.append(one_point['y'])
                if rect['trackId'] in obj_3d.keys():
                    contour_3d = obj_3d[rect['trackId']]['contour']
                    length, width, height = contour_3d['size3D'].values()
                    cur_rz = contour_3d['rotation3D']['z']

                    ry, alpha = gen_alpha(cur_rz, ext_matrix, np.array(list(contour_3d['center3D'].values())))

                    point = list(contour_3d['center3D'].values())
                    temp = np.hstack((np.array([point[0], point[1], point[2] - height / 2]), np.array([1])))
                    x, y, z = list((ext_matrix @ temp))[:3]
                    score = 1
                    string = f"{label} {truncated} {occluded} {alpha:.2f} " \
                             f"{min(x_list):.2f} {min(y_list):.2f} {max(x_list):.2f} {max(y_list):.2f} " \
                             f"{height:.2f} {width:.2f} {length:.2f} " \
                             f"{x:.2f} {y:.2f} {z:.2f} {ry:.2f} {score}\n"
                else:
                    string = f"DontCare -1 -1 -10 " \
                             f"{min(x_list):.2f} {min(y_list):.2f} {max(x_list):.2f} {max(y_list):.2f} " \
                             f"-1 -1 -1 -1000 -1000 -1000 -10\n"
                txt_file = join(export_folder, f"label_{cam_index}", file_name + '.txt')
                ensure_dir(dirname(txt_file))
                with open(txt_file, 'a+', encoding='utf-8') as tf:
                    tf.write(string)
        else:
            continue


def _to_kitti_like(annotation: list, export_folder: str):
    for anno in track(annotation, description='progress'):
        data_info = anno['data']
        file_name = data_info.get('name')
        anno_objects = anno['result'].get('objects')
        if anno_objects:
            config_url = data_info['cameraConfig']['url']
            cam_param = requests.get(config_url['url']).json()
            n_cams = len(cam_param)
            rects = [x for x in anno_objects if x['type'] == '2D_RECT']
            rect_map = groupby(rects, func=lambda x: x["trackId"])
            obj_3d = {x['trackId']: x for x in anno_objects if x['type'] == '3D_BOX'}

            # 补充2D结果
            for track_id, inst_3d in obj_3d.items():
                label = inst_3d["className"]
                cur_views = {x["contour"]["viewIndex"] for x in rect_map.get(track_id, [])}
                for view_id in range(n_cams):
                    if view_id in cur_views:
                        continue

                    add_rect = {
                        "type": "2D_RECT",
                        "trackId": track_id,
                        "classValues": [],
                        "contour": {
                            "points": [
                                {
                                    "x": 0,
                                    "y": 0
                                },
                                {
                                    "x": 0,
                                    "y": 0
                                }
                            ],
                            "viewIndex": view_id
                        },
                        "className": label
                    }
                    rects.append(add_rect)

            for rect in rects:
                cam_index = rect['contour']['viewIndex']
                ext_matrix = np.array(cam_param[cam_index]['camera_external']).reshape(4, 4)
                label = rect['className']

                try:
                    truncated = find_attr(rect['classValues'], 'truncated')
                    occluded = find_attr(rect['classValues'], 'occluded')
                except Exception:
                    truncated = "%.2f" % 0
                    occluded = 0

                x_list = []
                y_list = []
                for one_point in rect['contour']['points']:
                    x_list.append(one_point['x'])
                    y_list.append(one_point['y'])
                if rect['trackId'] in obj_3d.keys():
                    contour_3d = obj_3d[rect['trackId']]['contour']
                    length, width, height = contour_3d['size3D'].values()
                    cur_rz = contour_3d['rotation3D']['z']

                    ry, alpha = gen_alpha(cur_rz, ext_matrix, np.array(list(contour_3d['center3D'].values())))

                    point = list(contour_3d['center3D'].values())
                    temp = np.hstack((np.array([point[0], point[1], point[2] - height / 2]), np.array([1])))
                    x, y, z = list((ext_matrix @ temp))[:3]
                    score = 1
                    string = f"{label} {truncated} {occluded} {alpha:.2f} " \
                             f"{min(x_list):.2f} {min(y_list):.2f} {max(x_list):.2f} {max(y_list):.2f} " \
                             f"{height:.2f} {width:.2f} {length:.2f} " \
                             f"{x:.2f} {y:.2f} {z:.2f} {ry:.2f} {score}\n"
                else:
                    string = f"DontCare -1 -1 -10 " \
                             f"{min(x_list):.2f} {min(y_list):.2f} {max(x_list):.2f} {max(y_list):.2f} " \
                             f"-1 -1 -1 -1000 -1000 -1000 -10\n"
                txt_file = join(export_folder, f"label_{cam_index}", file_name + '.txt')
                ensure_dir(dirname(txt_file))
                with open(txt_file, 'a+', encoding='utf-8') as tf:
                    tf.write(string)
        else:
            continue
