import os
from flask import Flask, request, render_template_string, jsonify
import psycopg2

app = Flask(__name__)

# --- Database helper ---
def get_db_connection():
    """
    Opretter forbindelse til Railway PostgreSQL.
    """
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=int(os.getenv("DATABASE_PORT")),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )


# --- API endpoint: søg barcode ---
@app.route("/api/barcode", methods=["POST"])
def lookup_barcode():
    """
    Modtager barcode fra lokal scanner og viser resultatet.
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
            price = float(row[0])
            print(f"✅ Fundet: {barcode} → {price} kr.")

            # Render kun den ene scanning som UI
            html = f"""
            <!DOCTYPE html>
            <html lang="da">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>💰 Barcode fundet</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen">
                <div class="bg-white p-8 rounded-xl shadow-lg text-center">
                    <h1 class="text-3xl font-bold text-indigo-700 mb-6">💰 Barcode Fundet</h1>
                    <p class="text-gray-600 mb-3">Stregkode:</p>
                    <p class="text-2xl font-mono mb-4 text-gray-800">{barcode}</p>
                    <p class="text-gray-600 mb-3">Pris:</p>
                    <p class="text-3xl font-bold text-green-600">{price:.2f} kr.</p>
                    <p class="text-sm text-gray-400 mt-6">Data hentet fra Railway PostgreSQL</p>
                </div>
            </body>
            </html>
            """
            return html, 200
        else:
            print(f"⚠️ Ikke fundet: {barcode}")
            html = f"""
            <!DOCTYPE html>
            <html lang="da">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>❌ Barcode ikke fundet</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen">
                <div class="bg-white p-8 rounded-xl shadow-lg text-center">
                    <h1 class="text-3xl font-bold text-red-600 mb-6">❌ Ikke Fundet</h1>
                    <p class="text-gray-600 mb-3">Stregkode:</p>
                    <p class="text-2xl font-mono mb-4 text-gray-800">{barcode}</p>
                    <p class="text-gray-500">Ingen pris fundet i databasen.</p>
                    <p class="text-sm text-gray-400 mt-6">Railway PostgreSQL</p>
                </div>
            </body>
            </html>
            """
            return html, 404

    except Exception as e:
        print("❌ Databasefejl:", e)
        return jsonify({"error": f"Databasefejl: {e}"}), 500


# --- Start app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)