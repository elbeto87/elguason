python3 -m venv venv && \
./venv/bin/pip install --upgrade pip && \
./venv/bin/python -m pip install -e . && \
./venv/bin/python -m playwright install chromium && \
. ./venv/bin/activate
