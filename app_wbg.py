import json
from dash import Dash, dcc, html, callback, Input, Output, State, ctx 
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

#%%
# Base de datos
df_od0_19 = pd.read_parquet("assets/odmatrix_od_h_19.parquet")
df_od0_20 = pd.read_parquet("assets/odmatrix_od_h_20.parquet")
df_od0_21 = pd.read_parquet("assets/odmatrix_od_h_21.parquet")
df_part0 = pd.read_parquet("assets/odmatrix_part_mod.parquet")
df_h_i0 = pd.read_parquet("assets/odmatrix_h_i.parquet")
df_dist0 = pd.read_parquet("assets/odmatrix_dist.parquet")
    
# ZATs
with open('assets/BTA_ZAT.geojson') as jsonfile:
    geo_zat = json.load(jsonfile)
#Bta
with open('assets/BTA_Localidades.geojson') as jsonfile:
    geo_bta = json.load(jsonfile)
# Vias principales    
with open('assets/BTA_Vias_principales.geojson') as jsonfile:
    geo_vias = json.load(jsonfile)

#%%
    
colores = {
    'fondo': '#FFFFFF',
    'fondo_tit': '#black',
    'WBG': '#339FFF',
    'text': 'white'
}
    
# Nombre de las columnas
c_anio = "anio"
c_mes = "mes"
c_tipo_dia = "tipo_dia"
c_o = "origen"
c_d = "destino"
c_h_i = "periodo"
c_h_i2 = c_h_i+"2"
c_dist = "distancia"
c_res = "residencia"
c_prop = "proposito"
c_modo = "modo"
c_viajes = "viajes"
c_rango_dist="rango_dist"
c_var_v = "var_viajes"
c_var_v_p = "var_viajes_p"

# Opciones generales
anios_dispo = [2019, 2020, 2021]

tipo_dia_dispo = ["lab", "sab", "dom"]
dd_tipo_dia = [{"label":"Laborable", "value":"lab"},
               {"label":"Sábado", "value":"sab"},
               {"label":"Domingo", "value":"dom"}]

horas_dispo = ["0"+str(x) if len(str(x))==1 else str(x) for x in range(0,24)]
#sorted([x.replace("P","") for x in df_h_i0[c_h_i].unique()])
# dd_horas=[{"label":x+":00", "value":"P"+x} for x in horas_dispo]

zat_o_dispo = list(set(df_od0_19[c_o].unique())\
                   .union(set(df_od0_20[c_o].unique())\
                          .union(set(df_od0_21[c_o].unique()))))
zat_d_dispo = list(set(df_od0_19[c_d].unique())\
                   .union(set(df_od0_20[c_d].unique())\
                          .union(set(df_od0_21[c_d].unique()))))

modo_dispo = df_part0[c_modo].dropna().unique()

prop_val = ['HBO','HBW','HBEdu','NHB']
prop_dispo = ["Otro", "Trabajo", "Educación", "No basado en el hogar"]
dd_prop =  [{"label":x, "value":y} for x,y in zip(prop_dispo, prop_val)]

rangos_dist = ["[0-0.5)", "[0.5-1)", "[1-2)", "[2-5)", "[5-10)", "[10-20)", "[20-50)","+50"]
#%%

# Inicializa la app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

encabezado = dbc.Row([    
    html.Div([
    html.Header(children='Indicadores de movilidad urbana en Bogotá',
            style={'height': 60, 'fontSize': 35, 'backgroundColor': colores['fondo_tit'],
                'textAlign': 'center', #'padding': '15px 0', #'color': colores['text'],
                'width': '100%', 'display': 'inline-block'
                  },
               className  ="bg-primary text-white  text-center"), #p-2 mb-2
    html.Img(src=app.get_asset_url('WBG_Logo.png'), 
             style={'height': 60,'width': '15%','display': 'inline-block',
                    'position':'absolute', 'left':0})],
    style={'position': 'relative'}) 
], className  ="pb-2 rounded text-*-center") # Fin Row encabezado

filtros_1 = dbc.Row([
    # ZAT O
    dbc.Col([
        html.P("ZAT origen", style={'marginBottom':5}),
        dcc.Dropdown(options=["Todas"] + zat_o_dispo,
                     value = "Todas",
                     multi=True,
                     placeholder="ZAT origen",
                     id='dd-o'),
    ], width=6, className  ="fs-6"
    ),    
    # ZAT D
    dbc.Col([
        html.P("ZAT destino", style={'marginBottom':5}),
        dcc.Dropdown(options=["Todas"] + zat_d_dispo,
                     value = "Todas",
                     multi=True,
                     placeholder="ZAT destino",
                     id='dd-d'),
    ], width=6, className  ="fs-6"
    )
]) # Fin Row filtros 1

filtros_2 = dbc.Row([
    # Propósito
    dbc.Col([
        html.P("Propósito", style={'marginBottom':5}),
        dcc.Dropdown(options=dd_prop,
                     value='HBEdu',
                     multi=True,
                     placeholder="Propósito",
                     id='dd-prop'),
    ], width={"size": 5}, className  ="fs-6"
    ), # Fin Col Propósito
    # dbc.Col([
    #     dbc.Card([
    #         html.P(id="num-viajes-filt")
    #         ], body=True)
    #     ], width=3, align="end",
    #     className  =".text-primary text-center font-weight-bold fs-3 border-0 bg-transparent"),
    # Filtrar
    dbc.Col([
        html.P("", style={'marginBottom':5}),
        dbc.Button(
            "Filtrar datos",
            color="primary",
            id="button-filt-data",
            className  ="fs-5",
        )        
    ], width={"size": 2, 'offset':5}, align="end") # Fin Col botón filtrar
    
])

# Filtros generales        
filtros = dbc.Card([
    filtros_1, filtros_2
], body=True,
    className  ="border border-secondary p-2"
) # Fin Card filtros


controles_od = dbc.Card([
    dcc.Dropdown(options= anios_dispo,
                      value= max(anios_dispo),
                      multi=False, 
                      placeholder="Año",
                      disabled = False,
                      id='dd-v-anio',
                      className   = "mb-1"), 
    html.Div([
        dcc.Checklist(
           options=[
               {'label': 'Comparar',
                'value': 'Si',
                "disabled":False}
           ],
           id = "check_comp",
           className   = "mb-1"
        )
    ]),
   
    html.Div([
        dcc.RadioItems(
            # options=[{'label': 'Absoluto', 'value': 'Absoluto', 'disabled': True},
            #     {'label': 'Porcentaje', 'value': 'Porcentaje', 'disabled': True}],
            value="Absoluto",
           inline=True,
           id = "check_tipo_comp",
           className="pe-2"
        ),        
        dcc.Dropdown(options=anios_dispo,
                     value=min(anios_dispo),
                     multi=False,
                     placeholder="Año base",
                     disabled=False,
                     id='dd-v-anio-base'
                     ),        
        dcc.Dropdown(options=anios_dispo,
                     value=max(anios_dispo),
                     multi=False,
                     placeholder="Año de comparación",
                     disabled=False,
                     id='dd-v-anio-comparacion'
                     )
        ], className="vstack gap-2 mb-4"
        ),
    html.Div([
        dbc.Label("Tipo de día"),
        dcc.Dropdown(options= dd_tipo_dia,
                          value= "lab",
                          multi=False, 
                          placeholder="Tipo de día",
                          disabled = False,
                          id='dd-v-t-dia',
                          className   = "mb-1"),
        
    ]),    
    html.Div([
        dbc.Label("Hora de inicio"),
        dcc.RangeSlider(0, 23,
                        step=1,
                        marks={i:str(i) for i in range(0,24) if i%4==0 or i==23},
                        value=[0, 23],
                        tooltip={"placement": "bottom", "always_visible": True},
                        id='rs-h-i-od')
    ], className = "mb-1"),
    html.Div([
        dbc.Label("Rangos"),
        dcc.Input(type="text",
              value="100, 500, 1000, 2000",
              placeholder="Rangos, separados por comas",
              # debounce=True,
              id="in-rang",
              style={'fontSize': 12, 'fontStyle': 'italic', "width":"100%"}
              )
    ], className="vstack gap-1 mb-4" ),
    html.Div([
        dbc.Button(
            "Generar mapa",
            color="primary",
            id='button-gen-mapa-od',
            className ="d-flex justify-content-center m-3"
        )
        ])
], body=True, className  ="font-ligth fs-6") # Fin Card controles viajes OD

# Viajes por ZAT
gr_od = dbc.Card([
    dbc.Row([
        html.H3("Viajes por ZAT", className  ="bg-info p-1 text-white rounded-top")
    ]),
    dbc.Row([
        dbc.Tabs(
            [
                dbc.Tab(label="Origen", tab_id="tab-v-o"),
                dbc.Tab(label="Destino", tab_id="tab-v-d"),
                # dbc.Tab(label="Tasa de viajes", tab_id="tab-v-t"),

            ],
            id="tabs-v",
            active_tab="tab-v-o"
        ),
        # html.Br(),
        # dbc.Tabs(
        #     [
        #         dbc.Tab(label="Hábil", tab_id="tab-v-hab"),
        #         dbc.Tab(label="Sábado", tab_id="tab-v-sab"),
        #         dbc.Tab(label="Domingo", tab_id="tab-v-dom"),

        #     ],
        #     id="tabs-v-d",
        #     active_tab="tab-v-hab"
        # )
    ]), # Fin Row Tabs
    dbc.Row([
        dbc.Col(controles_od, width=2),
        dbc.Col(id='gr-v')
    ])
],className  ="border order-light pt-2", body=True) # Fin Card viajes OD
    
# Partición modal
gr_part_mod = dbc.Card([
    dbc.Row([
        html.H3("Partición modal", className  ="bg-info p-1 text-white rounded-top")
    ]),
    dbc.Tabs(
            [
                dbc.Tab(label="Hábil", tab_id="tab-part-mod-hab"),
                dbc.Tab(label="Sábado", tab_id="tab-part-mod-sab"),
                dbc.Tab(label="Domingo", tab_id="tab-part-mod-dom"),
                
            ],
            id="tabs-part-mod",
            active_tab="tab-part-mod-hab",
    ),
    dbc.Row(id='gr-part-mod')  
], className  ="border order-light pt-2", body=True) # Fin Card partición modal

# Hora de inicio
gr_h_i = dbc.Card([
    dbc.Row([
        html.H3("Hora de inicio", className  ="bg-info p-1 text-white rounded-top")
    ]),
    dbc.Tabs(
            [
                dbc.Tab(label="Hábil", tab_id="tab-h-i-hab"),
                dbc.Tab(label="Sábado", tab_id="tab-h-i-sab"),
                dbc.Tab(label="Domingo", tab_id="tab-h-i-dom"),
                
            ],
            id="tabs-h-i",
            active_tab="tab-h-i-hab",
    ),
    dbc.Row(id='gr-h-i') 
], className  ="border order-light pt-2", body=True) # Fin Card hora de inicio

# Distancia
gr_dist = dbc.Card([
    dbc.Row([
        html.H3("Distancia", className  ="bg-info p-1 text-white rounded-top")
    ]),
    dbc.Tabs(
            [
                dbc.Tab(label="Hábil", tab_id="tab-dist-hab"),
                dbc.Tab(label="Sábado", tab_id="tab-dist-sab"),
                dbc.Tab(label="Domingo", tab_id="tab-dist-dom"),
                
            ],
            id="tabs-distancia",
            active_tab="tab-dist-hab",
    ),
    dbc.Row(id='gr-dist')
], className  ="border order-light pt-2", body=True) # Fin Card distancia

# Tasa de viajes
# gr_tasa = dbc.Card([
#     dbc.Row([
#         html.H3("Tasa de generación de viajes", className  ="bg-info p-1 text-white rounded-top")
#     ]),
#     dbc.Tabs(
#             [
#                 dbc.Tab(label="Hábil", tab_id="tab-tasa-hab"),
#                 dbc.Tab(label="Sábado", tab_id="tab-tasa-sab"),
#                 dbc.Tab(label="Domingo", tab_id="tab-tasa-dom"),
                
#             ],
#             id="tabs-tasa",
#             active_tab="tab-tasa-hab",
#     ),
#     dbc.Row(id='gr-tasa')
# ], className  ="border order-light pt-2", body=True) # Fin tasa de viajes



#############
## Apariencia
#############
sto_type = "memory" #local, session, memory
app.layout = dbc.Container([
    # Almacena las tablas agregadas intermedias
    dcc.Store(id='store-val-inter-od', storage_type=sto_type),
    # Almacena las tablas agregadas intermedias
    dcc.Store(id='store-val-inter-od-comp', storage_type=sto_type),
    # Almacena los mapas    
    dcc.Store(id='store-graf-od', storage_type=sto_type),
    # Almacena los mapas de comparación    
    dcc.Store(id='store-graf-od-comp', storage_type=sto_type),
    # Almacena los gráficos de la partición modal
    dcc.Store(id='store-graf-part-mod', storage_type=sto_type),
    # Almacena los gráficos de la hora
    dcc.Store(id='store-graf-h-i', storage_type=sto_type),
    # Almacena los gráficos de la distancia
    dcc.Store(id='store-graf-dist', storage_type=sto_type),
    # Almacena los gráficos de la tasa de generación de viajes
    # dcc.Store(id='store-graf-tasa', storage_type=sto_type),
    encabezado,
    filtros,
    gr_od,
    gr_part_mod,
    gr_h_i,
    gr_dist,
    # gr_tasa    
], fluid=True) # Fin Container general
# Fin apariencia


#################
## Interactividad
#################
# Activa botón de filtrado con cambio en filtros
# @app.callback(
#     Output('button-filt-data', 'disabled'),
#     Input('dd-o', 'value'),
#     Input('dd-d', 'value'),
#     Input('dd-prop', 'value'),
#     State('button-filt-data', 'disabled'))
# def activa_filtro(origenes, destinos, propositos, filtro_act):
#     if filtro_act:
#         return False

# Filtrar para mapa
@app.callback(
    Output('store-val-inter-od', 'data'),
    Output('button-filt-data', 'disabled'),
    Input('dd-o', 'value'),
    Input('dd-d', 'value'),
    Input('dd-prop', 'value'),
    Input('button-filt-data', 'n_clicks'))
def filtra_df_od(origenes, destinos, propositos, btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
    
    if ctx.triggered_id != 'button-filt-data':
        return None, False
    
    test_o_19 = df_od0_19[c_o] >=  0
    test_o_20 = df_od0_20[c_o] >=  0
    test_o_21 = df_od0_21[c_o] >=  0
    test_d_19 = df_od0_19[c_d] >=  0
    test_d_20 = df_od0_20[c_d] >=  0
    test_d_21 = df_od0_21[c_d] >=  0
    test_prop_19 = df_od0_19[c_prop].isin(prop_val)
    test_prop_20 = df_od0_20[c_prop].isin(prop_val)
    test_prop_21 = df_od0_21[c_prop].isin(prop_val)
    
    if origenes is not None:
        if not isinstance(origenes,list):
            origenes=[origenes]            
        if "Todas" not in origenes:
            test_o_19 = df_od0_19[c_o].isin(origenes)
            test_o_20 = df_od0_20[c_o].isin(origenes)
            test_o_21 = df_od0_21[c_o].isin(origenes)
            
            
    if destinos is not None:
        if not isinstance(destinos,list):
            destinos=[destinos]            
        if "Todas" not in destinos:
            test_d_19 = df_od0_19[c_d].isin(destinos)
            test_d_20 = df_od0_20[c_d].isin(destinos)
            test_d_21 = df_od0_21[c_d].isin(destinos)            
            
    if propositos is not None:
        if not isinstance(propositos,list):
            propositos=[propositos]            
        test_prop_19 = df_od0_19[c_prop].isin(propositos)
        test_prop_20 = df_od0_20[c_prop].isin(propositos)
        test_prop_21 = df_od0_21[c_prop].isin(propositos)

    df_od_19_filt = df_od0_19[(test_o_19) & (test_d_19) & (test_prop_19)]
    df_od_20_filt = df_od0_20[(test_o_20) & (test_d_20) & (test_prop_20)]
    df_od_21_filt = df_od0_21[(test_o_21) & (test_d_21) & (test_prop_21)]
    
    df_o_19 = df_od_19_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_o])\
    .agg(viajes_o=(c_viajes,"sum"))
    df_o_19.reset_index(inplace=True)
    df_d_19 = df_od_19_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_d])\
    .agg(viajes_d=(c_viajes,"sum"))
    df_d_19.reset_index(inplace=True)
    
    df_o_20 = df_od_20_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_o])\
    .agg(viajes_o=(c_viajes,"sum"))
    df_o_20.reset_index(inplace=True)
    df_d_20 = df_od_20_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_d])\
    .agg(viajes_d=(c_viajes,"sum"))
    df_d_20.reset_index(inplace=True)    
    
    df_o_21 = df_od_21_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_o])\
    .agg(viajes_o=(c_viajes,"sum"))
    df_o_21.reset_index(inplace=True)
    df_d_21 = df_od_21_filt.groupby(by=[c_anio, c_tipo_dia, c_h_i2, c_d])\
    .agg(viajes_d=(c_viajes,"sum"))
    df_d_21.reset_index(inplace=True)
    
    
    datasets = {
         'df_o_19': df_o_19.to_json(orient='split', date_format='iso'),
         'df_d_19': df_d_19.to_json(orient='split', date_format='iso'),  
         
         'df_o_20': df_o_20.to_json(orient='split', date_format='iso'),
         'df_d_20': df_d_20.to_json(orient='split', date_format='iso'), 
         
         'df_o_21': df_o_21.to_json(orient='split', date_format='iso'),
         'df_d_21': df_d_21.to_json(orient='split', date_format='iso')
     }
    
    return json.dumps(datasets), True

# Mapa
@app.callback(
    Output('gr-v', 'children'),    
    Input('store-graf-od', 'data'),
    Input('store-graf-od-comp', 'data'),
    State('check_comp', 'value'),
    State('check_tipo_comp', 'value'),
    Input('tabs-v', "active_tab"), prevent_initial_call=True)
def render_mapa_od(grafs, grafs_comp, comp, tipo_comp, active_tab_v):
    if comp:
        if active_tab_v == "tab-v-o":
            return dcc.Graph(figure=grafs_comp["Origen"])
        elif active_tab_v == "tab-v-d":
            return dcc.Graph(figure=grafs_comp["Destino"])
    if not comp:    
        if active_tab_v == "tab-v-o":
            return dcc.Graph(figure=grafs["Origen"])
        elif active_tab_v == "tab-v-d":
            return dcc.Graph(figure=grafs["Destino"])

@app.callback(
    Output('store-graf-od', 'data'),
    Input('store-val-inter-od', 'data'),
    Input('button-gen-mapa-od', 'n_clicks'),
    State('check_comp', 'value'),
    State('dd-v-anio', 'value'),
    State('dd-v-t-dia', 'value'),
    State('rs-h-i-od', 'value'),
    State('in-rang', 'value'), prevent_initial_call=True)    
def genera_mapa_od(datos_json, btn_gen, comparar, anio, t_dia, horas_i, rango_input):
    
    if ctx.triggered_id != 'button-gen-mapa-od':
        raise PreventUpdate

    if comparar:
        raise PreventUpdate

    if rango_input is None:
        rango_input="100,500,1000,2000"        
    
    limites = [int(x.strip()) for x in rango_input.split(",")]

    label_limites = []
    for l in range(len(limites)):
        if l == 0:
            label = "<{}".format(limites[l])
        else:
            label = "[{};{})".format(limites[l-1],limites[l])
        label_limites.append(label)
    label_limites.append(">={}".format(limites[-1]))    
    
    datasets = json.loads(datos_json)    

    df_o = pd.read_json(datasets['df_o_'+str(anio)[-2:]], orient='split')
    df_d = pd.read_json(datasets['df_d_'+str(anio)[-2:]], orient='split') 
    
    df_o = df_o[(min(horas_i)<=df_o[c_h_i2]) & (df_o[c_h_i2]<=max(horas_i)) 
                & (df_o[c_tipo_dia]==t_dia)]
    df_d = df_d[(min(horas_i)<=df_d[c_h_i2]) & (df_d[c_h_i2]<=max(horas_i))
                & (df_d[c_tipo_dia]==t_dia)]
    
    df_o = df_o.groupby(by=[c_o]).agg(viajes_o=("viajes_o","sum"))
    df_o.reset_index(inplace=True)
    df_d = df_d.groupby(by=[c_d]).agg(viajes_d=("viajes_d","sum"))
    df_d.reset_index(inplace=True)
    
    df_o['viajes_rango'] = df_o['viajes_o'].apply(lambda x: np.searchsorted(limites, x, side="right"))
    df_d['viajes_rango'] = df_d['viajes_d'].apply(lambda x: np.searchsorted(limites, x, side="right"))

    df_od = [df_o, df_d]
    cols_o_d = [c_o, c_d]
    od_aux = ["Origen","Destino"]
    cols_viajes=['viajes_o','viajes_d' ]

    escala_colores = [((0.0, px.colors.sequential.Plasma_r[grupo]),
                       (1.0, px.colors.sequential.Plasma_r[grupo])) 
                  for grupo in range(len(label_limites))]

    figures_o_d = dict()

    for od_temp in range(len(od_aux)):
        df_anio_temp = df_od[od_temp]
        
        fig = go.Figure()
        
        if len(df_anio_temp) > 0:
            for grupo in range(len(label_limites)):                
                df_trace = df_anio_temp[df_anio_temp['viajes_rango'] == grupo]    
                fig.add_choroplethmapbox(geojson=geo_zat,
                                          locations=df_trace[cols_o_d[od_temp]],
                                          z=df_trace[cols_viajes[od_temp]],#'viajes_rango'
                                          featureidkey="properties.ID",
                                          showlegend=True,
                                          name=label_limites[grupo],
                                          colorscale=escala_colores[grupo],
                                          showscale=False,)
                
        fig.update_layout(
            title=dict(text=od_aux[od_temp] + " de los viajes en " + str(anio)),
            margin=dict(l=4, r=4, t=5, b=3),
            mapbox=dict(
                style='carto-positron',
                zoom=8,
                center={"lat": 4.657946861376187, "lon": -74.09476461866534},
                layers= [
                    {
                        "source": geo_bta,
                        "type": "line",
                        "color": "black",
                        "line": {"width": 2},
                    },
                    {
                        "source": geo_vias,
                        "type": "line",
                        "color": "#020081",
                        "line": {"width": 1.5},
                    }
                ],
            ),
        )
        
        figures_o_d[od_aux[od_temp]]=fig

    return figures_o_d

    
@app.callback(
    Output('store-graf-od-comp', 'data'),
    Input('store-val-inter-od', 'data'),
    Input('button-gen-mapa-od', 'n_clicks'),
    State('check_comp', 'value'),
    State('check_tipo_comp', 'value'),
    State('dd-v-anio-base', 'value'),
    State('dd-v-anio-comparacion', 'value'),
    State('dd-v-t-dia', 'value'),
    State('rs-h-i-od', 'value'),
    State('in-rang', 'value'), prevent_initial_call=True)
def genera_mapa_od_comp(datos_json, btn_gen, comparar, tipo_comp,
                        anio_b, anio_c, t_dia, horas_i, rango_input):
    
    if ctx.triggered_id != 'button-gen-mapa-od':
        raise PreventUpdate

    if not comparar:
        raise PreventUpdate

    if rango_input is None:
        if tipo_comp == "Absoluto":
            rango_input="-100, -50, -10, 0, 10, 50, 100"
        else:
            rango_input="-10, -5, -1, 0, 1, 5, 10"
    
    limites = [float(x.strip()) for x in rango_input.split(",")]

    label_limites = []
    for l in range(len(limites)):
        if l == 0:
            label = "<{}".format(limites[l])
        else:
            label = "[{};{})".format(limites[l-1],limites[l])
        label_limites.append(label)
    label_limites.append(">={}".format(limites[-1]))    
    
    datasets = json.loads(datos_json)    

    # Lee el año de interés
    df_o_b = pd.read_json(datasets['df_o_'+str(anio_b)[-2:]], orient='split')
    df_d_b = pd.read_json(datasets['df_d_'+str(anio_b)[-2:]], orient='split') 
    
    df_o_c = pd.read_json(datasets['df_o_'+str(anio_c)[-2:]], orient='split')
    df_d_c = pd.read_json(datasets['df_d_'+str(anio_c)[-2:]], orient='split')
    
    # Filtra las horas
    df_o_b = df_o_b[(df_o_b[c_h_i2].between(min(horas_i), max(horas_i))) & 
                    (df_o_b[c_tipo_dia]==t_dia)]
    df_o_b = df_o_b.groupby(by=[c_anio, c_o]).agg(viajes_o=("viajes_o","sum"))
    df_o_b.reset_index(inplace=True)
    df_d_b = df_d_b[(df_d_b[c_h_i2].between(min(horas_i), max(horas_i))) &
                    (df_d_b[c_tipo_dia]==t_dia)]
    df_d_b = df_d_b.groupby(by=[c_anio, c_d]).agg(viajes_d=("viajes_d","sum"))
    df_d_b.reset_index(inplace=True)
    
    df_o_c = df_o_c[(df_o_c[c_h_i2].between(min(horas_i), max(horas_i))) &
                    (df_o_c[c_tipo_dia]==t_dia)]
    df_o_c = df_o_c.groupby(by=[c_anio, c_o]).agg(viajes_o=("viajes_o","sum"))
    df_o_c.reset_index(inplace=True)
    df_d_c = df_d_c[(df_d_c[c_h_i2].between(min(horas_i), max(horas_i))) &
                    (df_d_c[c_tipo_dia]==t_dia)]
    df_d_c = df_d_c.groupby(by=[c_anio, c_d]).agg(viajes_d=("viajes_d","sum"))
    df_d_c.reset_index(inplace=True)
    
    
    df_o_diff = df_o_b.merge(df_o_c, how="left", on=[c_o])
    df_o_diff["anio_y"]=df_o_diff["anio_y"].fillna(anio_c)
    df_o_diff["viajes_o_y"]=df_o_diff["viajes_o_y"].fillna(0)
    
    df_d_diff = df_d_b.merge(df_d_c, how="left", on=[c_d])
    df_d_diff["anio_y"]=df_d_diff["anio_y"].fillna(anio_c)
    df_d_diff["viajes_d_y"]=df_d_diff["viajes_d_y"].fillna(0)
    
    
    df_o_diff.insert(df_o_diff.shape[1], c_var_v, df_o_diff["viajes_o_y"]-df_o_diff["viajes_o_x"])
    df_d_diff.insert(df_d_diff.shape[1], c_var_v, df_d_diff["viajes_d_y"]-df_d_diff["viajes_d_x"])
    
    if tipo_comp == "Porcentaje":
        df_o_diff.insert(df_o_diff.shape[1], c_var_v_p, df_o_diff[c_var_v]*100/df_o_diff["viajes_o_x"])
        df_d_diff.insert(df_d_diff.shape[1], c_var_v_p, df_d_diff[c_var_v]*100/df_d_diff["viajes_d_x"])
        df_o_diff[c_var_v_p] = df_o_diff[c_var_v_p].round(2) 
        df_d_diff[c_var_v_p] = df_d_diff[c_var_v_p].round(2)    
    
        df_o_diff['viajes_rango'] = df_o_diff[c_var_v_p].apply(lambda x: np.searchsorted(limites, x, side="right"))
        df_d_diff['viajes_rango'] = df_d_diff[c_var_v_p].apply(lambda x: np.searchsorted(limites, x, side="right"))
        valor_hover = c_var_v_p
    
    if tipo_comp == "Absoluto":
        df_o_diff['viajes_rango'] = df_o_diff[c_var_v].apply(lambda x: np.searchsorted(limites, x, side="right"))
        df_d_diff['viajes_rango'] = df_d_diff[c_var_v].apply(lambda x: np.searchsorted(limites, x, side="right"))
        valor_hover = c_var_v
    

    df_od = [df_o_diff, df_d_diff]
    cols_o_d = [c_o, c_d]
    od_aux = ["Origen","Destino"]

    escala_colores = [((0.0, px.colors.sequential.Plasma_r[grupo]),
                       (1.0, px.colors.sequential.Plasma_r[grupo])) 
                  for grupo in range(len(label_limites))]

    figures_o_d = dict()

    for od_temp in range(len(od_aux)):
        df_anio_temp = df_od[od_temp]
        fig = go.Figure()
        
        if len(df_anio_temp) > 0:
            for grupo in range(len(label_limites)):                
                df_trace = df_anio_temp[df_anio_temp['viajes_rango'] == grupo]    
                fig.add_choroplethmapbox(geojson=geo_zat,
                                          locations=df_trace[cols_o_d[od_temp]],
                                          z=df_trace[valor_hover],
                                          featureidkey="properties.ID",
                                          showlegend=True,
                                          name=label_limites[grupo],
                                          colorscale=escala_colores[grupo],
                                          showscale=False,)
    
            fig.update_layout(
                title=dict(text="Comparación del " + od_aux[od_temp].lower() + 
                           " entre " + str(anio_b) + " y " + str(anio_c)),
                margin=dict(l=4, r=4, t=5, b=3),
                mapbox=dict(
                    style='carto-positron',
                    zoom=8,
                    center={"lat": 4.657946861376187, "lon": -74.09476461866534},
                    layers= [
                        {
                            "source": geo_bta,
                            "type": "line",
                            "color": "black",
                            "line": {"width": 2},
                        },
                        {
                            "source": geo_vias,
                            "type": "line",
                            "color": "#020081",
                            "line": {"width": 1.5},
                        }
                    ],
                ),
            )
        figures_o_d[od_aux[od_temp]]=fig

    return figures_o_d

# Partición modal
@app.callback(
    Output('gr-part-mod', 'children'),    
    Input('store-graf-part-mod', 'data'),
    Input('tabs-part-mod', "active_tab"), prevent_initial_call=True)
def render_part_modal(grafs, active_tab):
        
    if active_tab == "tab-part-mod-hab":
        return dcc.Graph(figure=grafs["lab"])
    elif active_tab == "tab-part-mod-sab":
        return dcc.Graph(figure=grafs["sab"])
    elif active_tab == "tab-part-mod-dom":
        return dcc.Graph(figure=grafs["dom"])
    
# Hora de inicio
@app.callback(
    Output('gr-h-i', 'children'),    
    Input('store-graf-h-i', 'data'),
    Input('tabs-h-i', "active_tab"), prevent_initial_call=True)
def render_h_i(grafs, active_tab):        
    if active_tab == "tab-h-i-hab":
        return dcc.Graph(figure=grafs["lab"])
    elif active_tab == "tab-h-i-sab":
        return dcc.Graph(figure=grafs["sab"])
    elif active_tab == "tab-h-i-dom":
        return dcc.Graph(figure=grafs["dom"])
    
# Distancia de los viajes
@app.callback(
    Output('gr-dist', 'children'),    
    Input('store-graf-dist', 'data'),
    Input('tabs-distancia', "active_tab"), prevent_initial_call=True)
def render_dist(grafs, active_tab):        
    if active_tab == "tab-dist-hab":
        return dcc.Graph(figure=grafs["lab"])
    elif active_tab == "tab-dist-sab":
        return dcc.Graph(figure=grafs["sab"])
    elif active_tab == "tab-dist-dom":
        return dcc.Graph(figure=grafs["dom"])
    
@app.callback(
    Output('store-graf-part-mod', 'data'),
    Output('store-graf-h-i', 'data'),
    Output('store-graf-dist', 'data'),
    State('dd-o', 'value'),
    State('dd-d', 'value'),
    State('dd-prop', 'value'),
    Input('button-filt-data', 'n_clicks'))
def genera_grafs(origenes, destinos, propositos, btn_filtrar):
    
    if btn_filtrar is None:
        raise PreventUpdate
        
    if df_part0 is None or df_h_i0 is None or df_dist0 is None:
        raise PreventUpdate
        
    test_o_part = df_part0[c_o] >=  0
    test_d_part = df_part0[c_d] >=  0
    test_prop_part = df_part0[c_prop].isin(prop_val)
    
    test_o_h_i = df_h_i0[c_o] >=  0
    test_d_h_i = df_h_i0[c_d] >=  0
    test_prop_h_i = df_h_i0[c_prop].isin(prop_val)
    
    test_o_dist = df_dist0[c_o] >=  0
    test_d_dist = df_dist0[c_d] >=  0
    test_prop_dist = df_dist0[c_prop].isin(prop_val)
    
    if origenes is not None:
        if not isinstance(origenes,list):
            origenes=[origenes]            
        if "Todas" not in origenes:
            test_o_part = df_part0[c_o].isin(origenes)
            test_o_h_i = df_h_i0[c_o].isin(origenes)
            test_o_dist = df_dist0[c_o].isin(origenes)
            
    if destinos is not None:
        if not isinstance(destinos,list):
            destinos=[destinos]            
        if "Todas" not in destinos:
            test_d_part = df_part0[c_d].isin(destinos)
            test_d_h_i = df_h_i0[c_d].isin(destinos)
            test_d_dist = df_dist0[c_d].isin(destinos)
            
    if propositos is not None:
        if not isinstance(propositos,list):
            propositos=[propositos]            
        test_prop_part = df_part0[c_prop].isin(propositos)
        test_prop_h_i = df_h_i0[c_prop].isin(propositos)
        test_prop_dist = df_dist0[c_prop].isin(propositos)

    df_part_filt = df_part0[(test_o_part) & (test_d_part) & (test_prop_part)]    
    df_part = df_part_filt.groupby(by=[c_anio, c_tipo_dia, c_modo])\
    .agg(viajes_modo=(c_viajes,"sum"))
    df_part.reset_index(inplace=True)    
    df_part.insert(0, c_anio+"2", df_part[c_anio].astype(str))   
    
    df_h_i_filt = df_h_i0[(test_o_h_i) & (test_d_h_i) & (test_prop_h_i)]    
    df_hi = df_h_i_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, c_h_i])\
    .agg(viajes_h_i=(c_viajes,"sum"))
    df_hi.reset_index(inplace=True)
    
    
    df_dist_filt = df_dist0[(test_o_dist) & (test_d_dist) & (test_prop_dist)]    
    df_dist = df_dist_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, c_rango_dist])\
    .agg(viajes_dist=(c_viajes,"sum"))
    df_dist.reset_index(inplace=True)     
    df_dist.insert(0, c_anio+"2", df_dist[c_anio].astype(str))
    
    figs_part = genera_part(df_part)
    figs_h_i = genera_h_i(df_hi)
    figs_dist = genera_dist(df_dist)
    
    return figs_part, figs_h_i, figs_dist
    
def genera_part(df_part):    
    figures_part_mod = dict()

    for t_dia in tipo_dia_dispo:
        df_part_temp = df_part[df_part[c_tipo_dia]==t_dia]
        
        fig = px.bar(df_part_temp,
                     x=c_modo,
                     y="viajes_modo",
                     labels={c_anio+"2": "Año",
                             c_modo: "Modo",
                             "viajes_modo": "Viajes"
                            },
                     color=c_anio+"2",
                     barmode="group",

                     # facet_row=c_modo, facet_row_spacing=0.3,
                     #category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_part[c_tipo_dia].unique()]},
                     custom_data = [c_anio, "viajes_modo"])

        fig.update_xaxes(            
            tickmode = 'array',
            tickvals = modo_dispo,
            ticktext = modo_dispo
            )
        
        fig.update_layout(
            title=dict(text="Distribución modal de un día " + 
                       [lv['label'] for lv in dd_tipo_dia if lv['value'] == t_dia][0].lower())
            ) 

         # Actualiza el hover tooltip
        fig.update_traces(hovertemplate="<br>".join([
                    "Año: %{customdata[0]}",
                    "Viajes: %{customdata[1]:,.0f}"
        ]))

        figures_part_mod[t_dia] = fig

    return figures_part_mod

def genera_h_i(df_hi):
    
    figures_h_i = dict()
    
    for t_dia in tipo_dia_dispo:
        d_h_i_temp = df_hi[df_hi[c_tipo_dia]==t_dia]
        if len(d_h_i_temp) > 0:
            fig = px.line(d_h_i_temp, x=c_h_i, y="viajes_h_i",
                          color=c_anio, markers=True,
                          labels={c_anio: "Año",
                                  c_tipo_dia:"Día",
                                  c_h_i: "Hora de inicio",
                                  c_modo: "Modo",
                                  "viajes_h_i": "Viajes"
                                 },
                          facet_row=c_modo, facet_row_spacing=0.3,
                          category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_hi[c_tipo_dia].unique()]},
                          custom_data = [c_anio, "viajes_h_i"])
    
            fig.update_xaxes(
                tickmode = 'array',
                tickvals = sorted(df_hi[c_h_i].unique()),
                ticktext = horas_dispo
                )
            
            fig.update_layout(
                title=dict(text="Hora de inicio de los viajes de un día " +
                           [lv['label'] for lv in dd_tipo_dia if lv['value'] == t_dia][0].lower())
                )
    
            # Actualiza el hover tooltip
            fig.update_traces(hovertemplate="<br>".join([
                        "Año: %{customdata[0]}",
                        "Viajes: %{customdata[1]:,.0f}"
            ]))
        else:
            fig = go.Figure()
        
        figures_h_i[t_dia] = fig

    return figures_h_i


def genera_dist(df_dist):
    
    figures_dist = dict()
    
    for t_dia in tipo_dia_dispo:
        df_dist_temp = df_dist[df_dist[c_tipo_dia]==t_dia]
        if len(df_dist_temp) > 0:
            fig = px.bar(df_dist_temp, x=c_rango_dist, y="viajes_dist",
                         color=c_anio+"2",
                         barmode="group",
                         labels={c_anio+"2": "Año",
                                 c_tipo_dia:"Día",
                                 c_rango_dist: "Distancia",
                                 c_modo: "Modo",
                                 "viajes_dist": "Viajes"
                                },
                         facet_row=c_modo, facet_row_spacing=0.3,
                         category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_dist[c_tipo_dia].unique()],
                                          c_rango_dist:rangos_dist},
                         custom_data = ["viajes_dist", c_rango_dist])
    
            fig.update_layout(
                title=dict(text="Distancia de los viajes de un día "  + 
                           [lv['label'] for lv in dd_tipo_dia if lv['value'] == t_dia][0].lower())
                )
            
            # Actualiza el hover tooltip
            fig.update_traces(hovertemplate="<br>".join([
                        "Viajes: %{customdata[0]:,.0f}",
                        "Dist: %{customdata[1]}"
            ]))
            
            # fig.update_layout(height=700)
        else:
            fig = go.Figure()
        
        figures_dist[t_dia] = fig
    
    return figures_dist

 
@app.callback(
    Output('dd-v-anio', 'disabled'),
    Output('dd-v-anio-base', 'disabled'),
    Output('dd-v-anio-comparacion', 'disabled'),
    Output('check_tipo_comp', 'options'),
    Input('check_comp', 'value'))
def genera_dd_v_anio(comparar):  
    if comparar:
        return True, False, False, \
                [{'label': 'Absoluto', 'value': 'Absoluto', 'disabled': False},
                 {'label': 'Porcentaje', 'value': 'Porcentaje', 'disabled': False}]
    else:   
        return False, True, True, \
        [{'label': 'Absoluto', 'value': 'Absoluto', 'disabled': True},
            {'label': 'Porcentaje', 'value': 'Porcentaje', 'disabled': True}]
    
    
@app.callback(
    Output('dd-v-anio-comparacion', 'options'),
    State('dd-v-anio-base', 'disabled'),
    Input('dd-v-anio-base', 'value'), prevent_initial_call=True)
def genera_v_anio_comp(anio_b_des, anio_base):
    if anio_b_des:
        PreventUpdate
    if anio_base is None:
        PreventUpdate
    elif anio_base is not None:
        comp = [a for a in anios_dispo if a > anio_base]
        if len(comp) > 0:
            return comp
        else:
            return [-1]
    
# @app.callback(
#     Output('in-rang', 'value'),
#     Input('check_comp', 'value'),
#     Input('check_tipo_comp', 'value'))
# def ajustar_rangos_mapa(comparar, tipo_comp):
#     if not comparar:
#         return "100, 500, 1000, 2000"    
#     else:
#         if tipo_comp == "Absoluto":
#             return "-100, -50, -10, 0, 10, 50, 100"
#         elif tipo_comp == "Porcentaje":
#             return "-10, -5, -1, 0, 1, 5, 10"
    

@app.callback(
    Output('button-gen-mapa-od', 'disabled'),
    Input('button-filt-data', 'n_clicks'),
    Input('store-val-inter-od', 'data'))
def activa_butt_gen_mapa(btn_filtrar, datos_json):    
    if btn_filtrar is None:
        return True
    if ctx.triggered_id == 'store-val-inter-od':
        return False 

# Ejecuta la app
if __name__ == '__main__':
    # hot-reloading: La app cambia automáticamente con cambios en el código
    # Para desactivar esto, cambiar el parám. por dev_tools_hot_reload=False
    app.run_server(debug=True) 
