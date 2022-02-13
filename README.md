# El Guasón
![logo](meta/elguason.jpeg)

### Installation (Unix only for now)
`bash install_unix.sh`

## Setup
```
cp .env.sample .env
# fill with your CUIL, PASSWORD and your FACTURADOR name as it's seen while clicking on 'emitir factura'
# If you have more than one Point of Sale, you can also set PUNTO_DE_VENTA
```

# Como usarlo?
![usage](meta/guasonhelp.png)


## Quiero hacer una factura para hoy 

#### `guason facturar now`
> Emite una factura de forma automatica, recibiendo el monto, el servicio, y el destinatario del mismo.

## Quiero generar facturas para distintos dias por distintos montos
#### `guason facturar plan PLAN`
> Emite multiples factures segun lo especificado en el csv ingresado

## Quiero descargar los comprobantes de todas mis facturas en cierto rango de fechas
#### `guason reports download START END --destination comprobantes`
> Descarga facturas emitidas desde la fecha START hasta la fecha END y las guarda en el destino especificado

## Quiero un reporte de todo lo facturado a partir de los comprobantes de facturas
#### `guason reports build COMPROBANTESPATH --destination reports`
> Escribe un reporte csv y json a partir de la carpeta donde se encuentran las facturas

> Nota: Este comando depende de haber corrido y guardado los comprobantes previamente mediante `guason reports download`

## Quiero un reporte de mis ganancias por mes
#### `guason reports get REPORT_PATH`


## Quiero que me diga cuánto deberia facturar segun mis gastos mensuales
#### `guason create-plan GASTOMENSUAL`
> Genera un plan de facturacion mensual de GASTOMENSUAL que factura solo los dias habiles, variando los montos diarios
