# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Procedural Blender hull generator and X4 extension scaffold.
- Shared installation and publishing helpers and X4 9.00 dependency.
- Repository settings, development checks and documentation.
- Converter from the Sins of a Solar Empire text mesh format to OBJ, with hardpoints.
- Blender import that normalises the converted hull to X4 axes, scale and connections.
- Ship macro, ware, blueprint script and localised text, buildable only at a player shipyard.
- Andromeda hull exported to xmf with lods, collision, wreck and physics meshes.

### Fixed

- Preserve triangle winding through the Sins axis transform and reject invalid geometry before export.
- Repair legacy OBJ normals and simplified LOD shading; regenerate hull, wreck, collision and physics assets.
- Use opaque grey hull colour, neutral vertex colour and an explicit zero paint mask.
- Place stable turret/shield connections on triangles and align them with local surface normals.
- Separate engine and turret groups, expose both main weapons as individual slots and add fourteen local medium shield slots.
- Recover missing custom blueprints after game initialization and save loads, including completed legacy cues.
- Restore the previous installation after failed or interrupted install/publish operations and validate target paths and Workshop ids.
- Add local asset validation, conversion/transaction tests, Blender checks and a reproducible packaging step.

- Align all shield length axes with the ship, including on sloped and ventral mounting surfaces.
- Make main weapons selectable individual slots using an exclusive Ravager-derived component and correct forward emitter orientation.
- Restrict new engine and main-weapon equipment choices to Andromeda components through a registered compatibility type.
- Replace the pale flat hull with darker box-projected base-game panel textures also used by Hyperion, without requiring its DLC.
