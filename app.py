import os
from flask import Flask, request, jsonify, render_template_string
import psycopg2

app = Flask(__name__)

# --- Databaseforbindelse ---
def get_db_connection():
    """Opretter forbindelse til Railway PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )

# --- API: modtag barcode og returnér produkt + pris ---
@app.route("/api/barcode", methods=["POST"])
def lookup_product():
    """
    Modtager en barcode (JSON) fra den lokale scanner
    og søger efter produkt + pris i databasen.
    """
    data = request.get_json()
    barcode = data.get("barcode") if data else None

    if not barcode:
        return jsonify({"error": "Manglende 'barcode' felt"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT product_name, price FROM barcodes WHERE code = %s;", (barcode,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            product_name, price = row
            print(f"✅ Fundet: {barcode} → {product_name}, {price} kr.")
            return jsonify({
                "barcode": barcode,
                "product_name": product_name,
                "price": float(price)
            }), 200
        else:
            print(f"⚠️ Ikke fundet: {barcode}")
            return jsonify({"error": f"Produkt med barcode '{barcode}' blev ikke fundet"}), 404

    except Exception as e:
        print("❌ Databasefejl:", e)
        return jsonify({"error": f"Databasefejl: {e}"}), 500

# --- Simpelt UI til visning af hele databasen (til test) ---
@app.route("/")
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, product_name, price FROM barcodes ORDER BY code;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ DB læsefejl:", e)
        rows = []

    html = """
    <!DOCTYPE html>
    <html lang="da">
    <head>
        <meta charset="UTF-8">
        <title>💰 Barcode Prisopslag</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="max-w-3xl mx-auto my-10 bg-white p-6 rounded-xl shadow">
            <h1 class="text-3xl font-bold text-indigo-700 mb-4 text-center">💰 Barcode Prisopslag</h1>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-indigo-100">
                        <th class="p-2 border-b">Stregkode</th>
                        <th class="p-2 border-b">Produkt</th>
                        <th class="p-2 border-b">Pris (kr.)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for code, name, price in rows %}
                        <tr class="hover:bg-gray-50">
                            <td class="p-2 border-b font-mono">{{ code }}</td>
                            <td class="p-2 border-b">{{ name }}</td>
                            <td class="p-2 border-b">{{ price }}</td>
                        </tr>
                    {% else %}
                        <tr><td colspan="3" class="text-center py-4 text-gray-400">Ingen produkter fundet</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, rows=rows)

# --- Start app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)