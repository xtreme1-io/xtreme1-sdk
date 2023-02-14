import json
from copy import deepcopy
from typing import List, Dict, Optional, Union

from ..exceptions import NameDuplicatedException, ParamException

INDENT = 4


def _check_dup(
        nodes,
        new_name
):
    names = [x.name for x in nodes]
    if new_name in names:
        raise NameDuplicatedException(message='This label already exists!')


class Node:
    __slots__ = ['name', '_parent', '_nodes']

    total_attrs = []
    total_keys = []

    def __init__(
            self,
            name,
            nodes: Optional[List] = None
    ):
        self.name = name
        if not nodes:
            nodes = []
        self._nodes = nodes

    def __repr__(
            self
    ):
        return f'<{self.__class__.__name__}> {self.name}'

    def to_dict(
            self
    ) -> Dict:
        """
        Turn this `Node` object into `dict` form.

        Returns
        -------
        Dict
            A standard `dict` of ontology.
        """
        result = {}
        for i in range(len(self.total_attrs)):
            attr = self.total_attrs[i]
            k = self.total_keys[i]
            value = getattr(self, attr, None)
            if value is None:
                continue
            if attr == '_nodes':
                if (not value) and isinstance(self, AttrNode):
                    raise ParamException(message=f"Options of attribute '{self.name}' can not be null!")
                result[k] = []
                for node in value:
                    result[k].append(node.to_dict())
            else:
                result[k] = value

        return result

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        return {}, []

    @classmethod
    def to_node(
            cls,
            org_dict: Dict
    ):
        """
        Turn a `dict` into a `Node` object.

        Parameters
        ----------
        org_dict: Dict
            The `dict` of an ontology class/classification or attribute/option.

        Returns
        -------
        Node
            A `Node` object.
        """
        cur_args, cur_child_nodes = cls._parse_dict(org_dict)
        new_node = cls(
            **cur_args
        )

        for child in cur_child_nodes:
            new_child_node = NODE_MAP[cls].to_node(child)
            new_node._nodes.append(new_child_node)

        return new_node

    def copy(
            self
    ):
        return deepcopy(self)


class AttrNode(Node):
    __slots__ = ['name', '_nodes', 'type', 'required']

    total_attrs = ['name', 'type', 'required', '_nodes']
    total_keys = ['name', 'type', 'required', 'options']

    def __init__(
            self,
            name,
            options: Optional[List[str]] = None,
            input_type: str = 'RADIO',
            required: bool = False
    ):
        super().__init__(
            name=name
        )
        self.type = input_type
        self.required = required
        if not options:
            options = []
        for opt in options:
            self.add_option(opt)

    def __str__(
            self
    ):
        self_intro = {
            'name': self.name,
            'options': [n.name for n in self._nodes],
            'type': self.type,
            'required': self.required
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    @property
    def options(
            self
    ):
        return self._nodes

    def add_option(
            self,
            name: str
    ):
        """
        Add an `OptionNode` object to the options of an `AttrNode` object.

        Parameters
        ----------
        name: str
            The name of new option.

        Returns
        -------
        OptionNode
            An `OptionNode` of this `AttrNode`.
            Notice that it's already in its parent node.
        """
        _check_dup(
            nodes=self._nodes,
            new_name=name
        )

        new_opt = OptionNode(
            name=name
        )
        self._nodes.append(new_opt)

        return new_opt

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        kwargs = {
            'name': node_dict['name'],
            'input_type': node_dict['type'],
            'required': node_dict['required'],
        }

        child_nodes = node_dict['options']

        return kwargs, child_nodes


class OptionNode(Node):
    __slots__ = ['name', '_nodes']

    total_attrs = ['name', '_nodes']
    total_keys = ['name', 'attributes']

    def __init__(
            self,
            name
    ):
        super().__init__(
            name=name
        )
        self._nodes = []

    def __str__(
            self
    ):
        self_intro = {
            'name': self.name,
            'attributes': [n.name for n in self._nodes],
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    @property
    def attributes(
            self
    ):
        return self._nodes

    def add_attribute(
            self,
            name,
            input_type: str = 'RADIO',
            required: bool = False,
            options: Union[str, List[str]] = None
    ):
        """
        Add an `AttrNode` object to the attributes of an `OptionNode` object.

        Parameters
        ----------
        name: Union[str, List[str]]
            The name(s) of new option(s).
        input_type: str, default 'RADIO'
            The input type of this attribute.
            Options: ['RADIO', 'MULTI_SELECTION', 'DROPDOWN', 'TEXT']
        required: bool, default 'False'
            Whether this attribute is mandatory or optional.
        options: Union[str, List[str]], default 'None'
            The options of this attribute.

        Returns
        -------
        List
            The new `AttrNode`.
            Notice that it's already in its parent node.
        """
        _check_dup(
            nodes=self._nodes,
            new_name=name
        )

        new_attr = AttrNode(
            name=name,
            input_type=input_type,
            required=required,
            options=options
        )
        self._nodes.append(new_attr)

        return new_attr

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        kwargs = {
            'name': node_dict['name']
        }

        child_nodes = node_dict['attributes']

        return kwargs, child_nodes


class RootNode(Node):
    __slots__ = ['__id', 'name', '_nodes', 'node_type']

    def __init__(
            self,
            name,
            attrs,
            node_type: str = 'class',
            id_: Optional[int] = None
    ):
        super().__init__(
            name=name,
            nodes=attrs
        )
        node_type = node_type.lower()
        self.node_type = node_type
        self.__id = id_

    @property
    def id(self):
        return self.__id

    @property
    def attributes(
            self
    ):
        return self._nodes

    def add_attribute(
            self,
            name,
            input_type: str = 'RADIO',
            required: bool = False,
            options: Union[str, List[str]] = None
    ):
        """
        Add an `AttrNode` object to the attributes of an `RootNode` object.

        Parameters
        ----------
        name: Union[str, List[str]]
            The name(s) of new option(s).
        input_type: str, default 'RADIO'
            The input type of this attribute.
            Options: ['RADIO', 'MULTI_SELECTION', 'DROPDOWN', 'TEXT']
        required: bool, default 'False'
            Whether this attribute is mandatory or optional.
        options: Union[str, List[str]], default 'None'
            The options of this attribute.

        Returns
        -------
        List
            The new `AttrNode`.
            Notice that it's already in its parent node.
        """
        _check_dup(
            nodes=self._nodes,
            new_name=name
        )

        new_attr = AttrNode(
            name=name,
            input_type=input_type,
            required=required,
            options=options
        )
        self._nodes.append(new_attr)

        return new_attr

    def copy(
            self
    ):
        """
        Copy this `RootNode` with its `id` put to 'None'.

        Returns
        -------
        RootNode
            A copy of this `RootNode`.
        """
        new_root = deepcopy(self)
        new_root.__id = None

        return new_root


class ImageRootNode(RootNode):
    __slots__ = ['__id', 'name', 'color', 'tool_type', 'tool_type_options',
                 '_nodes', 'node_type']

    total_attrs = ['name', 'tool_type', 'tool_type_options', '_nodes', 'color']
    total_keys = ['name', 'toolType', 'toolTypeOptions', 'attributes', 'color']

    def __init__(
            self,
            name,
            tool_type: str = 'BOUNDING_BOX',
            attrs: Optional[List] = None,
            color: str = '#7dfaf2',
            id_: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            attrs=attrs,
            node_type='class',
            id_=id_
        )
        self.tool_type = tool_type.upper()
        self.tool_type_options = {}
        self.color = color

    def __str__(
            self
    ):
        self_intro = {
            'name': self.name,
            'color': self.color,
            'toolType': self.tool_type,
            'toolTypeOptions': self.tool_type_options,
            'attributes': [f"<{n.__class__.__name__}> {n.name}" for n in self._nodes],
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    def __setattr__(
            self,
            key,
            value
    ):
        if key == 'tool_type':
            value = value.upper()

        super().__setattr__(key, value)

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        kwargs = {
            'name': node_dict['name'],
            'tool_type': node_dict['toolType'],
            'color': node_dict['color'],
            'id_': node_dict['id']
        }

        child_nodes = node_dict['attributes']

        return kwargs, child_nodes


class LidarBasicRootNode(RootNode):
    __slots__ = ['__id', 'name', 'color', 'tool_type', 'tool_type_options',
                 '_nodes', 'node_type']

    total_attrs = ['name', 'tool_type', 'tool_type_options', '_nodes', 'color']
    total_keys = ['name', 'toolType', 'toolTypeOptions', 'attributes', 'color']

    def __init__(
            self,
            name,
            tool_type: str = 'CUBOID',
            tool_type_options: Optional[Dict] = None,
            attrs: Optional[List] = None,
            color: str = '#7dfaf2',
            id_: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            attrs=attrs,
            node_type='class',
            id_=id_
        )
        self.tool_type = tool_type.upper()
        if tool_type_options is None:
            tool_type_options = {}
            if self.tool_type in ['CUBOID']:
                tool_type_options = {
                    "width": [],
                    "height": [],
                    "length": [],
                    "points": [],
                    "isStandard": False,
                    "isConstraints": False
                }
        self.tool_type_options = tool_type_options
        self.color = color

    def __str__(
            self
    ):
        self_intro = {
            'name': self.name,
            'color': self.color,
            'toolType': self.tool_type,
            'toolTypeOptions': self.tool_type_options,
            'attributes': [f"<{n.__class__.__name__}> {n.name}" for n in self._nodes],
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    def __setattr__(
            self,
            key,
            value
    ):
        if key == 'tool_type':
            value = value.upper()

        super().__setattr__(key, value)

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        kwargs = {
            'name': node_dict['name'],
            'tool_type': node_dict['toolType'],
            'tool_type_options': node_dict['toolTypeOptions'],
            'color': node_dict['color'],
            'id_': node_dict['id']
        }

        child_nodes = node_dict['attributes']

        return kwargs, child_nodes


class LidarFusionRootNode(RootNode):
    __slots__ = ['__id', 'name', 'color', 'tool_type', 'tool_type_options',
                 '_nodes', 'node_type']

    total_attrs = ['name', 'tool_type', 'tool_type_options', '_nodes', 'color']
    total_keys = ['name', 'toolType', 'toolTypeOptions', 'attributes', 'color']

    def __init__(
            self,
            name,
            tool_type: str = 'CUBOID',
            tool_type_options: Optional[Dict] = None,
            attrs: Optional[List] = None,
            color: str = '#7dfaf2',
            id_: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            attrs=attrs,
            node_type='class',
            id_=id_
        )
        self.tool_type = tool_type.upper()
        if tool_type_options is None:
            tool_type_options = {}
            if self.tool_type in ['CUBOID']:
                tool_type_options = {
                    "width": [],
                    "height": [],
                    "length": [],
                    "points": [],
                    "isStandard": False,
                    "isConstraints": False
                }
        self.tool_type_options = tool_type_options
        self.color = color

    def __str__(
            self
    ):
        self_intro = {
            'name': self.name,
            'color': self.color,
            'toolType': self.tool_type,
            'toolTypeOptions': self.tool_type_options,
            'attributes': [f"<{n.__class__.__name__}> {n.name}" for n in self._nodes],
        }
        self_intro = json.dumps(self_intro, indent=' ' * INDENT)

        return f"<{self.__class__.__name__}>\n{self_intro}"

    def __setattr__(
            self,
            key,
            value
    ):
        if key == 'tool_type':
            value = value.upper()

        super().__setattr__(key, value)

    @staticmethod
    def _parse_dict(
            node_dict
    ):
        kwargs = {
            'name': node_dict['name'],
            'tool_type': node_dict['toolType'],
            'tool_type_options': node_dict['toolTypeOptions'],
            'color': node_dict['color'],
            'id_': node_dict['id']
        }

        child_nodes = node_dict['attributes']

        return kwargs, child_nodes


NODE_MAP = {
    Node: None,
    ImageRootNode: AttrNode,
    LidarBasicRootNode: AttrNode,
    LidarFusionRootNode: AttrNode,
    AttrNode: OptionNode,
    OptionNode: AttrNode
}
