import os
from dotenv import load_dotenv
from flask import Flask, request, render_template_string, jsonify
import psycopg2

# --- Indlæs miljøvariabler ---
load_dotenv()

app = Flask(__name__)

# --- Database helper ---
def get_db_connection():
    """
    Opretter forbindelse til PostgreSQL-databasen vha. miljøvariabler.
    Railway stiller selv disse værdier til rådighed.
    """
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )

# --- Database init (oprettes automatisk ved første start) ---
def init_db():
    """
    Sikrer at tabellen 'barcodes' eksisterer i databasen.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS barcodes (
                id SERIAL PRIMARY KEY,
                code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabellen 'barcodes' er klar.")
    except Exception as e:
        print("❌ DB init fejl:", e)

# Kør initialisering ved start
init_db()

# --- REST endpoint til modtagelse af barcode-data ---
@app.route("/api/barcode", methods=["POST"])
def receive_barcode():
    """
    Modtager barcode fra den lokale scanner (JSON) og gemmer i databasen.
    """
    data = request.get_json()
    barcode = data.get("barcode") if data else None

    if not barcode:
        return jsonify({"error": "Manglende 'barcode' felt"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO barcodes (code) VALUES (%s);", (barcode,))
        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Barcode gemt: {barcode}")
        return jsonify({"message": f"Barcode '{barcode}' gemt ✅"}), 201

    except Exception as e:
        print("❌ Databasefejl:", e)
        return jsonify({"error": f"Databasefejl: {e}"}), 500

# --- UI: viser alle gemte barcodes ---
@app.route("/")
def index():
    """
    Viser en simpel UI-side med alle barcodes og scanningstidspunkter.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, created_at FROM barcodes ORDER BY created_at DESC;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        rows = []
        print("DB læsefejl:", e)

    html = """
    <!DOCTYPE html>
    <html lang="da">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📦 Barcode Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 text-gray-800">
        <div class="max-w-3xl mx-auto my-10 bg-white p-6 rounded-xl shadow">
            <h1 class="text-3xl font-bold text-indigo-700 mb-4 text-center">📦 Barcode Dashboard</h1>
            <p class="text-center text-gray-500 mb-6">
                Viser data sendt fra den lokale stregkodescanner via REST API
            </p>

            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-indigo-100">
                        <th class="p-2 border-b">Stregkode</th>
                        <th class="p-2 border-b">Tidspunkt</th>
                    </tr>
                </thead>
                <tbody>
                    {% for code, created_at in rows %}
                        <tr class="hover:bg-gray-50">
                            <td class="p-2 border-b font-mono">{{ code }}</td>
                            <td class="p-2 border-b text-sm text-gray-500">{{ created_at }}</td>
                        </tr>
                    {% else %}
                        <tr>
                            <td colspan="2" class="text-center py-4 text-gray-400">
                                Ingen data scannet endnu
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>

            <div class="mt-6 text-center">
                <p class="text-xs text-gray-400">
                    Flask app kører på Railway &middot; Data gemmes i PostgreSQL
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