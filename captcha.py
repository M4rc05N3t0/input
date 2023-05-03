import base64

from banco_operacoes import Operacoes
import socket
import requests
from time import sleep
import tempfile

# db = Operacoes()
hostname = socket.gethostname()
# rpa_key = db.obterKey()


class Captcha:

    def __init__(self, ambiente):
        self.db = Operacoes(ambiente)
        self.token_captcha = self.db.obter_parametro(nome="token_captcha", vertical="rpa")

    def recaptcha(self, url, site_key):
        try:
            resultado = requests.get(url=f"http://2captcha.com/in.php?key={self.token_captcha}&method=userrecaptcha&googlekey={site_key}&pageurl={url}")
            status, token = "", ""
            while status == "" or status == "CAPCHA_NOT_READY" or status == "503 Service Unavailable":
                token = requests.get(url=f"http://2captcha.com/res.php?key={self.token_captcha}&action=get&id={resultado.text.split('%7C')[1]}")
                status = token.text
                sleep(1)
        except Exception as e:
            return f"Erro: {e}"
        else:
            return token.text.split("|")[1]

    def imagem(self, imagem):
        try:
            data = {"body": base64.b64encode(imagem)}
            resultado = requests.post(url=f"http://2captcha.com/in.php?key={self.token_captcha}&method=base64", data=data)

            # with tempfile.TemporaryDirectory() as temp_file:
            #     arquivo_temporario = open(f'{temp_file}\\captcha.png', 'wb')
            #     arquivo_temporario.write(imagem)
            #     arquivo_temporario.close()
            #     print(f'{temp_file}\\captcha.png')
            #     print('sadsadsd')

            #     with open(f'{temp_file}\\captcha.png', 'rb') as arquivo:
            #         files = {"media": base64.b64encode(arquivo.read())}
            #         resultado = requests.post(url=f"http://2captcha.com/in.php?key={self.token_captcha}&method=post", files=files)
            # print(resultado.text)
            if resultado.status_code != 200:
                raise Exception(resultado.text)
            status, texto = "", ""
            while status == "" or status == "CAPCHA_NOT_READY" or status == "503 Service Unavailable":
                try:
                    texto = requests.get(url=f"http://2captcha.com/res.php?key={self.token_captcha}&action=get&id={resultado.text.split('|')[1]}")
                    status = texto.text
                    sleep(1)
                except:
                    return ""
        except Exception as e:
            return f"Erro: {e}"
        else:
            if texto.text.__contains__("|"):
                return texto.text.split("|")[1]
            else:
                return ""
