/*
============================================================
  BPM CLOCK GENERATOR (Serial Only Version)

【機能】
  ・USBシリアルを介したBPM設定
  ・D9ピンからハードウェアクロック出力 (Timer1 CTCモード, OC1Aトグル)

【クロック仕様】
  ・出力ピン：D9 (OC1A)
  ・周波数(Hz) = BPM / 2.5
  ・DUTY 50%

【使い方】
  1. Arduino IDEのシリアルモニタを開く（ボーレート: 115200bps）
  2. 変更したいBPMの数値（例: 120, 135.5）を入力して送信する
============================================================
*/

/* ---- Clock ---- */
#define CLK_PIN 9  // OC1A

float bpm = 120.0;

/* ===== BPM設定 & Timer1 更新 ===== */
void applyBPM(float newBpm){
  if(newBpm < 0.0) newBpm = 0.0;
  if(newBpm > 999.0) newBpm = 999.0;
  
  bpm = newBpm;

  /* ---- BPM=0 → クロック停止 ---- */
  if(bpm == 0.0){
    TCCR1B &= ~((1 << CS12) | (1 << CS11) | (1 << CS10));
    digitalWrite(CLK_PIN, LOW);
    Serial.println("BPM = 0 -> Clock STOP");
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
  Serial.print("BPM updated: ");
  Serial.print(bpm, 1);
  Serial.print("  Freq: ");
  Serial.print(freq, 2);
  Serial.println(" Hz");
}

/* ===== Setup ===== */
void setup(){
  Serial.begin(115200);
  delay(100);   // シリアル安定化待ち

  pinMode(CLK_PIN, OUTPUT);
  digitalWrite(CLK_PIN, LOW);

  /* ---- Timer1 設定（16MHz / 64 / CTC / OC1Aトグル） ---- */
  TCCR1A = 0;
  TCCR1B = 0;

  TCCR1B |= (1 << WGM12);               // CTCモード
  TCCR1A |= (1 << COM1A0);              // OC1Aトグル出力

  // 初期BPMの適用
  applyBPM(bpm);

  Serial.println("--- CMU-800 Serial Tempo Clock Generator Ready ---");
  Serial.print("Current BPM: ");
  Serial.println(bpm);
  Serial.println("Please type a new BPM and press Enter.");
}

/* ===== Loop ===== */
void loop(){
  // シリアルモニタからの入力を監視
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // 前後の空白や改行コードを削除
    
    if (input.length() > 0) {
      float newBpm = input.toFloat();
      applyBPM(newBpm);
    }
  }
}
