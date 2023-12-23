import requests
import http.cookiejar
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import urllib.request
import re
import tkinter as tk
from tkinter import simpledialog
import time
import subprocess
import os
from bs4 import BeautifulSoup
from tkinterdnd2 import TkinterDnD
from mutagen.mp3 import MP3
from tkinter import messagebox
from tqdm import tqdm

def download_mp3(url, filename):
    # Descarga el archivo con una barra de progreso
    with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1, desc=f"Descargando {filename}") as t:
        urllib.request.urlretrieve(url, filename, reporthook=lambda blocks, block_size, total_size: t.update(block_size))

def extract_mix_number(tag):
    try:
        mix_text = tag.find('h3', class_='tm-audio-title').text
        mix_number = mix_text.split('Mix')[-1].strip()
        return mix_number
    except AttributeError:
        return None

def extract_folder_name(title_tag):
    try:
        folder_name = title_tag.text.strip().split('"')[1]
        return folder_name
    except (AttributeError, IndexError):
        return None

def load_file():
    code_file_path = "temp.txt"
    try:
        with open(code_file_path, 'r', encoding='utf-8') as code_file:
            code = code_file.read().strip()
            return code
    except FileNotFoundError:
        return None

def check_folder_exists(folder_path):
    return os.path.exists(folder_path)

def ask_overwrite_confirmation(folder_path):
    message = f"La carpeta '{folder_path}' ya existe. ¿Quieres sobreescribir los archivos mp3?"
    user_response = messagebox.askyesno("Confirmar Sobrescritura", message)
    return user_response

def clear_code_file():
    code_file_path = "temp.txt"
    open(code_file_path, 'w').close()

def main():
    print("Intentando cargar el código desde 'temp.txt'...")
    code = load_file()

    if not code:
        print("No se encontró el código en 'temp.txt'.")
        return
    else:
        texto = code

    try:
        soup = BeautifulSoup(texto, 'html.parser')
        mix_items = soup.find_all('div', class_='tm-audio-item')
        title_tag = soup.find('title')

        folder_name = extract_folder_name(title_tag)

        if not folder_name:
            print("No se pudo extraer el nombre de la carpeta desde la etiqueta <title>.")
            return

        folder_path = os.path.join(os.getcwd(), folder_name)

        if check_folder_exists(folder_path):
            if not ask_overwrite_confirmation(folder_path):
                print("Operación cancelada por el usuario.")
                return

        os.makedirs(folder_path, exist_ok=True)

        for item in mix_items:
            mix_link = item.find('a', href=True)
            mix_number = extract_mix_number(item)

            if mix_link and mix_number:
                filename = os.path.join(folder_path, f"Mix {mix_number}.mp3")
                download_mp3(mix_link['href'], filename)

                mp3 = MP3(filename)
                mp3.delete()
                mp3.save()

                print(f"Descargado y metadatos eliminados: {filename}")
            else:
                print("No se encontraron etiquetas Mix válidas en el enlace.")

        upload_text = "You've uploaded a file:"
        upload_tag = soup.find('p', string=lambda text: text and upload_text in text)

        if upload_tag:
            next_audio_tag = upload_tag.find_next('audio')

            if next_audio_tag:
                try:
                    mp3_link = next_audio_tag.find_next('source')['src']
                    download_mp3(mp3_link, os.path.join(folder_path, "My Mix.mp3"))

                    mp3 = MP3(os.path.join(folder_path, "My Mix.mp3"))
                    mp3.delete()
                    mp3.save()

                    print("Descargado y metadatos eliminados: My Mix.mp3")
                except (AttributeError, KeyError):
                    print("No se pudo encontrar el enlace mp3 para 'You've uploaded a file:'")

        print(f"Los archivos se han guardado en la carpeta: {folder_path}")

        clear_code_file()
        print("El archivo 'temp.txt' ha sido borrado.")

    except FileNotFoundError:
        print("Error: Archivo no encontrado.")


#####################################################

# URL del sitio y página de login
url = "https://tourna-mix.com/wp-login.php"

# Solicitar usuario y contraseña mediante cuadros de diálogo
usuario = simpledialog.askstring("Input", "Ingresa tu usuario:")
clave = simpledialog.askstring("Input", "Ingresa tu clave:", show='*')

# Crear un objeto CookieJar para manejar cookies
cookie_jar = http.cookiejar.CookieJar()

# Crear un objeto opener con manejo de cookies
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Abrir la página de login para obtener cookies
opener.open(url)

# Datos del formulario
datos_formulario = {
    'log': usuario,
    'pwd': clave,
    'wp-submit': 'Log In',
    'redirect_to': 'https://tourna-mix.com/my-account/members-area/260/my-membership-content/',
    'testcookie': '1'
}

# Realizar la solicitud POST para el login
respuesta = opener.open(url, data=urlencode(datos_formulario).encode('utf-8'))

# Crear un objeto BeautifulSoup para analizar el contenido de la página
soup = BeautifulSoup(respuesta.read(), 'html.parser')

# Verificar si el login fue exitoso mediante el contenido de la página
if "Tournaments" in soup.get_text():
    print("¡Login exitoso!")
else:
    print("Error en el login. Verifica las credenciales o el código.")

# Imprimir la URL después del login
print("URL después del login:", respuesta.geturl())

# Extraer información de los dos primeros elementos de la clase membership-content-title
elementos = soup.find_all('td', class_='membership-content-title')[:2]

# Crear una lista con los títulos de los elementos
titulos = [re.sub(r'[^a-zA-Z0-9\s]', '', enlace.get_text().replace('"', '')) for elemento in elementos for enlace in elemento.find_all('a')]

# Crear función para abrir la página correspondiente al elemento seleccionado
def abrir_pagina(elemento_index):
    if 0 <= elemento_index < len(elementos):
        # Eliminar cualquier carácter especial y formatear el título correctamente
        titulo_formateado = '-'.join(titulos[elemento_index].lower().split())
        url_elemento = f"https://tourna-mix.com/tournaments/{titulo_formateado}/"
        print(f"Abriendo la página: {url_elemento}")

        # Realizar la solicitud GET para obtener el source code de la página
        response = opener.open(url_elemento)
        source_code = response.read().decode('utf-8')

        # Guardar el source code en el archivo "temp.txt"
        with open("temp.txt", "w", encoding="utf-8") as source_file:
            source_file.write(source_code)

        print("Source code guardado en 'temp.txt'")

        # Verificar si hay enlaces a archivos MP3 en el source code
        mp3_links = re.findall(r'href=["\']([^"\']*\.mp3[^"\']*)["\']', source_code)

        if mp3_links:
            print("Enlaces a archivos MP3 encontrados.")
        else:
            print("No se encontraron enlaces a archivos MP3.")

        # Esperar 2 segundos antes de ejecutar downloader.py
        time.sleep(2)

        # Ejecutar downloader
        if __name__ == "__main__":
          main()

        root.destroy()  # Cerrar la ventana principal de Tkinter
    else:
        print("Índice no válido")

# Crear ventana principal de Tkinter
root = tk.Tk()

# Crear botones para cada título
botones = [tk.Button(root, text=titulo, command=lambda i=i: abrir_pagina(i)) for i, titulo in enumerate(titulos)]

# Mostrar los botones
for boton in botones:
    boton.pack(pady=5)

# Mantener la ventana abierta
root.mainloop()
