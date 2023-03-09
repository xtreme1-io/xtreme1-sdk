import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Iterable, Tuple
from datetime import datetime

import requests
from rich.progress import track

from ._api import Api
from .dataset import Dataset
from .exceptions import SDKException, ParamException, DatasetIdException, DataIdException
from .exporter.annotation import Annotation
from .models import ImageModel, PointCloudModel
from .ontology.ontology import Ontology
from ._others import _to_single, _parse_data_info


class Client:

    def __init__(
            self,
            access_token: str,
            base_url: str
    ):
        self.api = Api(access_token=access_token, base_url=base_url)
        self.image_model = ImageModel(self)
        self.point_cloud_model = PointCloudModel(self)

    def create_dataset(
            self, name: str,
            annotation_type: str,
            description: str = None
    ) -> Dataset:
        """
        Create a dataset with specific name and description.

        Parameters
        ----------
        name: str
            Dataset name.
        annotation_type: str
            An annotation type which can only choose from this list:
            ['LIDAR_FUSION', 'LIDAR_BASIC', 'IMAGE'].
        description: str, default None
            Further description about this dataset.

        Returns
        -------
        Dataset
            An instance of dataset class.
        """
        endpoint = 'dataset/create'
        payload = {
            'name': name,
            'type': annotation_type.upper(),
            'description': description
        }

        resp = self.api.post_request(endpoint, payload=payload)

        return Dataset(resp, self)

    def edit_dataset(
            self,
            dataset_id: Union[int, str],
            new_name: str,
            new_description: Optional[str] = None
    ) -> bool:
        """
        Change the name or description of a dataset.

        Parameters
        ----------
        dataset_id: Union[int, str]
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        new_name: str
            New name of the dataset.
        new_description: Optional[str], default None
            New description of the dataset.

        Returns
        -------
        bool
            True: edit complete.
        """
        endpoint = f'dataset/update/{dataset_id}'
        payload = {
            'name': new_name,
            'description': new_description
        }

        self.api.post_request(endpoint, payload=payload)

        return True

    def delete_dataset(
            self,
            dataset_id: Union[int, str],
            is_sure: bool = False
    ) -> bool:
        """
        Delete a dataset.

        Parameters
        ----------
        dataset_id: Union[int, str]
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        is_sure: bool, default False
            Sure or not sure to delete this dataset.

        Returns
        -------
        bool
            True: delete complete.
            False: user is not sure to delete the dataset or the dataset is already deleted.
        """
        if not is_sure:
            return False

        try:
            endpoint = f'dataset/delete/{dataset_id}'
            self.api.post_request(
                endpoint=endpoint,
                payload=None
            )
        except DatasetIdException:
            return False

        return True

    def _query_dataset_info(
            self,
            dataset_id: Union[int, str]
    ) -> Dict:
        endpoint = f'dataset/info/{dataset_id}'
        resp = self.api.get_request(endpoint=endpoint, params=None)

        return resp

    def _query_the_list_of_datasets(
            self,
            page_no: int,
            page_size: int,
            name: Optional[str] = None,
            create_start_time: Optional[Iterable] = None,
            create_end_time: Optional[Iterable] = None,
            sort_by: Optional[str] = None,
            ascending: Optional[bool] = True,
            dataset_type: Optional[str] = None
    ) -> Dict:
        endpoint = 'dataset/findByPage'

        create_start_time = datetime(*create_start_time) if create_start_time else datetime(1000, 1, 1)
        create_end_time = datetime(*create_end_time) if create_end_time else datetime.today()

        params = {
            'pageNo': page_no,
            'pageSize': page_size,
            'name': name,
            'createStartTime': create_start_time,
            'createEndTime': create_end_time,
            'sortField': sort_by,
            'ascOrDesc': 'ASC' if ascending else 'DESC',
            'type': dataset_type
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    def query_dataset(
            self,
            dataset_id: Union[int, str, None] = None,
            page_no: int = 1,
            page_size: int = 10,
            dataset_name: Optional[str] = None,
            create_start_time: Optional[Iterable] = None,
            create_end_time: Optional[Iterable] = None,
            sort_by: str = 'CREATED_AT',
            ascending: Optional[bool] = True,
            dataset_type: Optional[str] = None
    ) -> Union[Dataset, Tuple[List[Dataset], int]]:
        """
        Query a specific dataset or query several datasets with some filters.

        Parameters
        ----------
        dataset_id: Union[int, str, None], default None
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        page_no: int, default 1
            Page number of the total result.
            This is used when you have lots of datasets and only want to check them part by part.
        page_size: int, default 1
            Number of datasets on one page.
        dataset_name: str
            Name of the dataset you want to query.
            Notice that it's a fuzzy query.
        create_start_time: Iterable, default None
            An iterable object. For example:
            (2023, 1, 1, 12, 30, 30) means querying datasets created after 2023-01-01T12:30:30.
            Hour, minute and second are optional.
        create_end_time: Iterable, default None
            An iterable object. For example:
            (2023, 1, 1, 12, 30, 30) means querying datasets created before 2023-01-01T12:30:30.
            Hour, minute and second are optional.
        sort_by: str, default 'CREATED_AT'
            A sort field that can only choose from this list:
            ['NAME', 'CREATED_AT', 'UPDATED_AT']
        ascending: bool, default True
            Whether the order of datasets is ascending or descending.
        dataset_type: str, default None
            An annotation type that can only choose from this list:
            ['LIDAR_FUSION', 'LIDAR_BASIC', 'IMAGE']

        Returns
        -------
        Union[Dataset, Tuple[List[Dataset], int]]
            A list of `Dataset` objects and the total number of datasets.
        """
        if dataset_id:
            dataset_name = self._query_dataset_info(dataset_id)['name']

        resp = self._query_the_list_of_datasets(
            page_no=page_no,
            page_size=page_size,
            name=dataset_name,
            create_start_time=create_start_time,
            create_end_time=create_end_time,
            sort_by=sort_by,
            ascending=ascending,
            dataset_type=dataset_type
        )

        datasets = [Dataset(d, self) for d in resp['list']]
        total = resp['total']

        return _to_single(datasets, total)

    def _query_data_under_dataset(
            self,
            dataset_id: Union[int, str],
            page_no: int = 1,
            page_size: int = 10,
            name: Optional[str] = None,
            create_start_time: Optional[Iterable] = None,
            create_end_time: Optional[Iterable] = None,
            sort_by: str = 'CREATED_AT',
            ascending: Optional[bool] = True,
            annotation_status: Optional[str] = None
    ) -> Dict:
        endpoint = 'data/findByPage'

        create_start_time = datetime(*create_start_time) if create_start_time else datetime(1000, 1, 1)
        create_end_time = datetime(*create_end_time) if create_end_time else datetime.today()

        params = {
            'datasetId': dataset_id,
            'pageNo': page_no,
            'pageSize': page_size,
            'name': name,
            'createStartTime': create_start_time,
            'createEndTime': create_end_time,
            'sortField': sort_by,
            'ascOrDesc': 'ASC' if ascending else 'DESC',
            'annotationStatus': annotation_status
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    def query_data_under_dataset(
            self,
            dataset_id: Union[int, str],
            page_no: int = 1,
            page_size: int = 10,
            name: Optional[str] = None,
            create_start_time: Optional[Iterable] = None,
            create_end_time: Optional[Iterable] = None,
            sort_by: str = 'CREATED_AT',
            ascending: Optional[bool] = True,
            annotation_status: Optional[str] = None
    ) -> Dict:
        """
        Query data under a specific dataset with some filters.
        Notice that 'data' ≠ 'file'. For example:
        for a 'LIDAR_FUSION' dataset, a copy of data means:
        'a pcd file' + 'a camera config json' + 'several 2D images'.

        Parameters
        ----------
        dataset_id: Union[int, str]
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        page_no: int, default 1
            Page number of the total result.
            This is used when you have lots of data and only want to check them part by part.
        page_size: int, default 10
            Number of data on one page.
        name: str
            Name of the data you want to query.
            Notice that it's a fuzzy query.
        create_start_time: Iterable, default None
            An iterable object. For example:
            (2023, 1, 1, 12, 30, 30) means querying datasets created after 2023-01-01T12:30:30.
            Hour, minute and second are optional.
        create_end_time: Iterable, default None
            An iterable object. For example:
            (2023, 1, 1, 12, 30, 30) means querying datasets created before 2023-01-01T12:30:30.
            Hour, minute and second are optional.
        sort_by: str, default 'CREATED_AT'
            A sort field that can only choose from this list:
            ['NAME', 'CREATED_AT', 'UPDATED_AT']
        ascending: bool, default True
            Whether the order of datasets is ascending or descending.
        annotation_status: Optional[str], default None
            Annotation status of the data that can only choose from this list:
            ['ANNOTATED', 'NOT_ANNOTATED', 'INVALID'].

        Returns
        -------
        Dict
            JSON data containing all the data you're querying and information of all the files within these data.
        """
        resp = self._query_data_under_dataset(
            dataset_id=dataset_id,
            page_no=page_no,
            page_size=page_size,
            name=name,
            create_start_time=create_start_time,
            create_end_time=create_end_time,
            sort_by=sort_by,
            ascending=ascending,
            annotation_status=annotation_status
        )

        rps_dict = {
            "pageSize": resp.get('pageSize'),
            "pageNo": resp.get('pageNo'),
            "total": resp.get('total'),
            "datas": _parse_data_info(resp.get('list'))
        }

        return rps_dict

    def delete_data(
            self,
            dataset_id: Union[int, str],
            data_id: Union[int, List[int]],
            is_sure: bool = False
    ) -> bool:
        """
        Delete one specific data or a list of data from a specific dataset.
        Notice that 'data' ≠ 'file'. For example:
        for a 'LIDAR_FUSION' dataset, a copy of data means:
        'a pcd file' + 'a camera config json' + 'several 2D images'.

        Parameters
        ----------
        dataset_id: Union[int, str]
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        data_id: Union[int, List[int]]
            An id or list of ids of the data you want to delete.
        is_sure: bool, default False
            Sure or not sure to delete this dataset.

        Returns
        -------
        bool
            True: delete complete.
            False: user is not sure to delete the data or the data is already deleted.
        """
        if not is_sure:
            return False

        if type(data_id) == str:
            data_id = int(data_id)
        if not isinstance(data_id, list):
            data_id = [data_id]

        try:
            endpoint = 'data/deleteBatch'

            payload = {
                'datasetId': dataset_id,
                'ids': data_id
            }

            self.api.post_request(endpoint=endpoint, payload=payload)
        except DataIdException:
            return False

        return True

    def query_data(
            self,
            data_id: Union[int, List[int]]
    ) -> List[Dict]:
        """
        Use a specific id or a list of ids to delete data.
        Notice that 'data' ≠ 'file'. For example:
        for a 'LIDAR_FUSION' dataset, a copy of data means:
        'a pcd file' + 'a camera config json' + 'several 2D images'.

        Parameters
        ----------
        data_id: Union[str, List[str]]
            A specific id or a list of ids.

        Returns
        -------
        List[Dict]
            List of JSON data.
        """
        endpoint = 'data/listByIds'

        if type(data_id) == str:
            data_id = int(data_id)
        if not isinstance(data_id, list):
            data_id = [data_id]
        params = {
            'dataIds': data_id
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    def _generate_data_direct_upload_address(
            self,
            data_name: str,
            dataset_id: Union[int, str]
    ) -> Dict:
        endpoint = 'data/generatePresignedUrl'

        params = {
            'fileName': data_name,
            'datasetId': dataset_id
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    def _upload(
            self,
            url: str,
            dataset_id: Union[int, str],
            source: str
    ) -> str:
        endpoint = 'data/upload'

        payload = {
            'fileUrl': url,
            'datasetId': dataset_id,
            'source': source
        }

        resp = self.api.post_request(endpoint=endpoint, payload=payload)

        return resp

    def upload_data(
            self,
            data_path: str,
            dataset_id: Union[int, str],
            is_local: bool = True
    ) -> str:
        """
        Upload data to a specific dataset by using a local path or URL.
        Notice that 'data' ≠ 'file'. For example:
        for a 'LIDAR_FUSION' dataset, a copy of data means:
        'a pcd file' + 'a camera config json' + 'several 2D images'.

        This function always returns a serial number if the parameters are right.
        However, it doesn't mean the upload process is successful.
        It's necessary to check the upload status by using the 'query_upload_status' function.

        Parameters
        ----------
        data_path: str
            A local path or URL.
        dataset_id: Union[int, str]
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
        is_local: bool, default True
            Whether the data is local or not.

        Returns
        -------
        str
            A serial number for querying the upload status.
        """
        if is_local:
            data_name = os.path.split(data_path)[-1]
            url_dict = self._generate_data_direct_upload_address(data_name, dataset_id)
            put_resp = requests.put(url_dict['presignedUrl'], data=open(data_path, 'rb'))

            if put_resp.status_code != 200:
                raise SDKException(code=put_resp.status_code, message=put_resp.text)

            upload_url = url_dict['accessUrl']
            source = 'LOCAL'

        else:
            upload_url = data_path
            source = 'URL'

        resp = self._upload(upload_url, dataset_id, source)

        return resp

    def query_upload_status(
            self,
            serial_numbers: Union[str, List[str]]
    ) -> List[Dict]:
        """
        Query if the upload process is completed.
        Also shows the number of parsed data.

        Parameters
        ----------
        serial_numbers: Union[str, List[str]]
            A specific serial_number or list of serial_numbers.
            Notice that 'serial_number' is the response of 'upload_data' function,
            and it can't be acquired from other functions.

        Returns
        -------
        List[Dict]
            List of upload status.
        """
        endpoint = 'data/findUploadRecordBySerialNumbers'

        params = {
            'serialNumbers': serial_numbers
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    @staticmethod
    def _recursive_search_url(
            data: Union[List, Dict],
            output_folder: str,
            total: List,
            remain_directory_structure: bool = True
    ):
        if total is None:
            total = []
        if type(data) == list:
            for d in data:
                Client._recursive_search_url(d, output_folder, total, remain_directory_structure)

        elif type(data) == dict:
            if 'url' in data:
                total.append((data['id'], data['path'], data['url']))
            else:
                for v in data.values():
                    Client._recursive_search_url(v, output_folder, total, remain_directory_structure)

    def download_data(
            self,
            output_folder: str,
            data_id: Union[int, List[int], None] = None,
            dataset_id: Union[int, str, None] = None,
            remain_directory_structure: bool = True
    ) -> Union[str, List[Dict]]:
        """
        Download all data from a given dataset or download given data.

        Parameters
        ----------
        output_folder: str
            The folder path to save data.
        data_id: Union[str, List[str], None], default None
            A data id or a list or data ids.
            Pass this parameter to download given data.
        dataset_id: Union[int, str, None], default None
            A dataset id. You can find this in the last part of the dataset url, for example:
            ``https://localhost:8190/#/datasets/overview?id=766416``.
            Also, the id can be found in the attributes of an `Dataset` object.
            Pass this parameter to download all data from a given dataset.
        remain_directory_structure: bool, default True
            If this parameter is set to True, the folder structure of the data
            will remain exactly the same as it was uploaded.
            If this parameter is set to False, all data will be put in 'output_folder'
            even if there are files with the same name.

        Returns
        -------
        Union[str, List[Dict]]
            If find target data, returns a list of error information produced during downloading.
            If not find target data, returns 'No data'.
        """
        if data_id:
            data = self.query_data(data_id)
        else:
            if dataset_id:
                data = self._query_data_under_dataset(dataset_id)
            else:
                raise ParamException(message='You need to pass either data_id or dataset_id !!!')

        if not data:
            return 'No data'

        error_list = []
        total_list = []

        self._recursive_search_url(
            data=data,
            output_folder=output_folder,
            total=total_list,
            remain_directory_structure=remain_directory_structure,
        )

        for file in track(total_list, description='Downloading', ):
            try:
                if not remain_directory_structure:
                    output_path = os.path.join(output_folder, os.path.split(file[1])[2])
                else:
                    output_path = Path(output_folder, *Path(file[1]).parts[3:])
                cur_folder, cur_name = os.path.split(output_path)
                if not os.path.exists(cur_folder):
                    os.makedirs(cur_folder)

                with open(output_path, 'wb') as f:
                    f.write(requests.request('GET', file[2]).content)
            except:
                error_list.append(file)

        return error_list

    def _get_data_and_result_info(
            self,
            dataset_id: Union[int, str],
            data_ids: Union[int, List[int], None] = None
    ) -> Dict:
        endpoint = 'data/getDataAndResult'

        params = {
            'datasetId': dataset_id,
            'dataIds': data_ids
        }

        resp = self.api.get_request(endpoint=endpoint, params=params)

        return resp

    def query_data_and_result(
            self,
            dataset_id: Union[int, str],
            data_ids: Union[int, List[int], None] = None,
            limit: int = 5000,
            dropna: bool = False
    ) -> Annotation:
        """
        Query both the data information and the annotation result of a specific dataset.
        Accept a 'data_ids' parameter to query specific data.

        Parameters
        ----------
        dataset_id: Union[int, str]
            The id of the dataset you want to query.
        data_ids: Union[int, List[int], None], default None
            The id or ids of the data you want to query.
        limit: int, default 5000
            The max number of returned annotation results.
            Change this parameter according to your system memory.
        dropna: bool, default False
            Whether drop no result data or not.

        Returns
        -------
        Annotation
            An instance of Annotation class.
            It has some methods to convert the format of annotation result.
        """
        resp = self._get_data_and_result_info(dataset_id, data_ids)
        result_dict = {result['dataId']: result for result in resp['results']}
        annotation = [
            {
                'data': data,
                'result': result_dict.get(data['id'], {})
            }
            for data in resp['data'][:limit]
        ]

        if dropna:
            annotation = list(filter(lambda x: x['result'], annotation))

        return Annotation(
            client=self,
            annotation=annotation,
            dataset_name=resp['datasetName'],
            version=resp['version'],
            dataset_id=resp['datasetId'],
            export_time=resp['exportTime']
        )

    def query_classes_stat(
            self,
            dataset_id: Union[int, str]
    ) -> Dict:
        """
        Query the distribution of annotated classes.

        Parameters
        ----------
        dataset_id: Union[int, str]
            The id of the dataset you want to query.

        Returns
        -------
        Dict
            The statistic of the annotation result.
        """
        endpoint = f'dataset/{dataset_id}/statistics/classObject'

        return self.api.get_request(
            endpoint=endpoint
        )

    def _query_complete_ontology(
            self,
            endpoint: str,
            des_id: str,
            page_no: int = 1,
            page_size: int = 100,
    ):
        if 'dataset' not in endpoint:
            params = {
                'ontologyId': des_id,
            }
        else:
            params = {
                'datasetId': des_id,
            }

        params.update(
            {
                'pageNo': page_no,
                'pageSize': page_size
            }
        )

        resp = self.api.get_request(
            endpoint=endpoint,
            params=params
        )

        return resp['list']

    def _query_ontology_list(
            self,
            name,
            page_no: int = 1,
            page_size: int = 100
    ):
        endpoint = 'ontology/findByPage'

        params = {
            'name': name,
            'page_no': page_no,
            'page_size': page_size
        }

        resp = self.api.get_request(
            endpoint=endpoint,
            params=params
        )

        return resp

    def _query_ontology_info(
            self,
            des_id
    ):
        endpoint = f'ontology/info/{des_id}'

        resp = self.api.get_request(
            endpoint=endpoint
        )

        return resp

    def _query_a_single_ontology(
            self,
            des_id,
            des_type,
    ):
        if 'dataset' in des_type:
            endpoint1 = 'datasetClass/findByPage'
            endpoint2 = 'datasetClassification/findByPage'
            dataset_type = self._query_dataset_info(des_id)['type']
        else:
            endpoint1 = 'class/findByPage'
            endpoint2 = 'classification/findByPage'
            dataset_type = self._query_ontology_info(des_id)['type']

        classes = self._query_complete_ontology(
            endpoint=endpoint1,
            des_id=des_id
        )
        classifications = self._query_complete_ontology(
            endpoint=endpoint2,
            des_id=des_id
        )

        classifications = []

        return Ontology(
            client=self,
            des_type=des_type,
            classes=classes,
            classifications=classifications,
            des_id=des_id,
            dataset_type=dataset_type
        )

    def query_ontology(
            self,
            des_id: Optional[int] = None,
            name: Optional[str] = None,
            des_type='ontology_center',
            page_no: int = 1,
            page_size: int = 100
    ) -> Ontology:
        """
        Query the ontology from the given dataset or ontology center.

        Parameters
        ----------
        des_id: Optional[int], default None
            A dataset id or ontology id.
            Ontology id is the id of ontology from ontology center.
        name: Optional[str], default None
            The name of ontology from ontology center.
        des_type: str, default 'ontology_center'
            The source of ontology: 'ontology_center' or 'dataset'.
        page_no: int
            Current page number.
        page_size: int
            The max number of ontologies displayed in one query.

        Returns
        -------
        Ontology
            An `Ontology` object.
        """
        if not des_id and not name:
            raise ParamException(message="Can't miss both des_id and name!")

        if name and (not des_id):
            onto_list = self._query_ontology_list(
                name=name,
                page_no=page_no,
                page_size=page_size
            )
            total = onto_list['total']
            onto_ids = [onto['id'] for onto in onto_list['list']]
            result = []
            for onto_id in onto_ids:
                onto = self._query_a_single_ontology(
                    des_id=onto_id,
                    des_type=des_type
                )
                result.append(onto)

            return _to_single(result, total)

        return self._query_a_single_ontology(
            des_id=des_id,
            des_type=des_type
        )

    def create_ontology(
            self,
            ontology_name: str,
            dataset_type: str,
    ) -> Ontology:
        """
        Create an empty ontology in ontology center.
        Notice that every dataset has an empty ontology when it's created.

        Parameters
        ----------
        ontology_name: str
            The name of the ontology.
        dataset_type: str
            An annotation type that can only choose from this list:
            ['LIDAR_FUSION', 'LIDAR_BASIC', 'IMAGE']

        Returns
        -------
        Ontology
            An `Ontology` object.
        """
        endpoint = 'ontology/create'

        payload = {
            'name': ontology_name,
            'type': dataset_type
        }

        resp = self.api.post_request(
            endpoint=endpoint,
            payload=payload
        )

        des_type = 'ontology_center'
        des_id = resp

        return Ontology(
            client=self,
            des_type=des_type,
            classes=[],
            classifications=[],
            des_id=des_id,
            dataset_type=dataset_type
        )

    def delete_ontology(
            self,
            des_id: Union[int, str],
            is_sure=False
    ) -> bool:
        """
        Delete the ontology in your 'ontology center'.
        Notice that an ontology attached to a dataset can not be deleted.

        Parameters
        ----------
        des_id: Union[int, str]:
            An ontology id. You can find this in the last part of the ontology url, for example:
            ``https://localhost:8190/#/ontology/class?id=480002``.
            Also, the id can be found in the attributes of an `Ontology` object.
        is_sure: bool, default False
            Sure or not sure to delete this ontology.

        Returns
        -------
        bool
            True: delete complete.
            False: user is not sure to delete the ontology or the ontology is already deleted.
        """
        if not is_sure:
            return False

        endpoint = f'ontology/delete/{des_id}'

        resp = self.api.post_request(
            endpoint=endpoint
        )

        return resp
