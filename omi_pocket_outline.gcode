; Omi DevKit 2 Pocket Outline
; Dimensions: 42.0mm x 41.0mm
; Cut depth: 1mm for template verification

G90 ; Absolute positioning
G21 ; mm units
G17 ; XY plane
F1000 ; Feed rate

; Move to start position
G0 X-12.600 Y20.500
G0 Z0.5
G1 Z-1.0 ; Plunge

G1 X12.600 Y20.500 ; Point 1
G1 X21.000 Y7.500 ; Point 2
G1 X21.000 Y-7.500 ; Point 3
G1 X0.000 Y-20.500 ; Point 4
G1 X-21.000 Y-7.500 ; Point 5
G1 X-21.000 Y7.500 ; Point 6
G1 X-12.600 Y20.500 ; Point 7

G0 Z5 ; Retract
G0 X0 Y0 ; Return to origin
M30 ; Program end
