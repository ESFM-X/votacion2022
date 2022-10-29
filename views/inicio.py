# Paquetes instalados
from flask import (
    render_template, 
    request, 
    redirect, 
    make_response
) # Librería para hacer aplicaciones web
import requests # Librería para hacer solicitudes web
from bs4 import BeautifulSoup # Librería para hacer web scraping

# Paquetes locales
from secret import headers_kardex, headers_comprobante_reinscripcion
from utils import login_required
from data import getBoleta, createVoto, hasher


@login_required
def votar():
    """
    Función que recibe el voto y lo almacena
    """
    createVoto( # Función que se conecta a la base de datos y almacena lo siguiente:
        request.form.get('hash'), # Boleta hasehada
        request.form.get('respuesta') # La respuesta del usuario
        )
    return render_template('voto_enviado.html') # Envia el html de voto_enviado como respuesta

@login_required
def inicio():
    """
    Función que muestra la página una vez que el usuario se loguea
    """
    try:  
        # Se hace una solicitud al kardex del usuario para obtener únicamente su boleta y nombre
        session = requests.Session()
        session_id = request.cookies.get('session_id')
        ASPXFORMSAUTH = request.cookies.get('aspxformsauth')
        headers_kardex['Cookie'] = f'ASP.NET_SessionId={session_id}; .ASPXFORMSAUTH={ASPXFORMSAUTH};'
        response_kardex = session.get(
            'https://www.saes.esfm.ipn.mx/Alumnos/boleta/kardex.aspx',
            headers=headers_kardex
        )
        kardex = BeautifulSoup(response_kardex.text, features="html.parser")
        datos = kardex.find(attrs={'id':'ctl00_mainCopy_Lbl_Nombre'}).find_all('td')
        boleta = datos[1].text.replace(' ', '') # La boleta se hashea y se almacena al momento de votar
        nombre = datos[3].text # El nombre solo se utiliza para mostrarlo en la página, nunca se almacena
        boleta_hashed = hasher(boleta) # Se hashea la boleta

        # Si ya existe un voto con esa boleta, se carga el html voto_enviado
        if getBoleta(boleta_hashed):
            return render_template('voto_enviado.html')

        # Si no existe un voto con esa boleta se verifica que se tenga un comprobante de inscripción
        headers_comprobante_reinscripcion['Cookie'] = f'ASP.NET_SessionId={session_id}; .ASPXFORMSAUTH={ASPXFORMSAUTH};'
        response_comprobante_reinscripcion = session.get(
            'https://www.saes.esfm.ipn.mx/Alumnos/Reinscripciones/Comprobante_Horario.aspx',
            headers=headers_comprobante_reinscripcion
        )
        soup_comprobante_horario = BeautifulSoup(response_comprobante_reinscripcion.text, features="html.parser")
        tabla = soup_comprobante_horario.find(attrs={'id':'ctl00_mainCopy_PnlDatos'})

        if tabla: # Si existe el comprobante de reinscripción, se carga la página para votar
            m_response = make_response(
            render_template(
                'index.html', 
                nombre=nombre.split()[0],
                hash=boleta_hashed
            )
        )
        else: # Si no existe el comprobante de inscripción, se manda una página con mensaje de error
             m_response = make_response(
            render_template(
                'index.html', 
                error=True
            )
        )

    except Exception as e: # Si hubo cualquier error durante el procedimiento anterior
        print('*'*50, 'ERROR:', e) # Se imprime en consola y se manda un mensaje de error
        m_response = make_response(
            render_template(
                'index.html', 
                error=True
            )
        )

    return m_response 