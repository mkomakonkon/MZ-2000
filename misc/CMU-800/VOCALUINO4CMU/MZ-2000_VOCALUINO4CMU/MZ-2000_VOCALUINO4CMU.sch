EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "MZ-2000_CMU800"
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Connector_Generic:Conn_02x22_Row_Letter_First J1
U 1 1 627EE89C
P 2850 2700
F 0 "J1" H 2900 3850 50  0000 C CNN
F 1 "Conn_02x22_Row_Letter_First" H 2050 4450 50  0000 C CNN
F 2 "mz-2000:BUS_MZ2000" H 2850 2700 50  0001 C CNN
F 3 "~" H 2850 2700 50  0001 C CNN
	1    2850 2700
	1    0    0    -1  
$EndComp
Wire Wire Line
	2650 1800 2400 1800
Wire Wire Line
	2650 1900 2400 1900
Wire Wire Line
	2650 2000 2400 2000
Wire Wire Line
	3150 1800 3400 1800
Text Label 2450 1800 0    50   ~ 0
D2
Text Label 2450 1900 0    50   ~ 0
D1
Text Label 2450 2000 0    50   ~ 0
D0
Text Label 2450 2200 0    50   ~ 0
A15
Text Label 2450 2300 0    50   ~ 0
A14
Text Label 2450 2400 0    50   ~ 0
A13
Text Label 2450 2500 0    50   ~ 0
A12
Text Label 2450 2600 0    50   ~ 0
A11
Text Label 2450 2700 0    50   ~ 0
A10
Text Label 2450 2800 0    50   ~ 0
A9
Text Label 2450 2900 0    50   ~ 0
A8
Text Label 2450 3000 0    50   ~ 0
A7
Text Label 2450 3100 0    50   ~ 0
A6
Text Label 2450 3200 0    50   ~ 0
A5
Text Label 2450 3300 0    50   ~ 0
A4
Text Label 2450 3400 0    50   ~ 0
A3
Text Label 2450 3500 0    50   ~ 0
A2
Text Label 2450 3600 0    50   ~ 0
A1
Text Label 2450 3700 0    50   ~ 0
A0
Text Label 3150 3700 0    50   ~ 0
~MNI
Text Label 3150 3600 0    50   ~ 0
~EXWAIT
Text Label 3150 3500 0    50   ~ 0
~EXINT
Text Label 3150 3300 0    50   ~ 0
RESET
Text Label 3150 3200 0    50   ~ 0
IE0
Text Label 3150 3100 0    50   ~ 0
IE1
Text Label 3150 3000 0    50   ~ 0
~HALT
Text Label 3150 2800 0    50   ~ 0
~MREQ
Text Label 3150 2700 0    50   ~ 0
~IOREQ
Text Label 3150 2600 0    50   ~ 0
~RD
Text Label 3150 2500 0    50   ~ 0
~WR
Text Label 3150 2400 0    50   ~ 0
~M1
Text Label 3150 2300 0    50   ~ 0
phi
Text Label 3150 2200 0    50   ~ 0
D7
Text Label 3150 2100 0    50   ~ 0
D6
Text Label 3150 2000 0    50   ~ 0
D5
Text Label 3150 1900 0    50   ~ 0
D4
Text Label 3150 1800 0    50   ~ 0
D3
Wire Wire Line
	2650 2200 2400 2200
Wire Wire Line
	2650 2300 2400 2300
Wire Wire Line
	2650 2400 2400 2400
Wire Wire Line
	2650 2500 2400 2500
Wire Wire Line
	2650 2600 2400 2600
Wire Wire Line
	2650 2700 2400 2700
Wire Wire Line
	2650 2800 2400 2800
Wire Wire Line
	2650 2900 2400 2900
Wire Wire Line
	2650 3000 2400 3000
Wire Wire Line
	2650 3100 2400 3100
Wire Wire Line
	2650 3200 2400 3200
Wire Wire Line
	2650 3300 2400 3300
Wire Wire Line
	2650 3400 2400 3400
Wire Wire Line
	2650 3500 2400 3500
Wire Wire Line
	2650 3600 2400 3600
Wire Wire Line
	2650 3700 2400 3700
Wire Wire Line
	3150 1900 3400 1900
Wire Wire Line
	3150 2000 3400 2000
Wire Wire Line
	3150 2100 3400 2100
Wire Wire Line
	3150 2200 3400 2200
Wire Wire Line
	3150 2300 3400 2300
Wire Wire Line
	3150 2400 3400 2400
Wire Wire Line
	3150 2500 3400 2500
Wire Wire Line
	3150 2600 3400 2600
Wire Wire Line
	3150 2700 3400 2700
Wire Wire Line
	3150 2800 3400 2800
Wire Wire Line
	3150 3000 3400 3000
Wire Wire Line
	3150 3100 3400 3100
Wire Wire Line
	3150 3200 3400 3200
Wire Wire Line
	3150 3300 3400 3300
Wire Wire Line
	3150 3400 3400 3400
Wire Wire Line
	3150 3500 3400 3500
Wire Wire Line
	3150 3600 3400 3600
Wire Wire Line
	3150 3700 3400 3700
Text Label 3150 3400 0    50   ~ 0
~EXRESET
$Comp
L power:GND #PWR?
U 1 1 636B8114
P 2450 3950
AR Path="/6274F952/636B8114" Ref="#PWR?"  Part="1" 
AR Path="/636B8114" Ref="#PWR02"  Part="1" 
AR Path="/636550FF/636B8114" Ref="#PWR?"  Part="1" 
F 0 "#PWR02" H 2450 3700 50  0001 C CNN
F 1 "GND" H 2455 3777 50  0000 C CNN
F 2 "" H 2450 3950 50  0001 C CNN
F 3 "" H 2450 3950 50  0001 C CNN
	1    2450 3950
	1    0    0    -1  
$EndComp
Wire Wire Line
	2450 3950 2450 3800
Wire Wire Line
	2450 3800 2650 3800
Wire Wire Line
	3550 3800 3150 3800
$Comp
L power:PWR_FLAG #FLG?
U 1 1 636B8121
P 2950 4200
AR Path="/636550FF/636B8121" Ref="#FLG?"  Part="1" 
AR Path="/636B8121" Ref="#FLG01"  Part="1" 
F 0 "#FLG01" H 2950 4275 50  0001 C CNN
F 1 "PWR_FLAG" H 2950 4373 50  0000 C CNN
F 2 "" H 2950 4200 50  0001 C CNN
F 3 "~" H 2950 4200 50  0001 C CNN
	1    2950 4200
	1    0    0    -1  
$EndComp
Wire Wire Line
	3550 4300 2950 4300
Wire Wire Line
	2950 4300 2950 4200
Wire Wire Line
	3150 2900 3550 2900
Wire Wire Line
	3550 2900 3550 3800
Connection ~ 3550 3800
$Comp
L power:+5V #PWR?
U 1 1 636B8140
P 2450 1300
AR Path="/6274F952/636B8140" Ref="#PWR?"  Part="1" 
AR Path="/636B8140" Ref="#PWR01"  Part="1" 
AR Path="/636550FF/636B8140" Ref="#PWR?"  Part="1" 
F 0 "#PWR01" H 2450 1150 50  0001 C CNN
F 1 "+5V" H 2465 1473 50  0000 C CNN
F 2 "" H 2450 1300 50  0001 C CNN
F 3 "" H 2450 1300 50  0001 C CNN
	1    2450 1300
	1    0    0    -1  
$EndComp
Wire Wire Line
	2450 1700 2650 1700
$Comp
L power:PWR_FLAG #FLG?
U 1 1 636B814C
P 3400 1300
AR Path="/636550FF/636B814C" Ref="#FLG?"  Part="1" 
AR Path="/636B814C" Ref="#FLG02"  Part="1" 
F 0 "#FLG02" H 3400 1375 50  0001 C CNN
F 1 "PWR_FLAG" H 3400 1473 50  0000 C CNN
F 2 "" H 3400 1300 50  0001 C CNN
F 3 "~" H 3400 1300 50  0001 C CNN
	1    3400 1300
	1    0    0    -1  
$EndComp
Text Label 2450 1700 0    50   ~ 0
+5V
Text Label 2500 2100 0    50   ~ 0
GND
Text Label 2500 3800 0    50   ~ 0
GND
Text Label 3150 1700 0    50   ~ 0
+5V
Text Label 3150 2900 0    50   ~ 0
GND
Text Label 3150 3800 0    50   ~ 0
GND
Wire Wire Line
	3150 1700 3400 1700
NoConn ~ 3400 3100
NoConn ~ 3400 3000
NoConn ~ 3400 3200
NoConn ~ 3400 3400
NoConn ~ 3400 3500
NoConn ~ 3400 3600
NoConn ~ 3400 3700
NoConn ~ 2400 2200
NoConn ~ 2400 2300
NoConn ~ 2400 2400
NoConn ~ 2400 2500
NoConn ~ 2400 2600
NoConn ~ 2400 2700
NoConn ~ 2400 2800
NoConn ~ 2400 2900
NoConn ~ 3400 2800
NoConn ~ 3400 2300
NoConn ~ 3400 2400
$Comp
L Connector_Generic:Conn_02x25_Odd_Even J2
U 1 1 68F77FF1
P 5000 2900
F 0 "J2" H 5050 4317 50  0000 C CNN
F 1 "Conn_02x25_Odd_Even" H 5050 4226 50  0000 C CNN
F 2 "MZ-2000_SD_3_2:BUS_50Pin" H 5000 2900 50  0001 C CNN
F 3 "~" H 5000 2900 50  0001 C CNN
	1    5000 2900
	1    0    0    -1  
$EndComp
NoConn ~ 3400 3300
Text Label 4600 3300 0    50   ~ 0
A7
Text Label 4600 3200 0    50   ~ 0
A6
Text Label 4600 3100 0    50   ~ 0
A5
Text Label 4600 3000 0    50   ~ 0
A4
Text Label 4600 2900 0    50   ~ 0
A3
Text Label 4600 2800 0    50   ~ 0
A2
Text Label 4600 2700 0    50   ~ 0
A1
Text Label 4600 2600 0    50   ~ 0
A0
Wire Wire Line
	4800 3300 4550 3300
Wire Wire Line
	4800 3200 4550 3200
Wire Wire Line
	4800 3100 4550 3100
Wire Wire Line
	4800 3000 4550 3000
Wire Wire Line
	4800 2900 4550 2900
Wire Wire Line
	4800 2800 4550 2800
Wire Wire Line
	4800 2700 4550 2700
Wire Wire Line
	4800 2600 4550 2600
Wire Wire Line
	4550 2100 4800 2100
Text Label 4550 2500 0    50   ~ 0
D7
Text Label 4550 2400 0    50   ~ 0
D6
Text Label 4550 2300 0    50   ~ 0
D5
Text Label 4550 2200 0    50   ~ 0
D4
Text Label 4550 2100 0    50   ~ 0
D3
Wire Wire Line
	4550 2200 4800 2200
Wire Wire Line
	4550 2300 4800 2300
Wire Wire Line
	4550 2400 4800 2400
Wire Wire Line
	4550 2500 4800 2500
Wire Wire Line
	4550 2000 4800 2000
Wire Wire Line
	4550 1900 4800 1900
Wire Wire Line
	4550 1800 4800 1800
Text Label 4650 2000 2    50   ~ 0
D2
Text Label 4650 1900 2    50   ~ 0
D1
Text Label 4650 1800 2    50   ~ 0
D0
Wire Wire Line
	5550 4000 5300 4000
Text Label 5550 4000 2    50   ~ 0
GND
Text Label 4550 3700 0    50   ~ 0
~IOREQ
Wire Wire Line
	4550 3700 4800 3700
Text Label 4550 3400 0    50   ~ 0
~RD
Text Label 4550 3500 0    50   ~ 0
~WR
Wire Wire Line
	4550 3500 4800 3500
Wire Wire Line
	4550 3400 4800 3400
NoConn ~ 4800 1700
NoConn ~ 5300 1700
NoConn ~ 5300 1800
NoConn ~ 5300 1900
NoConn ~ 5300 2000
NoConn ~ 5300 2100
NoConn ~ 5300 2200
NoConn ~ 5300 2300
NoConn ~ 5300 2400
NoConn ~ 5300 2500
NoConn ~ 5300 2600
NoConn ~ 5300 2700
NoConn ~ 5300 2800
NoConn ~ 5300 2900
NoConn ~ 5300 3000
NoConn ~ 5300 3100
NoConn ~ 5300 3200
NoConn ~ 5300 3400
NoConn ~ 5300 3500
NoConn ~ 5300 3600
NoConn ~ 5300 3700
NoConn ~ 5300 3800
NoConn ~ 5300 3900
NoConn ~ 5300 4100
NoConn ~ 4800 4100
NoConn ~ 4800 4000
NoConn ~ 4800 3900
NoConn ~ 4800 3800
NoConn ~ 4800 3600
Wire Wire Line
	2450 1300 2450 1700
Wire Wire Line
	3400 1300 3400 1700
Wire Wire Line
	3550 3800 3550 4300
Wire Wire Line
	2650 2100 2400 2100
$EndSCHEMATC
