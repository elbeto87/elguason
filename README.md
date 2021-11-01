# El Guasón
![logo](meta/elguason.jpeg)

### Installation
```
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip flit && \
flit install && \
playwright install chromium && \
```

## Setup
```
cp .env.sample .env
# fill with your CUIL, PASSWORD and your name as it's seen while clicking on 'emitir factura'
# Usually SURNAME NAME all uppercase.
```

## Usage
After running `flit install` it will add a script under `facturar` alias so run:
```
facturar
```