import gzip
import json
from dataclasses import dataclass

from xpjutils.constants import PROGRAM_TYPE_DRUM, PROGRAM_TYPE_KEYGROUP
from .dupjson import FakeDict

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
        if k == 'locators':
            if isinstance(v, dict) and 'names' in v:
                d['locators__2'] = v
            elif isinstance(v, list) and len(v) and 'bar' in v[0]:
                d['locators__1'] = v
        else:
            if k in d:
                raise NotImplementedError(f"unhandled duplicate json key {v}, please add handler")
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
    def report_tracks(self):
        report_tracks = {}
        for track in self.data['tracks']:
            program = track['program']
            if program['type'] not in (PROGRAM_TYPE_DRUM, PROGRAM_TYPE_KEYGROUP):
                continue
            samples = track['samples']
            instruments = program['drum']['instruments']
            # now identify active instruments, ones with at least one layer that has samples
            active_instruments = {}
            referenced_samples = []
            for num, instrument in enumerate(instruments):
                active = False
                samples_in_use = []
                for layer in instrument['layers'].values():
                    if len(layer['sampleName']):
                        active = True
                        samples_in_use.append(layer['sampleName'])
                if not active:
                    continue
                low_note = instrument['lowNote']
                high_note = instrument['highNote']
                coarse_tune = instrument['coarseTune']
                fine_tune = instrument['fineTune']
                active_instruments[num] = {
                    'low_note': low_note,
                    'high_note': high_note,
                    'coarse_tune': coarse_tune,
                    'fine_tune': fine_tune,
                    'samples_in_use': samples_in_use,
                }
            for sample in samples:
                referenced_samples.append(sample['name'])
            report_tracks[track['name']] = {
                'referenced_samples': referenced_samples,
                'instruments': active_instruments,
            }
        return report_tracks

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
    def serialized_json(self):
        """this is special because we need to generate duplicate keys which are not supported well by """
        dict1_k = ['version', 'key', 'mixer', 'emulation', 'masterTempoEnabled', 'masterTempo']
        dict3_k = ['scene', 'samples', 'tracks', 'sequences', 'songs', 'qlinkProjectModeAssignments', 'qlinkPadSceneModeAssignments', 'qlinkPadParamModeAssignments', 'padPerformSettings', 'qlinkMode', 'currentAssignableXFader', 'currentAssignablePadBank', 'currentAssignableEnvelopeFollower', 'info', 'qlinkProjectModeAssignments2', 'assignableXFaderAssignments', 'assignableXYPadAssignments1', 'assignableXYPadAssignments2', 'assignableXYPadAssignments3', 'assignableXYPadAssignments4', 'assignablePadGridAssignments', 'assignableEnvelopeFollowerAssignments']
        dict4_k = ['clipPlayerData', 'midiSendDestinations', 'midiLearnSettings', 'quantiser', 'currentTrackIndex', 'parameterSnapshotterData', 'rowLaunchSnapshotAssignments', 'engineMode', 'sharedClipMatrixData', 'currentClipRow', 'arpeggiatorProperties', 'mpcControlSurfaceBehaviour', 'midiNoteFilterPipe', 'xyfxResponder']
        contents = []
        dat = self._json['data']
        for k in dict1_k:
            contents.append((k, dat[k]))
        contents.append(('locators', dat['locators__1']))
        for k in dict3_k:
            contents.append((k, dat[k]))
        contents.append(('locators', dat['locators__2']))
        for k in dict4_k:
            contents.append((k, dat[k]))

        # now validate top-level keys to make sure we do not miss fields in new versions
        for k in dat:
            if k in ('locators__1', 'locators__2', 'locators'):
                continue
            if k not in dict1_k and k not in dict3_k and k not in dict4_k:
                raise NotImplementedError(f"We are not dumping field {k}, need a bugfix")
        return FakeDict.to_json([('data', FakeDict(contents))])
    
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
        json_bytes = self.serialized_json.encode('utf-8')
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
