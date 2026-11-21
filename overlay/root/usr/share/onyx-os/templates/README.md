# ONYX starter projects

Copy these projects to persistent storage before shutting down a live USB.

Python: `cd python`, `python3 -m venv .venv`, then `.venv/bin/python main.py`.

C++: `cmake -S cpp -B cpp/build -G Ninja`, `cmake --build cpp/build`, then `cpp/build/hello`.

ESP32: install Arduino IDE and Espressif's ESP32 board package using Obryx Forge's links. Open `esp32_serial/esp32_serial.ino`, select your exact board (ESP32, C3 and S3 require different targets), select its serial port, then Upload. Open Serial Monitor at 115200 baud. This example does not assume an LED pin or drive any external hardware.

List detected USB serial ports with `python3 -m serial.tools.list_ports -v`. Use a USB cable that supports data. Unplug/replug a board after changing permissions. Other adapters may need additional udev rules or dialout membership.

The included host C++ compiler builds PC programs. ESP32 firmware needs the board-specific Arduino, ESP-IDF or PlatformIO toolchain. They are optional downloads, not preinstalled.
