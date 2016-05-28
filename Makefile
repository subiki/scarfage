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

docs: venv .docs

.docs:
	. venv/bin/activate && sphinx-apidoc -lo docs/source/ scarf
	. venv/bin/activate && sphinx-build docs/source/ docs

tempfile := $(shell tempfile)

gh-pages: clean .gh-pages docs
	-rm *
	rm -rfv scarf venv
	mv -v docs/* .
	rm -rf docs source
	touch .nojekyll
	git add -A
	git commit -m "Generated gh-pages"
	git push --force origin gh-pages
	git checkout master
	git branch -D gh-pages
	cp ${tempfile} scarf/config.py
	
.gh-pages:
	cp scarf/config.py ${tempfile}
	git checkout -b gh-pages
	cp ${tempfile} scarf/config.py

update: blns.base64.json
	git pull

blns.base64.json:
	curl https://raw.githubusercontent.com/minimaxir/big-list-of-naughty-strings/master/blns.base64.json > blns.base64.json

clean: docclean
	find -name "*.pyc" -exec rm -v {} \;
	rm -rfv venv tests.log blns.base64.json

docclean:
	rm -rfv docs/objects.inv docs/*.html docs/*.rst docs/*.js docs/_sources docs/_static docs/.buildinfo docs/.doctrees docs/.nojekyll

dbhost = $(shell grep DBHOST scarf/config.py | cut -d"'" -f2)
dbname = $(shell grep DBNAME scarf/config.py | cut -d"'" -f2)
username = $(shell grep DBUSER scarf/config.py | cut -d"'" -f2)
passwd = $(shell grep DBPASS scarf/config.py | cut -d"'" -f2)
dumpdb:
	mysqldump --user=${username} --password=${passwd} -h ${dbhost} --no-data ${dbname} | pv  > scarfage.sql

importdb:
	mysql --user=${username} --password=${passwd} -h ${dbhost} ${dbname} < scarfage.sql
