import sys
from . import AkaiXPJFile, CCMappingDefinition
import json
import yaml

xpj = None


def identify_tracks_and_layers(xpj_file: AkaiXPJFile, target_file: str):
    tracks_report = xpj_file.report_tracks
    templates = []
    params = { 514: "Cutoff", 515: "Resonance"}
    base_midi_cc = 16
    for track_name, v in tracks_report.items():
        active_instruments = list(v['instruments'].keys())
        for param, description in params.items():
            templates.append({
                "midiCCMappingObject": {
                    "name": f"{track_name} - {description}",
                    "controlChannel": 1,
                    "midiCC": base_midi_cc,
                    "targetTrack": track_name,
                    "targetInstruments": active_instruments,
                    "targetParameter": param,
                }
            })
            base_midi_cc += 1
        templates.append({
                "midiCCMappingObject": {
                    "name": f"{track_name} - Volume",
                    "controlChannel": 1,
                    "midiCC": base_midi_cc,
                    "targetTrack": track_name,
                    "targetInstruments": [257],
                    "targetParameter": 7,
                }
        })
    with open(target_file, 'w', encoding='utf-8') as fh:
        yaml.dump_all(templates, fh, Dumper=yaml.SafeDumper, explicit_start=True, default_flow_style=None)

def main(args):
    global xpj
    xpj = AkaiXPJFile(args[0])
    #print("\n".join(xpj.discover_top_keys(3, 'data', xpj.data)))
    #print(json.dumps(xpj.keygroup_track_instruments, indent=4))
    #instrs = xpj.keygroup_track_instruments
    #with open('mls.json', 'w', encoding='utf-8') as fh:
    #    json.dump(xpj.midi_learn_settings, fh, indent=2)
#
    #with open('all_instruments.json', 'w', encoding='utf-8') as fh:
    #    json.dump(xpj.all_instruments, fh, indent=2)
    #with open('all_populated_instruments.json', 'w', encoding='utf-8') as fh:
    #    json.dump(xpj.all_instruments_with_samples, fh, indent=2)
    
    midi_cc_changes = None
    if args[1] == 'change-mappings':
        with open(args[2], 'r', encoding='utf-8') as fh:
            midi_cc_changes = list(yaml.load_all(fh, Loader=yaml.SafeLoader))
    elif args[1] == 'make-mapping-template':
        identify_tracks_and_layers(xpj_file=xpj, target_file=args[2])
    if midi_cc_changes:
        print("changing MIDI CC Mappings")
        xpj.clear_midi_mappings()
        for cc in midi_cc_changes:
            b = cc['midiCCMappingObject']
            ccMapping = CCMappingDefinition(**b)
            xpj.add_midi_mapping(ccMapping)
        xpj.save_to(args[3])

main(sys.argv[1:])
