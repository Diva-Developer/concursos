"""Conteúdo fixo dos planos: perfis de cargo, bancas e fontes de estudo.

Perfil = "área padrão" do cargo. Cada concurso aponta para um ou mais perfis e uma banca;
o gerador monta o plano daquele concurso juntando os dois. Para incluir um perfil ou banca
novos, basta acrescentar aqui (o raspador usa os mesmos padrões para reconhecer cargos).
"""

AREAS = {"seg": "Segurança", "ti": "Tecnologia", "fis": "Fisioterapia", "adm": "Administrativo e geral"}

F = {  # fontes: (nome, url, grátis?)
    "pci": ("PCI Concursos: provas anteriores", "https://www.pciconcursos.com.br/provas/", 1),
    "qc": ("QConcursos (filtro por banca e cargo)", "https://www.qconcursos.com/", 0),
    "tec": ("TEC Concursos", "https://www.tecconcursos.com.br/", 0),
    "cf": ("Constituição (Planalto)", "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm", 1),
    "cp": ("Código Penal", "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm", 1),
    "cpp": ("Código de Processo Penal", "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm", 1),
    "lgpd": ("LGPD", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm", 1),
    "cert": ("Cartilha de Segurança CERT.br", "https://cartilha.cert.br/", 1),
    "owasp": ("OWASP Top 10", "https://owasp.org/www-project-top-ten/", 1),
    "sqlbolt": ("SQLBolt", "https://sqlbolt.com/", 1),
    "rota": ("Sua Rota Dev", "https://claude.ai/artifact/Ntmkh5rJmDz2a1Y2n16JGf", 1),
    "l8080": ("Lei 8.080/1990 (SUS)", "https://www.planalto.gov.br/ccivil_03/leis/l8080.htm", 1),
    "l8142": ("Lei 8.142/1990", "https://www.planalto.gov.br/ccivil_03/leis/l8142.htm", 1),
    "d7508": ("Decreto 7.508/2011", "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/decreto/d7508.htm", 1),
    "coffito": ("Código de Ética (COFFITO 424/2013)", "https://www.coffito.gov.br/nsite/?p=3187", 1),
    "redacao": ("Manual de Redação da Presidência", "https://www.gov.br/planalto/pt-br/centrais-de-conteudo/publicacoes/manual-de-redacao-da-presidencia-da-republica", 1),
    "bcb": ("Banco Central: cidadania financeira", "https://www.bcb.gov.br/cidadaniafinanceira", 1),
}

# rx: reconhece o perfil no nome do cargo ou no texto do edital/notícia
# conteudo: o que costuma cair (para o card) · etapas: plano (t, horas, tarefas, fontes)
PERFIS = {
    "seg_sup": dict(
        nome="Policial de nível superior", area="seg",
        rx=r"pol[ií]cia civil|delegad|escriv[aã]o|agente de pol[ií]cia|policial penal|policial rodovi|perito criminal|papiloscop|investigador",
        conteudo=["Língua Portuguesa", "Informática", "Raciocínio lógico", "Direito Constitucional", "Direito Administrativo",
                  "Direito Penal", "Processo Penal", "Legislação penal especial", "Direitos Humanos", "Legislação do estado",
                  "Redação (quando houver)", "TAF"],
        etapas=[
            ("Português e interpretação", 45, ["Interpretação e reescrita de frases", "Pontuação, concordância, regência e crase", "150 questões da banca"], ["qc", "pci"]),
            ("Informática e raciocínio lógico", 35, ["Segurança, redes, nuvem e Office", "Proposições, equivalências e porcentagem", "150 questões da banca"], ["cert", "qc"]),
            ("Constitucional e Administrativo", 55, ["Art. 5º e art. 144 na lei seca", "Poderes, atos e agentes públicos", "200 questões da banca"], ["cf", "qc"]),
            ("Penal e Processo Penal", 65, ["Teoria do crime e crimes em espécie", "Inquérito, provas e prisões", "250 questões da banca"], ["cp", "cpp", "qc"]),
            ("Legislação especial, Direitos Humanos e lei do estado", 40, ["Drogas, desarmamento, abuso de autoridade, Maria da Penha", "Estatuto e lei orgânica da carreira", "Tópicos do edital que faltarem"], ["qc"]),
            ("Redação e TAF", 15, ["1 redação por semana nas últimas 8 semanas", "Treino físico 3x por semana desde o início"], []),
        ]),
    "seg_med": dict(
        nome="Segurança de nível médio (Soldado, Guarda, Agente de Trânsito)", area="seg",
        rx=r"soldado|guarda (civil )?municipal|guarda civil|agente de tr[aâ]nsito|agente de seguran[cç]a|vigilante|bombeiro militar",
        conteudo=["Língua Portuguesa", "Matemática e raciocínio lógico", "Informática", "Noções de Direito Constitucional (art. 5º e 144)",
                  "Noções de Direito Penal e Direitos Humanos", "Estatuto da corporação ou do município", "História e geografia do estado",
                  "Redação (PM)", "TAF"],
        etapas=[
            ("Português", 40, ["Interpretação de texto", "Gramática: concordância, crase, pontuação", "120 questões da banca"], ["qc", "pci"]),
            ("Matemática e raciocínio lógico", 30, ["Porcentagem, regra de três, frações", "Lógica básica e sequências", "100 questões da banca"], ["qc"]),
            ("Informática", 15, ["Windows, Office, internet e e-mail", "Segurança básica: vírus, backup, senhas"], ["cert"]),
            ("Noções de Direito", 35, ["Art. 5º e art. 144 da Constituição", "Crimes contra a pessoa e o patrimônio (noções)", "Direitos Humanos e uso da força"], ["cf", "cp"]),
            ("Legislação da corporação e do estado", 20, ["Estatuto e regulamento citados no edital", "História e geografia do estado"], ["qc"]),
            ("Redação e TAF", 15, ["1 redação por semana nas últimas 6 semanas", "Treino físico 3x por semana desde o início"], []),
        ]),
    "ti_sup": dict(
        nome="Analista de TI (superior)", area="ti",
        rx=r"analista (de |em )?(ti\b|tecnologia|sistemas|suporte|redes|seguran[cç]a da informa|dados)|desenvolvedor|engenheiro de software|ci[eê]ncia de dados|especialista em ti|analista de ti",
        conteudo=["Língua Portuguesa", "Raciocínio lógico", "Engenharia de software e ágil", "Programação e algoritmos",
                  "Banco de dados e SQL", "Redes e infraestrutura", "Segurança da informação e LGPD", "Governança (ITIL, COBIT)",
                  "Nuvem e DevOps", "IA e dados (editais recentes)"],
        etapas=[
            ("Português e raciocínio lógico", 50, ["Interpretação e gramática em contexto", "Lógica, contagem e probabilidade", "150 questões da banca"], ["qc", "pci"]),
            ("Engenharia de software e programação", 55, ["Scrum, Kanban, UML e testes", "Estruturas de dados e orientação a objetos", "Ler código e prever a saída"], ["rota", "qc"]),
            ("Banco de dados e SQL", 30, ["Modelagem, normalização, transações", "SELECT, JOIN, GROUP BY e índices"], ["sqlbolt", "qc"]),
            ("Redes, nuvem e DevOps", 30, ["TCP/IP, DNS, HTTP, VPN", "IaaS/PaaS/SaaS, Docker, CI/CD"], ["rota"]),
            ("Segurança da informação e LGPD", 35, ["ISO 27001/27002, criptografia, controle de acesso", "OWASP Top 10 e resposta a incidentes", "LGPD no setor público"], ["owasp", "lgpd", "cert"]),
            ("Governança e legislação do órgão", 15, ["ITIL e COBIT no nível de conceito", "Normas do órgão citadas no edital"], ["qc"]),
        ]),
    "ti_med": dict(
        nome="Técnico de TI / Informática (médio)", area="ti",
        rx=r"t[eé]cnico (em|de) (inform[aá]tica|ti\b|tecnologia)|t[eé]cnico de suporte|programador|operador de computador|assistente de ti|t[eé]cnico banc[aá]rio.{0,10}ti",
        conteudo=["Língua Portuguesa", "Matemática", "Hardware e manutenção", "Windows e Linux", "Redes básicas",
                  "Office e suporte ao usuário", "Segurança básica", "Noções de programação e banco de dados"],
        etapas=[
            ("Português e matemática", 40, ["Interpretação e gramática", "Porcentagem, razão e lógica básica", "120 questões da banca"], ["qc", "pci"]),
            ("Hardware, Windows e Linux", 30, ["Componentes, montagem e manutenção", "Comandos e administração básica"], ["qc"]),
            ("Redes e segurança", 25, ["Modelo TCP/IP, cabeamento, Wi-Fi, IP", "Antivírus, backup, firewall"], ["cert"]),
            ("Office, suporte e noções de programação", 25, ["Planilhas e editores", "Atendimento ao usuário", "Lógica, SQL básico"], ["sqlbolt"]),
            ("Legislação local", 10, ["Estatuto do servidor e lei orgânica do município"], []),
        ]),
    "fis": dict(
        nome="Fisioterapeuta", area="fis",
        rx=r"fisioterap",
        conteudo=["Língua Portuguesa", "Legislação do SUS (Lei 8.080, 8.142, Decreto 7.508)", "Ética profissional (COFFITO)",
                  "Anatomia, fisiologia e cinesiologia", "Fisioterapia cardiorrespiratória e UTI", "Neurofuncional",
                  "Traumato-ortopédica", "Saúde da mulher, pediatria e geriatria", "Saúde coletiva", "Legislação do órgão (EBSERH, município)"],
        etapas=[
            ("Português", 30, ["Interpretação e gramática", "100 questões da banca"], ["qc", "pci"]),
            ("SUS e saúde coletiva", 30, ["Leis 8.080 e 8.142 e Decreto 7.508 na íntegra", "Princípios e diretrizes, atenção básica", "100 questões de SUS"], ["l8080", "l8142", "d7508"]),
            ("Ética e base (anatomia, fisiologia, cinesiologia)", 30, ["Código de Ética do COFFITO", "Avaliação, cinesiologia e recursos terapêuticos"], ["coffito"]),
            ("Cardiorrespiratória e UTI", 35, ["Ventilação mecânica e desmame", "Gasometria e oxigenoterapia", "80 questões"], ["qc"]),
            ("Neuro e traumato-ortopédica", 40, ["AVC, lesão medular, Parkinson", "Fraturas, lesões esportivas, pós-operatório", "80 questões"], ["qc"]),
            ("Mulher, pediatria, geriatria e órgão", 20, ["Gestação, neonatal, idoso", "Legislação do órgão citada no edital"], ["qc"]),
        ]),
    "banc": dict(
        nome="Bancário (Escriturário, Técnico Bancário)", area="adm",
        rx=r"escritur[aá]rio|t[eé]cnico banc[aá]rio|agente comercial",
        conteudo=["Língua Portuguesa", "Matemática financeira", "Conhecimentos bancários", "Atualidades do mercado financeiro",
                  "Informática", "Vendas e negociação", "Inglês (alguns editais)"],
        etapas=[
            ("Português", 35, ["Interpretação e gramática", "120 questões da banca"], ["qc", "pci"]),
            ("Matemática financeira", 35, ["Juros simples e compostos, descontos", "Amortização (Price e SAC)"], ["qc"]),
            ("Conhecimentos bancários e atualidades", 35, ["Sistema Financeiro Nacional, produtos e PIX", "Prevenção à lavagem de dinheiro"], ["bcb", "qc"]),
            ("Vendas, atendimento e informática", 25, ["Técnicas de vendas, CDC e ética", "Office e segurança"], ["cert"]),
        ]),
    "adm_med": dict(
        nome="Administrativo de nível médio (Assistente, Auxiliar, Agente)", area="adm",
        rx=r"(assistente|auxiliar|agente|t[eé]cnico|oficial) (administrativ|de administra)|recepcionista|digitador|agente de (atendimento|portaria)",
        conteudo=["Língua Portuguesa", "Matemática e raciocínio lógico", "Informática (Office)", "Noções de Administração e arquivologia",
                  "Redação oficial e atendimento", "Noções de Direito Constitucional e Administrativo", "Estatuto do servidor e lei orgânica",
                  "Conhecimentos gerais do município e do estado"],
        etapas=[
            ("Português", 35, ["Interpretação e gramática", "120 questões da banca"], ["qc", "pci"]),
            ("Matemática e raciocínio lógico", 25, ["Porcentagem, regra de três, juros simples", "Lógica e sequências"], ["qc"]),
            ("Informática", 15, ["Word, Excel, internet e e-mail", "Segurança básica"], ["cert"]),
            ("Administração, arquivo e redação oficial", 20, ["Organização, atendimento ao público", "Arquivologia e protocolo", "Redação oficial"], ["redacao"]),
            ("Noções de Direito e legislação local", 20, ["Princípios da administração (art. 37)", "Estatuto do servidor e lei orgânica"], ["cf"]),
            ("Conhecimentos gerais", 10, ["História, geografia e economia do município e do estado", "Atualidades dos últimos 6 meses"], []),
        ]),
    "geral_sup": dict(
        nome="Superior em geral (Analista, Controlador, Advogado, outros)", area="adm",
        rx=r"analista (judici[aá]rio|administrativ|de gest)|controlador|auditor|advogado|procurador|contador|assessor jur[ií]dico|administrador",
        conteudo=["Língua Portuguesa", "Raciocínio lógico", "Informática", "Direito Constitucional e Administrativo",
                  "Administração pública", "Legislação do órgão", "Conhecimentos específicos do cargo (edital)"],
        etapas=[
            ("Português e raciocínio lógico", 45, ["Interpretação e gramática", "Lógica e matemática básica", "150 questões da banca"], ["qc", "pci"]),
            ("Constitucional e Administrativo", 45, ["Organização do Estado, art. 37 a 41", "Atos, licitações (14.133) e improbidade"], ["cf", "qc"]),
            ("Específicas do cargo", 50, ["Listar o conteúdo específico do edital", "Estudar pela ordem do que mais cai na banca"], ["qc"]),
            ("Informática e legislação do órgão", 20, ["Office e segurança", "Regimento ou lei orgânica do órgão"], ["cert"]),
        ]),
}

# bancas: rx para reconhecer no texto da notícia/edital, formato e como cobra
BANCAS = {
    "Cebraspe": dict(rx=r"cebraspe|cespe", formato="Itens de certo ou errado; cada erro anula um acerto",
                     dicas=["Deixar em branco é estratégia: só marque com convicção", "Texto longo e pegadinha de extrapolação",
                            "Treine com a nota líquida (certos menos errados)"], provas="https://www.cebraspe.org.br/concursos"),
    "FGV": dict(rx=r"\bFGV\b|getulio vargas", formato="Múltipla escolha, 5 alternativas, enunciados longos",
                dicas=["Português interpretativo, gramática dentro do texto", "Casos práticos em vez de decoreba",
                       "Discursiva corrigida só para os mais bem colocados"], provas="https://conhecimento.fgv.br/concursos"),
    "FCC": dict(rx=r"\bFCC\b|carlos chagas", formato="Múltipla escolha, 5 alternativas, questões diretas",
                dicas=["Muito próxima da letra da lei e das normas", "Gramática clássica: regência, crase, concordância"],
                provas="https://www.concursosfcc.com.br/"),
    "Instituto AOCP": dict(rx=r"\bAOCP\b", formato="Múltipla escolha, 5 alternativas",
                           dicas=["Lei seca e gramática tradicional", "Repete muito o estilo de provas anteriores"],
                           provas="https://www.institutoaocp.org.br/"),
    "Idecan": dict(rx=r"idecan", formato="Múltipla escolha, 4 ou 5 alternativas",
                   dicas=["Cobrança próxima da lei seca", "Legislação local tem peso"], provas="https://idecan.org.br/"),
    "Cesgranrio": dict(rx=r"cesgranrio", formato="Múltipla escolha, 5 alternativas",
                       dicas=["Matemática e conhecimentos bancários com cálculo", "Português com textos jornalísticos"],
                       provas="https://www.cesgranrio.org.br/"),
    "CPCon/UEPB": dict(rx=r"cpcon|uepb", formato="Múltipla escolha, 5 alternativas",
                       dicas=["Banca da Paraíba, comum em prefeituras", "Cobra legislação municipal e conhecimentos da PB"],
                       provas="https://cpcon.uepb.edu.br/"),
    "Comperve/UFRN": dict(rx=r"comperve", formato="Múltipla escolha, 4 alternativas",
                          dicas=["Banca do RN, comum em UFRN e órgãos estaduais", "Questões diretas, conteúdo do edital ao pé da letra"],
                          provas="https://www.comperve.ufrn.br/"),
    "IBFC": dict(rx=r"\bIBFC\b", formato="Múltipla escolha, 4 ou 5 alternativas",
                 dicas=["Lei seca e conceitos diretos"], provas="https://www.ibfc.org.br/"),
    "Consulplan": dict(rx=r"consulplan", formato="Múltipla escolha, 4 ou 5 alternativas",
                       dicas=["Português com textos longos", "Legislação seca"], provas="https://www.institutoconsulplan.org.br/"),
    "Marinha do Brasil": dict(rx=r"marinha", formato="Prova objetiva + títulos; algumas com redação",
                              dicas=["Conteúdo específico da profissão pesa mais", "TAF e inspeção de saúde eliminam"],
                              provas="https://www.marinha.mil.br/"),
}
BANCA_PADRAO = dict(formato="Banca ainda não identificada: confira no edital",
                    dicas=["Assim que souber a banca, faça 2 provas anteriores dela para pegar o estilo",
                           "Bancas pequenas de prefeitura costumam cobrar lei seca e legislação municipal"], provas=None)
