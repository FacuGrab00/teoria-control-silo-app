#!/bin/bash

GPIO=17

# Configurar como salida y nivel bajo
raspi-gpio set $GPIO op dl

for i in {1..3}
do
    echo "Encendiendo relé ($i)..."
    raspi-gpio set $GPIO dh
    sleep 3

    echo "Apagando relé ($i)..."
    raspi-gpio set $GPIO dl
    sleep 3
done

echo "Prueba finalizada."
