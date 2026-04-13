#!/bin/sh
# Финальный установщик Goosembler

# Твой бинарник:
GSM_URL="https://github.com/MrTofYfY/EpstinVPN/raw/refs/heads/main/Linux/gsm"

echo "--- Установка Goosembler ---"

# Определяем папку
if [ -n "$PREFIX" ]; then
    INSTALL_DIR="$PREFIX/bin"
else
    INSTALL_DIR="/usr/local/bin"
fi

# Скачивание
echo "Скачивание Goosembler..."
curl -L "$GSM_URL" -o /tmp/gsm

# Делаем исполняемым
chmod +x /tmp/gsm

# Установка
echo "Перемещение в $INSTALL_DIR..."
if sudo mv /tmp/gsm "$INSTALL_DIR/gsm"; then
    echo "Успешно! Goosembler установлен."
    echo "Введи 'gsm' для начала работы."
else
    mv /tmp/gsm "$INSTALL_DIR/gsm"
    echo "Успешно! Goosembler установлен."
    echo "Введи 'gsm' для начала работы."
fi
