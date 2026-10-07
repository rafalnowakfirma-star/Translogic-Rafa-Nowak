// Ustawienia zegara z kukułką — zmień przed wgraniem programu.
#pragma once

// --- Wi-Fi (potrzebne tylko do pobierania dokładnego czasu) ---
#define WIFI_SIEC  "nazwa_sieci"
#define WIFI_HASLO "haslo_do_sieci"

// Strefa czasowa Polski z automatyczną zmianą czasu letni/zimowy.
#define STREFA_CZASOWA "CET-1CEST,M3.5.0,M10.5.0/3"
#define SERWER_NTP_1   "tempus1.gum.gov.pl"   // Główny Urząd Miar
#define SERWER_NTP_2   "pool.ntp.org"

// --- Kukanie ---
#define KUKANIE_O_WPOL   true   // jedno „ku-ku” o wpół do
#define CISZA_OD         22     // od tej godziny kukułka śpi…
#define CISZA_DO         7      // …do tej (ustaw obie na 0, żeby kukała całą dobę)
#define GLOSNOSC         22     // 0–30
#define KUKANIE_PRZY_STARCIE true  // jedno „ku-ku” po włączeniu — test, że wszystko działa

// --- Serwo ---
// Kąty dobierz w trybie kalibracji (opis w README): wpisz w Monitorze portu
// szeregowego „k 90”, „k 120” itd. i sprawdź, gdzie ptak jest schowany,
// a gdzie wysunięty. Różnica powinna wynosić ok. 30°.
#define KAT_SCHOWANA   90
#define KAT_WYSUNIETA  121
#define UKLON          6        // jak mocno ptak „kłania się” przy każdym ku-ku
#define CZAS_WYSUWANIA_MS  700
#define CZAS_CHOWANIA_MS   900
#define ODSTEP_KUKU_MS     1300 // jedno „ku-ku” co tyle ms (plik dźwięku ok. 1 s)

// --- Piny ESP32 (DevKit) ---
#define PIN_SERWA      18
#define PIN_DF_RX      16   // ESP32 RX2 ← TX odtwarzacza DFPlayer
#define PIN_DF_TX      17   // ESP32 TX2 → RX odtwarzacza (przez rezystor 1 kΩ)
#define PIN_PRZYCISK   0    // przycisk BOOT na płytce: test kukania
