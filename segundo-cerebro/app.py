from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz3hJ011Ckg6xniDC53BEe0yBm8PyXD4nZ0D6m077gT0bdWngJ8XEpa0_MxTrjMp4I1/exec"
# Esta ruta carga tu interfaz visual
@app.route('/')
def home():
    return render_template('main.html')

@app.route('/gastos')
def gastos():
    return render_template('gastos.html')

@app.route('/ingresos')
def ingresos():
    return render_template('index.html')


@app.route('/api/ingresos')
def obtener_ingresos():
    # Pasamos los parámetros como un diccionario
    params = {'hoja': 'ingresos'}
    respuesta = requests.get(GOOGLE_SCRIPT_URL, params=params)
    return jsonify(respuesta.json())

@app.route('/api/gastos')
def obtener_gastos():
    try:
        # Llamada a Google
        respuesta = requests.get(GOOGLE_SCRIPT_URL + "?hoja=gastos")
        datos_gastos = respuesta.json()
        gastos_limpios = []
        
        for fila in datos_gastos:
            # Comprobamos que tenga al menos 6 columnas y que no sea una fila vacía
            if len(fila) >= 6 and fila[0] != "":
                
                # --- AQUÍ ESTABA EL POSIBLE ERROR ---
                # Debemos calcular la cantidad ANTES de crear el diccionario 'gasto'
                cantidad_str = str(fila[1]).replace('€', '').replace(',', '').strip()
                try:
                    cantidad = float(cantidad_str)
                except ValueError:
                    cantidad = 0.0
                
                # Ahora sí, creamos el diccionario con la variable 'cantidad' ya definida
                gasto = {
                    "fecha": fila[0], 
                    "cantidad": cantidad, 
                    "categoria": fila[2],
                    "concepto": fila[4], 
                    "estado": fila[5]
                }
                gastos_limpios.append(gasto)

        # Devolvemos el objeto con la llave "gastos" que tu HTML espera
        return jsonify({"gastos": gastos_limpios})

    except Exception as e:
        # Si esto se ejecuta, es porque hubo un error en el código
        print(f"ERROR EN SERVIDOR: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
    
    
    
# Esta ruta trae los datos de Google Sheets
@app.route('/api/finanzas')
def obtener_finanzas():
    # Recuerda poner aquí tu URL secreta de Google Apps Script
    
    try:
        respuesta = requests.get(GOOGLE_SCRIPT_URL)
        datos_brutos = respuesta.json()
        
        ingresos_limpios = []
        
        # En programación, la fila 16 es el índice 15. 
        # Iteramos desde ahí hasta el final del Excel.
        for fila in datos_brutos[15:]:
            # Comprobamos que la fila tenga datos y la columna B (índice 1) no esté vacía
            if len(fila) >= 7 and fila[1] != "":
                
                # Limpiamos el texto de la cantidad para convertirlo a número decimal
                cantidad_str = str(fila[2]).replace('€', '').replace(',', '').strip()
                try:
                    cantidad = float(cantidad_str)
                except ValueError:
                    cantidad = 0.0

                ingreso = {
                    "fecha": fila[1],         # Columna B
                    "cantidad": cantidad,     # Columna C (ya como número)
                    "categoria": fila[3],     # Columna D
                    "concepto": fila[5],      # Columna F
                    "estado": fila[6]         # Columna G (✅ o 🅿️)
                }
                ingresos_limpios.append(ingreso)
                
                # --- DEBUG DE GASTOS ---
        respuesta_gastos = requests.get(GOOGLE_SCRIPT_URL + "?hoja=gastos")
        datos_gastos = respuesta_gastos.json()
        gastos_limpios = []
        
        # Quitamos el slicing [15:] y ajustamos el len() a 6
        for fila in datos_gastos:
            # Ahora pedimos que tenga al menos 6 columnas
            if len(fila) >= 6 and fila[0] != "":
                
                # La cantidad está en el índice 1 (según tu log)
                cantidad_str = str(fila[1]).replace('€', '').replace(',', '').strip()
                try:
                    cantidad = float(cantidad_str)
                except ValueError:
                    cantidad = 0.0
                
                gasto = {
                    "fecha": fila[0], 
                    "cantidad": cantidad, 
                    "categoria": fila[2],
                    "concepto": fila[4], 
                    "estado": fila[5]
                }
                gastos_limpios.append(gasto)

            return jsonify({"ingresos": ingresos_limpios, "gastos": gastos_limpios})
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # El debug=True es magia: actualiza la web al instante si cambias el código
    app.run(debug=True, port=5000)