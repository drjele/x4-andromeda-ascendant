# Andromeda Ascendant for X4: Foundations

<p align="center">
  <img src="extension/preview.jpg" alt="Andromeda Ascendant" width="512">
</p>

A fan mod that brings the Systems Commonwealth heavy cruiser **Andromeda Ascendant** into X4: Foundations 9.0 as a flyable XL ship.

**Status: buildable and flyable; rendering and equipment fixes await an in-game confirmation.**
The hull passes the Egosoft conversion pipeline, with six large and thirty medium turrets.
The current repair corrects reversed geometry, LOD shading, surface placement and equipment groups,
and recovers missing blueprints on existing saves. Existing ship and equipment identifiers are retained.
See [Open](#open) for the remaining visual and gameplay checks.

The procedural generator [`andromeda_gen.py`](andromeda_gen.py) is kept as a blocking tool and for the axis conventions, but it no longer produces the shipped hull.

## Requirements

|                 |                                                                                                   |
|-----------------|---------------------------------------------------------------------------------------------------|
| Blender         | **4.2** — the Egosoft export tooling does not support newer versions, so do not "upgrade" to 4.3+ |
| X4: Foundations | 9.0 — no DLC required                                                                             |
| Python          | Python 3.10+ for conversion, install/publish helpers and checks; Blender scripts use its bundled interpreter |

## Install

```bash
./install.sh
```

The helper copies `extension/` into the game's `extensions/<extension-id>`
directory, using the id in `extension/content.xml`. It searches the usual Steam layouts and additional library folders. To choose an installation:

```bash
X4_PATH="/path/to/X4 Foundations" ./install.sh
```

Restart X4 after installing or updating. To remove the manual installation:

```bash
./install.sh --uninstall
```

**The extension installs a buildable ship with its own hull.** The Andromeda geometry is exported to X4's own `.xmf` format through the official Egosoft toolchain, with LOD0-3, collision, wreck and Jolt physics meshes.

Restart X4 after installing. The ship is **player-only**: the ware names the player as its sole owner, so no faction builds or sells it and NPC fleets never fill up with Andromedas. The blueprint is granted by [`extension/md/andromeda_blueprint.xml`](extension/md/andromeda_blueprint.xml), so it can be built at a player shipyard and nowhere else.

## Mesh source

The hull was modelled by **[grannyte](https://www.reddit.com/user/grannyte/)** and is used here **with their permission**. The credit stays in this file, in the extension manifest and in the Workshop description. The copy this project works from was distributed inside the Andromeda mod for Sins of a Solar Empire on [ModDB](https://www.moddb.com/mods/andromedamod).

The archive ships `Mesh/XMC.mesh` — the XMC Glorious Heritage class heavy cruiser — in Ironclad's **text** mesh format, so no binary conversion is needed:

|                |                                                                    |
|----------------|--------------------------------------------------------------------|
| Geometry       | 9,853 vertices, 11,912 triangles, 2 materials                      |
| Hardpoints     | 23 points: `Weapon-0` ×6, `Weapon-1` ×4, `Hangar` ×2, plus effects |
| Source extents | 795 × 1368 × 358 units, bow along `+Z`, up along `+Y`              |
| Textures       | `stamp4.DDS`, `stamp4dm2.DDS` (emissive), `stamp4NRM.dds` (normal) |

The archive is not redistributed here and is excluded by `.gitignore`. Download it yourself from the ModDB page above.

## The asset pipeline

Getting the mesh from its Sins format into something X4 loads takes four stages. Every stage runs headless, so the whole chain is scriptable and repeatable.

### 1. Tooling

|                                     |                                                                                                                                       |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Blender **4.2**                     | The Egosoft extensions do not support 4.3+. Use the official build, not a distribution package.                                       |
| Egosoft Blender Mod Tools **0.7.0** | From the [bonus material page](https://www.egosoft.com/download/x4/bonus_en.php). Requires an X game registered on the forum account. |
| `innoextract`                       | The tools ship as an Inno Setup installer. Extracting it beats running it.                                                            |
| Docker, or a Windows box            | For the converter — see stage 3.                                                                                                      |

The installer holds four Blender extensions, `VHACD.exe`, `XUConverter.exe` and, importantly, a
`readme.txt` that is otherwise only visible during installation. Extract with
`innoextract -e -d <dir> EgosoftBlenderModTools_v0.7.0.exe`, then install the extensions:

```bash
for z in ego_tools groups io_scene_dae vhacd; do
    blender --command extension install-file -r user_default -e <dir>/userdocs/Egosoft/Extensions/$z.zip
done
```

Copy `Blender_Properties.xml` and `material_presets.xml` to `~/Documents/Blender/`. The first holds the full list of connection tags X4 understands and is worth reading.

### 2. Sins mesh to OBJ

```bash
python3 soase_import.py "<archive>/Mesh/XMC.mesh" -o ~/x4mod/source
```

[`soase_import.py`](soase_import.py) parses Ironclad's text mesh format — an indentation-nested key-value tree — and writes `XMC.obj`, `XMC.mtl` and `XMC_points.json`. It refuses binary meshes; convert those with ConvertX first.

Sins uses `X` right, `Y` up, `Z` forward. The converter maps `(x, y, z)` to `(-x, z, y)`: swapping the two axes alone would mirror the model, so negating `X` restores the handedness. This transform preserves handedness, so triangle winding is preserved too. `V` is flipped out of the DirectX convention. The converter rejects inconsistent winding, invalid indices and degenerate faces before writing output.

### 3. Blender scene

```bash
blender --background --python-exit-code 1 --python andromeda_import.py -- "<path>/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend" --source ~/x4mod/source --export
```

[`andromeda_import.py`](andromeda_import.py) builds the scene X4 expects: `part_main` plus
`part_main.LOD1` through `.LOD3` and a `part_main.wreck`, the UV channel renamed `uv1`, a `col` vertex colour attribute, and the connection empties. It scales the hull to `SHIP_LENGTH`, centres the origin and intersects the hull triangles to place turrets and shields. Stable mount names preserve existing ships. Legacy OBJ winding is repaired against its supplied normals before creating the LODs. If a mount falls outside the surface, the importer searches within 3.5% of ship length for the nearest face facing the correct hemisphere; otherwise the build fails instead of dropping the slot.

Three things about connections are easy to get wrong and cost real time:

- **Names do not matter, tags do.** X4 reads the tags; the names are free. A turret is
  `turret medium standard missile hittable combat`, an Andromeda engine `engine extralarge andromeda`, a shield
  `extralarge shield standard`. The role word alone is not enough — without a size the game offers no slot at all.
- **Orientation is the mounting normal.** In exported X4 coordinates a connection's local `+Y` points away from the hull. In the Blender scene this is local `+Z`; mount rotations align that axis with the sampled surface normal.
- **Turrets, engines and local shields need groups.** Vanilla groups all of them, named by station:
  `group_front_up_left`, `group_back_down_mid` and so on. Engine groups must be separate from turret groups, and turret/engine groups have local shields. Main weapons must stay ungrouped for the standard equipment menu; both use the same empty group. Their mounts are selectable, not tagged `mandatory`. Fourteen medium shield slots protect these groups in addition to the four existing XL shield slots.

The build script retains loaded addons when clearing the scene. It writes `extratags` and `group_name`, and copies the latter onto the addon's registered `groups` property before export. Use `--export` with the Egosoft addons enabled. The script exits with an error if either the DAE or component XML is missing.

### 4. Export and convert

The Egosoft exporter runs headless. The `.blend` path must contain the literal string `[assets]` or the operator refuses, and `scene.classAttr` has to be set first:

```python
bpy.context.scene.classAttr = "ship_xl"
bpy.ops.ego_tools.export_data(write_xml=True)
```

That writes a `.dae` and the component `.xml`. `XUConverter.exe` then turns the `.dae` into X4's own formats — lod meshes, collision, Jolt physics hulls. It takes a source and a destination folder and then watches the source, so conversion triggers on a file change; rewrite the `.dae` after it starts. The folder names `p1[assets]` and `p1data` are fixed, because the converter derives the destination by substituting one for the other.

**The converter does not run under Proton.** Proton's builtin `CONCRT140` is missing symbols it imports and `mfc140` is absent entirely, so it exits silently. Plain Wine with the real Microsoft runtime works:

```bash
docker run -d --name x4conv --entrypoint /bin/bash scottyhardy/docker-wine:latest -c 'sleep infinity'
docker exec x4conv bash -c 'WINEPREFIX=/root/.wine wineboot -i && xvfb-run -a winetricks -q -f vcrun2022'
```

Then run `XUConverter.exe "Z:\x4mod\p1[assets]" "Z:\x4mod\p1data"` inside the container.

### Textures

X4 reads **DXT5 with a full mipmap chain**, gzipped, referenced from the material library without an extension. Uncompressed dds is silently ignored. The material itself goes in a diff against
`/materiallibrary`, using the `p1_complex_surface` shader — lowercase, no `.fx` suffix, whatever the community guide says. The current hull retains `blendmode="TWOSIDED"` for thin source surfaces. It now references the base-game `gen_p2_hulltexture_02` diffuse, normal, smoothness and metal maps also used by Hyperion. Hull UVs use a 120 m box projection, with dark grey vertex colour and a zero paint mask. This adapts the panel texture to Andromeda; it does not copy Hyperion's mesh or UV layout and adds no DLC requirement. The old source DDS files remain diagnostic assets.

## Running the generator

1. Open Blender 4.2.
2. **Scripting** tab → **New**.
3. Paste the contents of [`andromeda_gen.py`](andromeda_gen.py).
4. **Run Script**.

Everything lands in a collection named `andromeda_ascendant`. Rerunning wipes that collection first, so tweak-and-rerun iteration is safe — you never accumulate duplicates.

The axis convention is **+Y forward, +Z up**, matching the hard-point export settings X4 expects. The console prints a one-line summary on every run:

```
andromeda: 1300 m, 449 faces at lod0
```

## What it produces

| Object                              | What it is                                                                                      |
|-------------------------------------|-------------------------------------------------------------------------------------------------|
| `andromeda_lod0` … `andromeda_lod3` | Four detail levels, each a single joined mesh (hull + both nacelles, plus fins on LOD0/LOD1)    |
| `andromeda_collision`               | Convex hull of LOD0 with a `DECIMATE` modifier at ratio `0.4`                                   |
| `con_*` empties                     | Connection points for engines, turrets, shields, dock and cockpit, placed at computed positions |

## Parameters

Two knobs do most of the shaping. Both live at the top of the script.

### `SHIP_LENGTH`

```python
SHIP_LENGTH = 1300.0
```

Overall length in metres, bow tip to stern plane. **Every other dimension in the script is a fraction of it**, so changing this one number rescales the entire ship — hull, nacelles, fins and hard-point positions — coherently. 1300 m is the figure quoted for the ship in the series.

### `HULL_PROFILE`

The shape table, and the thing you actually iterate on:

```python
HULL_PROFILE = [
    # (t,   half_width, half_height, vertical_offset)
    (0.000, 0.0000, 0.0000, 0.000),
    (0.040, 0.0066, 0.0060, -0.002),
    ...(1.000, 0.0523, 0.0390, 0.000),
]
```

Each row is one cross-section station along the ship:

| Field             | Meaning                                                                                                                  |
|-------------------|--------------------------------------------------------------------------------------------------------------------------|
| `t`               | Position along the hull. `0.0` is the tip of the prow, `1.0` is the stern plane. Must increase monotonically.            |
| `half_width`      | Half the beam at that station, as a fraction of `SHIP_LENGTH`                                                            |
| `half_height`     | Half the height at that station, as a fraction of `SHIP_LENGTH`                                                          |
| `vertical_offset` | How far the section's centre sits above/below the centreline, as a fraction of `SHIP_LENGTH`. Negative droops the belly. |

The rows are lofted into a closed surface: the first row collapses to a single apex vertex (the prow), consecutive rows are bridged with quads, and the last row is capped with an n-gon. The default table widens to its maximum beam at `t = 0.700` and tapers back toward the stern.

Add rows where you want more control, delete rows where the shape is doing nothing interesting. Tune, rerun, look, repeat.

### Secondary knobs

| Parameter                                                                             | Effect                                                                                                                                    |
|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `TOP_EXPONENT` / `BOTTOM_EXPONENT`                                                    | Superellipse exponents for each cross-section. Higher is boxier. They are split (`2.4` / `3.4`) so the belly reads flatter than the deck. |
| `NACELLE_START_T`, `NACELLE_LATERAL`, `NACELLE_HALF_WIDTH`, `NACELLE_HALF_HEIGHT`     | Where the engine nacelles begin, how far outboard they sit, and their cross-section                                                       |
| `FIN_START_T`, `FIN_END_T`, `FIN_HEIGHT`, `FIN_SWEEP`, `FIN_LATERAL`, `FIN_THICKNESS` | Root chord, height, sweep-back and thickness of the dorsal fins                                                                           |
| `RING_SEGMENTS`, `LOD_RING_SEGMENTS`, `LOD_PROFILE_STRIDE`                            | Tessellation per LOD (see below)                                                                                                          |
| `TURRET_ROWS_DORSAL`, `TURRET_ROWS_VENTRAL`, `TURRET_SPAN_T`                          | How many turret hard-points per side and over what stretch of the hull they spread                                                        |

## LODs

`LOD_RING_SEGMENTS` sets how many segments each cross-section ring is divided into;
`LOD_PROFILE_STRIDE` samples every N-th row out of `HULL_PROFILE`.

| LOD | Ring segments | Profile stride | Fins | Faces |
|-----|---------------|----------------|------|-------|
| 0   | 24            | 1              | yes  | 449   |
| 1   | 16            | 1              | yes  | 305   |
| 2   | 10            | 2              | no   | 135   |
| 3   | 6             | 3              | no   | 77    |

Face counts are for the default parameters and change as soon as you edit `HULL_PROFILE`. The script prints the real LOD0 count on every run, so you can always check.

These counts are deliberately tiny — this is a blocking pass, not a finished asset. A capital ship in X4 carries far more geometry at LOD0.

## Connection points

The script places empties (`ARROWS` display) at positions derived from the hull profile, so they stay on the surface when you reshape it.

| Name                                | Count | Placement                                                                                                               |
|-------------------------------------|-------|-------------------------------------------------------------------------------------------------------------------------|
| `con_engine_01`, `con_engine_02`    | 2     | On the nacelle centrelines, at the stern plane                                                                          |
| `con_turret_001` … `con_turret_008` | 8     | 4 dorsal (odd) + 4 ventral (even), interleaved, spread over `t` 0.300 → 0.880, snapped to the interpolated hull surface |
| `con_shield_01` … `con_shield_04`   | 4     | On the centreline at `t` 0.400, 0.560, 0.720, 0.860                                                                     |
| `con_dock_01`                       | 1     | Ventral, `t` 0.660                                                                                                      |
| `con_cockpit`                       | 1     | Dorsal, `t` 0.180                                                                                                       |

These names come from the generator and predate the real pipeline. X4 does not care about connection names at all — it reads tags and groups. See [The asset pipeline](#the-asset-pipeline) for the rules that actually apply.

## Help wanted

Issues and pull requests are welcome. In-game confirmation of rendering, existing-save blueprint recovery and equipment configuration is especially useful. See [Open](#open).

If you know the X4 asset pipeline, the section on it above is written down precisely so nobody has to rediscover it: the tag and group rules, the orientation convention, the texture format, and why the converter needs Wine rather than Proton. Corrections to any of that are as useful as code.

## Structure

| Path                                                                | Description                                                                                       |
|---------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| [`soase_import.py`](soase_import.py)                                | Sins text mesh to OBJ converter. A tool, not content.                                             |
| [`andromeda_import.py`](andromeda_import.py)                        | Blender import that normalises the converted hull and places connections. A tool.                 |
| [`andromeda_gen.py`](andromeda_gen.py)                              | The procedural hull generator, kept for blocking. A tool, not content.                            |
| [`extension/`](extension)                                           | The X4 extension itself. Copy into `X4 Foundations/extensions/andromeda_ascendant`.               |
| [`extension/content.xml`](extension/content.xml)                    | Mod manifest: id, name, version. DLC dependencies get declared here if any turn out to be needed. |
| [`extension/index/`](extension/index)                               | Component and macro index files                                                                   |
| [`extension/assets/units/size_xl/`](extension/assets/units/size_xl) | The XL ship asset — component, macro and mesh data                                                |
| [`extension/libraries/`](extension/libraries)                       | Wares and related library definitions                                                             |
| [`extension/t/`](extension/t)                                       | Localised text files                                                                              |
| [`extension/md/`](extension/md)                                     | Mission director scripts                                                                          |

The `extension/` directory contains the shipped XML, meshes, physics and textures; `.gitkeep` files are remnants of the initial scaffold.

## Status

### Done

- Ironclad text mesh parsed into OBJ with geometry, UVs, materials and hardpoints
- Axis, winding and texture-coordinate conversion into the X4 convention
- The whole Egosoft toolchain driven headless, from Blender scene to `.xmf`
- lod0-3, collision, wreck and Jolt physics meshes, converting with no errors
- Component XML generated from stable mount definitions, with protected equipment groups
- Six large and thirty medium turrets placed on hull triangles and aligned to their surface normals
- Ship macro, ware, localised text and index entries; the ship builds and flies
- Engines sunk into the hull so no engine model shows, only the exhaust

### Open

- **Visual confirmation is pending.** Earlier builds rendered red and partly see-through. All 11,912 LOD0 triangles opposed their supplied normals; the importer now repairs this, fixes LOD shading and uses darker panel textures shared with Hyperion, with no paint mask. Rebuilt XMF assets pass conversion, but the equipment preview and exterior still need comparison in X4.
- **Existing-save recovery needs an in-game check.** The old `GrantBlueprint` cue was already complete in an inspected save, which contained only the ship blueprint. `RecoverBlueprints` listens to `md.Setup.Start` on new games and loads, adding only missing ship, engine and weapon blueprints. The old cue name is retained for compatibility.
- **Equipment groups have been repaired.** Engines now use separate groups, main weapons are ungrouped and selectable, and fourteen new medium shield slots protect turret/engine groups. Existing connections keep their names. Engine and weapon tags now require the registered `Andromeda` compatibility type, so only the custom Slipstream Drive and Ravager-derived Point Singularity Projector can be newly equipped. Newly added shield slots start unequipped on existing ships; equip them at a player shipyard.

- **Turrets and shields sit on the hull rather than in it.** They are sunk a few metres, but the hull has no recesses for them because none were modelled. This one needs a modeller, not a script.
- **The hull texture is adapted, not authored for this ship.** Hyperion's shared base-game panel maps now use a box projection on Andromeda. A dedicated UV layout, seam cleanup and bespoke livery remain artist work.
- **Borrowed sub-macros.** The bridge and cargo bay bind Argon macros, so the interior is Argon.
- **Balance is unvalidated.** 2700 m, 392k hull, thirty-six turrets. Nobody has fought with it.

## Publishing to the Steam Workshop

Install **X Tools** (Steam app 282160) and keep Steam running and logged in with an account that owns X4. On Linux, install Proton as well; on Windows, run the helper from Git Bash, MSYS or Cygwin.

```bash
./publish.sh publish
./publish.sh update "what changed"
```

Use `publish` once, then `update` with a change note. `X4_PATH`,
`X_TOOLS_PATH` and `PROTON_PATH` override automatic discovery. The staging location must contain an `extensions` directory.

The first upload records the numeric id in `steam/workshop-id`; retain that file for future updates. The readable id in the repository's `content.xml`
stays unchanged. After publishing, open the printed Workshop URL, complete any required Steam agreement and choose the item's visibility. Avoid keeping both the manual installation and a subscription to the same mod enabled.

Update the manifest version and release date together with `CHANGELOG.md`
when releasing. See [Development](DEVELOPMENT.md) for staging, platform and release conventions.

Complete the in-game acceptance checks before publishing a release.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, code style, validation and release conventions.

## Legal

The code in this repository is MIT licensed — see [`LICENSE`](LICENSE).

The hull mesh was modelled by **[grannyte](https://www.reddit.com/user/grannyte/)** and is used with their permission. It is not covered by the MIT licence above — see [Mesh source](#mesh-source).

This is a **non-commercial fan project**. Andromeda, the Andromeda Ascendant and all related names and designs belong to the rights holders of the series. X4: Foundations and its file formats belong to Egosoft GmbH. This project is not affiliated with, sponsored by or endorsed by either, and is not for sale.

### Equipment update on existing ships

After installing the equipment fix, restart X4 and start a fresh ship configuration. Main weapons should appear in the left-hand weapon category as Point Singularity Projectors, and engine choices should contain only Slipstream Drives. Old ships and saved loadouts may still retain their previously fitted ATF weapons or faction engines; replace those at a player shipyard rather than expecting the mod to rewrite a save. Shield length axes are aligned to the ship's forward direction projected onto the hull, including ventral mounts.
