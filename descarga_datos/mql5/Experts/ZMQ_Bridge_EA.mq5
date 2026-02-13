//+------------------------------------------------------------------+
//|                                              ZMQ_Bridge_EA.mq5    |
//|                                          Bot Trader Copilot v4.11 |
//|                                       ZeroMQ Bridge for Python    |
//+------------------------------------------------------------------+
#property copyright "Bot Trader Copilot"
#property link      "https://github.com/copilot-bot"
#property version   "4.11"
#property strict

//--- Incluir librería ZMQ (descargar de: https://github.com/dingmaotu/mql-zmq)
#include <Zmq/Zmq.mqh>
#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>
#include <JAson.mqh>  // Librería JSON para MQL5

//--- Parámetros de entrada
input string   InpOrdersPort = "5555";           // Puerto para órdenes (REQ/REP)
input string   InpTicksPort = "5556";            // Puerto para ticks (PUB)
input int      InpMagicNumber = 20260129;        // Magic Number del bot
input bool     InpEnableTicks = true;            // Enviar ticks en tiempo real
input int      InpSlippage = 10;                 // Slippage máximo (puntos)
input bool     InpDebugMode = false;             // Modo debug

//--- Variables globales ZMQ
Context *context;
Socket  *ordersSocket;
Socket  *ticksSocket;

//--- Objetos de trading
CTrade         trade;
CPositionInfo  positionInfo;
CSymbolInfo    symbolInfo;

//--- Variables de estado
bool isInitialized = false;
datetime lastTickTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════════");
   Print("🔌 ZMQ Bridge EA v4.11 - Inicializando...");
   Print("═══════════════════════════════════════════════════════════════");
   
   //--- Crear contexto ZMQ
   context = new Context("ZMQ_Bridge");
   
   //--- Socket para órdenes (REP - responde a requests)
   ordersSocket = new Socket(context, ZMQ_REP);
   string ordersUrl = "tcp://*:" + InpOrdersPort;
   if(!ordersSocket.bind(ordersUrl))
   {
      Print("❌ Error: No se pudo bind al puerto de órdenes ", InpOrdersPort);
      return INIT_FAILED;
   }
   Print("✅ Socket órdenes: ", ordersUrl);
   
   //--- Socket para ticks (PUB - publica a subscribers)
   ticksSocket = new Socket(context, ZMQ_PUB);
   string ticksUrl = "tcp://*:" + InpTicksPort;
   if(!ticksSocket.bind(ticksUrl))
   {
      Print("❌ Error: No se pudo bind al puerto de ticks ", InpTicksPort);
      return INIT_FAILED;
   }
   Print("✅ Socket ticks: ", ticksUrl);
   
   //--- Configurar trading
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   trade.SetAsyncMode(false);
   
   //--- Establecer timeout no bloqueante para recibir
   ordersSocket.setReceiveTimeout(100);  // 100ms
   
   isInitialized = true;
   Print("✅ ZMQ Bridge EA inicializado correctamente");
   Print("   Magic Number: ", InpMagicNumber);
   Print("   Ticks habilitados: ", InpEnableTicks);
   Print("═══════════════════════════════════════════════════════════════");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("🔌 Cerrando ZMQ Bridge EA...");
   
   if(ordersSocket != NULL)
   {
      ordersSocket.unbind("tcp://*:" + InpOrdersPort);
      delete ordersSocket;
   }
   
   if(ticksSocket != NULL)
   {
      ticksSocket.unbind("tcp://*:" + InpTicksPort);
      delete ticksSocket;
   }
   
   if(context != NULL)
   {
      delete context;
   }
   
   Print("✅ ZMQ Bridge EA cerrado");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!isInitialized) return;
   
   //--- Procesar mensajes de órdenes
   ProcessOrderRequests();
   
   //--- Publicar ticks si está habilitado
   if(InpEnableTicks)
   {
      PublishTick();
   }
}

//+------------------------------------------------------------------+
//| Procesa requests de órdenes via ZMQ                                |
//+------------------------------------------------------------------+
void ProcessOrderRequests()
{
   ZmqMsg request;
   
   //--- Intentar recibir mensaje (no bloqueante)
   if(!ordersSocket.recv(request, true))  // true = no block
      return;
   
   string msg = request.getData();
   if(msg == "") return;
   
   if(InpDebugMode)
      Print("📥 Recibido: ", msg);
   
   //--- Parsear JSON
   CJAVal json;
   if(!json.Deserialize(msg))
   {
      SendErrorResponse("Invalid JSON");
      return;
   }
   
   //--- Obtener acción
   string action = json["action"].ToStr();
   
   //--- Procesar según acción
   if(action == "heartbeat")
      ProcessHeartbeat();
   else if(action == "order")
      ProcessOrder(json);
   else if(action == "close")
      ProcessClose(json);
   else if(action == "modify")
      ProcessModify(json);
   else if(action == "get_positions")
      ProcessGetPositions(json);
   else if(action == "account_info")
      ProcessAccountInfo();
   else if(action == "symbol_info")
      ProcessSymbolInfo(json);
   else
      SendErrorResponse("Unknown action: " + action);
}

//+------------------------------------------------------------------+
//| Procesa heartbeat                                                  |
//+------------------------------------------------------------------+
void ProcessHeartbeat()
{
   CJAVal response;
   response["status"] = "ok";
   response["timestamp"] = (double)TimeCurrent();
   response["server_time"] = TimeToString(TimeCurrent());
   
   SendResponse(response);
}

//+------------------------------------------------------------------+
//| Procesa orden de trading                                           |
//+------------------------------------------------------------------+
void ProcessOrder(CJAVal &json)
{
   string symbol = json["symbol"].ToStr();
   int orderType = (int)json["type"].ToInt();
   double volume = json["volume"].ToDbl();
   double price = json["price"].ToDbl();
   double sl = json["sl"].ToDbl();
   double tp = json["tp"].ToDbl();
   int magic = (int)json["magic"].ToInt();
   string comment = json["comment"].ToStr();
   
   //--- Validar símbolo
   if(!SymbolSelect(symbol, true))
   {
      SendErrorResponse("Symbol not found: " + symbol);
      return;
   }
   
   //--- Obtener precios actuales
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   //--- Determinar precio si es orden de mercado
   if(price == 0)
   {
      price = (orderType == 0) ? ask : bid;  // BUY usa ask, SELL usa bid
   }
   
   //--- Configurar magic si se especificó
   if(magic > 0)
      trade.SetExpertMagicNumber(magic);
   else
      trade.SetExpertMagicNumber(InpMagicNumber);
   
   //--- Ejecutar orden
   bool result = false;
   ulong ticket = 0;
   
   if(orderType == 0)  // BUY
   {
      result = trade.Buy(volume, symbol, 0, sl, tp, comment);
   }
   else if(orderType == 1)  // SELL
   {
      result = trade.Sell(volume, symbol, 0, sl, tp, comment);
   }
   else if(orderType == 2)  // BUY_LIMIT
   {
      result = trade.BuyLimit(volume, price, symbol, sl, tp, ORDER_TIME_GTC, 0, comment);
   }
   else if(orderType == 3)  // SELL_LIMIT
   {
      result = trade.SellLimit(volume, price, symbol, sl, tp, ORDER_TIME_GTC, 0, comment);
   }
   else if(orderType == 4)  // BUY_STOP
   {
      result = trade.BuyStop(volume, price, symbol, sl, tp, ORDER_TIME_GTC, 0, comment);
   }
   else if(orderType == 5)  // SELL_STOP
   {
      result = trade.SellStop(volume, price, symbol, sl, tp, ORDER_TIME_GTC, 0, comment);
   }
   
   //--- Enviar respuesta
   if(result)
   {
      ticket = trade.ResultOrder();
      CJAVal response;
      response["status"] = "ok";
      response["ticket"] = (double)ticket;
      response["price"] = trade.ResultPrice();
      response["volume"] = trade.ResultVolume();
      SendResponse(response);
      
      Print("✅ Orden ejecutada: ", symbol, " ", (orderType==0?"BUY":"SELL"), 
            " vol=", volume, " ticket=", ticket);
   }
   else
   {
      SendErrorResponse("Order failed: " + IntegerToString(trade.ResultRetcode()) + 
                       " - " + trade.ResultRetcodeDescription());
   }
}

//+------------------------------------------------------------------+
//| Procesa cierre de posición                                         |
//+------------------------------------------------------------------+
void ProcessClose(CJAVal &json)
{
   ulong ticket = (ulong)json["ticket"].ToInt();
   double volume = json["volume"].ToDbl();
   
   //--- Seleccionar posición
   if(!PositionSelectByTicket(ticket))
   {
      SendErrorResponse("Position not found: " + IntegerToString(ticket));
      return;
   }
   
   //--- Cerrar posición
   bool result;
   if(volume > 0)
      result = trade.PositionClosePartial(ticket, volume);
   else
      result = trade.PositionClose(ticket);
   
   if(result)
   {
      CJAVal response;
      response["status"] = "ok";
      response["ticket"] = (double)ticket;
      SendResponse(response);
      Print("✅ Posición cerrada: ", ticket);
   }
   else
   {
      SendErrorResponse("Close failed: " + IntegerToString(trade.ResultRetcode()));
   }
}

//+------------------------------------------------------------------+
//| Procesa modificación de SL/TP                                      |
//+------------------------------------------------------------------+
void ProcessModify(CJAVal &json)
{
   ulong ticket = (ulong)json["ticket"].ToInt();
   double sl = json["sl"].ToDbl();
   double tp = json["tp"].ToDbl();
   
   //--- Seleccionar posición
   if(!PositionSelectByTicket(ticket))
   {
      SendErrorResponse("Position not found: " + IntegerToString(ticket));
      return;
   }
   
   //--- Obtener valores actuales si no se especifican nuevos
   if(sl == 0) sl = PositionGetDouble(POSITION_SL);
   if(tp == 0) tp = PositionGetDouble(POSITION_TP);
   
   //--- Modificar posición
   if(trade.PositionModify(ticket, sl, tp))
   {
      CJAVal response;
      response["status"] = "ok";
      response["ticket"] = (double)ticket;
      response["sl"] = sl;
      response["tp"] = tp;
      SendResponse(response);
      Print("✅ Posición modificada: ", ticket, " SL=", sl, " TP=", tp);
   }
   else
   {
      SendErrorResponse("Modify failed: " + IntegerToString(trade.ResultRetcode()));
   }
}

//+------------------------------------------------------------------+
//| Procesa solicitud de posiciones                                    |
//+------------------------------------------------------------------+
void ProcessGetPositions(CJAVal &json)
{
   string filterSymbol = json["symbol"].ToStr();
   int filterMagic = (int)json["magic"].ToInt();
   
   CJAVal response;
   response["status"] = "ok";
   
   CJAVal positions;
   int count = 0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(!positionInfo.SelectByIndex(i))
         continue;
      
      //--- Filtrar por símbolo si se especificó
      if(filterSymbol != "" && positionInfo.Symbol() != filterSymbol)
         continue;
      
      //--- Filtrar por magic si se especificó
      if(filterMagic > 0 && positionInfo.Magic() != filterMagic)
         continue;
      
      CJAVal pos;
      pos["ticket"] = (double)positionInfo.Ticket();
      pos["symbol"] = positionInfo.Symbol();
      pos["type"] = (int)positionInfo.PositionType();
      pos["volume"] = positionInfo.Volume();
      pos["open_price"] = positionInfo.PriceOpen();
      pos["sl"] = positionInfo.StopLoss();
      pos["tp"] = positionInfo.TakeProfit();
      pos["profit"] = positionInfo.Profit();
      pos["open_time"] = (double)positionInfo.Time();
      pos["magic"] = (double)positionInfo.Magic();
      pos["comment"] = positionInfo.Comment();
      
      positions[count] = pos;
      count++;
   }
   
   response["positions"] = positions;
   response["count"] = count;
   
   SendResponse(response);
}

//+------------------------------------------------------------------+
//| Procesa solicitud de info de cuenta                                |
//+------------------------------------------------------------------+
void ProcessAccountInfo()
{
   CJAVal response;
   response["status"] = "ok";
   
   CJAVal account;
   account["login"] = (double)AccountInfoInteger(ACCOUNT_LOGIN);
   account["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   account["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   account["margin"] = AccountInfoDouble(ACCOUNT_MARGIN);
   account["free_margin"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   account["profit"] = AccountInfoDouble(ACCOUNT_PROFIT);
   account["leverage"] = (double)AccountInfoInteger(ACCOUNT_LEVERAGE);
   account["currency"] = AccountInfoString(ACCOUNT_CURRENCY);
   account["server"] = AccountInfoString(ACCOUNT_SERVER);
   account["trade_allowed"] = AccountInfoInteger(ACCOUNT_TRADE_ALLOWED);
   account["trade_expert"] = AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
   
   response["account"] = account;
   SendResponse(response);
}

//+------------------------------------------------------------------+
//| Procesa solicitud de info de símbolo                               |
//+------------------------------------------------------------------+
void ProcessSymbolInfo(CJAVal &json)
{
   string symbol = json["symbol"].ToStr();
   
   if(!symbolInfo.Name(symbol))
   {
      SendErrorResponse("Symbol not found: " + symbol);
      return;
   }
   
   symbolInfo.RefreshRates();
   
   CJAVal response;
   response["status"] = "ok";
   
   CJAVal info;
   info["symbol"] = symbol;
   info["bid"] = symbolInfo.Bid();
   info["ask"] = symbolInfo.Ask();
   info["spread"] = symbolInfo.Spread();
   info["point"] = symbolInfo.Point();
   info["digits"] = symbolInfo.Digits();
   info["volume_min"] = symbolInfo.LotsMin();
   info["volume_max"] = symbolInfo.LotsMax();
   info["volume_step"] = symbolInfo.LotsStep();
   info["trade_mode"] = (int)symbolInfo.TradeMode();
   info["trade_calc_mode"] = (int)symbolInfo.TradeCalcMode();
   info["contract_size"] = symbolInfo.ContractSize();
   info["tick_value"] = symbolInfo.TickValue();
   info["tick_size"] = symbolInfo.TickSize();
   
   response["symbol_info"] = info;
   SendResponse(response);
}

//+------------------------------------------------------------------+
//| Publica tick actual via ZMQ                                        |
//+------------------------------------------------------------------+
void PublishTick()
{
   string symbol = Symbol();
   datetime currentTime = TimeCurrent();
   
   //--- Evitar enviar ticks duplicados
   if(currentTime == lastTickTime)
      return;
   lastTickTime = currentTime;
   
   //--- Construir mensaje de tick
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
      return;
   
   CJAVal tickJson;
   tickJson["symbol"] = symbol;
   tickJson["bid"] = tick.bid;
   tickJson["ask"] = tick.ask;
   tickJson["last"] = tick.last;
   tickJson["volume"] = (double)tick.volume;
   tickJson["time"] = (double)tick.time;
   tickJson["flags"] = tick.flags;
   
   string msg = tickJson.Serialize();
   
   ZmqMsg zmqMsg(msg);
   ticksSocket.send(zmqMsg, true);  // non-blocking
}

//+------------------------------------------------------------------+
//| Envía respuesta JSON                                               |
//+------------------------------------------------------------------+
void SendResponse(CJAVal &json)
{
   string msg = json.Serialize();
   ZmqMsg response(msg);
   ordersSocket.send(response);
   
   if(InpDebugMode)
      Print("📤 Enviado: ", msg);
}

//+------------------------------------------------------------------+
//| Envía respuesta de error                                           |
//+------------------------------------------------------------------+
void SendErrorResponse(string error)
{
   CJAVal response;
   response["status"] = "error";
   response["error"] = error;
   SendResponse(response);
   
   Print("❌ Error: ", error);
}
//+------------------------------------------------------------------+
