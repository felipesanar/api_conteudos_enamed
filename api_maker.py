import pandas as pd
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
import os
from datetime import datetime
import glob

app = Flask(__name__)

# Configuração do Swagger
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "API Cronograma de Estudos"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Variável global para armazenar os dados processados
dados_cronograma = {}

def processar_arquivos(pasta_arquivos):
    """
    Processa todos os arquivos XLSX/CSV na pasta especificada e estrutura os dados
    """
    global dados_cronograma
    
    # Inicializar estrutura de dados
    dados_cronograma = {
        "semanas": {},
        "dias": {},
        "temas": {},
        "subtemas": {},
        "aulas": {}
    }
    
    # Processar todos os arquivos na pasta
    arquivos = glob.glob(os.path.join(pasta_arquivos, '*.xlsx')) + glob.glob(os.path.join(pasta_arquivos, '*.csv'))
    
    for arquivo in arquivos:
        try:
            # Determinar se é XLSX ou CSV
            if arquivo.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                df = pd.read_csv(arquivo)
            
            # Processar cada linha do arquivo
            for _, row in df.iterrows():
                processar_linha(row)
                
        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
    
    # Estruturar hierarquia completa
    estruturar_hierarquia()
    
    # Exibir resumo do processamento
    print("\nResumo do processamento:")
    print(f"- {len(dados_cronograma.get('semanas', {}))} semanas carregadas")
    print(f"- {len(dados_cronograma.get('dias', {}))} dias carregados")
    print(f"- {len(dados_cronograma.get('temas', {}))} temas carregados")
    print(f"- {len(dados_cronograma.get('subtemas', {}))} subtemas carregados")
    print(f"- {len(dados_cronograma.get('aulas', {}))} aulas carregadas")

def processar_linha(row):
    """
    Processa uma linha individual do arquivo e adiciona aos dados
    """
    def limpar(valor):
        return str(valor or '').strip()
    
    # Extrair informações básicas
    semana = limpar(row.get('Semana'))
    dia = limpar(row.get('Dia'))
    tema_principal = limpar(row.get('Tema Principal'))
    subtema = limpar(row.get('Subtema'))
    aula = limpar(row.get('Aula'))
    link_aula = limpar(row.get('Link Aula'))
    link_questoes = limpar(row.get('Link Questões'))
    
    # Adicionar semana se não existir
    if semana and semana not in dados_cronograma["semanas"]:
        dados_cronograma["semanas"][semana] = {
            "numero": semana,
            "periodo": extrair_periodo(semana),
            "dias": []
        }
    
    # Adicionar dia se não existir
    chave_dia = f"{semana}_{dia}"
    if dia and chave_dia not in dados_cronograma["dias"]:
        dados_cronograma["dias"][chave_dia] = {
            "nome": dia,
            "area_conhecimento": extrair_area_conhecimento(dia),
            "temas": []
        }
        if semana in dados_cronograma["semanas"]:
            dados_cronograma["semanas"][semana]["dias"].append(dados_cronograma["dias"][chave_dia])
    
    # Adicionar tema principal se não existir
    chave_tema = f"{chave_dia}_{tema_principal}"
    if tema_principal and chave_tema not in dados_cronograma["temas"]:
        dados_cronograma["temas"][chave_tema] = {
            "nome": tema_principal,
            "subtemas": []
        }
        if chave_dia in dados_cronograma["dias"]:
            dados_cronograma["dias"][chave_dia]["temas"].append(dados_cronograma["temas"][chave_tema])
    
    # Adicionar subtema se não existir
    chave_subtema = f"{chave_tema}_{subtema}"
    if subtema and chave_subtema not in dados_cronograma["subtemas"]:
        dados_cronograma["subtemas"][chave_subtema] = {
            "nome": subtema,
            "aulas": []
        }
        if chave_tema in dados_cronograma["temas"]:
            dados_cronograma["temas"][chave_tema]["subtemas"].append(dados_cronograma["subtemas"][chave_subtema])
    
    # Adicionar aula se existir
    if aula:
        chave_aula = f"{chave_subtema}_{aula}"
        dados_cronograma["aulas"][chave_aula] = {
            "nome": aula,
            "link_aula": link_aula,
            "link_questoes": link_questoes
        }
        if chave_subtema in dados_cronograma["subtemas"]:
            dados_cronograma["subtemas"][chave_subtema]["aulas"].append(dados_cronograma["aulas"][chave_aula])

def extrair_periodo(semana_str):
    """
    Extrai o período da string da semana (ex: "Semana 01 (11/08-17/08)" -> "11/08-17/08")
    """
    if '(' in semana_str and ')' in semana_str:
        return semana_str.split('(')[1].split(')')[0]
    return ""

def extrair_area_conhecimento(dia_str):
    """
    Extrai a área de conhecimento do nome do dia (ex: "Dia 1 - Ginecologia e Obstetrícia" -> "Ginecologia e Obstetrícia")
    """
    if '-' in dia_str:
        return dia_str.split('-')[1].strip()
    return ""

def estruturar_hierarquia():
    """
    Estrutura os dados em uma hierarquia completa para a API
    """
    global dados_cronograma
    
    cronograma = {
        "cronograma": {
            "semanas": []
        }
    }
    
    # Ordenar semanas
    semanas_ordenadas = sorted(dados_cronograma["semanas"].values(), key=lambda x: x["numero"])
    
    for semana in semanas_ordenadas:
        semana_dict = {
            "numero": semana["numero"],
            "periodo": semana["periodo"],
            "dias": []
        }
        
        # Processar dias da semana
        for dia in semana["dias"]:
            dia_dict = {
                "nome": dia["nome"],
                "area_conhecimento": dia["area_conhecimento"],
                "temas": []
            }
            
            # Processar temas do dia
            for tema in dia["temas"]:
                tema_dict = {
                    "nome": tema["nome"],
                    "subtemas": []
                }
                
                # Processar subtemas do tema
                for subtema in tema["subtemas"]:
                    subtema_dict = {
                        "nome": subtema["nome"],
                        "aulas": subtema["aulas"]
                    }
                    tema_dict["subtemas"].append(subtema_dict)
                
                dia_dict["temas"].append(tema_dict)
            
            semana_dict["dias"].append(dia_dict)
        
        cronograma["cronograma"]["semanas"].append(semana_dict)
    
    dados_cronograma["hierarquia"] = cronograma

# Endpoint raiz
@app.route('/')
def home():
    return """
    <h1>API Cronograma de Estudos</h1>
    <p>Endpoints disponíveis:</p>
    <ul>
        <li><a href="/api/cronograma">/api/cronograma</a> - Cronograma completo</li>
        <li><a href="/api/docs">/api/docs</a> - Documentação Swagger</li>
        <li><a href="/api/semanas">/api/semanas</a> - Lista de semanas</li>
        <li><a href="/api/dias">/api/dias</a> - Lista de dias</li>
        <li><a href="/api/temas">/api/temas</a> - Lista de temas</li>
        <li><a href="/api/subtemas">/api/subtemas</a> - Lista de subtemas</li>
        <li><a href="/api/aulas">/api/aulas</a> - Lista de aulas</li>
        <li><a href="/api/buscar?q=termo">/api/buscar?q=termo</a> - Busca flexível</li>
    </ul>
    """

# Endpoints da API
@app.route('/api/cronograma', methods=['GET'])
def get_cronograma_completo():
    """
    Retorna toda a estrutura do cronograma
    ---
    tags:
      - Cronograma
    responses:
      200:
        description: Estrutura completa do cronograma
    """
    return jsonify(dados_cronograma.get("hierarquia", {}))

@app.route('/api/semanas', methods=['GET'])
def get_semanas():
    """
    Retorna lista de todas as semanas
    ---
    tags:
      - Semanas
    responses:
      200:
        description: Lista de semanas
    """
    return jsonify({"semanas": list(dados_cronograma.get("semanas", {}).values())})

@app.route('/api/semanas/<string:semana_numero>', methods=['GET'])
def get_semana(semana_numero):
    """
    Retorna detalhes de uma semana específica
    ---
    tags:
      - Semanas
    parameters:
      - name: semana_numero
        in: path
        type: string
        required: true
        description: Número da semana (ex: "Semana 01")
    responses:
      200:
        description: Detalhes da semana
      404:
        description: Semana não encontrada
    """
    semana = dados_cronograma.get("semanas", {}).get(semana_numero)
    if semana:
        return jsonify(semana)
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route('/api/dias', methods=['GET'])
def get_dias():
    """
    Retorna lista de todos os dias
    ---
    tags:
      - Dias
    responses:
      200:
        description: Lista de dias
    """
    return jsonify({"dias": list(dados_cronograma.get("dias", {}).values())})

@app.route('/api/dias/<string:dia_nome>', methods=['GET'])
def get_dia(dia_nome):
    """
    Retorna detalhes de um dia específico
    ---
    tags:
      - Dias
    parameters:
      - name: dia_nome
        in: path
        type: string
        required: true
        description: Nome do dia (ex: "Dia 1 - Ginecologia e Obstetrícia")
    responses:
      200:
        description: Detalhes do dia
      404:
        description: Dia não encontrado
    """
    # Encontrar dia pelo nome (pode ser parcial)
    dias_encontrados = []
    for chave, dia in dados_cronograma.get("dias", {}).items():
        if dia_nome.lower() in dia["nome"].lower():
            dias_encontrados.append(dia)
    
    if dias_encontrados:
        return jsonify({"dias": dias_encontrados})
    return jsonify({"error": "Dia não encontrado"}), 404

@app.route('/api/temas', methods=['GET'])
def get_temas():
    """
    Retorna lista de todos os temas principais
    ---
    tags:
      - Temas
    responses:
      200:
        description: Lista de temas
    """
    return jsonify({"temas": list(dados_cronograma.get("temas", {}).values())})

@app.route('/api/subtemas', methods=['GET'])
def get_subtemas():
    """
    Retorna lista de todos os subtemas
    ---
    tags:
      - Subtemas
    responses:
      200:
        description: Lista de subtemas
    """
    return jsonify({"subtemas": list(dados_cronograma.get("subtemas", {}).values())})

@app.route('/api/subtemas/<string:subtema_nome>', methods=['GET'])
def get_subtema(subtema_nome):
    """
    Retorna detalhes de um subtema específico com todas as aulas
    ---
    tags:
      - Subtemas
    parameters:
      - name: subtema_nome
        in: path
        type: string
        required: true
        description: Nome do subtema (ex: "Assistência pré-natal")
    responses:
      200:
        description: Detalhes do subtema
      404:
        description: Subtema não encontrado
    """
    # Encontrar subtema pelo nome (pode ser parcial)
    subtemas_encontrados = []
    for chave, subtema in dados_cronograma.get("subtemas", {}).items():
        if subtema_nome.lower() in subtema["nome"].lower():
            subtemas_encontrados.append(subtema)
    
    if subtemas_encontrados:
        return jsonify({"subtemas": subtemas_encontrados})
    return jsonify({"error": "Subtema não encontrado"}), 404

@app.route('/api/aulas', methods=['GET'])
def get_aulas():
    """
    Retorna lista de todas as aulas
    ---
    tags:
      - Aulas
    responses:
      200:
        description: Lista de aulas
    """
    return jsonify({"aulas": list(dados_cronograma.get("aulas", {}).values())})

@app.route('/api/buscar', methods=['GET'])
def buscar():
    """
    Busca flexível por qualquer termo no cronograma
    ---
    tags:
      - Busca
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Termo de busca
    responses:
      200:
        description: Resultados da busca
    """
    termo = request.args.get('q', '').lower()
    if not termo:
        return jsonify({"error": "Parâmetro de busca 'q' é obrigatório"}), 400
    
    resultados = {
        "semanas": [],
        "dias": [],
        "temas": [],
        "subtemas": [],
        "aulas": []
    }
    
    # Buscar em semanas
    for semana in dados_cronograma.get("semanas", {}).values():
        if termo in semana["numero"].lower() or termo in semana["periodo"].lower():
            resultados["semanas"].append(semana)
    
    # Buscar em dias
    for dia in dados_cronograma.get("dias", {}).values():
        if (termo in dia["nome"].lower() or 
            termo in dia["area_conhecimento"].lower()):
            resultados["dias"].append(dia)
    
    # Buscar em temas
    for tema in dados_cronograma.get("temas", {}).values():
        if termo in tema["nome"].lower():
            resultados["temas"].append(tema)
    
    # Buscar em subtemas
    for subtema in dados_cronograma.get("subtemas", {}).values():
        if termo in subtema["nome"].lower():
            resultados["subtemas"].append(subtema)
    
    # Buscar em aulas
    for aula in dados_cronograma.get("aulas", {}).values():
        if termo in aula["nome"].lower():
            resultados["aulas"].append(aula)
    
    return jsonify(resultados)

@app.route('/static/swagger.json')
def swagger():
    """
    Retorna a especificação Swagger/OpenAPI
    """
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "API Cronograma de Estudos",
            "description": "API para acesso ao cronograma de estudos estruturado",
            "version": "1.0.0"
        },
        "paths": {
            "/api/cronograma": {
                "get": {
                    "summary": "Retorna toda a estrutura do cronograma",
                    "responses": {
                        "200": {
                            "description": "Estrutura completa do cronograma"
                        }
                    }
                }
            },
            "/api/semanas": {
                "get": {
                    "summary": "Retorna lista de todas as semanas",
                    "responses": {
                        "200": {
                            "description": "Lista de semanas"
                        }
                    }
                }
            },
            "/api/semanas/{semana_numero}": {
                "get": {
                    "summary": "Retorna detalhes de uma semana específica",
                    "parameters": [
                        {
                            "name": "semana_numero",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Detalhes da semana"
                        },
                        "404": {
                            "description": "Semana não encontrada"
                        }
                    }
                }
            },
            "/api/dias": {
                "get": {
                    "summary": "Retorna lista de todos os dias",
                    "responses": {
                        "200": {
                            "description": "Lista de dias"
                        }
                    }
                }
            },
            "/api/dias/{dia_nome}": {
                "get": {
                    "summary": "Retorna detalhes de um dia específico",
                    "parameters": [
                        {
                            "name": "dia_nome",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Detalhes do dia"
                        },
                        "404": {
                            "description": "Dia não encontrado"
                        }
                    }
                }
            },
            "/api/temas": {
                "get": {
                    "summary": "Retorna lista de todos os temas principais",
                    "responses": {
                        "200": {
                            "description": "Lista de temas"
                        }
                    }
                }
            },
            "/api/subtemas": {
                "get": {
                    "summary": "Retorna lista de todos os subtemas",
                    "responses": {
                        "200": {
                            "description": "Lista de subtemas"
                        }
                    }
                }
            },
            "/api/subtemas/{subtema_nome}": {
                "get": {
                    "summary": "Retorna detalhes de um subtema específico com todas as aulas",
                    "parameters": [
                        {
                            "name": "subtema_nome",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Detalhes do subtema"
                        },
                        "404": {
                            "description": "Subtema não encontrado"
                        }
                    }
                }
            },
            "/api/aulas": {
                "get": {
                    "summary": "Retorna lista de todas as aulas",
                    "responses": {
                        "200": {
                            "description": "Lista de aulas"
                        }
                    }
                }
            },
            "/api/buscar": {
                "get": {
                    "summary": "Busca flexível por qualquer termo no cronograma",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Resultados da busca"
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger_spec)

if __name__ == '__main__':
    # Configuração inicial
    pasta_arquivos = 'dados_cronograma'
    
    # Criar pasta se não existir
    if not os.path.exists(pasta_arquivos):
        os.makedirs(pasta_arquivos)
        print(f"Por favor, coloque os arquivos XLSX/CSV na pasta '{pasta_arquivos}'")
    
    # Processar arquivos
    processar_arquivos(pasta_arquivos)
    
    # Iniciar API
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)

