# El Guasón
![logo](meta/elguason.jpeg)

### Installation
```
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install . && \
playwright install chrome && \
python main.py
```

## Setup
```
cp .env.sample .env
# fill with your CUIL, PASSWORD and your name as it's seen while clicking on 'emitir factura'
# Usually SURNAME NAME all uppercase.
```

## Usage
```
python main.py
```