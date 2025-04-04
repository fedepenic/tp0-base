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

El protocolo de comunicación se inicia con el envío, por parte del cliente, de un mensaje que indica el comienzo del proceso de transmisión de apuestas en bloques (_batches_). Ante este mensaje, el servidor responde con una confirmación (_ACK_), lo que establece una sincronización inicial entre ambas partes.

Actualmente, la implementación no incluye un mecanismo formal de _handshake_ entre el cliente y el servidor. Sin embargo, se contempla la posibilidad de incorporar en el futuro un esquema de _Three-Way Handshake_, similar al utilizado en otros protocolos de comunicación, con el objetivo de reforzar la fiabilidad del proceso de inicio.

Cabe destacar que todos los mensajes intercambiados finalizan con el carácter delimitador `\n`, lo cual facilita la lectura y escritura de datos a través de sockets, asegurando una correcta separación de los mensajes sin pérdida de información.

### Paso 1: Inicio del proceso de transmisión de apuestas (Bets)

El cliente da inicio a la comunicación mediante el envío de un mensaje específico que señala el comienzo del proceso de transmisión de apuestas. Dicho mensaje se identifica como `INICIO_ENVIO_BETS`.

Una vez recibido dicho mensaje, el servidor responde con una confirmación denominada `ACK_INICIO_ENVIO_BETS`, lo que indica que ha reconocido correctamente el inicio del proceso de transmisión por parte del cliente.

### Paso 2: Envío de Batches de Apuestas

Una vez que el servidor ha recibido correctamente el mensaje indicado en el Paso 1, se encuentra en disposición de comenzar a recibir los _batches_ (lotes) de apuestas. El cliente inicia entonces el envío de los _batches_ utilizando el siguiente formato:

`BATCH_BET:AGENCIA|NÚMERO DE APUESTAS ENVIADAS POR BATCH|APUESTAS`

Cada campo de una apuesta se separa mediante comas, mientras que las distintas apuestas dentro de un mismo _batch_ se separan por punto y coma.

A medida que el servidor va recibiendo cada _batch_, los procesa y almacena adecuadamente mediante la función `store_bets()`. Una vez completado el almacenamiento de un lote, responde al cliente con un mensaje de confirmación:

**Mensaje enviado por el servidor**:  
`ACK_BATCH_RECEIVED`

### Paso 3: Finalización del Envío de Apuestas y Confirmación de Recepción

Una vez que el cliente ha completado el envío de todas las apuestas correspondientes a su agencia, transmite un mensaje especial al servidor para indicar dicha finalización. Este mensaje se identifica como `END_OF_BETS`.

Al recibirlo, el servidor responde con un mensaje de confirmación, indicando que ha recibido correctamente la notificación de finalización del envío de apuestas para la agencia en cuestión.

### Paso 4: Procesamiento de Resultados

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

Uno de los atributos del servidor que fue protegido con _locks_ es:

- **`_agency_sockets`**: Diccionario que asocia cada agencia con su respectivo socket de conexión.

Al utilizar _locks_, se garantiza que este recurso solo sea modificado por un hilo a la vez, evitando inconsistencias o corrupción de datos.

### Sincronización en la Escritura de Archivos

Otro caso relevante en el que se aplicó un mecanismo de sincronización es el método `store_bets(bets)`, encargado de escribir las apuestas en un archivo. Dado que múltiples hilos pueden intentar acceder al archivo simultáneamente, existe el riesgo de que el sistema operativo interrumpa la operación de escritura y le ceda el control a otro hilo, lo que podría generar datos corruptos o inconsistentes. Para mitigar este problema, se implementó un _lock_ adicional que asegura que la escritura en el archivo se realice de manera exclusiva por un solo hilo a la vez.

Por otro lado, este problema no se presenta en el método `load_bets()`, encargado de leer las apuestas del archivo. Dado que la lectura se realiza en el hilo principal, y únicamente después de que todas las apuestas han sido registradas, no es necesario aplicar un _lock_ en este caso.

El uso de estos mecanismos de sincronización garantiza la correcta ejecución del sistema en un entorno concurrente, asegurando la integridad de los datos y evitando conflictos entre los diferentes hilos.

## Utilización de Threads en Python a pesar del GIL

A pesar de las conocidas limitaciones impuestas por el Global Interpreter Lock (GIL) en Python, la utilización de threads en este programa es viable, ya que la naturaleza del problema no convierte al GIL en un impedimento significativo para su correcto funcionamiento.

### ¿Qué es el GIL?

El GIL es un mecanismo del intérprete de Python (CPython) que impide que múltiples hilos de ejecución (threads) ejecuten bytecode de Python simultáneamente en múltiples núcleos. Esto significa que, incluso en sistemas con múltiples procesadores, los threads en Python no pueden aprovechar completamente el paralelismo a nivel de CPU cuando están ejecutando código Python puro. El GIL fue introducido para simplificar la gestión de memoria interna del intérprete, pero su presencia ha sido objeto de debate debido a las limitaciones que impone en programas intensivos en CPU.

### Por qué los threads funcionan bien en el TP0?

El programa desarrollado se basa en una arquitectura concurrente donde cada cliente es atendido por un hilo separado. Esta estrategia es eficaz debido a que el trabajo principal que realiza cada hilo está centrado en:

- Comunicación mediante sockets (`recv`, `sendall`), que son operaciones de entrada/salida (I/O) bloqueantes.
- Escritura de datos en archivos o estructuras compartidas protegidas por `Locks`.
- Procesamiento ligero de datos (parseo de strings, validación básica, construcción de objetos simples).

Las operaciones I/O bloqueantes liberan el GIL temporalmente mientras el hilo espera por datos del cliente o por acceso al sistema de archivos. De esta manera, otros hilos pueden continuar ejecutándose en paralelo. Así, el GIL **no representa un cuello de botella** en este caso, ya que el programa no depende de tareas intensivas en CPU sino de I/O concurrente.

### ¿Cuándo el GIL puede convertirse en un impedimento?

Los hilos en Python tienden a ser ineficientes en aplicaciones donde la carga principal está orientada al procesamiento intensivo en CPU. Por ejemplo:

- Algoritmos de cálculo numérico o simulaciones científicas.
- Procesamiento de imágenes o video.
- Algoritmos criptográficos.
- Procesamiento de grandes volúmenes de datos en memoria.

En estos escenarios, debido a que el GIL impide la ejecución simultánea de threads en diferentes núcleos, el rendimiento no escala correctamente al agregar más hilos. Para este tipo de aplicaciones, se recomienda el uso de modelos basados en procesos (`multiprocessing`).
