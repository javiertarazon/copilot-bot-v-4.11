//+------------------------------------------------------------------+
//|                                      Simple_Bridge_EA.mq5         |
//|                                  Bot Trader Copilot v4.11         |
//|              Versión SIMPLE sin dependencias externas             |
//+------------------------------------------------------------------+
#property copyright "Bot Trader Copilot"
#property link      "https://github.com/copilot-bot"
#property version   "4.11"
#property strict
#property description "EA Bridge sin ZMQ - Usa archivos para comunicación"

//--- Incluir solo librerías nativas
#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//--- Parámetros de entrada
input int      InpMagicNumber = 20260129;        // Magic Number del bot
input int      InpCheckInterval = 100;           // Intervalo de chequeo (ms)
input bool     InpEnableTicks = true;            // Guardar ticks
input bool     InpDebugMode = false;             // Modo debug

//--- Objetos de trading
CTrade         trade;
CPositionInfo  positionInfo;
CSymbolInfo    symbolInfo;

//--- Directorios de comunicación
string CommandDir = "Bot_Commands\\";
string ResponseDir = "Bot_Responses\\";
string TicksDir = "Bot_Ticks\\";

//--- Variables de estado
bool isInitialized = false;
datetime lastTickTime = 0;
int commandCounter = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════════");
   Print("🔌 Simple Bridge EA v4.11 - Inicializando...");
   Print("═══════════════════════════════════════════════════════════════");
   
   //--- Configurar trading
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   trade.SetAsyncMode(false);
   
   //--- Crear archivos de estado
   CreateStateFiles();
   
   //--- Iniciar timer para procesar comandos activamente
   EventSetTimer(1);  // Cada 1 segundo
   
   isInitialized = true;
   Print("✅ Simple Bridge EA inicializado correctamente");
   Print("   Magic Number: ", InpMagicNumber);
   Print("   Modo: Comunicación por archivos");
   Print("   Intervalo de chequeo: ", InpCheckInterval, "ms");
   Print("═══════════════════════════════════════════════════════════════");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("🔌 Cerrando Simple Bridge EA...");
   Print("✅ Simple Bridge EA cerrado");
}

//+------------------------------------------------------------------+
//| Timer function                                                     |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!isInitialized) return;
   
   static int timer_count = 0;
   timer_count++;
   
   if(InpDebugMode && timer_count % 10 == 0)
   {
      Print("⏱️ Timer #", timer_count, " - Buscando comandos...");
   }
   
   //--- Procesar comandos pendientes
   ProcessCommands();
   
   //--- Actualizar archivo de estado
   CreateStateFiles();
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!isInitialized) return;
   
   //--- Procesar comandos pendientes
   ProcessCommands();
   
   //--- Guardar tick actual si está habilitado
   if(InpEnableTicks)
   {
      SaveCurrentTick();
   }
}

//+------------------------------------------------------------------+
//| Crea archivos de estado inicial                                   |
//+------------------------------------------------------------------+
void CreateStateFiles()
{
   //--- Crear archivo de heartbeat
   int handle = FileOpen("Bot_Status.txt", FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, "STATUS=READY\n");
      FileWriteString(handle, "TIME=" + TimeToString(TimeCurrent()) + "\n");
      FileWriteString(handle, "MAGIC=" + IntegerToString(InpMagicNumber) + "\n");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Procesa comandos de archivos                                      |
//| ESTRATEGIA FINAL: Intentar abrir directamente sin FileIsExist    |
//+------------------------------------------------------------------+
void ProcessCommands()
{
   //--- Archivo de comando activo (ÚNICO)
   string commandFile = "Bot_Commands\\ACTIVE_COMMAND.cmd";
   
   //--- Intentar abrir DIRECTAMENTE (sin FileIsExist que falla)
   int handle = FileOpen(commandFile, FILE_READ|FILE_TXT|FILE_COMMON);
   
   if(handle == INVALID_HANDLE)
   {
      //--- No hay comando pendiente (esto es normal)
      return;
   }
   
   //--- ¡Comando encontrado!
   if(InpDebugMode)
   {
      Print("📝 ¡COMANDO DETECTADO! Procesando...");
   }
   
   FileClose(handle);
   
   //--- Procesar comando
   ProcessCommandFile("ACTIVE_COMMAND.cmd");
   
   //--- Eliminar archivo procesado
   bool deleted = FileDelete(commandFile, FILE_COMMON);
   
   if(InpDebugMode)
   {
      Print("🗑️ Comando eliminado: ", deleted ? "SI" : "NO");
   }
   
   commandCounter++;
}

//+------------------------------------------------------------------+
//| Procesa un archivo de comando específico                          |
//+------------------------------------------------------------------+
void ProcessCommandFile(string filename)
{
   if(InpDebugMode)
   {
      Print("🔍 Intentando abrir: Bot_Commands\\", filename);
   }
   
   int handle = FileOpen("Bot_Commands\\" + filename, FILE_READ|FILE_TXT|FILE_COMMON);
   if(handle == INVALID_HANDLE)
   {
      int error = GetLastError();
      Print("❌ ERROR abriendo comando: ", error);
      return;
   }
   
   if(InpDebugMode)
   {
      Print("✅ Comando abierto correctamente");
   }
   
   string command = "";
   string action = "";
   string symbol = "";
   int orderType = -1;
   double volume = 0;
   double price = 0;
   double sl = 0;
   double tp = 0;
   ulong ticket = 0;
   int bars = 100;
   int timeframe = 15;
   double risk_percent = 1.0;
   double stop_distance = 50.0;
   double trailing_pct = 0.65;
   
   //--- Leer parámetros del archivo
   while(!FileIsEnding(handle))
   {
      string line = FileReadString(handle);
      if(StringLen(line) == 0) continue;
      
      string parts[];
      int count = StringSplit(line, '=', parts);
      if(count != 2) continue;
      
      string key = parts[0];
      string value = parts[1];
      
      if(key == "ACTION") action = value;
      else if(key == "SYMBOL") symbol = value;
      else if(key == "TYPE") orderType = (int)StringToInteger(value);
      else if(key == "VOLUME") volume = StringToDouble(value);
      else if(key == "PRICE") price = StringToDouble(value);
      else if(key == "SL") sl = StringToDouble(value);
      else if(key == "TP") tp = StringToDouble(value);
      else if(key == "TICKET") ticket = (ulong)StringToInteger(value);
      else if(key == "BARS") bars = (int)StringToInteger(value);
      else if(key == "TIMEFRAME") timeframe = (int)StringToInteger(value);
      else if(key == "RISK_PERCENT") risk_percent = StringToDouble(value);
      else if(key == "STOP_DISTANCE") stop_distance = StringToDouble(value);
      else if(key == "TRAILING_PCT") trailing_pct = StringToDouble(value);
   }
   
   FileClose(handle);
   
   //--- Ejecutar acción
   string response = "";
   
   if(action == "HEARTBEAT")
   {
      response = ProcessHeartbeat();
   }
   else if(action == "ORDER")
   {
      response = ProcessOrder(symbol, orderType, volume, price, sl, tp);
   }
   else if(action == "CLOSE")
   {
      response = ProcessClose(ticket, volume);
   }
   else if(action == "MODIFY")
   {
      response = ProcessModify(ticket, sl, tp);
   }
   else if(action == "GET_POSITIONS")
   {
      response = ProcessGetPositions(symbol);
   }
   else if(action == "ACCOUNT_INFO")
   {
      response = ProcessAccountInfo();
   }
   else if(action == "SYMBOL_INFO")
   {
      response = ProcessSymbolInfo(symbol);
   }
   else if(action == "HISTORICAL_DATA")
   {
      response = ProcessHistoricalData(symbol, timeframe, bars);
   }
   else if(action == "CALCULATE_LOT")
   {
      response = ProcessCalculateLot(symbol, risk_percent, stop_distance);
   }
   else if(action == "UPDATE_TRAILING")
   {
      response = ProcessUpdateTrailing(symbol, trailing_pct);
   }
   else
   {
      response = "STATUS=ERROR\nERROR=Unknown action: " + action + "\n";
   }
   
   //--- Guardar respuesta
   SaveResponse(filename, response);
}

//+------------------------------------------------------------------+
//| Procesa heartbeat                                                  |
//+------------------------------------------------------------------+
string ProcessHeartbeat()
{
   return "STATUS=OK\nTIME=" + IntegerToString(TimeCurrent()) + "\n";
}

//+------------------------------------------------------------------+
//| Procesa orden de trading                                           |
//+------------------------------------------------------------------+
string ProcessOrder(string symbol, int orderType, double volume, double price, double sl, double tp)
{
   //--- Validar símbolo
   if(!SymbolSelect(symbol, true))
   {
      return "STATUS=ERROR\nERROR=Symbol not found: " + symbol + "\n";
   }
   
   //--- Obtener precios actuales
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   //--- Determinar precio si es orden de mercado
   if(price == 0)
   {
      price = (orderType == 0) ? ask : bid;
   }
   
   //--- Ejecutar orden
   bool result = false;
   ulong ticket = 0;
   
   if(orderType == 0)  // BUY
   {
      result = trade.Buy(volume, symbol, 0, sl, tp, "BOT");
   }
   else if(orderType == 1)  // SELL
   {
      result = trade.Sell(volume, symbol, 0, sl, tp, "BOT");
   }
   
   //--- Retornar resultado
   if(result)
   {
      ticket = trade.ResultOrder();
      string resp = "STATUS=OK\n";
      resp += "TICKET=" + IntegerToString(ticket) + "\n";
      resp += "PRICE=" + DoubleToString(trade.ResultPrice(), 5) + "\n";
      resp += "VOLUME=" + DoubleToString(trade.ResultVolume(), 2) + "\n";
      return resp;
   }
   else
   {
      return "STATUS=ERROR\nERROR=Order failed: " + IntegerToString(trade.ResultRetcode()) + "\n";
   }
}

//+------------------------------------------------------------------+
//| Procesa cierre de posición                                         |
//+------------------------------------------------------------------+
string ProcessClose(ulong ticket, double volume)
{
   if(!PositionSelectByTicket(ticket))
   {
      return "STATUS=ERROR\nERROR=Position not found: " + IntegerToString(ticket) + "\n";
   }
   
   bool result;
   if(volume > 0)
      result = trade.PositionClosePartial(ticket, volume);
   else
      result = trade.PositionClose(ticket);
   
   if(result)
   {
      return "STATUS=OK\nTICKET=" + IntegerToString(ticket) + "\n";
   }
   else
   {
      return "STATUS=ERROR\nERROR=Close failed: " + IntegerToString(trade.ResultRetcode()) + "\n";
   }
}

//+------------------------------------------------------------------+
//| Procesa modificación de SL/TP                                      |
//+------------------------------------------------------------------+
string ProcessModify(ulong ticket, double sl, double tp)
{
   if(!PositionSelectByTicket(ticket))
   {
      return "STATUS=ERROR\nERROR=Position not found: " + IntegerToString(ticket) + "\n";
   }
   
   if(sl == 0) sl = PositionGetDouble(POSITION_SL);
   if(tp == 0) tp = PositionGetDouble(POSITION_TP);
   
   if(trade.PositionModify(ticket, sl, tp))
   {
      string resp = "STATUS=OK\n";
      resp += "TICKET=" + IntegerToString(ticket) + "\n";
      resp += "SL=" + DoubleToString(sl, 5) + "\n";
      resp += "TP=" + DoubleToString(tp, 5) + "\n";
      return resp;
   }
   else
   {
      return "STATUS=ERROR\nERROR=Modify failed: " + IntegerToString(trade.ResultRetcode()) + "\n";
   }
}

//+------------------------------------------------------------------+
//| Procesa solicitud de posiciones                                    |
//+------------------------------------------------------------------+
string ProcessGetPositions(string filterSymbol)
{
   string response = "STATUS=OK\n";
   int count = 0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(!positionInfo.SelectByIndex(i))
         continue;
      
      if(positionInfo.Magic() != InpMagicNumber)
         continue;
      
      if(filterSymbol != "" && positionInfo.Symbol() != filterSymbol)
         continue;
      
      response += "POS" + IntegerToString(count) + "_TICKET=" + IntegerToString(positionInfo.Ticket()) + "\n";
      response += "POS" + IntegerToString(count) + "_SYMBOL=" + positionInfo.Symbol() + "\n";
      response += "POS" + IntegerToString(count) + "_TYPE=" + IntegerToString(positionInfo.PositionType()) + "\n";
      response += "POS" + IntegerToString(count) + "_VOLUME=" + DoubleToString(positionInfo.Volume(), 2) + "\n";
      response += "POS" + IntegerToString(count) + "_OPEN_PRICE=" + DoubleToString(positionInfo.PriceOpen(), 5) + "\n";
      response += "POS" + IntegerToString(count) + "_SL=" + DoubleToString(positionInfo.StopLoss(), 5) + "\n";
      response += "POS" + IntegerToString(count) + "_TP=" + DoubleToString(positionInfo.TakeProfit(), 5) + "\n";
      response += "POS" + IntegerToString(count) + "_PROFIT=" + DoubleToString(positionInfo.Profit(), 2) + "\n";
      
      count++;
   }
   
   response += "COUNT=" + IntegerToString(count) + "\n";
   return response;
}

//+------------------------------------------------------------------+
//| Procesa solicitud de info de cuenta                                |
//+------------------------------------------------------------------+
string ProcessAccountInfo()
{
   string response = "STATUS=OK\n";
   response += "LOGIN=" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\n";
   response += "BALANCE=" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "\n";
   response += "EQUITY=" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "\n";
   response += "MARGIN=" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + "\n";
   response += "FREE_MARGIN=" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + "\n";
   response += "PROFIT=" + DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2) + "\n";
   response += "LEVERAGE=" + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + "\n";
   response += "CURRENCY=" + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
   response += "SERVER=" + AccountInfoString(ACCOUNT_SERVER) + "\n";
   response += "TRADE_ALLOWED=" + IntegerToString(AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) + "\n";
   
   return response;
}

//+------------------------------------------------------------------+
//| Procesa solicitud de info de símbolo                               |
//+------------------------------------------------------------------+
string ProcessSymbolInfo(string symbol)
{
   if(!symbolInfo.Name(symbol))
   {
      return "STATUS=ERROR\nERROR=Symbol not found: " + symbol + "\n";
   }
   
   symbolInfo.RefreshRates();
   
   string response = "STATUS=OK\n";
   response += "SYMBOL=" + symbol + "\n";
   response += "BID=" + DoubleToString(symbolInfo.Bid(), 5) + "\n";
   response += "ASK=" + DoubleToString(symbolInfo.Ask(), 5) + "\n";
   response += "SPREAD=" + IntegerToString(symbolInfo.Spread()) + "\n";
   response += "POINT=" + DoubleToString(symbolInfo.Point(), _Digits) + "\n";
   response += "DIGITS=" + IntegerToString(symbolInfo.Digits()) + "\n";
   response += "VOLUME_MIN=" + DoubleToString(symbolInfo.LotsMin(), 2) + "\n";
   response += "VOLUME_MAX=" + DoubleToString(symbolInfo.LotsMax(), 2) + "\n";
   
   return response;
}

//+------------------------------------------------------------------+
//| Guarda respuesta en archivo                                        |
//+------------------------------------------------------------------+
void SaveResponse(string commandFile, string response)
{
   //--- Usar nombre fijo ACTIVE_COMMAND.rsp
   string responseFile = "ACTIVE_COMMAND.rsp";
   
   if(InpDebugMode)
   {
      Print("💾 Guardando respuesta: Bot_Responses\\", responseFile);
   }
   
   int handle = FileOpen("Bot_Responses\\" + responseFile, FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_UNICODE);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, response);
      FileClose(handle);
      
      if(InpDebugMode)
      {
         Print("✅ Respuesta guardada correctamente");
         Print("📄 Contenido: ", response);
      }
   }
   else
   {
      int error = GetLastError();
      Print("❌ ERROR guardando respuesta: ", error);
   }
}

//+------------------------------------------------------------------+
//| Guarda tick actual                                                 |
//+------------------------------------------------------------------+
void SaveCurrentTick()
{
   string symbol = Symbol();
   datetime currentTime = TimeCurrent();
   
   if(currentTime == lastTickTime)
      return;
   lastTickTime = currentTime;
   
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
      return;
   
   int handle = FileOpen("Bot_Ticks\\tick_" + symbol + ".txt", FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, "SYMBOL=" + symbol + "\n");
      FileWriteString(handle, "BID=" + DoubleToString(tick.bid, 5) + "\n");
      FileWriteString(handle, "ASK=" + DoubleToString(tick.ask, 5) + "\n");
      FileWriteString(handle, "LAST=" + DoubleToString(tick.last, 5) + "\n");
      FileWriteString(handle, "VOLUME=" + IntegerToString(tick.volume) + "\n");
      FileWriteString(handle, "TIME=" + IntegerToString(tick.time) + "\n");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Procesa solicitud de datos históricos                              |
//+------------------------------------------------------------------+
string ProcessHistoricalData(string symbol, int timeframe, int bars)
{
   if(!SymbolSelect(symbol, true))
   {
      return "STATUS=ERROR\nERROR=Symbol not found: " + symbol + "\n";
   }
   
   //--- Convertir timeframe a ENUM_TIMEFRAMES
   ENUM_TIMEFRAMES tf;
   switch(timeframe)
   {
      case 1:    tf = PERIOD_M1; break;
      case 5:    tf = PERIOD_M5; break;
      case 15:   tf = PERIOD_M15; break;
      case 30:   tf = PERIOD_M30; break;
      case 60:   tf = PERIOD_H1; break;
      case 240:  tf = PERIOD_H4; break;
      case 1440: tf = PERIOD_D1; break;
      default:   tf = PERIOD_M15; break;
   }
   
   //--- Copiar datos históricos
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   int copied = CopyRates(symbol, tf, 0, bars, rates);
   if(copied <= 0)
   {
      return "STATUS=ERROR\nERROR=Failed to get historical data: " + IntegerToString(GetLastError()) + "\n";
   }
   
   //--- Construir respuesta
   string response = "STATUS=OK\n";
   response += "BARS=" + IntegerToString(copied) + "\n";
   response += "SYMBOL=" + symbol + "\n";
   response += "TIMEFRAME=" + IntegerToString(timeframe) + "\n";
   
   //--- Guardar en archivo CSV para eficiencia
   string csvFile = "Bot_Data\\" + symbol + "_" + IntegerToString(timeframe) + "_bars.csv";
   int handle = FileOpen(csvFile, FILE_WRITE|FILE_TXT|FILE_COMMON);
   
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, "time,open,high,low,close,volume\n");
      
      for(int i = 0; i < copied; i++)
      {
         string line = IntegerToString(rates[i].time) + ",";
         line += DoubleToString(rates[i].open, 5) + ",";
         line += DoubleToString(rates[i].high, 5) + ",";
         line += DoubleToString(rates[i].low, 5) + ",";
         line += DoubleToString(rates[i].close, 5) + ",";
         line += IntegerToString(rates[i].tick_volume) + "\n";
         
         FileWriteString(handle, line);
      }
      
      FileClose(handle);
      response += "CSV_FILE=" + csvFile + "\n";
   }
   
   return response;
}

//+------------------------------------------------------------------+
//| Calcula lotaje óptimo basado en riesgo                             |
//+------------------------------------------------------------------+
string ProcessCalculateLot(string symbol, double risk_percent, double stop_distance_points)
{
   if(!symbolInfo.Name(symbol))
   {
      return "STATUS=ERROR\nERROR=Symbol not found: " + symbol + "\n";
   }
   
   symbolInfo.RefreshRates();
   
   //--- Obtener balance
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = balance * (risk_percent / 100.0);
   
   //--- Calcular valor por punto
   double point = symbolInfo.Point();
   double tick_value = symbolInfo.TickValue();
   double tick_size = symbolInfo.TickSize();
   
   double pip_value = (tick_value / tick_size);
   
   //--- Para índices sintéticos, 1 punto = 1 USD
   if(StringFind(symbol, "Volatility") >= 0 || StringFind(symbol, "TM_VOLATILITY") >= 0)
   {
      pip_value = 1.0;
   }
   
   //--- Calcular lotaje
   double lot_size = 0.01;  // Default mínimo
   
   if(stop_distance_points > 0 && pip_value > 0)
   {
      lot_size = risk_amount / (stop_distance_points * pip_value);
   }
   
   //--- Ajustar a límites del símbolo
   double min_lot = symbolInfo.LotsMin();
   double max_lot = symbolInfo.LotsMax();
   double lot_step = symbolInfo.LotsStep();
   
   //--- Redondear correctamente (no usar round() que puede dar 0)
   if(lot_step > 0)
   {
      lot_size = MathCeil(lot_size / lot_step) * lot_step;
   }
   
   lot_size = MathMax(min_lot, MathMin(lot_size, max_lot));
   
   //--- Construir respuesta
   string response = "STATUS=OK\n";
   response += "LOT_SIZE=" + DoubleToString(lot_size, 2) + "\n";
   response += "RISK_AMOUNT=" + DoubleToString(risk_amount, 2) + "\n";
   response += "PIP_VALUE=" + DoubleToString(pip_value, 5) + "\n";
   response += "MIN_LOT=" + DoubleToString(min_lot, 2) + "\n";
   response += "MAX_LOT=" + DoubleToString(max_lot, 2) + "\n";
   response += "BALANCE=" + DoubleToString(balance, 2) + "\n";
   
   return response;
}

//+------------------------------------------------------------------+
//| Actualiza trailing stops de todas las posiciones                   |
//+------------------------------------------------------------------+
string ProcessUpdateTrailing(string filterSymbol, double trailing_pct)
{
   int updated = 0;
   int total = 0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(!positionInfo.SelectByIndex(i))
         continue;
      
      if(positionInfo.Magic() != InpMagicNumber)
         continue;
      
      if(filterSymbol != "" && positionInfo.Symbol() != filterSymbol)
         continue;
      
      total++;
      
      string symbol = positionInfo.Symbol();
      ulong ticket = positionInfo.Ticket();
      double open_price = positionInfo.PriceOpen();
      double current_sl = positionInfo.StopLoss();
      double current_tp = positionInfo.TakeProfit();
      
      //--- Obtener precio actual
      if(!symbolInfo.Name(symbol))
         continue;
      symbolInfo.RefreshRates();
      
      double bid = symbolInfo.Bid();
      double ask = symbolInfo.Ask();
      double point = symbolInfo.Point();
      
      double new_sl = current_sl;
      bool should_update = false;
      
      //--- Para posiciones LONG (BUY)
      if(positionInfo.PositionType() == POSITION_TYPE_BUY)
      {
         double profit_points = (bid - open_price) / point;
         
         if(profit_points > 0)
         {
            double trail_distance = profit_points * (1.0 - trailing_pct);
            new_sl = bid - (trail_distance * point);
            
            //--- Solo actualizar si el nuevo SL es mejor que el actual
            if(new_sl > current_sl || current_sl == 0)
            {
               should_update = true;
            }
         }
      }
      //--- Para posiciones SHORT (SELL)
      else if(positionInfo.PositionType() == POSITION_TYPE_SELL)
      {
         double profit_points = (open_price - ask) / point;
         
         if(profit_points > 0)
         {
            double trail_distance = profit_points * (1.0 - trailing_pct);
            new_sl = ask + (trail_distance * point);
            
            //--- Solo actualizar si el nuevo SL es mejor que el actual
            if(new_sl < current_sl || current_sl == 0)
            {
               should_update = true;
            }
         }
      }
      
      //--- Aplicar trailing stop
      if(should_update)
      {
         if(trade.PositionModify(ticket, new_sl, current_tp))
         {
            updated++;
         }
      }
   }
   
   string response = "STATUS=OK\n";
   response += "TOTAL_POSITIONS=" + IntegerToString(total) + "\n";
   response += "UPDATED=" + IntegerToString(updated) + "\n";
   response += "TRAILING_PCT=" + DoubleToString(trailing_pct, 2) + "\n";
   
   return response;
}
//+------------------------------------------------------------------+
