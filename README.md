# Xtreme1 Python SDK

## Installation

~~~python
pip install xtreme1
~~~

---

## Usage

```python
from xtreme1.client import Client

BASE_URL = 'http://localhost:8190'
ACCESS_TOKEN = '...jDC9Pfk9Xstt9vaanXkh8...'

x1_client = Client(
    base_url=BASE_URL, 
    access_token=ACCESS_TOKEN
)
```
---

### Datasets

A dataset contains a group of data and an ontology.

You can upload/query the data or annotation result here.

#### Create a dataset

You can use this method to create a dataset.

For now, supported annotation types are: **['LIDAR_FUSION', 'LIDAR_BASIC', 'IMAGE']**.

```python
car_dataset = x1_client.create_dataset(
    name='test', 
    annotation_type='IMAGE', 
    description='A test dataset.'
)
```
#### Query dataset

You can use this method to query a dataset or a list of datasets.

There are two important parameters: 'page_no' and 'page_size'. The queried result is splitted into pages like an iterator. You can change 'page_size' to get more or fewer datasets at a time and change 'page_no' to load the next page of all queried results.

```python 
# Query one single dataset by passing a dataset id
dataset = x1_client.query_dataset(dataset_id='888888')
print(dataset) 
# Dataset(id=888888, name=driver_dataset)

# Query a list of datasets with some filters
dataset_list, total = x1_client.query_dataset(
    page_no = 1, # default 1
    page_size = 3, # default 1
    dataset_name = 'car', # fuzzy query
    create_start_time = (2022, 1, 1),
    create_end_time = (2023, 1, 1),
    sort_by = 'CREATED_AT', # ['NAME', 'CREATED_AT', 'UPDATED_AT']
    ascending = True,
    dataset_type = 'LIDAR_FUSION'
)
print(dataset_list)
"""
[Dataset(id=888000, name=car_dataset1),
 Dataset(id=888001, name=car_dataset2),
 Dataset(id=888002, name=car_dataset3)]
"""
print(total) 
# 21
```
---

### Data

Data ≠ File! Data is the unit of your annotation work. For example:

- For an 'IMAGE' dataset, a copy of data means an independent image.
- For a 'LIDAR_BASIC' dataset, a copy of data means a pcd file.
- However, for a 'LIDAR_FUSION' dataset, a copy of data means **a pcd file + a camera config file + several images** because all these files together make an annotation work.

#### Query data under the dataset

This method is similar to the above one.

It returns a long dict. If you want to simplify this dict, use 'get_values()' to select specific keys in the dict. After that, you can use 'as_table()' to show the data in tabular form and use 'rich.print()' to print this table.

```python
data_dict = x1_client.query_data_under_dataset(
	dataset_id = '888888',
    page_no = 1, # default 1
    page_size = 10, # default 10
    name = None,
    create_start_time = None,
    create_end_time = None,
    sort_by = 'CREATED_AT',
    ascending = True,
    annotation_status = 'ANNOTATED' # ['ANNOTATED', 'NOT_ANNOTATED', 'INVALID']
)

# Or use 'dataset.query_data(...)'
data_dict = car_dataset.query_data(page_size=10)
```

#### Download data

A method for downloading data from a remote dataset. It will recursively search data urls in a query result and download files one by one.

Notice that the directory of your data will remain the same as they were uploaded in the '.zip' file. You can also put your files in one single folder by setting the 'remain_directory_structure' parameter to 'False'.

~~~python
# Download '777777' to the given folder 'my_dataset'
x1_client.download_data(
    output_folder='my_dataset', 
    dataset_id='777777'
)
~~~

---

### Annotation

A class contains all methods that convert json format to other widely used formats.

An instance of this class will be automatically generated after using the 'query_data_and_result' method.

It's not recommended to instantiate this class by yourself, because the annotation result needed is a list of dict in a specific format. 

#### Query annotation result

The 'query_data' method only returns information about data, but this 'query_data_and_result' method returns data information and annotation results together.

It returns an instance of the 'Annotation' class, which is convenient for format converting.

~~~python
my_annotation = x1_client.query_data_and_result(
    dataset_id='777777',
    limit = 1000
)
print(my_annotation) # Annotation(dataset_id=777777, dataset_name=test_dataset)

# Check all annotation results
my_annotation.annotation

# Check a few annotation results
my_annotation.head()

# Convert raw annotation results to BasicAI standard json
my_annotation.to_standard_json(
    export_folder='my_annotation_result'
)
~~~

Notice that this method only returns limited annotation results. If you want to download all annotation results, try this:

~~~python
i = 0
while True:
    i += 1
    data_list = x1_client.query_data_under_dataset(dataset_id='766402', page_no=i)['list']
    if not data_list:
        break
    
    data_ids = [x['id'] for x in data_list]
    my_annotation = x1_client.query_data_and_result(dataset_id='766402', data_ids=data_ids)
    
    # Any further actions
    my_annotation.to_standard_json(
        export_folder='my_annotation_result'
    )
~~~

---

### Ontology

An ontology encompasses a representation, formal naming, and definition of the categories, properties, and relations between the concepts, data, and entities.

#### Query ontology

You can query an ontology from a dataset or from the ontology center.

This function returns an `Ontology` object.

~~~python
# Query the ontology of a dataset
my_dataset = x1_client.query_dataset(
    dataset_id='888888'
)
onto = my_dataset.query_ontology()

# Query the ontology from your ontology center
onto = x1_client.query_ontology(
    des_id='11111', 
    des_type='ontology_center'
)
~~~

#### Import ontology

Import ontology to your online dataset or ontology center.

Notice that this function will not delete the old classes/classifications, but may update them if you have edited them. 

In my case, I changed the name of the 'car' class. Therefore, this class will be updated once I use the 'import_ontology' function.

~~~python
# Import the current ontology
onto.import_ontology()

# Import another existing ontology to current empty ontology
onto2 = my_client.query_ontology(
    des_id='22222', 
    des_type='ontology_center'
)
# Create a copy of ontology
# .copy() function clears the ids of ontology and classes/classifications
onto2_copy = onto2.copy()
onto.import_ontology(
	ontology=onto2
)
~~~

### Model

Xtreme1 has some available models. 

Use them properly to decrease your annotating time.

~~~python
img_model = x1_client.image_model
model_result = img_model.predict(
    min_confidence=0.7,
    dataset_id=777777
)
~~~

