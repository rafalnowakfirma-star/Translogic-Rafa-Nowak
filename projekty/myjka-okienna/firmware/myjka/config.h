#pragma once
// Konfiguracja myjki okiennej MO-1. Wartości ruchu, prądu i serwa dobierz przy
// uruchomieniu (README, rozdz. 9).

// ---------- Sieć ----------
#define WIFI_SSID "twoja_siec"
#define WIFI_PASS "twoje_haslo"
#define HOSTNAME  "myjka"          // http://myjka.local/

// ---------- Źródło wody ----------
// false: sam zbiornik (napełniany ręcznie).
// true:  zbiornik dolewany automatycznie z kranu przez zawór Z0.
constexpr bool     REFILL_FROM_MAINS  = false;
constexpr uint32_t REFILL_TIMEOUT_MS  = 300000;  // dłużej = wyciek lub zakręcony kran
constexpr uint32_t LOW_WATER_GRACE_MS = REFILL_FROM_MAINS ? 30000 : 3000;

// ---------- Płyn myjący (dozowanie do roztworu) ----------
constexpr float    DOSE_RATIO        = 0.005f;  // 1:200 (0,5 %); sprawdź zalecenie producenta płynu
constexpr float    FLOW_SOLUTION_LPM = 0.2f;    // wydatek dysz roztworu (zmierz!)
constexpr float    FLOW_DOSE_LPM     = 0.06f;   // wydajność pompy perystaltycznej (zmierz!)
constexpr uint32_t DOSE_PERIOD_MS    = 10000;   // impuls dozowania co 10 s

// ---------- Cykl mycia ----------
constexpr int      DEFAULT_CYCLES = 2;
constexpr int      MAX_CYCLES     = 5;
constexpr uint32_t SOAK_MS        = 10000;  // działanie płynu przed ściąganiem

// Prędkości jazdy w % wypełnienia PWM
constexpr int SPEED_HOME     = 60;
constexpr int SPEED_SCRUB    = 80;  // w górę: szczotka
constexpr int SPEED_SQUEEGEE = 60;  // w dół: guma
constexpr int SPEED_FINAL    = 50;  // ostatnie ściąganie, wolniej = mniej smug

// ---------- Szczotka obrotowa ----------
constexpr int      BRUSH_SPEED             = 90;    // % PWM
constexpr uint32_t BRUSH_RAMP_MS           = 800;
constexpr float    BRUSH_CURRENT_LIMIT_MA  = 2500.0f;

// ---------- Serwo wahacza (szerokość impulsu w µs) ----------
constexpr uint32_t SERVO_US_PARK     = 1500;  // oba elementy odsunięte od szyby
constexpr uint32_t SERVO_US_BRUSH    = 1200;  // dociśnięta szczotka
constexpr uint32_t SERVO_US_SQUEEGEE = 1800;  // dociśnięta guma
constexpr uint32_t SERVO_MOVE_MS     = 700;

// ---------- Zabezpieczenia ----------
constexpr float    MIN_TEMP_C        = 3.0f;
constexpr float    CURRENT_LIMIT_MA  = 1500.0f;  // silnik jazdy: ok. 1,5–2× prądu normalnej jazdy
constexpr uint32_t INRUSH_MS         = 250;      // ignoruj prąd rozruchu
constexpr uint32_t RAMP_MS           = 300;      // łagodny start
constexpr uint32_t STALL_MS          = 400;      // enkoder stoi = zablokowanie
constexpr uint32_t STROKE_TIMEOUT_MS = 150000;
constexpr float    SOFT_LIMIT_MARGIN = 0.03f;    // dopuszczalne przekroczenie skoku
constexpr int32_t  MIN_STROKE_COUNTS = 2000;     // krótszy skok = błąd krańcówek

// Kierunek enkodera: zmień na -1, jeśli przy jeździe w górę licznik maleje.
constexpr int ENC_DIR = 1;
