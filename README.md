# Andromeda Ascendant for X4: Foundations

<p align="center">
  <img src="extension/preview.jpg" alt="Andromeda Ascendant" width="512">
</p>

A fan mod that brings the Systems Commonwealth heavy cruiser **Andromeda Ascendant** into X4: Foundations 9.0 as a flyable XL ship.

**Status: it builds, it flies, and it looks wrong.** A modelled hull goes through the whole Egosoft toolchain to X4's own `.xmf`, the ship can be built at a player shipyard and flown, and its thirty-six turrets work. What it does not do is render correctly: the hull comes out red and partly see-through for reasons nobody has tracked down yet. See [Open](#open) for that and the rest, and
[The asset pipeline](#the-asset-pipeline) for how the conversion actually works — it is written down in full so nobody has to rediscover it.

The procedural generator [`andromeda_gen.py`](andromeda_gen.py) is kept as a blocking tool and for the axis conventions, but it no longer produces the shipped hull.

## Requirements

|                 |                                                                                                   |
|-----------------|---------------------------------------------------------------------------------------------------|
| Blender         | **4.2** — the Egosoft export tooling does not support newer versions, so do not "upgrade" to 4.3+ |
| X4: Foundations | 9.0 — no DLC required                                                                             |
| Python          | none separately — the script runs inside Blender's bundled interpreter                            |

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

Sins uses `X` right, `Y` up, `Z` forward. The converter maps `(x, y, z)` to `(-x, z, y)`: swapping the two axes alone would mirror the model, so negating `X` restores the handedness. Triangle winding is reversed to match and `V` is flipped out of the DirectX convention.

### 3. Blender scene

```bash
blender --background --python andromeda_import.py -- "<path>/p1[assets]/andromeda/ship_and_xl_cruiser_01.blend"
```

[`andromeda_import.py`](andromeda_import.py) builds the scene X4 expects: `part_main` plus
`part_main.LOD1` through `.LOD3` and a `part_main.wreck`, the UV channel renamed `uv1`, a `col` vertex colour attribute, and the connection empties. It scales the hull to `SHIP_LENGTH`, centres the origin and samples the hull surface to place turrets rather than trusting the source hardpoints.

Three things about connections are easy to get wrong and cost real time:

- **Names do not matter, tags do.** X4 reads the tags; the names are free. A turret is
  `turret medium standard missile hittable combat`, an engine `engine extralarge standard`, a shield
  `extralarge shield standard`. The role word alone is not enough — without a size the game offers no slot at all.
- **Orientation is the mounting normal.** A connection's local `+Y` points away from the hull, so a ventral mount carries a 180 degree flip. Without it every turret faces the same way.
- **Every connection needs a group.** Vanilla groups all of them, named by station:
  `group_front_up_left`, `group_back_down_mid` and so on. The equipment browser lists nothing for a connection with no group, even though a loadout preset can still fill it.

The Blender addon registers its tag and group properties as real object properties, which do not exist under `--factory-startup`. The build script writes an `extratags` string property and a `group_name`
custom property instead, and the export step copies `group_name` onto the addon's `groups` property before exporting.

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
`/materiallibrary`, using the `p1_complex_surface` shader — lowercase, no `.fx` suffix, whatever the community guide says. Thin surfaces need `blendmode="TWOSIDED"` or you see straight through them.

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

Issues and pull requests are welcome. The two open items worth the most are the red hull and the mission director cue, both described under [Open](#open) — they are the difference between a ship that looks and equips correctly and one that does not.

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

The `extension/` directories are empty placeholders for now, tracked with `.gitkeep` so the layout is visible.

## Status

### Done

- Ironclad text mesh parsed into OBJ with geometry, UVs, materials and hardpoints
- Axis, winding and texture-coordinate conversion into the X4 convention
- The whole Egosoft toolchain driven headless, from Blender scene to `.xmf`
- lod0-3, collision, wreck and Jolt physics meshes, converting with no errors
- Component XML with fifty-one tagged and grouped connections, generated rather than hand-written
- Six large and thirty medium turrets placed by sampling the hull surface, each oriented outward
- Ship macro, ware, localised text and index entries; the ship builds and flies
- Engines sunk into the hull so no engine model shows, only the exhaust

### Open

These are the things a contributor could pick up. The first two are the ones that matter.

- **The hull renders red, and partly see-through.** Not a missing material — a missing material gives magenta, and that was fixed long ago. The material resolves, the textures are valid DXT5 with mipmaps and load in other tools, `blendmode` is `TWOSIDED`, and the `col` vertex colour attribute is filled with neutral grey. Something else in `p1_complex_surface` is driving the colour and the transparency. Comparing against a vanilla ship material property by property is the obvious next step, and nobody has done it yet.
- **The mission director cue never fires.** `md/andromeda_blueprint.xml` holds a root cue with no conditions, which should run when the script is instantiated. A `debug_text` inside it never reaches the log on an existing save, so the blueprints are never granted — which is why the custom engine and main gun never appear for sale however correct their wares and index entries are. Either the cue needs a condition or a delay, or new MD scripts are only instantiated on a new game.
- **Turrets and shields sit on the hull rather than in it.** They are sunk a few metres, but the hull has no recesses for them because none were modelled. This one needs a modeller, not a script.
- **The hull has no detail texture.** The normal map from the source set is good and is used. The diffuse is nearly black where this hull's UVs land, and what looks like a self-illumination map is a team colour mask, so both were dropped in favour of flat grey. A proper hull texture is artist work.
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

Andromeda has no playable asset yet; publish only when the extension is ready.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, code style, validation and release conventions.

## Legal

The code in this repository is MIT licensed — see [`LICENSE`](LICENSE).

The hull mesh was modelled by **[grannyte](https://www.reddit.com/user/grannyte/)** and is used with their permission. It is not covered by the MIT licence above — see [Mesh source](#mesh-source).

This is a **non-commercial fan project**. Andromeda, the Andromeda Ascendant and all related names and designs belong to the rights holders of the series. X4: Foundations and its file formats belong to Egosoft GmbH. This project is not affiliated with, sponsored by or endorsed by either, and is not for sale.
