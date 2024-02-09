import json



class FakeDict(dict):
    def __init__(self, items):
        self['something'] = 'something'
        self._items = items
    def items(self):
        return self._items

    @staticmethod
    def to_json(tuple_list: list[tuple]):
        return json.dumps(FakeDict(tuple_list), indent=4)

    @staticmethod
    def dicts_to_json(*dicts):
        keys = []
        for dict in dicts:
            for k, v in dict.items():
                keys.append((k, v))
        return FakeDict.to_json(keys)
