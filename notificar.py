import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Notificar:

    def __init__(self, config):
        try:
            parametros = config.split(';')
            self.usuario_email = parametros[0]
            self.senha_email = parametros[1]
        except Exception as e:
            raise Exception(f"Falha ao inicializar log: {e}")

    def enviar_email(self, assunto, mensagem, destinatarios):
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(self.usuario_email, self.senha_email)
            email_msg = MIMEMultipart()
            email_msg["From"] = self.usuario_email
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
    # WHATSAPP / SLACK
    def enviar_mensagem(self, mensagem, anexo, destinatarios, plataforma):
        pass

