import zipfile
import json
import os

from os.path import *
from .annotation import __supported_format__, Annotation
from ..exceptions import *


class Result:
    _SUPPORTED_FORMAT_INFO = __supported_format__

    def __init__(self,
                 src_zipfile: str,
                 export_folder: str = None,
                 dropna: bool = False
                 ):
        if zipfile.is_zipfile(src_zipfile):
            self.src_zipfile = src_zipfile
        else:
            raise SDKException(code='SourceError', message=f'{src_zipfile} is not zip')
        zip_name = basename(src_zipfile)
        self.dataset_name = '-'.join(splitext(zip_name)[0].split('-')[:-1])
        if export_folder:
            self.export_folder = export_folder
        else:
            self.export_folder = dirname(self.src_zipfile)
        if not exists(self.export_folder):
            os.mkdir(self.export_folder)
        self.dropna = dropna
        self.annotation = Annotation(annotation=self.__reconstitution(), dataset_name=self.dataset_name)

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
            if fl.split('/')[1] == 'result':
                results.append(fl)
            else:
                datas.append(fl)
        id_result = {}
        annotation = []
        for result in results:
            result_content = json.loads(zip_file.read(result))
            id_result[result_content['dataId']] = result_content
        for data in datas:
            data_content = json.loads(zip_file.read(data))
            data_result = id_result.get(data_content['id'], {})
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

    def __ensure_dir(self, input_dir):
        if input_dir:
            export_folder = input_dir
        else:
            export_folder = self.export_folder
        return export_folder

    def supported_format(self) -> dict:
        """Query the supported conversion format.

        Returns
        -------
        dict
            Formats that support transformations.
        """
        return self._SUPPORTED_FORMAT_INFO

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
        self.annotation.head(count)

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
        self.annotation.tail(count)

    def to_dict(self):
        """Turn this `Annotation` object into a `dict`.

        Returns
        -------
        Dict
            A standard `dict` of annotations.

        """
        self.annotation.to_dict()

    def convert(self, format: str, export_folder: str = None):
        """Convert the saved result to a target format.
        Find more info, see `description <https://docs.xtreme1.io/xtreme1-docs>`_.

        Parameters
        ----------
        format: str
            Target format,Optional (JSON, COCO, VOC, LABEL_ME). Case-insensitive.

        export_folder: str
            The path to save the conversion result.

        Returns
        -------
        None

        """

        self.annotation.convert(format=format, export_folder=self.__ensure_dir(export_folder))

    def to_json(self, export_folder: str = None):
        """Convert the saved result to a json file in the xtreme1 standard format.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """

        self.annotation.to_json(export_folder=self.__ensure_dir(export_folder))

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

        self.annotation.to_coco(export_folder=self.__ensure_dir(export_folder))

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

        self.annotation.to_voc(export_folder=self.__ensure_dir(export_folder))

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

        self.annotation.to_labelme(export_folder=self.__ensure_dir(export_folder))
