import asyncio
from bleak import BleakClient
import json

MAC_BEACON = "DC:0D:30:1F:66:10"

async def main():
    print(f"Conectando al beacon {MAC_BEACON}...")
    
    client = BleakClient(MAC_BEACON)
    
    try:
        await client.connect()
        print("Conectado exitosamente.")
        
        # Obtener servicios
        services = client.services
        
        print("\nServicios y características:")
        dispositivos = []
        for service in services:
            print(f"\nServicio: {service.uuid}")
            for char in service.characteristics:
                print(f"  Característica: {char.uuid}")
                print(f"    Propiedades: {char.properties}")
                
                # Intentar leer si es legible
                if 'read' in char.properties:
                    try:
                        data = await client.read_gatt_char(char.uuid)
                        print(f"    Datos: {data}")
                        # Intentar decodificar como string
                        try:
                            decoded = data.decode('utf-8')
                            print(f"    Decodificado: {decoded}")
                            # Intentar parsear como JSON
                            try:
                                json_data = json.loads(decoded)
                                print(f"    JSON: {json_data}")
                                if isinstance(json_data, list):
                                    dispositivos.extend(json_data)
                                elif isinstance(json_data, dict) and 'dispositivos' in json_data:
                                    dispositivos.extend(json_data['dispositivos'])
                            except json.JSONDecodeError:
                                pass
                        except UnicodeDecodeError:
                            pass
                    except Exception as e:
                        print(f"    Error al leer: {e}")
        
        # Mostrar lista de dispositivos
        if dispositivos:
            print(f"\n{'='*50}")
            print("DISPOSITIVOS DETECTADOS:")
            print(f"{'='*50}")
            for i, disp in enumerate(dispositivos, 1):
                print(f"{i}. {disp}")
        else:
            print("\nNo se encontraron dispositivos en los datos leídos.")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Desconectado.")

if __name__ == "__main__":
    asyncio.run(main())