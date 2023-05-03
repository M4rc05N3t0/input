import keyboard
import pywinauto
from pywinauto.keyboard import send_keys
from selenium import webdriver
from seleniumwire import webdriver as webdriver_getresponse
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
# from selenium.common.exceptions import TimeoutException
# from selenium.common.exceptions import StaleElementReferenceException
# from selenium.common.exceptions import ElementClickInterceptedException
# from subprocess import Popen, CREATE_NEW_CONSOLE
from log import Log
from time import sleep
import os
import unicodedata


class ComandosWeb:

    def __init__(self, ambiente, navegador_nome):
        try:
            self.log = Log(ambiente)
            self.log.logar_mensagem(f'>>> ComandosWeb.__init__(ambiente={ambiente}, navegador_nome={navegador_nome})')
            self.janela_principal = ""
            self.navegador_nome = navegador_nome
            self.fechar_navegador()
            if navegador_nome == "chrome":
                driver = r"C:\RPA\chromedriver.exe"  # Chrome

                options = webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                options.add_experimental_option("useAutomationExtension", False)  # Adding Argument to Not Use Automation Extension
                # options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Excluding enable-automation Switch
                options.add_argument("disable-popup-blocking")
                options.add_argument("disable-notifications")
                options.add_argument("disable-gpu")  # renderer timeout
                options.add_argument("disable-web-security")
                # options.add_argument("user-data-dir=")
                self.navegador = webdriver_getresponse.Chrome(executable_path=driver, options=options)
            elif navegador_nome == "ie":
                print("\n\n\n* * * AVISO * * *\n\nCERTIFIQUE-SE DE QUE O MODO PROTEGIDO DO INTERNET EXPLORER ESTEJA DESATIVADO\n\n\n")
                driver = r"C:\RPA\IEDriverServer.exe"  # Internet Explorer

                ieOptions = webdriver.IeOptions()
                ieOptions.add_additional_option("ie.edgepath", 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
                ieOptions.attach_to_edge_chrome = True
                ieOptions.ignore_protected_mode_settings = True
                # ieOptions.accept_insecure_certs = True
                ieOptions.add_additional_option("ie.edgechromium", True)
                ieOptions.ignore_zoom_level = True
                self.navegador = webdriver.Ie(executable_path=driver, options=ieOptions)
            elif navegador_nome == "edge":  # todo IMPLEMENTAR OPÇÕES PARA O EDGE
                driver = r"C:\RPA\msedgedriver.exe"  # Edge

            self.navegador.maximize_window()
            self.acoes = ActionChains(self.navegador)
            self.log.logar_mensagem(f'<<< ComandosWeb.__init__()')

            # self.executar_javascript("""
            # var script = document.createElement( 'script' );
            # script.type = 'text/javascript';
            # script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js';
            # document.head.appendChild(script);
            # """)

        except Exception as e:
            raise Exception(f"Falha ao inicializar comandos_web: {e}")

    def __obter_seletor(self, seletor):
        if seletor == "id":
            return By.ID, "#"
        elif seletor == "xpath":
            return By.XPATH, ""
        elif seletor == "name":
            return By.NAME, ""
        elif seletor == "css":
            return By.CSS_SELECTOR, ""
        elif seletor == "class":
            return By.CLASS_NAME, "."
        else:
            return "", ""

    def obter_elemento(self, seletor, elemento):
        tipo_seletor = self.__obter_seletor(seletor)[0]
        return self.navegador.find_element(tipo_seletor, elemento)

    def esperar_elemento(self, seletor, elemento, tempo=5, javascript=False, desaparecer=False, iframe=""):
        # TODO VALIDAR QTDE DE IDs para seletor ID - não pode ser maior que 1
        self.log.logar_mensagem(f'Esperar elemento "{elemento}"{" desaparecer" if desaparecer else ""} por "{seletor}", usando {("Javascript" if javascript else "Selenium")}')
        if javascript:
            simbolo_seletor = self.__obter_seletor(seletor)[1]
            try:
                for i in range(1, tempo):
                    if iframe:
                        if self.navegador_nome == "ie":
                            retorno = self.navegador.execute_script(f"return $('{simbolo_seletor}{elemento}', top.frames['{iframe}'].document).length {'==' if desaparecer else '!='} 0;")
                        else:
                            retorno = self.navegador.execute_script(f"return top.frames['{iframe}'].document.querySelector('{simbolo_seletor}{elemento}').length {'==' if desaparecer else '!='} 0;")
                    else:
                        if self.navegador_nome == "ie":
                            retorno = self.navegador.execute_script(f"return $('{simbolo_seletor}{elemento}').length {'==' if desaparecer else '!='} 0;")
                        else:
                            retorno = self.navegador.execute_script(f"return document.querySelector('{simbolo_seletor}{elemento}').length {'==' if desaparecer else '!='} 0;")
                    if retorno:
                        return True
                    sleep(1)
                return False
            except Exception as e:
                print(e)
                return False
        else:
            tipo_seletor = self.__obter_seletor(seletor)[0]
            try:
                WebDriverWait(self.navegador, tempo).until(EC.presence_of_element_located((tipo_seletor, elemento)))
                WebDriverWait(self.navegador, tempo).until(EC.element_to_be_clickable((tipo_seletor, elemento)))
                # WebDriverWait(self.navegador, tempo).until(EC.visibility_of((tipo_seletor, elemento)))
                return True
            except:
                return False

    def esperar_url(self, url, tempo=15):
        tempo_total = 0
        url_atual = ""
        while url != url_atual:
            url_atual = self.executar_javascript("window.location.href", True)
            sleep(1)
            if tempo_total > tempo:
                return False
            tempo_total = tempo_total + 1
        return True

    def clicar_elemento(self, seletor, elemento, tempo=5, javascript=False, iframe=""):
        self.log.logar_mensagem(f'Clicar no elemento "{elemento}" por "{seletor}", usando {("Javascript" if javascript else "Selenium")}')
        esperar = self.esperar_elemento(seletor, elemento, tempo, javascript, False, iframe)
        if esperar:
            if javascript:
                simbolo_seletor = self.__obter_seletor(seletor)[1]
                if iframe:
                    self.navegador.execute_script(f"top.frames['{iframe}'].document.querySelector('{simbolo_seletor}{elemento}').click();")
                else:
                    self.navegador.execute_script(f"document.querySelector('{simbolo_seletor}{elemento}').click()")
            else:
                self.navegador.execute_script("arguments[0].click();", self.obter_elemento(seletor, elemento))
            return True
        else:
            return False

    def executar_javascript(self, instrucao, retorno=False):
        self.log.logar_mensagem(f'Executar instrução javascript:\n"{instrucao}"\n')
        try:
            return self.navegador.execute_script(f"{'return ' if retorno else ''}{instrucao}")
        except:
            return ""

    def selecionar_combo(self, seletor, elemento, texto):
        tipo_seletor = self.__obter_seletor(seletor)[1]
        return self.executar_javascript("""
                $('""" + tipo_seletor + elemento + """').each(function(i, valor) {
                if(valor.innerText == '""" + texto + """') {
                    $(this).click();
                };
            });""")

    def selecionar_combo_simples(self, seletor, elemento, valor, tempo=5, javascript=False, contem=False, simular_humano=False, iframe=""):
        if not valor:
            return False
        esperar = self.esperar_elemento(seletor, elemento, tempo, javascript, iframe=iframe)
        if esperar:
            if javascript:
                # $($x('/html/body/div[1]/div[2]/main/div[2]/div/section[4]/div/div[1]/form/div[1]/select/option'));
                self.executar_javascript("""
                    var elemento = '%s';
                    var elementos = document.querySelectorAll(elemento + ' > option');
                    for (var i = 0; i < elementos.length; i++) {
                        if (elementos[i].innerText%s) {
                            elementos[i].setAttribute('selected', 'selected');
                        }
                    };
                    // elemento.blur();
                    """ % (elemento, (f".includes('{valor}')" if contem else f" == '{valor}'")))
            else:
                Select(self.obter_elemento(seletor, elemento)).select_by_visible_text(valor)
                if simular_humano:
                    self.acoes.send_keys(Keys.TAB)
                    self.acoes.perform()
            return True
        else:
            return False

    def enquanto_javascript(self, instrucao, tempo=5, termo=False):
        tempo_total = 0
        try:
            while self.navegador.execute_script(f"return {instrucao}") != termo:
                print(f"Enquanto > {instrucao}")
                sleep(1)
                tempo_total = tempo_total + 1
                if tempo_total > tempo:
                    return False
            return True
        except:
            return "Erro"

    def definir_valor(self, seletor, elemento, valor="", tempo=5, javascript=False, simular_humano=False, iframe=""):
        self.log.logar_mensagem(f'Atribuir valor "{valor}" no elemento "{elemento}" por "{seletor}", usando {("Javascript" if javascript else "Selenium")}')
        if not valor:
            return True
        try:
            esperar = self.esperar_elemento(seletor, elemento, tempo, javascript)
            if esperar:
                if javascript:
                    if iframe:
                        self.navegador.execute_script(f"top.frames['{iframe}'].document.querySelector('{seletor}{elemento}').value('{valor}');")
                    else:
                        self.navegador.execute_script(f"arguments[0].value = '{valor}';", self.obter_elemento(seletor, elemento))
                else:
                    self.obter_elemento(seletor, elemento).send_keys(valor)
                    if simular_humano:
                        self.acoes.send_keys(Keys.TAB)
                        self.acoes.perform()
                return True
            else:
                return False
        except Exception as e:
            return False

    def obter_valor(self, seletor, elemento, tipo="texto", tempo=5, javascript=False):
        self.log.logar_mensagem(f'Obter {tipo} no elemento "{elemento}" por "{seletor}", usando {("Javascript" if javascript else "Selenium")}')
        if tipo == "valor":
            tipo = "value"
        elif tipo == "texto":
            tipo = "textContent"
        else:
            tipo = tipo

        esperar = self.esperar_elemento(seletor, elemento, tempo)
        if esperar:
            # return self.obter_elemento(seletor, elemento).get_attribute("value")
            return self.obter_elemento(seletor, elemento).get_attribute(tipo)  # .text
        else:
            return "Erro"

    def obter_imagem(self, seletor, elemento, nome_arquivo=""):
        self.log.logar_mensagem(f'Obter imagem no elemento "{elemento}" por "{seletor}"')
        return self.obter_elemento(seletor, elemento).screenshot_as_png
        # with open(f'{nome_arquivo}.png', 'wb') as file:
        #     file.write(self.obter_elemento(seletor, elemento).screenshot_as_png)

    def manipular_alerta(self, confirmar=True):
        self.log.logar_mensagem(f'Manipular alerta {"pressionando OK" if confirmar else "pressionando CANCELAR"}')
        try:
            mensagem = self.navegador.switch_to.alert.text
            if confirmar:
                self.navegador.switch_to.alert.accept()
            else:
                self.navegador.switch_to.alert.dismiss()
            return mensagem
        except Exception as e:
            return None

    def alternar_frame(self, seletor=None, elemento=None, voltar=False):
        self.log.logar_mensagem(f'Alternar frame de elemento "{elemento}" por "{seletor}"' if not voltar else "Voltar ao frame anterior")
        if voltar:
            self.navegador.switch_to.parent_frame()
        else:
            self.navegador.switch_to.frame(self.navegador.find_element(seletor, elemento))

    def alternar_janela(self, janela=""):
        self.janela_principal = self.navegador.current_window_handle
        if not janela:
            self.navegador.switch_to.window(self.janela_principal)
        else:
            self.navegador.switch_to.window(janela)

    def focar_proximo(self,):
        self.acoes.send_keys(Keys.TAB)
        self.acoes.perform()

    def navegar_para(self, url):
        self.log.logar_mensagem(f'Navegar para url: {url}')
        self.navegador.get(url)

    def fechar_navegador(self):
        self.log.logar_mensagem(f'Fechar instância do navegador: {self.navegador_nome}')
        # if self.navegador_nome == "ie":
        #     Popen("EncerrarProcessos.exe 60 msedge.exe iexplore.exe IEDriverServer.exe", creationflags=CREATE_NEW_CONSOLE)
        # try:
        #     self.navegador.close()
        # except:
        #     pass
        # if self.navegador_nome == "ie":
        #     os.system("taskkill /f /im EncerrarProcessos.exe /T")
        try:
            self.navegador.quit()
        except Exception as e:
            pass

        if self.navegador_nome == "chrome":
            os.system("taskkill /f /im chromedriver.exe /T")
        elif self.navegador_nome == "ie":
            os.system("taskkill /f /im IEDriverServer.exe /T")
            os.system("taskkill /f /im iexplore.exe /T")
            os.system("taskkill /f /im msedge.exe /T")
        elif self.navegador_nome == "edge":
            os.system("taskkill /f /im msedgedriver.exe /T")  # todo VALIDAR

    def escrever(self, teclas, pressionar_enter=False):
        keyboard.write(teclas, 0.002, True)
        if pressionar_enter:
            keyboard.send('ENTER')

    def enviar_tecla(self, tecla):
        keyboard.send(tecla)

    # NÃO SÃO COMANDOS WEB
    def remover_acentos(self, texto):
        aux = unicodedata.normalize('NFD', texto)
        aux = aux.encode('ascii', 'ignore')
        aux = aux.decode("utf-8")
        aux = aux.replace("'", " ")
        return aux

    def nulo_para_vazio(self, texto):
        return str(texto) if texto else ''

    def substituir_caracteres(self, texto):
        com_acento = "´`~¨*&'.,:;/|\?!{}[]()-+=@#$%§¢°ºª<> "
        sem_acento = "-------------------------------------"
        novo_texto = ""
        for i, caractere in enumerate(texto):
            indice = com_acento.find(caractere)
            if indice > 0:
                novo_texto = novo_texto + sem_acento[indice]
            else:
                novo_texto = novo_texto + caractere
        return novo_texto

    def manipular_caixa_dialogo_abrir(self, caminho_completo):
        pwa_app = pywinauto.Application().connect(path="C:\Windows/explorer.exe")
        w_handle = pywinauto.findwindows.find_windows(title=u'Abrir', class_name='#32770')[0]
        window = pwa_app.window(handle=w_handle)
        ctrl = window['Breadcrumb Parent']
        ctrl.TypeKeys("folder")
        sleep(1)
        pywinauto.keyboard.SendKeys(caminho_completo)

    def obter_resposta_rede(self, tipo=None, filtro_url=None):
        if self.navegador_nome == "chrome":
            # Access requests via the `requests` attribute
            requisicoes = []
            requisicoes_filtradas = []
            for request in self.navegador.requests:
                if request.response:
                    if tipo == "url":
                        requisicoes.append(request.url)
                    elif tipo == "status_code":
                        requisicoes.append(request.response.status_code)
                    elif tipo == "content_type":
                        requisicoes.append(request.response.headers['Content-Type'])
                    elif tipo == "body":
                        requisicoes.append(request.response.body)
                    else:
                        requisicoes.append([request.url, request.response.status_code, request.response.headers['Content-Type'], request.response.body])
            if filtro_url:
                for requisicao in requisicoes:
                    if str(requisicao[0]).__contains__(filtro_url):
                        requisicoes_filtradas.append(requisicao)
                return requisicoes_filtradas
            return requisicoes
