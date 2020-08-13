all: clean exec

clean:
	-find . -name __pycache__ | xargs rm -r
	-rm -r dist build

exec:
	pyinstaller --clean --onefile \
	-p search/digikey_api/ \
	-p kicad/ \
	-p database/inventree-python/ \
	kintree_gui.py
	-mkdir dist/config
	-mkdir dist/kicad
	-cp -r config/kicad/ dist/config/
	-cp -r config/digikey/ dist/config/
	-cp -r config/inventree/ dist/config/
	-cp config/version.yaml dist/config/
	-cp -r kicad/templates/ dist/kicad/
	
test:
	python run_tests.py
