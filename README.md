# XPJ Utils

Tools to manipulate XPM files from modern Akai workstations (Akai Force, Akai MPC series)

## XPJ file format

A XPJ file is a gzipped text file basically serializing a big JSON structure.

The format is as follows, once gunzipped:

```hex
ACVS\x0a<ProgramVersionInAscii>\x0a<KindOfFile>\x0a<FileFormat>\x0a<ProductionPlatform>\x0a<Payload>
```

The first characters are "ACVS", the program version is a text string of numbers, the kind of file is "SerialisableProjectData", the file format is "json", the production platform is "Linux" for my example, and the payload is a simple JSON string.

## Manipulating XPJ data

gunzip the file, make the changes you want, gzip the file, you're done. This python library helps with that.

## Filter architecture for keygroup

The keygroup architecture is as follows:

- A keygroup instrument is made of keygroups
- Each keygroup covers a potentially overlapping keyboard range
- Each keygroup is made of 4 layers, potentially empty. A Layer will hold info about how to play a given sample
- In a keygroup track, each keygroup is considered its own instrument, and because of that:
  - Each keygroup has a unique filter settings set for it

Because of that if you want to control filter parameters for your entire keygroup, you need to drive several parameters at once.

