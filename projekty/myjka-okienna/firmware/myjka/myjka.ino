/*
 * Myjka okienna MO-1 — sterownik (ESP32, Arduino-ESP32 3.x)
 * Opis konstrukcji i podłączenia: ../../README.md
 *
 * Biblioteki: OneWire, DallasTemperature, Adafruit INA219.
 *
 * Głowica parkuje na dole. Cykl: bazowanie w dół, potem N razy
 * [natrysk, namaczanie, w górę (szorowanie), płukanie, w dół (ściąganie)].
 * Pętla główna nie blokuje, więc STOP i czujniki działają w każdej chwili.
 */
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_INA219.h>
#include <esp_task_wdt.h>
#include "config.h"

// ---------- Piny ----------
constexpr int PIN_MOT_IN1 = 25;  // DRV8871 IN1 — w górę
constexpr int PIN_MOT_IN2 = 26;  // DRV8871 IN2 — w dół
constexpr int PIN_ENC_A   = 34;  // zewnętrzny pull-up 10k
constexpr int PIN_ENC_B   = 35;
constexpr int PIN_END_TOP = 32;  // Hall, LOW = magnes
constexpr int PIN_END_BOT = 33;
constexpr int PIN_PUMP    = 27;
constexpr int PIN_SASH    = 14;  // kontaktron, LOW = okno zamknięte
constexpr int PIN_TANK    = 13;  // pływak, LOW = jest woda
constexpr int PIN_RAIN    = 4;   // LOW = mokro
constexpr int PIN_ONEWIRE = 19;
constexpr int PIN_LED     = 2;

constexpr uint32_t PWM_FREQ = 20000;
constexpr uint8_t  PWM_BITS = 10;
constexpr int      PWM_MAX  = (1 << PWM_BITS) - 1;

// ---------- Stan ----------
enum class Mode { Idle, Running, Parking, Fault };
enum class Op : uint8_t { Home, Spray, Wait, Up, Down };

struct Step {
  Op op;
  uint32_t arg;  // ms dla Spray/Wait, prędkość % dla Home/Up/Down
};

constexpr int MAX_STEPS = 2 + MAX_CYCLES * 5;
Step program[MAX_STEPS];
int progLen = 0;
int progPos = 0;

Mode mode = Mode::Idle;
String lastError;      // awaria (wymaga /reset)
String lastWarning;    // przerwanie łagodne
uint32_t stepT0 = 0;
bool stepStarted = false;

volatile int32_t encCount = 0;
int32_t lastEnc = 0;
uint32_t lastEncChangeMs = 0;
bool homed = false;
int32_t strokeCounts = 0;  // zmierzony skok dół→góra

float currentMa = 0;
float tempC = NAN;
uint32_t lastTempReq = 0;

WebServer server(80);
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature tempSensor(&oneWire);
Adafruit_INA219 ina;
bool inaOk = false;

// ---------- Wejścia ----------
bool sashClosed() { return digitalRead(PIN_SASH) == LOW; }
bool waterOk()    { return digitalRead(PIN_TANK) == LOW; }
bool raining()    { return digitalRead(PIN_RAIN) == LOW; }
bool endTop()     { return digitalRead(PIN_END_TOP) == LOW; }
bool endBot()     { return digitalRead(PIN_END_BOT) == LOW; }

void IRAM_ATTR onEncA() {
  bool a = digitalRead(PIN_ENC_A);
  bool b = digitalRead(PIN_ENC_B);
  encCount += (a == b) ? ENC_DIR : -ENC_DIR;
}

int32_t encRead() {
  noInterrupts();
  int32_t v = encCount;
  interrupts();
  return v;
}

void encZero() {
  noInterrupts();
  encCount = 0;
  interrupts();
  lastEnc = 0;
}

// ---------- Wyjścia ----------
void motorDrive(int dir, int duty) {  // dir: +1 góra, -1 dół
  ledcWrite(PIN_MOT_IN1, dir > 0 ? duty : 0);
  ledcWrite(PIN_MOT_IN2, dir < 0 ? duty : 0);
}

void motorBrake() {  // DRV8871: oba wejścia wysokie = hamowanie
  ledcWrite(PIN_MOT_IN1, PWM_MAX);
  ledcWrite(PIN_MOT_IN2, PWM_MAX);
}

void motorCoast() {
  ledcWrite(PIN_MOT_IN1, 0);
  ledcWrite(PIN_MOT_IN2, 0);
}

void pump(bool on) { digitalWrite(PIN_PUMP, on ? HIGH : LOW); }

void allOff() {
  motorBrake();
  pump(false);
  delay(50);
  motorCoast();  // przekładnia ślimakowa trzyma głowicę sama
}

// ---------- Obsługa błędów ----------
void fault(const String& why) {
  allOff();
  mode = Mode::Fault;
  homed = false;
  lastError = why;
  Serial.println("AWARIA: " + why);
}

// Przerwanie łagodne: zjedź gumą na dół i zatrzymaj się.
void softAbort(const String& why) {
  pump(false);
  motorCoast();
  lastWarning = why;
  Serial.println("Przerwano: " + why);
  progLen = 0;
  program[progLen++] = {Op::Down, SPEED_SQUEEGEE};
  progPos = 0;
  stepStarted = false;
  mode = Mode::Parking;
}

// ---------- Program mycia ----------
void addStep(Op op, uint32_t arg) {
  if (progLen < MAX_STEPS) program[progLen++] = {op, arg};
}

void buildProgram(int cycles) {
  progLen = 0;
  addStep(Op::Home, SPEED_HOME);
  for (int i = 0; i < cycles; i++) {
    addStep(Op::Spray, SPRAY_MS);
    addStep(Op::Wait, SOAK_MS);
    addStep(Op::Up, SPEED_SCRUB);
    addStep(Op::Spray, RINSE_MS);
    addStep(Op::Wait, DRAIN_MS);
    addStep(Op::Down, i == cycles - 1 ? SPEED_FINAL : SPEED_SQUEEGEE);
  }
}

String precheck() {
  if (!sashClosed()) return "okno otwarte";
  if (!inaOk) return "brak czujnika pradu INA219";
  if (isnan(tempC)) return "brak odczytu temperatury";
  if (tempC < MIN_TEMP_C) return "za zimno (" + String(tempC, 1) + " C)";
  if (raining()) return "pada deszcz";
  if (!waterOk()) return "brak wody w zbiorniku";
  return "";
}

String startWash(int cycles) {
  if (mode == Mode::Running || mode == Mode::Parking) return "juz pracuje";
  if (mode == Mode::Fault) return "awaria: " + lastError + " (wymagany /reset)";
  String why = precheck();
  if (why.length()) return why;
  buildProgram(constrain(cycles, 1, MAX_CYCLES));
  progPos = 0;
  stepStarted = false;
  lastWarning = "";
  mode = Mode::Running;
  Serial.printf("Start: %d cykli\n", constrain(cycles, 1, MAX_CYCLES));
  return "";
}

void stopWash() {
  allOff();
  if (mode != Mode::Fault) mode = Mode::Idle;
  homed = false;  // pozycja niepewna, kolejny start zacznie od bazowania
}

// Zwraca true, gdy ruch dotarł do krańcówki.
bool motionTick(int dir, int speedPct) {
  uint32_t now = millis();
  uint32_t t = now - stepT0;

  if (dir > 0 ? endTop() : endBot()) {
    motorBrake();
    delay(30);
    motorCoast();
    return true;
  }

  int target = PWM_MAX * speedPct / 100;
  int duty = t < RAMP_MS ? (int)((int64_t)target * t / RAMP_MS) : target;
  motorDrive(dir, duty);

  int32_t pos = encRead();
  if (pos != lastEnc) {
    lastEnc = pos;
    lastEncChangeMs = now;
  }

  if (t > INRUSH_MS) {
    if (currentMa > CURRENT_LIMIT_MA) {
      fault("przeciazenie silnika " + String(currentMa, 0) + " mA");
      return false;
    }
    if (now - lastEncChangeMs > STALL_MS) {
      fault("glowica zablokowana (enkoder stoi)");
      return false;
    }
  }
  if (t > STROKE_TIMEOUT_MS) {
    fault("przekroczony czas ruchu");
    return false;
  }
  if (homed && strokeCounts > 0) {
    int32_t margin = (int32_t)(strokeCounts * SOFT_LIMIT_MARGIN);
    if (pos > strokeCounts + margin) {
      fault("nie zadzialala krancowka gorna");
      return false;
    }
    if (pos < -margin) {
      fault("nie zadzialala krancowka dolna");
      return false;
    }
  }
  return false;
}

// Zwraca true, gdy bieżący krok się zakończył.
bool stepTick(const Step& s) {
  uint32_t now = millis();
  if (!stepStarted) {
    stepStarted = true;
    stepT0 = now;
    lastEncChangeMs = now;
    lastEnc = encRead();
    if (s.op == Op::Spray) pump(true);
  }

  switch (s.op) {
    case Op::Home:
      if (motionTick(-1, s.arg)) {
        encZero();
        homed = true;
        return true;
      }
      return false;

    case Op::Up:
      if (motionTick(+1, s.arg)) {
        int32_t pos = encRead();
        if (homed && strokeCounts == 0) {
          if (pos < MIN_STROKE_COUNTS) {
            fault("za krotki skok - sprawdz krancowki");
            return false;
          }
          strokeCounts = pos;
          Serial.printf("Zmierzony skok: %ld impulsow\n", (long)pos);
        }
        return true;
      }
      return false;

    case Op::Down:
      if (motionTick(-1, s.arg)) {
        encZero();  // korekta dryfu enkodera na krańcówce dolnej
        return true;
      }
      return false;

    case Op::Spray:
      if (!waterOk()) {
        softAbort("skonczyla sie woda");
        return false;
      }
      if (now - stepT0 >= s.arg) {
        pump(false);
        return true;
      }
      return false;

    case Op::Wait:
      return now - stepT0 >= s.arg;
  }
  return true;
}

void runTick() {
  if (mode != Mode::Running && mode != Mode::Parking) return;

  // Bezpieczeństwo — sprawdzane w każdym obiegu pętli.
  if (!sashClosed()) {
    fault("otwarto okno w trakcie pracy");
    return;
  }
  if (mode == Mode::Running && raining()) {
    softAbort("zaczal padac deszcz");
    return;
  }

  if (progPos >= progLen) {
    allOff();
    mode = Mode::Idle;
    Serial.println(lastWarning.length() ? "Zaparkowano po przerwaniu" : "Mycie zakonczone");
    return;
  }

  Mode before = mode;
  bool done = stepTick(program[progPos]);
  if (mode != before) return;  // fault() lub softAbort() podmieniły program
  if (done) {
    progPos++;
    stepStarted = false;
  }
}

// ---------- Czujniki okresowe ----------
void sensorsTick() {
  static uint32_t lastIna = 0;
  uint32_t now = millis();

  if (inaOk && now - lastIna >= 10) {
    lastIna = now;
    currentMa = fabsf(ina.getCurrent_mA());
  }

  if (now - lastTempReq >= 5000) {  // pomiar asynchroniczny co 5 s
    float t = tempSensor.getTempCByIndex(0);
    tempC = (t == DEVICE_DISCONNECTED_C) ? NAN : t;
    tempSensor.requestTemperatures();
    lastTempReq = now;
  }
}

// ---------- Interfejs ----------
const char* modeName() {
  switch (mode) {
    case Mode::Idle:    return "idle";
    case Mode::Running: return "running";
    case Mode::Parking: return "parking";
    case Mode::Fault:   return "fault";
  }
  return "?";
}

const char* opName(Op op) {
  switch (op) {
    case Op::Home:  return "bazowanie";
    case Op::Spray: return "natrysk";
    case Op::Wait:  return "oczekiwanie";
    case Op::Up:    return "szorowanie (gora)";
    case Op::Down:  return "sciaganie (dol)";
  }
  return "?";
}

String statusJson() {
  String step = (mode == Mode::Running || mode == Mode::Parking) && progPos < progLen
                    ? String(opName(program[progPos].op)) + " " + (progPos + 1) + "/" + progLen
                    : "";
  String j = "{";
  j += "\"mode\":\"" + String(modeName()) + "\"";
  j += ",\"step\":\"" + step + "\"";
  j += ",\"error\":\"" + lastError + "\"";
  j += ",\"warning\":\"" + lastWarning + "\"";
  j += ",\"temp_c\":" + (isnan(tempC) ? String("null") : String(tempC, 1));
  j += ",\"current_ma\":" + String(currentMa, 0);
  j += ",\"position\":" + String(encRead());
  j += ",\"stroke\":" + String(strokeCounts);
  j += ",\"homed\":" + String(homed ? "true" : "false");
  j += ",\"sash_closed\":" + String(sashClosed() ? "true" : "false");
  j += ",\"water_ok\":" + String(waterOk() ? "true" : "false");
  j += ",\"raining\":" + String(raining() ? "true" : "false");
  j += ",\"end_top\":" + String(endTop() ? "true" : "false");
  j += ",\"end_bottom\":" + String(endBot() ? "true" : "false");
  j += "}";
  return j;
}

const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Myjka okienna</title>
<style>
body{font-family:system-ui,sans-serif;max-width:480px;margin:24px auto;padding:0 16px;background:#f6f7f9;color:#1d232b}
button{font-size:18px;padding:12px 18px;margin:4px;border:0;border-radius:8px;color:#fff;cursor:pointer}
#go{background:#1f7a4d}#st{background:#b3261e}#rs{background:#5b6573}
pre{background:#fff;border:1px solid #d8dde3;border-radius:8px;padding:12px;white-space:pre-wrap}
</style></head><body>
<h1>Myjka okienna MO-1</h1>
<button id="go" onclick="cmd('start?cycles=2')">Myj</button>
<button id="st" onclick="cmd('stop')">STOP</button>
<button id="rs" onclick="cmd('reset')">Reset</button>
<pre id="s">…</pre>
<script>
function cmd(c){fetch('/'+c).then(r=>r.text()).then(t=>{if(t!=='ok')alert(t);upd()})}
function upd(){fetch('/status').then(r=>r.json()).then(j=>s.textContent=JSON.stringify(j,null,1))}
setInterval(upd,1000);upd();
</script></body></html>)HTML";

void setupWeb() {
  server.on("/", [] { server.send_P(200, "text/html", PAGE); });
  server.on("/status", [] { server.send(200, "application/json", statusJson()); });
  server.on("/start", [] {
    int cycles = server.hasArg("cycles") ? server.arg("cycles").toInt() : DEFAULT_CYCLES;
    String err = startWash(cycles);
    server.send(err.length() ? 409 : 200, "text/plain", err.length() ? err : "ok");
  });
  server.on("/stop", [] {
    stopWash();
    server.send(200, "text/plain", "ok");
  });
  server.on("/reset", [] {
    if (mode == Mode::Fault) {
      mode = Mode::Idle;
      lastError = "";
    }
    server.send(200, "text/plain", "ok");
  });
  server.begin();
}

void serialTick() {
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 's': {
      String err = startWash(DEFAULT_CYCLES);
      Serial.println(err.length() ? "Nie startuje: " + err : "ok");
      break;
    }
    case 'x': stopWash(); Serial.println("STOP"); break;
    case 'r': if (mode == Mode::Fault) { mode = Mode::Idle; lastError = ""; } break;
    case '?': Serial.println(statusJson()); break;
  }
}

// ---------- Start ----------
void setup() {
  // Wyjścia mocy najpierw, żeby nic nie ruszyło przy starcie.
  pinMode(PIN_PUMP, OUTPUT);
  pump(false);
  ledcAttach(PIN_MOT_IN1, PWM_FREQ, PWM_BITS);
  ledcAttach(PIN_MOT_IN2, PWM_FREQ, PWM_BITS);
  motorCoast();

  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_ENC_A, INPUT);
  pinMode(PIN_ENC_B, INPUT);
  pinMode(PIN_END_TOP, INPUT_PULLUP);
  pinMode(PIN_END_BOT, INPUT_PULLUP);
  pinMode(PIN_SASH, INPUT_PULLUP);
  pinMode(PIN_TANK, INPUT_PULLUP);
  pinMode(PIN_RAIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), onEncA, CHANGE);

  Wire.begin(21, 22);
  inaOk = ina.begin();
  if (inaOk) ina.setCalibration_32V_2A();

  tempSensor.begin();
  tempSensor.setWaitForConversion(false);
  tempSensor.requestTemperatures();
  lastTempReq = millis();

  // Watchdog: zawieszenie pętli > 3 s resetuje ESP32 (silnik staje).
  esp_task_wdt_config_t wdt = {.timeout_ms = 3000, .idle_core_mask = 0, .trigger_panic = true};
  esp_task_wdt_reconfigure(&wdt);
  esp_task_wdt_add(NULL);

  WiFi.setHostname(HOSTNAME);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  MDNS.begin(HOSTNAME);
  setupWeb();

  Serial.println("Myjka MO-1 gotowa. Komendy: s=start x=stop r=reset ?=status");
}

void loop() {
  esp_task_wdt_reset();
  sensorsTick();
  runTick();
  server.handleClient();
  serialTick();

  // LED: świeci = praca, miga = awaria, zgaszona = spoczynek.
  bool led = mode == Mode::Running || mode == Mode::Parking ||
             (mode == Mode::Fault && (millis() / 250) % 2);
  digitalWrite(PIN_LED, led);
}
