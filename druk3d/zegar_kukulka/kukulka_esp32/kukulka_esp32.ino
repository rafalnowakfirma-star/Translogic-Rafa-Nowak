// Zegar z kukułką — sterownik ESP32
//
// Co pełną godzinę otwiera drzwiczki (ptak wysuwany serwem je wypycha)
// i kuka tyle razy, która jest godzina; o wpół do — raz.
// Czas pochodzi z internetu (NTP), więc nie trzeba go ustawiać.
//
// Biblioteki (Menedżer bibliotek Arduino IDE):
//   ESP32Servo (Kevin Harrington), DFRobotDFPlayerMini (DFRobot)
// Płytka: „ESP32 Dev Module” (pakiet esp32 od Espressif Systems).
//
// Polecenia w Monitorze portu szeregowego (115200, koniec linii „Nowa linia”):
//   k <kąt>   ustaw serwo na kąt 0–180 (kalibracja)
//   t <ile>   test: zakukaj podaną liczbę razy
//   g         pokaż aktualny czas

#include <WiFi.h>
#include <time.h>
#include <ESP32Servo.h>
#include <DFRobotDFPlayerMini.h>
#include "ustawienia.h"

HardwareSerial dfSerial(2);
DFRobotDFPlayerMini odtwarzacz;
Servo serwo;

bool odtwarzaczOk = false;
int  katTeraz = KAT_SCHOWANA;
long ostatniZnacznik = -1;          // zapobiega podwójnemu kukaniu w tej samej minucie

// ---------------------------------------------------------------------------

void ruchSerwa(int doKata, int czasMs) {
  int kroki = abs(doKata - katTeraz);
  if (kroki == 0) return;
  int odstep = max(1, czasMs / kroki);
  int krok = doKata > katTeraz ? 1 : -1;
  while (katTeraz != doKata) {
    katTeraz += krok;
    serwo.write(katTeraz);
    delay(odstep);
  }
}

void wlaczSerwo() {
  if (!serwo.attached()) {
    serwo.setPeriodHertz(50);
    serwo.attach(PIN_SERWA, 500, 2400);
    serwo.write(katTeraz);
    delay(50);
  }
}

// Serwo odłączone nie brzęczy i nie drży między kukaniami.
void wylaczSerwo() {
  delay(200);
  serwo.detach();
}

void kukanie(int ile) {
  Serial.printf("Ku-ku x%d\n", ile);
  int kierunekUklonu = KAT_SCHOWANA > KAT_WYSUNIETA ? 1 : -1;

  wlaczSerwo();
  ruchSerwa(KAT_WYSUNIETA, CZAS_WYSUWANIA_MS);
  delay(250);
  for (int i = 0; i < ile; i++) {
    if (odtwarzaczOk) odtwarzacz.playMp3Folder(1);
    ruchSerwa(KAT_WYSUNIETA + kierunekUklonu * UKLON, 150);
    ruchSerwa(KAT_WYSUNIETA, 150);
    delay(max(0, ODSTEP_KUKU_MS - 300));
  }
  ruchSerwa(KAT_SCHOWANA, CZAS_CHOWANIA_MS);
  wylaczSerwo();
}

bool cisza(int godzina) {
  if (CISZA_OD == CISZA_DO) return false;
  if (CISZA_OD < CISZA_DO) return godzina >= CISZA_OD && godzina < CISZA_DO;
  return godzina >= CISZA_OD || godzina < CISZA_DO;   // przez północ, np. 22–7
}

void pokazCzas() {
  struct tm t;
  if (getLocalTime(&t, 100)) {
    Serial.printf("%04d-%02d-%02d %02d:%02d:%02d\n", t.tm_year + 1900, t.tm_mon + 1, t.tm_mday,
                  t.tm_hour, t.tm_min, t.tm_sec);
  } else {
    Serial.println("Czas jeszcze nieznany (brak połączenia z NTP).");
  }
}

void obsluzPolecenia() {
  if (!Serial.available()) return;
  String linia = Serial.readStringUntil('\n');
  linia.trim();
  if (linia.length() == 0) return;
  char polecenie = linia.charAt(0);
  int liczba = linia.substring(1).toInt();

  if (polecenie == 'k') {
    liczba = constrain(liczba, 0, 180);
    wlaczSerwo();
    ruchSerwa(liczba, 400);
    Serial.printf("Serwo: %d°\n", liczba);
  } else if (polecenie == 't') {
    kukanie(liczba > 0 ? liczba : 3);
  } else if (polecenie == 'g') {
    pokazCzas();
  } else {
    Serial.println("Polecenia: k <kąt>, t <ile>, g");
  }
}

void polaczWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SIEC, WIFI_HASLO);
  Serial.print("Łączenie z Wi-Fi");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print('.');
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " OK" : " brak — spróbuję później");
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nZegar z kukułką");
  pinMode(PIN_PRZYCISK, INPUT_PULLUP);

  // Serwo: ustaw ptaka w pozycji schowanej
  wlaczSerwo();
  serwo.write(KAT_SCHOWANA);
  wylaczSerwo();

  // Odtwarzacz MP3: plik /mp3/0001.mp3 na karcie microSD
  dfSerial.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  odtwarzaczOk = odtwarzacz.begin(dfSerial, true, true);
  if (!odtwarzaczOk) odtwarzaczOk = odtwarzacz.begin(dfSerial, false, true);  // niektóre klony nie odpowiadają ACK
  if (odtwarzaczOk) {
    odtwarzacz.volume(GLOSNOSC);
    Serial.println("DFPlayer OK");
  } else {
    Serial.println("DFPlayer nie odpowiada — sprawdź kartę i połączenia. Kukułka będzie niema.");
  }

  polaczWiFi();
  configTzTime(STREFA_CZASOWA, SERWER_NTP_1, SERWER_NTP_2);   // czas odświeża się sam co godzinę

  if (KUKANIE_PRZY_STARCIE) kukanie(1);
}

void loop() {
  obsluzPolecenia();

  if (digitalRead(PIN_PRZYCISK) == LOW) {
    delay(50);
    if (digitalRead(PIN_PRZYCISK) == LOW) {
      struct tm t;
      int ile = 3;
      if (getLocalTime(&t, 10)) {
        ile = t.tm_hour % 12;
        if (ile == 0) ile = 12;
      }
      kukanie(ile);
      while (digitalRead(PIN_PRZYCISK) == LOW) delay(10);
    }
  }

  struct tm t;
  if (!getLocalTime(&t, 10)) {
    static unsigned long ostatniaProba = 0;
    if (WiFi.status() != WL_CONNECTED && millis() - ostatniaProba > 60000) {
      ostatniaProba = millis();
      WiFi.reconnect();
    }
    delay(200);
    return;
  }

  long znacznik = (long)t.tm_yday * 1440 + t.tm_hour * 60 + t.tm_min;
  if (t.tm_sec < 10 && znacznik != ostatniZnacznik) {
    ostatniZnacznik = znacznik;
    if (!cisza(t.tm_hour)) {
      if (t.tm_min == 0) {
        int ile = t.tm_hour % 12;
        kukanie(ile == 0 ? 12 : ile);
      } else if (t.tm_min == 30 && KUKANIE_O_WPOL) {
        kukanie(1);
      }
    }
  }
  delay(100);
}
