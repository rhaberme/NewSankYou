#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  4 06:47:17 2022

@author: jay3
"""



import sqlite3
import pandas as pd
from functools import reduce
import re
import numpy as np
import csv 
import seaborn as sns

import dash
import plotly.graph_objects as go
from dash import html
from dash import dcc
from dash import Input, Output
import dash_bootstrap_components as dbc

import json
import webbrowser
import os



#%%
# creating file path
loc_of_data = '/data'
nodes_csv = 'data/Nodes.csv'
month_key_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
dbfile = 'data/results.db'
result_num = 49



# Create a SQL connection to our SQLite database

def read_data_folder(loc_of_data):
    print('There are the following database files (.db) in the Data folder:\n')
    f = 0
    Files = []
    for a, b, files in os.walk(loc_of_data):
        for file in files:
            if '.db' in file:
                print(f, ') ', file)
                Files.append(file)
                f += 1
    print()
    return Files
                
            
            
def choose_from_list(List):
    asking = 1          
    while asking:            
        x = int(input('Choose a file by its number: '))
        if x in range(len(List)):
            target = List[x]
            return target
        else:
            print('Invalid Input. Please try again.')
            continue

# Files = read_data_folder(loc_of_data)
#dbfile = '../Data/'+choose_from_list(Files, dbfile)


def read_into_DataFrames(con, table_list):   
    DFs = []
    for t in table_list: 
        df = pd.read_sql_query('SELECT * FROM {}'.format(t), con)
        DFs.append(df)
    
    DF = reduce(lambda x, y: pd.merge(x, y, on = 'Variable'), DFs)
    table_list.insert(0, "Variable")
    DF.columns = table_list
    DF = DF.set_index('Variable')
    return DF


def choose_table(DB_file, result_num):
    con = sqlite3.connect(DB_file)
    cur = con.cursor()
    
    # reading all table names
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    table_list = [t[0]for t in table_list ]

    print('There are following', len(table_list), ' entries in the .db file: ', '\n')
    x = 0
    for t in table_list:
        print( x, ') ', t)
        x += 1
    print()
        
    DFS = read_into_DataFrames(con, table_list)
    con.close()
    #table = choose_from_list(table_list)
    table = table_list[result_num]
    
    return DFS[table], table


# assign every node a normed x position

def node_x_norm(Nodes):
    x_step = 1 / (max(Nodes['Position']) - 1)
    Nodes['x_norm'] = (Nodes['Position'] - 1) * x_step
    return Nodes


# assign every node a normed y position
def nodes_y_norm(Nodes):
    Set = set([])
    Dic = {}
    y_norm = []
    for p in Nodes['Position']:
        Set.add(p)

    for s in Set:
        n = list(Nodes['Position']).count(s)
        if n > 1:
            Dic[str(s)] = {
                'y-step': 1 / (n - 1),
                'count': 0
            }
        else:
            Dic[str(s)] = {
                'y-step': 1,
                'count': 0
            }

    for p in Nodes['Position']:
        step = Dic[str(p)]['count'] * Dic[str(p)]['y-step']
        y_norm.append(step)
        Dic[str(p)]['count'] += 1

    Nodes['y_norm'] = y_norm

    return Nodes, Set


# assign all nodes a specific node color

def assign_node_colors(Nodes, Set):
    iter = len(Set)
    palette = list(reversed(sns.color_palette("magma", iter).as_hex()))
    # print(palette)

    node_color = []
    for p in Nodes['Position']:
        node_color.append(palette[p - 1])
    Nodes['color'] = node_color
    return Nodes


# for every node assign a normed x and y position

def generate_nodes(csv_file):
    Nodes = pd.read_csv(csv_file, sep=';')
    # labels = list(Nodes['Node'])   #### maybe used in sankey_data
    Nodes = Nodes.set_index('Node')
    Nodes = node_x_norm(Nodes)
    Nodes, Set = nodes_y_norm(Nodes)
    Nodes = assign_node_colors(Nodes, Set)

    return Nodes

#create sanky data (for sum values first)
def sanky_data(month, flows):
    nodes = set([])
    sources = []
    targets = []
    values = []
    colors = []

    for flow in flows:
        if flows[flow]['data'][month] != 0:
            nodes.add(flows[flow]['source'])
            nodes.add(flows[flow]['target'])

    nodes = sorted(list(nodes))

    for flow in flows:
        if flows[flow]['data'][month] != 0:
            s = nodes.index(flows[flow]['source'])
            t = nodes.index(flows[flow]['target'])
            v = flows[flow]['data'][month]
            c = flows[flow]['color']

            sources.append(s)
            targets.append(t)
            values.append(v)
            colors.append(c)

    return nodes, sources, targets, values, colors


# get needed x/y-values and replace 0 with 1e-9
def x_Vals(Nodes, nodes):
    x_vals = [Nodes.loc[n, 'x_norm'] for n in nodes]
    for x in x_vals:
        if x == 0:
            i = x_vals.index(x)
            x_vals[i] = 1e-9

        if x == 1:
            i = x_vals.index(x)
            x_vals[i] = 0.999999
    return x_vals


def y_Vals(Nodes, nodes):
    y_vals = [Nodes.loc[n, 'y_norm'] for n in nodes]
    for y in y_vals:
        if y == 0:
            i = y_vals.index(y)
            y_vals[i] = 1e-9

        if y == 1:
            i = y_vals.index(y)
            y_vals[i] = 0.999999
    return y_vals


# =============================================================================
# #get needed  node colors
# n_color = [Nodes.loc[n, 'color'] for n in nodes]
#
# #as test print node name and position
# print('node: \t x-val: \t y-val:')
# for i in range(len(nodes)):
#     print(nodes[i], x_values[i], y_values[i], n_color[i])
#
# =============================================================================

# %%
# =============================================================================
# #there is the posibility of grouping
# groups = ['x']
#
# for n in nodes:
#     List = [nodes.index(n)]
#     for o in nodes:
#      if Nodes.loc[o, 'Position'] == Nodes.loc[n, 'Position'] and n != o:
#          if nodes.index(n) < nodes.index(o):
#              #if o != groups[-1][-1]:
#                  List.append(nodes.index(o))
#     #print(List)
#     if List[-1] != groups[-1][-1]:
#         groups.append(List)
#
# groups.pop(0)
# #x_values = [Nodes[ 'x_norm']]
# #y_values = [Nodes[ 'y_norm']]
# =============================================================================

# function to create the js data for the visualization in javascript and open the html file
# month_key is what is called month in other functions, js_files: 'JAN' for January
def create_data_and_show_html(filepath, month_key, flows, nodes_csv):
    nodes_df = generate_nodes(nodes_csv)
    nodes, sources, targets, values, l_colors = sanky_data(month_key, flows)
    nodes_list = []
    link_list = []
    for nod in nodes:
        nodes_list.append({"name": nod, "col": int(nodes_df.loc[nod]["Position"])})
    for i in range(len(sources)):
        source = nodes[sources[i]]
        target = nodes[targets[i]]
        value = values[i]
        link_list.append({"source": source, "target": target, "value": value, "optimal": "yes"})

    json_str = json.dumps({"nodes": nodes_list, "links": link_list})
    with open('../data/nodes_and_links.js', 'w') as f:
        output_str = "let input_data_object = " + json_str
        f.write(output_str)

    bash_command = filepath
    os.system(bash_command)


# %%
### define a sankey figure funktion:
def Figure(month):
    x_values = y_values = 0
    nodes = sources = targets = values = 0
    Nodes = generate_nodes(nodes_csv)
    nodes, sources, targets, values, l_colors = sanky_data(month, Flows)
    x_values = x_Vals(Nodes, nodes)
    y_values = y_Vals(Nodes, nodes)
    n_color = [Nodes.loc[n, 'color'] for n in nodes]

    # print()
    # print(month)
    # =============================================================================
    #     print('node: \t x-val: \t y-val:')
    #     for i in range(len(nodes)):
    #         print(nodes[i], '\t',  x_values[i], '\t', y_values[i])#, n_color[i])
    #     print()
    # =============================================================================
    # print('source: \t target: \t value:')
    # for i in range(len(sources)):
    #   print(nodes[sources[i]], '\t\t',  nodes[targets[i]], '\t\t', values[i])#, n_color[i])

    inputdata = [go.Sankey(
        valuesuffix="m³",
        arrangement='snap',
        orientation='h',
        # node_groups=groups,
        node=dict(
            # pad = 5,
            thickness=20,
            line=dict(color="black", width=0.5),
            # groups=groups,
            label=nodes,
            x=x_values,
            y=y_values,
            color='black'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=l_colors,
            # arrowlen = 5
        )
    )
    ]

    fig = go.Figure(data=inputdata)

    # height = 5*int(Flows['DP_HGW']['data'][month])

    fig.update_layout(
        title_text=table_name + ': ' + month,
        paper_bgcolor="gainsboro",
        autosize=False,
        width=2400,
        height=1200  # height #
    )
    fig.update_traces(
        link_source=sources,
        link_target=targets,
        link_value=values,
        link_color=l_colors,
        # link_arrowlen = 5
    )

    return fig  # , Nodes

def generate_button(button_names):

    return dbc.Button(children=str(button_names),
                      color="primary",
                      className="mr-1",
                      id='btn-'+str(button_names))

def generate_fig(month):
    fig = Figure(month)
    return dcc.Graph(children=str(month),
                    id="g-"+month,
                    figure=fig)

"""__________________"""

test_data_df, table_name = choose_table(dbfile, result_num)

Flows = {}
wrong_patterns = []

for x in test_data_df.index:
    #print(x)
    if re.search('var_\d\d\d\d', x):
        flow = list(x.split('_'))
        flow[1] = '\d\d\d\d'
        label = "_".join([ str(item) for item in flow[2:] ]) 
        
        Flows[ label ] = {'source' : flow[-2] ,
                          'target' : flow[-1] ,
                          'search pattern' : "_".join([str(item) for item in flow])
                          }
        
        if flow[-1] == 'big' or flow[-1] == 's':
            Flows[ label ]['source'] = flow[-3]
            Flows[ label ]['target'] = flow[-2]
            
        if len(flow) == 3:
            del Flows[ label ]
            continue
            #Flows[ label ] = {'source' : 'None' ,
            #              'target' : flow[-1] ,
            #              'search pattern' : "_".join([str(item) for item in flow])
            #              }
            
        #%%
#read in the data for each flow and sum up al months and create lists of nodes
# if flow is negative or small set it 0

nodes = set([])
mistakes = []

for flow in Flows:
    Values = np.array([])
    
    #read in values for each flow
    for x in test_data_df.index:
        if re.search(Flows[flow]['search pattern']+'$', x):
                Values = np.append(Values, test_data_df.loc[x])
                
    for i in range(len(Values)):
        if Values[i] < 0.1:
            Values[i] = 0
            
    if len(Values)== 12:            
        Flows[flow]['data'] = dict(zip(month_key_list, Values))
        Flows[flow]['data']['TOT'] = np.sum(Values)  
    else:
        mistakes.append({flow : Values })
    
    
    nodes.add(Flows[flow]['source'])
    nodes.add(Flows[flow]['target'])

nodes = sorted(list(nodes))

if len(mistakes) != 0:
    print('OOOOPS! something went wrong while analyzing the Flows of this database!')

for f in Flows:
    if Flows[f]['source'] == 'P' or Flows[f]['source'] == 'I':
        Flows[f]['color'] = 'rgb(146, 208, 80)' #hellgrün
        
    elif Flows[f]['source'] in ('SS', 'SR', 'SG', 'SSW', 'SSI', 'SIW'):
        if Flows[f]['target'] != 'E':
            Flows[f]['color'] = 'rgb(126, 255, 255)' #hellblau
        else:
            Flows[f]['color'] = 'rgb(127, 127, 127)' #grau
    
    elif Flows[f]['source'] in ('WQ1', 'WQ2', 'WQ2recy', 'WQ3', 'WQ3recy', 'NETD', 'NETS', 'NETI'):
        Flows[f]['color'] = 'rgb(0, 12, 192)' #dunkelblau
    elif Flows[f]['source'] in ('DP', 'DNP', 'HGW', 'HBW', 'ST'):
        if Flows[f]['target'] not in ('QU', 'QF'):
            Flows[f]['color'] = 'rgb(192, 0, 0)' #rot
        else:
            Flows[f]['color'] = 'rgb(127, 127, 127)' #grau
            
    elif Flows[f]['source'] in ('DAWP', 'DAWS', 'DIP', 'DIS', 'QI'):
        if Flows[f]['target'] not in ('WWSSfI', 'WWCSfI', 'OUT'):
            Flows[f]['color'] = 'rgb(255, 192, 0)' #gelb
        elif Flows[f]['target'] == 'OUT':
            Flows[f]['color'] = 'rgb(142, 77, 28)' #braun
        else:
            Flows[f]['color'] = 'rgb(127, 127, 127)' #grau
            
    elif Flows[f]['source'] in ('DG', 'DA'):
        Flows[f]['color'] = 'rgb(0, 176, 80)' #dunkelgrün
    
    elif Flows[f]['target'] in ('OUT', 'TWWfCS', 'TWWfSS'):
        if Flows[f]['source'] not in ('pRWSS', 'TWWfCS', 'TWWfDS', 'P'):
            Flows[f]['color'] = 'rgb(142, 77, 28)' #braun
    
    elif Flows[f]['source'] in ('TWWfCS', 'TWWfSS', 'GW'):
        if Flows[f]['target'] not in ('E', 'OUT'):
            Flows[f]['color'] = 'rgb(112, 48, 160)' #violet
    
    else:
        Flows[f]['color'] = 'rgb(127, 127, 127)' #grau
        
for f in Flows:
    if 'color' not in Flows[f]:
        Flows[f]['color'] = 'rgb(127, 127, 127)' #grau
#%%

btn_ids = ['btn-' + m for m in month_key_list]

app = dash.Dash(__name__)



app.layout = html.Div([
# =============================================================================
#                         dcc.Textarea(
#                             id='title',
#                             value='DATA BANK FILE: '+ table_name,
#                             #style={'width': '100%', 'height': 300},
#                         ),
# =============================================================================
                        html.Div([
                                dcc.Graph(id='g-TOT', figure=Figure('TOT')),
                                ],
                                id="main_div"),
                        html.Div(id='container'),
                        html.Div([
                                    dbc.Row([
                                            dbc.Col(children=[generate_button('TOT') ])
                                            ])
                                ]),
                        html.Div([
                                    dbc.Row([
                                            dbc.Col(children=[generate_button(i) for i in month_key_list])
                                            ])
                                ])

                        ])

app.title = table_name


@app.callback(Output('main_div', 'children'),
              Input('btn-TOT', 'n_clicks'),
              Input('btn-JAN', 'n_clicks'),
              Input('btn-FEB', 'n_clicks'),
              Input('btn-MAR', 'n_clicks'),
              Input('btn-APR', 'n_clicks'),
              Input('btn-MAY', 'n_clicks'),
              Input('btn-JUN', 'n_clicks'),
              Input('btn-JUL', 'n_clicks'),
              Input('btn-AUG', 'n_clicks'),
              Input('btn-SEP', 'n_clicks'),
              Input('btn-OCT', 'n_clicks'),
              Input('btn-NOV', 'n_clicks'),
              Input('btn-DEC', 'n_clicks'))
def display(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10, btn11, btn12, btn13):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'default_value'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    ctx_msg = json.dumps({
        'states': ctx.states,
        'triggered': ctx.triggered,
        'inputs': ctx.inputs
    }, indent=2)

    if button_id == 'default_value' or button_id == 'btn-TOT':
        return html.H3('TOT'), dcc.Graph(id='g-TOT', figure=Figure('TOT'))


    elif button_id in btn_ids:
        g_id = button_id.replace('btn-', 'g-')
        month = button_id.replace('btn-', '')
        return html.H3(month), dcc.Graph(id=g_id, figure=Figure(month))



if __name__ == '__main__':
    # app.run_server(debug=True)
    create_data_and_show_html(filepath="open js_files/index.html", month_key="JAN", flows=Flows, nodes_csv=nodes_csv)

