import json
import warnings
from io import BytesIO
from typing import List, Dict, Optional, Union
from copy import deepcopy

from .node import _check_dup, RootNode, ImageRootNode, LidarBasicRootNode, LidarFusionRootNode, INDENT
from ..exceptions import NodeIdException, ParamException


class Ontology:
    __slots__ = ['_client', '_des_id', '_des_type', '_dataset_type', 'classes', 'classifications']

    def __init__(
            self,
            client,
            des_type: str,
            des_id: int,
            dataset_type: str,
            classes: Optional[List] = None,
            classifications: Optional[List] = None,
    ):
        self._client = client
        self._des_id = des_id
        self._des_type = des_type
        self._dataset_type = dataset_type.upper()
        self.classes = []
        self.classifications = []
        if classes is None:
            classes = []
        if classifications is None:
            classifications = []
        for c in classes:
            if type(c) == dict:
                new_class = DATASET_DICT[self._dataset_type].to_node(
                    org_dict=c,
                )
                self.classes.append(new_class)
            elif isinstance(c, RootNode):
                self.classes.append(c)
        # for cf in classifications:
        #     new_classification = DATASET_DICT[self.dataset_type].to_node(
        #                 org_dict=cf,
        #     )
        #     self.classifications.append(new_classification)

    def __repr__(
            self
    ):
        return f'<{self.__class__.__name__}> The ontology of {self._des_type} {self._des_id}'

    def __str__(
            self
    ):
        self_intro = {
            'classes': [f'<{n.__class__.__name__}> {n.name}' for n in self.classes],
            'classifications': [f'<{n.__class__.__name__}> {n.name}' for n in self.classifications],
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    def to_dict(
            self
    ) -> Dict:
        """
        Turn this `Ontology` object into a `dict`.

        Returns
        -------
        Dict
            A standard `dict` of ontology.
        """
        result = {
            'classes': [c.to_dict() for c in self.classes],
            'classifications': [cf.to_dict() for cf in self.classifications]
        }

        return result

    def add_class(
            self,
            name,
            **kwargs
    ):
        """
        Add an `RootNode` object to the classes of an `Ontology` object.

        Parameters
        ----------
        name: str
            The name of a new class.
        kwargs:
            The args needed to create a `RootNode`. For example:
            ImageRootNode needs `name`, `tool_type` and `color`
            If you forget to pass a parameter such as `color`,
            it's also an option to edit it after the `RootNode` is created.

        Returns
        -------
        RootNode
            The new `RootNode`.
            Notice that it's already in its parent node.
        """
        _check_dup(
            nodes=self.classes,
            new_name=name
        )

        new_class = DATASET_DICT[self._dataset_type](
            name=name,
            **kwargs
        )

        self.classes.append(new_class)

        return new_class

    def get(
            self,
            node_id: int,
            node_type: str = 'class'
    ) -> Union[RootNode, None]:
        if node_type == 'class':
            for c in self.classes:
                if c.id == node_id:
                    return c
        else:
            for cf in self.classifications:
                if cf.id == node_id:
                    return cf

    def copy(
            self
    ):
        """
        Generate a copy of current `Ontology` object, which can be used to import to another ontology.

        Returns
        -------
        Ontology
            A copy of current `Ontology` object.
        """
        new_onto = SampleOntology(
            des_type=self._des_type,
            des_id=self._des_id,
            classes=[c.copy() for c in self.classes],
            classifications=[cf.copy() for cf in self.classifications]
        )

        return new_onto

    def delete_online_ontology(
            self,
            is_sure: bool = False
    ) -> bool:
        """
        Delete the ontology in your online 'ontology center'.
        Notice that an ontology attached to a dataset can not be deleted.

        Parameters
        ----------
        is_sure: bool, default False
            Sure or not sure to delete this ontology.

        Returns
        -------
        bool
            True: delete complete.
            False: user is not sure to delete the ontology or the ontology is already deleted.
        """
        return self._client.delete_ontology(
            des_id=self._des_id,
            is_sure=is_sure
        )

    def delete_online_rootnode(
            self,
            node_id: int,
            node_type: str = 'class',
            is_sure: bool = False
    ):
        """
        Delete a class/classification in your online ontology.

        Parameters
        ----------
        node_id: int
            `RootNode.id`.
        node_type: str, default `class`
            `class` or `classification`.
        is_sure: bool, default False
            Sure or not sure to delete this dataset.

        Returns
        -------
        bool
            True: delete complete.
            False: user is not sure to delete the `RootNode` or the `RootNode` is already deleted.
        """
        if node_type not in ['class', 'classification']:
            raise ParamException(message="Node type can only be 'class' or 'classification'")

        if is_sure:
            node = self.get(
                node_id=node_id,
                node_type=node_type
            )
            if not node:
                raise NodeIdException(message=f"Can't find this node: id-{node_id}!")

            if node_type == 'class':
                part1 = 'datasetClass' if 'dataset' in self._des_type else 'class'
                endpoint = f'{part1}/delete/{node_id}'
                resp = self._client.api.post_request(
                    endpoint=endpoint
                )
                self.classes.remove(node)
                return resp

            else:
                part1 = 'datasetClassification' if 'dataset' in self._des_type else 'classification'
                endpoint = f'{part1}/delete/{node_id}'
                resp = self._client.api.post_request(
                    endpoint=endpoint
                )
                self.classifications.remove(node)
                return resp

        return False

    def update_online_rootnode(
            self,
            node_id: int,
            node_type: str = 'class'
    ) -> True:
        """
        Overwrite an online class/classification.

        Parameters
        ----------
        node_id: int
            `RootNode.id`.
        node_type: str, default `class`
            `class` or `classification`.

        Returns
        -------
        True
            True: update complete.
        """
        node_type = 'class' if node_type == 'class' else 'classification'
        node = self.get(
            node_id=node_id,
            node_type=node_type
        )
        if not node:
            raise NodeIdException(message=f"Can't find this node: id-{node_id}!")

        onto_dict = node.to_dict()

        if 'ontology' in self._des_type:
            endpoint = f'{node_type}/update/{node_id}'
            onto_dict['ontologyId'] = self._des_id
        else:
            endpoint = f'dataset{node_type.capitalize()}/update/{node_id}'
            onto_dict['datasetId'] = self._des_id

        self._client.api.post_request(
            endpoint=endpoint,
            payload=onto_dict
        )

        return True

    def _import_ontology(
            self
    ):
        endpoint = 'ontology/importByJson'

        data = {
            'desType': self._des_type.upper(),
            'desId': self._des_id
        }

        file = BytesIO(json.dumps(self.to_dict()).encode())
        files = {
            'file': ('ontology.json', file)
        }

        return self._client.api.post_request(
            endpoint=endpoint,
            data=data,
            files=files
        )

    def _split_dup_nodes(
            self,
    ):
        existing_onto = self._client.query_ontology(
            des_id=self._des_id,
            des_type=self._des_type
        )

        existing_class_ids = [x.id for x in existing_onto.classes]
        existing_classification_ids = [x.id for x in existing_onto.classifications]

        dup_classes = []
        cur_classes = deepcopy(self.classes)
        for i in range(-len(cur_classes), 0):
            if cur_classes[i].id in existing_class_ids:
                dup_classes.append(cur_classes.pop(i))

        dup_classifications = []
        cur_classifications = deepcopy(self.classifications)
        for i in range(-len(cur_classifications), 0):
            if cur_classifications[i].id in existing_classification_ids:
                dup_classifications.append(cur_classifications.pop(i))

        return cur_classes, cur_classifications, dup_classes, dup_classifications

    def _compare_dup_nodes(
            self,
    ):
        existing_onto = self._client.query_ontology(
            des_id=self._des_id,
            des_type=self._des_type
        )

        existing_classes = {x.name: getattr(x, 'tool_type', None) for x in existing_onto.classes}
        existing_classification_names = [x.name for x in existing_onto.classifications]

        dup_classes = []
        cur_classes = deepcopy(self.classes)
        for i in range(-len(cur_classes), 0):
            if cur_classes[i].name in existing_classes:
                if getattr(cur_classes[i], 'tool_type', None) == existing_classes[cur_classes[i].name]:
                    dup_classes.append(cur_classes.pop(i))

        dup_classifications = []
        cur_classifications = deepcopy(self.classifications)
        for i in range(-len(cur_classifications), 0):
            if cur_classifications[i].id in existing_classification_names:
                dup_classifications.append(cur_classifications.pop(i))

        return cur_classes, cur_classifications, dup_classes, dup_classifications

    def import_ontology(
            self,
            ontology=None,
            replace=False
    ) -> Dict:
        """
        Import this `Ontology` object to your online dataset or ontology center.

        Parameters
        ----------
        ontology: SampleOntology
            A `SampleOntology` object generated by `copy()` method.
        replace: bool, default False
            Whether overwrite the online class/classification if `id` is duplicate.
        Returns
        -------
        Dict
            The information about which class/classification is appended into current ontology and which is updated.
        """
        if ontology:
            if replace:
                warnings.warn(message="The 'replace' parameter only works when the ontology is importing itself.")
                replace = False
            ontology._des_id = self._des_id
            ontology._des_type = self._des_type
            ontology._dataset_type = self._dataset_type
            ontology._client = self._client
            cur_onto = ontology
            no_dup_classes, no_dup_classifications, dup_classes, dup_classifications = cur_onto._compare_dup_nodes()
        else:
            cur_onto = self
            no_dup_classes, no_dup_classifications, dup_classes, dup_classifications = cur_onto._split_dup_nodes()

        new_onto = deepcopy(cur_onto)
        new_onto.classes = no_dup_classes
        new_onto.classifications = no_dup_classifications
        new_onto._import_ontology()

        if replace:
            for c in dup_classes:
                cur_onto.update_online_rootnode(
                    node_id=c.id,
                    node_type='class'
                )
            for cf in dup_classifications:
                cur_onto.update_online_rootnode(
                    node_id=cf.id,
                    node_type='classification'
                )

        message = {
            'update_classes': [{'id': x.id, 'name': x.name} for x in dup_classes],
            'update_classifications': [{'id': x.id, 'name': x.name} for x in dup_classifications],
            'append_classes': [{'id': x.id, 'name': x.name} for x in no_dup_classes],
            'append_classifications': [{'id': x.id, 'name': x.name} for x in no_dup_classifications],
        }

        return message


class SampleOntology(Ontology):
    def __init__(
            self,
            des_type,
            des_id,
            classes: Optional[List] = None,
            classifications: Optional[List] = None,
    ):
        super().__init__(
            client=None,
            des_type=des_type,
            des_id=des_id,
            dataset_type='',
            classes=classes,
            classifications=classifications
        )

    def __repr__(
            self
    ):
        return f'<{self.__class__.__name__}> The ontology copy of {self._des_type} {self._des_id}'


DATASET_DICT = {
    'IMAGE': ImageRootNode,
    'LIDAR_BASIC': LidarBasicRootNode,
    'LIDAR_FUSION': LidarFusionRootNode
}
