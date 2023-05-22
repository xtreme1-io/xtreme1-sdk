import json
import os
import numpy as np
import math
from os.path import *
import shutil
from nanoid import generate
from numpy.linalg import inv


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
                    obj['trackId'] = generate(size=16)
                if class_name is None:
                    if model_class:
                        obj['className'] = model_class
                objects.append(obj)

        f_json = {
            "sourceType": "EXTERNAL_GROUND_TRUTH",
            "objects": objects
        }
        file_name = splitext(basename(file))[0]
        new_file = join(dst, file_name + '.json')
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(f_json, f)
    return ''


def parse_coco(src, out):
    imgs = list_files(src, ['.jpg', '.png', '.jpeg', '.bmp'])
    coco_files = list_files(src, ['.json'])
    if not coco_files:
        error = 'The .json result file of coco format was not found in the zip package'
    elif len(coco_files) == 1:
        coco_file = coco_files[0]
        data = load_json(coco_file)
        images = data.get('images')
        categories = data.get('categories')
        annotations = data.get('annotations')
        if not images or not categories or not annotations:
            error = 'Cannot parse this format, unlike the coco standard format'
        else:
            id_name_mapping = {img['id']: img['file_name'] for img in images}
            id_label_mapping = {label['id']: label['name'] for label in categories}
            if not imgs:
                error = "The image('.jpg', '.png', '.jpeg', '.bmp') was not found in the zip package"
            else:
                image_dir = ensure_dir(join(out, 'image'))
                result_dir = ensure_dir(join(out, 'result'))
                for img_file in imgs:
                    new_img = join(image_dir, basename(img_file))
                    shutil.copyfile(img_file, new_img)
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
                                "points": points
                            }
                        }
                        objects.append(obj)
                    final_json = {
                        "sourceType": 'sourceType',
                        "sourceName": 'coco',
                        "objects": objects
                    }
                    with open(json_file, 'w', encoding='utf-8') as jf:
                        json.dump(final_json, jf)
                error = ''
    else:
        error = 'There are too many .json files to parse and expect only one .json file in the zip package'
    return error


def parse_kitti(kitti_dataset_dir, upload_dir):
    kittidataset = KittiDataset(kitti_dataset_dir, upload_dir)
    check_source = kittidataset.irregular_structure()
    if check_source:
        return check_source
    else:
        try:
            kittidataset.import_dataset()
            return ''
        except Exception as e:
            return e

class KittiDataset:
    def __init__(self, dataset_dir, output_dir):
        self.dataset_dir = dataset_dir
        self.calib_dir = join(dataset_dir, 'calib')
        self.image_dir = join(dataset_dir, 'image_2')
        self.label_dir = join(dataset_dir, 'label_2')
        self.velodyne_dir = join(dataset_dir, 'velodyne')
        if not self.irregular_structure():
            self.pc_dir = ensure_dir(join(output_dir, 'point_cloud'))
            self.image0_dir = ensure_dir(join(output_dir, 'image0'))
            self.camera_config_dir = ensure_dir(join(output_dir, 'camera_config'))
            self.result_dir = ensure_dir(join(output_dir, 'result'))

    def irregular_structure(self):
        check_info = []
        for _dir in [self.calib_dir, self.image_dir, self.label_dir, self.velodyne_dir]:
            if not exists(_dir):
                check_info.append(f"{_dir} is not exists")
        return check_info

    def import_dataset(self):
        for bin_file in list_files(self.velodyne_dir, '.bin'):
            file_name = splitext(basename(bin_file))[0]
            pcd_file = join(self.pc_dir, file_name + '.pcd')
            self.bin_to_pcd(bin_file, pcd_file)

            calib_file = join(self.calib_dir, file_name + '.txt')
            cfg_file = join(self.camera_config_dir, file_name + '.json')
            cam_param = self.parse_cam_param(calib_file, cfg_file)

            label_file = join(self.label_dir, file_name + '.txt')
            result_file = join(self.result_dir, file_name + '.json')
            self.parse_result(label_file, cam_param['camera_external'], result_file)

            img = join(self.image_dir, file_name + '.png')
            image0 = join(self.image0_dir, file_name + '.png')
            shutil.copyfile(img, image0)

    @staticmethod
    def alpha_in_pi(alpha):
        pi = math.pi
        return alpha - math.floor((alpha + pi) / (2 * pi)) * 2 * pi

    # 将点数据写入pcd文件(encoding=ascii)
    @staticmethod
    def bin_to_pcd(bin_file: str, pcd_file: str):
        try:
            with open(bin_file, 'rb') as bf:
                bin_data = bf.read()
                dtype = np.dtype([('x', 'float32'), ('y', 'float32'), ('z', 'float32'), ('i', 'float32')])
                points = np.frombuffer(bin_data, dtype=dtype)
                points = [list(o) for o in points]
                points = np.array(points)
                with open(pcd_file, 'wb') as pcd_file:
                    point_num = points.shape[0]
                    heads = [
                        '# .PCD v0.7 - Point Cloud Data file format',
                        'VERSION 0.7',
                        'FIELDS x y z i',
                        'SIZE 4 4 4 4',
                        'TYPE F F F U',
                        'COUNT 1 1 1 1',
                        f'WIDTH {point_num}',
                        'HEIGHT 1',
                        'VIEWPOINT 0 0 0 1 0 0 0',
                        f'POINTS {point_num}',
                        'DATA binary'
                    ]
                    header = '\n'.join(heads) + '\n'
                    header = bytes(header, 'ascii')
                    pcd_file.write(header)
                    pcd_file.write(points.tobytes())
        except Exception as e:
            print(f"{e}\n{bin_file} to {pcd_file} ===> failed : {bin_file} "
                  f"dtype isn't [('x','float32'),('y','float32'),('z','float32'),('i','float32')]")

    @staticmethod
    def parse_cam_param(calib_file, cfg_file):
            with open(calib_file, 'r', encoding='utf-8')as f:
                datas = f.readlines()
                p0 = np.array([float(x) for x in datas[0].split(' ')[1:]]).reshape(3, 4)
                p2 = np.array([float(x) for x in datas[2].split(' ')[1:]]).reshape(3, 4)
                r0 = np.array([float(x) for x in datas[4].split(' ')[1:]]).reshape(3, 3)
                r0 = np.hstack((r0, np.array([0, 0, 1]).reshape(-1, 1)))
                r0 = np.vstack((r0, np.array([0, 0, 0, 1])))
                ext0 = np.array([float(x) for x in datas[5].split(' ')[1:]]).reshape(3, 4)
                fx, cx, fy, cy = p2[0, 0], p2[0, 2], p2[1, 1], p2[1, 2]
                cam_t = p2[:, -1]
                ext_r = ext0[:, :3]
                ext_t = (np.array(ext0[:, -1]) + np.array(cam_t)) * 0.01
                ext2 = np.hstack((ext_r, ext_t.reshape(-1, 1)))
                lidar2cam_matrix = np.vstack((ext2, np.array([0, 0, 0, 1])))
                cfg_data = {

                    "camera_internal": {
                        "fx": fx,
                        "fy": fy,
                        "cx": cx,
                        "cy": cy
                    },
                    "camera_external": lidar2cam_matrix.flatten().tolist()
                }
                with open(cfg_file, 'w', encoding='utf-8') as cf:
                    json.dump([cfg_data], cf)
                return cfg_data


    def parse_result(self, label_file, cam_ext, result_file):
        ext_matrix = np.array(cam_ext).reshape(4, 4)
        with open(label_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            objects = []
            num = 1
            for line in lines:
                data = line.split(' ')
                label = data[0]
                if label in ['DontCare', 'Misc']:
                    continue
                x0, y0, x1, y1 = [float(x) for x in data[4:8]]
                height, width, length = [float(x) for x in data[8:11]]
                cam_center = [float(x) for x in data[11:14]]
                lidar_center = inv(ext_matrix) @ np.hstack((cam_center, [1]))
                ry = float(data[14])
                cam_to_lidar_point = inv(ext_matrix) @ np.array([np.cos(-ry), 0, np.sin(-ry), 1])
                point_0 = inv(ext_matrix) @ np.array([0, 0, 0, 1])
                rz = np.arctan2(cam_to_lidar_point[1] - point_0[1], cam_to_lidar_point[0]-point_0[0])

                track_id = generate(size=16)

                obj = {
                    "type": "3D_BOX",
                    "className": label,
                    "trackId": track_id,
                    "trackName": str(num),
                    "contour": {
                        "size3D": {
                            "x": length,
                            "y": width,
                            "z": height
                        },
                        "center3D": {
                            "x": lidar_center[0],
                            "y": lidar_center[1],
                            "z": lidar_center[2] + height/2
                        },
                        "rotation3D": {
                            "x": 0,
                            "y": 0,
                            "z": self.alpha_in_pi(rz)
                        }
                    }
                }
                objects.append(obj)
                obj_rect = {
                        "type": "2D_RECT",
                        "className": label,
                        "trackId": track_id,
                        "trackName": num,
                        "contour": {
                            "points": [{"x": x0, "y": y0}, {"x": x0, "y": y1},
                                       {"x": x1, "y": y1}, {"x": x1, "y": y0}],
                            "size3D": {"x": 0, "y": 0, "z": 0},
                            "center3D": {"x": 0, "y": 0, "z": 0},
                            "viewIndex": 0,
                            "rotation3D": {"x": 0, "y": 0, "z": 0}
                        }
                }
                objects.append(obj_rect)
                num += 1
            with open(result_file, 'w', encoding='utf-8')as rf:
                json.dump({"objects": objects}, rf)

