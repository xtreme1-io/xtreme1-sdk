from enum import Enum
from typing import List, Union, Optional, Dict, FrozenSet
from functools import reduce

from .exceptions import ParamException


class ImageModelClass(Enum):
    tool = frozenset({'KNIFE', 'BACKPACK', 'UMBRELLA', 'HANDBAG', 'TIE', 'SUITCASE',
                      'CLOCK', 'SCISSORS', 'TOOTHBRUSH'})
    dishware = frozenset({'SPOON', 'BOWL', 'BOTTLE', 'CUP', 'WINE_GLASS', 'FORK'})
    sports = frozenset({'FRISBEE', 'SKIS', 'SNOWBOARD', 'SPORTS_BALL', 'BASEBALL_BAT', 'BASEBALL_GLOVE', 'SKATEBOARD',
                        'SURFBOARD', 'TENNIS_RACKET'})
    toy = frozenset({'KITE', 'TEDDY_BEAR'})
    vegetable = frozenset({'BANANA', 'APPLE', 'ORANGE', 'BROCCOLI', 'CARROT'})
    food = frozenset({'SANDWICH', 'HOT_DOG', 'PIZZA', 'DONUT', 'CAKE'})
    traffic = frozenset({'TRAFFIC_LIGHT', 'STOP_SIGN', 'PARKING_METER', 'PERSON', 'BICYCLE', 'CAR', 'MOTORCYCLE',
                         'AIRPLANE', "BUS", "TRAIN", "TRUCK", "BOAT"})
    electronic = frozenset({'LAPTOP', 'KEYBOARD', 'CELL_PHONE', 'TV', 'MICROWAVE', 'OVEN', 'TOASTER',
                            'REFRIGERATOR', 'HAIR_DRIER'})
    furniture = frozenset({'CHAIR', 'BENCH', 'COUCH', 'POTTED_PLANT', 'BED', 'DINING_TABLE', 'TOILET', 'SINK'})
    animal = frozenset({'BIRD', 'CAT', 'DOG', 'HORSE', 'SHEEP', 'COW', 'ELEPHANT', 'MOUSE', 'BEAR', 'ZEBRA',
                        'GIRAFFE'})
    others = frozenset({'FIRE_HYDRANT', 'BOOK', 'VASE', 'REMOTE'})


class PointCloudModelClass(Enum):
    traffic = frozenset(
        {"CAR", "TRUCK", "CONSTRUCTION_VEHICLE", "BUS", "TRAILER", "BARRIER", "MOTORCYCLE", "BICYCLE", "PEDESTRIAN",
         "TRAFFIC_CONE"}
    )


class Model:
    classes = None

    def __init__(
            self,
            client,
    ):
        self._client = client

    @property
    def all_classes(
            self
    ) -> Dict[str, FrozenSet]:
        """
        Return all classes which are supported by a trained model as a dict.

        Returns
        -------
        Dict[str, FrozenSet]
            Various classes.
        """

        return {x.name: x.value for x in self.classes}

    def _predict(
            self,
            endpoint: str,
            min_confidence: Union[int, float] = 0.5,
            max_confidence: Union[int, float] = 1,
            data_id: Optional[Union[str, List[str]]] = None,
            dataset_id: Optional[str] = None,
            **kwargs
    ) -> List[Dict]:
        if data_id:
            if type(data_id) == str:
                data_id = [data_id]
        else:
            if dataset_id:
                data = self._client.query_data_under_dataset(dataset_id)
                data_id = [x['id'] for x in data['datas']]
            else:
                raise ParamException(message='You need to pass either data_id or dataset_id !!!')

        n = len(data_id)

        total = []
        for i in range(n):
            payload = {
                'dataId': data_id[i],
                'minConfidence': min_confidence,
                'maxConfidence': max_confidence,
            }
            payload.update(kwargs)

            total.append(self._client.api.post_request(endpoint, payload=payload))

        return total


class ImageModel(Model):
    classes = ImageModelClass

    def __init__(
            self,
            client
    ):
        super().__init__(client)

    def predict(
            self,
            min_confidence: Union[int, float] = 0.5,
            max_confidence: Union[int, float] = 1,
            classes: Optional[Union[str, List[str]]] = None,
            data_id: Optional[Union[int, List[int]]] = None,
            dataset_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Use a trained model to recognize given objects in an image.

        Parameters
        ----------
        classes: Optional[Union[str, List[str]]]
            Object classes.
            If this parameter is `None`, all the classes will be predicted.
            If you pass a 'str', the model will predict the given object in each data.
            If you pass a list of 'str', the model will predict all the given objects in each data.
        min_confidence: Union[int, float], default 0.5
            Filter out all the results that has a lower confidence than 'min_confidence'.
            Range from [0.5, 1].
        max_confidence: Union[int, float], default 1
            Filter out all the results that has a higher confidence than 'max_confidence'.
            Range from [0.5, 1].
        data_id: Optional[Union[int, List[int]]], default None
            If you pass this parameter, the model will only predict the given data.
        dataset_id: Optional[int], default None
            If you pass this parameter, the model will predict all the data under this dataset.

        Returns
        -------
        List[Dict]
            A list of data dict. Each dict represents a copy of data, containing all the boxes predicted by the model.
            Here's an example of objects::

                [
                    {
                        'points': [{'x': 1166, 'y': 498}, {'x': 1246, 'y': 548}],
                        'objType': 'rectangle',
                        'confidence': 0.64111328125,
                        'modelClass': 'Truck',
                        'modelClassId': 8
                    },
                    {
                        'points': [{'x': 1382, 'y': 528}, {'x': 1472, 'y': 567}],
                        'objType': 'rectangle',
                        'confidence': 0.64794921875,
                        'modelClass': 'Car',
                        'modelClassId': 3
                    }
                ]
        """
        endpoint = 'model/image/recognition'
        if not classes:
            classes = reduce(lambda x, y: x + y, [list(c.value) for c in self.classes])
        if isinstance(data_id, int):
            data_id = [data_id]

        return self._predict(
            endpoint=endpoint,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            data_id=data_id,
            dataset_id=dataset_id,
            classes=classes
        )


class PointCloudModel(Model):
    classes = PointCloudModelClass

    def __init__(
            self,
            client
    ):
        super().__init__(client)

    def predict(
            self,
            classes: Optional[Union[str, List[str]]],
            min_confidence: Union[int, float] = 0.5,
            max_confidence: Union[int, float] = 1,
            data_id: Optional[Union[str, List[str]]] = None,
            dataset_id: Optional[str] = None
    ):
        """
        Use a trained model to recognize given objects in a point cloud.

        Parameters
        ----------
        classes: Optional[Union[str, List[str]]]
            Object classes.
            If this parameter is `None`, all the classes will be predicted.
            If you pass a 'str', the model will predict the given object in each data.
            If you pass a list of 'str', the model will predict all the given objects in each data.
        min_confidence: Union[int, float], default 0.5
            Filter out all the results that has a lower confidence than 'min_confidence'.
            Range from [0.5, 1].
        max_confidence: Union[int, float], default 1
            Filter out all the results that has a higher confidence than 'max_confidence'.
            Range from [0.5, 1].
        data_id: Optional[Union[str, List[str]]], default None
            If you pass this parameter, the model will only predict the given data.
        dataset_id: Optional[str], default None
            If you pass this parameter, the model will predict all the data under this dataset.

        Returns
        -------
        List[Dict]
            A list of data dict. Each dict represents a copy of data, containing all the boxes predicted by the model.
            Here's an example of objects::

                [
                    {
                        'size3D': {
                            'x': 4.305268414854595,
                            'y': 1.616233427608904,
                            'z': 1.519332468509674
                        },
                        'objType': '3d',
                        'center3D': {
                            'x': -13.985993934930775,
                            'y': 9.282877771446682,
                            'z': 0.5724581182003021
                        },
                        'confidence': 0.8834354877471924,
                        'modelClass': 'Car',
                        'rotation3D': {
                            'x': 0,
                            'y': 0,
                            'z': -2.3066487312316895
                        }
                    },
                    ...
                ]
        """
        endpoint = 'model/pointCloud/recognition'
        if not classes:
            classes = reduce(lambda x, y: x + y, [list(c.value) for c in self.classes])

        return self._predict(
            endpoint=endpoint,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            data_id=data_id,
            dataset_id=dataset_id,
            classes=classes
        )
