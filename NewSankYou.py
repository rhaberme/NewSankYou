#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3
import pandas as pd
from functools import reduce
import re
import numpy as np
import json
import os


def get_tables(db_file, result_num_):
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # reading all table names
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    table_list = [t[0] for t in table_list]
    df_list = []
    for t in table_list:
        df_ = pd.read_sql_query('SELECT * FROM {}'.format(t), con)
        df_list.append(df_)

    df_all_tables = reduce(lambda df1, df2: pd.merge(df1, df2, on='Variable', suffixes=('', '_rename')), df_list)
    df_all_tables.columns = ["Variable"] + table_list
    df_all_tables = df_all_tables.set_index('Variable')

    con.close()
    if result_num_ < 0:
        return df_all_tables.iloc[:, 0]
    elif result_num_ > len(table_list) - 1:
        return df_all_tables.iloc[:, -1]
    else:
        return df_all_tables.iloc[:, result_num_]


def create_flows_dict(data_df):
    month_key_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    flows = {}

    for ind in data_df.index:
        if re.search('var_\d\d\d\d', ind):
            flow = list(ind.split('_'))
            flow[1] = '\d\d\d\d'
            label = "_".join([str(item) for item in flow[2:]])

            flows[label] = {'source': flow[-2],
                            'target': flow[-1],
                            'search pattern': "_".join([str(item) for item in flow])
                            }

            if flow[-1] == 'big' or flow[-1] == 's':
                flows[label]['source'] = flow[-3]
                flows[label]['target'] = flow[-2]

            if len(flow) == 3:
                del flows[label]
                continue

    # read in the data for each flow and sum up al months and create lists of nodes
    # if flow is negative or small set it 0

    mistakes = []

    for flow in flows:
        Values = np.array([])

        # read in values for each flow
        for ind in data_df.index:
            if re.search(flows[flow]['search pattern'] + '$', ind):
                Values = np.append(Values, data_df.loc[ind])

        for i in range(len(Values)):
            if Values[i] < 0.1:
                Values[i] = 0

        if len(Values) == 12:
            flows[flow]['data'] = dict(zip(month_key_list, Values))
            flows[flow]['data']['TOT'] = np.sum(Values)
        else:
            mistakes.append({flow: Values})

    return flows

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
def create_data_and_show_html(html_filepath, data_js_filepath, db_filepath, nodes_csv_filepath, result_number):
    data_df = get_tables(db_filepath, result_number)
    flows = create_flows_dict(data_df)
    nodes_df = pd.read_csv(nodes_csv_filepath, sep=';')
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


    with open(data_js_filepath, 'w') as f:
        output_str = "let input_data_object = " + json.dumps(json_str_dict)
        f.write(output_str)

    bash_command = "open " + html_filepath
    os.system(bash_command)


if __name__ == '__main__':
    nodes_csv = 'data/Nodes.csv'
    dbfile = 'data/results.db'

    result_num = 50

    create_data_and_show_html(html_filepath="js_files/index.html", data_js_filepath='data/nodes_and_links.js',
                              db_filepath=dbfile, nodes_csv_filepath=nodes_csv, result_number=result_num,)

