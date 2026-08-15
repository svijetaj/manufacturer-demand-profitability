.PHONY: setup data check eval clean

setup:
	pip install -r requirements.txt

data:
	cd data && python generate_data.py --out raw

check:
	cd data && python generate_data.py --out /tmp/_smoke >/dev/null && echo "generator OK"

eval:
	python eval/score.py --answers eval/answer_key.yaml --input $(FILE)

clean:
	rm -f data/raw/*.csv
