import dash
from dash.dependencies import Input, Output
from dash import dcc, html

import flask
import pandas as pd
import os

from app.database import SessionLocal, Session, Close

import pymongo
from pymongo import MongoClient

from dash import dash_table

from decimal import Decimal
import json
import time

from os import environ
from dotenv import load_dotenv
load_dotenv()
import certifi

DEBUG = environ['DEBUG']

def connecttodatabase():
    if DEBUG == '1':
        client = MongoClient("mongodb://127.0.0.1:27017/")
        mydb = client["bedahdataapbd"]
    elif DEBUG == '2':
        DATABASE_URL = environ['DATABASE_URL']
        client = MongoClient(DATABASE_URL, tlsCAFile=certifi.where())
        mydb = client["sisna"]
    else:
        DATABASE_URL = environ['DATABASE_URL']
        client = MongoClient(DATABASE_URL)
        mydb = client["sisna"]
    return mydb

db = connecttodatabase()

def standardization_kegiatan_datatable(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get('secret_key', 'secret')

    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    def dropdown():
        q = db['m_pemda'].aggregate([
            {"$group": {"_id": {'kodepemda': '$kodepemda', 'namapemda': "$namapemda"}, }},
            {'$sort': {'_id.kodepemda': 1}}
        ])

        result = []
        for q in list(q):
            result.append(q['_id']['namapemda'])

        return result

    dropdown = dropdown()

    app.layout = html.Div([
        dcc.Dropdown(dropdown, 1, id='dropdown'),
        dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="loading-output-1")
        ),
        html.Table(id='table'),
        # dcc.Graph(id='graph'),

        dcc.Store(id='intermediate-value')
    ])

    def slow_processing_step(value):
        anggaran_kegiatan = db['m_apbd_final'].aggregate([
            {'$match': {'nilaianggaran': {'$ne': float('NaN')}, 'namapemda': value}},
            {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
            {"$group": {
                "_id": {'namapemda': '$namapemda', 'kodestdsubkegiatan_similarity': "$kodestdsubkegiatan_similarity",
                        'namasubkegiatan_similarity': "$namasubkegiatan_similarity"},
                "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
            {'$sort': {'_id.kodestdsubkegiatan_similarity': 1}}
        ])
        # anggaran_kegiatan = db['m_apbd_final'].aggregate([
        #     {'$match': {'nilaianggaran': {'$ne': float('NaN')}, 'namapemda': value}},
        #     {'$lookup': { 'from': "m_subkegiatan", 'localField': "kodestdsubkegiatan_similarity", 'foreignField': 'kodestdsubkegiatanfull', 'as': 'namasubkegiatan' }},
        #     {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
        #     {"$group": {
        #         "_id": {'namapemda': '$namapemda', 'kodestdsubkegiatan_similarity': "$kodestdsubkegiatan_similarity", 'namasubkegiatan_similarity': "$namasubkegiatan"},
        #         "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
        #     {'$sort': {'_id.kodestdsubkegiatan_similarity': 1}}
        # ])
        result = []
        for q in list(anggaran_kegiatan):
            r = {
                'namapemda': q['_id']['namapemda'],
                'kodestdsubkegiatan_similarity': q['_id']['kodestdsubkegiatan_similarity'],
                'namasubkegiatan_similarity': q['_id']['namasubkegiatan_similarity'],
                'nilaianggaran': "Rp{:,.2f}".format(q['nilaianggaran']),
            }
            result.append(r)
        print(result)
        df_ = pd.DataFrame(result)
        df = df_.iloc[:, 0:]

        return df

    def create_table(df):
        dash_data_table = dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )
        return dash_data_table

    @app.callback(Output('intermediate-value', 'data'), Input('dropdown', 'value'))
    def clean_data(value):
        cleaned_df = slow_processing_step(value)

        return cleaned_df.to_json(date_format='iso', orient='split')

    @app.callback(Output('table', 'children'), Input('intermediate-value', 'data'))
    def update_table(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = create_table(dff)
        return table

    @app.callback(Output("loading-output-1", "children"), Input("dropdown", "value"))
    def input_triggers_spinner(value):
        time.sleep(3)
        return 'Data Standardisasi Nomenklatur Sub Kegiatan '+str(value)

    return app

def standardization_akun_datatable(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get('secret_key', 'secret')

    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    def dropdown():
        q = db['m_pemda'].aggregate([
            {"$group": {"_id": {'kodepemda': '$kodepemda', 'namapemda': "$namapemda"}, }},
            {'$sort': {'_id.kodepemda': 1}}
        ])

        result = []
        for q in list(q):
            result.append(q['_id']['namapemda'])

        return result

    dropdown = dropdown()

    app.layout = html.Div([
        dcc.Dropdown(dropdown, 1, id='dropdown'),
        dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="loading-output-1")
        ),
        html.Table(id='table'),
        dcc.Store(id='intermediate-value')
    ])

    def slow_processing_step(value):
        anggaran_kegiatan = db['m_apbd_final'].aggregate([
            {'$match': {'nilaianggaran': {'$ne': float('NaN')}, 'namapemda': value}},
            {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
            {"$group": {
                "_id": {'namapemda': '$namapemda', 'kode_akun': "$kode_akun",
                        'nama_akun': "$nama_akun"},
                "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
            {'$sort': {'_id.kode_akun': 1}}
        ])
        print(anggaran_kegiatan)
        result = []
        for q in list(anggaran_kegiatan):
            r = {
                'namapemda': q['_id']['namapemda'],
                'kode_akun': q['_id']['kode_akun'],
                'nama_akun': q['_id']['nama_akun'],
                'nilaianggaran': "Rp{:,.2f}".format(q['nilaianggaran']),
            }
            result.append(r)
        df_ = pd.DataFrame(result)
        df = df_.iloc[:, 0:]

        return df

    def create_table(df):
        dash_data_table = dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )
        return dash_data_table

    @app.callback(Output('intermediate-value', 'data'), Input('dropdown', 'value'))
    def clean_data(value):
        cleaned_df = slow_processing_step(value)

        return cleaned_df.to_json(date_format='iso', orient='split')

    @app.callback(Output('table', 'children'), Input('intermediate-value', 'data'))
    def update_table(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = create_table(dff)
        return table

    @app.callback(Output("loading-output-1", "children"), Input("dropdown", "value"))
    def input_triggers_spinner(value):
        time.sleep(6)
        return 'Data Standardisasi Nomenklatur Akun '+str(value)

    return app

def apemdafungsianggaran(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get('secret_key', 'secret')

    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    def dropdown():
        q = db['m_pemda'].aggregate([
            {"$group": {"_id": {'kodepemda': '$kodepemda', 'namapemda': "$namapemda"}, }},
            {'$sort': {'_id.kodepemda': 1}}
        ])

        result = []
        for q in list(q):
            result.append(q['_id']['namapemda'])

        return result

    dropdown = dropdown()

    app.layout = html.Div([
        dcc.Dropdown(dropdown, 1, id='dropdown'),
        dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="loading-output-1")
        ),
        html.Table(id='table'),
        html.Div(id="graph"),
        # dcc.Graph(id='graph'),
        dcc.Store(id='intermediate-value')
    ])

    def slow_processing_step(value):
        query = db['a_pemda_fungsi_anggaran'].aggregate([
            {'$match': {'nilaianggaran': {'$ne': float('NaN')}, 'namapemda': value}},
            {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
            {"$group": {
                "_id": {'kodepemda': '$kodepemda','namapemda': '$namapemda', 'kode_fungsi': "$kode_fungsi", 'nama_fungsi': "$nama_fungsi"},
                "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
            # {'$sort': {'_id.kode_fungsi': 1}}
        ])
        result = []
        for q in list(query):
            r = {
                'namapemda': q['_id']['namapemda'],
                'kode_fungsi': q['_id']['kode_fungsi'],
                'nama_fungsi': q['_id']['nama_fungsi'],
                # 'nilaianggaran': "Rp{:,.2f}".format(q['nilaianggaran']),
                'nilaianggaran': q['nilaianggaran'],
            }
            result.append(r)
        print(result)
        df_ = pd.DataFrame(result)
        df = df_.iloc[:, 0:]

        return df

    def create_table(df):
        dash_data_table = dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )
        return dash_data_table

    def create_graph(dff):
        print(dff["nama_fungsi"])
        print(dff["nilaianggaran"])
        colors = '#7FDBFF'
        graph = dcc.Graph(
                    figure={
                        'data': [
                            {
                                "x": dff["nama_fungsi"],
                                "y": dff["nilaianggaran"],
                                "type": "bar",
                                "marker": {"color": colors},
                            }
                        ],
                        'layout': {
                            "xaxis": {"automargin": True},
                            "yaxis": {
                                "automargin": True,
                                # "title": {"text": 'column'}
                            },
                            # "height": 250,
                            'title': 'Graph Anggaran Menurut Fungsi Wilayah '+dff["namapemda"][0]
                        }
                    }
                )

        return graph

    @app.callback(Output('intermediate-value', 'data'), Input('dropdown', 'value'))
    def clean_data(value):
        cleaned_df = slow_processing_step(value)

        return cleaned_df.to_json(date_format='iso', orient='split')

    @app.callback(Output('table', 'children'), Input('intermediate-value', 'data'))
    def update_table(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = create_table(dff)
        return table

    @app.callback(Output('graph', 'children'), Input('intermediate-value', 'data'))
    def update_graph(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = create_graph(dff)
        return table

    @app.callback(Output("loading-output-1", "children"), Input("dropdown", "value"))
    def input_triggers_spinner(value):
        time.sleep(1)
        return 'Data Anggaran Menurut Fungsi Wilayah '+str(value)

    return app

def aakunanggaran(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get('secret_key', 'secret')

    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    query = db['a_akun_anggaran'].aggregate([
        {'$match': {'nilaianggaran': {'$ne': float('NaN')}}},
        {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
        {"$group": {
            "_id": {'kode_akun': '$kode_akun', 'nama_akun': '$nama_akun'},
            "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
        {'$sort': {'_id.kode_akun': 1}}
    ])
    result = []
    for q in list(query):
        r = {
            'kode_akun': q['_id']['kode_akun'],
            'nama_akun': q['_id']['nama_akun'],
            'nilaianggaran': "Rp{:,.2f}".format(q['nilaianggaran']),
            # 'nilaianggaran': q['nilaianggaran'],
        }
        result.append(r)
    print(result)
    df_ = pd.DataFrame(result)
    df = df_.iloc[:, 0:]

    app.layout = dash_table.DataTable(
            id='table',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )

    return app

def asubkegiatananggaran(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get('secret_key', 'secret')

    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    query = db['a_subkegiatan_anggaran'].aggregate([
        {'$match': {'nilaianggaran': {'$ne': float('NaN')}}},
        {'$addFields': {'convertedAnggaran': {'$toDouble': "$nilaianggaran"}}},
        {"$group": {
            "_id": {'kodestdsubkegiatan_similarity': '$kodestdsubkegiatan_similarity', 'namasubkegiatan_similarity': '$namasubkegiatan_similarity'},
            "nilaianggaran": {"$sum": "$convertedAnggaran"}}},
        {'$sort': {'_id.kodestdsubkegiatan_similarity': 1}}
    ])
    result = []
    for q in list(query):
        r = {
            'kodestdsubkegiatan_similarity': q['_id']['kodestdsubkegiatan_similarity'],
            'namasubkegiatan_similarity': q['_id']['namasubkegiatan_similarity'],
            'nilaianggaran': "Rp{:,.2f}".format(q['nilaianggaran']),
        }
        result.append(r)
    print(result)
    df_ = pd.DataFrame(result)
    df = df_.iloc[:, 0:]

    app.layout = dash_table.DataTable(
            id='table',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )

    return app







