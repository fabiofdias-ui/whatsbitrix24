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
    return "Serviço de Tracking UTM para Bitrix24 (v4 - Final) está no ar!", 200

@app.route('/whatsapp')
def handle_whatsapp_redirect():
    utm_params = {key: value for key, value in request.args.items()}
    print(f"Parâmetros UTM capturados: {utm_params}")

    # Prepara os campos para a API
    fields_to_create = {
        "TITLE": f"Novo Lead via WhatsApp UTM - {time.strftime('%Y-%m-%d %H:%M')}"
    }
    # Adiciona os campos UTM ao dicionário
    for key, value in utm_params.items():
        fields_to_create[f"UTM_{key.upper()}"] = value

    if BITRIX24_INBOUND_WEBHOOK_URL and utm_params:
        create_url = f"{BITRIX24_INBOUND_WEBHOOK_URL}crm.lead.add"
        payload = {'fields': fields_to_create}

        try:
            response = requests.post(create_url, json=payload)
            response.raise_for_status()
            print(f"Comando para criar lead com UTMs enviado. Payload: {payload}. Resposta: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar comando para criar lead: {e}")
    
    # Redireciona para o WhatsApp independentemente do resultado
    if not WHATSAPP_NUMBER:
        return "Erro: O número de WhatsApp não está configurado no servidor.", 500

    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}"
    return redirect(whatsapp_url )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
