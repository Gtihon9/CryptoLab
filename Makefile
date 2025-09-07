PY=python3
PIP=pip

.PHONY: venv install run-spread scan markets httpx-50

venv:
	$(PY) -m venv .venv
	. .venv/bin/activate; $(PIP) install --upgrade pip
	. .venv/bin/activate; $(PIP) install -r requirements.txt

install: venv

run-spread:
	. .venv/bin/activate; $(PY) scripts/spread_loop.py

scan:
	. .venv/bin/activate; PYTHONPATH=src $(PY) -c 'from tasks.market_scanner import find_common_high_volume_futures, write_candidates; cs=find_common_high_volume_futures(); write_candidates("data/candidates.json", cs)'

httpx-50:
	. .venv/bin/activate; $(PY) test/latency/check_latency_httpx.py --trials 50


