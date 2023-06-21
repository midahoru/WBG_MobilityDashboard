import json
from dash import Dash, dcc, html, callback, Input, Output, ctx 
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Base de datos
df = pd.read_parquet("../assets/odmatrix_gped_no_pro.parquet")
    
# ZATs
with open('../assets/BTA_ZAT.geojson') as jsonfile:
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
c_rango_dist="rango_dist"

# Opciones generales
anios_dispo = sorted(df[c_anio].unique())

# ToDo arreglar para que pueda leer todos los meses del año
meses_dispo = ["mar", "oct"]
meses_dispo_label = ["Marzo", "Octubre"]
dd_meses = [{"label":x, "value":y} for x,y in zip(meses_dispo_label, meses_dispo)]

tipo_dia_dispo = sorted(df[c_tipo_dia].unique())
dd_tipo_dia = [{"label":"Laborable", "value":"lab"}, {"label":"Sábado", "value":"sab"}, {"label":"Domingo", "value":"dom"}]

horas_dispo = sorted([x.replace("P","") for x in df[c_h_i].unique()])
dd_horas=[{"label":x+":00", "value":"P"+x} for x in horas_dispo]

zat_o_dispo = sorted(df[c_o].unique())
zat_d_dispo = sorted(df[c_d].unique())

modo_dispo = df[c_modo].dropna().unique()

prop_val = ['HBO','HBW','HBEdu','NHB']
prop_dispo = ["Otro", "Trabajo", "Educación", "No basado en el hogar"]
dd_prop =  [{"label":x, "value":y} for x,y in zip(prop_dispo, prop_val)]

rangos_dist = ["[0-0.5)", "[0.5-1)", "[1-2)", "[2-5)", "[5-10)", "[10-20)", "[20-50)","+50"]

# Inicializa la app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

encabezado = dbc.Row([
    dbc.Col([
        html.Div([
        html.Header(children='Indicadores de movilidad urbana en Bogotá',
                style={'height': 60, 'fontSize': 35, 'backgroundColor': colores['fondo_tit'],
                    'textAlign': 'center', #'padding': '15px 0', #'color': colores['text'],
                    'width': '100%', 'display': 'inline-block'
                      },
                   className="bg-primary text-white p-2 mb-2 text-center"),
        html.Img(src=app.get_asset_url('WBG_Logo.png'), 
                 style={'height': 60,'width': '15%','display': 'inline-block',
                        'position':'absolute', 'left':0})],
        style={'position': 'relative'})    
    ])    
], className="pb-3 rounded") # Fin Row encabezado

filtros_1 = dbc.Row([
    # ZAT O
    dbc.Col([
        html.P("ZAT origen", style={'marginBottom':5}),
        dcc.Dropdown(options=["Todas"] + zat_o_dispo,
                     value = "Todas",
                     multi=True,
                     placeholder="ZAT origen",
                     id='dd-o'),
    ], width=6, className="fs-6"
    ),    
    # ZAT D
    dbc.Col([
        html.P("ZAT destino", style={'marginBottom':5}),
        dcc.Dropdown(options=["Todas"] + zat_d_dispo,
                     value = "Todas",
                     multi=True,
                     placeholder="ZAT destino",
                     id='dd-d'),
    ], width=6, className="fs-6"
    )
]) # Fin Row filtros 1

filtros_2 = dbc.Row([
    # Mes
    dbc.Col([
        html.P("Mes", style={'marginBottom':5}),
        dcc.Dropdown(options=dd_meses,
                     value="oct",
                     multi=False,
                     placeholder="Mes",
                     id='dd-mes'),
    ], width=2, className="fs-6"
    ),
    # Propósito
    dbc.Col([
        html.P("Propósito", style={'marginBottom':5}),
        dcc.Dropdown(options=dd_prop,
                     value=prop_val,
                     multi=True,
                     placeholder="Propósito",
                     id='dd-prop'),
    ], width={"size": 5}, className="fs-6"
    ), # Fin Col Propósito
    # Filtrar
    dbc.Col([
        html.P("", style={'marginBottom':5}),
        dbc.Button(
            "Filtrar datos",
            color="primary",
            id="button-filt-data",
            className="fs-5",
        )        
    ], width={"size": 2, 'offset':2}, align="end") # Fin Col botón filtrar
    
])

# Filtros generales        
filtros = dbc.Card([
    filtros_1, filtros_2
], body=True,
    className="border border-secondary p-2"
) # Fin Card filtros


controles_od = dbc.Card([
    html.Div([
        dcc.Dropdown(options= anios_dispo,
                     value= 2021,
                     multi=False, #options, #value #disable
                     placeholder="Año",
                     disabled = False,
                     id='dd-v-anio')
    ]),
    
    html.Div([
        dcc.Checklist(
           options=[
               {'label': 'Comparar', 'value': 'Si'}
           ]
        )
    ]),
    
    html.Div([
        dcc.Dropdown(multi=False, #options, #value #disable
                     placeholder="Año base",
                     disabled = True,
                     id='dd-v-anio-base'),
        
        dcc.Dropdown(multi=False,
                     placeholder="Año de comparación",
                     disabled = True,
                     id='dd-v-anio-comparacion')
    ]),
    
    html.Div([
        dbc.Label("Rangos"),
        dcc.Input(type="text",
              value="100,500,1000,2000,5000,10000",
              placeholder="Rangos, separados por comas (e.g. 0, 100, 1000, 10000)",
              debounce=True,
              id="in-rang", style={'fontSize': 12, 'fontStyle': 'italic', "width":"100%"})
    ]),
    
    
], body=True, className="font-ligth fs-6") # Fin Card controles viajes OD

# Viajes por ZAT
gr_od = dbc.Card([
    dbc.Row([
        html.H3("Viajes por ZAT", className="bg-info p-1 text-white rounded-top")
    ]),
    dbc.Row([
        dbc.Tabs(
            [
                dbc.Tab(label="Origen", tab_id="tab-v-o"),
                dbc.Tab(label="Destino", tab_id="tab-v-d"),
                dbc.Tab(label="Tasa de viajes", tab_id="tab-v-t"),

            ],
            id="tabs-v",
            active_tab="tab-v-o"
        ),
        html.Br(),
        dbc.Tabs(
            [
                dbc.Tab(label="Hábil", tab_id="tab-v-hab"),
                dbc.Tab(label="Sábado", tab_id="tab-v-sab"),
                dbc.Tab(label="Domingo", tab_id="tab-v-dom"),

            ],
            id="tabs-v-d",
            active_tab="tab-v-hab"
        )
    ]),
    dbc.Row([
        dbc.Col(controles_od, width=2),
        dbc.Col(id='gr-v')
    ]) 
],className="border order-light pt-2", body=True) # Fin Card viajes OD
    
# Partición modal
gr_part_mod = dbc.Card([
    dbc.Row([
        html.H3("Partición modal", className="bg-info p-1 text-white rounded-top")
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
], className="border order-light pt-2", body=True) # Fin Card partición modal

# Hora de inicio
gr_h_i = dbc.Card([
    dbc.Row([
        html.H3("Hora de inicio", className="bg-info p-1 text-white rounded-top")
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
], className="border order-light pt-2", body=True) # Fin Card hora de inicio

# Distancia
gr_dist = dbc.Card([
    dbc.Row([
        html.H3("Distancia", className="bg-info p-1 text-white rounded-top")
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
], className="border order-light pt-2", body=True) # Fin Card distancia



#############
## Apariencia
#############
sto_type = "memory" #local, session, memory
app.layout = dbc.Container([
    # Almacena las tablas agregadas intermedias
    dcc.Store(id='store-val-inter', storage_type=sto_type),
    # Almacena los mapas    
    dcc.Store(id='store-graf-od', storage_type=sto_type),
    # Almacena los gráficos
    dcc.Store(id='store-graf-part-mod', storage_type=sto_type),
    # Almacena los gráficos
    dcc.Store(id='store-graf-h-i', storage_type=sto_type),
    # Almacena los gráficos
    dcc.Store(id='store-graf-dist', storage_type=sto_type),
    encabezado,
    filtros,
    gr_od,
    gr_part_mod,
    gr_h_i,
    gr_dist    
], fluid=True) # Fin Container general
# Fin apariencia


#################
## Interactividad
#################
# Filtrado y agregación de los datos
@callback(
    Output('store-val-inter', 'data'),
    Input('dd-mes', 'value'),
    Input('dd-o', 'value'),
    Input('dd-d', 'value'),
    Input('dd-prop', 'value'),
    Input('button-filt-data', 'n_clicks'))
def filtrar_datos(meses, origenes, destinos, propositos, btn_filtrar):
    
    if btn_filtrar is None:
        raise PreventUpdate
    
    if ctx.triggered_id != 'button-filt-data':
        raise PreventUpdate
    
    if meses is not None:
        if not isinstance(meses,list):
            meses=[meses]
        test_mes = df[c_mes].isin(meses)
    else:
        test_mes = True

    if origenes is not None:
        if not isinstance(origenes,list):
            origenes=[origenes]

        if "Todas" not in origenes:
            test_o = df[c_o].isin(origenes)
        else:
            test_o = True
    else:
        test_o = True

    if destinos is not None:
        if not isinstance(destinos,list):
            destinos=[destinos]                
        if "Todas" not in destinos:
            test_d = df[c_d].isin(destinos)
        else:
            test_d = True
    else:
        test_d = True

    if propositos is not None:
        if not isinstance(propositos,list):
            propositos=[propositos]
        test_prop = df[c_prop].isin(propositos)
    else:
        test_prop = True

    df_filt = df[(test_mes) & (test_o) & (test_d) & (test_prop)]

    # Agrupación de los datos
    df_o = df_filt.groupby(by=[c_anio, c_tipo_dia, c_o])\
    .agg(viajes_o=(c_viajes,"sum"))
    df_o.reset_index(inplace=True)

    df_d = df_filt.groupby(by=[c_anio, c_tipo_dia, c_d])\
    .agg(viajes_d=(c_viajes,"sum"))
    df_d.reset_index(inplace=True)

    # Agrupación hora de inicio
    df_hi = df_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, c_h_i])\
    .agg(viajes_h_i=(c_viajes,"sum"))
    df_hi.reset_index(inplace=True)
    # Agrupación distancia
    df_dist = df_filt.groupby(by=[c_anio, c_tipo_dia, c_modo, c_rango_dist])\
    .agg(viajes_dist=(c_viajes,"sum"))
    df_dist.reset_index(inplace=True)
    # Partición modal
    df_part = df_hi.groupby(by=[c_anio, c_tipo_dia, c_modo])\
    .agg(viajes_modo=("viajes_h_i","sum"))
    df_part.reset_index(inplace=True) 

    datasets = {
         'df_o': df_o.to_json(orient='split', date_format='iso'),
         'df_d': df_d.to_json(orient='split', date_format='iso'),
         'df_part': df_part.to_json(orient='split', date_format='iso'),
         'df_hi': df_hi.to_json(orient='split', date_format='iso'),
         'df_dist': df_dist.to_json(orient='split', date_format='iso'),        
     }
    
    return json.dumps(datasets)

# Mapa
@app.callback(
    Output('gr-v', 'children'),    
    Input('store-graf-od', 'data'),
    Input('tabs-v', "active_tab"),
    Input('tabs-v-d', "active_tab"),
    Input('button-filt-data', 'n_clicks'), prevent_initial_call=True)
def render_mapa_od(grafs, active_tab_v, active_tab_d, btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
        
    if active_tab_v == "tab-v-o":
        if active_tab_d == "tab-v-hab":
            return dcc.Graph(figure=grafs[("Origen","lab")])
        elif active_tab_d == "tab-v-sab":
            return dcc.Graph(figure=grafs[("Origen","sab")])
        elif active_tab_d == "tab-v-dom":
            return dcc.Graph(figure=grafs[("Origen","dom")])
    elif active_tab_v == "tab-v-d":
        if active_tab_d == "tab-v-hab":
            return dcc.Graph(figure=grafs[("Destino","lab")])
        elif active_tab_d == "tab-v-sab":
            return dcc.Graph(figure=grafs[("Destino","sab")])
        elif active_tab_d == "tab-v-dom":
            return dcc.Graph(figure=grafs[("Destino","dom")])
    elif active_tab_v == "tab-v-t":
        if active_tab_d == "tab-v-hab":
            return dcc.Graph(figure=grafs[("Tasa","lab")])
        elif active_tab_d == "tab-v-sab":
            return dcc.Graph(figure=grafs[("Tasa","sab")])
        elif active_tab_d == "tab-v-dom":
            return dcc.Graph(figure=grafs[("Tasa","dom")])
        
    
@app.callback(
    Output('store-graf-od', 'data'),
    Input('store-val-inter', 'data'),
    Input('dd-v-anio', 'value'),
    Input('in-rang', 'value'),
    Input('button-filt-data', 'n_clicks'), prevent_initial_call=True)
def genera_mapa_od(datos_json, anio, rango_input, btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
    
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
    od_aux = ["Origen","Destino"]

    escala_colores = [((0.0, px.colors.sequential.Plasma_r[grupo]), (1.0, px.colors.sequential.Plasma_r[grupo])) 
                 for grupo in range(len(label_limites))]

    figures_o_d = dict()

    for t_dia in tipo_dia_dispo:
        for od_temp in range(len(od_aux)):
            df_anio_temp = df_od[od_temp][(df_od[od_temp][c_anio] == anio) &
                                          (df_od[od_temp][c_tipo_dia]==t_dia)]
            fig = go.Figure()
            for grupo in range(len(label_limites)):                
                df_trace = df_anio_temp[df_anio_temp['viajes_rango'] == grupo]    
                fig.add_choroplethmapbox(geojson=geo_zat,
                                         locations=df_trace[cols_o_d[od_temp]],
                                         z=df_trace['viajes_rango'],
                                         featureidkey="properties.ID",
                                         showlegend=True,
                                         name=label_limites[grupo],
                                         colorscale=escala_colores[grupo],
                                         showscale=False,)

            fig.update_layout(
                title=dict(text=od_aux[od_temp] + " " + str(anio)),
                mapbox=dict(
                    style='carto-positron',
                    zoom=9,
                    center={"lat": 4.657946861376187, "lon": -74.09476461866534},
                ),
            )
            figures_o_d[(od_aux[od_temp],t_dia)]=fig

    return figures_o_d

# Partición modal
@app.callback(
    Output('gr-part-mod', 'children'),    
    Input('store-graf-part-mod', 'data'),
    Input('tabs-part-mod', "active_tab"),
    Input('button-filt-data', 'n_clicks'), prevent_initial_call=True)
def render_part_modal(grafs, active_tab, btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
        if active_tab == "tab-part-mod-hab":
            return dcc.Graph(figure=grafs["lab"])
        elif active_tab == "tab-part-mod-sab":
            return dcc.Graph(figure=grafs["sab"])
        elif active_tab == "tab-part-mod-dom":
            return dcc.Graph(figure=grafs["dom"])
    
@app.callback(
    Output('store-graf-part-mod', 'data'),
    Input('store-val-inter', 'data'))
def genera_part_modal(datos_json):
    datasets = json.loads(datos_json)

    df_part = pd.read_json(datasets['df_part'], orient='split')

    figures_part_mod = dict()

    for t_dia in tipo_dia_dispo:

        fig = px.bar(df_part[df_part[c_tipo_dia]==t_dia],
                     x=c_anio,
                     y="viajes_modo",
                     title="Partición modal",
                     labels={c_anio: "Año",
                             c_modo: "Modo",
                             "viajes_modo": "Viajes"
                            },

                     facet_row=c_modo, facet_row_spacing=0.3,
                     #category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_part[c_tipo_dia].unique()]},
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

        figures_part_mod[t_dia] = fig

    return figures_part_mod

# Hora de inicio
@app.callback(
    Output('gr-h-i', 'children'),    
    Input('store-graf-h-i', 'data'),
    Input('tabs-h-i', "active_tab"),
    Input('button-filt-data', 'n_clicks'), prevent_initial_call=True)
def render_h_i(grafs, active_tab, btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
        
    if active_tab == "tab-h-i-hab":
        return dcc.Graph(figure=grafs["lab"])
    elif active_tab == "tab-h-i-sab":
        return dcc.Graph(figure=grafs["sab"])
    elif active_tab == "tab-h-i-dom":
        return dcc.Graph(figure=grafs["dom"])

@app.callback(
    Output('store-graf-h-i', 'data'),   
    Input('store-val-inter', 'data'))
def genera_h_i(datos_json):
    
    datasets = json.loads(datos_json)
    
    df_hi = pd.read_json(datasets['df_hi'], orient='split')
    
    figures_h_i = dict()
    
    for t_dia in tipo_dia_dispo:

        fig = px.line(df_hi[df_hi[c_tipo_dia]==t_dia], x=c_h_i, y="viajes_h_i",
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

        # Actualiza el hover tooltip
        fig.update_traces(hovertemplate="<br>".join([
                    "Año: %{customdata[0]}",
                    "Viajes: %{customdata[1]:,.0f}"
        ]))
        
        figures_h_i[t_dia] = fig

    return figures_h_i

# Distancia de los viajes
@app.callback(
    Output('gr-dist', 'children'),    
    Input('store-graf-dist', 'data'),
    Input('tabs-distancia', "active_tab"),
    Input('button-filt-data', 'n_clicks'), prevent_initial_call=True)
def render_dist(grafs, active_tab,btn_filtrar):
    if btn_filtrar is None:
        raise PreventUpdate
        
    if active_tab == "tab-dist-hab":
        return dcc.Graph(figure=grafs["lab"])
    elif active_tab == "tab-dist-sab":
        return dcc.Graph(figure=grafs["sab"])
    elif active_tab == "tab-dist-dom":
        return dcc.Graph(figure=grafs["dom"])

@app.callback(
    Output('store-graf-dist', 'data'),   
    Input('store-val-inter', 'data'))
def genera_dist(datos_json):
    
    datasets = json.loads(datos_json)    
    df_dist = pd.read_json(datasets['df_dist'], orient='split') 
    
    df_dist.insert(0, c_anio+"2", df_dist[c_anio].astype(str))
    
    figures_dist = dict()
    
    for t_dia in tipo_dia_dispo:
    
        fig = px.bar(df_dist[df_dist[c_tipo_dia]==t_dia], x=c_rango_dist, y="viajes_dist",
                     color=c_anio+"2", barmode="group",
                     labels={c_anio+"2": "Año",
                             c_tipo_dia:"Día",
                             c_rango_dist: "Distancia",
                             c_modo: "Modo",
                             "viajes_dist": "Viajes"
                            },
                     facet_row=c_modo, facet_row_spacing=0.3,
                     category_orders={c_tipo_dia:[x for x in ["lab","sab","dom"] if x in df_dist[c_tipo_dia].unique()],
                                      c_rango_dist:rangos_dist},
                     custom_data = [c_anio, "viajes_dist", c_rango_dist])

        # Actualiza el hover tooltip
        fig.update_traces(hovertemplate="<br>".join([
                    "Viajes: %{customdata[1]:,.0f}",
                    "Dist: %{customdata[2]}"
        ]))
        
        figures_dist[t_dia] = fig
    
    return figures_dist


# Ejecuta la app
if __name__ == '__main__':
    # hot-reloading: La app cambia automáticamente con cambios en el código
    # Para desactivar esto, cambiar el parám. por dev_tools_hot_reload=False
    app.run_server(debug=True) 
