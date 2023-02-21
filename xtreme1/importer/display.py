from ..exceptions import *
from ..importer._popular import _coco_to_x1, _voc_to_x1, _yolo_to_x1, _labelme_to_x1, _kitti_to_x1

__supported_source_type__ = {
    "COCO": {
        "description": 'Coco dataset'
    },
    "VOC": {
        "description": 'Voc dataset'
    },
    "YOLO": {
        "description": 'Yolo dataset'
    },
    "LABELME": {
        "description": 'LabelMe dataset'
    },
    "KITTI": {
        "description": 'Kitti dataset'
    },

}


class Display:
    __SUPPORTED_SOURCE_TYPE__ = __supported_source_type__

    def __init__(self,
                 source: str
                 ):
        self.source = source

    @property
    def supported_source(self):
        """Query the supported conversion format.

        Returns
        -------
        dict
            Formats that support transformations
        """

        return self.__SUPPORTED_SOURCE_TYPE__

    def displayer(self,
                  source_type: str
                  ):
        source_type = source_type.upper()
        if source_type == 'COCO':
            self.parse_coco()
        elif source_type == 'VOC':
            self.parse_voc()
        elif source_type == 'YOLO':
            self.parse_yolo()
        elif source_type == 'LABELME':
            self.parse_labelme()
        elif source_type == 'KITTI':
            self.parse_kitti()

    def parse_coco(self):

        _coco_to_x1(source=self.source)

    def parse_voc(self):

        _voc_to_x1(source=self.source)

    def parse_yolo(self):

        _yolo_to_x1(source=self.source)

    def parse_labelme(self):

        _labelme_to_x1(source=self.source)

    def parse_kitti(self):

        _kitti_to_x1(source=self.source)
