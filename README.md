# TGmusicBot

TGmusicBot es un bot de Discord que reproduce música desde YouTube en canales de voz.

Asegurate de instalar los modulos necesarios ejecutando el siguiente comando:

```shell
pip install -r requirements.txt
```
Asi de como tambien tener instalado FFmpeg
https://ffmpeg.org

Configuración

Antes de ejecutar el bot, asegúrate de haber configurado las siguientes variables de entorno en un archivo .env en el directorio raíz del proyecto:

BOT_TOKEN: El token del bot de Discord.

API_KEY: La clave de la API de YouTube.

Uso

Invita al bot a tu servidor de Discord.

Ejecuta el bot utilizando el siguiente comando:
```shell
python bot.py
```

Únete a un canal de voz en tu servidor de Discord.

Usa el prefijo . seguido de los comandos disponibles para controlar la reproducción de música:

.play <consulta>: Busca y reproduce una canción de YouTube.

.play <enlace de playlist>: Añade una playlist de YouTube a la cola de reproducción.

.skip: Omitir la canción actual

.queue: Muestra la lista de reproducción actual.

.shuffle: Mezcla la lista de reproducción actual.

.join: Hace que el bot se una al canal de voz en el que te encuentras.

¡Disfruta de la música con TGmusicBot en tu servidor de Discord!
