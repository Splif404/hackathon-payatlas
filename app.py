import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from config import DIRECTUS_URL, API_TOKEN, COLLECTION_NAME

# Load and process data from Directus
def load_data():
    # Directus configuration from config.py
    
    try:
        # Fetch data from Directus
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get all records from the incidents collection
        response = requests.get(
            f"{DIRECTUS_URL}/items/{COLLECTION_NAME}",
            headers=headers,
            params={
                "limit": -1,  # Get all records
                "sort": ["-started_at"]  # Sort by started_at descending
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Convert Directus response to DataFrame
            if 'data' in data:
                records = data['data']
                data_df = pd.DataFrame(records)
                
                # Ensure required columns exist
                required_columns = ['guid', 'provider', 'status', 'title', 'started_at', 'link', 'id']
                missing_columns = [col for col in required_columns if col not in data_df.columns]
                
                if missing_columns:
                    print(f"Warning: Missing columns in Directus data: {missing_columns}")
                    print("Available columns:", list(data_df.columns))
                    # Create missing columns with default values
                    for col in missing_columns:
                        if col == 'id':
                            data_df[col] = range(len(data_df))
                        else:
                            data_df[col] = ''
                
                # Process datetime
                data_df['started_at'] = pd.to_datetime(data_df['started_at'])
                data_df['date'] = data_df['started_at'].dt.date
                data_df['month'] = data_df['started_at'].dt.to_period('M')
                data_df['year'] = data_df['started_at'].dt.year
                
                print(f"✅ Successfully loaded {len(data_df)} incidents from Directus")
                return data_df
            else:
                print("❌ No data found in Directus response")
                return pd.DataFrame()
                
        else:
            print(f"❌ Error fetching data from Directus: {response.status_code}")
            print(f"Response: {response.text}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error connecting to Directus: {str(e)}")
        print("📝 Please check your Directus URL, API token, and collection name")
        return pd.DataFrame()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Payment Services Incident Dashboard"

# Add custom CSS for dropdown styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .Select-control {
                background-color: #404040 !important;
                border-color: #555 !important;
            }
            .Select-control .Select-value-label {
                color: #ffffff !important;
            }
            .Select-control .Select-placeholder {
                color: #ffffff !important;
            }
            .Select-menu-outer {
                background-color: #404040 !important;
                border-color: #555 !important;
            }
            .Select-option {
                background-color: #404040 !important;
                color: #ffffff !important;
            }
            .Select-option:hover {
                background-color: #555 !important;
                color: #ffffff !important;
            }
            .Select-option.is-focused {
                background-color: #555 !important;
                color: #ffffff !important;
            }
            .Select-option.is-selected {
                background-color: #00ff88 !important;
                color: #1a1a1a !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Load data
df = load_data()

# Color scheme for dark theme
colors = {
    'up': '#00ff88',
    'down': '#ff4444',
    'degraded': '#ffaa00',
    'maintenance': '#0088ff',
    'info': '#888888'
}

# Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Payment Services Incident Dashboard", 
                    className="text-center text-light mb-4"),
            html.P("Real-time monitoring of payment service provider incidents", 
                   className="text-center text-muted mb-5")
        ])
    ]),
    
    # Summary Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-incidents", className="card-title text-center"),
                    html.P("Total Incidents (All Statuses)", className="card-text text-center text-muted")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="active-incidents", className="card-title text-center"),
                    html.P("Active Issues (Down/Degraded)", className="card-text text-center text-muted")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="providers-count", className="card-title text-center"),
                    html.P("Providers Monitored", className="card-text text-center text-muted")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="recent-incidents", className="card-title text-center"),
                    html.P("Last 30 Days", className="card-text text-center text-muted")
                ])
            ], className="mb-4")
        ], width=3)
    ]),
    
    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Filters", className="card-title"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Status Filter:"),
                            dcc.Dropdown(
                                id='status-filter',
                                options=[
                                    {'label': 'All Statuses', 'value': 'all'},
                                    {'label': 'Up', 'value': 'up'},
                                    {'label': 'Down', 'value': 'down'},
                                    {'label': 'Degraded', 'value': 'degraded'},
                                    {'label': 'Maintenance', 'value': 'maintenance'}
                                ],
                                value='all',
                                className="mb-3"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Provider Filter:"),
                            dcc.Dropdown(
                                id='provider-filter',
                                options=[{'label': 'All Providers', 'value': 'all'}] + 
                                       [{'label': provider, 'value': provider} 
                                        for provider in sorted(df['provider'].unique())],
                                value='all',
                                className="mb-3"
                            )
                        ], width=6)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),
    
    # Charts Row 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Incident Status Distribution", className="card-title"),
                    dcc.Graph(id='status-pie-chart')
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Status by Provider Heatmap", className="card-title"),
                    dcc.Graph(id='heatmap-chart')
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    
    # Charts Row 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Incidents Over Time", className="card-title"),
                    dcc.Graph(id='timeline-chart')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # Charts Row 3
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Monthly Trend Analysis", className="card-title"),
                    dcc.Graph(id='monthly-trend-chart')
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Incidents by Provider", className="card-title"),
                    dcc.Graph(id='provider-bar-chart')
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    
    # Recent Incidents Table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Recent Incidents", className="card-title"),
                    html.Div(id='recent-incidents-table')
                ])
            ], className="mb-4")
        ])
    ])
], fluid=True, className="py-4")

# Callbacks
@app.callback(
    [Output('total-incidents', 'children'),
     Output('active-incidents', 'children'),
     Output('providers-count', 'children'),
     Output('recent-incidents', 'children')],
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_summary_cards(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    total = len(filtered_df)
    # Only count down and degraded as active incidents (exclude "up" which means resolved)
    active = len(filtered_df[filtered_df['status'].isin(['down', 'degraded'])])
    providers = len(filtered_df['provider'].unique())
    recent = len(filtered_df[filtered_df['started_at'] >= datetime.now() - timedelta(days=30)])
    
    return total, active, providers, recent

@app.callback(
    Output('status-pie-chart', 'figure'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_status_pie_chart(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    status_counts = filtered_df['status'].value_counts()
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Incident Status Distribution",
        color_discrete_map=colors
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig

@app.callback(
    Output('heatmap-chart', 'figure'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_heatmap_chart(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    # Create pivot table for heatmap
    heatmap_data = filtered_df.groupby(['provider', 'status']).size().unstack(fill_value=0)
    
    fig = px.imshow(
        heatmap_data,
        title="Status Distribution by Provider",
        color_continuous_scale='Viridis',
        aspect="auto"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis_title="Status",
        yaxis_title="Provider"
    )
    
    return fig

@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_timeline_chart(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    # Group by date and status
    timeline_data = filtered_df.groupby(['date', 'status']).size().reset_index(name='count')
    
    fig = px.line(
        timeline_data,
        x='date',
        y='count',
        color='status',
        title="Incidents Over Time",
        color_discrete_map=colors
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis_title="Date",
        yaxis_title="Number of Incidents"
    )
    
    return fig

@app.callback(
    Output('monthly-trend-chart', 'figure'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_monthly_trend_chart(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    # Group by month and status
    monthly_data = filtered_df.groupby(['month', 'status']).size().reset_index(name='count')
    monthly_data['month'] = monthly_data['month'].astype(str)
    
    fig = px.bar(
        monthly_data,
        x='month',
        y='count',
        color='status',
        title="Monthly Incident Trends",
        color_discrete_map=colors
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis_title="Month",
        yaxis_title="Number of Incidents"
    )
    
    return fig

@app.callback(
    Output('provider-bar-chart', 'figure'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_provider_bar_chart(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    provider_counts = filtered_df['provider'].value_counts().head(10)
    
    fig = px.bar(
        x=provider_counts.values,
        y=provider_counts.index,
        orientation='h',
        title="Top 10 Providers by Incident Count",
        color_discrete_sequence=['#00ff88']
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis_title="Number of Incidents",
        yaxis_title="Provider"
    )
    
    return fig

@app.callback(
    Output('recent-incidents-table', 'children'),
    [Input('status-filter', 'value'),
     Input('provider-filter', 'value')]
)
def update_recent_incidents_table(status_filter, provider_filter):
    filtered_df = filter_data(df, status_filter, provider_filter)
    
    # Get recent incidents (last 10)
    recent_df = filtered_df.sort_values('started_at', ascending=False).head(10)
    
    table_rows = []
    for _, row in recent_df.iterrows():
        status_color = colors.get(row['status'], '#888888')
        table_rows.append(
            dbc.Row([
                dbc.Col(row['provider'], width=2),
                dbc.Col([
                    html.Span(row['status'], style={'color': status_color, 'fontWeight': 'bold'})
                ], width=1),
                dbc.Col(row['title'][:50] + "..." if len(row['title']) > 50 else row['title'], width=6),
                dbc.Col(row['started_at'].strftime('%Y-%m-%d %H:%M'), width=2),
                dbc.Col([
                    dbc.Button("Link", href=row['link'], target="_blank", size="sm")
                ], width=1)
            ], className="mb-2")
        )
    
    return table_rows

def filter_data(data_df, status_filter, provider_filter):
    filtered_df = data_df.copy()
    
    if status_filter != 'all':
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if provider_filter != 'all':
        filtered_df = filtered_df[filtered_df['provider'] == provider_filter]
    
    return filtered_df

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) 