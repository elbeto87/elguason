# El Guasón
![logo](meta/elguason.jpeg)

### Installation (Unix only for now)
`bash install_unix.sh`

## Setup
```
cp .env.sample .env
# fill with your CUIL, PASSWORD and your name as it's seen while clicking on 'emitir factura'
# Usually SURNAME NAME all uppercase.
```

## Como usarlo?
Despues de instalar con `flit install` se pueden usar los siguientes comandos

### `facturar`
> Emite una factura de forma automatica, recibiendo el monto, el servicio, y el destinatario del mismo.

### `facturarcsv csvspec`
> Emite multiples factures segun lo especificado en el csv ingresado

### `download START END --destination comprobantes`
> Descarga facturas emitidas desde START hasta END y las guarda en el destino especificado

### `report comprobantes --destination reports`
> Escribe un reporte csv y json a partir de la carpeta donde se encuentran las facturas

### `crontador HOUR CSVSPEC`
> Dado un csv con las facturas a emitir, configura un cron que las emite de forma periodica a la hora especificada
