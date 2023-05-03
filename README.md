pyinstaller --onefile main.py --name ItauSaqueAniversario.exe --add-data '.env;.' --add-data 'ca.crt;seleniumwire' --add-data 'ca.key;seleniumwire' --clean

