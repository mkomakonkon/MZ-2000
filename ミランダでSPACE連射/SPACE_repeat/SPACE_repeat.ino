/*
MZ-2000のSPACEキーを連打するスケッチ。
初め1秒間に16連打しようと思ったけど、PC側の処理と競合するようでうまく動作しなかった。
1秒間に5連打にして、念のため毎回Keyboard.begin();を呼び出すようにしたら
いい感じに連射できた。
SPACEは文字送信ではなく、SPACEのASCIIコードでpressする必要あり。

【接続】
┌Arduino ┐
│Leonard │　　┌セルフロック┐
│    GND ├──┤スイッチ　　│
│    D13 ├──┤　　　　　　│
│     5V ├──┤　　　　　　│
└────┘　　└──────┘
　　　　　　　 5V-D13ショート時にON
*/

#include "Keyboard.h"

// set pin numbers for the switch:
#define REP_SW 13

void setup() {
  // initialize the pinmode:
  pinMode(REP_SW, INPUT);
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);
  // initialize control over the keyboard:
  Keyboard.begin();
}

void loop() {
  // check switch:
  if (digitalRead(REP_SW) == HIGH) {
    Keyboard.begin();
      Keyboard.press(32);         // push SPACE
      digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
      delay(100);  //5times/s
      Keyboard.release(32);         // release SPACE
    Keyboard.end();
      delay(100);  //5times/s
  } else {
  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
  }
}
