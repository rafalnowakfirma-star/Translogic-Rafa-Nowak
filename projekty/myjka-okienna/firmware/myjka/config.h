#pragma once
// Konfiguracja myjki okiennej MO-1. Wartości ruchu i prądu dobierz przy
// uruchomieniu (README, rozdz. 9).

// ---------- Sieć ----------
#define WIFI_SSID "twoja_siec"
#define WIFI_PASS "twoje_haslo"
#define HOSTNAME  "myjka"          // http://myjka.local/

// ---------- Cykl mycia ----------
constexpr int      DEFAULT_CYCLES = 2;
constexpr int      MAX_CYCLES     = 5;
constexpr uint32_t SPRAY_MS       = 10000;  // natrysk przed szorowaniem
constexpr uint32_t SOAK_MS        = 15000;  // namaczanie brudu
constexpr uint32_t RINSE_MS       = 5000;   // natrysk płuczący przed ściąganiem
constexpr uint32_t DRAIN_MS       = 3000;   // spłynięcie wody przed ściąganiem

// Prędkości w % wypełnienia PWM
constexpr int SPEED_HOME     = 60;
constexpr int SPEED_SCRUB    = 80;  // w górę: mikrofibra
constexpr int SPEED_SQUEEGEE = 60;  // w dół: guma
constexpr int SPEED_FINAL    = 50;  // ostatnie ściąganie, wolniej = mniej smug

// ---------- Zabezpieczenia ----------
constexpr float    MIN_TEMP_C        = 3.0f;
constexpr float    CURRENT_LIMIT_MA  = 1200.0f;  // ok. 1,5–2× prądu normalnej jazdy
constexpr uint32_t INRUSH_MS         = 250;      // ignoruj prąd rozruchu
constexpr uint32_t RAMP_MS           = 300;      // łagodny start
constexpr uint32_t STALL_MS          = 400;      // enkoder stoi = zablokowanie
constexpr uint32_t STROKE_TIMEOUT_MS = 120000;
constexpr float    SOFT_LIMIT_MARGIN = 0.03f;    // dopuszczalne przekroczenie skoku
constexpr int32_t  MIN_STROKE_COUNTS = 2000;     // krótszy skok = błąd krańcówek

// Kierunek enkodera: zmień na -1, jeśli przy jeździe w górę licznik maleje.
constexpr int ENC_DIR = 1;
