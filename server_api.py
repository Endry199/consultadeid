from flask import Flask, request, jsonify
from flask_cors import CORS 
from selenium import webdriver
# NECESITAS ESTA IMPORTACIÓN PARA ESPECIFICAR EL PATH EN EL SERVIDOR
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# =================================================================
# FUNCIÓN DE SCRAPING MODIFICADA PARA USO EN API
# =================================================================
def obtener_apodo_freefire_ui(user_id: str) -> str:
    """
    Simula la interacción de un usuario en la página web para obtener
    el apodo de Free Fire. Devuelve solo el apodo o un código de error.
    """
    url_pagina = "https://mobentas.com/product/free-fire/"
    
    # 1. Configuración del Navegador (Modo Headless)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # AÑADIDO: Ruta al binario de Chromium en el entorno Docker/Render
    options.binary_location = '/usr/bin/chromium' 
    
    try:
        # AÑADIDO: Especifica el Service con la ruta del ChromeDriver en el entorno Docker/Render
        service = Service(executable_path='/usr/bin/chromedriver') 
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        # Devuelve un código de error específico para el servidor
        return f"DRIVER_ERROR: {e}" 

    try:
        driver.get(url_pagina)
        print(f"-> Abriendo la página: {url_pagina}")
        
        wait = WebDriverWait(driver, 15)

        # 2. Localizar y Aceptar el Aviso de Cookies (Manejo robusto)
        try:
            cookie_button = wait.until(
                EC.element_to_be_clickable((By.ID, "cn-accept-cookie"))
            )
            # Usar JavaScript para hacer click
            driver.execute_script("arguments[0].click();", cookie_button)
            print("-> Aviso de cookies aceptado mediante JS Click.")
            time.sleep(1) 
            
        except TimeoutException:
            print("-> No se detectó o no fue necesario aceptar el aviso de cookies.")
        except Exception as e:
            print(f"-> Error al intentar hacer click en las cookies (continuando): {e}")


        # 3. Localizar el Campo de ID y el Botón
        id_input = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "server_user_id"))
        )
        submit_button = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "custom_field_submit"))
        )

        # 4. Ingresar la ID y Hacer clic
        id_input.clear()
        id_input.send_keys(user_id)
        
        # Usar JavaScript para hacer click en el botón "Ingresar"
        driver.execute_script("arguments[0].click();", submit_button)
        print(f"-> ID '{user_id}' ingresada y botón 'Ingresar' presionado usando JS.")
        
        # 5. Esperar la Aparición del Apodo
        apodo_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".response_message_api .name"))
        )

        # 6. Extraer el Apodo
        nickname = apodo_element.text.strip()

        if nickname:
            # DEVUELVE SÓLO EL APODO (CADENA DE TEXTO LIMPIA)
            return nickname
        else:
            return "ID_INCORRECTA"

    except TimeoutException:
        try:
            # Verificar si existe un mensaje de ID incorrecta en la página
            error_msg = driver.find_element(By.CSS_SELECTOR, ".response_message_api_not_found .inner_span_api").text
            if "ID no encontrada" in error_msg or "ID incorrecta" in error_msg:
                 return "ID_INCORRECTA"
            else:
                 return "TIMEOUT_ERROR"
        except NoSuchElementException:
             return "TIMEOUT_ERROR"
             
    except Exception as e:
        return f"GENERIC_ERROR: {e}"
        
    finally:
        # 7. Asegúrate de cerrar el navegador
        if 'driver' in locals():
            driver.quit()

# =================================================================
# CONFIGURACIÓN DEL SERVIDOR FLASK
# =================================================================

app = Flask(__name__)
CORS(app) 

# Definición de la ruta API a la que llamará el navegador
@app.route('/verify-id', methods=['GET'])
def verify_id():
    user_id = request.args.get('id')
    
    if not user_id:
        return jsonify({"success": False, "nickname": None, "message": "Falta la ID del usuario."}), 400

    print(f"RECIBIDA PETICIÓN para verificar ID: {user_id}")
    
    result = obtener_apodo_freefire_ui(user_id)
    
    # Manejo de respuestas basadas en los códigos de retorno de la función
    if result.startswith("ERROR") or result == "ID_INCORRECTA" or result == "TIMEOUT_ERROR":
        
        if result == "ID_INCORRECTA":
             msg = "La ID de Free Fire proporcionada no es válida."
        elif "DRIVER_ERROR" in result:
             msg = "Error interno del servidor al iniciar el bot (Driver/Chrome)."
        else:
             msg = "Ocurrió un error desconocido. Intenta de nuevo más tarde."
             
        return jsonify({
            "success": False, 
            "nickname": None, 
            "message": msg
        }), 500
        
    else:
        # Éxito: el resultado es el nickname
        return jsonify({
            "success": True,
            "nickname": result, 
            "message": "Apodo verificado."
        })

# ELIMINAMOS la sección if __name__ == '__main__':