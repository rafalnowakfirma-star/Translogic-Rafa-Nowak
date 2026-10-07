#!/usr/bin/env bash
# Sprawdza, czy w pełnym cyklu (720°) żadne części nie wchodzą na siebie.
# Wymaga: OpenSCAD, python3, pip install trimesh manifold3d numpy
set -euo pipefail
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
ids=$(grep -o '"L_[a-z_]*"' silnik_v8.scad | sort -u | tr -d '"')
for id in $ids; do
    openscad -q -D "czesc=\"$id\"" -D '$fn=32' -o "$TMP/$id.stl" silnik_v8.scad &
    while [ "$(jobs -r | wc -l)" -ge 8 ]; do sleep 0.2; done
done
wait
python3 narzedzia/kolizje.py silnik_v8.scad "$TMP" $(seq 0 ${KROK:-5} 715)
