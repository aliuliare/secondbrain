from flask import Flask, jsonify, render_template
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby2W2Bqu74h3lWLcejhtuqVA8f0sAhB85sviCNjvHrViwjvAAmSGgu6cTle7psWJzYv/exec"
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

@app.route('/ahorros')
def ahorros():
    return render_template('ahorros.html')

@app.route('/inversiones')
def inversiones():
    return render_template('inversiones.html')

@app.route('/api/inversiones')
def obtener_inversiones():
    try:
        params = {'hoja': 'inversiones'}
        respuesta = requests.get(GOOGLE_SCRIPT_URL, params=params)
        datos_brutos = respuesta.json()

        inversiones = []
        total_invertido_global = 0
        total_actual_global = 0

        # --- LÓGICA DE FECHAS (REAL) ---
        año_inicio = 2026 # ¡Año correcto!
        mes_inicio = 6
        dia_inicio = 2
        hoy = datetime.now()

        fechas_inversion = []
        año_act, mes_act = año_inicio, mes_inicio
        while True:
            fecha = datetime(año_act, mes_act, dia_inicio)
            if fecha > hoy:
                break
            fechas_inversion.append(fecha)
            mes_act += 1
            if mes_act > 12:
                mes_act = 1
                año_act += 1
        
        print(f"\n--- Calculando compras reales desde el {dia_inicio}/{mes_inicio}/{año_inicio} ---")

        for fila in datos_brutos:
            if len(fila) < 5 or not fila[0] or not fila[2]:
                continue
                
            nombre = fila[0]
            ticker_sym = str(fila[2]).strip()
            
            raw_str = str(fila[4]).replace('€', '').strip()
            raw_str = raw_str.replace(',', '.')
            try:
                cantidad_mensual = float(raw_str)
            except ValueError:
                continue

            if cantidad_mensual <= 0:
                continue

            # Descargamos el histórico
            fondo = yf.Ticker(ticker_sym)
            
            # Pedimos histórico desde el año anterior para asegurar que el DataFrame nunca esté vacío
            fecha_str_inicio = f"{hoy.year - 1}-01-01" 
            hist = fondo.history(start=fecha_str_inicio)

            if hist.empty:
                print(f"⚠️ Yahoo Finance no encontró: {ticker_sym}. Verifica el ticker.")
                
            if hasattr(hist.index, 'tz') and hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)

            acciones_totales = 0
            dinero_invertido = 0

            # Si hoy es anterior a junio de 2026, la lista 'fechas_inversion' está vacía 
            # y este bucle simplemente no se ejecuta, dejando todo a cero (como debe ser).
            for fecha_inv in fechas_inversion:
                fechas_disponibles = hist.index[hist.index >= fecha_inv]
                if len(fechas_disponibles) > 0:
                    fecha_compra = fechas_disponibles[0]
                    precio_compra = hist.loc[fecha_compra]['Close']
                    
                    acciones_totales += cantidad_mensual / precio_compra
                    dinero_invertido += cantidad_mensual

            # Aunque el invertido sea 0, calculamos el precio actual 
            precio_actual = 0
            if not hist.empty:
                try:
                    precio_actual = hist['Close'].iloc[-1]
                except IndexError:
                    pass

            valor_actual = acciones_totales * precio_actual
            beneficio = valor_actual - dinero_invertido
            porcentaje_beneficio = (beneficio / dinero_invertido * 100) if dinero_invertido > 0 else 0

            total_invertido_global += dinero_invertido
            total_actual_global += valor_actual

            print(f"✅ {ticker_sym}: {dinero_invertido}€ invertidos.")

            # Añadimos el fondo SIEMPRE, aunque tenga 0€, para verlo en el HTML
            inversiones.append({
                "nombre": nombre,
                "ticker": ticker_sym,
                "invertido": dinero_invertido,
                "valor_actual": valor_actual,
                "beneficio": beneficio,
                "porcentaje": porcentaje_beneficio
            })

        print(f"--- Fin de cálculos. Invertido global: {total_invertido_global:.2f}€ ---\n")

        return jsonify({
            "inversiones": inversiones,
            "total_invertido": total_invertido_global,
            "total_actual": total_actual_global,
            "beneficio_global": total_actual_global - total_invertido_global,
            "porcentaje_global": ((total_actual_global - total_invertido_global) / total_invertido_global * 100) if total_invertido_global > 0 else 0
        })

    except Exception as e:
        print(f"Error grave en API Inversiones: {e}")
        return jsonify({"error": str(e)}), 500


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
    
    
@app.route('/api/ahorros')
def obtener_ahorros():
    params = {'hoja': 'ahorros'}
    respuesta = requests.get(GOOGLE_SCRIPT_URL, params=params)
    datos = respuesta.json()
    
    # Formateamos para el frontend
    ahorros_limpios = []
    for fila in datos:
        # fila[0]=Categoria, fila[1]=Ahorrado, fila[2]=TotalMeta
        ahorros_limpios.append({
            "categoria": fila[0],
            "ahorrado": float(fila[1]) if fila[1] else 0.0,
            "meta": float(fila[2]) if fila[2] else 0.0
        })
    return jsonify({"ahorros": ahorros_limpios})
    
    
# Esta ruta trae los datos de Google Sheets
# Esta ruta trae los datos de Google Sheets
@app.route('/api/finanzas')
def obtener_finanzas():
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

        # ¡CORREGIDO! El return ahora está completamente fuera de los bucles for
        return jsonify({"ingresos": ingresos_limpios, "gastos": gastos_limpios})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # El debug=True es magia: actualiza la web al instante si cambias el código
    app.run(debug=True, port=5000)