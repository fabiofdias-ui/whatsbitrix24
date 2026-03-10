import os
import time
from flask import Flask, request, redirect
import requests

# --- CONFIGURAÇÃO (lida a partir do Render) ---
BITRIX24_INBOUND_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '')

app = Flask(__name__)

@app.route('/')
def home():
    return "Serviço de Tracking UTM para Bitrix24 (v2) está no ar!", 200

@app.route('/whatsapp')
def handle_whatsapp_redirect():
    # 1. Captura todos os parâmetros da URL (utm_source, etc.)
    utm_params = {key: value for key, value in request.args.items()}
    print(f"Parâmetros UTM capturados: {utm_params}")

    # 2. Prepara os campos para a API do Bitrix24
    # O Bitrix espera os campos no formato 'fields[UTM_SOURCE]', etc.
    fields_to_create = {f"UTM_{key.upper()}": value for key, value in utm_params.items()}
    
    # Adiciona um título para o lead para fácil identificação
    fields_to_create["TITLE"] = f"Novo Lead via WhatsApp UTM - {time.strftime('%Y-%m-%d %H:%M')}"
    
    # Adiciona o número de telefone ao lead (se quiser que ele já seja criado)
    # fields_to_create["PHONE"] = [{"VALUE": WHATSAPP_NUMBER, "VALUE_TYPE": "WORK"}]


    # 3. Monta a chamada para criar um NOVO lead já com os UTMs
    if BITRIX24_INBOUND_WEBHOOK_URL and utm_params:
        create_url = f"{BITRIX24_INBOUND_WEBHOOK_URL}crm.lead.add"
        payload = {'fields': fields_to_create}

        try:
            response = requests.post(create_url, json=payload)
            response.raise_for_status()
            print(f"Comando para criar lead com UTMs enviado. Resposta: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar comando para criar lead: {e}")
            # Mesmo que falhe, continua para o WhatsApp
    
    # 4. Redireciona o utilizador para o WhatsApp
    if not WHATSAPP_NUMBER:
        return "Erro: O número de WhatsApp não está configurado no servidor.", 500

    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}"
    return redirect(whatsapp_url )

# O webhook de saída não é mais necessário com esta abordagem
# A rota /bitrix-webhook pode ser removida ou deixada inativa

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

