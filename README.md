# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso

El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de: **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target                | accion                                                                                                                                                                                                                                                                                                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker-compose-up`   | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers.                                                                                                                                                                                   |
| `docker-compose-down` | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
| `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose.                                                                                                                                                                                                                            |
| `docker-image`        | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto.                                                                                                                       |
| `build`               | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_.                                                                                                                                         |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar.

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.

### Cliente

se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:

1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up` y luego `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```

## Parte 1: Introducción a Docker

En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:

Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes. El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc.

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:

Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).

### Ejercicio N°3:

Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `

### Ejercicio N°4:

Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:

Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente

Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Servidor

Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:

Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:

- Definición de un protocolo para el envío de los mensajes.
- Serialización de los datos.
- Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
- Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

### Ejercicio N°6:

Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_).
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del _batch_ fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB.

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia

En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_, deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega

Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
(hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Respetar las entradas de log planteadas en los ejercicios, pues son las que se chequean en cada uno de los tests.

La corrección personal tendrá en cuenta la calidad del código entregado y casos de error posibles, se manifiesten o no durante la ejecución del trabajo práctico. Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).

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
