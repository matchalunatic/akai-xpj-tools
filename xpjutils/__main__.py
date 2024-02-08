import sys
from . import AkaiXPJFile, CCMappingDefinition
import json
import yaml


def main(args):
    print("ARgz", args)
    xpj = AkaiXPJFile(args[0])
    print(xpj)
    #print("\n".join(xpj.discover_top_keys(3, 'data', xpj.data)))
    #print(json.dumps(xpj.keygroup_track_instruments, indent=4))
    instrs = xpj.keygroup_track_instruments
    print(len(instrs))
    print(instrs.keys())
    dumped = json.dumps(instrs, indent=4)
    print(json.dumps(instrs[1], indent=2))
    with open('mls.json', 'w', encoding='utf-8') as fh:
        json.dump(xpj.midi_learn_settings, fh, indent=2)

    with open('all_instruments.json', 'w', encoding='utf-8') as fh:
        json.dump(xpj.all_instruments, fh, indent=2)
    with open('all_populated_instruments.json', 'w', encoding='utf-8') as fh:
        json.dump(xpj.all_instruments_with_samples, fh, indent=2)
    
    midi_cc_changes = None

    with open(args[1], 'r', encoding='utf-8') as fh:
        midi_cc_changes = list(yaml.load_all(fh, Loader=yaml.SafeLoader))
    
    if midi_cc_changes:
        print("changing MIDI CC Mappings")
        xpj.clear_midi_mappings()
        for cc in midi_cc_changes:
            b = cc['midiCCMappingObject']
            ccMapping = CCMappingDefinition(**b)
            xpj.add_midi_mapping(ccMapping)
        xpj.save_to('Demons.xpj')


def compare(a, b):
    xpj1 = AkaiXPJFile(a)
    xpj2 = AkaiXPJFile(b)
    with open('comp1.json', 'w', encoding='utf-8') as fh:
        json.dump(xpj1._json, fh, indent=2)
    with open('comp2.json', 'w', encoding='utf-8') as fh:
        json.dump(xpj2._json, fh, indent=2)
    with open('comp1.raw.json', 'wb') as fh:
        fh.write(xpj1.raw_json)
    with open('comp2.raw.json', 'wb') as fh:
        fh.write(xpj2.raw_json)
if sys.argv[1] == 'compare':
    compare(sys.argv[2], sys.argv[3])
else:
    main(sys.argv[1:])
