//+------------------------------------------------------------------+
//|                                                        JAson.mqh   |
//|                                     Simplified JSON Parser for MQL5 |
//|                                          Bot Trader Copilot v4.11   |
//+------------------------------------------------------------------+
#property copyright "Bot Trader Copilot"
#property link      "https://github.com/copilot-bot"

//+------------------------------------------------------------------+
//| Clase para manejar valores JSON                                    |
//+------------------------------------------------------------------+
class CJAVal
{
private:
   string         m_key;
   string         m_value;
   int            m_type;  // 0=null, 1=string, 2=number, 3=bool, 4=array, 5=object
   CJAVal        *m_children[];
   int            m_size;
   
public:
   CJAVal()  { m_type = 0; m_size = 0; m_key = ""; m_value = ""; }
   ~CJAVal() { Clear(); }
   
   void Clear()
   {
      for(int i = 0; i < m_size; i++)
         if(m_children[i] != NULL)
            delete m_children[i];
      ArrayResize(m_children, 0);
      m_size = 0;
      m_value = "";
   }
   
   //--- Operadores de asignación
   void operator=(const string val) { m_value = val; m_type = 1; }
   void operator=(const double val) { m_value = DoubleToString(val, 8); m_type = 2; }
   void operator=(const int val)    { m_value = IntegerToString(val); m_type = 2; }
   void operator=(const long val)   { m_value = IntegerToString(val); m_type = 2; }
   void operator=(const bool val)   { m_value = val ? "true" : "false"; m_type = 3; }
   void operator=(CJAVal &val)      { Copy(val); }
   
   //--- Operador de índice para objetos/arrays
   CJAVal* operator[](const string key)
   {
      for(int i = 0; i < m_size; i++)
         if(m_children[i].m_key == key)
            return m_children[i];
      
      // Crear nuevo hijo
      m_type = 5;  // object
      ArrayResize(m_children, m_size + 1);
      m_children[m_size] = new CJAVal();
      m_children[m_size].m_key = key;
      m_size++;
      return m_children[m_size - 1];
   }
   
   CJAVal* operator[](const int index)
   {
      if(m_type != 4) m_type = 4;  // array
      
      while(m_size <= index)
      {
         ArrayResize(m_children, m_size + 1);
         m_children[m_size] = new CJAVal();
         m_size++;
      }
      return m_children[index];
   }
   
   //--- Conversiones
   string ToStr()    { return m_value; }
   double ToDbl()    { return StringToDouble(m_value); }
   int    ToInt()    { return (int)StringToInteger(m_value); }
   long   ToLong()   { return StringToInteger(m_value); }
   bool   ToBool()   { return m_value == "true" || m_value == "1"; }
   
   //--- Copiar
   void Copy(CJAVal &src)
   {
      Clear();
      m_key = src.m_key;
      m_value = src.m_value;
      m_type = src.m_type;
      
      for(int i = 0; i < src.m_size; i++)
      {
         ArrayResize(m_children, m_size + 1);
         m_children[m_size] = new CJAVal();
         m_children[m_size].Copy(src.m_children[i]);
         m_size++;
      }
   }
   
   //--- Deserializar JSON string
   bool Deserialize(string json)
   {
      Clear();
      json = StringTrimLeft(StringTrimRight(json));
      if(json == "") return false;
      
      int pos = 0;
      return ParseValue(json, pos);
   }
   
   //--- Serializar a JSON string
   string Serialize()
   {
      string result = "";
      
      if(m_type == 5)  // object
      {
         result = "{";
         for(int i = 0; i < m_size; i++)
         {
            if(i > 0) result += ",";
            result += "\"" + m_children[i].m_key + "\":" + m_children[i].Serialize();
         }
         result += "}";
      }
      else if(m_type == 4)  // array
      {
         result = "[";
         for(int i = 0; i < m_size; i++)
         {
            if(i > 0) result += ",";
            result += m_children[i].Serialize();
         }
         result += "]";
      }
      else if(m_type == 1)  // string
      {
         result = "\"" + EscapeString(m_value) + "\"";
      }
      else if(m_type == 2 || m_type == 3)  // number or bool
      {
         result = m_value;
      }
      else
      {
         result = "null";
      }
      
      return result;
   }
   
private:
   string EscapeString(string s)
   {
      StringReplace(s, "\\", "\\\\");
      StringReplace(s, "\"", "\\\"");
      StringReplace(s, "\n", "\\n");
      StringReplace(s, "\r", "\\r");
      StringReplace(s, "\t", "\\t");
      return s;
   }
   
   string UnescapeString(string s)
   {
      StringReplace(s, "\\\"", "\"");
      StringReplace(s, "\\\\", "\\");
      StringReplace(s, "\\n", "\n");
      StringReplace(s, "\\r", "\r");
      StringReplace(s, "\\t", "\t");
      return s;
   }
   
   bool ParseValue(string &json, int &pos)
   {
      SkipWhitespace(json, pos);
      if(pos >= StringLen(json)) return false;
      
      ushort c = StringGetCharacter(json, pos);
      
      if(c == '{')
         return ParseObject(json, pos);
      else if(c == '[')
         return ParseArray(json, pos);
      else if(c == '"')
         return ParseString(json, pos);
      else if(c == 't' || c == 'f')
         return ParseBool(json, pos);
      else if(c == 'n')
         return ParseNull(json, pos);
      else if(c == '-' || (c >= '0' && c <= '9'))
         return ParseNumber(json, pos);
      
      return false;
   }
   
   bool ParseObject(string &json, int &pos)
   {
      m_type = 5;
      pos++;  // skip '{'
      
      SkipWhitespace(json, pos);
      if(StringGetCharacter(json, pos) == '}')
      {
         pos++;
         return true;
      }
      
      while(pos < StringLen(json))
      {
         SkipWhitespace(json, pos);
         
         // Parse key
         if(StringGetCharacter(json, pos) != '"') return false;
         pos++;
         
         string key = "";
         while(pos < StringLen(json))
         {
            ushort c = StringGetCharacter(json, pos);
            if(c == '"') break;
            if(c == '\\') { pos++; c = StringGetCharacter(json, pos); }
            key += CharToString((uchar)c);
            pos++;
         }
         pos++;  // skip closing '"'
         
         SkipWhitespace(json, pos);
         if(StringGetCharacter(json, pos) != ':') return false;
         pos++;
         
         // Parse value
         ArrayResize(m_children, m_size + 1);
         m_children[m_size] = new CJAVal();
         m_children[m_size].m_key = key;
         if(!m_children[m_size].ParseValue(json, pos))
            return false;
         m_size++;
         
         SkipWhitespace(json, pos);
         ushort c = StringGetCharacter(json, pos);
         if(c == '}') { pos++; return true; }
         if(c == ',') { pos++; continue; }
         return false;
      }
      return false;
   }
   
   bool ParseArray(string &json, int &pos)
   {
      m_type = 4;
      pos++;  // skip '['
      
      SkipWhitespace(json, pos);
      if(StringGetCharacter(json, pos) == ']')
      {
         pos++;
         return true;
      }
      
      while(pos < StringLen(json))
      {
         ArrayResize(m_children, m_size + 1);
         m_children[m_size] = new CJAVal();
         if(!m_children[m_size].ParseValue(json, pos))
            return false;
         m_size++;
         
         SkipWhitespace(json, pos);
         ushort c = StringGetCharacter(json, pos);
         if(c == ']') { pos++; return true; }
         if(c == ',') { pos++; continue; }
         return false;
      }
      return false;
   }
   
   bool ParseString(string &json, int &pos)
   {
      m_type = 1;
      pos++;  // skip opening '"'
      
      m_value = "";
      while(pos < StringLen(json))
      {
         ushort c = StringGetCharacter(json, pos);
         if(c == '"') { pos++; return true; }
         if(c == '\\')
         {
            pos++;
            c = StringGetCharacter(json, pos);
            if(c == 'n') m_value += "\n";
            else if(c == 'r') m_value += "\r";
            else if(c == 't') m_value += "\t";
            else m_value += CharToString((uchar)c);
         }
         else
         {
            m_value += CharToString((uchar)c);
         }
         pos++;
      }
      return false;
   }
   
   bool ParseNumber(string &json, int &pos)
   {
      m_type = 2;
      m_value = "";
      
      while(pos < StringLen(json))
      {
         ushort c = StringGetCharacter(json, pos);
         if(c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E' || 
            (c >= '0' && c <= '9'))
         {
            m_value += CharToString((uchar)c);
            pos++;
         }
         else
            break;
      }
      return m_value != "";
   }
   
   bool ParseBool(string &json, int &pos)
   {
      m_type = 3;
      if(StringSubstr(json, pos, 4) == "true")
      {
         m_value = "true";
         pos += 4;
         return true;
      }
      if(StringSubstr(json, pos, 5) == "false")
      {
         m_value = "false";
         pos += 5;
         return true;
      }
      return false;
   }
   
   bool ParseNull(string &json, int &pos)
   {
      if(StringSubstr(json, pos, 4) == "null")
      {
         m_type = 0;
         m_value = "";
         pos += 4;
         return true;
      }
      return false;
   }
   
   void SkipWhitespace(string &json, int &pos)
   {
      while(pos < StringLen(json))
      {
         ushort c = StringGetCharacter(json, pos);
         if(c != ' ' && c != '\t' && c != '\n' && c != '\r')
            break;
         pos++;
      }
   }
};
//+------------------------------------------------------------------+
