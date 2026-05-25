"""
Gestor de cuenta MT5 demo canónica.
"""
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

class MT5AccountManager:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "mt5_accounts.yaml"
        self.env_path = Path(__file__).parent.parent / ".env"
        self.load_accounts()
    
    def load_accounts(self):
        """Cargar configuración de cuentas"""
        with open(self.config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
    
    def list_accounts(self):
        """Listar todas las cuentas disponibles"""
        print("🏦 CUENTAS MT5 DEMO DISPONIBLES")
        print("=" * 50)
        
        active = self.config['active_account']
        
        for account_id, account in self.config['accounts'].items():
            status = "✅ ACTIVA" if account_id == active else "⚪ Disponible"
            print(f"\n{status} - {account_id.upper()}")
            print(f"   Nombre: {account['name']}")
            print(f"   Login: {account['login']}")
            print(f"   Servidor: {account['server']}")
            print(f"   Broker: {account['broker']}")
            print(f"   Tipo: {account['account_type']}")
            print(f"   Descripción: {account['description']}")
    
    def switch_account(self, account_id):
        """Cambiar a una cuenta específica"""
        if account_id not in self.config['accounts']:
            print(f"❌ Error: Cuenta '{account_id}' no encontrada")
            return False
        
        account = self.config['accounts'][account_id]
        
        # Actualizar .env sin persistir secretos en el repositorio
        if str(account.get('login', '')).strip():
            set_key(self.env_path, "MT5_LOGIN", str(account['login']))
        if str(account.get('password', '')).strip():
            set_key(self.env_path, "MT5_PASSWORD", account['password'])
        set_key(self.env_path, "MT5_SERVER", account['server'])
        
        # Actualizar cuenta activa en config
        self.config['active_account'] = account_id
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ Cambiado a cuenta: {account['name']}")
        print(f"   Servidor: {account['server']}")
        print(f"   Login/password: configurarlos manualmente en {self.env_path}")
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"1. Completar MT5_LOGIN y MT5_PASSWORD en {self.env_path}")
        print(f"2. Abrir MT5 y conectar a {account['server']}")
        print(f"3. Habilitar AutoTrading")
        print(f"4. Ejecutar: python tests/diagnose_simple.py")
        
        return True
    
    def get_active_account(self):
        """Obtener información de la cuenta activa"""
        active_id = self.config['active_account']
        return self.config['accounts'][active_id]
    
    def verify_installation(self):
        """Verificar instalación de MT5"""
        print("🔍 VERIFICANDO INSTALACIÓN MT5")
        print("=" * 40)
        
        for path in self.config['mt5_paths']:
            if Path(path).exists():
                print(f"✅ MT5 encontrado: {path}")
                return path
            else:
                print(f"❌ No encontrado: {path}")
        
        print("\n🚨 MT5 NO INSTALADO")
        print("📥 Descargar desde:")
        print("   - ThinkMarkets: https://www.thinkmarkets.com/en/trading-platforms/metatrader-5/")
        return None

def main():
    """Función principal para uso desde línea de comandos"""
    import sys
    
    manager = MT5AccountManager()
    
    if len(sys.argv) == 1:
        # Sin argumentos, mostrar cuentas
        manager.list_accounts()
        print(f"\n💡 Uso: python {sys.argv[0]} [thinkmarkets|verify]")
        
    elif sys.argv[1] == "verify":
        # Verificar instalación
        manager.verify_installation()
        
    elif sys.argv[1] in ["thinkmarkets"]:
        # Cambiar cuenta
        manager.switch_account(sys.argv[1])
        
    else:
        print(f"❌ Cuenta '{sys.argv[1]}' no válida")
        print("✅ Cuentas disponibles: thinkmarkets")

if __name__ == "__main__":
    main()