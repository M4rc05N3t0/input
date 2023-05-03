import json
import os
import shutil
import traceback

from banco_operacoes import Operacoes
from comandos_web import ComandosWeb
from http_requests import Request
from notificar import Notificar
from notificar import Notificar
from log import Log
from captcha import Captcha
# from pathlib import Path
from dateutil.relativedelta import relativedelta
from pywinauto.application import Application
import pywinauto as p
from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, CREATE_NEW_CONSOLE
import locale
import socket
import secrets
import re


class Processamento:

    def __init__(self, ambiente, navegador, input=False):
        try:
            self.db = Operacoes(ambiente)
            self.log = Log(ambiente)
            self.log.logar_mensagem(f'>>> Processamento.__init__(ambiente={ambiente}, navegador={navegador})')
            self.notificar = Notificar(self.db.obter_parametro("email_robo", None, None, "rpa"))
            self.captcha = Captcha(ambiente)
            self.request = Request(ambiente)
            self.hostname = socket.gethostname()
            self.input = input
            #self.sistema = f"""fgts-saque-aniversario{"-input" if input else ""}"""
            self.sistema = f"""fgts-saque-aniversario"""
            self.area_negocio = "itau"
            self.vertical = "finance"

            if navegador:
                # if self.db.verificar_registro(id_processo) == 0:
                #     self.log.logar_mensagem('Registro não encontrado')
                #     sys.exit(0)
                # self.id_processo = id_processo
                if navegador == "ie":
                    Popen("EncerrarProcessos.exe 60 msedge.exe iexplore.exe IEDriverServer.exe", creationflags=CREATE_NEW_CONSOLE)
                self.comandos_web = ComandosWeb(ambiente, navegador)
                if navegador == "ie":
                    os.system("taskkill /f /im EncerrarProcessos.exe /T")
                self.navegador = navegador

            self.destinatarios_monitoramento = self.db.obter_parametro("monitoramento", self.sistema, self.area_negocio, self.vertical)
            self.destinatarios_sucesso = self.db.obter_parametro("destinatarios", self.sistema, self.area_negocio, self.vertical)
            self.destinatarios_erro = self.db.obter_parametro("destinatarios_erro", self.sistema, self.area_negocio, self.vertical)
            self.destinatarios_erro_impeditivo = self.db.obter_parametro("destinatarios_erro_impeditivo", self.sistema, self.area_negocio, self.vertical)
            login = self.db.obter_parametro(f"login-{self.hostname}", 'fgts-saque-aniversario-input', self.area_negocio, self.vertical).split(";")
            self.valor_minimo_elegivel = float(self.db.obter_parametro("valor_minimo_elegivel", self.sistema, self.area_negocio, self.vertical))
            if not login:
                raise Exception(f"Não existe login cadastrado para esta máquina - IBConsig")

            self.usuario = login[0]
            self.senha = login[1]
            self.email_usuario = login[2]
            self.logins_icconsig = self.db.obter_parametros(f"login-ICConsig", self.sistema, self.area_negocio, self.vertical)

            # login_icconsig = self.db.obter_parametro(f"login-ICConsig", self.sistema, self.area_negocio, self.vertical).split(";")
            # if not login_icconsig:
            #     raise Exception(f"Não existe login cadastrado para esta máquina - ICConsig")
            #
            # self.usuario_icconsig = login_icconsig[0]
            # self.senha_icconsig = login_icconsig[1]
            # self.email_usuario_icconsig = login_icconsig[2]

            self.mensagem_lentidao = "tempo limite de carregamento de página/elemento excedido"
            # self.caminho_arquivo = r"C:\RPA\ItauSaqueAniversario\ICConsig"
            # self.mover_para = r"C:\RPA\ItauSaqueAniversario\ICConsig\Importados"
            self.origem_doc_proposta = os.path.join(os.environ['USERPROFILE'], r"Downloads\consignacao.pdf")
            # Path(self.caminho_arquivo).mkdir(parents=True, exist_ok=True)
            # Path(self.mover_para).mkdir(parents=True, exist_ok=True)
            self.caminho_arquivo = r"\\Cobawsdc-0001\rpa repository$"
            # self.mover_para = r"\\Cobawsdc-0001\rpa repository$\Importados"

            locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')
            self.fgts_limite_disponivel, self.fgts_valor_liberado, self.resultado, self.tentativas_captcha, \
            self.mensagem_erro, self.sucesso_captcha_consulta, self.texto_captcha_2, self.logado,\
            self.fgts_parcelas_antecipadas, self.numero_proposta, self.valor_antecipar, self.data_hora_input = "", "", "", 1, "", False, False, False, "", "", "", None
            self.erros_impeditivos = ["consultas excedida", "Não é possível prosseguir", "Não existe login cadastrado",
                                      "não tem permissão para efetuar o login nesse horário", "Usuário e/ou senha inválido", "horário limite"]
            self.registro = []
            self.log.logar_mensagem(f'<<< Processamento.__init__()')
        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"""Falha ao inicializar processamento{f": {e}" if str(e) else ""}""")

    def efetuar_login(self):
        self.log.logar_mensagem(f'>>> efetuar_login()')
        try:
            self.comandos_web.navegar_para("https://www.ibconsigweb.com.br/Index.do?method=prepare")
            self.comandos_web.esperar_elemento("xpath", "/html/body/table/tbody/tr[2]/td[3]/table/tbody/tr/td/form/table/tbody/tr[1]/td[3]/input", 60)
            self.verificar_disponibilidade()
            campo_proposta = False
            while not campo_proposta:
                sucesso_captcha_login = False
                while not sucesso_captcha_login:
                    # self.comandos_web.esperar_elemento("xpath", "/html/body/table/tbody/tr[2]/td[3]/table/tbody/tr/td/form/table/tbody/tr[1]/td[3]/input")
                    # self.comandos_web.executar_javascript("""
                    #     $("#Table_02 > tbody > tr > td > form > table > tbody > tr:nth-child(1) > td:nth-child(3) > input").val('');
                    #     $("#Table_02 > tbody > tr > td > form > table > tbody > tr:nth-child(2) > td:nth-child(2) > font > strong > input").val('');""")
                    self.comandos_web.definir_valor("xpath", "/html/body/table/tbody/tr[2]/td[3]/table/tbody/tr/td/form/table/tbody/tr[1]/td[3]/input", self.usuario)
                    self.comandos_web.definir_valor("xpath", "/html/body/table/tbody/tr[2]/td[3]/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/font/strong/input", self.senha)
                    imagem_captcha_login = self.comandos_web.obter_imagem("name", "iCaptcha")
                    self.log.logar_mensagem("Resolver captcha")
                    codigo_imagem = self.captcha.imagem(imagem_captcha_login)
                    if not codigo_imagem.__contains__("Erro"):
                        sucesso_captcha_login = True
                        self.db.registrar_captcha(self.hostname)

                    self.comandos_web.definir_valor("xpath", "/html/body/table/tbody/tr[2]/td[3]/table/tbody/tr/td/form/table/tbody/tr[4]/td/table/tbody/tr[1]/td[2]/input", codigo_imagem)
                    self.comandos_web.executar_javascript("loginSubmit();")
                    sleep(2)
                    self.aguardar_carregamento()
                    # mensagem_existe = self.comandos_web.esperar_elemento("css", "#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font")
                    # mensagem_existe = self.comandos_web.enquanto_javascript("""$('#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font').length != 0""")
                    try:
                        self.comandos_web.manipular_alerta()
                    except:
                        pass
                    self.comandos_web.enquanto_javascript("""$('#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font').length != 0;""")
                    mensagem_existe = self.comandos_web.executar_javascript("""$('#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font').length != 0""", True)
                    if mensagem_existe:
                        # mensagem_texto = self.comandos_web.obter_valor("css", "#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font")
                        # mensagem_texto = self.comandos_web.executar_javascript("""$('#Table_01 > tbody > tr:nth-child(3) > td > table:nth-child(3) > tbody > tr:nth-child(1) > td > font').innerText;""", True)
                        mensagem_texto = self.comandos_web.executar_javascript("""$('font.erro').text();""", True).strip()
                        if mensagem_texto.__contains__("inválida"):
                            sucesso_captcha_login = False
                            continue
                        # elif mensagem_texto.__contains__("acesso simultâneo"):
                        #     raise Exception(f"[{self.usuario}]: Acesso simultâneo detectado")

                        else:
                            raise Exception(f"{mensagem_texto}")

                    self.verificar_disponibilidade()
                    # campo_proposta = self.comandos_web.esperar_url("https://www.ibconsigweb.com.br/principal/fsconsignataria.jsp")
                    campo_proposta = self.comandos_web.executar_javascript("""$('.aviso', frames['rightFrame'].document).length == 0;""", True)
                    # campo_proposta = self.comandos_web.esperar_elemento("id", "top")
                    if not campo_proposta:
                        # valor_elemento = self.comandos_web.obter_valor("css", "body > form > center:nth-child(2) > table > tbody > tr:nth-child(2) > td > table > tbody > tr > td:nth-child(2) > font")

                        valor_elemento = self.comandos_web.executar_javascript("""$('.aviso', frames['rightFrame'].document).text();""", True)
                        if valor_elemento.__contains__("senha expirou"):
                            campo_proposta = self.alterar_senha()

        except Exception as e:
            raise Exception(f"""Falha ao realizar login{f": {e}" if str(e) else ""}""")
        else:
            self.logado = True
            return "OK"

    def alterar_senha(self):
        self.log.logar_mensagem(f'>>> alterar_senha()')
        sucesso = False
        while not sucesso:
            self.comandos_web.alternar_frame("id", "rightFr")
            self.comandos_web.definir_valor("css", "body > form > center:nth-child(3) > table > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(2) > td.CEDmeio > input", self.senha)
            nova_senha = secrets.token_urlsafe(10)
            self.comandos_web.definir_valor("id", "newpassword", nova_senha)
            self.comandos_web.definir_valor("css", "body > form > center:nth-child(3) > table > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(4) > td.CEDmeio > input", nova_senha)
            self.comandos_web.definir_valor("css", "body > form > center:nth-child(3) > table > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(5) > td.CEDmeio > input", "Gerada pelo RPA")
            self.comandos_web.clicar_elemento("css", "body > form > table > tbody > tr > td:nth-child(1) > a")
            self.aguardar_carregamento()
            self.comandos_web.alternar_frame(voltar=True)
            mensagem = self.comandos_web.executar_javascript("""$('.TituloTabela', frames['rightFrame'].document).text();""", True)
            if mensagem:
                if mensagem.__contains__("não foi atingido"):
                    continue
            else:
                continue
            sucesso = True
            self.db.atualizar_senha(self.usuario, nova_senha, self.email_usuario, self.hostname)
            self.notificar.enviar_email(f"[SENHA] ITAÚ - Saque Aniversário - {self.hostname}", f"""
                Sua senha do IBConsig expirou.
    
                Usuário: {self.usuario}
                Nova senha: {nova_senha}
            """, self.email_usuario)

        return True  # self.comandos_web.esperar_elemento("id", "top")

    def verificar_disponibilidade(self):
        self.log.logar_mensagem(f'>>> verificar_disponibilidade()')
        url = str(self.comandos_web.executar_javascript("document.location.href;", True))
        if url.__contains__("j_security_check"):
            raise Exception(f"Página indisponível")

    def verificar_horario(self, input):
        self.log.logar_mensagem(f'>>> verificar_horario(input={input})')
        hora_atual = int(datetime.now().strftime("%H"))
        minuto_atual = int(datetime.now().strftime("%m"))
        horario_limite = self.db.obter_parametro("horario_limite", self.sistema, self.area_negocio, self.vertical)
        hora_limite = int(horario_limite.split(":")[0])
        minuto_limite = int(horario_limite.split(":")[1])
        mensagem = ""
        if hora_atual >= hora_limite:
            if minuto_atual >= minuto_limite:
                mensagem = "Horário limite atingido"
                self.efetuar_logout()
                # sys.exit()
        if mensagem:
            self.log.logar_mensagem(mensagem, True)
        return self.obter_espera(mensagem)

    def efetuar_logout(self):
        self.log.logar_mensagem(f'>>> efetuar_logout()')
        if self.logado:
            if self.navegador == "ie":
                # self.comandos_web.alternar_frame("id", "topFrame")
                self.comandos_web.executar_javascript("""window.open('../login/logout.jsp', 'rightFrame');""")
                # self.comandos_web.clicar_elemento("css", "#item_barra_funcao > span:nth-child(4) > a:nth-child(1)", 5, True, "topFrame")
                # self.comandos_web.esperar_elemento("css", "#buttonLink", 5, True, False, "rightFrame")
                sleep(1)
                # self.comandos_web.clicar_elemento("css", "#buttonLink")
                self.comandos_web.executar_javascript("""window.open("javascript:setAcao('logout')", 'rightFrame');""")
                sleep(1)
                self.comandos_web.manipular_alerta()
                sleep(1)
                self.logado = False
                self.comandos_web.fechar_navegador()
            elif self.navegador == "chrome":
                self.efetuar_logout_icconsig()
        # self.comandos_web.alternar_frame(voltar=True)

    def resolver_captcha(self):
        self.log.logar_mensagem(f'>>> resolver_captcha()')
        self.comandos_web.executar_javascript("""var src = $("span[id='identificacao-form:idCaptcha:idImagemCaptcha'] > img",frames['rightFrame'].document).attr('src');var elemento = document.createElement('img');
            var url = 'https://www.ibconsigweb.com.br' + src;
            elemento.setAttribute('src', url);
            elemento.setAttribute('style', "width: 180px; height: 80px");
            
            elemento.setAttribute('id', 'imagem-captcha');
            $('html').append(elemento);""")
        self.comandos_web.esperar_elemento("id", "imagem-captcha")
        recorte = self.comandos_web.obter_imagem("id", "imagem-captcha")
        self.texto_captcha_2 = self.captcha.imagem(recorte)
        if not self.texto_captcha_2.__contains__("Erro"):
            self.sucesso_captcha_consulta = True
            self.db.registrar_captcha(self.hostname)
        self.comandos_web.executar_javascript("$('#imagem-captcha').remove();")

    def consultar_cpf(self, registro, executar_input=False):
        self.log.logar_mensagem(f'>>> consultar_cpf(registro=\n{registro},\n executar_input={executar_input})')
        try:
            if not registro["fgts_valor_contratado"] and executar_input:
                self.resultado = "RPA: Valor contratado ausente"
                return
        except:
            pass
        try:
            # self.comandos_web.alternar_frame("name", "leftFrame")
            self.fgts_limite_disponivel, self.fgts_valor_liberado, self.resultado, self.tentativas_captcha, self.mensagem_erro, \
            self.fgts_parcelas_antecipadas, self.numero_proposta, self.valor_antecipar, self.data_hora_input = "", "", "", 1, "", "", "", "", None

            if self.navegador == "chrome":
                # self.comandos_web.executar_javascript("""top.frames['leftFrame'].document.querySelector('#slidingMenu > div > div:nth-child(2) > a:nth-child(1)').click();""")
                self.comandos_web.clicar_elemento("css", "#slidingMenu > div > div:nth-child(2) > a:nth-child(1)", 5, True, "leftFrame")
            else:
                self.comandos_web.executar_javascript("""window.open('/consignacao/identificacao.jsf', 'rightFrame');""")
            self.comandos_web.esperar_elemento("id", "rightFr", 15)
            sleep(1)
            url_frame = self.comandos_web.executar_javascript("""window.frames['rightFrame'].location.href""", True)
            if url_frame != "https://www.ibconsigweb.com.br/consignacao/identificacao.jsf":
                raise Exception("A página de consulta não carregou")
            mensagem_card = self.comandos_web.esperar_elemento("css", "#global-msg > li.error_message", 5, True, False, "rightFrame")
            if mensagem_card:
                # self.resultado = self.comandos_web.obter_valor("id", "global-msg")

                # ALTERADO DE self.resultado PARA self.mensagem_erro
                # self.mensagem_erro = self.comandos_web.executar_javascript("""top.frames['rightFrame'].document.querySelector('#global-msg').innerText;""", True)
                self.mensagem_erro = self.comandos_web.executar_javascript("""$('#global-msg').text();""", True)
                return False
            self.verificar_disponibilidade()
            self.comandos_web.alternar_frame("id", "rightFr")
            self.comandos_web.definir_valor("id", "identificacao-form:orgao:find:txt-value", "11-", simular_humano=True)
            # self.comandos_web.clicar_elemento("css", ".curr_img", 5, True, "rightFrame")
            ## self.comandos_web.clicar_elemento("css", ".curr_img")
            ## self.comandos_web.esperar_elemento("id", "waitDiv", 60, True, True, "rightFrame")
            self.aguardar_carregamento(20)
            sleep(1)
            # self.comandos_web.definir_valor("id", "identificacao-form:cpf", cpf, 5, True, "rightFrame")
            self.comandos_web.definir_valor("id", "identificacao-form:cpf", str(registro["cpf"]).zfill(11))
            self.sucesso_captcha_consulta = False
            while not self.sucesso_captcha_consulta:
                if self.tentativas_captcha > 3:
                    # self.erro = True
                    return False
                # self.resolver_captcha()
                # sleep(1)
                imagem_captcha_consulta = self.comandos_web.obter_imagem("css", ".curr_img")
                # imagem_captcha_consulta = self.comandos_web.obter_imagem("css", "#identificacao-form\:idCaptcha\:idImagemCaptcha > img")
                # self.comandos_web.alternar_frame(voltar=True)
                codigo_imagem = self.captcha.imagem(imagem_captcha_consulta)
                if not codigo_imagem.__contains__("Erro"):
                    self.sucesso_captcha_consulta = True
                    self.db.registrar_captcha(self.hostname)
                if not self.sucesso_captcha_consulta:
                    self.tentativas_captcha =+ 1
                    continue
                self.texto_captcha_2 = self.comandos_web.definir_valor("id", "identificacao-form:idCaptcha:txt-value", codigo_imagem)
                self.comandos_web.clicar_elemento("id", "identificacao-form:idCommandLink")
                if not executar_input:
                    self.db.registrar_consulta(registro["id"], self.usuario)
                self.aguardar_carregamento(60)
                self.comandos_web.enquanto_javascript("""$("#servidor.dataNascimento").length != 0;""", 5)
                carregou = self.comandos_web.esperar_elemento("id", "servidor.dataNascimento", 2)

                if not carregou:
                    # sleep(2)
                    # self.comandos_web.esperar_elemento("id", "waitDiv", 60, True, True, "rightFrame")
                    self.verificar_disponibilidade()
                    #
                    if not self.verificar_erro_interno():
                        return False
                    # mensagem_card = self.comandos_web.esperar_elemento("id", "global-msg")
                    existe_proposta = self.comandos_web.executar_javascript("""$('#identificacao-form > div.ui-dialog.ui-widget.ui-widget-content.ui-corner-all.ui-shadow.ui-overlay-visible > div.ui-dialog-content.ui-widget-content > div:nth-child(1)').text();""", True)
                    if existe_proposta:
                        if existe_proposta.__contains__("Já existe uma proposta em andamento"):
                            self.resultado = "Já existe uma proposta em andamento para esse CPF"
                            return True
                    self.comandos_web.enquanto_javascript("""document.getElementById('global-msg').length != 1;""", 3)
                    mensagem_card = self.comandos_web.esperar_elemento("css", "#global-msg", 5, True, False, "rightFrame")
                    if mensagem_card:
                        # self.resultado = self.comandos_web.obter_valor("css", "#global-msg > li")
                        self.resultado = self.comandos_web.executar_javascript("""$('#global-msg > li').text();""", True)
                        if self.resultado.__contains__("imagem está incorreta") \
                                or self.resultado.__contains__("verificação expirou") \
                                or self.resultado.__contains__("Erro ao consultar saldo do cliente"):
                            # self.comandos_web.executar_javascript(r"""top.frames['rightFrame'].document.querySelector('#identificacao-form\\:idCaptcha\\:txt-value').value = ''""")
                            self.comandos_web.executar_javascript("""$("input[id='identificacao-form:idCaptcha:txt-value']").val('');""")
                            self.tentativas_captcha =+ 1
                            self.sucesso_captcha_consulta = False
                            self.resultado = ""
                            continue
                        else:
                            return True

                detalhes_existe = self.comandos_web.esperar_elemento("css", "#codigoRegistro > tbody > tr > td:nth-child(6) > a", 2)
                if detalhes_existe:
                    self.comandos_web.clicar_elemento("css", "#codigoRegistro > tbody > tr > td:nth-child(6) > a")
                    self.verificar_disponibilidade()
                # carregou = self.comandos_web.esperar_elemento("id", "label_ade.valorEmprestimo", 15)
                # if not carregou:
                #     raise Exception("Página não carregou")
                # sleep(1)
            else:
                valores_fgts = self.comandos_web.executar_javascript("""
                    function Valores() {
                        var lista = [];
                        lista.push($("span[id='label_ade.valorEmprestimo']").text());
                        lista.push($("span[id='label_ade.valorLiberado']").text());
                        lista.push($("span[id='label_ade.quantidadePrestacoes']").text());
                        lista.push($("input[id='ade.valorAntecipacaoFgts']").val().replace(',', '.'));
                        return lista;
                    }
                    return Valores();""")
                try:
                    self.fgts_limite_disponivel, self.fgts_valor_liberado, self.fgts_parcelas_antecipadas, self.valor_antecipar = valores_fgts[0], valores_fgts[1], valores_fgts[2], valores_fgts[3]
                except:
                    self.mensagem_erro = "Erro ao obter os valores da página"
                    return False
                if executar_input:
                    Popen("EncerrarProcessos.exe 360 msedge.exe iexplore.exe IEDriverServer.exe", creationflags=CREATE_NEW_CONSOLE)
                    self.preencher_proposta(registro)
                    os.system("taskkill /f /im EncerrarProcessos.exe /T")

        except Exception as e:
            self.mensagem_erro = str(e)
            return False
        else:
            return True
        finally:
            self.comandos_web.alternar_frame(voltar=True)

    def verificar_erro_interno(self):
        self.log.logar_mensagem(f'>>> verificar_erro_interno()')
        self.mensagem_erro = self.comandos_web.executar_javascript("""
            function verificarErro() {
                var el1 = $("font[class='erro']");
                var el2 = $("li[class='error_message']");
                var erro = '';
                if (el1) {
                    erro = el1.text();
                }
                else if (el2) {
                    erro = el2.text();
                }
                return erro;
            }
            return verificarErro();""")
        if self.mensagem_erro:
            if self.mensagem_erro.__contains__("Erro interno do sistema"):
                # self.erro = True
                return False
        return True

    def persistir_banco(self, id_registro):
        self.log.logar_mensagem(f'>>> persistir_banco(id_registro={id_registro})')
        try:
            if not self.db.verificar_registro(id_registro):
                return True

            if not self.resultado:
                if self.fgts_valor_liberado:
                    valor_liberado = float(self.fgts_valor_liberado)
                    if valor_liberado < self.valor_minimo_elegivel:
                        self.db.atualizar_mensagem(id_registro, f"Cliente não se enquadra no limite mínimo de {self.valor_minimo_elegivel} reais")
                    else:
                        self.db.atualizar_valor(id_registro, self.fgts_valor_liberado, self.fgts_limite_disponivel, self.fgts_parcelas_antecipadas)
                else:
                    self.db.limpar_consulta(id_registro)
                    raise Exception(f"Consulta sem retorno")

            else:
                erros = ["erro inesperado", "verificação expirou", "imagem está incorreta", "consultas excedida", "Não é possível prosseguir", "Conexão finalizada por inatividade"]
                erros_parada = ["consultas excedida", "Não é possível prosseguir"]
                if any(erro in self.resultado for erro in erros):
                    self.db.limpar_consulta(id_registro)
                    if any(erro_parada in self.resultado for erro_parada in erros_parada):
                        self.logado = True
                    raise Exception(f"{self.resultado}")
                else:
                    self.db.atualizar_mensagem(id_registro, self.resultado)
            return True
        except Exception as e:
            raise Exception(f"""Falha ao persistir no banco{f": {e}" if str(e) else ""}""")

    def persistir_banco_input(self, registro):
        self.log.logar_mensagem(f'>>> persistir_banco_input(registro=\n{registro}\n)')
        try:
            if not self.db.verificar_registro(registro["id"], True):
                return True

            if not self.resultado:
                if self.numero_proposta:
                    # mensagem = "Pendente envio do link por SMS (ICConsig)"
                    # sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 2, mensagem, self.numero_proposta, self.fgts_valor_liberado)
                    # self.db.atualizar_status_input(registro["id"], "ag_icconsig" if sucesso else "falha_hs", self.numero_proposta, self.fgts_valor_liberado)

                    self.db.atualizar_status_input(registro["id"], "ag_icconsig", self.numero_proposta, self.fgts_valor_liberado, data_hora_input=self.data_hora_input)
                else:
                    if not self.mensagem_erro:
                        self.mensagem_erro = "Consulta sem retorno"
                    elif not self.mensagem_erro.__contains__("Erro interno do sistema"):
                        raise Exception(self.mensagem_erro)
                    if int(registro["tentativas"]) > 2:
                        sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, self.mensagem_erro)
                        self.db.atualizar_mensagem(registro["id"], self.mensagem_erro, True, "concluido" if sucesso else "falha_hs")
                    else:
                        self.db.limpar_consulta(registro["id"], True)
            else:
                # Erro ao obter os valores da página <- ADICIONAR ERRO?
                erros = ["Erro ao consultar saldo do cliente", "erro inesperado", "verificação expirou", "imagem está incorreta", "consultas excedida", "Não é possível prosseguir"]
                erros_parada = ["consultas excedida", "Não é possível prosseguir"]
                if any(erro in self.resultado for erro in erros):
                    self.db.limpar_consulta(registro["id"], True)
                    if any(erro_parada in self.resultado for erro_parada in erros_parada):
                        self.logado = True
                    raise Exception(f"{self.resultado}")
                else:
                    if self.numero_proposta:
                        sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, self.resultado, self.numero_proposta, self.fgts_valor_liberado)
                        self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs", self.numero_proposta, self.fgts_valor_liberado, mensagem_hubspot=self.resultado, data_hora_input=self.data_hora_input)
                    else:
                        sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, self.resultado)
                        self.db.atualizar_mensagem(registro["id"], self.resultado, True, "concluido" if sucesso else "falha_hs")

            return True
        except Exception as e:
            raise Exception(e if str(e) else "")

    def obter_espera(self, mensagem):
        self.log.logar_mensagem(f'>>> obter_espera(mensagem={mensagem})')
        agora = datetime.now()

        reinicio = agora + timedelta(minutes=5)  # DEFAULT
        espera = int((reinicio - agora).total_seconds())  # DEFAULT

        if mensagem.__contains__("acesso simultâneo"):
            reinicio = agora + timedelta(minutes=12)
            espera = int((reinicio - agora).total_seconds())
        else:
            self.comandos_web.fechar_navegador()
            erros = ["verificação expirou", "imagem está incorreta"]
            erros_criticos = ["erro inesperado", "sem retorno", "erros no processamento", "Ocorreu um erro"]

            if any(erro in mensagem for erro in erros_criticos):
                reinicio = agora + timedelta(minutes=5)
                espera = int((reinicio - agora).total_seconds())

            if any(erro in mensagem for erro in self.erros_impeditivos):
                hora = agora.hour
                if 21 <= hora <= 23:
                    reinicio = datetime.date(datetime.today() + relativedelta(days=1)) + relativedelta(hours=7, minutes=0)
                elif 0 <= hora < 7:
                    reinicio = datetime.today().date() + relativedelta(hours=7, minutes=0)
                else:
                    reinicio = agora + timedelta(hours=2)
                espera = int((reinicio - agora).total_seconds())

        self.log.logar_mensagem(f"       Parada em: {agora}\nPróxima execução: {reinicio} ({espera}s)")

        return espera

        # todo: obter do banco - tabela a ser criada
        # """Ocorreu um erro ao tentar efetuar o login
        #     consultas excedida
        #     Usuário e/ou senha inválido
        #     Acesso simultâneo
        #     Não é possível
        #     Página indisponível
        #     Não é possível prosseguir
        #     Consulta sem retorno
        #     Erro interno do sistema"""


    def processar_registros(self):
        self.log.logar_mensagem(f'>>> processar_registros()')
        registro = self.obter_registro()
        while registro:
            # self.db.atualizar_status(registro["id"])
            sucesso = self.consultar_cpf(registro)
            if not sucesso:
                return self.mensagem_erro
                # if self.mensagem_erro.__contains__("Erro interno do sistema"):
                #     break
            else:

                self.persistir_banco(registro["id"])

            # self.verificar_horario(False)
            registro = self.obter_registro()
        return "OK"

    def processar_registros_input(self):
        self.log.logar_mensagem(f'>>> processar_registros_input()')
        # self.input = True
        self.registro = self.obter_registro(True)
        while self.registro:
            if not self.registro["tentativas"]:
                self.registro["tentativas"] = 1
            else:
                self.registro["tentativas"] += 1
            self.db.atualizar_status_input(self.registro["id"], tentativas=self.registro["tentativas"])
            sucesso = self.consultar_cpf(self.registro, True)
            # if not sucesso:
            #     return self.mensagem_erro
            #     #  # if self.mensagem_erro.__contains__("Erro interno do sistema"):
            #     #  #     break
            # else:

            self.persistir_banco_input(self.registro)

            # self.verificar_horario(True)
            self.registro = self.obter_registro(True)
        return "OK"

    def preencher_proposta(self, registro):
        self.log.logar_mensagem(f'>>> preencher_proposta(registro=\n{registro}\n)')
        if float(self.fgts_valor_liberado) == 0:
            self.resultado = "Valor liberado é igual a 0 (zero)"
            return
        if float(self.fgts_valor_liberado) < float(registro["fgts_valor_contratado"]):
            valor_excedente = float(registro["fgts_valor_contratado"]) - float(self.fgts_valor_liberado)
            percentual = valor_excedente / float(self.fgts_valor_liberado)
            if percentual <= 0.03:
                registro["fgts_valor_contratado"] = self.fgts_valor_liberado
            else:
                # 8.12
                self.resultado = "Saldo liberado é menor que o valor contratado"
                return

        janelas = p.findwindows.find_elements(title_re="Consig - Perfil 1 — Microsoft​ Edge", top_level_only=True)
        if len(janelas) != 1:
            janela = Application(backend='uia').connect(title="Consig - Perfil 1 — Microsoft​ Edge", found_index=0, timeout=500)
            janela.ConsigPerfil1MicrosoftEdge.child_window(control_type="Button", found_index=0).wrapper_object().click_input()
        self.comandos_web.enquanto_javascript("""$("#confirmar").length != 0;""", 3)
        botao_confirmar = self.comandos_web.esperar_elemento("id", "confirmar", 2)
        if not botao_confirmar:
            self.resultado = "RPA: Botão Confirmar ausente no IBConsig"
            return True

        loja = self.comandos_web.executar_javascript(r"""$("#ade\\.loja").attr('type') == "text";""", True)
        if loja:
            self.comandos_web.definir_valor("css", "#ade\.loja", "48708")

        data_renda_completa = 0
        try:
            fgts_data_da_renda = int(registro["fgts_data_da_renda"])
            hoje = datetime.today()
            if fgts_data_da_renda:
                if fgts_data_da_renda > 27:
                    data_renda_completa = datetime.strptime(f"""01/{hoje.month}/{hoje.year}""", "%d/%m/%Y") - relativedelta(days=1)
                else:
                    data_renda_completa = datetime.today().strptime(f"""{fgts_data_da_renda}/{hoje.month}/{hoje.year}""", "%d/%m/%Y")
                if data_renda_completa > hoje:
                    data_renda_completa = data_renda_completa - relativedelta(months=1)
                # self.comandos_web.definir_valor("css", "#registro\.dataRenda", str(registro["fgts_data_da_renda"]) + datetime.now().strftime("/%m/%Y"))
                self.comandos_web.definir_valor("css", "#registro\.dataRenda", data_renda_completa.strftime("%d/%m/%Y"))
        except Exception as e:
            self.log.logar_mensagem(f"Erro ao processar regra de negócio.\n    Não preencheu fgts_data_da_renda:\n    {e}")

        try:
            fgts_data_de_admissao = registro["fgts_data_de_admissao"]
            if fgts_data_de_admissao:
                fgts_data_de_admissao = datetime.strptime(registro["fgts_data_de_admissao"], "%Y-%m-%d")
                self.comandos_web.executar_javascript("""$("input[id='registro.dataAdmissao']").val('');""")
                if fgts_data_de_admissao > data_renda_completa:
                    data_renda_completa = data_renda_completa - relativedelta(months=1)
                    self.comandos_web.definir_valor("css", "#registro\.dataAdmissao", data_renda_completa.strftime("%d/%m/%Y"))
                else:
                    self.comandos_web.definir_valor("css", "#registro\.dataAdmissao", fgts_data_de_admissao.strftime("%d/%m/%Y"))
        except Exception as e:
            self.log.logar_mensagem(f"Erro ao processar regra de negócio.\n    Não preencheu fgts_data_de_admissao:\n    {e}")
        self.comandos_web.definir_valor("css", "#registro\.renda", registro["fgts_valor_da_renda"])
        self.comandos_web.definir_valor("css", "#registro\.cargo", registro["fgts_cargo_geral"][0:19])
        if self.navegador == "chrome":
            self.comandos_web.selecionar_combo_simples("css", "#servidor\.grauInstrucao", registro["grau_instrucao"], javascript=True)
            self.comandos_web.selecionar_combo_simples("css", "#servidor\.profissao", "Outros trabalhadores de serviços diversos")
            self.comandos_web.selecionar_combo_simples("css", "#dadosBancarios\.formaCredito", "TED Conta Corrente")
        else:
            self.comandos_web.definir_valor("css", "#servidor\.grauInstrucao", registro["grau_instrucao"])
            self.comandos_web.definir_valor("css", "#servidor\.profissao", "Outros trabalhadores de serviços diversos")
            self.comandos_web.definir_valor("css", "#dadosBancarios\.formaCredito", "TED Conta Corrente")
        self.comandos_web.definir_valor("css", "#dadosBancarios\.numeroBanco", str(registro["fgts_codigo_do_banco"]).strip(), simular_humano=True)
        # sleep(0.5)
        self.aguardar_carregamento(5)
        erro_banco = self.comandos_web.executar_javascript("""$("#erroBanco").text();""", True)
        if erro_banco == "Não encontrado!":
            self.resultado = "Código do banco não encontrado"
            return
        try:
            registro["fgts_agencia"] = registro["fgts_agencia"].strip().replace(" ", "-").replace(".", "-").replace("_", "-").replace("=", "-")
            if str(registro["fgts_agencia"]).__contains__("-"):
                self.comandos_web.definir_valor("css", "#dadosBancarios\.agencia", int(str(registro["fgts_agencia"]).split("-")[0]))
                # self.comandos_web.definir_valor("css", "#dadosBancarios\.agenciaDv", int(str(registro["fgts_agencia"]).split("-")[1]))
                if self.navegador == "chrome":
                    self.comandos_web.executar_javascript(rf"""top.frames['rightFrame'].document.querySelector("#dadosBancarios\\.agenciaDv").value = {int(str(registro["fgts_agencia"]).split("-")[1])}""")
                else:
                    self.comandos_web.definir_valor("css,", "#dadosBancarios\.agenciaDv", int(str(registro["fgts_agencia"]).split("-")[1]), simular_humano=True)
            else:
                self.comandos_web.definir_valor("css", "#dadosBancarios\.agencia", int(str(registro["fgts_agencia"]).strip()), simular_humano=True)
            # sleep(0.5)
            self.aguardar_carregamento(5)

            erro_agencia = self.comandos_web.executar_javascript("""$("#erroAgencia").text();""", True)
            if erro_agencia == "Não encontrado!":
                self.resultado = "Agência bancária não reconhecida"
                return
        except Exception as e:
            print(e)

        if registro["fgts_tipo_de_conta"] != "Corrente":
            self.comandos_web.definir_valor("css", "#dadosBancarios\.finalidadeCredito", "CONTA POUPANÇA")

        try:
            registro["fgts_conta_corrente"] = str(registro["fgts_conta_corrente"]).strip().replace(" ", "-").replace(".", "-").replace("_", "-").replace("=", "-")
            if str(registro["fgts_conta_corrente"]).__contains__("-"):
                self.comandos_web.definir_valor("css", "#dadosBancarios\.conta", int(str(registro["fgts_conta_corrente"]).split("-")[0]))
                if self.navegador == "chrome":
                    self.comandos_web.executar_javascript(rf"""top.frames['rightFrame'].document.querySelector("#dadosBancarios\\.contaDv").value = {str(registro["fgts_conta_corrente"]).split("-")[1]}""")
                else:
                    self.comandos_web.definir_valor("css", "#dadosBancarios\.contaDv", str(registro["fgts_conta_corrente"]).split("-")[1])
            else:
                self.comandos_web.definir_valor("css", "#dadosBancarios\.conta", int(registro["fgts_conta_corrente"]))
        except Exception as e:
            print(e)


        try:
            # 8.13
            if float(self.fgts_valor_liberado) > float(registro["fgts_valor_contratado"]):
                for i in range(10):
                    novo_valor = (float(self.valor_antecipar) / float(self.fgts_valor_liberado)) * float(registro["fgts_valor_contratado"])
                    self.comandos_web.executar_javascript("""$("input[id='ade.valorAntecipacaoFgts']").val('');""")
                    self.comandos_web.definir_valor("css", "#ade\.valorAntecipacaoFgts", str(round(novo_valor, 2)).replace(".", ","))
                    self.comandos_web.clicar_elemento("css", "#buttonLink")
                    sleep(0.5)
                    self.fgts_valor_liberado = float(self.comandos_web.executar_javascript("""$("span[id='label_ade.valorLiberado']").text();""", True))
                    if (self.fgts_valor_liberado >= float(registro["fgts_valor_contratado"])) and ((self.fgts_valor_liberado) < (float(registro["fgts_valor_contratado"]) + 50.0)):
                        break
                    else:
                        self.valor_antecipar = str(round(novo_valor, 2))
                        if i == 9:
                            self.resultado = "RPA não conseguiu ajustar o valor liberado"
                            return
        except Exception as e:
            raise Exception(f"""Falha ao calcular valor liberado: {e}\nself.fgts_valor_liberado: [{self.fgts_valor_liberado}]\nregistro["fgts_valor_contratado"]: [{registro["fgts_valor_contratado"]}]\nself.valor_antecipar: [{self.valor_antecipar}]""")

        self.comandos_web.clicar_elemento("css", "#buttonLink")  # SEMPRE CLICAR EM SIMULAR PARA EVITAR ERRO INTERNO DO SISTEMA
        self.comandos_web.definir_valor("css", "#servidor\.sexo", registro["fgts_genero"])  # combo
        self.comandos_web.definir_valor("css", "#servidor\.estadoCivil", registro["fgts_estado_civil"])  # combo
        if registro["fgts_estado_civil"] == "Casado" and registro["fgts_nome_do_conjuge"] == "":
            # raise Exception("O nome do cônjuge é obrigatório")
            self.resultado = "O nome do cônjuge é obrigatório"
            return
        self.comandos_web.definir_valor("css", "#servidor\.nomeConjuge", registro["fgts_nome_do_conjuge"])
        self.comandos_web.definir_valor("css", "#servidor\.nomeMae", registro["fgts_nome_da_mae"])
        self.comandos_web.definir_valor("css", "#servidor\.nomePai", registro["fgts_nome_do_pai"])
        self.comandos_web.definir_valor("css", "#servidor\.cidadeNascimento", registro["fgts_naturalidade"])
        self.comandos_web.definir_valor("css", "#servidor\.ufNascimento", registro["estado"])  # combo
        # try:
        #     self.comandos_web.selecionar_combo_simples("css", r"#servidor\\.nacionalidade", str(registro["fgts_nacionalidade"]).upper()[0:len(str(registro["fgts_nacionalidade"])) - 1], javascript=True, contem=True, iframe="rightFrame")  # combo
        # except:
        self.comandos_web.definir_valor("css", "#servidor\.nacionalidade", "BRASILEIRA")  # combo
        self.comandos_web.definir_valor("css", "#servidor\.identidade\.tipo", registro["fgts_tipo_de_documento"])  # combo
        self.comandos_web.definir_valor("css", "#servidor\.identidade\.numero", registro["fgts_numero_do_documento"])
        self.comandos_web.definir_valor("css", "#servidor\.identidade\.emissor", registro["fgts_orgao_emissor_doc"])  # combo
        self.comandos_web.definir_valor("css", "#servidor\.identidade\.uf", self.comandos_web.remover_acentos(str(registro["fgts_estado_emissao_doc"]).upper()))  # combo
        try:
            self.comandos_web.definir_valor("css", "#servidor\.identidade\.dataEmissao", datetime.strptime(registro["fgts_data_emissao_documento"], "%Y-%m-%d").strftime("%d/%m/%Y"))
        except:
            pass
        if registro["fgts_cep"] != "":
            self.comandos_web.definir_valor("css", "#endereco\.cep", registro["fgts_cep"], simular_humano=True)
            self.aguardar_carregamento(5)
            erro_cep = self.comandos_web.executar_javascript("""$('#erroCep').text()""", True)
            if erro_cep == "Não encontrado!":
                # raise Exception("CEP não encontrado")
                self.resultado = "CEP não encontrado"
                return
        logradouro = self.comandos_web.executar_javascript("""$("input[id='endereco.logradouro']").text();""", True)
        if not logradouro:
            self.comandos_web.definir_valor("css", "#endereco\.logradouro2", str(registro["fgts_rua"]))  # .replace("/", ""))
        if not registro["fgts_numero_da_residencia"]:
            self.comandos_web.clicar_elemento("css", "#logradouroSemNumeroCheck")
        else:
            self.comandos_web.definir_valor("css", "#endereco\.numero", registro["fgts_numero_da_residencia"])
        self.comandos_web.definir_valor("css", "#endereco\.complemento", registro["fgts_complemento_endereco"])
        bairro = self.comandos_web.executar_javascript("""$("input[id='endereco.logradouro']").text();""", True)
        if not bairro:
            self.comandos_web.definir_valor("css", "#endereco\.bairro2", registro["fgts_bairro"])
        if registro["fgts_numero_do_telefone"]:
            registro["fgts_numero_do_telefone"] = str(registro["fgts_numero_do_telefone"]).replace("+55", "")
            ddd = registro["fgts_numero_do_telefone"][0:2]
            telefone = registro["fgts_numero_do_telefone"][2:len(registro["fgts_numero_do_telefone"])]
            self.comandos_web.definir_valor("css", "#endereco\.telefone\.ddd", ddd)
            self.comandos_web.definir_valor("css", "#endereco\.telefone\.numero", telefone)
            self.comandos_web.definir_valor("css", "#endereco\.telefoneCelular1\.ddd", ddd)
            self.comandos_web.definir_valor("css", "#endereco\.telefoneCelular1\.numero", telefone)
            self.comandos_web.definir_valor("css", "#endereco\.telefoneCelular2\.ddd", ddd)
            self.comandos_web.definir_valor("css", "#endereco\.telefoneCelular2\.numero", telefone)
        self.comandos_web.executar_javascript("""$("input[id='endereco.email']").val('');""")
        self.comandos_web.definir_valor("css", "#endereco\.email", registro["email"])
        #  # self.comandos_web.executar_javascript(r"""top.frames['rightFrame'].document.querySelector("#mesmoAgenteRadioId").click();""")
        self.comandos_web.clicar_elemento("css", "#mesmoAgenteRadioId")
        sleep(0.3)
        self.comandos_web.definir_valor("css", "#ade\.codigoFormaEnvioTermo", "Balcão")  # combo
        self.comandos_web.definir_valor("css", "#contraCheque\.tipoAnexo\[0\]", "Contracheque")
        self.comandos_web.clicar_elemento("css", "#confirmar")
        sleep(2)

        try:
            self.resultado = self.comandos_web.manipular_alerta(True)
            if self.resultado:
                return True
        except Exception as e:
            print(e)

        if not self.verificar_erro_interno():
            return False
        sleep(2)
        try:
            janelas = p.findwindows.find_elements(title_re="Consig - Perfil 1 — Microsoft​ Edge", top_level_only=True)
            print(janelas)
            if len(janelas) != 1:
                janela = Application(backend='uia').connect(title="Consig - Perfil 1 — Microsoft​ Edge", found_index=0, timeout=5000)
                janela.ConsigPerfil1MicrosoftEdge.child_window(control_type="Hyperlink", found_index=1).wrapper_object().click_input()
        except Exception as e:
            print(e)

        # self.comandos_web.enquanto_javascript("""$('#label_numeroAde', frames['rightFrame'].document).length != 0;""", 5)
        # self.numero_proposta = self.comandos_web.executar_javascript("""$('#label_numeroAde', frames['rightFrame'].document).text();""", True)
        self.aguardar_carregamento(15)
        sleep(3)
        self.comandos_web.enquanto_javascript("""$('#label_numeroAde').length == 0;""", 5)
        self.numero_proposta = self.comandos_web.executar_javascript("""$('#label_numeroAde').text();""", True)
        # self.numero_proposta = self.comandos_web.obter_valor("css", "#label_numeroAde")
        if self.numero_proposta:
            if self.numero_proposta.__contains__("Erro"):
                self.resultado = "RPA: Ocorreu um erro ao gerar/obter o número da proposta"
                return True
                #self.numero_proposta = input("Número proposta:")
            else:
                self.data_hora_input = datetime.now()
        # self.comandos_web.alternar_janela("Anexo -- Caixa de diálogo Página da Web")
        # self.comandos_web.executar_javascript("""this.confirmCancel();""")

        # OBTENÇÃO DO ARQUIVO PDF E ENVIO DO SMS SUSPENSOS EM 20/09/2022 18:00

        # TODO DESMEMBRAR PARA GARANTIR A ATUALIZAÇÃO DA HS
        try:
            sleep(2)
            self.comandos_web.executar_javascript("""top.frames['rightFrame'].gerarTermoAdesaoPopUp(false);""")
            # self.comandos_web.executar_javascript("""top.frames['rightFrame'].gerarDetalhePropostaRelatorioPopUp(false);""")
            sleep(2)

            # self.fechar_popup()

            janela = Application(backend='uia').connect(title="Exibir Downloads - Internet Explorer", found_index=0, timeout=60)
            existe_documento = os.path.exists(self.origem_doc_proposta)
            if existe_documento:
                os.remove(self.origem_doc_proposta)
            # janela
            janela.window().wait("exists enabled visible ready", 5)
            janela.window().set_focus()
            janela.ExibirDownloadsInternetExplorer.child_window(control_type="SplitButton", found_index=0).wrapper_object().click_input()  # Salvar
            baixou_arquivo = self.esperar_download(20)
            if not baixou_arquivo:
                self.log.logar_mensagem("Falha no download do detalhamento da proposta (PDF)")
                # self.resultado = "Falha no download do detalhamento da proposta (PDF)"
                # return

            janela.ExibirDownloadsInternetExplorer.child_window(control_type="Button", found_index=1).wrapper_object().click_input()  # Limpar lista
            sleep(0.5)
            janela.ExibirDownloadsInternetExplorer.child_window(control_type="Button", found_index=2).wrapper_object().click_input()  # Fechar
            sleep(0.5)

            self.fechar_popup()

            nome_arquivo = f"""{registro["id"]}_{registro["contact_id"]}_{str(registro["cpf"]).zfill(11)}_{str(self.numero_proposta)}"""
            self.renomear_arquivo_termo(nome_arquivo)
            # self.comandos_web.executar_javascript("""top.frames['rightFrame'].gerarDetalhePropostaRelatorioPopUp(false);""")
            sleep(0.1)
        except Exception as e:
            self.log.logar_mensagem(f"""Falha ao tentar baixar o arquivo PDF{f": {e}" if str(e) else ""}""")
            self.resultado = None  # "Pendente envio do link por SMS (ICConsig)"
            return True
            # raise Exception(f"""Falha ao tentar baixar o arquivo PDF{f": {e}" if str(e) else ""}""")

    def fechar_popup(self):
        # FECHA A JANELA: Modelo de Célula de Crédito Bancário (CCB) -- Caixa de diálogo Página da Web
        try:
            janelas = p.findwindows.find_elements(title_re="Consig - Perfil 1 — Microsoft​ Edge", top_level_only=True)
            if len(janelas) > 1:
                # janela = Application(backend='uia').connect(title="Consig - Perfil 1 — Microsoft​ Edge", found_index=0, timeout=15)
                # janela.window().wait("exists enabled visible ready", 5)
                # janela.window().set_focus()
                # janela.ConsigPerfil1MicrosoftEdge.child_window(control_type="Button", found_index=0).wrapper_object().click_input()
                janela = Application(backend='uia').connect(title="Consig - Perfil 1 — Microsoft​ Edge", found_index=0, timeout=20)
                janela = janela.window(class_name="Alternate Modal Top Most")
                janela = janela.child_window(title="Modelo de Célula de Crédito Bancário (CCB)", control_type="Pane")
                janela.window().wait("exists enabled visible ready", 20)
                janela.window().set_focus()
                janela = Application(backend='uia').connect(title="Consig - Perfil 1 — Microsoft​ Edge", found_index=0, timeout=20)
                janela = janela.window(class_name="Alternate Modal Top Most")
                janela = janela.child_window(title="", control_type="TitleBar")
                janela.child_window(control_type="Button", found_index=0).wrapper_object().click_input()

                sleep(1)
        except Exception as e:
            print(e)
            pass

    def esperar_download(self, tempo=10):
        self.log.logar_mensagem(f"Esperando download do arquivo...\n[{self.origem_doc_proposta}]")
        for i in range(tempo):
            sleep(1)
            existe_documento = os.path.exists(self.origem_doc_proposta)
            if existe_documento:
                return True
        return False

    def renomear_arquivo_termo(self, nome_arquivo):
        destino = rf"{self.caminho_arquivo}\{nome_arquivo}.pdf"
        self.log.logar_mensagem(f"Movendo arquivo...\nDe: {self.origem_doc_proposta}\nPara: {destino}")
        try:
            # os.rename(self.origem_doc_proposta, destino)
            shutil.move(self.origem_doc_proposta, destino)
        except Exception as e:
            raise Exception(f"""Falha ao tentar renomear o arquivo PDF{f": {e}" if str(e) else ""}""")

    def obter_registro(self, input_=False):
        self.log.logar_mensagem(f'>>> obter_registro(input_={input_})')
        registro = self.db.obter_registro(self.hostname, input_)
        if registro:
            print("Encontrou registro")
            return registro[0]
        else:
            print("NÃO encontrou registro")
            return None

    def aguardar_carregamento(self, tempo=60):
        self.log.logar_mensagem(f'>>> aguardar_carregamento(tempo={tempo})')
        try:
            for i in range(1, tempo):
                # retorno = self.comandos_web.executar_javascript("return top.frames['rightFrame'].document.querySelector('#waitDiv').getAttribute('class').includes('inivisivel');")  # inivisivel < classe com nome errado no portal do Itau
                # retorno = self.comandos_web.executar_javascript("return $('#waitDiv', frames['rightFrame'].document).hasClass('inivisivel');")  # inivisivel < classe com nome errado no portal do Itau

                retorno = self.comandos_web.executar_javascript("$('div.blockUI.blockMsg.blockPage > div.carregando').length == 0;", True)  # inivisivel < classe com nome errado no portal do Itau
                print(f"[{i}/{tempo}] Aguardando carregamento: {retorno}")
                if retorno:
                    return True
                sleep(1)
        except:
            return False
        else:
            return False

    def enviar_email(self, mensagem, falha=False, enviar_usuario=True, titulo=None):
        self.log.logar_mensagem(f'>>> enviar_email(mensagem={mensagem},\nfalha={falha})')
        try:
            # todo aprimorar com any e variável com erros_ignorados
            if mensagem.__contains__("Connection aborted"):
                return

            destinatarios_erro = self.destinatarios_erro
            if any(erro in mensagem for erro in self.erros_impeditivos):
                if self.destinatarios_erro_impeditivo:
                    destinatarios_erro += ";" + self.destinatarios_erro_impeditivo

            if self.registro:
                try:
                    registro = " - [id: " + str(self.registro["id"]) + "]"
                except:
                    self.log.logar_mensagem("Falha na obtenção do ID do registro")
                    registro = ""
            else:
                registro = ""

            assunto_monitoramento = f"[RPA-{'INPUT' if self.input else 'ELEGIBILIDADE'}][{'ERRO' if falha else 'ALERTA'}]"
            retorno = self.notificar.enviar_email(assunto_monitoramento, f"""{"[" + self.usuario + "]: " if enviar_usuario else ""}{mensagem}{registro} - {titulo if titulo else self.hostname}""", self.destinatarios_monitoramento)
            if retorno:
                self.log.logar_mensagem(f"Notificação enviada para:\n{destinatarios_erro if falha else self.destinatarios_sucesso}")
            else:
                self.log.logar_mensagem(f". /!\ FALHA NO ENVIO DA NOTIFICAÇÃO DE MONITORAMENTO /!\ .")

            assunto = f"[{'FALHA' if falha else 'SUCESSO'}] ITAÚ FGTS {'INPUT' if self.input else 'ELEGIBILIDADE'} - Saque Aniversário - {titulo if titulo else self.hostname}"
            retorno = self.notificar.enviar_email(assunto, f"""{"[" + self.usuario + "]: " if enviar_usuario else ""}{mensagem}{registro}""", destinatarios_erro if falha else self.destinatarios_sucesso)
            if retorno:
                self.log.logar_mensagem(f"Notificação enviada para:\n{destinatarios_erro if falha else self.destinatarios_sucesso}")
            else:
                self.log.logar_mensagem(f". /!\ FALHA NO ENVIO DA NOTIFICAÇÃO PADRÃO /!\ .")
        except Exception as e:
            self.log.logar_mensagem(e)

    def processar_registros_icconsig(self, qtde_registros):
        self.log.logar_mensagem(f'>>> processar_registros_icconsig()')
        try:
            registro = self.db.obter_registro_icconsig(self.hostname)

            self.efetuar_login_icconsig()
            while registro:

                # self.db.atualizar_status_input(registro["id"], self.hostname, "proc_icconsig")
                self.navegar_nova_proposta()
                numero_card = self.pesquisar_proposta_icconsig(registro[0])
                if numero_card:
                    self.excluir_ccb(registro[0])
                else:
                    sucesso = self.importar_proposta(registro[0])
                    if not sucesso:
                        registro = self.db.obter_registro_icconsig(self.hostname)
                        continue
                    for i in range(1, 4):
                        self.navegar_nova_proposta()
                        numero_card = self.pesquisar_proposta_icconsig(registro[0])
                        if numero_card:
                            break
                        sleep(10)
                    if not numero_card:
                        mensagem_hubspot = "Falha na importação do PDF"
                        sucesso = self.request.atualizar_proposta_input(registro[0]["contact_id"], 0, mensagem_hubspot, registro[0]["numero_proposta"], registro[0]["valor_contratado"], registro[0]["data_hora_input"])
                        self.db.atualizar_status_input(registro[0]["id"], "concluido" if sucesso else "falha_hs_ic", mensagem_hubspot=mensagem_hubspot)
                        registro = self.db.obter_registro_icconsig(self.hostname)
                        continue
                self.enviar_sms(registro[0], numero_card)
                registro = self.db.obter_registro_icconsig(self.hostname)

            self.efetuar_logout_icconsig()

            return "OK"
        except Exception as e:
            raise Exception(f"[Pendente envio de SMS: {qtde_registros}]  \n\n{e}")

    def efetuar_login_icconsig(self):
        self.log.logar_mensagem(f'>>> efetuar_login_icconsig()')
        # todo try: Registrar no campo do HubSpot “Status da proposta RPA – FGTS” (fgts_status_da_proposta_rpa): “FALHA – Confirmação do input ”;
        try:

            url = "https://portal.icconsig.com.br/"
            self.comandos_web.navegar_para(url)
            self.comandos_web.esperar_url(url, 60)
            carregou = self.comandos_web.esperar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface > div > app-auth-dialog > div > iframe", 15)
            if not carregou:
                raise Exception("Página indisponível")

            self.comandos_web.executar_javascript("""window.open(document.querySelector("body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface > div > app-auth-dialog > div > iframe").getAttribute('src'), '_self')""")
            # self.comandos_web.alternar_frame("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface > div > app-auth-dialog > div > iframe")
            carregou = self.comandos_web.esperar_elemento("css", "#username", 20)
            if not carregou:
                raise Exception("Página indisponível")

            for login_icconsig in self.logins_icconsig:
                usuario_icconsig = login_icconsig[0].split(";")[0]
                senha_icconsig = login_icconsig[0].split(";")[1]
                self.comandos_web.definir_valor("css", "#username", usuario_icconsig)
                self.comandos_web.definir_valor("css", "#password", senha_icconsig)
                self.comandos_web.clicar_elemento("css", "#kc-login")
                msg_login = self.comandos_web.esperar_elemento("css", ".lm-form-messages")
                if msg_login:
                    mensagem = self.comandos_web.obter_valor("css", ".lm-form-messages").strip()
                    if mensagem.__contains__("Conta desativada") or mensagem.__contains__("inválida"):
                        self.enviar_email(f"[{usuario_icconsig}]: {mensagem}", True)
                        continue
                else:
                    break

            self.comandos_web.navegar_para(url)
            self.comandos_web.esperar_url(url + "proposal", 60)
            # carregou = self.comandos_web.esperar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface > div > app-auth-dialog > div > iframe", 15)
            carregou = self.comandos_web.esperar_elemento("css", "#my-label-id > input")
            if not carregou:
                raise Exception("Página indisponível")

        except Exception as e:
            raise Exception(f"""Falha ao efetuar login no ICConsig{f": {e}" if str(e) else ""}""")

    def pesquisar_proposta_icconsig(self, registro):
        self.log.logar_mensagem(f'>>> pesquisar_proposta_icconsig(id={registro["id"]}, contact_id={registro["contact_id"]}, numero_proposta={registro["numero_proposta"]}, valor_contratado={registro["valor_contratado"]})')
        try:
            self.comandos_web.clicar_elemento("css", "body > app-root > app-content-layout > cc-drawer > aside > div > div > app-sidenav > div > div.flex-fill > div:nth-child(3) > div > nav > a.button.button--menu.mb-2.ng-star-inserted.mdc-ripple-upgraded.button--menu-active > div")
            self.comandos_web.clicar_elemento("css", "#my-label-id > input")
            # self.comandos_web.esperar_elemento("css", "app-kanban > div.kanban", 20)
            sleep(1)
            self.comandos_web.definir_valor("css", "#my-label-id > input", registro["numero_proposta"], simular_humano=True)
            self.comandos_web.enquanto_javascript("""document.querySelector('div:nth-child(1) > div > div.kanban__column__header > div > div.col.col-auto > span').length != 0;""", 5)
            for i in range(1, 4):
                existe = self.comandos_web.enquanto_javascript(f"""document.querySelector('div.swiper-wrapper > div:nth-child({i}) > div > div.kanban__column__header > div > div.col.col-auto > span').innerText == '1';""", 1.5, True)
                if existe:
                    return i
            return 0
            # resultado = self.comandos_web.enquanto_javascript("""document.querySelector('div.kanban__column__header > div > div.col.col-auto > span').innerText == '1';""", 5)
            # if resultado:
            #     return True
            # else:
            #     # self.request.atualizar_proposta_input(registro["contact_id"], 0, "Proposta não localizada no ICConsig", registro["numero_proposta"], registro["valor_contratado"])
            #     # self.db.atualizar_mensagem(registro["id"], "Proposta não localizada no ICConsig", True)
            #     return False
        except Exception as e:
            raise Exception(f"""Falha ao pesquisar proposta no ICConsig{f": {e}" if str(e) else ""}""")

    def importar_proposta(self, registro):
        self.log.logar_mensagem(f'>>> importar_proposta(registro)')
        try:
            nome_arquivo = f"""{registro["id"]}_{registro["contact_id"]}_{registro["cpf"]}_{registro["numero_proposta"]}.pdf"""
            caminho_completo = rf"{self.caminho_arquivo}\{nome_arquivo}"
            # mover_para = rf"{self.mover_para}\{nome_arquivo}"
            self.comandos_web.executar_javascript("""document.querySelector('body > app-root > app-content-layout > cc-drawer > div > div > main > app-kanban > div.floating-button-bottom-right > button').click();""")
            sleep(0.5)
            self.comandos_web.executar_javascript("document.querySelector(`input[type='file']`).className = ''")

            sucesso = self.comandos_web.definir_valor("xpath", "/html/body/cc-lib-dialog/div/div[1]/div[2]/div/app-proposal-import/div/div/div/div[3]/div[2]/cc-dropzone/div/input", caminho_completo)
            self.comandos_web.esperar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-proposal-import > div > div > div > div:nth-child(3) > div.col-12.mb-3 > div", 10)
            sleep(3)
            sucesso = self.comandos_web.executar_javascript("""document.querySelector("body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-proposal-import > div > div > div > div:nth-child(3) > div.col-12.mb-3 > div").innerText.includes("sucesso")""", True)
            if not sucesso:
                mensagem_hubspot = "Falha na importação do PDF"
                sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, mensagem_hubspot, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
                self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic", mensagem_hubspot=mensagem_hubspot)
            sleep(1)

            # BOTÃO FECHAR
            self.comandos_web.clicar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-proposal-import > div > div > div > div.row.align-items-center.justify-content-end > div > button")

            if sucesso:
                # os.rename(caminho_completo, mover_para)
                self.excluir_ccb(registro[0])
            else:
                # mensagem = "Falha ao enviar o SMS ao cliente (ICConsig)"
                mensagem = "Falha no download da Proposta (IBConsig)"
                sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, mensagem, registro["numero_proposta"], registro["valor_contratado"])
                self.db.atualizar_mensagem(registro["id"], mensagem, True, "concluido" if sucesso else "falha_hs_ic")
                return False

            # BOTÃO VER DETALHES
            # self.comandos_web.clicar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-proposal-import > div > div > div > div:nth-child(4) > div.col-12.text__align--center.mb-3 > button")
        except Exception as e:
            print(e)
        else:
            return True

    def excluir_ccb(self, registro):
        nome_arquivo = f"""{registro["id"]}_{registro["contact_id"]}_{str(registro["cpf"]).zfill(11)}_{str(registro["numero_proposta"])}.pdf"""
        caminho_completo = rf"{self.caminho_arquivo}\{nome_arquivo}"
        try:
            os.remove(caminho_completo)
        except Exception as e:
            self.log.logar_mensagem(f"Falha ao excluir CCB: {e}\n{caminho_completo}")

    def enviar_sms(self, registro, numero_card):
        self.log.logar_mensagem(f'>>> enviar_sms(id={registro["id"]}, contact_id={registro["contact_id"]}, numero_proposta={registro["numero_proposta"]}, valor_contratado={registro["valor_contratado"]})')
        try:
            # rotulo_botao = self.comandos_web.executar_javascript("""document.querySelector('app-send-link-button > button > span').innerText;""", True)
            botao = self.comandos_web.executar_javascript("""document.querySelector('app-send-link-button > button').length != 0;""", True)

            if numero_card in (1, 2):
                if botao:
                    # if rotulo_botao.__contains__("enviar link para o cliente"):
                    #
                    self.comandos_web.clicar_elemento("css", "app-send-link-button > button > span")
                    sleep(1)
                    #self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-center.mb-2 > div.col.col-auto.d-flex.align-self-stretch.ng-star-inserted > div > div > label > div.row.d-flex.justify-content-center.m-1 > div > div > div > input').click();""")
                    self.comandos_web.executar_javascript("""document.querySelector('body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-center.mb-2 > div:nth-child(1) > div > div > label > div.row.justify-content-center.m-1 > div > div > div').click()""")
                    self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__actions > div > button').click();""")
                    # sleep(1)
                    # self.comandos_web.executar_javascript("document.querySelector('app-link-generated > div > div > div:nth-child(4) > button').click();")
                    # sleep(1)
                    # resposta = self.comandos_web.obter_resposta_rede(filtro_url="/generateLink/correspondent")
                    # json_resposta = json.loads(resposta[0][3])
                    clipboard = 'Sem link'
                    #clipboard = json_resposta["linkCorrespondent"]
                    # clipboard = pyperclip.paste()

                    print("CLIPBOARD: " + clipboard)
                    # if not clipboard:
                    #     raise Exception("Falha na obtenção do link")
                    # text_data = wx.TextDataObject()
                    # if wx.TheClipboard.Open():
                    #     success = wx.TheClipboard.GetData(text_data)
                    #     wx.TheClipboard.Close()
                    # if success:
                    #     return text_data.GetText()

                    #self.comandos_web.executar_javascript("document.querySelector('app-link-generated > div > div > div:nth-child(1) > button').click();")
                    link = None
                    #link = ""
                    # try:
                    #     link = re.findall("https.*", clipboard)[0]
                    # except:
                    #     pass
                    #
                    sleep(2)
                    self.comandos_web.clicar_elemento("css", "app-send-link-button > button > span")
                    sleep(1)
                    self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-center.mb-2 > div:nth-child(1) > div > div > label > div.row.justify-content-center.m-1 > div > div > div > input').click();""")
                    # self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__actions > div > button').click();""")
                    sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 1, None, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"], link)
                    self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic")
                else:
                    sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 1, None, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
                    self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic")
            elif numero_card == 3:
                # EXISTE UM MOTIVO PARA ENVIAR FALHA
                sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, "Proposta já concluída", registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
                self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic")
            else:
                raise Exception("Coluna do ICConsig não definida")

            # rotulo_botao = self.comandos_web.obter_valor("css", "#swiper-wrapper-a73f44713e647acd > div:nth-child(1) > div > div.kanban__column__body > cdk-virtual-scroll-viewport > div.cdk-virtual-scroll-content-wrapper > div > app-card > div > div > div.cc-card__content > div:nth-child(3) > div > app-send-link-button > button > span")
            #
            # if rotulo_botao == "enviar link para o cliente":
            #     self.comandos_web.clicar_elemento("css", "app-send-link-button > button > span")
            #     # self.comandos_web.esperar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-sent-link")
            #     sleep(2)
            #     # self.comandos_web.clicar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-center.mb-2 > div:nth-child(1) > div > div > label > div.row.justify-content-center.m-1 > div > div > div > input")
            #     self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-center.mb-2 > div:nth-child(1) > div > div > label > div.row.justify-content-center.m-1 > div > div > div > input').click();""")
            #     # self.comandos_web.clicar_elemento("css", "body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface.mdc-dialog__surface--full > div > app-sent-link > form > div > div.cc-dialog__actions > div > button")
            #     self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__actions > div > button').click();""")
            #     # sleep(1)
            #     # rotulo_botao = self.comandos_web.executar_javascript("""document.querySelector('app-send-link-button > button > span').innerText;""", True)
            #     sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 1, None, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
            #     self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic")
            # elif rotulo_botao == "reenviar link para o cliente":
            #     # mensagem = "SMS já enviado para o cliente"
            #     sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 1, None, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
            #     # self.db.atualizar_mensagem(registro["id"], mensagem, True, "concluido" if sucesso else "falha_hs_ic")
            #     self.db.atualizar_status_input(registro["id"], "concluido" if sucesso else "falha_hs_ic")
            # else:
            #     mensagem = "Falha ao enviar o SMS ao cliente (ICConsig)"
            #     sucesso = self.request.atualizar_proposta_input(registro["contact_id"], 0, mensagem, registro["numero_proposta"], registro["valor_contratado"], registro["data_hora_input"])
            #     self.db.atualizar_mensagem(registro["id"], mensagem, True, "concluido" if sucesso else "falha_hs_ic")
        except Exception as e:
            raise Exception(f"""ICConsig - Falha ao enviar SMS{f": {e}" if str(e) else ""}""")

    def navegar_nova_proposta(self):
        self.log.logar_mensagem(f'>>> navegar_nova_proposta()')
        url = "https://portal.icconsig.com.br/"
        self.comandos_web.navegar_para(url)
        self.comandos_web.esperar_url(url, 60)
        carregou = self.comandos_web.esperar_elemento("css","body > cc-lib-dialog > div > div.mdc-dialog__container > div.mdc-dialog__surface > div > app-auth-dialog > div > iframe", 15)
        self.comandos_web.executar_javascript("""document.querySelector('app-sent-link > form > div > div.cc-dialog__content > div > div.row.d-flex.justify-content-end > button').click();""")
        self.comandos_web.definir_valor("css", "#my-label-id > input", "0", simular_humano=True)
        self.comandos_web.executar_javascript("""document.querySelector('#my-label-id > input').value = '';""")

    def efetuar_logout_icconsig(self):
        self.log.logar_mensagem(f'>>> efetuar_logout_icconsig()')
        self.comandos_web.clicar_elemento("css", "body > app-root > app-content-layout > cc-drawer > aside > div > div > app-sidenav > div > div.flex-fill > div:nth-child(3) > div > nav > a:nth-child(2)")
        self.comandos_web.fechar_navegador()







