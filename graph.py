from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import json

df = pd.read_csv('Major_Crime_Indicators.csv')

data = df.groupby(['Neighbourhood', 'reportedyear', 'Hood_ID'], sort=False)['Neighbourhood'].size().reset_index(name='Count')
data = data.groupby(['Neighbourhood', 'reportedyear'], as_index=False).agg({'Hood_ID': 'first', 'Count': 'sum'})
data.loc[data['reportedyear'] == 2022, 'Count'] *= 2

list_n = data.groupby(['Neighbourhood']).sum()

lowest_rates = list_n.nsmallest(5, 'Count')
l_names = [name for name, df in lowest_rates.groupby('Neighbourhood')]
highest_rates = list_n.nlargest(5, 'Count')
h_names = [name for name, df in highest_rates.groupby('Neighbourhood')]

link = 'https://www.toronto.ca/city-government/data-research-maps/neighbourhoods-communities/neighbourhood-profiles/about-toronto-neighbourhoods/'

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Neighbourhood Crime Rates in Toronto (2014 - 2022)", style={'text-align': 'center'}),
    html.P('Search for: '),
    dcc.Dropdown(id='info',
        options=[
            {'label': 'Top 5 neighbourhoods with the highest crime rates', 'value': 'highest'},
            {'label': 'Top 5 neighbourhoods with the lowest crime rates', 'value': 'lowest'},
            {'label': 'Crime rates in Toronto on a map', 'value': 'map'}],
        multi=False,
        value='highest',
        style={'width': '60%'}
    ),
    html.P("*Note: The data for 2022 is estimated as only the first half of the year was recorded."),
    html.Div(id='slider_container', children=[
        html.P('Choose a year:'),
        dcc.Slider(2014, 2022, 1, id='slider', value=2021, marks={2014:'2014', 2015:'2015', 2016:'2016', 2017:'2017', 2018:'2018', 2019:'2019', 2020:'2020', 2021:'2021', 2022:'2022'}),
        html.P(children=[
            '*Note: The data for the map corresponds with the 140/158 neighbourhoods (Click ',
            html.A("here", href=link, target="_blank"),
            ' for more details)'])
        ], hidden=True),
    html.Br(),
    dcc.Graph(id='graph', figure={})
])

@app.callback(
    Output(component_id='graph', component_property='figure'),
    Output(component_id='slider_container', component_property='hidden'),
    Input(component_id='info', component_property='value'),
    Input(component_id='slider', component_property='value')
)

def update_graph(info_option, year):

    df_copy = data.copy()

    slide = True

    if info_option != 'map':
        if info_option == 'highest':
            df_copy = df_copy[df_copy['Neighbourhood'].isin(h_names)]
        else:
            df_copy = df_copy[df_copy['Neighbourhood'].isin(l_names)]

        fig = px.line(
            data_frame=df_copy,
            x='reportedyear',
            y='Count',
            line_group='Neighbourhood',
            color='Neighbourhood',
            labels={'reportedyear': 'Year', 'Count': 'Number of offences'},
            template='plotly'
        )
    else:
        slide = False
        df_copy = df_copy[df_copy['reportedyear'] == year]
        geoJson = json.load(open('Neighbourhoods_historical_140.geojson'))
        fig = px.choropleth(
            data_frame=df_copy,
            geojson=geoJson,
            locations='Hood_ID',
            featureidkey='properties.AREA_SHORT_CODE',
            projection='robinson',
            color='Count',
            labels={'reportedyear': 'Year', 'Count': 'Number of offences'},
            hover_data=['Neighbourhood'],
            color_continuous_scale='sunset',
            fitbounds='locations',
            basemap_visible=False
        )

    fig.update_yaxes(rangemode="tozero")
    #fig.update_geos(fitbounds='locations', visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig, slide

if __name__ == '__main__':
    app.run_server(debug=True)