from typing import List, Dict, Optional, Union

from .exporter.annotation import Annotation
from .ontology.ontology import Ontology


class Dataset:

    def __init__(
            self,
            org_json,
            client
    ):
        self.id = org_json.get('id')
        self.name = org_json.get('name')
        self.type = org_json.get('type')
        self.description = org_json.get('description')
        self.annotated_count = org_json.get('annotatedCount')
        self.unannotated_count = org_json.get('notAnnotatedCount')
        self.invalid_count = org_json.get('invalidCount')
        self.item_count = org_json.get('itemCount')
        self._client = client

    def __str__(self):
        return f"<{self.__class__.__name__}> id={self.id}, name={self.name}"

    def __repr__(self):
        return f"<{self.__class__.__name__}> id={self.id}, name={self.name}"

    def show_attrs(
            self,
            blocks=None
    ) -> Dict:
        """
        Get all attributes of the dataset.

        Parameters
        ----------
        blocks: List
            Attributes you don't need.

        Returns
        -------
        Dict
            Attributes of the dataset.
        """
        if blocks is None:
            blocks = []
        blocks.append('_client')

        return {k: v for k, v in self.__dict__.items() if k not in blocks}

    def edit(
            self,
            new_name: Optional[str] = None,
            new_description: Optional[str] = None
    ):
        """
        Change the name or description of a dataset.

        Parameters
        ----------
        new_name: str
            New name of the dataset.
        new_description: Optional[str], default None
            New description of the dataset

        Returns
        -------
        str
            'Success'.
        """
        self.name = new_name or self.name
        self.description = new_description or self.description
        return self._client.edit_dataset(self.id, self.name, self.description)

    def delete(
            self,
            is_sure: bool
    ) -> str:
        """
        Delete a dataset.

        Parameters
        ----------
        is_sure: bool, default False
            Set it to 'True' to delete the dataset.

        Returns
        -------
        str
            'Unsure' if 'is_sure' is not set to 'True'.
            'Success' if the dataset is deleted.
        """
        return self._client.delete_dataset(self.id, is_sure)

    def query_data(
            self,
            page_no: int = 1,
            page_size: int = 10,
            name: Optional[str] = None,
            create_start_time: Optional[str] = None,
            create_end_time: Optional[str] = None,
            sort_by: Optional[str] = None,
            ascending: Optional[bool] = True,
            annotation_status: Optional[str] = None,
    ) -> Dict:
        """
        Query data under current dataset with some filters.
        Notice that 'data' ≠ 'file'. For example:
        for a 'LIDAR_FUSION' dataset, a copy of data means:
        'a pcd file' + 'a camera config json' + 'several 2D images'.

        Parameters
        ----------
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
            Json data containing all the data you're querying and information of all the files within these data.
        """

        return self._client.query_data_under_dataset(
            self.id,
            page_no,
            page_size,
            name,
            create_start_time,
            create_end_time,
            sort_by,
            ascending,
            annotation_status
        )

    def download_data(
            self,
            output_folder: str,
            data_id: Union[str, List[str], None] = None,
            remain_directory_structure: bool = True
    ) -> List[Dict]:
        """
        Download all or given data from current dataset.

        Parameters
        ----------
        output_folder: str
            The folder path to save data.
        data_id: Union[str, List[str], None], default None
            A data id or a list or data ids.
            Pass this parameter to download given data.
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
        return self._client.download_data(
            output_folder=output_folder,
            data_id=data_id,
            dataset_id=self.id,
            remain_directory_structure=remain_directory_structure
        )

    def query_data_and_result(
            self,
            data_ids: Union[int, List[int], None] = None,
            limit: int = 5000,
            dropna: bool = False
    ) -> Annotation:
        """
        Query both the data information and the annotation result of current dataset.
        Accept a 'data_ids' parameter to query specific data.

        Parameters
        ----------
        data_ids: Union[int, List[int], None], default None
            The id or ids of the data you want to query.
        limit: int, default 5000
            The max number of returned annotation results.
            Change this parameter according to your system memory.
        dropna: bool, default False
            Whether the unannotated data is preserved or not.

        Returns
        -------
        Annotation
            An instance of Annotation class.
            It has some methods to convert the format of annotation result.
        """

        return self._client.query_data_and_result(
            dataset_id=self.id,
            data_ids=data_ids,
            limit=limit,
            dropna=dropna
        )

    def query_classes_stat(
            self
    ) -> Dict:
        """
        Query the distribution of annotated classes.

        Returns
        -------
        Dict
            The statistic of the annotation result.
        """
        return self._client.query_classes_stat(
            dataset_id=self.id
        )

    def query_ontology(
            self
    ) -> Ontology:
        return self._client.query_ontology(
            des_id=self.id,
            des_type='dataset',
            name=None
        )
