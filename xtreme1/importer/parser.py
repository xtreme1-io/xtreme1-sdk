from ..exceptions import ParserException
from ._parse_data import parse_coco, parse_xtreme1

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
        format = format.upper()
        if format == 'COCO':
            self.from_coco(output)
        elif format == 'XTREME1':
            self.from_xtreme1(output)
        else:
            raise ParserException(message=f'Do not support this format:<{format}> to parse')

    def from_coco(self, output):
        parse_coco(src=self.source_path, out=output)

    def from_xtreme1(self, output):
        parse_xtreme1(src=self.source_path, dst=output)

