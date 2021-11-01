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

## Usage
After successfull installation, and alias is stored under `facturar` so run:
```
facturar
```
And you should see something like..
```
Ingresa el titulo del servicio a facturar [Servicios Profesionales]: Mantenimiento Pc
Ingresa el monto a facturar [10000]: 5200
Inicio de facturacion 📝
Abriendo página monotributo..
Ingresando al sitio..
```