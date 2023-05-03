from banco import Banco


class Operacoes:

    def __init__(self, ambiente):
        try:
            if ambiente == 'prod':
                self.maestro = 'MAESTRO_PROD'
            else:
                self.maestro = 'MAESTRO_STAGING'
            self.db = Banco(ambiente)
        except Exception as e:
            raise Exception(f"Falha ao inicializar banco_operacoes: {e}")

    def obter_parametro(self, nome, sistema=None, area_negocio=None, vertical=None):
        return self.db.executar_query_scalar(f"""
            SELECT valor FROM rpa_parametros
            WHERE nome = '{nome}'
            AND sistema {"= '" + sistema + "'" if sistema else "is null"}
            AND area_negocio {"= '" + area_negocio + "'" if area_negocio else "is null"}
            AND vertical {"= '" + vertical + "'" if vertical else "is null"}
        """, self.maestro)

    def obter_parametros(self, nome, sistema=None, area_negocio=None, vertical=None):
        return self.db.executar_query(f"""
            SELECT valor FROM rpa_parametros
            WHERE nome = '{nome}'
            AND sistema {"= '" + sistema + "'" if sistema else "is null"}
            AND area_negocio {"= '" + area_negocio + "'" if area_negocio else "is null"}
            AND vertical {"= '" + vertical + "'" if vertical else "is null"}
        """, self.maestro)

    def registrar_captcha(self, hostname):
        if self.maestro == "MAESTRO_PROD":
            self.db.executar_comando(f"""INSERT INTO captcha_control (hostname, recaptcha, script)
                                         VALUES ('{hostname}', false, 'itau-saque-aniversario');""", self.maestro)

    def registrar_consulta(self, id_registro, usuario):
        self.db.executar_comando(f"""INSERT INTO saque_aniversario_consultas (usuario, id_registro) VALUES
                                     ('{usuario}', {id_registro});""", self.maestro)

    def atualizar_senha(self, usuario, nova_senha, email_usuario, hostname):
        self.db.executar_comando(f"""UPDATE public.rpa_parametros
                                    SET valor = '{usuario};{nova_senha};{email_usuario}'
                                    WHERE  nome = 'login-{hostname}'
                                    AND sistema = 'fgts-saque-aniversario'
                                    AND area_negocio = 'itau'
                                    AND vertical = 'finance';""", self.maestro)

    def obter_registro(self, hostname, input_):
        instrucao = ""
        if input_:
            instrucao = """, (SELECT para FROM saque_aniversario_itau_correspondencias WHERE de ILIKE sai.fgts_grau_de_instrucao) AS grau_instrucao,
                             (SELECT para FROM saque_aniversario_itau_correspondencias WHERE de = sai.fgts_estado) AS estado"""

        # return self.db.executar_query(f"""
        #     SELECT *{instrucao if input_ else ""} FROM saque_aniversario_itau{"_input" if input_ else ""} AS sai
        #     WHERE (status = 'processando' and hostname = '{hostname}')
        #     OR (status IS NULL and (hostname IS NULL or hostname = '{hostname}'))
        #     ORDER BY updated_at ASC
        #     LIMIT 1;
        # """, self.maestro, True)

        # return self.db.executar_query(f"""
        # WITH registro AS (
        #    SELECT id
        #    FROM saque_aniversario_itau{"_input" if input_ else ""}
        #     WHERE (status = 'processando' and hostname = '{hostname}')
        #     OR (status IS NULL and (hostname IS NULL or hostname = '{hostname}'))
        #     ORDER BY updated_at ASC
        #    LIMIT 1
        #    )
        # UPDATE saque_aniversario_itau{"_input" if input_ else ""} AS sai
        # SET status = 'processando',
        # hostname = '{hostname}',
        # updated_at = NOW()
        # FROM registro
        # WHERE  sai.id = registro.id
        # RETURNING sai.*{instrucao};""", self.maestro, True)

        # print(f"""
        # UPDATE saque_aniversario_itau{"_input" if input_ else ""} AS sai
        # SET status = 'processando',
        # hostname = '{hostname}',
        # updated_at = NOW()
        # FROM registro
        # WHERE  sai.id = (
        #     SELECT id
        #        FROM saque_aniversario_itau{"_input" if input_ else ""}
        #         WHERE (status = 'processando' and hostname = '{hostname}')
        #         OR (status IS NULL and (hostname IS NULL or hostname = '{hostname}'))
        #         AND pg_try_advisory_xact_lock(id)
        #         ORDER BY updated_at ASC
        #         FOR UPDATE
        #        LIMIT 1
        # )
        # RETURNING sai.*{instrucao};""")

        return self.db.executar_query(f"""
        UPDATE saque_aniversario_itau{"_input" if input_ else ""} AS sai
        SET status = 'processando',
        hostname = '{hostname}',
        updated_at = NOW()
        WHERE  sai.id = (
            SELECT id
               FROM saque_aniversario_itau{"_input" if input_ else ""}
                WHERE (status = 'processando' and hostname = '{hostname}')
                OR (status IS NULL and (hostname IS NULL or hostname = '{hostname}'))
                AND pg_try_advisory_xact_lock(id)
                ORDER BY updated_at ASC
                FOR UPDATE
               LIMIT 1                
        )
        RETURNING sai.*{instrucao};""", self.maestro, True)

    def verificar_registros(self, hostname, input_):
        return self.db.executar_query(f"""
            SELECT id FROM saque_aniversario_itau{"_input" if input_ else ""} AS sai 
            WHERE (status = 'processando' and hostname = '{hostname}')
            OR (status IS NULL and (hostname IS NULL or hostname = '{hostname}'))
            LIMIT 1;
        """, self.maestro, True)

    def registros_processando(self):
        return self.db.executar_query("""
            SELECT id FROM saque_aniversario_itau_input
            WHERE (status = 'processando'
            AND updated_at > (NOW() - '10 MINUTES'::interval))
            or (status is NULL
            AND created_at > (NOW() - '30 MINUTES'::interval))
            OR status = 'ag_icconsig'
        """, self.maestro)

    def obter_registro_icconsig(self, hostname):
        return self.db.executar_query(f"""
            SELECT id, contact_id, numero_proposta, valor_contratado, cpf, data_hora_input FROM saque_aniversario_itau_input AS sai 
            WHERE status = 'ag_icconsig'
            -- AND hostname = ''
            ORDER BY updated_at DESC
            LIMIT 1;
        """, self.maestro, True)  # AND hostname = '{hostname}'

    def obter_qtde_registros_icconsig(self, hostname):
        return self.db.executar_query_scalar(f"""
            SELECT count(id) FROM saque_aniversario_itau_input
            WHERE status = 'ag_icconsig'
        """, self.maestro)

    def logar_mensagem(self, tipo, mensagem, id_projeto):
        mensagem = str(mensagem).replace("'", "''")
        self.db.executar_comando(f"""INSERT INTO rpa_log (tipo, mensagem, id_projeto) VALUES ('{tipo}', '{mensagem}', {id_projeto});""", self.maestro)

    def obter_info_projeto(self):
        return self.db.executar_query(f"""SELECT id, nome, descricao FROM rpa_projetos
                                          WHERE nome = 'fgts-saque-aniversario';
        """, self.maestro, True)

    def atualizar_status(self, id):
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau
            SET status = 'processando',
            updated_at = NOW()
            WHERE id = {id};
        """, self.maestro)

    def atualizar_status_input(self, id, status="processando", numero_proposta=None, valor_contratado=None, tentativas=None, mensagem_hubspot=None, data_hora_input=None):
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau_input
            SET status = '{status}',
            {"numero_proposta = '" + numero_proposta + "'," if numero_proposta else ""}
            {"valor_contratado = '" + str(valor_contratado) + "'," if valor_contratado else ""}
            {"tentativas = " + str(tentativas) + "," if tentativas else ""}
            {"mensagem_hubspot = '" + mensagem_hubspot + "'," if mensagem_hubspot else ""}
            {"data_hora_input = '" + str(data_hora_input) + "'," if data_hora_input else ""}
            updated_at = NOW()
            WHERE id = {id};
        """, self.maestro)

    def verificar_registro(self, id, input_=False):
        return self.db.executar_query_scalar(f"""
            SELECT id FROM saque_aniversario_itau{"_input" if input_ else ""}
            WHERE id = {id};
        """, self.maestro)

    def atualizar_mensagem(self, id, mensagem, input_=False, status="concluido"):
        mensagem = mensagem.strip()
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau{"_input" if input_ else ""} 
            SET mensagem_hubspot = '{mensagem}',
            status = '{status}',
            updated_at = NOW()
            WHERE id = {id};
        """, self.maestro)

    def atualizar_valor(self, id, valor_liberado, limite_disponivel, parcelas_antecipadas):
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau 
            SET valor = {valor_liberado},
            limite_fgts = {limite_disponivel},
            parcelas_antecipadas = {parcelas_antecipadas},
            status = 'pendente_valor',
            updated_at = NOW()
            WHERE id = {id};
        """, self.maestro)

    def limpar_consulta(self, id, input_=False):
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau{"_input" if input_ else ""} 
            SET status = NULL,
            hostname = NULL
            WHERE id = {id};
        """, self.maestro)

    def limpar_registros(self, hostname, input_=False):
        self.db.executar_comando(f"""
            UPDATE saque_aniversario_itau{"_input" if input_ else ""}
            SET hostname = NULL,
            status = NULL,
            updated_at = NOW()
            WHERE hostname = '{hostname}'
            AND status = 'processando'
        """, self.maestro)

    def inserir_proposta_input(self, proposta):
        for indice, item in enumerate(proposta):
            if not proposta[indice] or proposta[indice] == 'None':
                proposta[indice] = ''
            else:
                proposta[indice] = proposta[indice].replace("'", "''").encode("latin-1", "ignore").decode("cp1252")

        return self.db.executar_query_scalar(f'''
            INSERT INTO public.saque_aniversario_itau_input
                (contact_id, cpf, email, fgts_data_de_nascimento, fgts_data_de_admissao, fgts_data_da_renda, fgts_valor_da_renda,
                fgts_cargo_geral, fgts_grau_de_instrucao, fgts_codigo_do_banco, fgts_agencia, fgts_conta_corrente, fgts_estado_civil,
                fgts_nome_do_conjuge, fgts_nome_da_mae, fgts_nome_do_pai, fgts_naturalidade, fgts_nacionalidade, fgts_tipo_de_documento,
                fgts_numero_do_documento, fgts_orgao_emissor_doc, fgts_estado_emissao_doc, fgts_data_emissao_documento, fgts_cep, fgts_rua,
                fgts_numero_da_residencia, fgts_complemento_endereco, fgts_bairro, fgts_numero_do_telefone, fgts_valor_contratado, fgts_genero,
                fgts_tipo_de_conta, fgts_estado, updated_at)
            VALUES (
                 {proposta[0]}, '{proposta[1]}', '{proposta[2]}', '{proposta[3]}', '{proposta[4]}', '{proposta[5]}', '{proposta[6]}',
                '{proposta[7]}', '{proposta[8]}', '{proposta[9]}', '{proposta[10]}', '{proposta[11]}', '{proposta[12]}', '{proposta[13]}',
                '{proposta[14]}', '{proposta[15]}', '{proposta[16]}', '{proposta[17]}', '{proposta[18]}', '{proposta[19]}', '{proposta[20]}',
                '{proposta[21]}', '{proposta[22]}', '{proposta[23]}', '{proposta[24]}', '{proposta[25]}', '{proposta[26]}', '{proposta[27]}',
                '{proposta[28]}', '{proposta[29]}', '{proposta[30]}', '{proposta[31]}', '{proposta[32]}', NOW()
            ) RETURNING id''', self.maestro)

    def excluir_registros_nao_processados(self, input_=False):
        self.db.executar_comando(f"""
            {'''
            DELETE FROM saque_aniversario_consultas sac
            WHERE sac.id_registro IN(
                SELECT id FROM saque_aniversario_itau
                WHERE status = 'falha_interna'
                OR status IS NULL
                OR status = 'processando');
            ''' if not input_ else ""}

            DELETE FROM saque_aniversario_itau{"_input" if input_ else ""}
            WHERE status IN('falha_interna', 'processando')
            OR status IS NULL
            {"" if input_ else "OR status = 'processando'"}
        """, self.maestro)

