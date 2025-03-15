import sys
import yaml

def generar_compose(archivo_salida, cantidad_clientes):
    compose = {
        "name": "tp0",
        "services": {
            "server": {
                "container_name": "server",
                "image": "server:latest",
                "entrypoint": "python3 /main.py",
                "environment": [
                    "PYTHONUNBUFFERED=1",
                    "LOGGING_LEVEL=DEBUG"
                ],
                "networks": ["testing_net"]
            }
        },
        "networks": {
            "testing_net": {
                "ipam": {
                    "driver": "default",
                    "config": [{"subnet": "172.25.125.0/24"}]
                }
            }
        }
    }

    # Agregar clientes dinámicamente
    for i in range(1, cantidad_clientes + 1):
        compose["services"][f"client{i}"] = {
            "container_name": f"client{i}",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": [
                f"CLI_ID={i}",
                "CLI_LOG_LEVEL=DEBUG"
            ],
            "networks": ["testing_net"],
            "depends_on": ["server"]
        }

    # Guardar en archivo YAML
    with open(archivo_salida, "w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: mi-generador.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    archivo_salida = sys.argv[1]
    try:
        cantidad_clientes = int(sys.argv[2])
        if cantidad_clientes < 1:
            raise ValueError
    except ValueError:
        print("Error: La cantidad de clientes debe ser un número entero positivo.")
        sys.exit(1)

    generar_compose(archivo_salida, cantidad_clientes)
