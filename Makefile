usage:
	# run       -   run the app in debug mode
	# tests     -   run tests, app must be configured for db access
	# docs      -   generate docs
	# clean     -   clean up docs, venv, test log
	# dumpdb    -   dump the database schema (config.py must already exist)
	# importdb  -   import the database (config.py must already exist)

venv:
	virtualenv venv --no-site-packages
	. venv/bin/activate && MAKEFLAGS="-j4" pip install -r requirements.txt

tests: venv blns.base64.json
	. venv/bin/activate && python -m unittest scarf.core.test

run: venv
	. venv/bin/activate && python run.py

docs: venv
	. venv/bin/activate && pydoc -w ./
	mkdir docs
	mv *.html docs

update: blns.base64.json
	git pull

blns.base64.json:
	curl https://raw.githubusercontent.com/minimaxir/big-list-of-naughty-strings/master/blns.base64.json > blns.base64.json

clean:
	find -name "*.pyc" -exec rm -v {} \;
	rm -rfv venv docs tests.log blns.base64.json

dbhost = $(shell grep DBHOST scarf/config.py | cut -d"'" -f2)
dbname = $(shell grep DBNAME scarf/config.py | cut -d"'" -f2)
username = $(shell grep DBUSER scarf/config.py | cut -d"'" -f2)
passwd = $(shell grep DBPASS scarf/config.py | cut -d"'" -f2)
dumpdb:
	mysqldump --user=${username} --password=${passwd} -h ${dbhost} --no-data ${dbname} | pv  > scarfage.sql

importdb:
	mysql --user=${username} --password=${passwd} -h ${dbhost} ${dbname} < scarfage.sql
