# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Current status — 2026-09-11

- Development paused pending help with X4 modelling, materials and turret integration.
- The user reported that the latest custom-turret attempt does not work in-game; the exact failure mode and root cause remain undiagnosed. Offline tests and successful conversion do not establish gameplay functionality.
- Preserve the experimental assets for handoff. The desired original-turret designs remain the goal; a decorative socket fallback has not been implemented.
- Repetitive hull textures and poor seating of standard turrets/shields on the rounded hull remain unresolved.
- Correct documentation that presented experimental turrets as completed, described the current visual state as untested, or claimed connection names were irrelevant.

### Added

- Experimental High Guard twin-beam component and four exclusive slots, using extracted original models, aiming-joint definitions, two muzzle connections and a blueprint recovery entry. Failed in-game acceptance; retained for diagnosis.

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
- Use opaque grey hull colour, dark vertex tint and an explicit zero paint mask.
- Place stable turret/shield connections on triangles and align them with local surface normals.
- Separate engine and turret groups, expose both main weapons as individual slots and add fourteen local medium shield slots.
- Recover missing custom blueprints after game initialization and save loads, including completed legacy cues.
- Restore the previous installation after failed or interrupted install/publish operations and validate target paths and Workshop ids.
- Add local asset validation, conversion/transaction tests, Blender checks and a reproducible packaging step.

- Align all shield length axes with the ship, including on sloped and ventral mounting surfaces.
- Make main weapons selectable individual slots using an exclusive Ravager-derived component and correct forward emitter orientation.
- Restrict new engine and main-weapon equipment choices to Andromeda components through a registered compatibility type.
- Replace the pale flat hull with darker box-projected base-game panel textures also used by Hyperion, without requiring its DLC.
