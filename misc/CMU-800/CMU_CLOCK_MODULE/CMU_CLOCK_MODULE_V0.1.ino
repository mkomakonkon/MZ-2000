/*
============================================================
  BPM CLOCK GENERATOR  最終完成版

【機能】
  ・4桁BPM表示（OLED 128x32 I2C）
  ・カーソルで各桁編集
  ・SETボタン押下時にのみクロック更新
  ・D9からクロック出力

【クロック仕様】
  ・出力ピン：D9
  ・周波数(Hz) = BPM / 2.5
  ・LOW = 30%
  ・HIGH = 70%
  ・Timer未使用（micros制御）
  ・OLED表示中も安定動作

【ピン接続図】

            +----------------------+
            |      Arduino Nano    |
            |                      |
   D2  ---- | UPボタン  (GNDへ)    |
   D3  ---- | DOWNボタン(GNDへ)    |
   D4  ---- | LEFTボタン(GNDへ)    |
   D5  ---- | RIGHTボタン(GNDへ)   |
   D6  ---- | SETボタン  (GNDへ)   |
   D9  ---- | CLOCK出力            |
            |                      |
   A4  ---- | OLED SDA             |
   A5  ---- | OLED SCL             |
   5V  ---- | OLED VCC             |
   GND ---- | OLED GND             |
            +----------------------+

※ ボタンは INPUT_PULLUP 使用
   押すとGNDに落ちる構成
============================================================
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

/* ---- Buttons ---- */
#define BTN_UP    2
#define BTN_DOWN  3
#define BTN_LEFT  4
#define BTN_RIGHT 5
#define BTN_SET   6

/* ---- Clock ---- */
#define CLK_PIN 9

/* ---- BPM digits ---- */
int d1000 = 0;
int d100  = 1;
int d10   = 2;
int d1    = 0;

int cursor = 2;
float bpm = 120.0;

/* ---- Clock timing ---- */
unsigned long high_us = 0;
unsigned long low_us  = 0;
unsigned long lastTime = 0;
bool clkState = HIGH;

/* ===== Button debounce ===== */
bool pressed(int pin){
  static unsigned long lastTimeBtn[10];
  static bool lastState[10];

  bool state = digitalRead(pin);

  if(lastState[pin] == HIGH && state == LOW){
    if(millis() - lastTimeBtn[pin] > 30){
      lastTimeBtn[pin] = millis();
      lastState[pin] = state;
      return true;
    }
  }

  lastState[pin] = state;
  return false;
}

/* ===== SET時のみクロック再計算 ===== */
void applyBPM(){
  
  bpm = d1000*1000 + d100*100 + d10*10 + d1;

  if(bpm < 1)    bpm = 1;
  if(bpm > 1250) bpm = 1250;

  float freq = bpm / 2.5;

  const float F_CPU_F = 16000000.0;
  const float N = 64.0;

  float ocr_f = (F_CPU_F / (2.0 * N * freq)) - 1.0;
  if(ocr_f < 0) ocr_f = 0;
  if(ocr_f > 65535) ocr_f = 65535;

  uint16_t ocr = (uint16_t)(ocr_f + 0.5);

  OCR1A = ocr;

  // ★ シリアルに現在の周波数を表示
  Serial.print("BPM=");
  Serial.print(bpm);
  Serial.print("  Freq=");
  Serial.print(freq);
  Serial.println(" Hz");
}


/* ===== Setup ===== */
void setup(){
  Serial.begin(115200);
  delay(100);   // ★これを入れると Serial が安定する

  pinMode(CLK_PIN, OUTPUT);
  digitalWrite(CLK_PIN, LOW);

  pinMode(BTN_UP,    INPUT_PULLUP);
  pinMode(BTN_DOWN,  INPUT_PULLUP);
  pinMode(BTN_LEFT,  INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_SET,   INPUT_PULLUP);

  // ---- Timer1 設定（16MHz / プリスケーラ64 / CTC / OC1Aトグル）----
  TCCR1A = 0;
  TCCR1B = 0;

  // CTC モード
  TCCR1B |= (1 << WGM12);

  // プリスケーラ 64
  TCCR1B |= (1 << CS11) | (1 << CS10);

  // ★これが無いと D9 が動かない
  TCCR1A |= (1 << COM1A0);

  // ★Timer1 初期化が終わってから OCR1A を設定する
  applyBPM();

  // ---- OLED ----
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.setRotation(0);
  display.clearDisplay();
}


/* ===== Loop ===== */
void loop(){

  /* ---- Cursor move ---- */
  if(pressed(BTN_LEFT))  cursor = (cursor + 3) % 4;
  if(pressed(BTN_RIGHT)) cursor = (cursor + 1) % 4;

  /* ---- Digit change ---- */
  if(pressed(BTN_UP)){
    if(cursor==0) d1000=(d1000+1)%10;
    if(cursor==1) d100 =(d100 +1)%10;
    if(cursor==2) d10  =(d10  +1)%10;
    if(cursor==3) d1   =(d1   +1)%10;
  }

  if(pressed(BTN_DOWN)){
    if(cursor==0) d1000=(d1000+9)%10;
    if(cursor==1) d100 =(d100 +9)%10;
    if(cursor==2) d10  =(d10  +9)%10;
    if(cursor==3) d1   =(d1   +9)%10;
  }

  /* ---- SETで反映 ---- */
  if(pressed(BTN_SET)){
    applyBPM();
  }

  /* ---- Clock generation ---- */
  unsigned long now = micros();

  if(clkState){
    if(now - lastTime >= high_us){
      digitalWrite(CLK_PIN, LOW);
      clkState = LOW;
      lastTime += high_us;
    }
  } else {
    if(now - lastTime >= low_us){
      digitalWrite(CLK_PIN, HIGH);
      clkState = HIGH;
      lastTime += low_us;
    }
  }

  /* ---- OLED表示 ---- */
  display.clearDisplay();
  display.setTextSize(4);

  int digits[4] = {d1000, d100, d10, d1};
  bool blink = (millis()/400)%2;

  for(int i=0;i<4;i++){
    int x = i * 23;

    if(i == cursor && blink){
      display.fillRect(x,0,23,32,SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK);
    } else {
      display.setTextColor(SSD1306_WHITE);
    }

    display.setCursor(x,0);
    display.print(digits[i]);
  }

  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  int bpmX = 96;
  display.setCursor(bpmX,4);  display.print("b");
  display.setCursor(bpmX,14); display.print("p");
  display.setCursor(bpmX,24); display.print("m");

  display.display();
}
