@echo off
chcp 65001 >nul
echo.
echo ═══════════════════════════════════════════════════════════════
echo   COMPILADOR AUTOMÁTICO - SIMPLE BRIDGE EA
echo ═══════════════════════════════════════════════════════════════
echo.

REM Ruta del MetaEditor
set "METAEDITOR=C:\Program Files\MetaTrader 5\metaeditor64.exe"
set "EA_SOURCE=C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Simple_Bridge_EA.mq5"

echo 📝 Verificando MetaEditor...
if not exist "%METAEDITOR%" (
    echo ❌ MetaEditor no encontrado en la ubicación predeterminada
    echo    Compila manualmente: Abre MetaEditor, abre el archivo y presiona F7
    pause
    exit /b 1
)

echo ✅ MetaEditor encontrado
echo.
echo 🔨 Compilando Simple_Bridge_EA.mq5...
echo.

REM Intentar compilar
"%METAEDITOR%" /compile:"%EA_SOURCE%" /log

echo.
echo ═══════════════════════════════════════════════════════════════
echo   COMPILACIÓN COMPLETADA
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📝 PRÓXIMOS PASOS:
echo.
echo 1. Verifica en MetaEditor que no haya errores
echo 2. En MT5, QUITA el EA del gráfico (clic derecho → Expert list → Remove)
echo 3. ARRASTRA nuevamente Simple_Bridge_EA.ex5 al gráfico
echo 4. Acepta permisos (Allow algo trading)
echo 5. Verifica el icono en la esquina del gráfico
echo 6. Revisa logs en pestaña "Experts" - debe decir "Intervalo de chequeo: 100ms"
echo.
pause
