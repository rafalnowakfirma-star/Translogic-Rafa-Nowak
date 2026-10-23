"""Wymiary zabudowy wokół sofy narożnej z ukrytymi głośnikami tylnymi (metry).

Wspólne dla renderów (render.py) i rysunku technicznego (rysunek.py).
Układ: x – w prawo, patrząc na sofę z pokoju; y – od ściany w głąb pokoju; z – od podłogi.
"""
import math

SUFIT = 2.70          # wysokość pokoju
GL = 0.40             # głębokość regałów i pawlacza
PLYTA = 0.018         # grubość płyty korpusu
FRONT = 0.018         # grubość frontu

# sofa narożna prawostronna (część narożna po prawej, patrząc na sofę)
SOFA_W = 2.80         # szerokość części przy ścianie
SOFA_D = 0.95         # głębokość siedziska z oparciem
SZEZL_W = 0.85        # szerokość części narożnej
SZEZL_D = 1.75        # długość części narożnej, licząc od ściany
SOFA_OD_SCIANY = 0.03
OPARCIE_Z = 0.85
SIEDZISKO_Z = 0.45

SZCZELINA = 0.05                       # odstęp sofa–regał
REG_W = 0.60                           # szerokość regału
X_REG = SOFA_W / 2 + SZCZELINA         # 1.45: bok regału od strony sofy
X_ZEW = X_REG + REG_W                  # 2.05: zewnętrzny bok regału

COKOL = 0.06
SZAFKA_Z = 0.75                        # wierzch szafki dolnej
POLKI = (1.13, 1.52)                   # półki otwarte nad szafką
MOST_Z = 1.90                          # spód pawlacza nad sofą = półka regału
POLKA_GORNA = 2.30                     # półka w górnej strefie regału (wariant otwarty)

WNEKA_W = 0.45                         # wnęka na głośnik na końcu pawlacza
X_WNEKA = X_REG - WNEKA_W              # 1.00: przegroda wnęki

# głośnik tylny: mały monitor półkowy na uchwycie uchylnym
GLOSNIK = (0.16, 0.25, 0.18)           # szer. × wys. × głęb.
G_X = X_REG - WNEKA_W / 2              # 1.225: środek wnęki
G_Y = 0.20                             # środek głośnika od ściany
G_Z = 2.17                             # środek głośnika od podłogi
UCHO_Y = 0.60                          # uszy siedzącego od ściany
UCHO_Z = 1.10                          # wysokość uszu siedzącego
CEL_Y = 0.85                           # oś trafia trochę przed głowę: siedzący oparty i pochylony
CEL_Z = UCHO_Z
POCHYLENIE = math.degrees(math.atan2(G_Z - CEL_Z, CEL_Y - G_Y))   # ≈ 59° w dół
ZBIEZNOSC = 12.0                       # skręt osi do środka sofy
NAD_USZAMI = G_Z - UCHO_Z              # ≈ 1,07 m
