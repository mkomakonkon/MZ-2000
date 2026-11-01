/*
============================================================
  VOCALUINO4CMU - Serial Tempo Clock & Long Text Speech (VD=0)

【機能】
  1. D9ピンからのハードウェア・テンポクロック出力
     - PCのシリアルモニタ（115200bps）から数値入力でBPM変更
  2. VD[5:0] = 0 受信時の長文発声機能 (atp1 単体使用)
     - LS259のキャプチャ時、VD[5:0] == 0 で長文を順番に発声
============================================================
*/

#include <AquesTalk.h>
#include <Wire.h>
#include <avr/pgmspace.h>

// AquesTalk (atp1) インスタンス
AquesTalk atp1(AQTK_I2C_ADDR); // デフォルトI2Cアドレス(0x2E)

// ------------------------------------------------------------
// VD[5:0] = 0 用の長文メッセージテーブル (PROGMEM)
// ------------------------------------------------------------
const char long_text_0[] PROGMEM = "yosen/suta'-todesu.";

const char * const long_text_table[] PROGMEM = {
  long_text_0,
};

int longTextIndex = 0; // 長文メッセージのカウンタ

// ---------- Pins ----------
#define CLK_PIN 9 // TEMPO CLOCK 出力ピン (Timer1 OC1A)

const int PIN_S0   = A0;   // CHA
const int PIN_S1   = A1;   // CHB
const int PIN_S2   = A2;   // CHC
const int PIN_G    = A3;   // CHD = /G
const int PIN_D    = 8;    // GATE = D
const int PIN_ATP_RST = 13; // *ATP_RST

const uint8_t V_CH = 8;
const uint8_t V_Q  = V_CH - 1;

// ---------- VD input ----------
const int PIN_VD0 = 2;
const int PIN_VD1 = 3;
const int PIN_VD2 = 4;
const int PIN_VD3 = 5;
const int PIN_VD4 = 6;
const int PIN_VD5 = 7;

// ---------- Event queue ----------
enum EventType : uint8_t {
  EVENT_Q_FALL = 0,
  EVENT_Q_RISE = 1
};

struct QEvent {
  uint8_t type;
  uint8_t q;
  uint8_t vd;
};

const uint8_t EVENT_QUEUE_SIZE = 32;
volatile QEvent eventQueue[EVENT_QUEUE_SIZE];
volatile uint8_t eventHead = 0;
volatile uint8_t eventTail = 0;

// ---------- LS259 state ----------
volatile uint8_t qLatch = 0;

// ---------- Clock Variables ----------
float bpm = 120.0;

// ------------------------------------------------------------
// LS259 / VD 処理関数
// ------------------------------------------------------------
static inline uint8_t readVD() {
  return (uint8_t)((PIND >> 2) & 0x3F);
}

static inline uint8_t calculateQ(uint8_t s0, uint8_t s1, uint8_t s2, uint8_t g, uint8_t d) {
  uint8_t q = qLatch;
  if (!g) {
    uint8_t address = s0 | (s1 << 1) | (s2 << 2);
    if (d) q |= (uint8_t)(1u << address);
    else   q &= (uint8_t)~(1u << address);
  }
  return q;
}

static inline void pushEventFromISR(uint8_t type, uint8_t q, uint8_t vd) {
  uint8_t next = (uint8_t)((eventHead + 1) % EVENT_QUEUE_SIZE);
  if (next == eventTail) return;
  eventQueue[eventHead].type = type;
  eventQueue[eventHead].q = q;
  eventQueue[eventHead].vd = vd;
  eventHead = next;
}

static inline void ls259ISR_fast() {
  uint8_t pc = PINC;
  uint8_t pb = PINB;
  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  uint8_t oldQ = qLatch;
  uint8_t newQ = calculateQ(s0, s1, s2, g, d);
  if (newQ == oldQ) return;

  qLatch = newQ;
  uint8_t falling = oldQ & (uint8_t)~newQ;
  uint8_t rising  = (uint8_t)~oldQ & newQ;

  if (falling) {
    uint8_t vd = readVD();
    for (uint8_t q = 0; q < 8; q++) {
      if (falling & (uint8_t)(1u << q)) pushEventFromISR(EVENT_Q_FALL, q, vd);
    }
  }

  if (rising) {
    for (uint8_t q = 0; q < 8; q++) {
      if (rising & (uint8_t)(1u << q)) pushEventFromISR(EVENT_Q_RISE, q, 0);
    }
  }
}

ISR(PCINT1_vect) { ls259ISR_fast(); }
ISR(PCINT0_vect) { ls259ISR_fast(); }

bool popEvent(QEvent &ev) {
  noInterrupts();
  if (eventTail == eventHead) {
    interrupts();
    return false;
  }
  ev.type = eventQueue[eventTail].type;
  ev.q    = eventQueue[eventTail].q;
  ev.vd   = eventQueue[eventTail].vd;
  eventTail = (uint8_t)((eventTail + 1) % EVENT_QUEUE_SIZE);
  interrupts();
  return true;
}

// ------------------------------------------------------------
// 長文発声処理 (VD[5:0] = 0)
// ------------------------------------------------------------
void startVoice(uint8_t q, uint8_t vd) {
  if (q != V_Q || vd > 63) return;

  // VD = 0 (000000): 長文メッセージを順番に音声出力
  if (vd == 0) {
    atp1.Break(); // 発音中ならBreak

    // PROGMEMから長文文字列のポインタを取得
    const char *ptr = (const char *)pgm_read_word(&long_text_table[longTextIndex]);

    atp1.SetPitch(0x0);
    atp1.SetAccent(0xff);
    atp1.SetSpeed(130);
    Serial.println("speak begin");
    atp1.SyntheP(ptr); // PROGMEM上の文字列を直接送信
    Serial.println("speak end");
    atp1.SetAccent(0x00);
    atp1.SetSpeed(190); // 速度を190に復帰

    // インデックスを進める
    longTextIndex++;
    if (longTextIndex >= (int)(sizeof(long_text_table) / sizeof(long_text_table[0]))) {
      longTextIndex = 0;
    }
  }
}

// ------------------------------------------------------------
// BPM設定 & Timer1 更新処理
// ------------------------------------------------------------
void applyBPM(float newBpm){
  if(newBpm < 0.0) newBpm = 0.0;
  if(newBpm > 999.0) newBpm = 999.0;
  
  bpm = newBpm;

  if(bpm == 0.0){
    TCCR1B &= ~((1 << CS12) | (1 << CS11) | (1 << CS10));
    digitalWrite(CLK_PIN, LOW);
    Serial.println("BPM = 0 -> Clock STOP");
    return;
  }

  float freq = bpm / 2.5;

  const float F_CPU_F = 16000000.0;
  const float N = 64.0;

  float ocr_f = (F_CPU_F / (2.0 * N * freq)) - 1.0;
  if(ocr_f < 0) ocr_f = 0;
  if(ocr_f > 65535) ocr_f = 65535;

  uint16_t ocr = (uint16_t)(ocr_f + 0.5);

  OCR1A = ocr;

  TCCR1B &= ~((1 << CS12) | (1 << CS11) | (1 << CS10));
  TCCR1B |= (1 << CS11) | (1 << CS10);

  Serial.print("BPM updated: ");
  Serial.print(bpm, 1);
  Serial.print("  Tempo Clock Freq: ");
  Serial.print(freq, 2);
  Serial.println(" Hz");
}

// ------------------------------------------------------------
// setup()
// ------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(100);

  // ピン設定
  pinMode(CLK_PIN, OUTPUT);
  digitalWrite(CLK_PIN, LOW);

  pinMode(PIN_ATP_RST, OUTPUT);
  digitalWrite(PIN_ATP_RST, HIGH);

  pinMode(PIN_S0, INPUT);
  pinMode(PIN_S1, INPUT);
  pinMode(PIN_S2, INPUT);
  pinMode(PIN_G,  INPUT_PULLUP);
  pinMode(PIN_D,  INPUT_PULLUP);

  pinMode(PIN_VD0, INPUT);
  pinMode(PIN_VD1, INPUT);
  pinMode(PIN_VD2, INPUT);
  pinMode(PIN_VD3, INPUT);
  pinMode(PIN_VD4, INPUT);
  pinMode(PIN_VD5, INPUT);

  // I2C設定
  Wire.begin();
  Wire.setClock(100000L);

  atp1.SetAccent(0x00);
  atp1.SetSpeed(190);

  // Timer1 設定 (16MHz / プリスケーラ64 / CTC / OC1Aトグル)
  TCCR1A = 0;
  TCCR1B = 0;
  TCCR1B |= (1 << WGM12);
  TCCR1A |= (1 << COM1A0);

  // 初期BPM (120) 適用
  applyBPM(bpm);

  // ピン割り込み初期化
  uint8_t pc = PINC;
  uint8_t pb = PINB;
  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  qLatch = calculateQ(s0, s1, s2, g, d);

  PCICR |= _BV(PCIE1);
  PCMSK1 |= _BV(PCINT8) | _BV(PCINT9) | _BV(PCINT10) | _BV(PCINT11);

  PCICR |= _BV(PCIE0);
  PCMSK0 |= _BV(PCINT0);

  (void)PINC;
  (void)PINB;

  Serial.println("--- VOCALUINO4CMU Ready ---");
}

// ------------------------------------------------------------
// loop()
// ------------------------------------------------------------
void loop() {
  // 1. USBシリアルからのBPM変更入力の受け取り
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      float newBpm = input.toFloat();
      applyBPM(newBpm);
    }
  }

  // 2. LS259イベントキューの処理（VD[5:0]=0 の発声）
  QEvent ev;
  while (popEvent(ev)) {
Serial.print("EV type="); Serial.print(ev.type);
Serial.print(" q="); Serial.print(ev.q);
Serial.print(" vd="); Serial.println(ev.vd);
    if (ev.type == EVENT_Q_FALL) {
      startVoice(ev.q, ev.vd);
    }
  }
}
