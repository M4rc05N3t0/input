import json
from banco_operacoes import Operacoes
import requests
from datetime import datetime


class Request:

    def __init__(self, ambiente):
        try:
            self.db = Operacoes(ambiente)
            self._api_key = self.db.obter_parametro('hubspot', 'fgts-saque-aniversario', 'itau', 'finance')
        except Exception as e:
            raise Exception(f"Falha ao inicializar http_request: {e}")

    def obter_propostas_input(self, pagina=0):
        # todo verificar classificação dos registros por: finan_rpa_datetime_input_simulacao?
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/search'
        headers = {'content-type': 'application/json',
                   'authorization': f'Bearer {self._api_key}'
        }
        data = '''{
                      "filterGroups": [
                        {
                          "filters": [
                            {
                              "value": "true",
                              "propertyName": "fgts_input_de_propostas_rpa",
                              "operator": "EQ"
                            },
                            {
                              "value": "RG",
                              "propertyName": "fgts_tipo_de_documento",
                              "operator": "CONTAINS_TOKEN"
                            }
                          ]
                        },
                        {
                          "filters": [                  
                            {
                              "value": "true",
                              "propertyName": "fgts_input_de_propostas_rpa",
                              "operator": "EQ"
                            },
                            {
                              "value": "CNH",
                              "propertyName": "fgts_tipo_de_documento",
                              "operator": "CONTAINS_TOKEN"
                            }
                          ]
                        }
                      ],
                      "sorts": [
                        "fgts_datetime_input_de_proposta"
                      ],
                      "properties": [
                        "cpf",
                        "email",
                        "fgts_data_de_nascimento",
                        "fgts_data_de_admissao",
                        "fgts_data_de_pagamento",
                        "fgts_valor_da_renda",
                        "fgts_cargo_geral",
                        "fgts_grau_de_instrucao",
                        "fgts_codigo_do_banco",
                        "fgts_agencia",
                        "fgts_conta_corrente",
                        "fgts_estado_civil",
                        "fgts_nome_do_conjuge",
                        "fgts_nome_da_mae",
                        "fgts_nome_do_pai",
                        "fgts_naturalidade",
                        "fgts_nacionalidade",
                        "fgts_tipo_de_documento",
                        "fgts_numero_do_documento",
                        "fgts_orgao_emissor_doc",
                        "fgts_estado_emissao_doc",
                        "fgts_data_emissao_documento",
                        "fgts_cep",
                        "fgts_rua",
                        "fgts_numero_da_residencia",
                        "fgts_complemento_endereco",
                        "fgts_bairro",
                        "phone",
                        "fgts_valor_contratado",
                        "fgts_genero",
                        "fgts_tipo_de_conta",
                        "fgts_estado",
                        "fgts_datetime_input_de_proposta"
                      ],
                     
                      "limit": 100,
                      "after": %s
                    }
        ''' % pagina
        request = requests.post(url=url, headers=headers, data=data)
        return request.text

    def atualizar_proposta_input(self, contact_id, status, motivo=None, numero_proposta=None, valor_contratado=None, data_hora_input=None, link=None):
        status_descricao = ["FALHA", "SUCESSO", "PENDENTE"]
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
        # 'authorization': f'Bearer {self._api_key}',
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self._api_key}'
        }

        data = json.loads(json.dumps({
            "fgts_input_de_propostas_rpa": "false",

            "fgts_data_input_proposta": datetime.today().strftime("%Y-%m-%d"),
            "fgts_hora_input_proposta_rpa": datetime.now().hour
        }))

        status = {"fgts_status_da_proposta_rpa": f"{status_descricao[status]}"}
        data.update(status)

        if motivo:
            motivo = {"fgts_detalhe_status_rpa": f"{motivo}"}
            data.update(motivo)
        if numero_proposta:
            numero_proposta = {"fgts_numero_proposta": f"{numero_proposta}"}
            data.update(numero_proposta)
        if valor_contratado:
            valor_contratado = {"fgts_valor_contratado": valor_contratado}
            data.update(valor_contratado)
        if link:
            link = {"fgts_link_contrato": link}
            data.update(link)

        # if data_hora_input:
        # data_hora_input = int(datetime.strptime(data_hora_input, '%Y-%m-%d %H:%M:%S.%f %z').timestamp()) * 1000
        agora = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S.%f')
        data_hora_input = (int(datetime.strptime(agora, '%Y-%m-%d %H:%M:%S.%f').timestamp())) * 1000  # offset: America/Sao Paulo (-03) => - 10800
        data_hora_input = {"fgts_datetime_retorno_rpa_input": data_hora_input}
        data.update(data_hora_input)

        propriedades = json.dumps({"properties": data})
        print(propriedades)
        request = requests.patch(url=url, headers=headers, data=propriedades)
        if request.status_code == 200:
            return True

        #     "properties": {
        #         "fgts_status_da_proposta_rpa": f"{status_descricao[status]}",
        #         "fgts_detalhe_status_rpa": f"{motivo}",
        #         "fgts_numero_proposta": f"{numero_proposta}",
        #         "fgts_valor_contratado": valor_contratado,
        #         "fgts_data_input_proposta": datetime.today().strftime("%Y-%m-%d"),
        #         "fgts_hora_input_proposta_rpa": datetime.now().hour
        #     }
        # }