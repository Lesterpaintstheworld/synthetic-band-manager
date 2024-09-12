import PyInstaller.__main__
import os
import sys
import site
import PyQt5
import numpy as np

# Ajouter le répertoire courant au chemin de recherche
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

# Obtenir le chemin des packages site-packages
site_packages = site.getsitepackages()[0]

# Obtenir le chemin d'installation de PyQt5
pyqt5_path = os.path.dirname(PyQt5.__file__)

# Obtenir le chemin d'installation de NumPy
numpy_path = os.path.dirname(np.__file__)

options = [
    'main.py',
    '--name=BandManager',
    '--onefile',
    '--windowed',
    '--add-data', f'{current_dir}\\prompts;prompts',
    '--add-data', f'{current_dir}\\*.md;.',
    '--add-data', f'{current_dir}\\*.json;.',
    '--add-data', f'{current_dir}\\style.css;.',
    '--add-data', f'{current_dir}\\spinner.gif;.',
    '--add-data', f'{current_dir}\\.env;.',
    '--add-data', f'{current_dir}\\splash.png;.',
    '--icon', f'{current_dir}/icon.ico',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
    '--hidden-import=openai',
    '--hidden-import=dotenv',
    '--hidden-import=numpy',
    '--hidden-import=numpy.core._dtype_ctypes',
    '--exclude-module=transformers',
    '--exclude-module=torch',
    '--exclude-module=tensorflow',
    '--noupx',
    '--log-level=DEBUG',
]

if sys.platform.startswith('win'):
    options.extend([
        '--add-binary', f'{pyqt5_path}\\Qt5\\bin\\Qt5Core.dll;PyQt5/Qt5/bin',
        '--add-binary', f'{pyqt5_path}\\Qt5\\bin\\Qt5Gui.dll;PyQt5/Qt5/bin',
        '--add-binary', f'{pyqt5_path}\\Qt5\\bin\\Qt5Widgets.dll;PyQt5/Qt5/bin',
        '--add-binary', f'{pyqt5_path}\\Qt5\\plugins\\platforms\\qwindows.dll;PyQt5/Qt5/plugins/platforms',
        '--add-data', f'{numpy_path};numpy',
    ])

# Ajouter tous les fichiers de NumPy
for root, dirs, files in os.walk(numpy_path):
    for file in files:
        full_path = os.path.join(root, file)
        relative_path = os.path.relpath(full_path, numpy_path)
        options.extend(['--add-data', f'{full_path};numpy\\{relative_path}'])

PyInstaller.__main__.run(options)

# Afficher le chemin de l'exécutable généré
output_path = os.path.join(current_dir, 'dist', 'BandManager.exe')
print(f"Exécutable généré : {output_path}")
