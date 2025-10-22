import os
from flask import Flask, request, jsonify, render_template_string
import psycopg2

app = Flask(__name__)

# --- Databaseforbindelse ---
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )

# --- HTML (simpel side) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <title>Produktopslag</title>
    <style>
        body { font-family: Arial; margin: 50px; background: #f7f7f7; }
        h1 { color: #333; }
        input, button { padding: 10px; font-size: 16px; }
        #result { margin-top: 20px; font-size: 18px; }
    </style>
</head>
<body>
    <h1>Slå produkt op</h1>
    <input id="barcode" type="text" placeholder="Indtast stregkode">
    <button onclick="lookup()">Søg</button>
    <div id="result"></div>

    <script>
    async function lookup() {
        const code = document.getElementById('barcode').value;
        const res = await fetch('/api/barcode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({barcode: code})
        });
        const data = await res.json();
        const result = document.getElementById('result');
        if (res.ok) {
            result.innerHTML = `<b>${data.product_name}</b> - ${data.price} kr.`;
        } else {
            result.innerHTML = data.error || 'Fejl ved opslag';
        }
    }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/api/barcode", methods=["POST"])
def get_product():
    data = request.get_json()
    barcode = data.get("barcode")

    if not barcode:
        return jsonify({"error": "Ingen barcode modtaget"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, product_name, price FROM barcodes WHERE code = %s;", (barcode,))
        product = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": "Databasefejl"}), 500

    if product:
        code, name, price = product
        return jsonify({"code": code, "product_name": name, "price": price})
    else:
        return jsonify({"error": "Produkt ikke fundet"}), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)