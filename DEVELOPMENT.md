# Development

## Checks and formatting

Use Python 3.10 or newer and Bash. Install the pinned tools in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
export PATH="$PWD/.venv/bin:$PATH"
python3 scripts/check.py
```

Run `python3 scripts/check.py --fix` to format Python and shell and normalize text whitespace. The same checks run on pushes and pull requests. XML is checked for well-formedness; game schemas, XPath matches and gameplay require separate X4 validation. Blender scripts are parsed and linted without importing Blender.

Use UTF-8, LF, a final newline, spaces and no trailing whitespace. Indent code with four spaces and workflow YAML with two. Use descriptive names, uppercase shell variables, constant-first equality comparisons and explicit boolean checks. Ruff's E712 rule is disabled to retain explicit boolean comparisons. Keep shell free of prose comments. Keep only short, non-obvious constraints in code; put explanations here. XML continuation attributes may align with their opening attribute. Preserve XPath selectors, savegame identifiers and embedded game expressions when applying formatting.

## Installation and publishing helpers

`install.sh` and `publish.sh` both source `lib/find_x4.sh`. The library searches usual Steam roots and additional library folders. `X4_PATH`, `X_TOOLS_PATH`
and `PROTON_PATH` override discovery. Proton Experimental is preferred when found; otherwise the helper uses the last matching Proton directory it encounters.

Installation replaces the extension directory with a copy of `extension/`. Refresh it after edits; X4 enumerates real extension directories, so a symlink does not substitute for installation. Restart the game after installing or removing.

Publishing stages a separate copy inside the game's extensions directory. The repository keeps its readable extension id; `steam/workshop-id` holds the numeric Workshop id. The helper changes only the staged manifest, runs the interactive WorkshopTool and restores the manual installation after success. On Linux it runs WorkshopTool through Proton and maps paths through drive Z. A failed upload can leave the staged copy behind; rerun `./install.sh` to restore it.

## Release metadata

`content.xml` uses an integer version multiplied by 100 and an ISO release date. The date matches the corresponding released entry in `CHANGELOG.md`. Development changes belong under `Unreleased`; they do not advance the manifest's release version or date. An unreleased scaffold may retain its initial creation date until its first release. Keep existing extension ids stable.

## Mesh conversion

`soase_import.py` reads Ironclad's text mesh format, an indentation-nested key-value tree whose blocks
repeat by name. It refuses binary meshes; convert those with ConvertX first. Sins uses X right, Y up
and Z forward, so the converter maps `(x, y, z)` to `(-x, z, y)`: swapping the two axes alone would
mirror the model, and negating X restores the handedness. Triangle winding is reversed to match, and
the V coordinate is flipped from the DirectX convention OBJ does not use. Hardpoint orientations are
transformed row by row; in this source they are all identity and carry no facing information.

`andromeda_import.py` imports the OBJ with `forward_axis="Y"` and `up_axis="Z"` so Blender's own axis
conversion stays out of the way, then scales, centres, decimates and places connections. Keep both
scripts self-contained: they are pasted into Blender's text editor, not installed as modules.

## Exporting to xmf

The Egosoft Blender Mod Tools install four Blender 4.2 extensions and `XUConverter.exe`. Install the
extensions from their zips with `blender --command extension install-file -r user_default -e <zip>`;
the export operator is `ego_tools.export_data`, and it runs headless. The `.blend` path must contain
the literal string `[assets]` or the operator refuses to run. Set `scene.classAttr` to `ship_xl`
before exporting.

Connection empties are tagged, not named: X4 reads the tags, and the names are free. The exporter
takes tags from registered property groups, and falls back to an `extratags` string property, which is
what a headless build uses because the add-on property groups are not registered under
`--factory-startup`.

`XUConverter.exe` takes a source and a destination folder as arguments and then watches the source. It
does not run under Proton: Proton's builtin `CONCRT140` lacks symbols the converter imports, and
`mfc140` is missing entirely. Run it under plain Wine instead, in a container with the real Microsoft
runtime installed by `winetricks -q vcrun2022`. Conversion triggers on file changes, so rewrite the
`.dae` after the watcher starts.

## Generator geometry

The axis convention is +Y forward and +Z up. Hull profile rows hold position, half-width, half-height and vertical offset as fractions of SHIP_LENGTH. Position 0 is the prow and 1 the stern. Separate superellipse exponents give the belly a flatter section than the deck. See README.md for generator use and parameters.
