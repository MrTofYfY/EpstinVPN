#!/bin/sh
set -e

# Ссылка на файл будет здесь (заменишь потом)
URL="URL_К_ТВОЕМУ_БИНАРНИКУ"

echo "Установка Goosembler..."

# Определяем папку для установки
if [ -n "$PREFIX" ]; then
    INSTALL_DIR="$PREFIX/bin" # Для Termux
else
    INSTALL_DIR="/usr/local/bin" # Для Linux/macOS
fi

# Скачивание
curl -L "$URL" -o /tmp/gsm
chmod +x /tmp/gsm

# Установка
echo "Перемещение в $INSTALL_DIR..."
sudo mv /tmp/gsm "$INSTALL_DIR/gsm" || mv /tmp/gsm "$INSTALL_DIR/gsm"

echo "Goosembler успешно установлен! Введи 'gsm' для начала."
