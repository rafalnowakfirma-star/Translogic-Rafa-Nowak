#!/bin/sh
# Publiczne strony TV (4 sekcje); użycie: sh tv/buduj.sh [v2a v2b v1a v1b]
cd "$(dirname "$0")/.." || exit 1
for s in ${@:-v2a v2b v1a v1b}; do
  case $s in
    v2a) w=2; d=p01-p10; t="domy 1–10";;
    v2b) w=2; d=p11-p20; t="domy 11–20";;
    v1a) w=1; d=p01-p08; t="archiwum 1–8";;
    v1b) w=1; d=p09-p16; t="archiwum 9–16";;
  esac
  nice -n 5 python3 film/portal.py --wersja $w --domy $d --publiczny --out tv/$s --tytul "Ogrody pod szkłem TV · $t" \
    --linki "$(cat tv/linki.json)" --sekcje tv/sekcje.json --sekcja $s 2>&1 | grep -E "PORTAL|Traceback|rror"
done
