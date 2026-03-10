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
    return "Serviço de Tracking UTM para Bitrix24 (v5 - Corrigido) está no ar!", 200

@app.route('/whatsapp')
def handle_whatsapp_redirect():
    utm_params = {key: value for key, value in request.args.items()}
    print(f"Parâmetros UTM capturados: {utm_params}")

    # Prepara os campos para a API
    fields_to_create = {
        "TITLE": f"Novo Lead via WhatsApp UTM - {time.strftime('%Y-%m-%d %H:%M')}"
    }
    
    # --- CORREÇÃO FINAL AQUI ---
    # Adiciona os campos UTM ao dicionário, garantindo que não há duplicação
    for key, value in utm_params.items():
        # Transforma 'utm_source' em 'UTM_SOURCE' e não 'UTM_UTM_SOURCE'
        field_name = key.upper()
        if not field_name.startswith('UTM_'):
            field_name = f"UTM_{field_name}"
        fields_to_create[field_name] = value

    if BITRIX24_INBOUND_WEBHOOK_URL and utm_params:
        create_url = f"{BITRIX24_INBOUND_WEBHOOK_URL}crm.lead.add"
        payload = {'fields': fields_to_create}

        try:
            response = requests.post(create_url, json=payload)
            response.raise_for_status()
            print(f"Comando para criar lead com UTMs enviado. Payload: {payload}. Resposta: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar comando para criar lead: {e}")
    
    # Redireciona para o WhatsApp
    if not WHATSAPP_NUMBER:
        return "Erro: O número de WhatsApp não está configurado no servidor.", 500

    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}"
    return redirect(whatsapp_url )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
