import sys
import random
from datetime import datetime, timedelta

def generar_fecha_aleatoria():
    start_date = datetime(1950, 1, 1)
    end_date = datetime(2005, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def generar_compose(archivo_salida, cantidad_clientes):
    # Base structure
    compose = """name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
"""

    # Adding clients only if cantidad_clientes > 0
    if cantidad_clientes > 0:
        for i in range(1, cantidad_clientes + 1):
            nombre = f"nombre{i}"
            apellido = f"apellido{i}"
            nacimiento = generar_fecha_aleatoria()
            documento = 40000000 + i
            numero = i
            
            compose += f"""  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - NOMBRE={nombre}
      - APELLIDO={apellido}
      - DOCUMENTO={documento}
      - NACIMIENTO={nacimiento}
      - NUMERO={numero}
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
"""

    # Append networks section at the end
    compose += """networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

    # Save to file
    with open(archivo_salida, "w") as f:
        f.write(compose)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: mi-generador.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    archivo_salida = sys.argv[1]
    try:
        cantidad_clientes = int(sys.argv[2])
        if cantidad_clientes < 0:
            raise ValueError
    except ValueError:
        print("Error: La cantidad de clientes debe ser un número entero no negativo.")
        sys.exit(1)

    generar_compose(archivo_salida, cantidad_clientes)
