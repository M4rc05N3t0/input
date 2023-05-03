CREATE TABLE public.saque_aniversario_itau_input (
	id serial4 NOT NULL,
	contact_id int4 NOT NULL,
	status varchar DEFAULT NULL,
	mensagem_hubspot varchar DEFAULT NULL,
	numero_proposta varchar NULL,
	valor_contratado varchar NULL,
	hostname varchar DEFAULT NULL,
	tentativas int4 NULL,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NULL,
	cpf varchar NULL,
	email varchar NULL,
	fgts_data_de_nascimento varchar NULL,
	fgts_data_de_admissao varchar NULL,
	fgts_data_da_renda varchar NULL,
	fgts_valor_da_renda varchar NULL,
	fgts_cargo_geral varchar NULL,
	fgts_grau_de_instrucao varchar NULL,
	fgts_codigo_do_banco varchar NULL,
	fgts_agencia varchar NULL,
	fgts_conta_corrente varchar NULL,
	fgts_estado_civil varchar NULL,
	fgts_nome_do_conjuge varchar NULL,
	fgts_nome_da_mae varchar NULL,
	fgts_nome_do_pai varchar NULL,
	fgts_naturalidade varchar NULL,
	fgts_nacionalidade varchar NULL,
	fgts_tipo_de_documento varchar NULL,
	fgts_numero_do_documento varchar NULL,
	fgts_orgao_emissor_doc varchar NULL,
	fgts_estado_emissao_doc varchar NULL,
	fgts_data_emissao_documento varchar NULL,
	fgts_cep varchar NULL,
	fgts_rua varchar NULL,
	fgts_numero_da_residencia varchar NULL,
	fgts_complemento_endereco varchar NULL,
	fgts_bairro varchar NULL,
	fgts_numero_do_telefone varchar NULL,
	fgts_valor_contratado varchar NULL,
	fgts_genero varchar NULL,
	fgts_tipo_de_conta varchar NULL,
	fgts_estado varchar NULL,
	CONSTRAINT saque_aniversario_itau_input_id_pk PRIMARY KEY (id)
);

CREATE TABLE public.saque_aniversario_itau_correspondencias (
	id serial4 NOT NULL,
	de varchar NOT NULL,
	para varchar NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT saque_aniversario_itau_corresp_id_pk PRIMARY KEY (id)
);

-- INSERT INTO public.saque_aniversario_itau_correspondencias (de, para)
-- VALUES
-- ('Analfabeto', 'Analfabeto'),
-- ('Ensino médio incompleto', 'Ensino médio incompleto'),
-- ('Ensino médio completo', 'Ensino médio completo'),
-- ('Ensino fundamental incompleto', 'Da 4 a 8 série do ensino fundamental'),
-- ('Ensino fundamental completo', 'Ensino fundamental completo'),
-- ('Superior completo (ou graduação)', 'Educação superior completo'),
-- ('Pós-graduação', 'Pós-graduação completo'),
-- ('Mestrado', 'Mestrado completo'),
-- ('Doutorado', 'Doutorado completo'),
-- ('Pós-Doutorado', 'Pós-Doutorado completo');

INSERT INTO public.saque_aniversario_itau_correspondencias (de, para)
VALUES
('Analfabeto', 'ANALFABETO'),
('Ensino Médio Incompleto', 'ENSINO MÉDIO INCOMPLETO'),
('Ensino Médio Completo', 'ENSINO MÉDIO COMPLETO'),
('Ensino Fundamental Incompleto', 'DA 5 A 8 SERIE DO ENSINO FUNDAMENTAL'),
('Ensino Fundamental Completo', 'ENSINO FUNDAMENTAL COMPLETO'),
('Superior Completo (Ou Graduação)', 'EDUCACAO SUPERIOR COMPLETO'),
('Superior Completo', 'EDUCACAO SUPERIOR COMPLETO'),
('Pós-Graduação', 'POS-GRADUAÇÃO COMPLETO'),
('Mestrado', 'MESTRADO COMPLETO'),
('Doutorado', 'DOUTORADO COMPLETO'),
('Pós-Doutorado', 'POS-DOUTORADO COMPLETO'),
('Superior Completo', 'EDUCACAO SUPERIOR COMPLETO'),
('Fundamental Incompleto', 'DA 5 A 8 SERIE DO ENSINO FUNDAMENTAL'),
('Superior Incompleto', 'EDUCACAO SUPERIOR INCOMPLETO'),
('Fundamental Completo', 'ENSINO FUNDAMENTAL COMPLETO'),
('Pós Graduado', 'POS-GRADUAÇÃO COMPLETO'),
('AC', 'ACRE'),
('AL',  'ALAGOAS'),
('AP',  'AMAPA'),
('AM',  'AMAZONAS'),
('BA',  'BAHIA'),
('CE',  'CEARA'),
('DF',  'DISTRITO FEDERAL'),
('ES',  'ESPIRITO SANTO'),
('GO',  'GOIAS'),
('MA',  'MARANHAO'),
('MT',  'MATO GROSSO'),
('MS',  'MATO GROSSO DO SUL'),
('MG',  'MINAS GERAIS'),
('PA',  'PARA'),
('PB',  'PARAIBA'),
('PR',  'PARANA'),
('PE',  'PERNAMBUCO'),
('PI',  'PIAUI'),
('RJ',  'RIO DE JANEIRO'),
('RN',  'RIO GRANDE DO NORTE'),
('RS',  'RIO GRANDE DO SUL'),
('RO',  'RONDONIA'),
('RR',  'RORAIMA'),
('SC',  'SANTA CATARINA'),
('SP',  'SAO PAULO'),
('SE',  'SERGIPE'),
('TO',  'TOCANTINS');

• Campo Dígito da Agência não aceita entrada;
• Lista de correspondência de escolaridade com dados divergentes;
• Lista de correspondência de Estado ausente;
• Sem menção ao endpoint e relacionamento interno da Hubspot para obtenção dos dados;
• Tipagem dos dados da Hubspot ausente;
• Tipagem dos dados do IBConsig ausente;
• Formato/Máscara dos dados esperados ausente;


