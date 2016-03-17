tests:
	python -m unittest scarf.core.test

clean:
	find -name "*.pyc" -exec rm -v {} \;
	rm -v tests.log
