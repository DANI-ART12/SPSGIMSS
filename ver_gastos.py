import pandas as pd

print("🔍 VERIFICANDO HOJA GASTOS")
print("="*40)

try:
    df = pd.read_excel("base_datos.xlsx", sheet_name="gastos")
    print(f"✅ Hoja encontrada")
    print(f"📊 Filas: {len(df)}")
    print(f"📋 Columnas: {len(df.columns)}")
    print(f"📌 Nombres: {list(df.columns)}")
    
    if len(df.columns) == 0:
        print("\n⚠️  LA HOJA ESTÁ VACÍA (sin columnas)")
        print("   Solución: Crear tabla manualmente")
        
except Exception as e:
    print(f"❌ Error: {e}")
