help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "   clean 	removes all META-* and egg-info/ files created by build tools"
	@echo "   sdist 	make a source distribution"
	@echo "   bdist 	make an egg distribution"
	@echo "   install 	install package"
	@echo "   publish 	publish to pypi.python.org"

cleanmeta:
	-rm -rf gretis.egg-info

clean: cleanmeta
	-rm -rf dist
	-rm -rf build
	-find . -type f -name "*.orig" -exec rm -f "{}" \;
	-find . -type f -name "*.rej" -exec rm -f "{}" \;
	-find . -type f -name "*.pyc" -exec rm -f "{}" \;
	-find . -type f -name "*.parse-index" -exec rm -f "{}" \;

sdist: cleanmeta
	python setup.py sdist

bdist: cleanmeta
	python setup.py bdist_egg

install:
	python setup.py install

publish:
	python setup.py sdist register upload

