#include <MIDI.h>

// 標準のハードウェアシリアル（TXピン: D1）を使用してMIDIを出力 (31250bps)
MIDI_CREATE_DEFAULT_INSTANCE();

// ---------- LS259 input (メロディ/コード用: CH1〜CH8 = Q0〜Q7) ----------
const int PIN_S0   = A0;   // CHA
const int PIN_S1   = A1;   // CHB
const int PIN_S2   = A2;   // CHC
const int PIN_G    = A3;   // CHD = /G
const int PIN_D    = 8;    // GATE = D

// ---------- VD input ----------
const int PIN_VD0 = 2;
const int PIN_VD1 = 3;
const int PIN_VD2 = 4;
const int PIN_VD3 = 5;
const int PIN_VD4 = 6;
const int PIN_VD5 = 7;

// ---------- ドラム入力ピン・ノート設定 (ピンアサイン反映) ----------
// インデックス順: [0]=Y(D9), [1]=H(D10), [2]=L(D11), [3]=S(D12), [4]=B(D13), [5]=C(A6), [6]=O(A7)
const uint8_t DRUM_PINS[7]  = { 9,  10, 11, 12, 13, A6, A7 };
//const uint8_t DRUM_NOTES[7] = { 49, 48, 41, 38, 35, 42, 46 }; // Y, H, L, S, B, C, O(旧版)
const uint8_t DRUM_NOTES[7] = { 42, 46, 35, 38, 41, 48, 49   }; // C, O, B, S, L, H, Y 
bool prevDrumState[7]       = { HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH };

// ---------- チャンネル初期設定 (メロディCH1〜CH8) ----------
// 構成: { MIDIチャンネル(1〜16), GM楽器番号(0〜127), ボリューム(0〜127) }
struct ChannelConfig {
  uint8_t midiChannel;
  uint8_t gmInstrument; 
  uint8_t volume;
};

//ここでMIDI機器の設定をしてください。出力CH,楽器、ボリュームを設定可能
ChannelConfig channelConfigs[8] = {
  { 1, 81, 127 },  // CH1: MIDI-CH 1, 楽器番号 80 (Lead 1), ボリューム 100
  { 2, 1,  127 },  // CH2: MIDI-CH 2, 楽器番号 33 (Electric Bass), ボリューム 100
  { 3, 1,  127 },  // CH3: MIDI-CH 3, 楽器番号 16 (Organ), ボリューム 100
  { 3, 1,  127 },  // CH4: MIDI-CH 4, 楽器番号 81 (Lead 2), ボリューム 100
  { 3, 1,  127 },  // CH5: MIDI-CH 5, 楽器番号 11 (Voice), ボリューム 100
  { 3, 1,  127 },  // CH6: MIDI-CH 6, 楽器番号 90 (Synth Pad), ボリューム 100
  { 3, 1,  127 },  // CH7: MIDI-CH 7, 楽器番号 15 (Bell), ボリューム 100
  { 10, 0, 127 }   // CH8: MIDI-CH 8, 楽器番号 0 (Piano等), ボリューム 100
};

// ---------- ドラム設定 (CH10) ----------
const uint8_t DRUM_MIDI_CHANNEL = 10;
const uint8_t DRUM_VOLUME       = 127; // ドラムの初期ボリューム (0〜127)

// ---------- event queue (メロディ用) ----------
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

// 起動直後の初回イベント確実化のためのフラグ
volatile bool isFirstEventPending = true;

// 8チャンネル分（Q0〜Q7 = CH1〜CH8）の発音状態管理
struct ChannelState {
  bool isPlaying;
  uint8_t activeNote;
};

ChannelState chState[8] = {
  {false, 0}, {false, 0}, {false, 0}, {false, 0},
  {false, 0}, {false, 0}, {false, 0}, {false, 0}
};

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
    return;
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

  if (newQ == oldQ && !isFirstEventPending) {
    return;
  }

  qLatch = newQ;

  uint8_t falling = oldQ & (uint8_t)~newQ;
  uint8_t rising  = (uint8_t)~oldQ & newQ;

  // 起動直後の初回イベントで万が一差分が出なかった場合の救済措置
  if (isFirstEventPending) {
    isFirstEventPending = false;
    uint8_t vd = readVD();
    // 最初に変化した（またはアクティブになった）アドレスを特定して強制プッシュ
    uint8_t address = s0 | (s1 << 1) | (s2 << 2);
    if (!g && d) {
      pushEventFromISR(EVENT_Q_FALL, address, vd);
      return;
    }
  }

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
// メロディ Note On 処理 (CH1〜CH8 = Q0〜Q7)
// ------------------------------------------------------------
void startVoice(uint8_t q, uint8_t vd)
{
  if (q > 7) {
    return;
  }

  if (vd > 63) {
    return;
  }

  uint8_t midiCh = channelConfigs[q].midiChannel;

  if (chState[q].isPlaying) {
    MIDI.sendNoteOff(chState[q].activeNote, 0, midiCh);
  }

  uint8_t noteNo = (uint8_t)(vd + 24);

  MIDI.sendNoteOn(noteNo, 127, midiCh);

  chState[q].activeNote = noteNo;
  chState[q].isPlaying = true;
}

// ------------------------------------------------------------
// メロディ Note Off 処理 (CH1〜CH8 = Q0〜Q7)
// ------------------------------------------------------------
void stopVoice(uint8_t q)
{
  if (q > 7) {
    return;
  }

  uint8_t midiCh = channelConfigs[q].midiChannel;

  if (chState[q].isPlaying) {
    MIDI.sendNoteOff(chState[q].activeNote, 0, midiCh);
    chState[q].isPlaying = false;
  }
}

// ------------------------------------------------------------
// ドラム信号の読み取りとMIDI変換処理 (立ち下がりエッジ検知)
// ------------------------------------------------------------
void checkDrums()
{
  for (uint8_t i = 0; i < 7; i++) {
    bool currentState = digitalRead(DRUM_PINS[i]);
    
    // 立ち下がり（HIGH -> LOW）を検知してドラムトリガーを発信
    if (prevDrumState[i] == HIGH && currentState == LOW) {
      MIDI.sendNoteOn(DRUM_NOTES[i], 127, DRUM_MIDI_CHANNEL);
      MIDI.sendNoteOff(DRUM_NOTES[i], 0, DRUM_MIDI_CHANNEL);
    }
    prevDrumState[i] = currentState;
  }
}

// ------------------------------------------------------------
// setup
// ------------------------------------------------------------
void setup()
{
  MIDI.begin(MIDI_CHANNEL_OFF);

  // 起動時に全てのMIDIチャンネル (1〜16) へ鳴りっぱなし対策を実施
  for (uint8_t ch = 1; ch <= 16; ch++) {
    MIDI.sendControlChange(123, 0, ch); // All Notes Off
    MIDI.sendControlChange(120, 0, ch); // All Sound Off
  }

  // 各CH (CH1〜CH8) の初期設定（プログラムチェンジ ＆ ボリューム送信）
  for (uint8_t i = 0; i < 8; i++) {
    MIDI.sendProgramChange(channelConfigs[i].gmInstrument, channelConfigs[i].midiChannel);
    MIDI.sendControlChange(7, channelConfigs[i].volume, channelConfigs[i].midiChannel);
  }

  // ドラム (CH10) の初期ボリューム送信
  MIDI.sendControlChange(7, DRUM_VOLUME, DRUM_MIDI_CHANNEL);

  // LS259関連ピン
  pinMode(PIN_S0, INPUT);
  pinMode(PIN_S1, INPUT);
  pinMode(PIN_S2, INPUT);
  pinMode(PIN_G,  INPUT_PULLUP);
  pinMode(PIN_D,  INPUT_PULLUP);

  // VDピン
  pinMode(PIN_VD0, INPUT);
  pinMode(PIN_VD1, INPUT);
  pinMode(PIN_VD2, INPUT);
  pinMode(PIN_VD3, INPUT);
  pinMode(PIN_VD4, INPUT);
  pinMode(PIN_VD5, INPUT);

  // ドラム入力ピンの設定（全7本、内部プルアップ有効）
  for (uint8_t i = 0; i < 7; i++) {
    pinMode(DRUM_PINS[i], INPUT_PULLUP);
  }

  // LS259初期状態作成
  uint8_t pc = PINC;
  uint8_t pb = PINB;
  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  qLatch = calculateQ(s0, s1, s2, g, d);
  isFirstEventPending = true; // 起動直後の初回イベント待ち受けを有効化

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
  // 1. メロディ側のQイベント処理 (CH1〜CH8 = Q0〜Q7)
  QEvent ev;
  while (popEvent(ev)) {
    if (ev.type == EVENT_Q_FALL) {
      startVoice(ev.q, ev.vd);
    }
    else {
      stopVoice(ev.q);
    }
  }

  // 2. ドラム信号の監視・変換処理 (独立ピン7本)
  checkDrums();
}
