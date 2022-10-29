# Paquetes instalados
from flask import (
    render_template, 
    request, 
    redirect, 
    make_response
) # Librería para hacer aplicaciones web
import requests # Librería para hacer solicitudes web
from bs4 import BeautifulSoup # Librería para hacer web scraping
from requests_ip_rotator import ApiGateway # Librería para conectarse a una GateWay de Amazon Web Services

# Paquetes locales
from secret import headers_login, form_data_login
from utils import (
    login_required, 
    not_login_required,
    setLoginCookies,
    loginRequestData
)
from aws_credentials import key_id, key_secret, api_url


url_base = 'https://www.saes.esfm.ipn.mx'

@not_login_required # Decorador para que solo los que no están logueados tengan acceso a esta ruta
def login():  
    """
    Función que realiza el login
    - Cuando el usuario ingresa por primera vez, hace una solicitud al SAES para obtener los inputs ocultos
      y el captcha. 
    - Cuando el usuario manda los datos de su logueo, manda otra solicitud enviando esos datos y comprueba 
      que el logueo se haya realizado con éxito.
    """
    if request.method == 'GET':  # Si el usuario ingresa por primera vez
        return render_template( 
            'login.html', # Carga el html login
            **loginRequestData() # Manda los inputs solicitados al SAES necesarios para loguearse
        )
    
    # Si el usuario manda datos de login
    data = request.form

    # Directamente se enlazan a los datos que se enviarán al SAES
    headers_login['Cookie'] = f'ASP.NET_SessionId={data["session_id"]};' # El id de Sesión
    
    # Inputs de login que necesita el SAES
    form_data_login['__VIEWSTATE'] =  data['VIEWSTATE']
    form_data_login['__VIEWSTATEGENERATOR'] = data['VIEWSTATEGENERATOR']
    form_data_login['__EVENTVALIDATION'] = data['EVENTVALIDATION']
    form_data_login['ctl00$leftColumn$LoginUser$UserName'] = data['username']
    form_data_login['ctl00$leftColumn$LoginUser$Password'] = data['password']
    form_data_login['ctl00$leftColumn$LoginUser$CaptchaCodeTextBox'] = data['captcha']
    form_data_login['LBD_VCID_c_default_ctl00_leftcolumn_loginuser_logincaptcha'] = data['LBD_VCID_c_default_ctl00_leftcolumn_loginuser_logincaptcha']
    

    # A partir de aqui se hace la conexión de Login con el SAES
    try:
        # Se crea la Gateway con AWS Api Gateway
        gateway = ApiGateway(
            api_url, 
            access_key_id=key_id, 
            access_key_secret=key_secret,
            # regions=ip_rotator.DEFAULT_REGIONS + EXTRA_REGIONS
        )
        gateway.start(force=True)
        
        session = requests.Session()
        session.mount(api_url, gateway)

        # Se manda la solicitud al SAES con los datos de login
        response_login = session.post(
            'https://www.saes.esfm.ipn.mx/default.aspx',    
            headers=headers_login,
            data=form_data_login,
        )
        # Se cierran las Gateway
        gateway.shutdown() 

        # El SAES manda un código de éxito aunque el logueo sea fállido (HTTP Status Code de 200)
        # Es por eso que verificamos mediante web scraping que el login sea éxitoso
        soup_login = BeautifulSoup(response_login.text, features="html.parser")
        nombre = soup_login.find(attrs={'id':'ctl00_mainCopy_FormView1_nombrelabel'})
        
        if nombre: # Si es posible obtener el nombre del alumno de la respuesta del SAES, entonces es un logueo éxitoso
            # Se guardan las cookies de inicio éxitoso en el navegador y se redirecciona a la ruta principal
            m_response = setLoginCookies(
                '/ ', 
                data["session_id"], 
                session.cookies.get('.ASPXFORMSAUTH'), 
                nombre.text)
        else: # Si el logueo no fue exitoso
            # Se carga de nuevo el html de login con los datos necesarios de logueo para el SAES
            m_response = make_response(render_template('login.html', 
                error='Usuario, contraseña o captcha inválidos',
                **loginRequestData()
                ))
        return m_response
    except Exception as e: # Si hubo cualquier error 
        print('*'*50, e) # Se imprime en la consola del servidor
        return render_template("generic_error.html") # Se carga el html de error genérico


@login_required
def logout():
    """
    Función que borra las cookies del navegador y te redirecciona a la ruta para 
    hacer login. (Es básicamente cerrar sesión)
    """
    response = make_response(redirect('/login'))
    response.set_cookie('session_id', '', expires=0)
    response.set_cookie('aspxformsauth', '', expires=0)
    
    return response