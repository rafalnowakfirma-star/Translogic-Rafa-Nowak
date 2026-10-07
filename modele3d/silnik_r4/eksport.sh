#!/usr/bin/env bash
# Eksportuje wszystkie części silnika R4 do plików STL (wymaga OpenSCAD).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p stl
for c in podstawa blok wal korbowod tlok sworzen kolo male_czesci; do
    echo ">> $c"
    openscad -q -D "czesc=\"$c\"" -D '$fn=96' -o "stl/$c.stl" silnik_r4.scad
done
