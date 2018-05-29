INSTALL_DIR ?= ~/dotfiles/bin

install: package
	cp dist/tasky $(INSTALL_DIR)

clean:
	rm -rf dist

package: clean
	pyinstaller --onefile tasky.py

