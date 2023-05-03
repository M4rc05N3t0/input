from processamento import Processamento
from datetime import datetime, timedelta
import sys
from log import Log
from time import sleep
from banco_operacoes import Operacoes
import socket
from manipular_hubspot import ManipularHubspot
import os
import ctypes
# import logging

# logging.basicConfig(filename="ItauSaqueAniversario.log", level=logging.INFO, format="%(asctime)s :: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %A")
print("Inicializando...")
global proc, main
parametros = sys.argv
ambiente = ''
acao = ''
if len(parametros) != 1:
    ambiente = parametros[1]
    if ambiente not in ('hml', 'prod'):
        print(f"Parâmetro '{ambiente}' não corresponde a um ambiente válido. Ex.: hml ou prod")
        sleep(15)
        sys.exit(1)
    if len(parametros) > 2:
        if parametros[2] in ("input", "input+", "importacao", "atualizacao", "importacao_input", "icconsig"):
            acao = parametros[2]
    else:
        acao = "consulta"

mensagem = f"""* * * ITAÚ SAQUE ANIVERSÁRIO FGTS * * *
Ambiente de {'Produção' if ambiente == 'prod' else 'Homologação'}
MODO: {acao.upper() + ("" if acao.__contains__("input") or acao.__contains__("icconsig") else " - ELEGIBILIDADE") + (" IMPORTAÇÃO" if acao.__contains__("+") else "")}
"""
os.system("cls")
print(mensagem)
sleep(3)


class Main:

    def __init__(self):
        try:
            self.tentativa = 0
            self.db = Operacoes(ambiente)
            self.log = Log(ambiente)
            self.hostname = socket.gethostname()
            self.hubspot = ManipularHubspot(ambiente)

        except Exception as e:
            raise Exception(e)

    def verificar_execucao(self, erro):
        self.log.logar_mensagem(f'>>> verificar_execucao(erro={erro})')
        self.tentativa += 1
        if acao.__contains__("input") or acao.__contains__("consulta"):
            proc.efetuar_logout()
        proc.enviar_email(str(erro), True)
        sleep(proc.obter_espera(str(erro)))

        # print(f"* * * * * * Tentativa #{self.tentativa} * * * * * *")
        # if self.tentativa > 3:
        #     self.tentativa = 0
        #     proc.enviar_email(erro, True)
        #     sleep(3600)  # 1 hora

    # def processar_icconsig(self):
    #     self.log.logar_mensagem(f'>>> processar_icconsig()')
    #     try:
    #         registro = self.db.obter_registro_icconsig(main.hostname)
    #         if registro:
    #             proc_icconsig = Processamento(ambiente, "chrome", True)
    #             proc_icconsig.processar_registros_icconsig(registro)
    #     except Exception as e:
    #         self.log.logar_mensagem(e)
    #         raise Exception(e)

    def desconectar_usuario(self):
        # self.log.logar_mensagem(f'>>> desconectar_usuario()')
        try:
            if not any(parametro in "monitor" for parametro in parametros):
                self.minimizar_console()
                if acao == "input":
                    if self.hostname.__contains__("AWS"):
                        os.system(r'''
                            Powershell -Command "& { Start-Process \"C:\\RPA\\AlwaysOn.bat\" -WindowStyle Minimized -ArgumentList @(\"C:\\Windows\\System32\\drivers\\etc\\hosts\") -Verb RunAs } "
                        ''')
        except Exception as e:
            self.log.logar_mensagem(e)

    def minimizar_console(self):
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
        except:
            pass


while True:
    try:
        main = Main()
        main.desconectar_usuario()
        os.system("cls")
        break
    except Exception as e:
        print(f"Erro ao inicializar main: {e}")
        agora = datetime.now()
        reinicio = agora + timedelta(minutes=15)
        espera = int((reinicio - agora).total_seconds())
        print(f"       Parada em: {agora}\nPróxima execução: {reinicio} ({espera}s)")
        sleep(espera)

if acao == "importacao":
    pass
elif acao == "atualizacao":
    pass
elif acao == "importacao_input":
    try:
        while True:
            os.system('cls')
            print(mensagem)
            main.minimizar_console()
            qtde_registros = main.hubspot.importar_input()
            if qtde_registros:
                aviso = f"Registros importados: {qtde_registros}"
                proc = Processamento(ambiente, None, True)
                proc.enviar_email(aviso, False, False, "Importação da base")
                print(aviso)

            print("Aguardando por 5 minutos")
            sleep(5*60)
    except Exception as e:
        main.log.logar_mensagem(e, True, "ERRO")
        main.verificar_execucao(e)

elif acao == "icconsig":

    # registro = main.db.obter_registro_icconsig(main.hostname)
    while True:
        qtde = int(main.db.obter_qtde_registros_icconsig(main.hostname))
        if qtde:
            try:
                proc = Processamento(ambiente, "chrome", True)
                proc.processar_registros_icconsig(qtde)
            except Exception as e:
                main.log.logar_mensagem(e, True, "ERRO")
                main.verificar_execucao(e)
        else:
            os.system('cls')
            print("Sem registros para processar.\n\n")
            print("Aguardando por 5 minutos")
            sleep(5*60)

else:
    input = acao.__contains__("input")
    while True:
        os.system('cls')
        print(mensagem)
        try:
            if acao == "input+":
                main.hubspot.importar_input()

            # main.processar_icconsig()  # todo DESCOMENTAR

            retorno = ""
            if main.db.verificar_registros(main.hostname, input):
                main.db.limpar_registros(main.hostname, input)
                proc = Processamento(ambiente, "ie" if input else "chrome", input)

                # espera = proc.verificar_horario(input)
                # sleep(espera)
                proc.efetuar_login()
                if input:
                    retorno = proc.processar_registros_input()
                else:
                    retorno = proc.processar_registros()
                if retorno != "OK":
                    proc.enviar_email(str(retorno), True)
                proc.efetuar_logout()
            else:
                os.system('cls')
                # espera = proc.verificar_horario(input)
                print("Sem registros para processar.\n\n")

                agora = datetime.now()
                reinicio = agora + timedelta(minutes=5)
                espera = int((reinicio - agora).total_seconds())
                print(f"       Parada em: {agora}\nPróxima execução: {reinicio} ({espera}s)")
                sleep(espera)

            # main.processar_icconsig()

        except Exception as e:
            # del proc
            main.log.logar_mensagem(e, True, "ERRO")
            try:
                main.verificar_execucao(e)
            except:
                pass
        finally:
            pass
