# Copyright 2021 Horáci Henriques
# Simple app to view data from any country

country = "Timor"
days = 160


# Data from "Our World in Data"

from flask import Flask, render_template
import pandas as pd
import json
import plotly
from datetime import datetime, timezone

import os.path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from google.cloud import datastore

datastore_client = datastore.Client()

def store_data(data, ref, country):
    key = datastore_client.key(ref, country)
    entity = datastore.Entity(key=key)
    entity.exclude_from_indexes = {"data"}
    entity.update({
        'timestamp': datetime.now(timezone.utc),
        'data': data
    })
    datastore_client.put(entity)

def fetch_data(ref, country):
    key=datastore_client.key(ref, country)
    data = datastore_client.get(key=key)
    return data

def create_fig(country, df, days=90):
 
  title = country + ": Novos casos vs Taxa de Positividade"
 
  # Create figure with secondary y-axis
  fig = make_subplots(specs=[[{"secondary_y": True}]])
 
  # Add traces
  fig.add_trace(
      go.Scatter(x=df.date, y=df.new_cases_smoothed_per_million, name="Novos casos (média movel 7 dias, por milhão de pessoas)"),
      secondary_y=False,
  )
  
  fig.add_trace(
      go.Scatter(x=df.date, y=df.positive_rate, name="Taxa de positividade"),
      secondary_y=True,
  )
 
  # Add figure title
  fig.update_layout(
      legend=dict(orientation="h", yanchor="bottom", y=1),
      title_text=title,
      title_x=0.5,
  )
 
  fig.layout.yaxis2.tickformat = ',.1%'
 
  # Set y-axes titles
  fig.update_yaxes(title_text="<b>Novos casos</b>", secondary_y=False)
  fig.update_yaxes(title_text="<b>Taxa de positividade</b>", secondary_y=True)
  return fig

app = Flask(__name__)

file_name = 'owid-covid-data.csv'

@app.route('/')
def main():
    print('vou começar...')

    try:
        data = fetch_data("OWD", country)
        time = (datetime.now(timezone.utc) - data['timestamp']).total_seconds()/8600
        print(time)
        if time > 8:
                df = update()
        else:
                df = pd.read_json(data['data'])

    except:
        print('Error on data. Get new data')
        df = update()

    fig = create_fig(country, df, days)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    res = render_template("notdash.html", graphJSON=graphJSON)

    return res

def update():
    covid = pd.read_csv('https://covid.ourworldindata.org/data/'+file_name)
    df = covid[(covid.location==country)& (covid.new_cases_smoothed_per_million.notnull())][['date','positive_rate', 'new_cases_smoothed_per_million']].tail(days)
    store_data(df.to_json(), "OWD", country)
    return df

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    print('local...')
    credential_path = 'local path'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_app]
# [END gae_python38_app]
