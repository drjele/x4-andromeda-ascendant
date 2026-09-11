# Development

## Checks and formatting

Use Python 3.10 or newer and Bash. Install the pinned tools in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
export PATH="$PWD/.venv/bin:$PATH"
python3 scripts/check.py
```

Run `python3 scripts/check.py --fix` to format Python and shell and normalize text whitespace. The same checks run on pushes and pull requests. Checks include XML well-formedness, local index/macro/component references, localization, texture mip chains and conversion/installer regression tests. Game schemas, XPath matches and gameplay still require separate X4 validation. Blender scripts are parsed and linted without importing Blender; run `blender -b --python-exit-code 1 --python scripts/check_blender.py` for geometry and mount tests.

Use UTF-8, LF, a final newline, spaces and no trailing whitespace. Indent code with four spaces and workflow YAML with two. Use descriptive names, uppercase shell variables, constant-first equality comparisons and explicit boolean checks. Ruff's E712 rule is disabled to retain explicit boolean comparisons. Keep shell free of prose comments. Keep only short, non-obvious constraints in code; put explanations here. XML continuation attributes may align with their opening attribute. Preserve XPath selectors, savegame identifiers and embedded game expressions when applying formatting.

## Installation and publishing helpers

`install.sh` and `publish.sh` both source `lib/find_x4.sh`. The library searches usual Steam roots and additional library folders. `X4_PATH`, `X_TOOLS_PATH`
and `PROTON_PATH` override discovery. Proton Experimental is preferred when found; otherwise the helper uses the last matching Proton directory it encounters.

Installation prepares a complete copy before replacing the extension directory. Both helpers require Python 3.10+ to parse the manifest safely. Unknown install arguments and unsafe target paths are rejected. A per-extension directory lock prevents simultaneous helper operations; temporary copies live outside `extensions/`. A failed or interrupted operation restores the previous installation. SIGKILL or power loss cannot run cleanup: inspect the printed transaction paths or hidden `.<extension-id>.*` directories in the game root before removing a stale lock. Refresh it after edits; X4 enumerates real extension directories, so a symlink does not substitute for installation. Restart the game after installing or removing.

Publishing stages a separate copy inside the game's extensions directory. The repository keeps its readable extension id; `steam/workshop-id` holds the numeric Workshop id. The helper changes only the staged manifest and runs the interactive WorkshopTool. An exit trap restores the exact previous installation on success, error or a handled interrupt; if none existed, it removes the staged copy. On Linux it runs WorkshopTool through Proton and maps paths through drive Z. Workshop ids must be complete numeric ids, not strings from which digits can be extracted. Tests use a fake WorkshopTool and never upload anything.

## Release metadata

`content.xml` uses an integer version multiplied by 100 and an ISO release date. The date matches the corresponding released entry in `CHANGELOG.md`. Development changes belong under `Unreleased`; they do not advance the manifest's release version or date. An unreleased scaffold may retain its initial creation date until its first release. Keep existing extension ids stable.

## Mesh conversion

`soase_import.py` reads Ironclad's text mesh format, an indentation-nested key-value tree whose blocks repeat by name. It refuses binary meshes; convert those with ConvertX first. Sins uses X right, Y up and Z forward, so the converter maps `(x, y, z)` to `(-x, z, y)`: swapping the two axes alone would mirror the model, and negating X restores the handedness. This transform has determinant +1, so triangle winding is preserved, and the V coordinate is flipped from the DirectX convention OBJ does not use. Hardpoint orientations use a basis change (`T R T^-1`), so identity remains identity. Positions and normals use `T`.

`andromeda_import.py` imports the OBJ with `forward_axis="Y"` and `up_axis="Z"` so Blender's own axis conversion stays out of the way, then scales, centres, decimates and places connections. Keep both scripts self-contained: they are pasted into Blender's text editor, not installed as modules.

## Reproducing the pipeline

README.md documents the four stages end to end. What belongs here are the traps, which cost the most time to find:

- The exporter refuses any `.blend` whose path lacks the literal string `[assets]`, and reports the refusal only as an info message alongside a success message.
- `XUConverter.exe` is the tool the community guide calls "P1 Converter Local". It watches its source folder, so nothing converts until a file changes after it starts.
- Under Proton it exits silently with no output. Two DLLs are the cause: Proton's builtin `CONCRT140`
  lacks `?PPLParallelForEventGuid@Concurrency` and `mfc140` is missing. Plain Wine with
  `winetricks -q vcrun2022` runs it, and it then prints a usage line proving it takes arguments.
- Extension files are read off a case-sensitive filesystem. The localisation file must be
  `t/0001-l044.xml`, lowercase, as it is inside the game's own catalogues.
- Textures must be DXT5 with mipmaps, gzipped. Uncompressed dds is ignored without a word in the log.

## Exporting to xmf

The Egosoft Blender Mod Tools install four Blender 4.2 extensions and `XUConverter.exe`. Install the extensions from their zips with `blender --command extension install-file -r user_default -e <zip>`; the export operator is `ego_tools.export_data`, and it runs headless. The `.blend` path must contain the literal string `[assets]` or the operator refuses to run. Set `scene.classAttr` to `ship_xl`
before exporting.

Connection empties are tagged, not named: X4 reads the tags, and the names are free. The exporter takes tags from registered property groups, and falls back to an `extratags` string property, which is what a headless build uses because the add-on property groups are not registered under
`--factory-startup`.

`XUConverter.exe` takes a source and a destination folder as arguments and then watches the source. It does not run under Proton: Proton's builtin `CONCRT140` lacks symbols the converter imports, and
`mfc140` is missing entirely. Run it under plain Wine instead, in a container with the real Microsoft runtime installed by `winetricks -q vcrun2022`. Conversion triggers on file changes, so rewrite the
`.dae` after the watcher starts.

## Generator geometry

The axis convention is +Y forward and +Z up. Hull profile rows hold position, half-width, half-height and vertical offset as fractions of SHIP_LENGTH. Position 0 is the prow and 1 the stern. Separate superellipse exponents give the belly a flatter section than the deck. See README.md for generator use and parameters.

## Rebuilding and packaging the repaired hull

The source archive is not required if `~/x4mod/source/XMC.obj` and `XMC_points.json` already exist. The importer detects the legacy inverted OBJ faces using supplied normals, reverses them before decimation, clears stale custom normals and makes problematic smooth faces flat on simplified LODs. The source OBJ on disk is left unchanged. Fresh OBJ exports from `soase_import.py` already have the correct winding.

```bash
blender -b --python-exit-code 1 --python andromeda_import.py -- "/path/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend" --source ~/x4mod/source --export
```

Run XUConverter on that source folder using the Wine setup described in README. Prefer a fresh source/output directory and a fresh converter process for a release build: file changes made through Docker copying may not reach the Wine watcher. Check that the output timestamps correspond to the current export rather than relying on an older zero-error log. After conversion finishes with zero errors, copy its `p1data/andromeda` output to a local directory and package it:

```bash
python3 scripts/package_assets.py /path/p1data/andromeda --component "/path/p1[assets]/andromeda/ship_and_xl_cruiser_01.xml"
python3 scripts/check.py
```

Packaging takes the freshly exported component XML explicitly: the converter may retain an older component XML when only the DAE changes. It verifies the required mesh/physics outputs before copying. It preserves existing connection names, accepts the explicit Andromeda engine/weapon compatibility tags, ungrouped weapon slots, dedicated engine groups and the fourteen local shield additions, and rewrites the geometry path to the extension's installed path. It never copies the intermediate DAE into the extension.

## Existing saves and acceptance checks

`AndromedaBlueprint.GrantBlueprint` remains as an empty compatibility cue. The new instantiated `RecoverBlueprints` cue listens to the vanilla `md.Setup.Start` signal, which vanilla emits for new games and loaded saves. After one second it adds only missing blueprints. This handles a completed legacy cue without editing the save. Schema validation does not prove runtime behavior.

Before release, restart X4 and check an existing built Andromeda: hull appearance in the equipment preview and outside, turret/shield seating and orientation, engine choices, both main weapons, and all three custom blueprints. The new medium shield slots will need equipment on existing ships. Build a new ship, then save and reload to verify recovery does not repeat grants. Repeat blueprint availability on a new game. Check the debug log for Andromeda errors; unsigned-file messages are expected for a manual mod installation. Combat balance, authored recesses and a detailed hull texture remain separate work.

## Selectable exclusive equipment and hull appearance

`libraries/equipmentcompatibilities.xml` registers `andromeda`. Ship engine/weapon mounts and their component bindings use that tag without `standard` or `mandatory`. The custom lance component is a separate copy of the Ravager's geometry-free laser emitter, with the original Kha'ak beam macro and effects. The original vanilla weapon component is not patched. Emitter orientation is identity, as on the Ravager; its firing axis differs from a turret mounting normal.

The vanilla ship configuration menu treats weapons as individual slots, not turret/engine groups. Keep both weapon connections ungrouped. Compatibility and macro identities are tested locally; previously fitted equipment is not replaced in saves.

Shields use an explicit orthonormal frame: local Blender Z is the surface normal and local Y is ship-forward projected onto the mounting plane. This corresponds to the native shield mesh's longitudinal Z axis after X4 export and avoids the arbitrary roll of `to_track_quat` on sloped hull faces.

The hull uses base-game panel maps `gen_p2_hulltexture_02` shared by Hyperion, through the existing p1 shader, with a 120 m box UV projection and dark grey vertex tint. No Egosoft textures are redistributed. Run `python3 scripts/validate_extension.py --game "/path/to/X4 Foundations"` to also verify these external texture paths in the base-game catalogs. Run `blender -b --python-exit-code 1 --python scripts/check_blender.py -- "/path/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend"` to check the saved scene, longitudinal shields and emitted DAE.
