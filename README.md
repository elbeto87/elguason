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

## Como usarlo?
Despues de instalar con `flit install` se pueden usar los siguientes comandos

### `facturar`
> Emite una factura de forma automatica, recibiendo el monto, el servicio, y el destinatario del mismo.

### `facturarcsv CSVSPEC`
> Emite multiples factures segun lo especificado en el csv ingresado

### `download START END --destination comprobantes`
> Descarga facturas emitidas desde la fecha START hasta la fecha END y las guarda en el destino especificado

### `report COMPROBANTESPATH --destination reports`
> Escribe un reporte csv y json a partir de la carpeta donde se encuentran las facturas

### `crontador HOUR CSVSPEC`
> Dado un csv con las facturas a emitir, configura un cron que las emite de forma periodica a la hora especificada
