from ..exceptions import ParserException
from ._parse_data import parse_coco, parse_xtreme1, parse_kitti

__supported_format__ = {
    "COCO": {
        "description": 'An annotation format defined by xtreme1 similar to the coco format',
        "tags": 'Rectangles, polygons, polyline segments in image tasks.'
    },
    "xtreme1": {
        "description": 'Standard json format exported from xtreme1',
        "tags": ''
    }
}


class Parser:
    __SUPPORTED_FORMAT_INFO = __supported_format__

    def __init__(self, source_path):
        self.source_path = source_path

    @property
    def supported_format(self) -> dict:
        """Query the supported conversion format.

        Returns
        -------
        dict
            Formats that support transformations.
        """
        return self.__SUPPORTED_FORMAT_INFO

    def parser(self, format, output):
        """Parser, which parses the data into a json format that xtreme 1 recognizes.

        Parameters
        ----------
        format: str
            The data format to be parsed.
        output: str
            The path to save the parsed results will be used for uploading.

        Returns
        -------
        error message

        """
        format = format.upper()
        if format == 'COCO':
            return self.from_coco(output)
        elif format == 'XTREME1':
            return self.from_xtreme1(output)
        elif format == 'KITTI':
            return self.from_kitti(output)
        else:
            raise ParserException(message=f'Do not support this format:<{format}> to parse')

    def from_coco(self, output: str):
        """Parse the annotation result data in coco format.

        Parameters
        ----------
        output: str
            The path to save the parsed results will be used for uploading.

        Returns
        -------
        error message

        """
        return parse_coco(src=self.source_path, out=output)

    def from_kitti(self, output: str):
        """Parse the annotation result data in kitti dataset.

        Parameters
        ----------
        output: str
            The path to save the parsed results will be used for uploading.

        Returns
        -------
        error message

        """
        return parse_kitti(kitti_dataset_dir=self.source_path, upload_dir=output)

    def from_xtreme1(self, output):
        """

        Parameters
        ----------
        output

        Returns
        -------

        """
        return parse_xtreme1(src=self.source_path, dst=output)

