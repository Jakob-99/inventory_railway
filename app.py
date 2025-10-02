# app.py (Minimal version til test af databaseforbindelse og miljøvariabler)
import os
from dotenv import load_dotenv
from flask import Flask, render_template_string
import psycopg2

# Dette er kun til lokal test, da Railway selv injicerer variablerne.
# Vi beholder det for at undgå lokale fejl.
load_dotenv() 

app = Flask(__name__)

DB_VARIABLE_NAMES = [
    'DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 
    'DATABASE_PASSWORD', 'DATABASE_PORT', 'DB_SSLMODE'
]

def get_db_config_and_env_status():
    """Henter databasekonfiguration fra miljøvariabler og logger dem."""
    config = {}
    env_status = {}
    
    for name in DB_VARIABLE_NAMES: # loop gennem environment variabler og gem dem i env_status dict
        value = os.environ.get(name)
        env_status[name] = f"'{value}'" if value else "❌ MANGES (eller er tom)"
        
        # Behandling for PORT nummer: heltal, så skal konverteres til int
        if name == 'DATABASE_PORT' and value:
             try:
                 config['port'] = int(value)
             except ValueError:
                 config['port'] = value # Beholder strengen, hvis konvertering fejler

        # De andre variabler
        elif name == 'DATABASE_HOST':
             config['host'] = value
        elif name == 'DATABASE_NAME':
             config['database'] = value
        elif name == 'DATABASE_USER':
             config['user'] = value
        elif name == 'DATABASE_PASSWORD':
             config['password'] = value
        elif name == 'DB_SSLMODE':
             config['sslmode'] = value
        
    return config, env_status

def fetch_first_product(config):
    # Forsøg at oprette forbindelse og hent første række
    connection = None
    result = None
    error = None
    
    # Validering: Tjekker, at host er en streng (ikke None) og port er et heltal
    is_valid_config = isinstance(config.get('host'), str) and isinstance(config.get('port'), int)

    if not is_valid_config:
        error = f"Konfigurationsfejl: Host er ikke gyldig (type: {type(config.get('host'))}) eller Port er ikke et heltal (type: {type(config.get('port'))}). Tjek jeres Railway variabler."
        return result, error

    try:
        # Overfør nøglerne: host, database, user, password, port, sslmode til psycopg2 connect
        connection = psycopg2.connect(**config)
        
        with connection.cursor() as cursor:
            # Hent de første kolonner og 1 række til test
            cursor.execute("SELECT * FROM products LIMIT 1;") # kørsel af SQL forespørgsel
            row = cursor.fetchone()
            col_names = [desc[0] for desc in cursor.description]
            
            if row:
                result = dict(zip(col_names, row))
            else:
                result = "Tabellen 'products' er tom."
                
    except Exception as e:
        error = f"Databaseforbindelsesfejl: {e}"
        
    finally:
        if connection:
            connection.close()
            
    return result, error

@app.route('/')
def test_db():
    config, env_status = get_db_config_and_env_status()
    
    result, db_error = fetch_first_product(config)
    
    # --- Vis miljøstatus og resultat i HTML ---
    
    env_table = "".join([
        f"<li class='flex justify-between border-b py-2'><span class='font-mono text-gray-600'>{name}</span><span class='font-bold {('text-red-500' if 'MANGES' in status or 'None' in status else 'text-green-600')}'>{status}</span></li>" 
        for name, status in env_status.items()
    ])

    # Omdan konfiguration til en pænere streng for debug
    config_display = ", ".join([f"{k}: {v!r}" for k, v in config.items()])

    if db_error:
        db_result_html = f"<h2 class='text-2xl text-red-600 mb-4'>❌ Databaseforbindelsesfejl</h2><p class='bg-red-100 p-3 rounded text-red-800 break-words whitespace-pre-wrap'>{db_error}</p>"
    elif result:
        db_result_html = f"<h2 class='text-2xl text-green-600 mb-4'>✅ Forbindelse og Forespørgsel Lykkedes</h2><pre class='bg-gray-100 p-3 rounded overflow-auto whitespace-pre-wrap'>{result}</pre>"
    else:
        db_result_html = f"<h2 class='text-2xl text-yellow-600 mb-4'>⚠️ Database Test Resultat</h2><p class='bg-yellow-100 p-3 rounded text-yellow-800'>{result}</p>"

    # inline HTML til browser
    html_content = f"""
    <html>
    <head>
        <title>Railway DB Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          /* Sikrer Inter-fonten */
          body {{ font-family: 'Inter', sans-serif; }}
        </style>
    </head>
    <body class="bg-gray-50 p-4 sm:p-8">
        <div class="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-xl">
            <h1 class="text-2xl sm:text-3xl font-bold mb-6 text-center text-indigo-700">Railway Miljø & Database Debugger</h1>
            
            <div class="mb-8 border p-4 rounded-lg bg-blue-50 shadow-inner">
                <h2 class="text-xl font-semibold mb-3 text-blue-700">1. Miljøvariabler Fundet (os.environ.get)</h2>
                <ul class="list-none p-0">{env_table}</ul>
            </div>
            
            <div class="border p-4 rounded-lg bg-white shadow">
                <h2 class="text-xl font-semibold mb-3 text-indigo-700">2. Database Test Resultat</h2>
                {db_result_html}
            </div>
            
            <p class='mt-6 text-xs text-gray-500 text-center break-words'>
                Konfigurationsdata brugt (Host, Port er afgørende for typen): 
                <br><span class="font-mono">{config_display}</span>
            </p>
        </div>
    </body>
    </html>
    """
        
    return render_template_string(html_content)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
