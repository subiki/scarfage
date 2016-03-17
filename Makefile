usage:
	# run       -   run the app in debug mode
	# tests     -   run tests, app must be configured for db access
	# docs      -   generate docs
	# clean     -   clean up docs, venv, test log

venv:
	virtualenv venv --no-site-packages
	. venv/bin/activate && MAKEFLAGS="-j4" pip install -r requirements.txt

tests: venv
	. venv/bin/activate && python -m unittest scarf.core.test

run: venv
	. venv/bin/activate && python run.py

docs: venv
	. venv/bin/activate && pydoc -w ./
	mkdir docs
	mv *.html docs

clean:
	find -name "*.pyc" -exec rm -v {} \;
	rm -rf venv docs tests.log

dbhost = $(shell grep DBHOST scarf/config.py | cut -d"'" -f2)
dbname = $(shell grep DBNAME scarf/config.py | cut -d"'" -f2)
username = $(shell grep DBUSER scarf/config.py | cut -d"'" -f2)
passwd = $(shell grep DBPASS scarf/config.py | cut -d"'" -f2)
dumpdb:
	mysqldump --user=${username} --password=${passwd} -h ${dbhost} --no-data ${dbname} | pv  > scarfage.sql
