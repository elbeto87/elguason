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
Despues de instalar con `flit install` existen distintos comandos segun lo que se quiera hacer y 
cuan automático queremos que sea..

## Quiero hacer una factura para hoy 
#### `facturar`
> Emite una factura de forma automatica, recibiendo el monto, el servicio, y el destinatario del mismo.

## Quiero generar facturas para distintos dias por distintos montos
#### `facturarcsv CSVSPEC`
> Emite multiples factures segun lo especificado en el csv ingresado

## Quiero descargar los comprobantes de todas mis facturas en cierto rango de fechas
#### `download START END --destination comprobantes`
> Descarga facturas emitidas desde la fecha START hasta la fecha END y las guarda en el destino especificado

## Quiero un reporte de todo lo facturado a partir de los comprobantes de facturas
#### `report COMPROBANTESPATH --destination reports`
> Escribe un reporte csv y json a partir de la carpeta donde se encuentran las facturas

> Nota: Este comando depende de haber corrido y guardado los comprobantes previamente mediante `download`

## Quiero que me diga cuánto deberia facturar segun mis gastos mensuales
#### `planificar GASTOMENSUAL`
> Genera un plan de facturacion mensual de GASTOMENSUAL que factura solo los dias habiles, variando los montos diarios

## No quiero acordarme de facturar todos los dias. No se puede automatizar?
Si, con
#### `crontador HOUR CSVSPEC`
> Dado un csv con las facturas a emitir, configura un cron que las emite de forma periodica a la hora especificada

> Nota: El archivo `CSVSPEC` puede ser creado manualmente o declarativamente mediante el comando `planificar`

