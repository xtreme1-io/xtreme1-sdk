import zipfile
import json
import os

from os.path import *
from ..exceptions import *
from ..exporter.annotation import __supported_format__
from ..exporter._standard import _to_json
from ..exporter._popular import _to_coco, _to_voc, _to_labelme, _to_kitti, _to_kitti_like


class Result:
    __SUPPORTED_FORMAT_INFO = __supported_format__

    def __init__(self,
                 src_zipfile: str,
                 dropna: bool = False
                 ):
        if zipfile.is_zipfile(src_zipfile):
            self.src_zipfile = src_zipfile
        else:
            raise SDKException(code='SourceError', message=f'{src_zipfile} is not zip')
        zip_name = basename(src_zipfile)
        self.dataset_name = '-'.join(splitext(zip_name)[0].split('-')[:-1])
        self.dropna = dropna
        self.annotation = self.__reconstitution()

    def __setattr__(self, key, value):
        if key == '_SUPPORTED_FORMAT':
            raise NoPermissionException(message='You are performing an operation that is not allowed')
        else:
            self.__dict__[key] = value

    def __reconstitution(self):
        dropna = self.dropna
        zip_file = zipfile.ZipFile(self.src_zipfile, 'r')
        file_list = zip_file.namelist()
        results = []
        datas = []
        for fl in file_list:
            pts = fl.strip('/').split('/')
            if len(pts) >= 2 and pts[-2] == 'result':
                results.append(fl)
            elif len(pts) >= 2 and pts[-2] == 'data':
                datas.append(fl)
        id_result = {}
        annotation = []
        for result in results:
            result_content = json.loads(zip_file.read(result))[0]
            objs = []
            for obj in json.loads(zip_file.read(result)):
                objs.extend(obj['objects'])
            result_content['objects'] = objs
            id_result[result_content['dataId']] = result_content
        for data in datas:
            data_content = json.loads(zip_file.read(data))
            data_result = id_result.get(data_content['dataId'], {})
            anno = {
                'data': data_content,
                'result': data_result
            }
            if dropna:
                if data_result:
                    annotation.append(anno)
                else:
                    continue
            else:
                annotation.append(anno)
        return annotation

    def __str__(self):
        return f"Offline annotation(dataset_name={self.dataset_name})"

    def __repr__(self):
        return f"Offline annotation(dataset_name={self.dataset_name})"

    def __gen_dir(self, input_dir):
        # save_folder = join(input_dir, f'x1 dataset {self.dataset_name} annotations')
        if not exists(input_dir):
            os.makedirs(input_dir, exist_ok=True)
        return input_dir

    def __ensure_dir(self, input_dir):
        if input_dir:
            export_folder = input_dir
        else:
            export_folder = dirname(self.src_zipfile)
        return self.__gen_dir(export_folder)

    @property
    def supported_format(self) -> dict:
        """Query the supported conversion format.

        Returns
        -------
        dict
            Formats that support transformations.
        """
        return self.__SUPPORTED_FORMAT_INFO

    def head(self, count=5):
        """Check out the first 5

        Parameters
        ----------
        count: int
            Displays the first n results in the list. The default number is 5.

        Returns
        -------
        list
            A list of results.
        """
        return self.annotation[:count]

    def tail(self, count=5):
        """Check out the last 5

        Parameters
        ----------
        count: int
            Displays the last n results in the list. The default number is 5.

        Returns
        -------
        list
            A list of results.
        """
        return self.annotation[:count]

    def to_dict(self):
        """Turn this `Annotation` object into a `dict`.

        Returns
        -------
        Dict
            A standard `dict` of annotations.

        """
        return self.annotation

    def convert(self, format: str, export_folder: str = None):
        """Convert the saved result to a target format.
        Find more info, see `description <https://docs.xtreme1.io/xtreme1-docs>`_.

        Parameters
        ----------
        format: str
            Target format,Optional (JSON, COCO, VOC, LABEL_ME, KITTI).
            Case-insensitive

        export_folder: str
            The path to save the conversion result.

        Returns
        -------
        None

        """
        format = format.upper()
        if format in ['JSON']:
            if format == 'JSON':
                self.to_json(export_folder)
        elif format in ['COCO', 'VOC', 'LABELME']:
            if format == 'COCO':
                self.to_coco(export_folder)
            elif format == 'VOC':
                self.to_voc(export_folder)
            else:
                self.to_labelme(export_folder)
        elif format in ['KITTI']:
            if format == 'KITTI':
                self.to_kitti(export_folder)
        elif format == 'KITTI_LIKE':
            self.to_kitti_like(export_folder)
        else:
            raise ConverterException(message=f'Do not support this format <{format}>')

    def to_json(self, export_folder: str = None):
        """Convert the saved result to a json file in the xtreme1 standard format.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """

        _to_json(self.annotation, self.__ensure_dir(export_folder))

    def to_coco(self, export_folder: str = None):
        """
        Export data in coco format, and the resulting format varies somewhat depending on the tool type
        (RECTANGLE,POLYGON,POLYLINE,KEYPOINTS).
        Note that exports in this format only support image-type annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """

        _to_coco(self.annotation, dataset_name=self.dataset_name, export_folder=self.__ensure_dir(export_folder))

    def to_voc(self, export_folder: str = None):
        """
        Export data in voc format.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """

        _to_voc(self.annotation, self.__ensure_dir(export_folder))

    def to_labelme(self, export_folder: str = None):
        """Export data in label_me format.
        Note that exports in this format only support image-type annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result

        Returns
        -------
        None

        """

        _to_labelme(self.annotation, self.__ensure_dir(export_folder))

    def to_kitti(self, export_folder: str = None):
        """Export data in kitti format.
        Note that exports in this format only support lidar-fusion annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result

        Returns
        -------
        None

        """

        _to_kitti(self.annotation, self.__ensure_dir(export_folder))

    def to_kitti_like(self, export_folder: str = None):
        """Export data in kitti-like format.
        Note that exports in this format only support lidar-fusion annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result

        Returns
        -------
        None

        """

        _to_kitti_like(self.annotation, self.__ensure_dir(export_folder))
