#include <MIDI.h>

// 標準のハードウェアシリアル（TXピン）を使用してMIDIを出力します（ボーレート31250bps）
MIDI_CREATE_DEFAULT_INSTANCE();

// ---------- LS259 input ----------
const int PIN_S0   = A0;   // CHA
const int PIN_S1   = A1;   // CHB
const int PIN_S2   = A2;   // CHC
const int PIN_G    = A3;   // CHD = /G
const int PIN_D    = 8;    // GATE = D

// 発音させるCHを1～8で指定
const uint8_t V_CH = 1;
const uint8_t V_Q  = V_CH - 1;

// ---------- VD input ----------
const int PIN_VD0 = 2;
const int PIN_VD1 = 3;
const int PIN_VD2 = 4;
const int PIN_VD3 = 5;
const int PIN_VD4 = 6;
const int PIN_VD5 = 7;

// ---------- event queue ----------
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

// 発音管理用（Note Offを確実に行うため）
uint8_t activeNote = 0;
bool isPlaying = false;
const uint8_t MIDI_CHANNEL = 1; // 使用するMIDIチャンネル (1〜16)

// ------------------------------------------------------------
// VD0～VD5を読む (0～63の6bit値)
// ------------------------------------------------------------
static inline uint8_t readVD()
{
  return (uint8_t)((PIND >> 2) & 0x3F);
}

// ------------------------------------------------------------
// 現在のLS259 Q状態を計算
// ------------------------------------------------------------
static inline uint8_t calculateQ(uint8_t s0,
                                 uint8_t s1,
                                 uint8_t s2,
                                 uint8_t g,
                                 uint8_t d)
{
  uint8_t q = qLatch;

  if (!g) {
    uint8_t address = s0 | (s1 << 1) | (s2 << 2);

    if (d) {
      q |= (uint8_t)(1u << address);
    } else {
      q &= (uint8_t)~(1u << address);
    }
  }

  return q;
}

// ------------------------------------------------------------
// イベントをキューへ追加 (ISRから呼び出し)
// ------------------------------------------------------------
static inline void pushEventFromISR(uint8_t type,
                                    uint8_t q,
                                    uint8_t vd)
{
  uint8_t next = (uint8_t)((eventHead + 1) % EVENT_QUEUE_SIZE);

  if (next == eventTail) {
    return; // キュー満杯時は破棄
  }

  eventQueue[eventHead].type = type;
  eventQueue[eventHead].q = q;
  eventQueue[eventHead].vd = vd;
  eventHead = next;
}

// ------------------------------------------------------------
// LS259入力変化割り込み
// ------------------------------------------------------------
static inline void ls259ISR_fast()
{
  uint8_t pc = PINC;
  uint8_t pb = PINB;

  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  uint8_t oldQ = qLatch;
  uint8_t newQ = calculateQ(s0, s1, s2, g, d);

  if (newQ == oldQ) {
    return;
  }

  qLatch = newQ;

  uint8_t falling = oldQ & (uint8_t)~newQ;
  uint8_t rising  = (uint8_t)~oldQ & newQ;

  if (falling) {
    uint8_t vd = readVD();
    for (uint8_t q = 0; q < 8; q++) {
      if (falling & (uint8_t)(1u << q)) {
        pushEventFromISR(EVENT_Q_FALL, q, vd);
      }
    }
  }

  if (rising) {
    for (uint8_t q = 0; q < 8; q++) {
      if (rising & (uint8_t)(1u << q)) {
        pushEventFromISR(EVENT_Q_RISE, q, 0);
      }
    }
  }
}

ISR(PCINT1_vect)
{
  ls259ISR_fast();
}

ISR(PCINT0_vect)
{
  ls259ISR_fast();
}

// ------------------------------------------------------------
// イベントを1件取り出す
// ------------------------------------------------------------
bool popEvent(QEvent &ev)
{
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
// MIDI Note On 処理
// ------------------------------------------------------------
void startVoice(uint8_t q, uint8_t vd)
{
  if (q != V_Q) {
    return;
  }

  if (vd > 63) {
    return;
  }

  // 前に鳴っている音があれば先にNote Offを送る
  if (isPlaying) {
    MIDI.sendNoteOff(activeNote, 0, MIDI_CHANNEL);
  }

  // VD (0〜63) からMIDIノート番号へ変換 (元コードのオフセット +36 を適用)
  uint8_t noteNo = (uint8_t)(vd + 36);

  MIDI.sendNoteOn(noteNo, 127, MIDI_CHANNEL);

  activeNote = noteNo;
  isPlaying = true;
}

// ------------------------------------------------------------
// MIDI Note Off 処理
// ------------------------------------------------------------
void stopVoice(uint8_t q)
{
  if (q != V_Q) {
    return;
  }

  if (isPlaying) {
    MIDI.sendNoteOff(activeNote, 0, MIDI_CHANNEL);
    isPlaying = false;
  }
}

// ------------------------------------------------------------
// setup
// ------------------------------------------------------------
void setup()
{
  // MIDIライブラリの開始
  MIDI.begin(MIDI_CHANNEL_OFF);

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

  // 現在の入力状態からLS259初期状態を作る
  uint8_t pc = PINC;
  uint8_t pb = PINB;
  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  qLatch = calculateQ(s0, s1, s2, g, d);

  // Pin Change Interrupt設定
  PCICR |= _BV(PCIE1);   // PORTC (A0〜A3)
  PCMSK1 |= _BV(PCINT8) | _BV(PCINT9) | _BV(PCINT10) | _BV(PCINT11);

  PCICR |= _BV(PCIE0);   // PORTB (D8)
  PCMSK0 |= _BV(PCINT0);

  (void)PINC;
  (void)PINB;
}

// ------------------------------------------------------------
// loop
// ------------------------------------------------------------
void loop()
{
  QEvent ev;

  while (popEvent(ev)) {
    if (ev.type == EVENT_Q_FALL) {
      startVoice(ev.q, ev.vd);
    }
    else {
      stopVoice(ev.q);
    }
  }
}
