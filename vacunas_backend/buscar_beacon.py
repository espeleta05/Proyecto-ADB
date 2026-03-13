import asyncio
from bleak import BleakScanner
import struct
import sys



TU_NOMBRE = "FSC-BP104D"
TU_UUID = "FDA50693-A4E2-4FB1-AFCF-C6EB07647825"
TU_MAJOR = 10065 
TU_MINOR = 26049 

FILTRAR_POR_NOMBRE = True
FILTRAR_POR_UUID = True
FILTRAR_POR_MAJOR_MINOR = True


def decode_ibeacon(manufacturer_data):
    """
    Decodifica los datos de un iBeacon
    """
    try:
        if 0x004C in manufacturer_data:
            data = manufacturer_data[0x004C]
            
            if len(data) >= 21 and data[0] == 0x02 and data[1] == 0x15:
                uuid_bytes = data[2:18]
                uuid = format_uuid(uuid_bytes)
                major = struct.unpack('>H', data[18:20])[0]
                minor = struct.unpack('>H', data[20:22])[0]
                
                measured_power = None
                if len(data) >= 23:
                    measured_power = struct.unpack('b', bytes([data[22]]))[0]
                
                return {
                    'uuid': uuid,
                    'major': major,
                    'minor': minor,
                    'measured_power': measured_power
                }
    except Exception as e:
        pass
    return None

def format_uuid(uuid_bytes):
    """Formatea los bytes del UUID en formato estándar"""
    if len(uuid_bytes) == 16:
        hex_str = uuid_bytes.hex()
        return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"
    return str(uuid_bytes)


def es_mi_beacon(device, advertisement_data, ibeacon_data):
    """
    Verifica si el dispositivo detectado es tu beacon específico
    """
    if not ibeacon_data:
        return False
    
    coincidencias = []
    
    # Verificar por nombre
    if FILTRAR_POR_NOMBRE and TU_NOMBRE:
        nombre_coincide = (advertisement_data.local_name and 
                          TU_NOMBRE.lower() in advertisement_data.local_name.lower())
        coincidencias.append(("nombre", nombre_coincide))
    
    # Verificar por UUID
    if FILTRAR_POR_UUID and TU_UUID:
        uuid_coincide = (ibeacon_data['uuid'].upper() == TU_UUID.upper())
        coincidencias.append(("UUID", uuid_coincide))
    
    # Verificar por Major y Minor
    if FILTRAR_POR_MAJOR_MINOR:
        major_coincide = (ibeacon_data['major'] == TU_MAJOR)
        minor_coincide = (ibeacon_data['minor'] == TU_MINOR)
        coincidencias.append(("Major/Minor", major_coincide and minor_coincide))
    
    # Si no hay filtros activados, mostrar todo
    if not any([FILTRAR_POR_NOMBRE, FILTRAR_POR_UUID, FILTRAR_POR_MAJOR_MINOR]):
        return True
    
    # Si hay filtros, debe cumplir al menos uno
    return any(coincide for _, coincide in coincidencias if coincide is not None)

def estimate_distance(rssi, measured_power, n=2.0):
    """
    Estima la distancia basada en RSSI
    """
    if rssi == 0 or measured_power is None:
        return -1.0
    
    ratio = rssi / measured_power
    if ratio < 1.0:
        return ratio ** 10
    else:
        return (0.89976) * (ratio ** 7.7095) + 0.111

def detection_callback(device, advertisement_data):
    """
    Callback que se ejecuta cuando se detecta un dispositivo
    """
    # Decodificar iBeacon si existe
    ibeacon_data = None
    if advertisement_data.manufacturer_data:
        ibeacon_data = decode_ibeacon(advertisement_data.manufacturer_data)
    
    # Mostrar todos los dispositivos detectados
    print(f"\n📱 DISPOSITIVO DETECTADO:")
    print(f"  • Dirección MAC: {device.address}")
    print(f"  • Nombre: {advertisement_data.local_name or 'Desconocido'}")
    print(f"  • RSSI: {advertisement_data.rssi} dBm")
    
    # Estimar distancia
    if ibeacon_data and ibeacon_data['measured_power']:
        distancia = estimate_distance(advertisement_data.rssi, ibeacon_data['measured_power'])
        print(f"  • Distancia estimada: {distancia:.2f} metros")
    else:
        # Para dispositivos no iBeacon, usar un valor por defecto de measured_power (-59 dBm es común)
        distancia = estimate_distance(advertisement_data.rssi, -59)
        print(f"  • Distancia estimada (aprox): {distancia:.2f} metros (basado en valor estándar)")
    
    if ibeacon_data:
        print(f"  • Es iBeacon: Sí")
        print(f"  • UUID: {ibeacon_data['uuid']}")
        print(f"  • Major: {ibeacon_data['major']}")
        print(f"  • Minor: {ibeacon_data['minor']}")
        if ibeacon_data['measured_power']:
            print(f"  • RSSI a 1m: {ibeacon_data['measured_power']} dBm")
    else:
        print(f"  • Es iBeacon: No")
    
    # Coordenadas: BLE no proporciona coordenadas GPS absolutas.
    # Para coordenadas relativas o absolutas, se necesita triangulación con múltiples beacons o GPS.
    print(f"  • Coordenadas: No disponibles (requiere múltiples beacons o GPS)")
    
    # Verificar si es nuestro beacon específico
    if es_mi_beacon(device, advertisement_data, ibeacon_data):
        print(f"  • ¡COINCIDE CON TU CONFIGURACIÓN! 🚨")
    
    print(f"{'-'*50}")

async def scan_for_my_beacon(scan_time=30):
    """
    Escanea específicamente buscando tu beacon
    """
    print(f"\n🔍 BUSCANDO TU BEACON ESPECÍFICO...")
    print(f"{'='*60}")
    print(f"\n📋 ESTAMOS BUSCANDO:")
    if FILTRAR_POR_NOMBRE and TU_NOMBRE:
        print(f"  • Nombre: {TU_NOMBRE}")
    if FILTRAR_POR_UUID and TU_UUID:
        print(f"  • UUID: {TU_UUID}")
    if FILTRAR_POR_MAJOR_MINOR:
        print(f"  • Major: {TU_MAJOR}, Minor: {TU_MINOR}")
    print(f"\n⏱️  Escaneando por {scan_time} segundos...")
    print(f"Presiona Ctrl+C para detener\n")
    
    scanner = BleakScanner(detection_callback)
    
    try:
        await scanner.start()
        await asyncio.sleep(scan_time)
        await scanner.stop()
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Escaneo detenido")
        await scanner.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await scanner.stop()

def mostrar_instrucciones():
    """Muestra instrucciones para configurar el código"""
    print("="*60)
    print("     BUSCADOR DE BEACON FSC-BP104D")
    print("="*60)
    print("\n📝 ANTES DE EMPEZAR:")
    print("  1. Abre este archivo en un editor de texto")
    print("  2. Modifica la sección CONFIGURACIÓN con los datos de tu beacon")
    print("  3. Guarda el archivo y ejecútalo de nuevo")
    print("\n⚙️  CONFIGURACIÓN ACTUAL:")
    print(f"  • Nombre a buscar: {TU_NOMBRE or 'NO ESPECIFICADO'}")
    print(f"  • UUID a buscar: {TU_UUID or 'NO ESPECIFICADO'}")
    print(f"  • Major: {TU_MAJOR if FILTRAR_POR_MAJOR_MINOR else 'NO FILTRANDO'}")
    print(f"  • Minor: {TU_MINOR if FILTRAR_POR_MAJOR_MINOR else 'NO FILTRANDO'}")
    
    if not any([FILTRAR_POR_NOMBRE and TU_NOMBRE, 
                FILTRAR_POR_UUID and TU_UUID, 
                FILTRAR_POR_MAJOR_MINOR]):
        print("\n⚠️  ATENCIÓN: No has configurado ningún filtro.")
        print("   El programa mostrará TODOS los iBeacons detectados.")
        print("   Busca tu beacon en la lista y anota su MAC.")

def main():
    mostrar_instrucciones()
    
    # Usar tiempo de escaneo por defecto
    scan_time = 10
    
    # Ejecutar escaneo
    asyncio.run(scan_for_my_beacon(scan_time))
    
    print(f"\n✅ Escaneo completado")
    print("="*60)

if __name__ == "__main__":
    main()