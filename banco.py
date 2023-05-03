import psycopg2
from dotenv import load_dotenv
import socket
import sys
import os
from time import sleep
# import mysql.connector as mysql
# from log import Log
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Banco:

    @staticmethod
    def __obter_parametro(chave):
        extDataDir = os.getcwd()
        if getattr(sys, 'frozen', False):
            extDataDir = sys._MEIPASS
        load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))
        return os.environ[chave]

    def __init__(self, ambiente):
        # self.log = Log()
        if ambiente == 'prod':
            self.maestro = 'MAESTRO_PROD'
        else:
            self.maestro = 'MAESTRO_STAGING'
        self.hostname = socket.gethostname()

    def abrir_conexao(self, banco):
        try:
            db_conn = None
            tentativas = 1
            while not db_conn:
                try:
                    conn_string = self.__obter_parametro(banco).split(',')
                    tipo = conn_string[0]
                    if tipo == 'mysql':
                        # db_conn = mysql.connect(host=conn_string[1], port=conn_string[2], database=conn_string[3], user=conn_string[4], password=conn_string[5])
                        pass
                    elif tipo == 'postgresql':
                        db_conn = psycopg2.connect(host=conn_string[1], port=conn_string[2], dbname=conn_string[3], user=conn_string[4], password=conn_string[5])

                except Exception as e:
                    mensagem = f'Erro ao tentar abrir conexão com o banco de dados: \n{e}'
                    print(mensagem)
                    sleep(15)
                    if tentativas > 9:
                        self.enviar_email(f"Conexão {banco} - {self.hostname}", f"""{mensagem}""")
                        raise Exception(e)
                    tentativas += 1
            return db_conn
        except Exception as e:
            raise Exception(e)

    def executar_comando(self, query, banco):
        db_conn = self.abrir_conexao(banco)
        db_cursor = db_conn.cursor()

        db_cursor.execute(f'/***{self.hostname}***/{query}')
        db_conn.commit()

        db_cursor.close()
        db_conn.close()

    def executar_query_scalar(self, query, banco):
        db_conn = self.abrir_conexao(banco)
        try:
            db_cursor = db_conn.cursor()
            db_cursor.execute(f'/***{self.hostname}***/{query}')
            retorno = db_cursor.fetchone()[0]

            db_conn.commit()
            db_cursor.close()
            db_conn.close()
            return retorno
        except:
            return None

    def executar_query(self, query, banco, dicionario=False):
        db_conn = self.abrir_conexao(banco)
        db_cursor = db_conn.cursor()
        db_cursor.execute(f'/***{self.hostname}***/{query}')
        if dicionario:
            cabecalho = [x[0] for x in db_cursor.description]
            retorno = db_cursor.fetchall()
            objeto = []
            for resultado in retorno:
                objeto.append(dict(zip(cabecalho, resultado)))
        else:
            objeto = db_cursor.fetchall()
        db_conn.commit()
        db_cursor.close()
        db_conn.close()
        return objeto

    def importar_csv(self, arquivo_csv, tabela, colunas, separador, banco):
        db_conn = self.abrir_conexao(banco)
        db_cursor = db_conn.cursor()

        db_cursor.execute(f'/***{self.hostname}***/truncate table ' + tabela)
        db_cursor.copy_from(arquivo_csv, tabela, columns=colunas, sep=separador)

        db_conn.commit()
        db_cursor.close()
        db_conn.close()

    def executar_query_arquivo(self, query, banco):
        db_conn = self.abrir_conexao(banco)
        db_cursor = db_conn.cursor()
        db_cursor.execute(f'/***{self.hostname}***/{query}')
        retorno = str(db_cursor.fetchone()[0], 'cp1252')

        db_conn.commit()
        db_cursor.close()
        db_conn.close()
        return retorno

    # def obter_parametro(self, nome, sistema=None, area_negocio=None, vertical=None):
    #     return self.executar_query_scalar(f"""
    #         SELECT valor FROM rpa_parametros
    #         WHERE nome = '{nome}'
    #         AND sistema {"= '" + sistema + "'" if sistema else "is null"}
    #         AND area_negocio {"= '" + area_negocio + "'" if area_negocio else "is null"}
    #         AND vertical {"= '" + vertical + "'" if vertical else "is null"}
    #     """, self.maestro)

    def enviar_email(self, assunto, mensagem):
        destinatarios = "rpa-geral@escale.com.br"
        usuario_email = "robo@cobmax.com.br"
        senha_email = "uX&0Wq,<"
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(usuario_email, senha_email)
            email_msg = MIMEMultipart()
            email_msg["From"] = usuario_email
            email_msg["To"] = destinatarios
            email_msg["Subject"] = assunto
            email_msg.attach(MIMEText(mensagem, "html", _charset='utf-8'))  # 'plain'))
            server.sendmail(
                email_msg["From"],
                email_msg["To"].split(';'),
                email_msg.as_string())
            server.quit()
        except Exception as e:
            print(e)
            return False
        else:
            return True
