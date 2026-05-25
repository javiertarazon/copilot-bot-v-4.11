# Validación canónica XAUUSD

Este repositorio solo promueve versiones del bot XAUUSD siguiendo este orden:

1. **Entrenamiento**
2. **Validación**
3. **Prueba final**
4. **Sandbox/demo en vivo**

## Reglas

- Ninguna versión puede pasar a `--live-mt5` si no completó entrenamiento, validación y prueba final.
- Ninguna versión puede pasar a cuenta real si no completó además sandbox/demo.
- El reporte oficial se consulta con:

```bash
python /tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py --validation-report
```

## Estado inicial

El archivo `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/config/config.yaml` arranca con todas las etapas en `false`.
Cada promoción debe actualizar explícitamente ese estado antes de habilitar trading demo o real.
