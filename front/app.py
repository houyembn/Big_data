from flask import Flask, render_template, request, redirect, url_for
import os
import json
import csv
import requests
from elasticsearch import Elasticsearch

# import requests  # Don't forget to import requests

app = Flask(__name__)

es = Elasticsearch(["http://localhost:9200"])

LOGS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'logstash', 'logs')

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Define Kibana URL and visualization ID
KIBANA_URL = "https://special-zebra-p4xxxpp6px7frgpw-5601.app.github.dev/"
# /  # URL complète de votre instance Kibana
VISUALIZATION_ID = "2fd19d70-b0f4-11ef-b56f-dd912938df1d"


@app.route('/')
def install():
    error_message = request.args.get('error_message')
    return render_template('install.html', error_message=error_message)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('install', error_message="Aucun fichier sélectionné"))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('install', error_message="Aucun fichier sélectionné"))

    if file and allowed_file(file.filename):
        filename = os.path.join(LOGS_DIR, file.filename)
        file.save(filename)

        try:
            if filename.endswith('.json'):
                process_json(filename)
            elif filename.endswith('.csv'):
                process_csv(filename)
        except Exception as e:
            return redirect(url_for('install', error_message=f"Erreur lors du traitement du fichier: {str(e)}"))

        return redirect(url_for('install'))

    return redirect(url_for('install', error_message="Fichier non autorisé, uniquement JSON ou CSV."))


@app.route('/dashboard')
def show_visualization():
    return render_template('dashboard.html')


@app.route('/chercher', methods=['GET', 'POST'])
def chercher_logs():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            # Elasticsearch search query
            es_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["LineId", "Label", "Timestamp", "Date", "Node", "Time", "NodeRepeat", "Type"," Component","Level", "Content","EvenId","EventTemplate"]
                    }
                }
            }
            response = es.chercher(install="csv-2024.12.02", body=es_query)
            results = response.get('hits', {}).get('hits', [])

            # Remove duplicates based on 'LineId'
            results = {result['_source']['LineId']                       : result for result in results}.values()

    return render_template('chercher.html', results=results, query=query)


if __name__ == '__main__':
    app.run(debug=True)
