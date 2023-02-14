from functools import reduce


# from typing import Union, List, Dict, Optional
# from rich.table import Table
# from rich import box
# from .dataset import Dataset


# def _get_value_by_key(json_info, key, nth=-1, cur_cnt=0):
#     if type(json_info) == list:
#         result = []
#         for j in json_info:
#             single_result, cur_cnt = _get_value_by_key(j, key, nth, cur_cnt)
#             if single_result:
#                 if cur_cnt == nth:
#                     return single_result, cur_cnt
#                 result.append(single_result)
#         return result, cur_cnt
#
#     elif type(json_info) == dict:
#         value = json_info.get(key)
#         if value:
#             cur_cnt += 1
#             return value, cur_cnt
#
#         for k, v in json_info.items():
#             if type(v) in [dict, list]:
#                 result, cur_cnt = _get_value_by_key(v, key, nth, cur_cnt)
#                 if result:
#                     return result, cur_cnt
#
#     return None, cur_cnt
#
#
# def _find_nth(key_param):
#     loc = key_param.find(':')
#     if loc == -1:
#         return key_param, 0
#     return key_param[:loc], int(key_param[loc + 1:])
#
#
# def _get_value_by_keys(json_info, keys):
#     result = json_info
#
#     for k in keys:
#         key, n = _find_nth(k)
#         result, _ = _get_value_by_key(result, key, n)
#
#     return result
#
#
# def get_values(json_info, needed_keys):
#     result = []
#
#     if type(json_info) == list:
#         for j in json_info:
#             result.append(get_values(j, needed_keys))
#
#     elif type(json_info) == dict:
#         for k in needed_keys:
#             if type(k) in [tuple, list]:
#                 result.append(_get_value_by_keys(json_info, k))
#             else:
#                 key, n = _find_nth(k)
#                 result.append(_get_value_by_key(json_info, key, n)[0])
#
#     return result
#
#
# def as_table(
#         target_list: List[Union[Dataset, List, Dict]],
#         blocks: Optional[List[str]] = None,
#         headers: Optional[List[str]] = None
# ):
#     if blocks is None:
#         blocks = []
#
#     sample = target_list[0]
#     if not headers:
#         if type(sample) == dict:
#             headers = sample.keys()
#         elif type(sample) == Dataset:
#             blocks += ['data', '_client']
#             headers = sample.__dict__
#         else:
#             headers = ['']
#         headers = [key for key in headers if key not in blocks]
#
#     total = []
#     if type(sample) == Dataset:
#         total = [x.show_attrs(blocks).values() for x in target_list]
#     elif type(sample) == dict:
#         total = [[v for k, v in y.items() if k not in blocks] for y in target_list]
#     elif type(target_list[0]) == list:
#         total = target_list
#
#     tb = Table(*headers, box=box.SIMPLE_HEAD)
#
#     for data in total:
#         tb.add_row(*map(str, data))
#
#     return tb


def _to_single(query_result, total):
    if total == 1:
        return query_result[0]
    return query_result, total


def _parse_data_info(data_content: list):
    datas = []
    for data in data_content:
        one_data = {
            "id": data['id'],
            "name": data['name']
        }
        datas.append(one_data)
    return datas
