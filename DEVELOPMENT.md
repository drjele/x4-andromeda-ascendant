# Development

## Current handoff (2026-09-11)

Development is paused at the user's request. The ship builds and flies, but the latest attempt to make the four original custom turrets functional failed the user's in-game test. Preserve this snapshot as unfinished work for an X4 modeller/asset contributor. Do not describe the custom turrets as working or merely awaiting their first test. The exact visible symptom and root cause were not isolated, and no post-test log analysis has established a cause.

The desired result is the original four twin-barrel designs operating as turrets. Their original geometry was extracted into an experimental shared component; only the projectile/aiming parameters come from the Argon L beam turret. The user questioned whether ordinary L models had replaced them in-game, so confirm both appearance and function rather than relying on the source geometry alone. A decorative-original-socket fallback is acceptable if articulation cannot be made functional, but is not implemented here. This pause makes no further mesh, rig or loadout changes.

Known art work: repetitive 120 m box-projected hull panels, UV seams and material appearance, and standard turret/shield bases that do not conform to the rounded hull. Surface-normal alignment and numerical sinking are insufficient to solve the latter. Assistance is needed with Blender/X4 modelling, rigging/export, collision and material authoring; the failure has not been proven to be exclusively graphical.

### Evidence and files for the next contributor

- `c3025ab` is the checkpoint before extraction of the original turret assemblies. It records the improved hull/equipment state, not a fully accepted release.
- `andromeda_import.py` removes the four assemblies before generating hull LODs. `andromeda_turrets.py` builds their shared experimental socket/yaw/pitch model. The shipped turret component and macro are under `extension/assets/props/weaponsystems/energy/`; new ship connections are `con_turret_integrated_01` through `_04`.
- The source has 11,912 triangles. Extraction removes 1,016 triangles (812 source vertices), leaving 10,896 hull LOD0 triangles. The four assemblies match after their original transforms in the offline geometry check; that does not establish correct runtime mounting or articulation.
- On the maintainer's machine, source files are `~/x4mod/source/XMC.obj`, `XMC.mtl` and `XMC_points.json`. Current scene/export files are in `~/x4mod/repair-2026-09-11-turrets/p1[assets]/andromeda/` and `p1[assets]/turrets/` under that same directory; converted outputs are in its `converted/` directory. The earlier pre-extraction scenes are in `~/x4mod/repair-2026-09-11/`. These local files are not bundled in the Git repository; another contributor needs access to the source assets under the mesh permission described in README.md.
- User screenshots `Screenshot from 2026-09-11 07-17-00.png` and `Screenshot from 2026-09-11 07-54-16.png` in `~/Pictures/Screenshots/` document earlier rendering/equipment iterations. They predate the final custom-turret test and do not demonstrate its behavior.
- Last offline validation: 28 regression tests passed, Blender hull/rig checks passed, and XUConverter processed four input files with zero reported errors. The installed extension was verified against all 53 repository asset files by SHA-256. None of these supersedes the failed in-game acceptance.
- X4 base-game `libraries/defaults.xml` already supplies `defencenpc` for class `ship_xl`. Its absence from the explicit ship component XML is not evidence that the ship lacks turret control.

### Resume with an in-game diagnosis

Use Steam launch options `-debug all -logfile debug.log`, restart X4, and reproduce with one of the four custom turrets equipped and enabled. On the maintainer's Steam Snap installation the log is expected at `~/snap/steam/common/.config/EgoSoft/X4/23682333/debug.log`. Capture the actual equipped component, appearance, aiming, firing and relevant errors. Verify the exported parent/IK chain, muzzle transforms and collision against a known-working turret before changing the model. Preserve the existing ship/connection identifiers and the user's saves.

Useful references reviewed: [Modding Ressource for S-Class Turrets](https://www.nexusmods.com/x4foundations/mods/1185) and [S Turrets Extension](https://www.nexusmods.com/x4foundations/mods/1233). They provide attachment examples, not a demonstrated fix for this XL ship; neither is a dependency of this mod.

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

`andromeda_import.py` imports the OBJ with `forward_axis="Y"` and `up_axis="Z"` so Blender's own axis conversion stays out of the way, then scales, centres, decimates and places connections. Keep `andromeda_import.py` and `andromeda_turrets.py` together; run their files through Blender so the shared extraction module can be resolved.

## Reproducing the pipeline

README.md documents the four stages end to end. What belongs here are the traps, which cost the most time to find:

- The exporter refuses any `.blend` whose path lacks the literal string `[assets]`, and reports the refusal only as an info message alongside a success message.
- `XUConverter.exe` is the tool the community guide calls "P1 Converter Local". It processes the initial source files and then watches the folder; use a fresh process and fresh input/output directories to avoid stale conversions.
- Under the tested Proton setup it exited silently with no output. Two DLLs are the cause: Proton's builtin `CONCRT140`
  lacks `?PPLParallelForEventGuid@Concurrency` and `mfc140` is missing. Plain Wine with
  `winetricks -q vcrun2022` runs it, and it then prints a usage line proving it takes arguments.
- Extension files are read off a case-sensitive filesystem. The localisation file must be
  `t/0001-l044.xml`, lowercase, as it is inside the game's own catalogues.
- This pipeline uses gzipped DXT5 textures with mipmaps. Earlier uncompressed DDS experiments did not render correctly; other supported X4 texture formats were not exhaustively tested.

## Exporting to xmf

The Egosoft Blender Mod Tools install four Blender 4.2 extensions and `XUConverter.exe`. Install the extensions from their zips with `blender --command extension install-file -r user_default -e <zip>`; the export operator is `ego_tools.export_data`, and it runs headless. The `.blend` path must contain the literal string `[assets]` or the operator refuses to run. Set `scene.classAttr` to `ship_xl`
before exporting.

Tags describe connection roles; names are identifiers used by macro bindings and saves and must remain stable. The importer uses `extratags` on connection empties and registered properties for groups and mesh IK tags. Retain the enabled Egosoft addons when clearing a headless scene; do not reset to factory settings before exporting.

`XUConverter.exe` takes a source and a destination folder as arguments and then watches the source. The tested Proton setup could not run it: Proton's builtin `CONCRT140` lacks symbols the converter imports, and
`mfc140` is missing entirely. Run it under plain Wine instead, in a container with the real Microsoft runtime installed by `winetricks -q vcrun2022`. The initial scan converts existing inputs. Later file changes may trigger another conversion, but Docker copies did not reliably reach the Wine watcher; prefer fresh directories and a fresh process.

## Generator geometry

This section describes the legacy `andromeda_gen.py`, not the shipped imported model. The axis convention is +Y forward and +Z up. Hull profile rows hold position, half-width, half-height and vertical offset as fractions of SHIP_LENGTH. Position 0 is the prow and 1 the stern. Separate superellipse exponents give the belly a flatter section than the deck. See README.md for generator use and parameters.

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

Packaging takes the freshly exported component XML explicitly: the converter may retain an older component XML when only the DAE changes. It verifies the required mesh/physics outputs before copying. It preserves existing connection names, accepts the explicit Andromeda engine/weapon compatibility tags, ungrouped weapon slots, dedicated engine groups, the fourteen local shield additions and the four experimental custom-turret additions, and rewrites the geometry path to the extension's installed path. It never copies the intermediate DAE into the extension.

## Existing saves and acceptance checks

`AndromedaBlueprint.GrantBlueprint` remains as an empty compatibility cue. The new instantiated `RecoverBlueprints` cue listens to the vanilla `md.Setup.Start` signal, which vanilla emits for new games and loaded saves. After one second it adds only missing blueprints. This handles a completed legacy cue without editing the save. Schema validation does not prove runtime behavior.

Before release, restart X4 and check an existing built Andromeda: hull appearance in the equipment preview and outside, turret/shield seating and orientation, engine choices, both main weapons, and all four custom blueprints. The new medium shield slots will need equipment on existing ships. Build a new ship, then save and reload to verify recovery does not repeat grants. Repeat blueprint availability on a new game. Check the debug log for Andromeda errors; unsigned-file messages are expected for a manual mod installation. Combat balance, authored recesses and a detailed hull texture remain separate work.

## Selectable exclusive equipment and hull appearance

`libraries/equipmentcompatibilities.xml` registers `andromeda`. Ship engine/weapon mounts and their component bindings use that tag without `standard` or `mandatory`. The custom lance component is a separate copy of the Ravager's geometry-free laser emitter, with the original Kha'ak beam macro and effects. The original vanilla weapon component is not patched. Emitter orientation is identity, as on the Ravager; its firing axis differs from a turret mounting normal.

The vanilla ship configuration menu treats weapons as individual slots, not turret/engine groups. Keep both weapon connections ungrouped. Compatibility and macro identities are tested locally; previously fitted equipment is not replaced in saves.

Shields use an explicit orthonormal frame: local Blender Z is the surface normal and local Y is ship-forward projected onto the mounting plane. This corresponds to the native shield mesh's longitudinal Z axis after X4 export and avoids the arbitrary roll of `to_track_quat` on sloped hull faces.

The hull uses base-game panel maps `gen_p2_hulltexture_02` shared by Hyperion, through the existing p1 shader, with a 120 m box UV projection and dark grey vertex tint. No Egosoft textures are redistributed. Run `python3 scripts/validate_extension.py --game "/path/to/X4 Foundations"` to also verify these external texture paths in the base-game catalogs. Run `blender -b --python-exit-code 1 --python scripts/check_blender.py -- "/path/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend"` to check the saved scene, longitudinal shields and emitted DAE.


### Original integrated twin turrets — experimental, failed in-game

The four original `Weapon-1` stations each contain five disconnected mesh islands: a socket, two body halves and two barrels. `andromeda_turrets.py` identifies their topology and locations before normalization, removes those complete islands from the hull, and builds a common turret model. All four assemblies are geometrically congruent after their original roll transforms; the Blender integration check verifies this within 0.001 source units. The offline transforms preserve their original socket geometry; the actual in-game mounting still needs diagnosis.

The component has a fixed socket, a yaw part with `iklink` and `rotation_y`, and a pitch part with `iklink` and `rotation_x`. Both laser connections follow the pitch part and extend just beyond the barrel tips. It uses the base-game Argon L beam bullet and aiming properties. Four new dedicated `andromeda` L slots share the corresponding shield-protected side groups; all previous slot identities remain. Existing ships require manual equipment at a shipyard. No save migration is performed.

Export the hull as above and the turret separately, then run both through XUConverter:

```sh
blender -b --python-exit-code 1 --python andromeda_turrets.py -- "/path/p1[assets]/turrets/turret_and_l_twin_01_mk1.blend" --export
python3 scripts/package_turret.py /path/p1data/turrets --component "/path/p1[assets]/turrets/turret_and_l_twin_01_mk1.xml"
blender -b --python-exit-code 1 --python scripts/check_turrets_blender.py -- "/path/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend" "/path/p1[assets]/turrets/turret_and_l_twin_01_mk1.blend"
```

The latest in-game test failed. Before calling this implementation functional, diagnose that failure and verify all four purchase slots, tracking and fire from both barrels, destruction/repair, and save/reload. Offline geometry and XML tests cannot establish combat behavior. Repetitive hull panel mapping and the seating of standard faction equipment on curved surfaces still need art work.
