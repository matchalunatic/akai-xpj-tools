import gzip
import json
from dataclasses import dataclass


@dataclass
class AkaiMidiLearnSettingsControlTargetParamIndex:
    initialized: bool = False


@dataclass
class AkaiControlRange:
    min: float
    max: float
    stride: float
    deadspot: float
    skew: float


@dataclass
class AkaiMidiLearnSettingsControlTargetControlInputRange(AkaiControlRange):
    pass


@dataclass
class AkaiMidiLearnSettingsControlTargetParameterRange(AkaiControlRange):
    pass


@dataclass
class AkaiMidiLearnSettingsControlTarget:
    version: int
    parameter: int
    track: str
    insert_param_index: AkaiMidiLearnSettingsControlTargetParamIndex
    instrument_index: int
    param_type: int
    control_input_range: AkaiMidiLearnSettingsControlTargetControlInputRange
    parameter_range: AkaiMidiLearnSettingsControlTargetParameterRange
    behaviour: int


@dataclass
class AkaiMidiLearnSettingsControl:
    name: str
    control_type: int
    target_data: AkaiMidiLearnSettingsControlTarget
    momentary: int
    control_value: float


@dataclass
class AkaiMidiLearnSettingsMapping:
    mapping_type: int
    control_type: int
    channel: int
    data1: int
    reverse_input: bool


@dataclass
class AkaiMidiLearnSettings:
    control: AkaiMidiLearnSettingsControl
    mapping: AkaiMidiLearnSettingsMapping


@dataclass
class CCMappingDefinition:
    name: str
    controlChannel: int
    midiCC: int
    targetTrack: str
    targetInstruments: list[int]
    targetParameter: int

    def to_akai_format(self):
        # fixme: use the proper dataclasses to make conversions
        tgtData = []
        for inst in self.targetInstruments:
            tgtData.append(
                {
                    "version": 1,
                    "parameter": self.targetParameter,
                    "track": self.targetTrack,
                    "insertParamIndex": {
                        "initialized": False,
                    },
                    "instrumentIndex": inst,
                    "paramType": 0,
                    "controlInputRange": {
                        "min": 0.0,
                        "max": 1.0,
                        "stride": 0.0,
                        "deadspot": 2.0,
                        "skew": 1.0,
                    },
                    "parameterRange": {
                        "min": 0.0,
                        "max": 1.0,
                        "stride": 0.0,
                        "deadspot": 2.0,
                        "skew": 1.0,
                    },
                    "behaviour": 0,
                }
            )
        return {
            "control": {
                "name": self.name,
                "controlType": 0,
                "targetData": tgtData,
                "momentary": 0,
                "controlValue": 0.4214321,  # a random value
            },
            "mapping": {
                "mappingType": 2,
                "controlType": 5,
                "channel": self.controlChannel,
                "data1": self.midiCC,
                "reverseInput": False,
            },
        }


def duplicate_locators_pair_hook(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            assert k == 'locators'
            if isinstance(v, dict) and 'names' in v:
                d['locators__1'] = v
            elif isinstance(v, list) and len(v) and "bar" in v[0]:
                d['locators__2'] = v
            else:
                raise ValueError(f"Bad locators entry %s", v)
        else:
            d[k] = v
    return d


class AkaiXPJFile:
    @property
    def midi_learn_settings(self):
        return self._json["data"]["midiLearnSettings"]

    @property
    def data(self):
        return self._json["data"]

    @property
    def raw_json(self):
        return self._raw_json_bytes
    @property
    def keygroup_track_instruments(self):
        res = {}
        total_layer_counter = 0
        for idx, track in enumerate(self.tracks):
            program = track["program"]
            try:
                instrus = program["drum"]["instruments"]
            except:
                continue
            worth_layers = {}
            for instru in instrus:
                layers = instru["layers"]
                for layerKeyName, layer in layers.items():
                    if len(layer["sampleName"]):  # we have a hit
                        worth_layers[total_layer_counter] = layer
                    total_layer_counter += 1
            res[idx + 1] = worth_layers
        return res

    @property
    def all_instruments(self):
        res = {}
        total_instruments_counter = 0
        for track in self.tracks:
            program = track["program"]
            if "drum" not in program or "instruments" not in program["drum"]:
                continue
            for instrument in program["drum"]["instruments"]:
                res[total_instruments_counter] = instrument
                total_instruments_counter += 1
        return res

    @property
    def all_instruments_with_samples(self):
        def pred(item):
            if "layers" not in item:
                return False
            return any(len(x["sampleName"]) > 0 for x in item["layers"].values())

        res = self.all_instruments
        for item in list(res.keys()):
            v = res[item]
            if not pred(v):
                del res[item]
        return res

    @property
    def tracks(self):
        return self._json["data"]["tracks"]

    def __init__(self, path):
        self._path = path
        self._data = bytearray(0)
        self._json = None
        self._program_version = b""
        self._file_kind = b""
        self._file_type = b""
        self._platform = b""
        self._raw_json_bytes = b""
        self.load_data()

    def clear_midi_mappings(self):
        self._json["data"]["midiLearnSettings"] = dict(controls=[])

    def add_midi_mapping(self, midi_mapping: CCMappingDefinition):
        self._json["data"]["midiLearnSettings"]["controls"].append(
            midi_mapping.to_akai_format()
        )

    def save_to(self, path):
        out = bytearray()
        out.extend(b"ACVS\x0a")
        out.extend(self._program_version)
        out.extend(b"\x0a")
        out.extend(self._file_kind)
        out.extend(b"\x0a")
        out.extend(self._file_type)
        out.extend(b"\x0a")
        out.extend(self._platform)
        out.extend(b"\x0a")
        locators1 = self._json['data']['locators__1']
        locators2 = self._json['data']['locators']
        data_clone = dict(self._json['data'])
        del data_clone['locators__1']
        del data_clone['locators']
        json_data = json.dumps({"data": data_clone}, indent=4)
        # urgh
        json_data = json_data.replace('"clipPlayerData":', json.dumps({"locators": locators1})[1:-1] + ', "clipPlayerData":')
        json_data = json_data.replace('"scene":', json.dumps({"locators": locators2})[1:-1] + ', "scene":')
        # reindent
        with open('argh.json', 'w', encoding='utf-8') as fh:
            fh.write(json_data)
        # json_data = json.dumps(json.loads(json_data), indent=4)
        json_bytes = json_data.encode('utf-8')
        out.extend(json_bytes)
        with gzip.open(path, "wb", compresslevel=6) as fh:
            fh.write(out)

    def load_data(self):
        with gzip.open(self._path, "rb") as fh:
            self._data[:] = fh.read()
        signature, program_version, file_kind, file_type, platform, payload = (
            self._data.split(b"\x0a", 5)
        )
        assert signature == b"ACVS"
        assert file_type == b"json"
        self._file_type = file_type
        self._file_kind = file_kind
        self._program_version = program_version
        self._platform = platform
        # print('payload', len(payload))
        self._raw_json_bytes = payload
        with open("raw.json", "w", encoding="utf-8") as fh:
            fh.write(payload.decode("utf-8"))
        self._json = json.loads(payload, object_pairs_hook=duplicate_locators_pair_hook)

    def discover_top_keys(self, depth=3, prefix: str = None, root: dict = None) -> list:
        if root is None:
            root = self._json
            prefix = ""
        if depth == 0:
            return []
        res = []
        if isinstance(root, (str, int, float)):
            return []

        if isinstance(root, list):
            return []
        for k, v in root.items():
            if isinstance(v, dict):
                res += self.discover_top_keys(depth - 1, f"{prefix}.{k}", v)
            elif (
                isinstance(v, list)
                and len(v)
                and not isinstance(v[0], (str, float, int))
            ):
                res += self.discover_top_keys(depth - 1, f"{prefix}.{k}[]", v[0])
            else:
                res.append(f"{prefix}.{k}#")
        return res
