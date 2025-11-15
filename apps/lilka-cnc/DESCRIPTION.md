# Lilka CNC

Кастомна прошивка для консолі Лілка [https://github.com/and3rson/lilka](https://github.com/and3rson/lilka) щоб керувати CNC на базі GRBL прошивок.

Custom firmware for Lilka console to control CNC machines based on GRBL firmware.

## Можливості

Дана прошивка дозволяє:

- ✅ Ручне керування по X, Y осям
- Відкриття файлу з sdcard та запуск
- Статус GRBL контроллера та відображення помилки
- Зупинка, пауза та відновлення роботи

## Підключення

Маючи grbl плату підключити до пінів

Якщо плата використовує більше ніж 3.3v потрібно використовувати перетворювач логічних рівнів (наприклад [https://arduino.ua/prod1141-two-channel-iic-i2c-logic-level-converter](https://arduino.ua/prod1141-two-channel-iic-i2c-logic-level-converter) ~16грн)

| Lilka | GRBL |
|-------|------|
| 3v3 | не підключати, якщо Лілка має своє живлення через usb або батарею |
| RX | TX |
| TX | RX |
| GND | GND |


## Запустити

Завантажити .bin та .elf на карту, та запускати напряму з карти

## Використовується

Використовується бібліотека [ESP32-GRBL-Parser](https://github.com/shah253kt/ESP32-GRBL-Parser)
