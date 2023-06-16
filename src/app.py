import json
from jupyter_dash import JupyterDash # Change Dash for JupyterDash
from dash import Dash
from dash import dcc # For rendering interactive graph
from dash import html # For using html for app layout
from dash import callback, Input, Output # To work with callback 
from dash import dash_table # Display data inside of a Dash DataTable
import numpy as np
import pandas as pd
import pickle
import plotly.graph_objects as go
import plotly.express as px # Build interactive graphs

# Base de datos
with open('odmatrix_completa.pickle', 'rb') as handle:
    df = pickle.load(handle)
    
# ZATs
with open('BTA_ZAT.geojson') as jsonfile:
    geo_zat = json.load(jsonfile)
    
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
c_dist = "distancia"
c_res = "residencia"
c_prop = "proposito"
c_modo = "modo"
c_viajes = "viajes"
c_prof = "profesional"

# Opciones generales
anios_dispo = sorted(df[c_anio].unique())
# ToDo arreglar para que pueda leer todos los meses del año
meses_dispo = ["mar", "oct"]
meses_dispo_label = ["Marzo", "Octubre"]
dd_meses = [{"label":x, "value":y} for x,y in zip(meses_dispo_label, meses_dispo)]
tipo_dia_dispo = sorted(df[c_tipo_dia].unique())
dd_tipo_dia = [{"label":"Hábil", "value":"lab"}, {"label":"Sábado", "value":"sab"}, {"label":"Domingo", "value":"dom"}]
horas_dispo = sorted([x.replace("P","") for x in df[c_h_i].unique()])
dd_horas=[{"label":x+":00", "value":"P"+x} for x in horas_dispo]
prop_val = ['HBO','HBW','HBEdu','NHB']
prop_dispo = ["Otro", "Trabajo", "Educación", "No basado en el hogar"]
dd_prop =  [{"label":x, "value":y} for x,y in zip(prop_dispo, prop_val)]
prof_dispo = df[c_prof].unique()
zat_o_dispo = sorted(df[c_o].unique())
zat_d_dispo = sorted(df[c_d].unique())
modo_dispo = df[c_modo].dropna().unique()

# # Agrupación partición modal
df_part = df.groupby(by=[c_anio, c_mes, c_tipo_dia, c_modo]).agg(viajes_modo=(c_viajes,"sum"))
df_part.reset_index(inplace=True)
# Agrupación hora de inicio
df_hi = df.groupby(by=[c_anio, c_mes, c_tipo_dia, c_modo, c_h_i]).agg(viajes_h_i=(c_viajes,"sum"))
df_hi.reset_index(inplace=True)
# Agrupación distancia
rangos_dist = ["[0-0.5)", "[0.5-1)", "[1-2)", "[2-5)", "[5-10)", "[10-20)" "[20-50)","+50"]
df_dist = df.groupby(by=[c_anio, c_mes, c_tipo_dia, c_modo,"rango_dist"]).agg(viajes_dist=(c_viajes,"sum"))
df_dist.reset_index(inplace=True)
# Agrupación OD
df_o = df.groupby(by=[c_anio, c_mes, c_tipo_dia, c_modo, c_o]).agg(viajes_o=("viajes","sum"))
df_o.reset_index(inplace=True)

df_d = df.groupby(by=[c_anio, c_mes, c_tipo_dia, c_modo, c_d]).agg(viajes_d=("viajes","sum"))
df_d.reset_index(inplace=True)


rangos_dist = ["[0-0.5)", "[0.5-1)", "[1-2)", "[2-5)", "[5-10)", "[10-20)" "[20-50)","+50"]

# Inicializa la app
# ToDo: change JupyterDash to Dash
app = JupyterDash(__name__)

# # Base de datos
# with open('odmatrix_completa.pickle', 'rb') as handle:
#     df = pickle.load(handle)

## Apariencia
app.layout = html.Div(style={'backgroundColor': colores['fondo']}, children=[
    
# Encabezado
    # Título
    html.Div([
        html.Header(
            children='Indicadores de movilidad urbana en Bogotá',
            style={
                'height': 40,
                'fontSize': 30,
                'backgroundColor': colores['fondo_tit'],
                'textAlign': 'center',
                'padding': '15px 0',
                'color': colores['text'],
                'width': '100%', 
                'display': 'inline-block'
            }),
        html.Img(src=app.get_asset_url('WBG_Logo.png'), 
                 style={'height': 60,'width': '15%','display': 'inline-block',
                        'position':'absolute', 'left':0})
    ], style={'position': 'relative'}),
    
# Filtros generales
     html.Div([
         # Tiempo
         html.Div([
             html.H4("Año", style={'marginBottom':5}),
             dcc.Dropdown(options=anios_dispo,
                          value=anios_dispo,
                          multi=True,
                          placeholder="Año",
                          id='dd-anio')],
                 style={'width': '20%','display': 'inline-block', 'marginRight':10}),
         
         html.Div([
             html.H4("Mes", style={'marginBottom':5}),
             dcc.Dropdown(options=dd_meses,
                          value="oct",
                          multi=True,
                          placeholder="Mes",
                          id='dd-mes')],
             style={'width': '20%', 'display': 'inline-block', 'marginRight':10}),

         html.Div([
             html.H4("Tipo de día", style={'marginBottom':5}),
             dcc.Dropdown(options=dd_tipo_dia,
                           value="lab",
                           multi=True,
                           placeholder="Tipo de día",
                           id='dd-tipo-dia')],
             style={'width': '20%', 'display': 'inline-block', 'marginRight':10}),
        
         html.Div([
             html.H4("Hora", style={'marginBottom':5}),
             dcc.Dropdown(options=[{"label":"Todas", "value":"Todas"}] + dd_horas,
                                value = "Todas",
                                multi=True,
                                placeholder="Hora de inicio",
                                id='dd-h-i')],
                  style={'width': '20%','display': 'inline-block'})
     ], style={'marginBottom':10}),
    
    # OD + modo
    html.Div([
        html.Div([
             html.H4("ZAT origen", style={'marginBottom':5}),
             dcc.Dropdown(options=["Todas"] + zat_o_dispo,
                                value = "Todas",
                                multi=True,
                                placeholder="ZAT origen",
                                id='dd-o')],
            style={'width': '30%', 'display': 'inline-block', 'marginRight':10}),

         html.Div([
             html.H4("ZAT destino", style={'marginBottom':5}),
             dcc.Dropdown(options=["Todas"] + zat_d_dispo,
                                value = "Todas",
                                multi=True,
                                placeholder="ZAT destino",
                                id='dd-d')],
             style={'width': '30%', 'display': 'inline-block', 'marginRight':10}),

         html.Div([
             html.H4("Modo", style={'marginBottom':5}),
             dcc.Dropdown(options=modo_dispo,
                                value=modo_dispo,
                           multi=True,
                           placeholder="Modo",
                           id='dd-modo')],
             style={'width': '30%', 'display': 'inline-block', 'marginRight':10})
     ], style={'marginBottom':10}),
    
    # Prop y prof
    html.Div([             
             html.Div([
                 html.H4("Propósito", style={'marginBottom':5}),
                 dcc.Dropdown(options=dd_prop,
                               value=prop_val,
                               multi=True,
                               placeholder="Propósito",
                               id='dd-prop')],
                 style={'width': '20%', 'display': 'inline-block', 'marginRight':10}),
             
             html.Div([
                 html.H4("Profesional?", style={'marginBottom':5}),
                 dcc.Dropdown(options=prof_dispo,
                               value="No",
                               multi=True,
                               placeholder="Profesional?",
                               id='dd-prof')],
                 style={'width': '10%', 'display': 'inline-block'})
         ], style={'marginBottom':20}),
    
    # Almacena las tablas agregadas intermedias
    html.Div([
        dcc.Store(id='store-val-inter')
    ]),   
    
    
# Viajes por zona
    html.Div([
        html.Div([
            html.Hr(),
            html.H3("Viajes por ZAT"),
            html.H4("Rangos de viajes", style={'marginBottom':5}),
            html.Div([
                dcc.Input(type="text",
                      value="100,500,1000,2000,5000,10000",
                      placeholder="Rangos, separados por comas (e.g. 0, 100, 1000, 10000)",
                      debounce=True,
                      id="in-rang", style={'width':"80%"})],
                      style={'marginBottom':5, 'marginRigth':10, 'display': 'inline-block', 'width': '20%'}
                  ),
            html.Div([
                html.P(["Ingresa un conjunto de número, separados por comas, \
                   para definir los rangos (cerrados a la izquierda, abiertos a la derecha) \
                   de agrupación de los viajes" , html.Br(),
                   "(e.g. 100, 500, 2000 creará los rangos [0,100), [100, 500), [500, 2000) y [2000, inf))"])],
                   style={'marginBottom':5, 'display': 'inline-block', 'fontSize':14}
            )
        ]),
        
        html.Div([
            html.Div([
                html.Div([
                    html.H4(id="tit-od-1")
                ], style={'fontSize':20,'textAlign': 'center','marginBottom':5}),
                html.Div([
                    html.H5(children="Origen")
                ], style={'textAlign': 'left','marginBottom':5}),
                dcc.Graph(id="gr-o-1"),
                html.Div([
                    html.H5(children="Destino")
                ], style={'textAlign': 'left','marginBottom':5}),
                dcc.Graph(id="gr-d-1"),
                dcc.Slider(
                    df[c_anio].min(),
                    df[c_anio].max(),
                    step=None,
                    value=df[c_anio].min(),
                    marks={str(anio): str(anio) for anio in df[c_anio].unique()},
                    id='slider-anio-1'
                )
            ], style={'width': '48%','display': 'inline-block'}),
            html.Div([
                html.Div([
                    html.H4(id="tit-od-2")
                ], style={'fontSize':20,'textAlign': 'center','marginBottom':5}),
                html.Div([
                    html.H5(children="Origen")
                ], style={'textAlign': 'left','marginBottom':5}),
                dcc.Graph(id="gr-o-2"),
                html.Div([
                    html.H5(children="Destino")
                ], style={'textAlign': 'left','marginBottom':5}),
                dcc.Graph(id="gr-d-2"),
                dcc.Slider(
                    df[c_anio].min(),
                    df[c_anio].max(),
                    step=None,
                    value=df[c_anio].max(),
                    marks={str(anio): str(anio) for anio in df[c_anio].unique()},
                    id='slider-anio-2'
                )
            ], style={'width': '48%', 'display': 'inline-block'})
        ])
        
    ]),
    
    html.Div([
        # Partición modal
        html.Hr(),        
        html.H3("Partición modal"),        
        html.Div([
            dcc.Graph(id='gr-part-modal')            
        ])       
    ]),
    
# Indicadores de tiempo       
    html.Div([
        html.Hr(),
        # Hora de inicio de los viajes modal
        html.H3("Hora de inicio"),
        html.Div([
            dcc.Graph(id='gr-h-i')            
        ]),       
    ]),
    
# Indicadores de distancia
    html.Div([
        html.Hr(),
        html.H3("Distancia"),
        # Distancia de viajes
        html.Div([
            dcc.Graph(id="gr-dist")
        ]),
    ])
    
])
# Fin apariencia


#################
## Interactividad
#################
# Filtrado y agregación de los datos
@callback(
    Output('store-val-inter', 'data'),    
    Input('dd-anio', 'value'),
    Input('dd-mes', 'value'),
    Input('dd-tipo-dia', 'value'),    
    Input('dd-h-i', 'value'),
    Input('dd-o', 'value'),
    Input('dd-d', 'value'),
    Input('dd-modo', 'value'),
    Input('dd-prop', 'value'),
    Input('dd-prof', 'value'))
def filtrar_datos(anios, meses, tipo_dias, horas, origenes, destinos,
            modos, propositos, profesional):
    if not isinstance(anios,list):
        anios=[anios]
    if not isinstance(meses,list):
        meses=[meses]
    if not isinstance(tipo_dias,list):
        tipo_dias=[tipo_dias]        
    if not isinstance(horas,list):
        horas=[horas]
    if not isinstance(origenes,list):
        origenes=[origenes]
    if not isinstance(destinos,list):
        destinos=[destinos]        
    if not isinstance(modos,list):
        modos=[modos]
    if not isinstance(propositos,list):
        propositos=[propositos]        
    if not isinstance(profesional,list):
        profesional=[profesional]

    if "Todas" not in horas:
        test_h_i = df[c_h_i].isin(horas)
    else:
        test_h_i = True
    if "Todas" not in origenes:
        test_o = df[c_o].isin(origenes)
    else:
        test_o = True
    if "Todas" not in destinos:
        test_d = df[c_d].isin(destinos)
    else:
        test_d = True
        
    test_anio = df[c_anio].isin(anios)
    test_mes = df[c_mes].isin(meses)
    test_tipo_dia = df[c_tipo_dia].isin(tipo_dias)
    test_modo = df[c_modo].isin(modos)
    test_prop = df[c_prop].isin(propositos)
    test_prof = df[c_prof].isin(profesional)
    
    df_filt = df[(test_anio) & (test_mes) &
                 (test_tipo_dia) & (test_h_i) &
                 (test_o) & (test_d) & (test_modo) &
                 (test_prop) & (test_prof)
                ]
    
    # Agrupación de los datos
    # Agrupación OD
    df_o = df_filt.groupby(by=[c_anio, c_o]).agg(viajes_o=(c_viajes,"sum"))
    df_o.reset_index(inplace=True)

    df_d = df_filt.groupby(by=[c_anio, c_mes, c_d]).agg(viajes_d=(c_viajes,"sum"))
    df_d.reset_index(inplace=True)
    # Partición modal
    df_part = df_filt.groupby(by=[c_anio, c_tipo_dia, c_modo]).agg(viajes_modo=(c_viajes,"sum"))
    df_part.reset_index(inplace=True)
    # Agrupación hora de inicio
    df_hi = df_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, c_h_i]).agg(viajes_h_i=(c_viajes,"sum"))
    df_hi.reset_index(inplace=True)
    # Agrupación distancia
    df_dist = df_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, "rango_dist"]).agg(viajes_dist=(c_viajes,"sum"))
    df_dist.reset_index(inplace=True)
    
    datasets = {
         'df_o': df_o.to_json(orient='split', date_format='iso'),
         'df_d': df_d.to_json(orient='split', date_format='iso'),
         'df_part': df_part.to_json(orient='split', date_format='iso'),
         'df_hi': df_hi.to_json(orient='split', date_format='iso'),
         'df_dist': df_dist.to_json(orient='split', date_format='iso'),        
     }

    return json.dumps(datasets) 


# OD
# Rango para mapa
@app.callback(
    Output('gr-o-1', 'figure'),
    Output('gr-d-1', 'figure'),
    Output('gr-o-2', 'figure'),
    Output('gr-d-2', 'figure'),
    Input('in-rang', 'value'),    
    Input('store-val-inter', 'data'),
    Input('slider-anio-1', 'value'),
    Input('slider-anio-2', 'value'))
def update_mapa_od(rango_input, datos_json, anio_1, anio_2):
    
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
    
    df_o = pd.read_json(datasets['df_o'], orient='split')
    df_d = pd.read_json(datasets['df_d'], orient='split')
    
    df_o['viajes_rango'] = df_o['viajes_o'].apply(lambda x: np.searchsorted(limites, x, side="right"))
    df_d['viajes_rango'] = df_d['viajes_d'].apply(lambda x: np.searchsorted(limites, x, side="right"))
    
    df_od = [df_o, df_d]
    cols_o_d = [c_o, c_d]
    
    escala_colores = [((0.0, px.colors.sequential.Plasma_r[grupo]), (1.0, px.colors.sequential.Plasma_r[grupo])) 
                 for grupo in range(len(label_limites))]
    
    figures_o_d = []
    
    for anio_temp in [anio_1, anio_2]:
        for od_temp in range(len(["O","D"])):
            fig = go.Figure()
            for grupo in range(len(label_limites)):                
                df_trace = df_od[od_temp][(df_od[od_temp][c_anio] == anio_temp) &
                                          (df_od[od_temp]['viajes_rango'] == grupo)]    
                fig.add_choroplethmapbox(geojson=geo_zat,
                                         locations=df_trace[cols_o_d[od_temp]],
                                         z=df_trace['viajes_rango'],
                                         featureidkey="properties.ID",
                                         showlegend=True,
                                         name=label_limites[grupo],
                                         colorscale=escala_colores[grupo],
                                         showscale=False)

            fig.update_layout(
                mapbox=dict(
                    style='carto-positron',
                    zoom=9,
                    center={"lat": 4.657946861376187, "lon": -74.09476461866534},
                ),
            )

            figures_o_d.append(fig)
        
    return figures_o_d[0], figures_o_d[1], figures_o_d[2], figures_o_d[3]

# Títulos subgraficos OD
@app.callback(
    Output('tit-od-1', 'children'),    
    Input('slider-anio-1', 'value')
)
def update_titulos_mapa_od(anio1):
    return str(anio1)

@app.callback(
    Output('tit-od-2', 'children'),    
    Input('slider-anio-2', 'value')
)
def update_titulos_mapa_od(anio2):
    return str(anio2)
    

# Partición modal
@app.callback(
    Output('gr-part-modal', 'figure'),    
    Input('store-val-inter', 'data'))
def update_part_modal(datos_json):
    
    datasets = json.loads(datos_json)
    
    df_part = pd.read_json(datasets['df_part'], orient='split')    

    fig = px.bar(df_part,
                 x=c_anio,
                 y="viajes_modo",
                 title="Partición modal",
                 labels={c_anio: "Año",
                         c_modo: "Modo",
                         "viajes_modo": "Viajes"
                        },
                 
                 facet_row=c_modo, facet_row_spacing=0.15, facet_col=c_tipo_dia,
                 category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_part[c_tipo_dia].unique()]},
                 custom_data = [c_anio, "viajes_modo"])
    
    fig.update_xaxes(            
        tickmode = 'array',
        tickvals = list(range(df_part[c_anio].min(),df_part[c_anio].max()+1)),
        ticktext = list(range(df_part[c_anio].min(),df_part[c_anio].max()+1))
        )
    
     # Actualiza el hover tooltip
    fig.update_traces(hovertemplate="<br>".join([
                "Año: %{customdata[0]}",
                "Viajes: %{customdata[1]:,.0f}"
    ]))
    
    return fig

# Hora de inicio
@app.callback(
    Output('gr-h-i', 'figure'),    
    Input('store-val-inter', 'data'))
def update_h_i(datos_json):
    
    datasets = json.loads(datos_json)
    
    df_hi = pd.read_json(datasets['df_hi'], orient='split')   

    fig = px.line(df_hi, x=c_h_i, y="viajes_h_i",
                  color=c_anio, markers=True,
                  title="Número de viajes por hora de inicio",
                  labels={c_anio: "Año",
                          c_tipo_dia:"Día",
                          c_h_i: "Hora de inicio",
                          c_modo: "Modo",
                          "viajes_h_i": "Viajes"
                         },
                  facet_row=c_modo, facet_row_spacing=0.15, facet_col=c_tipo_dia,
                  category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_hi[c_tipo_dia].unique()]},
                  custom_data = [c_anio, "viajes_h_i"])
    
    fig.update_xaxes(
        tickmode = 'array',
        tickvals = sorted(df_hi[c_h_i].unique()),
        ticktext = horas_dispo
        )

    # Actualiza el hover tooltip
    fig.update_traces(hovertemplate="<br>".join([
                "Año: %{customdata[0]}",
                "Viajes: %{customdata[1]:,.0f}"
    ]))

    return fig

# Distancia de los viajes
@app.callback(
    Output('gr-dist', 'figure'),    
    Input('store-val-inter', 'data'))
def update_dist(datos_json):
    
    datasets = json.loads(datos_json)    
    df_dist = pd.read_json(datasets['df_dist'], orient='split') 
    
    df_dist.insert(0, c_anio+"2", df_dist[c_anio].astype(str))
    df_dist.insert(0, "viajes_dist_int", -(-df_dist["viajes_dist"]//2))
    
    fig = px.bar(df_dist, x="rango_dist", y="viajes_dist",
                 color=c_anio+"2", barmode="group",
                 title="Distribución del número de viajes por distancia",
                 labels={c_anio+"2": "Año",
                         c_tipo_dia:"Día",
                         "rango_dist": "Distancia",
                         c_modo: "Modo",
                         "viajes_dist": "Viajes"
                        },
                 facet_row=c_modo, facet_row_spacing=0.15, facet_col=c_tipo_dia,
                 category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_dist[c_tipo_dia].unique()],
                             "rango_dist":rangos_dist},
                 custom_data = [c_anio, "viajes_dist", "rango_dist"])

    # Actualiza el hover tooltip
    fig.update_traces(hovertemplate="<br>".join([
                "Viajes: %{customdata[1]:,.0f}",
                "Dist: %{customdata[2]}"
    ]))
    
    return fig


# Ejecuta la app
if __name__ == '__main__':
    # hot-reloading: La app cambia automáticamente con cambios en el código
    # Para desactivar esto, cambiar el parám. por dev_tools_hot_reload=False
    app.run_server(debug=True) 
