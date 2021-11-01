python3 -m venv venv && \
./venv/bin/pip install --upgrade pip flit && \
./venv/bin/python -m flit install && \
./venv/bin/python -m playwright install chromium && \
. ./venv/bin/activate
