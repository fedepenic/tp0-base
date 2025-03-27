# Manual de Uso

Este manual describe los pasos necesarios para ejecutar cada uno de los ejercicios del trabajo práctico. A continuación, se detallan las instrucciones para la ejecución de los distintos scripts asociados a cada ejercicio.

## Instrucciones Generales

**Clonación del repositorio:**

Para comenzar, debe descargar el repositorio y luego seleccionar la rama correspondiente al ejercicio que desea ejecutar. Esto se realiza utilizando el siguiente comando:

```bash
git checkout ejX
```

Donde `X` corresponde al número del ejercicio.

## Ejercicio 1 y Ejercicio 2

Para ejecutar los scripts del primer y segundo ejercicio, se debe posicionar en el directorio raíz del proyecto y ejecutar el siguiente comando:

```bash
bash generar-compose.sh docker-compose.yaml N
```

En este caso, `N` es el número de clientes deseado. Este comando generará el archivo `docker-compose.yaml` correspondiente con la configuración de contenedores para la cantidad de clientes especificada.

## Ejercicio 3

Para el tercer ejercicio, debe ubicarse nuevamente en el directorio raíz y ejecutar el siguiente comando para validar el servidor Echo:

```bash
bash validar-echo-server.sh
```

## Ejercicio 4

Para el cuarto ejercicio, una vez ubicado en el directorio base, ejecute el siguiente comando para levantar los contenedores Docker:

```bash
make docker-compose-up
```

Este comando iniciará los contenedores configurados en el archivo `docker-compose.yaml`.

Para detener los contenedores y finalizar la ejecución, utilice el siguiente comando:

```bash
make docker-compose-down
```

## Ejercicios 5 a 8

Los ejercicios 5, 6, 7 y 8 se ejecutan de manera similar al ejercicio 4. Para cada uno de estos, debe ubicarse en el directorio raíz y ejecutar los scripts correspondientes utilizando los mismos comandos que para el ejercicio 4.

## Modificación de la Cantidad de Clientes

Es importante destacar que en todos los ejercicios, la cantidad de clientes puede ser modificada utilizando el script proporcionado en el primer ejercicio (`generar-compose.sh`), permitiendo ajustar la configuración según sea necesario.

# Protocolo de Comunicación entre Clientes y Servidor (Parte 2)

Este documento describe el protocolo de comunicación utilizado entre los diferentes clientes (agencias) y el servidor (lotería). A continuación, se detallan los pasos y los mensajes intercambiados durante el proceso de envío y recepción de apuestas, así como las consideraciones sobre la arquitectura actual y posibles mejoras futuras.

## Descripción General del Protocolo

El protocolo de comunicación comienza con los clientes enviando la cantidad de apuestas que desean procesar. Cada agencia debe contar la cantidad de apuestas y enviarla al servidor para su procesamiento. Actualmente, no se implementa un mecanismo de _handshake_ entre los clientes y el servidor. Sin embargo, se contempla la posibilidad de implementar un _Three-Way Handshake_ en el futuro, similar a otros protocolos.

### Paso 1: Envío de la Cantidad de Apuestas

El cliente envía al servidor la cantidad de apuestas que tiene intención de procesar. El servidor, al recibir esta información, responde con un mensaje de confirmación, indicando que ha recibido correctamente el número de apuestas.

**Mensaje enviado por el servidor**:  
`ACK_TOTAL_BETS`

Este mensaje confirma que el servidor ha recibido el número total de apuestas enviadas por el cliente.

### Paso 2: Envío de Batches de Apuestas

Una vez que el servidor ha recibido la cantidad de apuestas, se encuentra en disposición de comenzar a recibir los batches (lotes) de apuestas. El cliente comienza a enviar los batches utilizando el siguiente formato:

`BATCH_BET:AGENCIA|NÚMERO DE APUESTAS ENVIADAS POR BATCH|APUESTAS`

Cada campo de la apuesta se separa por comas, y las apuestas dentro de un batch se separan por punto y coma. A medida que el servidor recibe cada batch, responde con un mensaje de confirmación:

**Mensaje enviado por el servidor**:  
`ACK_BATCH_RECEIVED`

### Paso 3: Almacenamiento de Apuestas y Confirmación

El servidor procesa y almacena cada una de las apuestas enviadas. Una vez que ha almacenado todas las apuestas correspondientes a una agencia, envía un mensaje de confirmación al cliente informando que las apuestas han sido guardadas correctamente:

**Mensaje enviado por el servidor**:  
`Successfully stored N bets for agency {agency}`

### Paso 4: Finalización del Envío de Apuestas

Una vez que el cliente ha enviado todos los batches de apuestas, debe notificar al servidor que ha terminado de enviar las apuestas. Esto se hace mediante el siguiente mensaje:

**Mensaje enviado por el cliente**:  
`FINISHED SENDING BETS`

### Paso 5: Procesamiento de Resultados

En este punto, el servidor está listo para procesar los resultados de la lotería y determinar los ganadores. El servidor envía una lista de los ganadores de la lotería a las agencias, en el siguiente formato:

**Mensaje enviado por el servidor**:  
`GANADORES: DNI1, DNI2, ETC`

Si no hubo ganadores, el servidor envía:

**Mensaje enviado por el servidor**:  
`GANADORES: None`

Cada agencia recibe esta información, la procesa y puede imprimir los resultados en sus registros o logs.

## Consideraciones y Mejoras Futuras

El protocolo descrito actualmente no contempla un sistema de reintentos en caso de pérdida de paquetes o en situaciones en las que los datos lleguen corrompidos. Además, la serialización de la cantidad de apuestas y los mensajes de confirmación se podría mejorar en el futuro para garantizar una comunicación más robusta y eficiente. Con más tiempo, se podrían implementar soluciones para manejar estos casos, como la introducción de un mecanismo de control de errores y reenvío de mensajes fallidos.

# Mecanismos de Sincronización (Parte 3)

Para permitir que los diferentes clientes o agencias se conecten y procesen apuestas de manera concurrente, se decidió implementar el manejo de conexiones mediante hilos (_threads_), utilizando la biblioteca `threading` de Python.

Cada vez que se acepta una nueva conexión, es decir, cuando un cliente se conecta al servidor, se asigna un nuevo hilo para su gestión. Esto permite que el sistema operativo optimice el uso de los recursos, minimizando tiempos de espera y permitiendo que se procesen múltiples conexiones en paralelo. Gracias a esta estrategia, las apuestas pueden ser registradas de manera más eficiente en el servidor. En consecuencia, el método `__handle_new_client` se ejecuta en un hilo independiente para cada cliente que establece una conexión.

### Gestión de Recursos Compartidos

El uso de múltiples hilos conlleva la existencia de recursos compartidos, los cuales pueden generar resultados inesperados si no se manejan adecuadamente. Para evitar condiciones de carrera (_race conditions_) y garantizar la consistencia de los datos, se implementaron mecanismos de sincronización mediante _locks_. Estos aseguran que determinadas operaciones se realicen de manera atómica, evitando modificaciones simultáneas que puedan comprometer la integridad del sistema.

Dos de los atributos del servidor que fueron protegidos con _locks_ son:

- **`_completed_agencies`**: Lista que almacena los identificadores de las agencias que han finalizado el proceso de envío de apuestas.
- **`_agency_sockets`**: Diccionario que asocia cada agencia con su respectivo socket de conexión.

Al utilizar _locks_, se garantiza que estos recursos solo sean modificados por un hilo a la vez, evitando inconsistencias o corrupción de datos.

### Sincronización en la Escritura de Archivos

Otro caso relevante en el que se aplicó un mecanismo de sincronización es el método `store_bets(bets)`, encargado de escribir las apuestas en un archivo. Dado que múltiples hilos pueden intentar acceder al archivo simultáneamente, existe el riesgo de que el sistema operativo interrumpa la operación de escritura y le ceda el control a otro hilo, lo que podría generar datos corruptos o inconsistentes. Para mitigar este problema, se implementó un _lock_ adicional que asegura que la escritura en el archivo se realice de manera exclusiva por un solo hilo a la vez.

Por otro lado, este problema no se presenta en el método `load_bets()`, encargado de leer las apuestas del archivo. Dado que la lectura se realiza en el hilo principal, y únicamente después de que todas las apuestas han sido registradas, no es necesario aplicar un _lock_ en este caso.

El uso de estos mecanismos de sincronización garantiza la correcta ejecución del sistema en un entorno concurrente, asegurando la integridad de los datos y evitando conflictos entre los diferentes hilos.
