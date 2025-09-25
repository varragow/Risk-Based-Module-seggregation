import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import os
import dash_bootstrap_components as dbc
import csv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
path = os.path.join(os.getcwd(), "categorized_data.xlsx")
data = pd.read_excel(path)
module_vs_techarea_details = r'\\rover\cts\Axiom\Executables\ModuleVsTechArea_Data'
if os.path.exists(os.path.join(os.getcwd(),"subplans_path.txt")):
    with open(os.path.join(os.getcwd(),"subplans_path.txt"),'r') as file:
        contents=file.read()

print(f"Subplans path : {contents}")
reference_data = []
def parse_confluence_data():
    for root, dirs, files in os.walk(module_vs_techarea_details):
        for file in files:
            if file.endswith(".csv"):
                with open(os.path.join(module_vs_techarea_details, file), 'r', encoding='utf-8') as csv_file:
                    csvreader = csv.reader(csv_file)
                    for rows in csvreader:
                        reference_data.append([rows[0], rows[3], rows[4]]) 

parse_confluence_data()
headers = reference_data[0]
reference_data = reference_data[1:]
reference_data = pd.DataFrame(reference_data, columns=['PackageName', 'Functionality', 'No.of TC'])
my_data = data.rename(columns={'Module': "PackageName"})
# print(my_data)
my_data = my_data[['PackageName', 'Suite', 'mean', 'Coefficient of Variation', 'Cluster']]
df_merged = pd.merge(my_data, reference_data, on=['PackageName'])

# Create a new DataFrame with cluster-wise, suite-wise test case counts
df_merged[['No.of TC']] = df_merged[['No.of TC']].apply(pd.to_numeric)
cluster_suite_counts = df_merged.groupby(['Cluster', 'Suite'])['No.of TC'].sum().reset_index()

# Select all relevant columns for clustering and plotting
numeric_data = data[['Coefficient of Variation', 'mean', 'Cluster']].copy()

# Function to generate the scatter plot
def generate_scatter_plot(numeric_data):
    # Calculate the total number of test cases in each cluster
    cluster_counts = df_merged.groupby('Cluster')['No.of TC'].sum().to_dict()
    numeric_data.loc[:, 'Total Entries'] = numeric_data['Cluster'].map(cluster_counts)
    fig = px.scatter(
        numeric_data,
        x='Coefficient of Variation',
        y='mean',
        color='Cluster',
        color_continuous_scale='Viridis',
        size_max=80,
        title='Scatter Plot of Clusters with Centers',
        labels={'Coefficient of Variation': 'Consistency of Failures', 'mean': 'Failure count'},
        hover_data={'Cluster': True, 'Total Entries': True}
    )
    
    # Calculate the centers of each cluster
    centers = numeric_data.groupby('Cluster').mean().reset_index()
    centers = centers.sort_values(by=['mean', 'Coefficient of Variation'], ascending=[False, True])

    # Add a red marker for the center of each cluster
    for index, row in centers.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Coefficient of Variation']],
            y=[row['mean']],
            mode='markers',
            marker=dict(color='red', size=10, symbol='star'),
            name=f'Center of Cluster {row["Cluster"]}',
            showlegend=False
        ))

    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.5)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.5)'),
        height=600
    )
    return fig, centers

# Create a Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Define the layout of the app
print(">> Entering Callback function")
scatter_plot, cluster_centers = generate_scatter_plot(numeric_data)
app.layout = html.Div([
    html.H1("Risk Based Module Segregation",style={'marginBottom': '24px'}),
    html.H2("Categorized Data Dashboard", style={'marginBottom': '24px'}),
    
    html.Div([
        dcc.Graph(id='example-graph', figure=scatter_plot),
        html.Div([
            html.Div(id='cluster-suite-table-container', style={'marginBottom': '24px'}),
            html.Div(id='priority-bar-container', style={'marginBottom': '24px'}),
            html.H6(f"Find the subplans here : {contents}")
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '24px',  # Adds equal gap between table and priority bar
            'border': '1px solid #ccc',  # Apply border to the container
            'padding': '12px',
            'borderRadius': '8px',
            'width': '45%'  # Adjust width to align with the graph
        })
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'gap': '50px',  # Adds equal gap between graph and table
        'marginBottom': '24px'
    }),
    html.Div(id='table-container', style={'marginBottom': '24px'}),
    html.Div(id='functionality-bar-chart-container')
])

# Callback to update the table
@app.callback(
    Output('table-container', 'children'),
    [Input('example-graph', 'hoverData')]
)
def update_table(hoverData):
    if hoverData is None:
        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in data.columns if i not in ['mean', 'std_dev', 'variance', 'Coefficient of Variation']],
            data=data.to_dict('records'),
            style_table={'height': '300px', 'overflowY': 'auto', 'border': '1px solid #ccc', 'borderRadius': '8px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'border': '1px solid #ccc'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )

    point_index = hoverData['points'][0]['pointIndex']
    cluster_value = data.iloc[point_index]['Cluster']
    related_modules = data[data['Cluster'] == cluster_value]
    table_container_heading = html.H3(f"Cluster: {cluster_value} - Module Info")
    
    return html.Div([
        table_container_heading,
        dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in related_modules.columns if i not in ['mean', 'std_dev', 'variance', 'Coefficient of Variation']],
        data=related_modules.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'},
        filter_action='native',
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'left', 'padding': '8px'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    )])

# Callback to update the bar chart
@app.callback(
    Output('functionality-bar-chart-container', 'children'),
    [Input('example-graph', 'hoverData')]
)
def update_bar_chart(hoverData):
    if hoverData is None:
        return html.Div()

    point_index = hoverData['points'][0]['pointIndex']
    cluster_value = data.iloc[point_index]['Cluster']
    cluster_data = df_merged[df_merged['Cluster'] == cluster_value]
    functionality_counts = cluster_data['Functionality'].value_counts().reset_index()

    fig = px.bar(
        functionality_counts,
        x='Functionality',
        y='count',
        title=f'Functionality Count for Cluster {cluster_value}',
        labels={'Functionality': 'Functionality', 'count': 'Count'},
        text='count'  # Display count on the bar
    )

    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        hovermode=False,  # Remove hover functionality
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.5)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.5)'),
        height=600
    )

    return dcc.Graph(id='functionality-bar-chart', figure=fig)

# Callback to update the new cluster-suite table
@app.callback(
    Output('cluster-suite-table-container', 'children'),
    [Input('example-graph', 'hoverData')]
)
def update_cluster_suite_table(hoverData):
    if hoverData is None:
        return html.Div()

    point_index = hoverData['points'][0]['pointIndex']
    cluster_value = data.iloc[point_index]['Cluster']
    cluster_suite_data = cluster_suite_counts[cluster_suite_counts['Cluster'] == cluster_value]
    # Add total number of test cases for the cluster
    total_no_of_tc = df_merged[df_merged['Cluster'] == cluster_value]['No.of TC'].sum()
    cluster_suite_heading = html.H3(f'Cluster {cluster_value} - Testcase count: {total_no_of_tc}')

    return html.Div([
        cluster_suite_heading,
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in cluster_suite_data.columns],
            data=cluster_suite_data.to_dict('records'),
            style_table={'height': '300px', 'overflowY': 'auto', 'border': '1px solid #ccc', 'borderRadius': '8px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'border': '1px solid #ccc'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ])

# Callback to update the priority bar
@app.callback(
    Output('priority-bar-container', 'children'),
    [Input('example-graph', 'hoverData')]
)
def update_priority_bar(hoverData):
    if hoverData is None:
        return html.Div()

    # Create a DataFrame for priority order
    priority_order_df = cluster_centers[['Cluster']].copy()
    priority_order_df['Priority'] = range(len(priority_order_df))
    priority_order_df['Priority'] = 'P' + priority_order_df['Priority'].astype(str)
    priority_order_df = priority_order_df.sort_values(by=['Priority'], ascending=True)

    return html.Div([
        html.H5("Priority Order"),
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in priority_order_df.columns],
            data=priority_order_df.to_dict('records'),
            style_table={'height': 'auto', 'overflowY': 'auto', 'border': '1px solid #ccc', 'borderRadius': '8px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'border': '1px solid #ccc'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ])

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
