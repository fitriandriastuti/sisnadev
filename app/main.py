
from fastapi import FastAPI, Depends, HTTPException, Request, status, Form, Body
import uvicorn
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from app import models, database
from app.database import SessionLocal, Session, Close

from fastapi import Security
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from starlette.status import HTTP_403_FORBIDDEN

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware

from starlette.config import Config
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.responses import RedirectResponse, JSONResponse

from os import environ
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta

import pymongo

import socket
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

GOOGLE_CLIENT_ID = environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_ID = environ['GOOGLE_CLIENT_SECRET']
apikeyapp = environ['APIKEYAPP']

tags_metadata = [
    {
        "name": "Similarity Services",
        "description": "API Information of Machine Learning/ Deep Learning",
        "externalDocs": {
            "description": "Domain",
            "url": "https://sisnadev.fitrengineer.com/",
        },
    },
]

app = FastAPI(
    title="API SISNA",
    description="Application Programming Interface (API) SISNA - Sistem Standarisasi Nomenklatur APBD",
    version="0.0.1",
    openapi_tags=tags_metadata,
)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

#add middleware to connect dash/flask server
from fastapi.middleware.wsgi import WSGIMiddleware

def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        Close

API_KEY = "1234567asdfgh"
API_KEY_NAME = "access_token"
COOKIE_DOMAIN = "localtest.me"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_query: str = Security(api_key_query), api_key_header: str = Security(api_key_header), api_key_cookie: str = Security(api_key_cookie)):
    if api_key_query == apikeyapp : return api_key_query
    elif api_key_header == apikeyapp: return api_key_header
    elif api_key_cookie == apikeyapp: return api_key_cookie
    else: raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")

proxy_ip = socket.gethostbyname("")
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=proxy_ip)

app.add_middleware(SessionMiddleware, secret_key="secret-string")

config = Config('.env')
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get("/", include_in_schema=False)
async def homepage(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
    else:
        data = {}
    return templates.TemplateResponse("home.html", {"request": request, "data": data})

@app.get('/signin', include_in_schema=False)
async def signin(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user is not None:
        data = await db["user"].find_one({"email": user['email']})
    else:
        data = {}
    return templates.TemplateResponse("signin.html", {"request": request, "data": data})

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth', include_in_schema=False)
async def auth(request: Request, db = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    data = request.session['user']
    email = data['email']
    try:
        if (user := await db["user"].find_one({"email": email})) is None:
            return RedirectResponse(url='/createuser')

    except Exception as e:
        print(e)

    return RedirectResponse(url='/')

@app.route('/signup')
async def signup(request: Request):
    redirect_uri = request.url_for('authorize')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/authorize')
async def authorize(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    print(token)
    print(user)
    return RedirectResponse(url='/createuser')

@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.route('/createuser')
async def createuser(request: Request):
    user = request.session['user']
    email = {}
    if len(user)>0: email = user['email']
    response = {}
    return templates.TemplateResponse("signup.html", {"request": request, "data": user, "response": response})

@app.post('/adduser/', include_in_schema=False)
async def adduser(request: Request, db = Depends(get_db), email: str = Form(...), name: str = Form(...), photo: str = Form(...)):
    response = {}
    try:
        if (user_ := await db["user"].find_one({"email": email})) is None:
            print(user_)
            current_time = datetime.utcnow() + timedelta(hours=7)
            userId = int(current_time.strftime('%Y%m%d%H%M')[2:12])
            disabled = 0
            data = {
                "userId": userId,
                "email": email,
                "name": name,
                "photo": photo,
                "disabled": 0,
            }
            new_user = await db["user"].insert_one(data)
            response = {
                'status': 'success',
                'message': 'Berhasil menambahkan user',
            }
        else:
            response = {
                'status': 'error',
                'message': 'Gagal menambahkan user. Email sudah ada didatabase.',
            }
    except Exception as e:
        print(e)

    data = {
        'email': email,
        'name': name,
        'photo': photo,
    }
    return templates.TemplateResponse("signup.html", {"request": request, "data": data, "response": response})

@app.get('/about', include_in_schema=False)
async def about(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user is not None:
        data = await db["user"].find_one({"email": user['email']})
    else:
        data = {}
    return templates.TemplateResponse("about.html", {"request": request, "data": data})

@app.get('/dashboardall', include_in_schema=False)
async def dashboardall(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import dashdashboardall
        dash_app_dashboard = dashdashboardall(
            requests_pathname_prefix="/dashdashboard/")
        app.mount("/dashdashboard", WSGIMiddleware(dash_app_dashboard.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_dashboard.index(), 'html.parser')
        querydata = soup.footer
    else:
        data = {}
    return templates.TemplateResponse("dashboard.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/similarityscore', include_in_schema=False)
async def similarityscore(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import similarityscore
        dash_app_similarityscore = similarityscore(
            requests_pathname_prefix="/dashsimilarityscore/")
        app.mount("/dashsimilarityscore", WSGIMiddleware(dash_app_similarityscore.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_similarityscore.index(), 'html.parser')
        querydata = soup.footer
    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/standardizationakun', include_in_schema=False)
async def standardizationakun(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import standardization_akun_datatable
        dash_app_standardization_datatable = standardization_akun_datatable(
            requests_pathname_prefix="/dashstandardizationakun/")
        app.mount("/dashstandardizationakun", WSGIMiddleware(dash_app_standardization_datatable.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_standardization_datatable.index(), 'html.parser')
        querydata = soup.footer
    else:
        data = {}
    return templates.TemplateResponse("standardization/standardizationkegiatan.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/standardizationkegiatan', include_in_schema=False)
async def standardizationkegiatan(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import standardization_kegiatan_datatable
        dash_app_standardization_datatable = standardization_kegiatan_datatable(
            requests_pathname_prefix="/dashstandardizationkegiatan/")
        app.mount("/dashstandardizationkegiatan", WSGIMiddleware(dash_app_standardization_datatable.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_standardization_datatable.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("standardization/standardizationkegiatan.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/apemdafungsianggaran', include_in_schema=False)
async def apemdafungsianggaran(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import apemdafungsianggaran
        dash_app_apemdafungsianggaran = apemdafungsianggaran(
            requests_pathname_prefix="/dashapemdafungsianggaran/")
        app.mount("/dashapemdafungsianggaran", WSGIMiddleware(dash_app_apemdafungsianggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_apemdafungsianggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/apemdafungsibelanja', include_in_schema=False)
async def apemdafungsibelanja(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import apemdafungsibelanja
        dash_app_apemdafungsibelanja = apemdafungsibelanja(
            requests_pathname_prefix="/dashapemdafungsibelanja/")
        app.mount("/dashapemdafungsibelanja", WSGIMiddleware(dash_app_apemdafungsibelanja.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_apemdafungsibelanja.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/aakunanggaran', include_in_schema=False)
async def aakunanggaran(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import aakunanggaran
        dash_app_aakunanggaran = aakunanggaran(
            requests_pathname_prefix="/dashaakunanggaran/")
        app.mount("/dashaakunanggaran", WSGIMiddleware(dash_app_aakunanggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_aakunanggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/asubkegiatananggaran', include_in_schema=False)
async def asubkegiatananggaran(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import asubkegiatananggaran
        dash_app_asubkegiatananggaran = asubkegiatananggaran(
            requests_pathname_prefix="/dashasubkegiatananggaran/")
        app.mount("/dashasubkegiatananggaran", WSGIMiddleware(dash_app_asubkegiatananggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_asubkegiatananggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/preprocessing', include_in_schema=False)
async def preprocessing(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import apemdafungsianggaran
        dash_app_apemdafungsianggaran = apemdafungsianggaran(
            requests_pathname_prefix="/dashapemdafungsianggaran/")
        app.mount("/dashapemdafungsianggaran", WSGIMiddleware(dash_app_apemdafungsianggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_apemdafungsianggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/similarityscore', include_in_schema=False)
async def similarityscore(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import apemdafungsianggaran
        dash_app_apemdafungsianggaran = apemdafungsianggaran(
            requests_pathname_prefix="/dashapemdafungsianggaran/")
        app.mount("/dashapemdafungsianggaran", WSGIMiddleware(dash_app_apemdafungsianggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_apemdafungsianggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.get('/classification', include_in_schema=False)
async def classification(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    querydata = {}
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
        from app.dashapp import apemdafungsianggaran
        dash_app_apemdafungsianggaran = apemdafungsianggaran(
            requests_pathname_prefix="/dashapemdafungsianggaran/")
        app.mount("/dashapemdafungsianggaran", WSGIMiddleware(dash_app_apemdafungsianggaran.server))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(dash_app_apemdafungsianggaran.index(), 'html.parser')
        querydata = soup.footer

    else:
        data = {}
    return templates.TemplateResponse("visualization.html", {"request": request, "data": data, "querydata":querydata})

@app.exception_handler(404)
async def custom_404_handler(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    print(user['email'])
    if user is not None:
        data = {
            "name": user['name'],
            "email": user['email'],
            "photo": user['picture'],
        }
    else:
        data = {}
    return templates.TemplateResponse("error404.html", {"request": request, "data": data})

@app.get("/similaritysiap/", tags=["Similarity Services"], include_in_schema=False)
async def get_similaritysiap(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    import re
    skip = 0
    limit = 1000
    maximal = 5300
    a = 0
    while a < maximal:
        skip = a * limit
        a += 1
        print(skip)

        m_akun = await db['m_akun'].find(
            {
                'kode_akun': {'$exists': 'true'},
                '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]},
            },
        ).sort("_id", pymongo.ASCENDING).to_list(11000)

        data_A2022 = await db['A2022'].find(
            {
                # 'namaakunsubrinci': 'Retribusi Pelayanan Persampahan/Kebersihan',
            },
        ).sort("_id", pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)

        akun = []
        for base in m_akun:
            akun.append(base['nama_akun'].strip())

        for data in data_A2022:
            data_namaakunsubrinci = (data.get('namaakunsubrinci', '')).rstrip().lstrip()
            namaakunsubrinci = re.sub(r'(?:(?<=\/) | (?=\/))','',data_namaakunsubrinci)
            print(data_namaakunsubrinci, ' => ', namaakunsubrinci, ' - pepo')
            list_notinclude = ['DID', 'Pajak Tras', 'PBBP2', 'Dana Desa', 'DAU', 'Rek Lvl6']
            if len(namaakunsubrinci) > 0 and data_namaakunsubrinci != 'Rek Lvl6' :
                cek_akun = await db['m_akun'].find_one({'nama_akun': namaakunsubrinci,'$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                if cek_akun is None:
                    akun = await db['m_akun'].find(
                        {'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},
                        {'score': {'$meta': "textScore"}}).sort([('score', {'$meta': 'textScore'})]).limit(1).to_list(1)
                    nama_akun = akun[0]['nama_akun']
                    kode_akun = akun[0]['kode_akun']

                    max_val_w2v = 1
                    idx = None

                    if akun is None and len(namaakunsubrinci) > 10:
                        from app import similarity
                        dataapbd_cek = namaakunsubrinci
                        w2v = similarity.word2vecpepo(dataapbd_cek, akun)
                        print(w2v)
                        if 1 in w2v:
                            max_val_w2v = 1
                        else:
                            max_val_w2v = max(w2v)
                        idx_max = w2v.index(max_val_w2v)
                        idx = idx_max
                        print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx],' - Data APBD Awalnya: ', namaakunsubrinci)
                        q_akun = await db['m_akun'].find_one({'nama_akun': akun[idx], '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                        nama_akun = akun[idx]
                        kode_akun = q_akun['kode_akun']
                    score_similarity = {
                        'score_similarity': max_val_w2v,
                        'idx_similarity': idx,
                        'nama_akun': nama_akun,
                        'kode_akun': kode_akun,
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_similarity_w2v"].insert_one(data)
                else:
                    nama_akun = cek_akun['nama_akun']
                    kode_akun = cek_akun['kode_akun']
                    print('cek pepo akun: ', namaakunsubrinci, ' - ',cek_akun)

                    score_similarity = {
                        'score_similarity': 1,
                        'idx_similarity': None,
                        # 'nama_akun': namaakunsubrinci,
                        'nama_akun': nama_akun,
                        'kode_akun': kode_akun,
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_similarity_w2v"].insert_one(data)
                print(cek_akun)
            else:
                nama_akun = namaakunsubrinci
                kode_akun = None
                if len (namaakunsubrinci)>0:
                    namaakunrinci = data.get('namaakunrinci', '')
                    cek_akun = await db['m_akun'].find_one({'nama_akun': namaakunrinci, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 12]}})
                    new_kode_akun = cek_akun['kode_akun'] + '.0001'
                    print('namaakunrinci',namaakunrinci, cek_akun)
                    kode_akun = new_kode_akun
                score_similarity = {
                    'score_similarity': None,
                    'idx_similarity': None,
                    'nama_akun': namaakunsubrinci,
                    'kode_akun': kode_akun,
                }
                insert_result_similarity = data.update(score_similarity)
                new_user = db["m_similarity_w2v"].insert_one(data)

    return {'status': 'berhasil run. cek database'}

@app.get("/similaritysubkegiatan/", tags=["Similarity Services"], include_in_schema=False)
async def get_similarity_subkegiatan(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    import re
    skip = 0
    limit = 1000
    maximal = 5300
    a = 0
    while a < maximal:
        skip = a * limit
        a += 1
        print(skip)

        m_subkegiatan = await db['m_subkegiatan'].find(
            {
                'kodestdsubkegiatan': {'$exists': 'true'},
                '$expr': {'$gte': [{'$strLenCP': '$kodestdsubkegiatan'}, 22]},
            },
        ).sort("_id", pymongo.ASCENDING).to_list(7000)

        data_A2022 = await db['m_similarity_w2v'].find(
            {
            },
        ).sort("_id", pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)

        for data in data_A2022:
            kewenangan_ = data.get('kodepemda', '')
            kewenangan = '1'
            if kewenangan_[-2:] == '00':
                kewenangan = '1'
            else:
                kewenangan = '2'
            data_namasubkegiatan = (data.get('namasubkegiatan', '')).rstrip().lstrip()
            namasubkegiatan = re.sub(r'(?:(?<=\/) | (?=\/))','',data_namasubkegiatan)
            print(data_namasubkegiatan, ' => ', namasubkegiatan, ' - pepo')

            try:
                if len(namasubkegiatan) > 0 and data_namasubkegiatan != 'Non Sub Kegiatan' and data_namasubkegiatan != 'Pelaksanaa':
                    cek_subkegiatan = await db['m_subkegiatan'].find_one(
                        {'namasubkegiatan': namasubkegiatan, 'KEWENANGAN': kewenangan,
                         '$expr': {'$gte': [{'$strLenCP': '$kodestdsubkegiatan'}, 22]}})

                    if cek_subkegiatan is None:
                        subkegiatan = {}
                        subkegiatan = await db['m_subkegiatan'].find(
                            {'$text': {'$search': namasubkegiatan},
                             '$expr': {'$gte': [{'$strLenCP': '$kodestdsubkegiatan'}, 22]}},
                            {'score': {'$meta': "textScore"}}).sort([('score', {'$meta': 'textScore'})]).limit(
                            1).to_list(1)

                        print(subkegiatan)

                        namasubkegiatan = subkegiatan[0].get('namasubkegiatan', '')
                        kodestdsubkegiatan = subkegiatan[0].get('kodestdsubkegiatan', '')
                        score_similarity_subkegiatan = subkegiatan[0].get('score', '')

                        max_val_w2v = 1
                        idx = None

                        if subkegiatan is None and len(namasubkegiatan) > 10:
                            from app import similarity
                            dataapbd_cek = namasubkegiatan
                            w2v = similarity.word2vecpepo(dataapbd_cek, subkegiatan)
                            print(w2v)
                            if 1 in w2v:
                                max_val_w2v = 1
                            else:
                                max_val_w2v = max(w2v)
                            idx_max = w2v.index(max_val_w2v)
                            idx = idx_max
                            print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk subkegiatan: ', subkegiatan[idx],' - Data APBD Awalnya: ', namasubkegiatan)
                            q_subkegiatan = await db['m_subkegiatan'].find_one({'namasubkegiatan': subkegiatan[idx], 'KEWENANGAN': kewenangan, '$expr': {'$gte': [{'$strLenCP': '$kodestdsubkegiatan'}, 22]}})
                            namasubkegiatan = subkegiatan[idx]
                            kodestdsubkegiatan = q_subkegiatan['kodestdsubkegiatan']
                            score_similarity_subkegiatan = max_val_w2v
                        score_similarity = {
                            'score_similarity_subkegiatan': score_similarity_subkegiatan,
                            'idx_similarity_subkegiatan': idx,
                            'namasubkegiatan_similarity': namasubkegiatan,
                            'kodestdsubkegiatan_similarity': kodestdsubkegiatan,
                        }
                        insert_result_similarity = data.update(score_similarity)
                        new_user = db["m_similarity_all"].insert_one(data)
                    else:
                        namasubkegiatan = cek_subkegiatan['namasubkegiatan']
                        kodestdsubkegiatan = cek_subkegiatan['kodestdsubkegiatan']
                        print('cek pepo subkegiatan: ', namasubkegiatan, ' - ', cek_subkegiatan)

                        score_similarity = {
                            'score_similarity_subkegiatan': 1,
                            'idx_similarity_subkegiatan': None,
                            # 'namasubkegiatan': namasubkegiatan,
                            'namasubkegiatan_similarity': namasubkegiatan,
                            'kodestdsubkegiatan_similarity': kodestdsubkegiatan,
                        }
                        insert_result_similarity = data.update(score_similarity)
                        new_user = db["m_similarity_all"].insert_one(data)
                    print(cek_subkegiatan)
                else:
                    namasubkegiatan = namasubkegiatan
                    kodestdsubkegiatan = None
                    score_similarity = {
                        'score_similarity_subkegiatan': None,
                        'idx_similarity_subkegiatan': None,
                        'namasubkegiatan_similarity': namasubkegiatan,
                        'kodestdsubkegiatan_similarity': kodestdsubkegiatan,
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_similarity_all"].insert_one(data)
            except:
                namasubkegiatan = None
                kodestdsubkegiatan = None
                score_similarity = {
                    'score_similarity_subkegiatan': None,
                    'idx_similarity_subkegiatan': None,
                    'namasubkegiatan_similarity': namasubkegiatan,
                    'kodestdsubkegiatan_similarity': kodestdsubkegiatan,
                }
                insert_result_similarity = data.update(score_similarity)
                new_user = db["m_similarity_all"].insert_one(data)

    return {'status': 'berhasil run. cek database'}

@app.get("/similarity/", tags=["Similarity Services"], include_in_schema=False)
async def get_similarity(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    import re
    skip = 0
    limit = 1000
    # limit = 10
    # maximal = 5300
    maximal = 2
    a = 0
    while a < maximal:
        skip = a * limit
        a += 1
        print(skip)

        m_akun = await db['m_akun'].find(
            {
                'kode_akun': {'$exists': 'true'},
                '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]},
                # 'nama_akun': {'$regex': 'pns', '$options': 'i'}
            },
            # {'nama_akun': 1 }
        ).sort("_id", pymongo.ASCENDING).to_list(11000)

        # print(m_akun)

        data_A2022 = await db['A2022'].find(
            {
                # 'namaakunsubrinci': {'$regex': 'pns', '$options':'i'},
                # 'namaaplikasi': 'SIMDA'
                # 'namaakunsubrinci': 'Rek Lvl6',
                # 'namaakunsubrinci': {'$regex': '', '$options':'i'},
                # '$expr': {'$lte': [{'$strLenCP': '$namaakunsubrinci'}, 10]}
                'namaakunsubrinci': 'Retribusi Pelayanan Persampahan/Kebersihan',
            },
        ).sort("_id", pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)
        # print(data_A2022)

        akun = []
        for base in m_akun:
            akun.append(base['nama_akun'].strip())
        # print(akun)

        dataapbd = []
        dataapbd_not_in_m_akun=[]
        for data in data_A2022:
            # namaakunsubrinci = re.sub('([:.,!?()]) ([:.,!?()])', r'\1\2', data['namaakunsubrinci'].strip())
            # namaakunsubrinci1 = re.sub(r'(?<=[/?!-])\s', '', data['namaakunsubrinci'])
            data_namaakunsubrinci = (data.get('namaakunsubrinci', '')).rstrip().lstrip()
            # # data_namaakunsubrinci = data.get('namaakunsubrinci', '')
            # namaakunsubrinci1 = re.sub(r'(?<=[/?!-])\s', '', data_namaakunsubrinci)
            # # namaakunsubrinci2 = re.sub(r'\s+(?=[/?!-])', '', namaakunsubrinci1)
            # namaakunsubrinci = re.sub(r'(?<=[/?!-])\s+(?=[/?!-])', '', namaakunsubrinci1)
            namaakunsubrinci = re.sub(r'(?:(?<=\/) | (?=\/))','',data_namaakunsubrinci)
            # namaakunsubrinci = re.sub(r'(?: (?=\/))','',data_namaakunsubrinci)
            dataapbd.append(namaakunsubrinci)
            print(data_namaakunsubrinci, ' => ', namaakunsubrinci, ' - pepo')
            # cek_akun = await db['m_akun'].find_one({'nama_akun': {'$regex': namaakunsubrinci, '$options':'i'}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
            # from bson import ObjectId
            # id = ObjectId(data.get('_id', ''))
            # cek_sudah_ada_didb_belum = await db['m_similarity_w2v'].find_one({ '_id': id})
            # if cek_sudah_ada_didb_belum is None:
            list_notinclude = ['DID', 'Pajak Tras', 'PBBP2', 'Dana Desa', 'DAU', 'Rek Lvl6']
            if len(namaakunsubrinci) > 0 and data_namaakunsubrinci != 'Rek Lvl6' :
                cek_akun = await db['m_akun'].find_one(
                    {'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                # if cek_akun is None and (len(namaakunsubrinci) > 5 or namaakunsubrinci not in list_notinclude):
                if cek_akun is None and len(namaakunsubrinci) > 10 :
                    from app import similarity

                    dataapbd_not_in_m_akun.append(data)

                    dataapbd_cek = namaakunsubrinci
                    w2v = similarity.word2vecpepo(dataapbd_cek, akun)
                    print(w2v)
                    if 1 in w2v:
                        max_val_w2v = 1
                    else:
                        max_val_w2v = max(w2v)
                    idx_max = w2v.index(max_val_w2v)
                    idx = idx_max
                    print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx],
                          ' - Data APBD Awalnya: ', namaakunsubrinci)
                    # q_akun = await db['m_akun'].find({'nama_akun': {'$regex': akun[idx], '$options': 'i'}})
                    q_akun = await db['m_akun'].find_one(
                        {'nama_akun': akun[idx], '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                    # print(q_akun)
                    score_similarity = {
                        'score_similarity_word2vec': max_val_w2v,
                        'idx_similarity_word2vec': idx,
                        'nama_akun': akun[idx],
                        'kode_akun': q_akun['kode_akun'],
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_similarity_w2v"].insert_one(data)
                else:
                    # cek_akun = await db['m_akun'].find_one({'nama_akun': {'$regex': namaakunsubrinci, '$options':'x'}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                    # cek_akun = await db['m_akun'].find_one({'nama_akun': namaakunsubrinci, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}})
                    # cek_akun = await db['m_akun'].find_one({'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},{ 'score': { '$meta': "textScore" } })
                    # cek_akun = await db['m_akun'].find({'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},{ 'score': { '$meta': "textScore" } }).sort({'ignoredName':{'$meta':"textScore"}}).limit(1).to_list(1)
                    # cek_akun = await db['m_akun'].find({'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},{'score':{'$meta':"textScore"}}).sort({'ignoredName':{'$meta':"textScore"}}).limit(1).to_list(1)
                    # cek_akun = await db['m_akun'].find({'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},{'score':{'$meta':"textScore"}}).sort("score", pymongo.ASCENDING).limit(1).to_list(1)
                    cek_akun = await db['m_akun'].find({'$text': {'$search': namaakunsubrinci}, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 17]}},{'score':{'$meta':"textScore"}}).sort({'score':{'$meta':"textScore"}}).limit(1).to_list(1)
                    print('cek pepo akun: ', namaakunsubrinci, ' - ',cek_akun)

                    score_similarity = {
                        'score_similarity_word2vec': 1,
                        'idx_similarity_word2vec': None,
                        # 'nama_akun': namaakunsubrinci,
                        'nama_akun': cek_akun['nama_akun'],
                        'kode_akun': cek_akun['kode_akun'],
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_similarity_w2v"].insert_one(data)
                print(cek_akun)
            else:
                # kodeakunutama = data['kodeakunutama']
                # kodeakunkelompok = data['kodeakunkelompok']
                namaakunrinci = data.get('namaakunrinci', '')
                cek_akun = await db['m_akun'].find_one(
                    {'nama_akun': namaakunrinci, '$expr': {'$gte': [{'$strLenCP': '$kode_akun'}, 12]}})
                new_kode_akun = cek_akun['kode_akun'] + '.0001'
                print('namaakunrinci',namaakunrinci, cek_akun)
                score_similarity = {
                    'score_similarity_word2vec': None,
                    'idx_similarity_word2vec': None,
                    'nama_akun': namaakunsubrinci,
                    'kode_akun': new_kode_akun,
                }
                insert_result_similarity = data.update(score_similarity)
                new_user = db["m_similarity_w2v"].insert_one(data)
        print(dataapbd)
        print(dataapbd_not_in_m_akun)
        print(len(dataapbd_not_in_m_akun))

    return {'status': 'berhasil run. cek database'}

@app.get("/word2vectest/", tags=["Similarity Services"], include_in_schema=False)
async def get_word2vectest(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    skip = 0
    limit = 1000
    # range = 1000
    # maximal = 5300000
    max = 5300
    a = 0
    while a < max:
        skip = a * limit
        a += 1
        print(skip)

    m_akun = await db['m_akun'].find(
        {
            'kode_akun': { '$exists': 'true' },
            '$expr': { '$gte': [ { '$strLenCP': '$kode_akun' }, 17 ] },
            # 'nama_akun': {'$regex': 'pns', '$options': 'i'}
        },
        # {'nama_akun': 1 }
    ).sort("_id",pymongo.ASCENDING).to_list(11000)
    # print(m_akun)
    # A2022 = await db["A2022"].find({'namaakunsubrinci': {'$regex': 'pns','$options':'i'}}, { 'namapemda': 1, 'kodeakunutama': 1, 'kodeakunkelompok': 1, 'kodeakunjenis': 1, 'kodeakunobjek': 1, 'kodeakunrinci': 1, 'kodeakunsubrinci': 1, 'namaakunsubrinci': 1, 'namasubkegiatan': 1, 'nilaianggaran': 1 }).sort("_id",pymongo.ASCENDING).to_list(1000)
    data_A2022 = await db['A2022'].find(
        {
            # 'namaakunsubrinci': {'$regex': 'pns', '$options':'i'},
        },
        # {'_id': 1, 'kodeakunutama': 1, 'kodeakunkelompok': 1, 'kodeakunjenis': 1, 'kodeakunobjek': 1, 'kodeakunrinci': 1, 'kodeakunsubrinci': 1, 'namaakunsubrinci': 1, 'namasubkegiatan': 1}
    ).sort("_id",pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)
    print(data_A2022)

    akun = []
    for base in m_akun:
        akun.append(base['nama_akun'].strip())
    print(akun)

    dataapbd = []
    for data in data_A2022:
        dataapbd.append(data['namaakunsubrinci'].strip())
    print(dataapbd)

    # from app import similarity
    # score = similarity.similairty_word2vec(db, dataapbd, akun, data_A2022, m_akun)

    from app import similarity
    w2v = similarity.word2vec(dataapbd, akun)
    print(w2v)
    i = 0
    for w2v_ in w2v:
        if 1 in w2v_:
            max_val_w2v = 1
        else:
            max_val_w2v = max(w2v_)
        idx_max = w2v_.index(max_val_w2v)
        idx = idx_max
        # print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx], ' - m_akun: ', m_akun[idx],' - Data APBD Awalnya: ', dataapbd[i],' - data_A2022: ', data_A2022[i])
        print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx],
              ' - Data APBD Awalnya: ', dataapbd[i])
        # q_akun = await db['m_akun'].find({'nama_akun': {'$regex': akun[idx], '$options': 'i'}})
        q_akun = await db['m_akun'].find_one({'nama_akun': akun[idx]})
        print(q_akun)
        score_similarity = {
            'score_similarity_word2vec': max_val_w2v,
            'idx_similarity_word2vec': idx,
            'nama_akun': akun[idx],
            'akun': q_akun,
        }
        insert_result_similarity = data_A2022[i].update(score_similarity)

        new_user = db["m_similarity"].insert_one(data_A2022[i])
        i += 1

    result = {
        'Status': 'Oke',
    }

    return result

@app.get("/similaritybisa/", tags=["Similarity Services"], include_in_schema=False)
async def get_similaritybisa(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    skip=0
    limit=1000
    m_akun = await db['m_akun'].find(
        {
            'kode_akun': { '$exists': 'true' },
            '$expr': { '$gte': [ { '$strLenCP': '$kode_akun' }, 17 ] },
            'nama_akun': {'$regex': 'pns', '$options': 'i'}
        },
        # {'nama_akun': 1 }
    ).sort("_id",pymongo.ASCENDING).to_list(11000)
    # print(m_akun)
    # A2022 = await db["A2022"].find({'namaakunsubrinci': {'$regex': 'pns','$options':'i'}}, { 'namapemda': 1, 'kodeakunutama': 1, 'kodeakunkelompok': 1, 'kodeakunjenis': 1, 'kodeakunobjek': 1, 'kodeakunrinci': 1, 'kodeakunsubrinci': 1, 'namaakunsubrinci': 1, 'namasubkegiatan': 1, 'nilaianggaran': 1 }).sort("_id",pymongo.ASCENDING).to_list(1000)
    data_A2022 = await db['A2022'].find(
        {
            'namaakunsubrinci': {'$regex': 'pns', '$options':'i'},
        },
        # {'_id': 1, 'kodeakunutama': 1, 'kodeakunkelompok': 1, 'kodeakunjenis': 1, 'kodeakunobjek': 1, 'kodeakunrinci': 1, 'kodeakunsubrinci': 1, 'namaakunsubrinci': 1, 'namasubkegiatan': 1}
    ).sort("_id",pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)
    # print(data_A2022)

    # q_akun = await db['m_akun'].find_one({'nama_akun': 'Belanja Gaji Pokok PNS'})
    # print(q_akun)

    from app import similarity
    akun = []
    for base in m_akun:
        akun.append(base['nama_akun'].strip())
    print(akun)

    dataapbd = []
    for data in data_A2022:
        dataapbd.append(data['namaakunsubrinci'].strip())
    print(dataapbd)

    # score = similarity.similairty_word2vec(db, dataapbd, akun, data_A2022, m_akun)

    from app import similarity
    w2v = similarity.word2vec(dataapbd, akun)
    print(w2v)
    i = 0
    for w2v_ in w2v:
        if 1 in w2v_:
            max_val_w2v = 1
        else:
            max_val_w2v = max(w2v_)
        idx_max = w2v_.index(max_val_w2v)
        idx = idx_max
        # print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx], ' - m_akun: ', m_akun[idx],' - Data APBD Awalnya: ', dataapbd[i],' - data_A2022: ', data_A2022[i])
        print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx],
              ' - Data APBD Awalnya: ', dataapbd[i])
        # q_akun = await db['m_akun'].find({'nama_akun': {'$regex': akun[idx], '$options': 'i'}})
        q_akun = await db['m_akun'].find_one({'nama_akun': akun[idx]})
        print(q_akun)
        score_similarity = {
            'score_similarity_word2vec': max_val_w2v,
            'idx_similarity_word2vec': idx,
            'nama_akun': akun[idx],
            'akun': q_akun,
        }
        insert_result_similarity = data_A2022[i].update(score_similarity)

        new_user = db["m_similarity"].insert_one(data_A2022[i])
        i += 1

    result = {
        'Status': 'Oke',
    }

    return result


@app.get("/similarityfungsi/", tags=["Similarity Services"], include_in_schema=False)
async def get_similarity_fungsi(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    import re
    skip = 0
    limit = 1000
    # limit = 10
    maximal = 5300
    # maximal = 1
    a = 0
    while a < maximal:
        skip = a * limit
        a += 1
        print(skip)

        data_A2022 = await db['m_similarity_all'].find(
            {
                # 'kodepemda': '01.00'
             },
            {'_id':1,'kodepemda':1,'namapemda':1,'namaaplikasi':1,'kodefungsi':1,'namafungsi':1,'kode_akun':1,'nama_akun':1,'kodestdsubkegiatan_similarity':1,'namasubkegiatan_similarity':1,'nilaianggaran':1}
        ).sort("_id", pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)
        # print(data_A2022)

        for data in data_A2022:
            data_namafungsi = data.get('namafungsi', '')
            namafungsi = re.sub(r'(?:(?<=\/) | (?=\/))','',data_namafungsi)
            print(data_namafungsi, ' => ', namafungsi, ' - pepo')

            try:
                if len(namafungsi) > 0 and data_namafungsi != '':
                    cek_fungsi = await db['m_fungsi'].find_one(
                        {'namafungsi': namafungsi})

                    if cek_fungsi is None:
                        fungsi = {}
                        fungsi = await db['m_fungsi'].find(
                            {'$text': {'$search': namafungsi},},
                            {'score': {'$meta': "textScore"}}).sort([('score', {'$meta': 'textScore'})]).limit(
                            1).to_list(1)

                        print(fungsi)

                        namafungsi = fungsi[0].get('namafungsi', '')
                        kodefungsi = fungsi[0].get('kodefungsi', '')
                        # score_similarity_fungsi = fungsi[0].get('score', '')

                        score_similarity = {
                            'kode_fungsi': kodefungsi,
                            'nama_fungsi': namafungsi,
                        }
                        insert_result_similarity = data.update(score_similarity)
                        new_user = db["m_apbd_final"].insert_one(data)
                    else:
                        namafungsi = cek_fungsi['namafungsi']
                        kodefungsi = cek_fungsi['kodefungsi']
                        print('cek pepo fungsi: ', namafungsi, ' - ', kodefungsi)

                        score_similarity = {
                            'kode_fungsi': kodefungsi,
                            'nama_fungsi': namafungsi,
                        }
                        insert_result_similarity = data.update(score_similarity)
                        new_user = db["m_apbd_final"].insert_one(data)
                    print(cek_fungsi)
                else:
                    namafungsi = namafungsi
                    kodefungsi = None
                    score_similarity = {
                        'kode_fungsi': kodefungsi,
                        'nama_fungsi': namafungsi,
                    }
                    insert_result_similarity = data.update(score_similarity)
                    new_user = db["m_apbd_final"].insert_one(data)
            except:
                namafungsi = None
                kodefungsi = None
                score_similarity = {
                        'kode_fungsi': kodefungsi,
                        'nama_fungsi': namafungsi,
                }
                insert_result_similarity = data.update(score_similarity)
                new_user = db["m_apbd_final"].insert_one(data)

    return {'status': 'berhasil run. cek database'}

@app.get("/similaritybelanja/", tags=["Similarity Services"])
async def get_similarity_belanja(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    from bson.objectid import ObjectId
    import re
    skip = 0
    limit = 1000
    # limit = 100
    maximal = 5300
    # maximal = 1
    a = 0

    # keywords_pendidikan_1 = ['sekolah','universitas','akademi','politeknik','pelatihan','pendidikan','guru','pesantren','madrasah','pendidik','silabus','SDM','sumber daya manusia','edukasi','pembinaan','kompetensi']
    # keywords_pendidikan_2 = ['pengembangan kapasitas','pengembangan manusia','pengembangan pemuda','pengembangan pramuka']
    #
    # keywords_kesehatan_1 = ['rumah sakit','klinik','puskesmas','kesehatan','dokter','medical']
    #
    # keywords_infrastruktur_1 = ['pembangunan','bangunan','gedung','ruang','rehabilitasi','pemeliharaan','pengadaan','sarana','prasarana']
    # keywords_infrastruktur_2 = ['pengembangan gedung','pengembangan rumah','pengembangan fasilitas','pengembangan unit','pengembangan sistem','pengembangan permukiman','pengembangan perumahan','pengembangan data','pengembangan informasi','pengembangan sarana','pengembangan prasarana','pengembangan aplikasi','pengembangan infrastruktur','pengembangan museum','pengembangan cagar','pengembangan taman','pengembangan desa','pengembangan perpustakaan','pengembangan koleksi','pengembangan pustaka','pengembangan naskah','pengembangan lahan','pengembangan air','pengembangan kawasan','pengembangan ruang']

    while a < maximal:
        skip = a * limit
        a += 1
        print(skip)
        print('pepo')

        data_A2022 = await db['m_apbd_final'].find(
            {
                # '_id': ObjectId('62933e88087a71b7653174ba'),
                # 'nama_fungsi': 'perumahan dan fasilitasi umum',
                # "kode_akun" : {'$regex': '5.2.', '$options': 'i'}
                # "kode_akun" : {'$regex': '4.2.01.01.04.0007', '$options': 'i'}
             },
            {'_id':1,'kodepemda':1,'namapemda':1,'namaaplikasi':1,'kode_fungsi':1,'nama_fungsi':1,'kode_akun':1,'nama_akun':1,'kodestdsubkegiatan_similarity':1,'namasubkegiatan_similarity':1,'nilaianggaran':1}
        ).sort("_id", pymongo.ASCENDING).skip(skip).limit(limit).to_list(limit)
        # print(data_A2022)

        for data in data_A2022:
            try:
                nama_fungsi = data.get('nama_fungsi', '')
                namasubkegiatan_similarity = data.get('namasubkegiatan_similarity', '')
                words_pendidikan = (await db['m_keyword_belanja'].find_one({}))['pendidikan']
                words_kesehatan = (await db['m_keyword_belanja'].find_one({}))['kesehatan']
                words_infrastruktur = (await db['m_keyword_belanja'].find_one({}))['infrastruktur']
                kode_akun = data.get('kode_akun', '')
                print('kode_akun',kode_akun)
                _id = data.get('_id', '')
                belanja_modal = '' if kode_akun is None or len(kode_akun)==0 else kode_akun[:4]
                print('akun 4 digit: ',belanja_modal)
                # print(ph_pendidikan)
                pendidikan = None
                kesehatan = None
                infrastruktur = None
                filter = None

                if nama_fungsi == 'pendidikan':
                    pendidikan = 'pendidikan'
                else:
                    if any(w in namasubkegiatan_similarity.lower() for w in words_pendidikan):
                        pendidikan = 'pendidikan'
                        print('keyword: ', pendidikan,' ada pada kalimat: ',namasubkegiatan_similarity,' kode_akun: ', kode_akun)
                    else:
                        pendidikan = 'nonpendidikan'
                        print('keyword: ', pendidikan, 'ga ada pada kalimat: ', namasubkegiatan_similarity,' kode_akun: ', kode_akun)

                if nama_fungsi == 'kesehatan':
                    kesehatan = 'kesehatan'
                else:
                    if any(w in namasubkegiatan_similarity.lower() for w in words_kesehatan):
                        kesehatan = 'kesehatan'
                        print('keyword: ', kesehatan, ' ada pada kalimat: ', namasubkegiatan_similarity,' kode_akun: ', kode_akun)
                    else:
                        kesehatan = 'nonkesehatan'
                        print('keyword: ', kesehatan, 'ga ada pada kalimat: ', namasubkegiatan_similarity,' kode_akun: ', kode_akun)

                if belanja_modal=='5.2.':
                    if nama_fungsi == 'perumahan dan fasilitasi umum':
                        infrastruktur = 'infrastruktur'
                    else:
                        if any(w in namasubkegiatan_similarity.lower() for w in words_infrastruktur):
                            infrastruktur = 'infrastruktur'
                            print('keyword: ', infrastruktur, ' ada pada kalimat: ', namasubkegiatan_similarity,' kode_akun: ', kode_akun, '_id:',_id)
                        else:
                            infrastruktur = 'noninfrastruktur'
                            print('keyword: ', infrastruktur, 'ga ada pada kalimat: ', namasubkegiatan_similarity,' kode_akun: ', kode_akun)
                else:
                    infrastruktur='noninfrastruktur'

                cek_filter = (await db['m_akun'].find_one({'kode_akun': kode_akun},{'filter':1}))['filter']
                print(cek_filter)
                if cek_filter=='1' or cek_filter=='2':
                    filter=cek_filter

                add_field_tambahan = {
                    'pendidikan': pendidikan,
                    'kesehatan': kesehatan,
                    'infrastruktur': infrastruktur,
                    'filter': filter
                }
                print(add_field_tambahan)

                data = {
                    '_id': data.get('_id', None),
                    'kodepemda': data.get('kodepemda', None),
                    'namapemda': data.get('namapemda', None),
                    'namaaplikasi': data.get('namaaplikasi', None),
                    'kode_fungsi': data.get('kode_fungsi', None),
                    'nama_fungsi': data.get('nama_fungsi', None),
                    'kode_akun': data.get('kode_akun', None),
                    'nama_akun': data.get('nama_akun', None),
                    'kodestdsubkegiatanfull': data.get('kodestdsubkegiatan_similarity', None),
                    'namasubkegiatan': data.get('namasubkegiatan_similarity', None),
                    'nilaianggaran': data.get('nilaianggaran', None),
                }

                add_field = data.update(add_field_tambahan)
                new_user = db["m_apbd_release"].insert_one(data)
            except:
                print('error insert')

    return {'status': 'berhasil run. cek database'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, port=port, host="0.0.0.0")























