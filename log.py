import os
from datetime import datetime
from banco_operacoes import Operacoes


class Log:

    def __init__(self, ambiente):
        try:
            self.db = Operacoes(ambiente)
            self.info = self.db.obter_info_projeto()[0]
            self.__arquivoLog = f"""log_{self.info['nome']}.txt"""
            if os.path.isfile(self.__arquivoLog):
                tamanho = os.stat(self.__arquivoLog).st_size
                if tamanho > 2048000:  # 2MB
                    # os.remove(self.__arquivoLog)
                    open(self.__arquivoLog, "w+")
            else:
                open(self.__arquivoLog, "w+")
        except Exception as e:
            print(f"\n\n*-*-*-*-*\n{e}\n*-*-*-*-*\n\n")

    def logar_mensagem(self, mensagem, persistir_banco=False, tipo="INFO"):
        print(mensagem)
        with open(self.__arquivoLog, 'a') as log:
            log.write('\n[' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '] ' + str(mensagem))
        if persistir_banco:
            self.db.logar_mensagem(tipo, mensagem, self.info["id"])
