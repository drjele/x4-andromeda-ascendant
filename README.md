# Andromeda Ascendant for X4: Foundations

<p align="center">
  <img src="extension/preview.jpg" alt="Andromeda Ascendant" width="512">
</p>

A fan mod that brings the Systems Commonwealth heavy cruiser **Andromeda Ascendant** into X4: Foundations 9.0 as a flyable XL ship.

**Status: early. Nothing has been loaded by the game yet.** The hull is now a real modelled mesh
rather than a procedural loft: [`soase_import.py`](soase_import.py) converts the Andromeda Ascendant
from the [Sins of a Solar Empire Andromeda Mod](#mesh-source), and
[`andromeda_import.py`](andromeda_import.py) normalises it to X4 axes, scale and connection points.
Nothing has been exported to XMF. See [Status](#status) for the honest split, and
[Help wanted](#help-wanted) if you know the X4 asset pipeline.

I write the XML side. The procedural generator [`andromeda_gen.py`](andromeda_gen.py) is kept as a
blocking tool and as the source of the axis and naming conventions the import mirrors.

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

**The extension installs a buildable ship with its own hull.** The Andromeda geometry is exported to
X4's own `.xmf` format through the official Egosoft toolchain, with LOD0-3, collision, wreck and Jolt
physics meshes.

Restart X4 after installing. The blueprint is granted by [`extension/md/andromeda_blueprint.xml`](extension/md/andromeda_blueprint.xml),
so the ship can be built at a player shipyard, and bought at Argon and Antigone yards. It needs the
capital ship licence, like any other XL hull.

## Mesh source

The hull comes from the **SOASE Andromeda Mod** for Sins of a Solar Empire, by **CKYRules**, published
on [ModDB](https://www.moddb.com/mods/andromedamod) in 2011. It is used here **with the author's
permission**, and the credit stays in this file, in the extension manifest and in the Workshop
description.

The archive ships `Mesh/XMC.mesh` — the XMC Glorious Heritage class heavy cruiser — in Ironclad's
**text** mesh format, so no binary conversion is needed:

| | |
|-----------------|---------------------------------------------------------------------|
| Geometry        | 9,853 vertices, 11,912 triangles, 2 materials                       |
| Hardpoints      | 23 points: `Weapon-0` ×6, `Weapon-1` ×4, `Hangar` ×2, plus effects |
| Source extents  | 795 × 1368 × 358 units, bow along `+Z`, up along `+Y`               |
| Textures        | `stamp4.DDS`, `stamp4dm2.DDS` (emissive), `stamp4NRM.dds` (normal)  |

The archive is not redistributed here and is excluded by `.gitignore`. Download it yourself from the
ModDB page above.

## Converting the mesh

```bash
python3 soase_import.py "<archive>/Mesh/XMC.mesh" -o ~/andromeda
```

This writes `XMC.obj`, `XMC.mtl` and `XMC_points.json`, converting the Sins axes (`X` right, `Y` up,
`Z` forward) into the `+Y` forward, `+Z` up convention X4 expects, flipping `X` to preserve winding
and flipping `V` to the OpenGL texture convention. It prints geometry counts and extents on every run.

## Importing into Blender

1. Open Blender 4.2.
2. **Scripting** tab → **New**.
3. Paste the contents of [`andromeda_import.py`](andromeda_import.py).
4. Set `SOURCE_DIRECTORY` to the directory you converted into.
5. **Run Script**.

Everything lands in the `andromeda_ascendant` collection, and rerunning wipes it first. The script
scales the hull so bow-to-stern is `SHIP_LENGTH`, centres the origin, decimates the LOD chain, derives
a convex-hull collision mesh and places the `con_*` empties. The console prints:

```
andromeda: 1300 m, scale 0.9502, lod0 11912, lod1 6551, lod2 2978, lod3 1191
andromeda: collision 384 faces, 10 turrets, 2 docks
```

| Empty                               | Count | Derived from                                                         |
|-------------------------------------|-------|------------------------------------------------------------------------|
| `con_turret_001` … `con_turret_010` | 10    | The `Weapon-0` and `Weapon-1` hardpoints, ordered bow to stern         |
| `con_dock_01`, `con_dock_02`        | 2     | The `Hangar` hardpoints                                                |
| `con_engine_01`, `con_engine_02`    | 2     | Computed — the source mesh carries no engine hardpoint                |

The source hardpoints all carry an identity orientation, so orientation still has to be authored.

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

**These names are a working guess and have not been validated against what X4's component XML expects.** Verifying them is one of the open items below.

## Help wanted

I am posting this looking for someone who knows Blender and, ideally, the X4 asset pipeline. Concretely, the useful contributions are:

1. Authoring X4 materials and textures for the hull — it currently renders untextured.
2. Judging whether the 2009 Sins textures are worth converting, or whether the hull wants new ones.
3. Balance: 1300 m is larger than any vanilla ship, and ten turrets on an XL hull is a guess.

Issues and PRs are welcome, and so is a reply on the reddit thread. If the procedural approach is simply the wrong way round and the ship should be modelled by hand, that is useful to hear too.

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

- Parsing Ironclad's text mesh format: geometry, UVs, materials and hardpoints
- Axis, winding and texture-coordinate conversion into the X4 convention
- A real modelled hull at 11,912 triangles, with UVs and the original texture assignments
- Normalisation to `SHIP_LENGTH` with a centred origin, and a decimated four-step LOD chain
- Collision mesh from a cleaned convex hull with interior geometry removed
- Turret and dock connections derived from the original hardpoints rather than guessed
- Export to `.xmf` through the official Egosoft Blender tools, driven headless
- Component XML with 20 tagged connections, generated by the toolchain rather than hand-written
- The procedural generator, still runnable for blocking work

### Missing

- **Textures and materials.** The hull ships with one placeholder material and no X4 material library entry, so it renders untextured. The 2009 Sins textures are still unconverted.
- **Borrowed sub-macros.** The cockpit, storage and dock connections bind Argon macros, so the bridge interior and cargo bay are vanilla Argon parts.
- **Hard-point naming and orientation.** The `con_*` names need to be checked against the naming X4's component XML actually resolves. The source hardpoints all carry an identity orientation, so turret facing has to be authored from scratch.
- **Engine connections.** The source mesh has no engine hardpoint; the two placed are computed from the aft of the central hull and are a guess.
- **Materials for X4.** The mesh keeps its Sins materials and DDS references. X4's shaders and material library need their own definitions, and the 2009 textures may not survive the move.
- **Scale sanity.** At 1300 m this is considerably larger than any vanilla X4 ship. Whether that survives contact with the game's balance, and how many turret hard-points it should really carry, is unvalidated.
- **The component XML.** The macro, ware, blueprint script and text exist; the component that would describe our own geometry and connections does not, because there is nothing to point it at yet.

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

The hull mesh originates in the **SOASE Andromeda Mod** by **CKYRules** and is used with the author's
permission. It is not covered by the MIT licence above, and it is not redistributed in this
repository — see [Mesh source](#mesh-source).

This is a **non-commercial fan project**. Andromeda, the Andromeda Ascendant and all related names and designs belong to the rights holders of the series. X4: Foundations and its file formats belong to Egosoft GmbH. This project is not affiliated with, sponsored by or endorsed by either, and is not for sale.
