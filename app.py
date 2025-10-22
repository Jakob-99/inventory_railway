import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string
import psycopg2

load_dotenv()  # Læs .env-filen automatisk

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )
# --- Simpelt HTML UI ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <title>Barcode Lookup</title>
    <style>
        body { font-family: Arial; background: #f4f4f4; text-align: center; margin-top: 100px; }
        h1 { color: #333; }
        .card { display: inline-block; background: white; padding: 20px 40px; border-radius: 10px; box-shadow: 0 2px 10px #ccc; }
        .result { margin-top: 20px; font-size: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📦 Produktopslag</h1>
        {% if product %}
            <div class="result">
                <b>Produkt:</b> {{ product }}<br>
                <b>Pris:</b> {{ price }} kr.
            </div>
        {% elif message %}
            <div class="result">{{ message }}</div>
        {% else %}
            <div class="result">Venter på scanning...</div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- Gem sidste produkt i hukommelsen ---
last_product = None
last_price = None
last_message = None

@app.route("/")
def home():
    return render_template_string(HTML_PAGE, product=last_product, price=last_price, message=last_message)

@app.route("/api/barcode", methods=["POST"])
def receive_barcode():
    global last_product, last_price, last_message

    data = request.get_json()
    barcode = data.get("barcode")

    if not barcode:
        last_product = None
        last_price = None
        last_message = "Ingen barcode modtaget"
        return jsonify({"error": "Ingen barcode modtaget"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT barcode, description, unitprice FROM products WHERE barcode = %s;", (barcode,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            last_product, last_price = result
            last_message = None
            print(f"✅ Fundet: {last_product} - {last_price} kr.")
            return jsonify({"message": "OK"}), 200
        else:
            last_product = None
            last_price = None
            last_message = "Produkt ikke fundet"
            print("❌ Produkt ikke fundet")
            return jsonify({"error": "Produkt ikke fundet"}), 404

    except Exception as e:
        last_product = None
        last_price = None
        last_message = "Databasefejl"
        print("⚠️ Databasefejl:", e)
        return jsonify({"error": "Databasefejl"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)