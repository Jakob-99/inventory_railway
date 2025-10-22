import os
from flask import Flask, request, render_template_string, jsonify
import psycopg2

app = Flask(__name__)

# --- Database helper ---
def get_db_connection():
    """
    Opretter forbindelse til Railway PostgreSQL via miljøvariabler.
    """
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )


# --- REST endpoint: søg barcode i DB ---
@app.route("/api/barcode", methods=["POST"])
def lookup_barcode():
    """
    Modtager en barcode fra den lokale scanner (JSON),
    søger i databasen og returnerer prisen hvis den findes.
    """
    data = request.get_json()
    barcode = data.get("barcode") if data else None

    if not barcode:
        return jsonify({"error": "Manglende 'barcode' felt"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT price FROM barcodes WHERE code = %s;", (barcode,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            price = row[0]
            print(f"✅ Fundet: {barcode} → {price} kr.")
            return jsonify({"barcode": barcode, "price": float(price)}), 200
        else:
            print(f"⚠️ Ikke fundet: {barcode}")
            return jsonify({"error": f"Barcode '{barcode}' blev ikke fundet"}), 404

    except Exception as e:
        print("❌ Databasefejl:", e)
        return jsonify({"error": f"Databasefejl: {e}"}), 500


# --- UI: viser hele barcode-listen med priser ---
@app.route("/")
def index():
    """
    Simpelt dashboard med alle barcodes og deres priser.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, price, created_at FROM barcodes ORDER BY created_at DESC;")
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>💰 Barcode Prisopslag</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 text-gray-800">
        <div class="max-w-3xl mx-auto my-10 bg-white p-6 rounded-xl shadow">
            <h1 class="text-3xl font-bold text-indigo-700 mb-4 text-center">💰 Barcode Prisopslag</h1>
            <p class="text-center text-gray-500 mb-6">
                Viser registrerede barcodes og deres priser
            </p>

            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-indigo-100">
                        <th class="p-2 border-b">Stregkode</th>
                        <th class="p-2 border-b">Pris (kr.)</th>
                        <th class="p-2 border-b">Oprettet</th>
                    </tr>
                </thead>
                <tbody>
                    {% for code, price, created_at in rows %}
                        <tr class="hover:bg-gray-50">
                            <td class="p-2 border-b font-mono">{{ code }}</td>
                            <td class="p-2 border-b">{{ price }}</td>
                            <td class="p-2 border-b text-sm text-gray-500">{{ created_at }}</td>
                        </tr>
                    {% else %}
                        <tr>
                            <td colspan="3" class="text-center py-4 text-gray-400">
                                Ingen barcodes fundet
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>

            <div class="mt-6 text-center">
                <p class="text-xs text-gray-400">
                    Flask app kører på Railway &middot; Prisopslag via PostgreSQL
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, rows=rows)


# --- Start app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)