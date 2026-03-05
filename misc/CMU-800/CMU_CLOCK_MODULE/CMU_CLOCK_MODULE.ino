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
  ・DUTY 50%
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
            | jackの先端(mono)に出力 |
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
#define CLK_PIN 9  // OC1A

/* ---- BPM digits (3桁) ---- */
int d100 = 1;
int d10  = 2;
int d1   = 0;

int cursor = 1;   // 0〜2
int bpm = 120;

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

/* ===== BPM → Timer1 設定 ===== */
void applyBPM(){

  bpm = d100*100 + d10*10 + d1;

  if(bpm < 0) bpm = 0;
  if(bpm > 999) bpm = 999;

  /* ---- BPM=000 → クロック停止 ---- */
  if(bpm == 0){
    // プリスケーラを 0 にして Timer1 停止
    TCCR1B &= ~((1 << CS12) | (1 << CS11) | (1 << CS10));
    Serial.println("BPM=000  Clock STOP");
    return;
  }

  /* ---- BPM → 周波数 ---- */
  float freq = bpm / 2.5;   // Hz

  /* ---- OCR1A 計算 ---- */
  const float F_CPU_F = 16000000.0;
  const float N = 64.0;

  float ocr_f = (F_CPU_F / (2.0 * N * freq)) - 1.0;
  if(ocr_f < 0) ocr_f = 0;
  if(ocr_f > 65535) ocr_f = 65535;

  uint16_t ocr = (uint16_t)(ocr_f + 0.5);

  OCR1A = ocr;

  /* ---- Timer1 再開（プリスケーラ 64） ---- */
  TCCR1B &= ~((1 << CS12) | (1 << CS11) | (1 << CS10));
  TCCR1B |= (1 << CS11) | (1 << CS10);

  /* ---- シリアル表示 ---- */
  Serial.print("BPM=");
  Serial.print(bpm);
  Serial.print("  Freq=");
  Serial.print(freq);
  Serial.println(" Hz");
}

/* ===== Setup ===== */
void setup(){

  Serial.begin(115200);
  delay(100);   // ★互換機では必須（Serial安定化）

  pinMode(CLK_PIN, OUTPUT);
  digitalWrite(CLK_PIN, LOW);

  pinMode(BTN_UP,    INPUT_PULLUP);
  pinMode(BTN_DOWN,  INPUT_PULLUP);
  pinMode(BTN_LEFT,  INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_SET,   INPUT_PULLUP);

  /* ---- Timer1 設定（16MHz / 64 / CTC / OC1Aトグル） ---- */
  TCCR1A = 0;
  TCCR1B = 0;

  TCCR1B |= (1 << WGM12);               // CTC
  TCCR1A |= (1 << COM1A0);              // OC1A トグル

  // プリスケーラは applyBPM() 内で設定する

  applyBPM();   // ★Timer1 初期化後に呼ぶ

  /* ---- OLED ---- */
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.setRotation(0);
  display.clearDisplay();
}

/* ===== Loop ===== */
void loop(){

  /* ---- Cursor move ---- */
  if(pressed(BTN_LEFT))  cursor = (cursor + 2) % 3;
  if(pressed(BTN_RIGHT)) cursor = (cursor + 1) % 3;

  /* ---- Digit change ---- */
  if(pressed(BTN_UP)){
    if(cursor==0) d100=(d100+1)%10;
    if(cursor==1) d10 =(d10 +1)%10;
    if(cursor==2) d1  =(d1  +1)%10;
  }

  if(pressed(BTN_DOWN)){
    if(cursor==0) d100=(d100+9)%10;
    if(cursor==1) d10 =(d10 +9)%10;
    if(cursor==2) d1  =(d1  +9)%10;
  }

  /* ---- SETで反映 ---- */
  if(pressed(BTN_SET)){
    applyBPM();
  }

/* ---- OLED表示 ---- */
display.clearDisplay();
display.setTextSize(4);

int digits[3] = {d100, d10, d1};
bool blink = (millis()/400)%2;

for(int i=0;i<3;i++){
  int x = i * 26;   // ★数字間隔を26pxに詰める（32→26）

  if(i == cursor && blink){
    display.fillRect(x,0,26,32,SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK);
  } else {
    display.setTextColor(SSD1306_WHITE);
  }

  display.setCursor(x,0);
  display.print(digits[i]);
}

/* ---- bpm を大きく（TextSize=2）で右側に配置 ---- */
display.setTextSize(2);
display.setTextColor(SSD1306_WHITE);

// 数字3桁の幅は 26×3 = 78px → 右側に配置
display.setCursor(82, 8);   // ★自然に見える位置
display.print("BPM");

display.display();
}
