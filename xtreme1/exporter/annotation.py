import os
from os.path import join, exists
from ..exporter._standard import _to_json
from ..exporter._popular import _to_coco, _to_voc, _to_labelme
from ..exceptions import *

__supported_format__ = {
    "JSON": {
        "description": 'Xtreme1 standard json format.',
        "tags": 'All types of labeling tasks.'
    },
    "CSV": {
        "description": 'Coming soon'
    },
    "XML": {
        "description": 'Coming soon'
    },
    "TXT": {
        "description": 'Coming soon'
    },
    "COCO": {
        "description": 'Popular machine learning format used by the COCO dataset for object detection and image segmentation and polyline tasks with polygons and rectangles.',
        "tags": 'Rectangles, polygons, polyline segments in image tasks.'
    },
    "VOC": {
        "description": 'Popular XML format used for object detection and polygon image segmentation and polyline tasks.',
        "tags": 'Rectangles, polygons, polyline segments in image tasks.'
    },
    "YOLO": {
        "description": 'Coming soon'
    },
    "LABELME": {
        "description": 'Popular XML format used for object detection and polygon image segmentation and polyline tasks.',
        "tags": 'Rectangles, polygons, polyline segments in image tasks.'
    },
    "KITTI": {
        "description": 'Coming soon'
    }
}


class Annotation:
    _SUPPORTED_FORMAT = __supported_format__

    def __init__(
            self,
            client,
            annotation,
            dataset_name,
            version=None,
            dataset_id=None,
            export_time=None
    ):
        self.version = version
        self.dataset_id = dataset_id
        self.dataset_name = dataset_name
        self.export_time = export_time
        self.annotation = annotation
        self._client = client
        self.anno_type = self.__query_dataset_type()

    def __query_dataset_type(self):

        return self._client.query_dataset(self.dataset_id).type

    def __str__(self):
        return f"Annotation(dataset_id={self.dataset_id}, dataset_name={self.dataset_name})"

    def __repr__(self):
        return f"Annotation(dataset_id={self.dataset_id}, dataset_name={self.dataset_name})"

    def __setattr__(self, key, value):
        if key == '_SUPPORTED_FORMAT':
            raise NoPermissionException(message='You are performing an operation that is not allowed')
        else:
            self.__dict__[key] = value

    def __gen_dir(self, input_dir):
        save_folder = join(input_dir, f'x1 dataset {self.dataset_name} annotations')
        if not exists(save_folder):
            os.makedirs(save_folder, exist_ok=True)
        return save_folder


    def supported_format(self) -> dict:
        """Query the supported conversion format.

        Returns
        -------
        dict
            Formats that support transformations.
        """

        return self._SUPPORTED_FORMAT

    def head(self, count: int = 5) -> list:
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

    def tail(self, count=5) -> list:
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
        return self.annotation[-count:]

    def to_dict(self):
        """Turn this `Annotation` object into a `dict`.

        Returns
        -------
        Dict
            A standard `dict` of annotations.

        """
        return self.annotation

    def convert(self, format: str, export_folder: str):
        """Convert the saved result to a target format.
        Find more info, see `description <https://docs.xtreme1.io/xtreme1-docs>`_.

        Parameters
        ----------
        format: str
            Target format,Optional (JSON, COCO, VOC, LABEL_ME).
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
                self.to_json(self.__gen_dir(export_folder))
        elif format in ['COCO', 'VOC', 'LABELME']:
            if self.anno_type == 'IMAGE':
                if format == 'COCO':
                    self.to_coco(self.__gen_dir(export_folder))
                elif format == 'VOC':
                    self.to_voc(self.__gen_dir(export_folder))
                else:
                    self.to_labelme(self.__gen_dir(export_folder))
            else:
                raise ConverterException(message='Annotations do not support this format')
        else:
            raise ConverterException(message=f'Do not support this format <{format}>')

    def to_json(self, export_folder: str):
        """Convert the saved result to a json file in the xtreme1 standard format.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """
        _to_json(annotation=self.annotation,
                 export_folder=self.__gen_dir(export_folder))

    def to_coco(self, export_folder: str):
        """
        Export data in coco format, and the resulting format varies somewhat depending on the tool type
        (RECTANGLE,POLYGON,POLYLINE).
        Note that exports in this format only support image-type annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """
        if self.anno_type == 'IMAGE':
            _to_coco(annotation=self.annotation,
                     dataset_name=self.dataset_name,
                     export_folder=self.__gen_dir(export_folder))
        else:
            raise ConverterException(message='This annotations do not support export to coco format')

    def to_voc(self, export_folder: str):
        """
        Export data in voc format.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """
        if self.anno_type == 'IMAGE':
            _to_voc(annotation=self.annotation,
                    dataset_name=self.dataset_name,
                    export_folder=self.__gen_dir(export_folder))
        else:
            raise ConverterException(message='This annotations do not support export to voc format')

    def to_labelme(self, export_folder: str):
        """Export data in labelme format.
        Note that exports in this format only support image-type annotations.

        Parameters
        ----------
        export_folder: The path to save the conversion result.

        Returns
        -------
        None

        """
        if self.anno_type == 'IMAGE':
            _to_labelme(annotation=self.annotation,
                        export_folder=self.__gen_dir(export_folder))
        else:
            raise ConverterException(message='This annotations do not support export to labelme format')
