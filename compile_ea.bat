@echo off
		echo Compilando Simple_Bridge_EA...
		"C:\Program Files\MetaTrader 5\metaeditor64.exe" /compile:"C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Simple_Bridge_EA.mq5" /log
		if exist "C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Simple_Bridge_EA.ex5" (
		    echo [OK] Simple_Bridge_EA compilado exitosamente.
		) else (
		    echo [ERROR] No se pudo compilar Simple_Bridge_EA. Revisa el log.
		)
		pause
