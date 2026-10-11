#!/usr/bin/env python3
"""Pobiera zewnętrzne zasoby do filmów (modele mebli, tekstury, HDRI, fonty) do katalogu zasoby/.

Wszystko na licencjach CC0 / CC BY 4.0 / OFL / MIT – lista z autorami w ZASOBY poniżej
(napisy końcowe filmów biorą atrybucje stąd).  Uruchom:  python3 film/zasoby.py
"""
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(HERE, "zasoby")

KH = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/{0}/glTF-Binary/{0}.glb"
TJ = "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/"
DREI = "https://raw.githubusercontent.com/pmndrs/drei-assets/master/hdri/"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"

# (plik lokalny, adres, autor / licencja)
ZASOBY = [
    ("modele/GlamVelvetSofa.glb", KH.format("GlamVelvetSofa"), "Eric Chadwick, Khronos glTF Sample Assets – CC BY 4.0"),
    ("modele/SheenWoodLeatherSofa.glb", KH.format("SheenWoodLeatherSofa"), "Eric Chadwick, Fran Calvente – CC BY 4.0"),
    ("modele/SheenChair.glb", KH.format("SheenChair"), "Eric Chadwick – CC0"),
    ("modele/SpecularSilkPouf.glb", KH.format("SpecularSilkPouf"), "Eric Chadwick – CC BY 4.0"),
    ("modele/AnisotropyBarnLamp.glb", KH.format("AnisotropyBarnLamp"), "Eric Chadwick – CC BY 4.0"),
    ("modele/IridescenceLamp.glb", KH.format("IridescenceLamp"), "Eric Chadwick – CC BY 4.0"),
    ("modele/GlassVaseFlowers.glb", KH.format("GlassVaseFlowers"), "Eric Chadwick, Rico Cilliers – CC0"),
    ("modele/GlassHurricaneCandleHolder.glb", KH.format("GlassHurricaneCandleHolder"), "Eric Chadwick – CC BY 4.0"),
    ("modele/DiffuseTransmissionPlant.glb", KH.format("DiffuseTransmissionPlant"), "Eric Chadwick, Rico Cilliers – CC BY 4.0"),
    ("modele/DiffuseTransmissionTeacup.glb", KH.format("DiffuseTransmissionTeacup"), "Poly Haven, Eric Chadwick – CC0"),
    ("modele/IridescentDishWithOlives.glb", KH.format("IridescentDishWithOlives"), "Eric Chadwick – CC BY 4.0"),
    ("modele/ClearcoatWicker.glb", KH.format("ClearcoatWicker"), "Eric Chadwick – CC0"),
    ("modele/CarConcept.glb", KH.format("CarConcept"), "Eric Chadwick – CC BY 4.0"),
    ("tekstury/hardwood2_diffuse.jpg", TJ + "hardwood2_diffuse.jpg", "three.js examples – MIT"),
    ("tekstury/hardwood2_bump.jpg", TJ + "hardwood2_bump.jpg", "three.js examples – MIT"),
    ("tekstury/hardwood2_roughness.jpg", TJ + "hardwood2_roughness.jpg", "three.js examples – MIT"),
    ("tekstury/brick_diffuse.jpg", TJ + "brick_diffuse.jpg", "three.js examples – MIT"),
    ("tekstury/brick_bump.jpg", TJ + "brick_bump.jpg", "three.js examples – MIT"),
    ("tekstury/brick_roughness.jpg", TJ + "brick_roughness.jpg", "three.js examples – MIT"),
    ("tekstury/grasslight-big.jpg", TJ + "terrain/grasslight-big.jpg", "three.js examples – MIT"),
    ("tekstury/waternormals.jpg", TJ + "waternormals.jpg", "three.js examples – MIT"),
    ("hdri/forest_slope_1k.hdr", DREI + "forest_slope_1k.hdr", "Poly Haven – CC0"),
    ("hdri/rooitou_park_1k.hdr", DREI + "rooitou_park_1k.hdr", "Poly Haven – CC0"),
    ("hdri/kiara_1_dawn_1k.hdr", DREI + "kiara_1_dawn_1k.hdr", "Poly Haven – CC0"),
    ("fonty/Archivo.ttf", GF + "archivo/Archivo%5Bwdth,wght%5D.ttf", "Archivo – SIL OFL"),
    ("fonty/HankenGrotesk.ttf", GF + "hankengrotesk/HankenGrotesk%5Bwght%5D.ttf", "Hanken Grotesk – SIL OFL"),
    ("fonty/IBMPlexMono-Regular.ttf", GF + "ibmplexmono/IBMPlexMono-Regular.ttf", "IBM Plex Mono – SIL OFL"),
]


def path(rel):
    return os.path.join(DIR, rel)


def main():
    bad = 0
    for rel, url, _lic in ZASOBY:
        p = path(rel)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r, open(p + ".part", "wb") as f:
                    f.write(r.read())
                os.replace(p + ".part", p)
                print("ok ", rel, os.path.getsize(p) // 1024, "kB")
                break
            except Exception as e:  # sieć bywa kapryśna
                print("błąd", rel, e, file=sys.stderr)
        else:
            bad += 1
    return bad


if __name__ == "__main__":
    sys.exit(main())
