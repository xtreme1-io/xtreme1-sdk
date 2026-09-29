"""Checks the COCO polygon shape, in both directions.

Run with `python test_coco_polygon.py`; it needs nothing but the package.
"""
from xtreme1.importer._parse_data import _polygon_rings

SQUARE = [10, 10, 110, 10, 110, 60, 10, 60]
POINTS = [{"x": 10, "y": 10}, {"x": 110, "y": 10}, {"x": 110, "y": 60}, {"x": 10, "y": 60}]


def test_reads_the_shape_the_spec_uses():
    # COCO stores a polygon as a list of polygons.
    assert _polygon_rings([SQUARE]) == [POINTS]


def test_still_reads_the_flat_array_older_exports_wrote():
    assert _polygon_rings(SQUARE) == [POINTS]


def test_every_part_of_a_split_annotation_is_kept():
    # An occluder splits one object into disjoint polygons; none may be dropped.
    other = [0, 0, 50, 0, 50, 50]
    rings = _polygon_rings([SQUARE, other])
    assert len(rings) == 2
    assert rings[0] == POINTS
    assert rings[1] == [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 50, "y": 50}]


def test_rle_is_not_a_polygon():
    # iscrowd=1 stores {"counts": ..., "size": ...}; the caller falls back to bbox.
    assert _polygon_rings({"counts": "abc", "size": [200, 200]}) == []


def test_nothing_to_read():
    assert _polygon_rings(None) == []
    assert _polygon_rings([]) == []
    assert _polygon_rings([[10, 10, 20, 20]]) == []  # two points is not an area


def test_exported_polygon_is_nested_and_has_a_box():
    from xtreme1.exporter._popular import _to_coco
    import json, tempfile, os

    annotation = [{
        "data": {"name": "a", "images": [{"width": 200, "height": 200, "url": "http://x/a.jpg"}]},
        "result": {"objects": [{
            "type": "POLYGON",
            "className": "cat",
            "classValues": [],
            "contour": {"points": [{"x": p[0], "y": p[1]} for p in
                                   zip(SQUARE[::2], SQUARE[1::2])]},
        }]},
    }]
    with tempfile.TemporaryDirectory() as out:
        _to_coco(annotation, "ds", out)
        path = os.path.join(out, os.listdir(out)[0])
        coco = json.load(open(path, encoding="utf-8"))

    (anno,) = coco["annotations"]
    assert anno["segmentation"] == [SQUARE], anno["segmentation"]
    assert anno["bbox"] == [10, 10, 100, 50], anno["bbox"]


def test_a_polygon_with_no_points_does_not_kill_the_export():
    # min() on an empty sequence raises, and _to_coco's caller turns any
    # exception into a failure of the whole dataset export.
    from xtreme1.exporter._popular import _to_coco
    import tempfile

    annotation = [{
        "data": {"name": "a", "images": [{"width": 9, "height": 9, "url": "http://x/a.jpg"}]},
        "result": {"objects": [{"type": "POLYGON", "className": "cat",
                                "classValues": [], "contour": {"points": []}}]},
    }]
    with tempfile.TemporaryDirectory() as out:
        _to_coco(annotation, "ds", out)   # must not raise


def test_polyline_carries_its_box():
    from xtreme1.exporter._popular import _to_coco
    import json, tempfile, os

    annotation = [{
        "data": {"name": "a", "images": [{"width": 200, "height": 200, "url": "http://x/a.jpg"}]},
        "result": {"objects": [{"type": "POLYLINE", "className": "edge", "classValues": [],
                                "contour": {"points": [{"x": 5, "y": 5}, {"x": 60, "y": 40},
                                                       {"x": 120, "y": 15}]}}]},
    }]
    with tempfile.TemporaryDirectory() as out:
        _to_coco(annotation, "ds", out)
        coco = json.load(open(os.path.join(out, os.listdir(out)[0]), encoding="utf-8"))
    (anno,) = coco["annotations"]
    assert anno["bbox"] == [5, 5, 115, 35], anno["bbox"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  " + name)
    print("all good")
