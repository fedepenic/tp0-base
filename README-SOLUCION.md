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
