import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import tempfile

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO INICIAL
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Erro ao configurar a API do Google: {e}")

# -----------------------------------------------------------------------------
# CARREGAMENTO DO PLAYBOOK
# -----------------------------------------------------------------------------
def carregar_playbook():
    try:
        caminho_script = os.path.dirname(__file__)
        caminho_playbook = os.path.join(caminho_script, 'playbook.txt')
        with open(caminho_playbook, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Nenhum playbook foi carregado. Analise com base em boas práticas de vendas."

playbook_texto = carregar_playbook()

# -----------------------------------------------------------------------------
# PROMPTS PARA ÁUDIO E TEXTO
# -----------------------------------------------------------------------------
# Prompt para quando o input é um ÁUDIO
PROMPT_AUDIO = f"""
Você é um coach de vendas de alta performance. Seu objetivo é analisar o ÁUDIO de uma ligação e fornecer feedback baseado no playbook abaixo.

--- PLAYBOOK ---
{playbook_texto}
--- FIM DO PLAYBOOK ---

**TAREFA:**
Ouça o áudio, transcreva-o mentalmente e analise a transcrição. Sua resposta DEVE ser em formato Markdown com as seções "✅ PONTOS POSITIVOS" e "💡 PONTOS CONSTRUTIVOS".
"""

# Prompt para quando o input é um TEXTO
PROMPT_TEXTO = f"""
Você é um coach de vendas de alta performance. Seu objetivo é analisar a TRANSCRIÇÃO de uma ligação e fornecer feedback baseado no playbook abaixo.

--- PLAYBOOK ---
{playbook_texto}
--- FIM DO PLAYBOOK ---

**TAREFA:**
Analise a transcrição fornecida. Sua resposta DEVE ser em formato Markdown com as seções "✅ PONTOS POSITIVOS" e "💡 PONTOS CONSTRUTIVOS".

A transcrição é a seguinte:
"""

# -----------------------------------------------------------------------------
# ROTA PRINCIPAL DA API
# -----------------------------------------------------------------------------
@app.route('/api/analisar', methods=['POST'])
def analisar_input():
    if not os.getenv("GOOGLE_API_KEY"):
        return jsonify({"erro": "A chave de API do Google não está configurada no servidor."}), 500

    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

    try:
        # --- FLUXO PARA ÁUDIO ---
        if request.content_type.startswith('multipart/form-data'):
            if 'audio' not in request.files:
                return jsonify({"erro": "Nenhum arquivo de áudio foi enviado."}), 400
            
            audio_file = request.files['audio']
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name

            audio_file_uploaded = genai.upload_file(path=temp_audio_path)
            while audio_file_uploaded.state.name == "PROCESSING":
                audio_file_uploaded = genai.get_file(audio_file_uploaded.name)
            
            if audio_file_uploaded.state.name == "FAILED":
                return jsonify({"erro": "Falha ao processar o arquivo de áudio."}), 500
            
            response = model.generate_content([PROMPT_AUDIO, audio_file_uploaded])
            os.remove(temp_audio_path) # Limpa o arquivo temporário
            return jsonify({"feedback": response.text})

        # --- FLUXO PARA TEXTO ---
        elif request.content_type == 'application/json':
            data = request.get_json()
            if not data or 'texto' not in data or not data['texto'].strip():
                return jsonify({"erro": "Nenhum texto foi enviado no corpo da requisição."}), 400
            
            texto_transcrito = data['texto']
            prompt_final = f"{PROMPT_TEXTO}\n\n{texto_transcrito}"
            
            response = model.generate_content(prompt_final)
            return jsonify({"feedback": response.text})

        else:
            return jsonify({"erro": f"Tipo de conteúdo não suportado: {request.content_type}"}), 415

    except Exception as e:
        print(f"Ocorreu um erro na API: {e}")
        return jsonify({"erro": f"Ocorreu um erro no servidor. Detalhes: {str(e)}"}), 500

# Rota de "health check"
@app.route('/', methods=['GET'])
def health_check():
    return "Backend do Coach de IA (Gemini) está funcionando!"
