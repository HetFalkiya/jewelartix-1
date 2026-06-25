from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import json

app = Flask(__name__, static_folder='../static', template_folder='../templates')
CORS(app)

DATABASE_URL = (
    os.environ.get('DATABASE_URL') or
    os.environ.get('POSTGRES_URL') or
    os.environ.get('KOYEB_POSTGRESQL_URL') or ''
)

def get_db():
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    try:
        return psycopg2.connect(url, sslmode='require')
    except Exception:
        return psycopg2.connect(url)

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS quotations (
                id SERIAL PRIMARY KEY,
                quot_no TEXT UNIQUE NOT NULL,
                design_no TEXT,
                client_name TEXT,
                quot_date TEXT,
                data JSONB NOT NULL,
                pdf_base64 TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    return send_from_directory('../templates', 'quotation.html')

@app.route('/fp')
def finished_product():
    return send_from_directory('../templates', 'finished_product.html')

@app.route('/api/quotations', methods=['GET'])
def get_quotations():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT id,quot_no,design_no,client_name,quot_date,data,(pdf_base64 IS NOT NULL) as has_pdf,created_at,updated_at FROM quotations ORDER BY updated_at DESC')
    rows = cur.fetchall(); cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/quotations/<quot_no>', methods=['GET'])
def get_quotation(quot_no):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM quotations WHERE quot_no = %s', (quot_no,))
    row = cur.fetchone(); cur.close(); conn.close()
    return jsonify(dict(row)) if row else (jsonify({'error':'Not found'}), 404)

@app.route('/api/quotations', methods=['POST'])
def save_quotation():
    body = request.json
    quot_no = body.get('quotNo') or body.get('quot_no')
    if not quot_no: return jsonify({'error':'quotNo required'}), 400
    conn = get_db(); cur = conn.cursor()
    cur.execute('''
        INSERT INTO quotations (quot_no,design_no,client_name,quot_date,data,pdf_base64,updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (quot_no) DO UPDATE SET
        design_no=EXCLUDED.design_no,client_name=EXCLUDED.client_name,
        quot_date=EXCLUDED.quot_date,data=EXCLUDED.data,
        pdf_base64=EXCLUDED.pdf_base64,updated_at=NOW()
    ''', (quot_no, body.get('designNo',''), body.get('clientName',''),
          body.get('quotDate',''), json.dumps(body), body.get('pdfBase64')))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success':True, 'quotNo':quot_no})

@app.route('/api/quotations/<quot_no>', methods=['DELETE'])
def delete_quotation(quot_no):
    conn = get_db(); cur = conn.cursor()
    cur.execute('DELETE FROM quotations WHERE quot_no=%s', (quot_no,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success':True})

@app.route('/api/settings/<key>', methods=['GET'])
def get_setting(key):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT value FROM settings WHERE key=%s', (key,))
    row = cur.fetchone(); cur.close(); conn.close()
    return jsonify(row['value']) if row else jsonify(None)

@app.route('/api/settings/<key>', methods=['POST'])
def save_setting(key):
    value = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute('''
        INSERT INTO settings (key,value,updated_at) VALUES (%s,%s,NOW())
        ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value,updated_at=NOW()
    ''', (key, json.dumps(value)))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success':True})

@app.route('/api/settings/<key>', methods=['DELETE'])
def delete_setting(key):
    conn = get_db(); cur = conn.cursor()
    cur.execute('DELETE FROM settings WHERE key=%s', (key,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success':True})

@app.route('/api/formstate/<tool>', methods=['GET'])
def get_formstate(tool):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT value FROM settings WHERE key=%s', (f'formstate_{tool}',))
    row = cur.fetchone(); cur.close(); conn.close()
    return jsonify(row['value']) if row else jsonify(None)

@app.route('/api/formstate/<tool>', methods=['POST'])
def save_formstate(tool):
    value = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute('''
        INSERT INTO settings (key,value,updated_at) VALUES (%s,%s,NOW())
        ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value,updated_at=NOW()
    ''', (f'formstate_{tool}', json.dumps(value)))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success':True})

init_db()
