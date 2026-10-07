#!/usr/bin/env bash
# Eksportuje wszystkie części silnika V8 do plików STL (wymaga OpenSCAD 2021+).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p stl
CZESCI="blok pokrywa_lozyska miska ramie_walu czop_korbowy czop_glowny_1 czop_glowny_2 czop_glowny_3
czop_glowny_4 czop_glowny_5 korbowod pokrywa_korbowodu tlok sworzen walek_rozrzadu_gora walek_rozrzadu_dol
kolo_rozrzadu_walu kolo_rozrzadu_walka popychacz drazek dzwigienka os_dzwigienek zawor talerzyk sprezyna_tpu
glowica pokrywa_zaworow kolektor_wydechowy kolektor_ssacy gaznik filtr_powietrza aparat_zaplonowy
kolo_zamachowe kolo_pasowe kolek"
for c in $CZESCI; do
    ( openscad -q -D "czesc=\"$c\"" -D '$fn=72' -o "stl/$c.stl" silnik_v8.scad && echo "OK  $c" ) &
    while [ "$(jobs -r | wc -l)" -ge "${JOBS:-4}" ]; do sleep 0.2; done
done
wait
