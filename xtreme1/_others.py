from functools import reduce


def groupby(
        items,
        func,
        assign_keys=None
):
    if assign_keys:
        result = {k: [] for k in assign_keys}
    else:
        result = {}

    for x in items:
        k = func(x)
        result.setdefault(k, []).append(x)

    return result


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
