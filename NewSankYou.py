#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3
import pandas as pd
from functools import reduce
import re
import numpy as np
import json
import os


def choose_table(db_file, result_num_):
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # reading all table names
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    table_list = [t[0] for t in table_list]

    df_list = read_into_dfs(con, table_list)
    con.close()
    if result_num_ < 1:
        table = table_list[1]
    elif result_num_ > len(table_list) - 1:
        table = table_list[-1]
    else:
        table = table_list[result_num_]

    return df_list[table]


def read_into_dfs(con, table_list):
    df_list = []
    for t in table_list: 
        df_ = pd.read_sql_query('SELECT * FROM {}'.format(t), con)
        df_list.append(df_)
    
    df = reduce(lambda x, y: pd.merge(x, y, on = 'Variable'), df_list)
    table_list.insert(0, "Variable")
    df.columns = table_list
    df = df.set_index('Variable')
    return df

def create_flows_dict(data_df):
    month_key_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    Flows = {}

    for ind in data_df.index:
        if re.search('var_\d\d\d\d', ind):
            flow = list(ind.split('_'))
            flow[1] = '\d\d\d\d'
            label = "_".join([str(item) for item in flow[2:]])

            Flows[label] = {'source': flow[-2],
                            'target': flow[-1],
                            'search pattern': "_".join([str(item) for item in flow])
                            }

            if flow[-1] == 'big' or flow[-1] == 's':
                Flows[label]['source'] = flow[-3]
                Flows[label]['target'] = flow[-2]

            if len(flow) == 3:
                del Flows[label]
                continue

    # read in the data for each flow and sum up al months and create lists of nodes
    # if flow is negative or small set it 0

    mistakes = []

    for flow in Flows:
        Values = np.array([])

        # read in values for each flow
        for ind in data_df.index:
            if re.search(Flows[flow]['search pattern'] + '$', ind):
                Values = np.append(Values, data_df.loc[ind])

        for i in range(len(Values)):
            if Values[i] < 0.1:
                Values[i] = 0

        if len(Values) == 12:
            Flows[flow]['data'] = dict(zip(month_key_list, Values))
            Flows[flow]['data']['TOT'] = np.sum(Values)
        else:
            mistakes.append({flow: Values})

    return Flows

#create sanky data (for sum values first)
def sanky_data(month, flows):
    nodes = set([])
    sources = []
    targets = []
    values = []

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

            sources.append(s)
            targets.append(t)
            values.append(v)

    return nodes, sources, targets, values


# function to create the js data for the visualization in javascript and open the html file
# month_key is what is called month in other functions, js_files: 'JAN' for January
def create_data_and_show_html(filepath, dbfile, result_num,  nodes_csv_file):
    data_df = choose_table(dbfile, result_num)
    flows = create_flows_dict(data_df)
    nodes_df = pd.read_csv(nodes_csv_file, sep=';')
    nodes_df = nodes_df.set_index('Node')

    json_str_dict = {}
    for month_key in ["TOT", 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']:
        nodes, sources, targets, values = sanky_data(month_key, flows)
        nodes_list = []
        link_list = []
        for nod in nodes:
            nodes_list.append({"name": nod, "col": int(nodes_df.loc[nod]["Position"])})
        for i in range(len(sources)):
            source = nodes[sources[i]]
            target = nodes[targets[i]]
            value = values[i]
            link_list.append({"source": source, "target": target, "value": value, "optimal": "yes"})
        json_str_dict[month_key] = {"nodes": nodes_list, "links": link_list}


    with open('data/nodes_and_links.js', 'w') as f:
        output_str = "let input_data_object = " + json.dumps(json_str_dict)
        f.write(output_str)

    bash_command = "open " + filepath
    os.system(bash_command)


if __name__ == '__main__':
    nodes_csv = 'data/Nodes.csv'
    dbfile = 'data/results.db'

    for i in range(10, 40):
        result_num = i

        create_data_and_show_html(filepath="js_files/index.html", dbfile=dbfile, result_num=result_num,
                                  nodes_csv_file=nodes_csv)

