# Cradle Tilt & Mudra Rise Mechanism — Design Spec

**Date:** 2026-05-22
**Status:** Approved
**Depends on:** Motorized reveal infrastructure (servo mounts, push rod slots, wiring channels — all complete)

## 1. Overview

Four mechanical linkages connecting the installed SG90 servos to wearable cradles. Three front-row devices (UH Ring, R1, Omi) get **drop-in tilt plates** with filament pin hinges along their rear edge. The Mudra pole gets a **vertical rise stop** limiting upward travel to 15mm.

All servos, push rod slots, and wiring are already installed. This spec covers only the moving parts: tilt plates, push rods, hinge hardware in the cradle pockets, and the Mudra rise stop.

## 2. Spatial Reference

Key positions (from existing design):

| Device | Cradle Center (X, Y) | Pocket Shape | Pocket Size | Cradle Depth | Push Rod Slot (X, Y) |
|--------|---------------------|--------------|-------------|--------------|---------------------|
| UH Ring | (-81.0, -49.5) | Square | 41mm side, 4mm corner R | 10mm | (-81.0, -37.0) |
| R1 Ring | (-27.0, -49.5) | Circle | 32mm diameter | 10mm | (-27.0, -37.0) |
| Omi | (27.0, -49.5) | 6-sided diamond | 30/15mm edges, 3mm vertex R | 15mm | (27.0, -37.0) |
| Mudra | (73.0, -49.5) | Rectangular socket | 20.6x22.6mm through-hole | 16mm (full) | (73.0, -37.0) |

Push rod slots: 4mm (X) x 12mm (Y), centered at SERVO_Y = -37.

Top tray floor: Z = SPLIT_Z = 41mm. Top surface: Z = STAND_H = 58mm.

## 3. Drop-In Tilt Plates (3 parts)

### 3.1 Concept

Each tilt plate is a thin slab matching its cradle pocket footprint. It sits inside the pocket and tilts on a filament pin hinge along its rear edge. When the servo push rod pushes from below, the front edge rises ~30 degrees, presenting the wearable to the user. When the servo retracts, gravity returns the plate to flush.

### 3.2 Plate Dimensions

| Device | Shape | Dimensions | Thickness | Clearance from pocket walls |
|--------|-------|------------|-----------|---------------------------|
| UH Ring | Square, 4mm corner R | 40mm x 40mm | 2mm | 0.5mm per side |
| R1 Ring | Circular | 31mm diameter | 2mm | 0.5mm radial |
| Omi | 6-sided diamond, 3mm vertex R | 29/14.5mm edges | 2mm | 0.5mm per side |

Plates are 1mm smaller than pocket in each dimension (0.5mm clearance per side) to tilt freely without binding.

### 3.3 Pin Hinge System

Each plate has **two cylindrical barrels** on its rear edge (the edge closest to Y=0, i.e., the +Y edge of the pocket):

- **Barrel dimensions:** 8mm long x 3mm OD x 1.75mm ID (bore for filament pin)
- **Barrel count:** 2 per plate, spaced symmetrically ~10mm from each end of the rear edge
- **Barrel orientation:** Axis parallel to X (horizontal, spanning the rear edge)
- **Barrel position:** Centered on the plate thickness (1mm from top/bottom), protruding 1.5mm beyond the rear edge

Matching **barrel sockets** are cut into the cradle pocket rear wall:

- **Socket dimensions:** 8.6mm long x 3.6mm diameter semicircular channel (0.3mm tolerance on each dimension)
- **Socket position:** At pocket floor level (Z = STAND_H - cradle_depth), centered on the wall thickness
- **Socket count:** 2 per pocket, aligned with plate barrels

**Hinge pin:** 1.75mm diameter filament (standard FDM filament), cut to plate width + 4mm. Threads through both barrels and both sockets.

### 3.4 Hinge Line Positions

The hinge is along the rear edge (+Y side) of each cradle pocket. For non-square pockets, the barrels are placed on a flat chord cut across the rear of the plate:

- **UH Ring:** Rear edge is flat (square pocket). Barrels sit directly on the +Y edge at Y = -29.0.
- **R1 Ring:** Circular plate. A 2mm-tall flat chord is cut across the rear at Y = -33.5 (the +Y extent of the 31mm disc). The two barrels mount on this flat. The chord width is ~20mm — enough for two 8mm barrels with spacing.
- **Omi:** Diamond plate. The rearmost vertex is at approximately Y = -30.3. The two barrels mount on the two edges flanking this vertex, angled slightly. Alternatively, a small flat is added at the vertex to mount both barrels on a straight line.

| Device | Hinge Y Position | Distance from Push Rod (Y=-37) | Front Edge Y |
|--------|-----------------|-------------------------------|--------------|
| UH Ring | -29.0 | 8.0mm | -70.0 |
| R1 Ring | -33.5 | 3.5mm | -65.5 |
| Omi | -30.3 (rearmost vertex) | 6.7mm | -68.7 |

### 3.5 Tilt Geometry

At 30 degree tilt with push rod at Y = -37:

| Device | Rod-to-Hinge Dist | Rise at Rod | Front Edge Dist from Hinge | Rise at Front Edge |
|--------|-------------------|-------------|---------------------------|-------------------|
| UH Ring | 8.0mm | 4.6mm | 41.0mm | 23.7mm |
| R1 Ring | 3.5mm | 2.0mm | 32.0mm | 18.5mm |
| Omi | 6.7mm | 3.9mm | 38.4mm | 22.2mm |

The front edge rise of 18-24mm provides a dramatic reveal. The actual tilt angle will be limited by the servo horn travel — full 90 degree horn rotation through the push rod linkage will produce approximately 30 degree plate tilt.

### 3.6 Captured Slot (Push Rod Contact)

On the underside of each tilt plate, centered at the push rod position:

- **Slot channel:** 4.5mm wide (X) x 3mm deep (Y) x 1.5mm tall, running parallel to Y axis
- **Position:** Centered at the point where the push rod slot falls within the plate (X = plate center, Y = -37 relative to world, converted to plate-local coordinates)
- **Purpose:** The push rod T-head sits in this channel, preventing lateral sliding

## 4. Push Rods (4 parts)

### 4.1 Tilt Push Rods (3 — UH Ring, R1, Omi)

- **Cross-section:** 3.5mm x 3.5mm square (fits through 4mm x 12mm slot with clearance)
- **Length:** Variable per device, from servo horn (~Z=30) to tilt plate underside (~Z=48 for UH/R1, ~Z=43 for Omi)
  - UH Ring: ~18mm
  - R1 Ring: ~18mm
  - Omi: ~13mm
- **Top end — T-head:** 6mm wide (X) x 2mm tall (Z) cross-piece, perpendicular to rod axis. Fits in the captured slot on the tilt plate underside. The T-head is wider than the 4mm push rod slot, so it cannot fall through.
- **Bottom end — Horn clip:** Fork with 1.5mm hole, fits over servo horn screw post. Or: flat tab with M2 hole for horn screw.

### 4.2 Mudra Push Rod (1)

- **Cross-section:** 3.5mm x 3.5mm square
- **Length:** ~11mm (from servo horn to pole base)
- **Top end:** Flat pad, 8mm x 8mm x 1.5mm, presses against Mudra pole base
- **Bottom end:** Same horn clip as tilt rods

### 4.3 Push Rod Travel

SG90 servo horn: standard single-arm, ~15mm from center to tip. At 90 degree rotation:
- Vertical displacement at horn tip: 15 x sin(90) = 15mm
- This delivers 15mm of upward push rod travel — sufficient for both the 30 degree tilt and the 15mm Mudra rise.

## 5. Mudra Vertical Rise — Servo-Limited Travel

### 5.1 Concept

The Mudra pole sits in a 20.6mm x 22.6mm through-socket, retained by snap hooks. No socket modification is needed for the rise mechanism. The servo travel itself acts as the rise stop:

- The Mudra push rod has a flat pad (8x8mm) that presses the pole base from below
- Push rod length is sized so that at maximum servo extension (90 degree horn rotation), the pole rises exactly 15mm
- The pole cannot rise further because the servo has reached its mechanical limit
- The pole cannot fall out because the existing snap hooks hold it in the socket
- When the servo retracts, the pole drops back to its rest position (gravity + snap hook engagement)

### 5.2 Why No Socket Modification

Internal shelves or tabs to limit rise travel would block pole insertion — the pole body (20mm) is wider than any gap created by shelves inside the 20.6mm socket. The servo-limited approach avoids this entirely: the servo horn's rotation range mechanically caps the rise at 15mm without any physical stop inside the socket.

## 6. Parts Summary

| Part | Count | Material | Print Orientation | Supports Needed |
|------|-------|----------|-------------------|-----------------|
| UH Ring tilt plate | 1 | PLA+ | Flat (barrels on top face) | No |
| R1 Ring tilt plate | 1 | PLA+ | Flat (barrels on top face) | No |
| Omi tilt plate | 1 | PLA+ | Flat (barrels on top face) | No |
| Push rod (tilt, UH) | 1 | PLA+ | Vertical | No |
| Push rod (tilt, R1) | 1 | PLA+ | Vertical | No |
| Push rod (tilt, Omi) | 1 | PLA+ | Vertical | No |
| Push rod (Mudra) | 1 | PLA+ | Vertical | No |
| Hinge pins | 3 | 1.75mm filament | N/A (cut from spool) | N/A |

**Modified existing parts:**
- Top tray: Add hinge barrel sockets in 3 cradle pockets (UH Ring, R1, Omi rear walls)
- Mudra pole: No modification needed (snap hooks already constrain it, servo travel limits rise)

## 7. Assembly Order

1. Print all new parts (4 push rods, 3 tilt plates)
2. Cut 3 filament pins from spool (~45mm for UH, ~35mm for R1, ~50mm for Omi)
3. Drop tilt plates into cradle pockets (barrels aligned with sockets in rear wall)
4. Thread filament pins through sockets and barrels to lock plates in place
5. From below: insert push rods through push rod slots (T-heads engage captured slots on plate underside)
6. Attach push rod bottoms to servo horns
7. Insert Mudra pole into socket (snap hooks engage as before)
8. Insert Mudra push rod from below, attach to servo horn

## 8. Changes to Existing Code

### 8.1 Top Tray (`build_top_tray()`)

**Add to each of 3 cradle pocket sections (UH Ring, R1, Omi):**
- Two semicircular barrel sockets cut into the rear wall of each pocket
- Socket position: at pocket floor level, rear (+Y) wall
- Socket dimensions: 8.6mm long x 3.6mm diameter semicircular channel

**No changes to Mudra socket** — servo travel limits rise, snap hooks prevent fallout.

### 8.2 New Functions

- `build_uh_tilt_plate()` — returns the UH Ring tilt plate solid (40x40x2mm square plate + 2 hinge barrels + captured slot)
- `build_r1_tilt_plate()` — returns the R1 Ring tilt plate solid (31mm dia x 2mm disc + 2 hinge barrels + captured slot)
- `build_omi_tilt_plate()` — returns the Omi tilt plate solid (29/14.5mm diamond x 2mm + 2 hinge barrels + captured slot)
- `build_push_rod(length, top_type)` — returns a push rod solid (3.5x3.5mm square rod + T-head or flat pad on top + horn clip on bottom)

### 8.3 Export Script

Add exports for the 3 tilt plates and 4 push rods (7 new STL files). Push rods are small enough to print together on one plate, but export individually for flexibility.

### 8.4 Ghost Visualization

Add translucent ghost overlays for the tilt plates (in tilted position) and push rods (extended position) to visualize the mechanism in cadquery-server.

## 9. Future Considerations

- **Spring return:** If gravity return proves unreliable (e.g., cable drag holds plate up), add a small torsion spring around the hinge pin
- **Damping:** If the plate drops too fast and makes noise, add a small rubber bumper on the pocket floor
- **Tilt angle tuning:** Adjustable by changing push rod length or servo horn arm position — no reprints needed
