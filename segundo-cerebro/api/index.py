from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/api/finanzas')
def obtener_finanzas():
    # Pega aquí la URL secreta que te dio Google Apps Script
    url_google = "https://script.google.com/macros/s/AKfycbxz2IrhnJ42YJyPrZ6UuruWDVIYXKrbY_Wvv0ta45VOxApeXtHV3lscEfcZMgyQeZ1O/exec"
    
    # Python le pide los datos a tu Excel
    respuesta = requests.get(url_google)
    datos_brutos = respuesta.json()
    
    # Aquí en el futuro podrás filtrar, sumar o agrupar los datos
    # Por ahora, simplemente se los pasamos limpios al frontend
    return jsonify({"datos": datos_brutos})

# Esto es necesario para que Vercel ejecute la app
if __name__ == '__main__':
    app.run()