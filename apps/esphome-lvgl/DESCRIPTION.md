# ESPHome LVGL для Lilka (в процесі)

ESPHome конфігурація для Lilka з підтримкою LVGL (LittlevGL) графічного фреймворку.

ESPHome configuration for Lilka with LVGL (LittlevGL) graphics framework support.

## Можливості

- ✅ Підтримка дисплея ST7789V (240x280, SPI)
- ✅ Інтеграція LVGL для графічного інтерфейсу
- ✅ Моніторинг батареї (напруга та рівень у відсотках)
- ✅ Підтримка всіх кнопок Lilka (Up, Down, Left, Right, A, B, C, D, Start, Select)
- ✅ Web-сервер для керування через браузер
- ✅ WiFi підключення з fallback hotspot
- ✅ OTA оновлення прошивки
- ✅ API для Home Assistant інтеграції

## Технічні деталі

### Апаратне забезпечення

- **Платформа**: ESP32-S3 DevKitC-1
- **Дисплей**: ST7789V (SPI)
  - DC: GPIO15
  - CS: GPIO7
  - CLK: GPIO18
  - MOSI: GPIO17
- **Живлення дисплея**: GPIO46
- **Батарея**: ADC GPIO3 (з множником 1.33)

### Кнопки

| Кнопка | GPIO |
|--------|------|
| Up | 38 |
| Down | 41 |
| Left | 39 |
| Right | 40 |
| A | 5 |
| B | 6 |
| C | 10 |
| D | 9 |
| Start | 4 |
| Select | 0 |

## LVGL інтерфейс

Базовий інтерфейс включає:
- Заголовок "Lilka LVGL"
- Індикатор рівня батареї з автооновленням кожні 5 секунд
- Центральний текст "LVGL Works!"

## Встановлення

1. Встановіть [ESPHome](https://esphome.io/)
2. Створіть файл `lilka.yaml` з конфігурацією
3. Налаштуйте WiFi credentials у `secrets.yaml`:
   ```yaml
   wifi_ssid: "YourWiFiName"
   wifi_password: "YourWiFiPassword"
   ```
4. Завантажте прошивку: `esphome run lilka.yaml`

## Конфігурація

Повна конфігурація доступна на [Pastebin](https://pastebin.com/aNXqw5bQ)

## Статус розробки

⚠️ **В процесі розробки** - Кнопки підключені, але LVGL дії для них ще не реалізовані.

## Автор

Свердлюк (sverdlyuk)
