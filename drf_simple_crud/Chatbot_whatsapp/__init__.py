# __init__.py (PhoneFX WhatsApp Bot + Flask + RiveScript + citas)
from flask import Flask, jsonify, request
from rivescript import RiveScript
import requests
import mysql.connector
import os
import re

app = Flask(__name__)

# --- CONFIGURACIÓN GENERAL ---
WA_TOKEN = os.getenv("WA_TOKEN", "EAAJPfe9KjgoBPxUTETELcmYo8tATHVcCuxz274jJnDGZCeKvjNC9HjsSZBNJ91Mp8S0ZCZBCuuMUoNZBpGIjfOjzQZC0CUcafovLpFs0jCGJFJyS2Ye9oixtjYeZC7yfZAFj7lld8ZB9f0HcpzlPgtoWGhDHXxjrBdPcRlkzN6LrpxBNfWyGrqXAmquhSspoEkT1qQdzdsEU6LF5m3BfinSoILPb4Hm7ZA6DcUenw8HpEBrQDtAxOEok9M8banaakuHa0Me0Dsa7DKlNd33g66qPGMQTJB")
WA_PHONE_ID = os.getenv("WA_PHONE_ID", "706948065843345")
HUMAN_PHONE = os.getenv("HUMAN_PHONE", "+57 3103407868")

# --- CONEXIÓN A LA BASE DE DATOS ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3307)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "rooot"),
        database=os.getenv("DB_NAME", "phonefx_2")
    )

# --- REGISTRO DE MENSAJES ---
def registrar_log(mensaje_recibido, mensaje_enviado, id_wa, timestamp_wa, telefono_wa, tipo="faq"):
    db = get_db_connection()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO registro (mensaje_recibido, mensaje_enviado, id_wa, timestamp_wa, telefono_wa, tipo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (mensaje_recibido, mensaje_enviado, id_wa, timestamp_wa, telefono_wa, tipo))
        db.commit()
    except Exception as e:
        print("Error insert registro:", e)
    finally:
        cur.close()
        db.close()

# --- CREAR O BUSCAR CLIENTE (solo por teléfono) ---
def buscar_o_crear_usuario(telefono):
    # No existe tabla usuarios, pero mantenemos función por compatibilidad
    tel = telefono.replace("+", "").replace(" ", "")
    return tel[-4:]  # se usa parte del número como pseudo-ID

# --- CREAR CITA (tabla: cita) ---
def crear_cita(id_cliente, fecha, hora, tipo_servicio="Reparación", observaciones="Agendada via WhatsApp"):
    db = get_db_connection()
    cur = db.cursor()
    try:
        # Insert adaptado al esquema real de 'cita'
        cur.execute("""
            INSERT INTO cita (nombre, fecha, hora, tipo)
            VALUES (%s, %s, %s, %s)
        """, (f"Cliente {id_cliente}", fecha, hora, tipo_servicio))
        db.commit()
        id_cita = cur.lastrowid
    except Exception as e:
        print("Error crear cita:", e)
        id_cita = None
    finally:
        cur.close()
        db.close()
    return id_cita

# --- ENVIAR MENSAJE POR WHATSAPP (API META) ---
def enviar_whatsapp(telefono, texto):
    url = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": texto}
    }
    headers = {"Authorization": f"Bearer {WA_TOKEN}"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=8)
        print("WA send:", r.status_code, r.text)
        return r.status_code == 200 or r.status_code == 201
    except Exception as e:
        print("Error enviar WA:", e)
        return False

# --- DETECTAR INTENCIÓN ---
def detectar_intencion(mensaje):
    m = mensaje.lower()
    if any(x in m for x in ["humano", "asesor", "representante", "hablar con alguien", "atención humana"]):
        return "humano"
    if any(x in m for x in ["cita", "agendar", "reservar", "hora", "fecha"]):
        return "cita"
    return "faq"

# --- EXTRAER FECHA Y HORA DEL TEXTO ---
def extraer_fecha_hora(mensaje):
    fecha = re.search(r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})", mensaje)
    hora = re.search(r"(\d{1,2}:\d{2})", mensaje)
    return fecha.group(0) if fecha else None, hora.group(0) if hora else None

# --- RiveScript ---
bot = RiveScript()
bot.load_file("tienda.rive")
bot.sort_replies()

# --- WEBHOOK ---
@app.route("/webhook/", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        if token == os.getenv("VERIFY_TOKEN", "HolaNovato"):
            return request.args.get("hub.challenge")
        return "Token inválido", 403

    data = request.get_json(silent=True) or {}
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        telefono = msg["from"]
        texto = msg["text"]["body"]
        id_wa = msg.get("id")
        timestamp = msg.get("timestamp")
    except Exception:
        return jsonify({"status": "sin_mensaje"}), 200

    intent = detectar_intencion(texto)

    # --- Escalar a humano ---
    if intent == "humano":
        respuesta = f"Te conecto con un asesor humano. Comunícate al {HUMAN_PHONE} o espera que te contactemos."
        enviar_whatsapp(telefono, respuesta)
        registrar_log(texto, respuesta, id_wa, timestamp, telefono, tipo="escalado")
        enviar_whatsapp(HUMAN_PHONE, f"[Escalado] Usuario {telefono} solicita atención humana. Mensaje: {texto}")
        return jsonify({"status": "escalado"}), 200

    # --- Agendar cita ---
    if intent == "cita":
        fecha, hora = extraer_fecha_hora(texto)
        if not fecha or not hora:
            respuesta = "Para agendar dime la fecha (dd/mm/aaaa) y la hora (hh:mm). Ejemplo: 15/11/2025 14:30"
            enviar_whatsapp(telefono, respuesta)
            registrar_log(texto, respuesta, id_wa, timestamp, telefono, tipo="cita_pedir")
            return jsonify({"status": "pedir_fecha"}), 200

        user_id = buscar_o_crear_usuario(telefono)
        id_cita = crear_cita(user_id, fecha, hora)
        if id_cita:
            respuesta = f"Tu cita ha sido agendada ✅ (ID {id_cita}). Fecha: {fecha} Hora: {hora}. ¡Te esperamos!"
            enviar_whatsapp(telefono, respuesta)
            registrar_log(texto, respuesta, id_wa, timestamp, telefono, tipo="cita_agendada")
            enviar_whatsapp(HUMAN_PHONE, f"🗓 Nueva cita (ID {id_cita}) - Cliente: {telefono} - Fecha: {fecha} Hora: {hora}")
            return jsonify({"status": "cita_agendada", "id_cita": id_cita}), 200
        else:
            respuesta = "Ocurrió un error al agendar la cita. Intenta nuevamente o contacta a un asesor."
            enviar_whatsapp(telefono, respuesta)
            registrar_log(texto, respuesta, id_wa, timestamp, telefono, tipo="cita_error")
            return jsonify({"status": "error_crear_cita"}), 200

    # --- Preguntas normales (FAQ) ---
    reply = bot.reply("localuser", texto).strip()
    if not reply:
        reply = "No entendí eso. Si quieres hablar con un humano escribe 'hablar con humano'."
    enviar_whatsapp(telefono, reply)
    registrar_log(texto, reply, id_wa, timestamp, telefono, tipo="faq")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
