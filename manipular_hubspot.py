import json
from http_requests import Request
from banco_operacoes import Operacoes


class ManipularHubspot:

    def __init__(self, ambiente):
        try:
            self.request = Request(ambiente)
            self.db = Operacoes(ambiente)
        except Exception as e:
            raise Exception(f"Falha ao inicializar manipular_hubspot: {e}")

    def importar_input(self):
        try:
            processando = self.db.registros_processando()
            if processando:
                return  # todo DESCOMENTAR

            qtde_input = self.request.obter_propostas_input()
            json_qtde_input = json.loads(qtde_input)
            total = int(json_qtde_input['total'])
            # print(json_qtde_input)

            if total == 0:
                return

            print("Excluindo registros não processados...")
            self.db.excluir_registros_nao_processados(True)  # todo DESCOMENTAR

            print("Importando registros...")
            paginas = int(total / 100) + 1
            valor_after = 0

            for j in range(paginas):

                if valor_after >= 500:  # LIMITE DE IMPORTAÇÃO
                    break  # LIMITE DE IMPORTAÇÃO

                importacao_input = self.request.obter_propostas_input(valor_after)
                json_importacao_input = json.loads(importacao_input)
                resultado = range(len(json_importacao_input['results']))
                for i, item in enumerate(resultado):
                    proposta = []
                    proposta.append(json_importacao_input['results'][i]['id'])
                    proposta.append(json_importacao_input['results'][i]['properties']['cpf'])
                    proposta.append(json_importacao_input['results'][i]['properties']['email'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_data_de_nascimento'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_data_de_admissao'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_data_de_pagamento'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_valor_da_renda'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_cargo_geral'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_grau_de_instrucao'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_codigo_do_banco'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_agencia'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_conta_corrente'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_estado_civil'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_nome_do_conjuge'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_nome_da_mae'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_nome_do_pai'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_naturalidade'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_nacionalidade'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_tipo_de_documento'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_numero_do_documento'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_orgao_emissor_doc'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_estado_emissao_doc'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_data_emissao_documento'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_cep'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_rua'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_numero_da_residencia'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_complemento_endereco'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_bairro'])
                    proposta.append(json_importacao_input['results'][i]['properties']['phone'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_valor_contratado'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_genero'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_tipo_de_conta'])
                    proposta.append(json_importacao_input['results'][i]['properties']['fgts_estado'])
                    id_proposta = self.db.inserir_proposta_input(proposta)  # todo DESCOMENTAR PARA IMPORTAR
                    print(id_proposta)  # todo DESCOMENTAR PARA IMPORTAR
                    # print(i, proposta)  # todo EXCLUIR

                valor_after += 100
        except Exception as e:
            return e
        else:
            return total



