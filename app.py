import os
import time
from flask import Flask, request, redirect
import requests

# --- CONFIGURAÇÃO (será feita no Render) ---
BITRIX24_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '')

# --- ARMAZENAMENTO TEMPORÁRIO ---
utm_storage = {}

app = Flask(__name__)

def clean_old_entries():
    current_time = time.time()
    keys_to_delete = [
        ip for ip, data in utm_storage.items()
        if current_time - data.get('timestamp', 0) > 300  # 5 minutos
    ]
    for ip in keys_to_delete:
        del utm_storage[ip]

@app.route('/')
def home():
    return "Serviço de Tracking UTM para Bitrix24 está no ar!", 200

@app.route('/whatsapp')
def handle_whatsapp_redirect():
    clean_old_entries()
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    utm_params = {key: value for key, value in request.args.items()}

    if utm_params:
        utm_storage[user_ip] = {
            'params': utm_params,
            'timestamp': time.time()
        }
        print(f"UTMs armazenados para o IP {user_ip}: {utm_params}")

    if not WHATSAPP_NUMBER:
        return "Erro: O número de WhatsApp não está configurado no servidor.", 500

    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}"
    return redirect(whatsapp_url )

@app.route('/bitrix-webhook', methods=['POST'])
def handle_bitrix_webhook():
    lead_id = request.form.get('data[FIELDS][ID]')
    if not lead_id:
        return "Webhook recebido, mas sem ID do Lead.", 400

    print(f"Webhook recebido para o Lead ID: {lead_id}")

    # Lógica de associação: encontrar a entrada mais recente no armazenamento
    if not utm_storage:
        print("Nenhum UTM em memória para associar.")
        return "Nenhum dado UTM em memória.", 200

    latest_ip = max(utm_storage, key=lambda ip: utm_storage[ip]['timestamp'])
    stored_data = utm_storage.pop(latest_ip) # Usar e remover
    utm_params = stored_data['params']
    
    print(f"Associando Lead {lead_id} com os UTMs de {latest_ip}: {utm_params}")

    if not BITRIX24_WEBHOOK_URL:
        print("Erro: O URL do webhook do Bitrix24 não está configurado.")
        return "Erro de configuração no servidor.", 500

    update_url = f"{BITRIX24_WEBHOOK_URL}crm.lead.update"
    fields_to_update = {f"UTM_{key.upper()}": value for key, value in utm_params.items()}

    payload = {'id': lead_id, 'fields': fields_to_update}

    try:
        response = requests.post(update_url, json=payload)
        response.raise_for_status()
        print(f"Lead {lead_id} atualizado com sucesso. Resposta: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao atualizar o lead {lead_id}: {e}")
        return "Erro ao comunicar com a API do Bitrix24", 500

    return "Lead atualizado com sucesso!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
