import dash
import dash_core_components as dcc
from dash import html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from dash.exceptions import PreventUpdate
import base64

# Read and preprocess the Marvel movies dataset


def preprocess_data():
    df = pd.read_csv('marvel.csv')

    # Calculate the '% budget recovered' column
    df['percent budget recovered'] = (
        df['worldwide gross ($m)'] / df['budget']) * 100

    # Remove the percentage sign and convert 'critics % score' column to numeric values
    df['critics percent score'] = pd.to_numeric(
        df['critics % score'].str.rstrip('%'))

    return df


df = preprocess_data()

# Define category colors and categories
category_colors = {
    'Ant-Man': '#FF5733',
    'Avengers': '#FFEBEB',
    'Black Panther': '#9E6F21',
    'Unique': '#8E44AD',
    'Captain America': '#138D75',
    'Dr Strange': '#F39C12',
    'Guardians': '#6C3483',
    'Iron Man': '#C0392B',
    'Spider-Man': '#3498DB',
    'Thor': '#1ABC9C'
}

categories = df['category'].unique()

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[
                'https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
                ])

# Read and encode the image
logo_filename = 'logo.png'  # Replace with your logo file name
encoded_logo = base64.b64encode(open(logo_filename, 'rb').read())

# Define the app layout
app.layout = html.Div([
    html.Div([
        html.H1("Which is The Best Performing Marvel Movie?",
                className='mb-2 text-center title'),
        html.P("use the legend to filter",
               className='mb-4 text-center description'),
    ], className='header'),
    html.Div([
        html.Button(category,
                    id=f'button-{category}',
                    n_clicks=0,
                    className=f'btn btn-outline-primary mr-1 category-btn btn-category-{category.replace(" ", "-")}')
        for category in categories
    ] + [html.Button("Reset Filter",  # Add this line
                     id="reset-button",
                     n_clicks=0,
                     className="btn btn-outline-danger ml-2 reset-btn")],  # Add this line
        className='mb-4 d-flex justify-content-center'),
    html.Div(
        dcc.Graph(id='bubble-chart', config={'displayModeBar': False}),
        style={'border': 'none', 'background-color': 'rgba(0,0,0,0)'}
    ),
    dcc.Store(id='active-category', storage_type='memory'),
    html.Div(id='background-click', n_clicks=0, style={
        'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'zIndex': -1})
], className='wrapper')


# Define the callback function
@app.callback(
    Output('bubble-chart', 'figure'),
    Output('active-category', 'data'),
    [Input(f'button-{category}', 'n_clicks')
     for category in categories] + [Input("reset-button", "n_clicks")],
    State('active-category', 'data')
)
def update_bubble_chart(*n_clicks_and_active_category):
    n_clicks = n_clicks_and_active_category[:-2]
    reset_clicks = n_clicks_and_active_category[-2]
    active_category = n_clicks_and_active_category[-1]

    # Get the button_ids from the categories
    button_ids = [f'button-{category}' for category in categories]

    # Find the clicked button
    clicked_button_idx = None
    max_clicks = -1
    for i, n_click in enumerate(n_clicks):
        if n_click > max_clicks:
            clicked_button_idx = i
            max_clicks = n_click

    if reset_clicks > 0 and active_category is not None:
        # Reset the filter
        clicked_category = None
        active_category = None
    elif clicked_button_idx is not None and max_clicks > 0:
        clicked_category = button_ids[clicked_button_idx].replace(
            "button-", "")
    else:
        clicked_category = active_category

    # Filter the dataframe based on the clicked category, if any
    if clicked_category is not None:
        filtered_df = df[df['category'] ==
                         clicked_category].reset_index(drop=True)
    else:
        filtered_df = df

    # Create the bubble chart with the filtered dataframe
    fig = px.scatter(filtered_df,
                     x='critics percent score',
                     y='percent budget recovered',
                     size='worldwide gross ($m)',
                     color='category',
                     color_discrete_map=category_colors,
                     title=None,
                     hover_name='film',
                     hover_data={
                         'worldwide gross ($m)': True, 'percent budget recovered': ':.2f', 'critics percent score': ':.2f', 'film': True},
                     )

    hover_template = "<b>Film:</b> %{hovertext}<br>" \
        "<b>Critics Percent Score:</b> %{x:.2f}%<br>" \
        "<b>Percent Budget Recovered:</b> %{y:.2f}%<br>" \
        "<b>Worldwide Gross ($m):</b> %{marker.size:,.0f}"

    fig.update_traces(hovertemplate=hover_template,
                      textposition='top center',
                      textfont_size=10)

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=dict(x=0.5, font=dict(size=24)),
        xaxis=dict(
            title=dict(font=dict(size=10, color='rgba(255, 255, 255, 0.1)')),
            tickfont=dict(size=14, color='rgba(255, 255, 255, 0.1)',
                          family='SFMono-Regular, sans-serif'),
            gridcolor='rgba(0,0,0,0)',
            showline=True,
            linewidth=0.2,
            linecolor='rgba(255, 255, 255, 0.1)',
            tickformat=",.0f",
            tickprefix="",
            ticksuffix="%",
            ticks="inside"
        ),
        yaxis=dict(
            title=dict(font=dict(size=10, color='rgba(255, 255, 255, 0.1)')),
            tickfont=dict(size=14, color='rgba(255, 255, 255, 0.1)',
                          family='SFMono-Regular, sans-serif'),
            gridcolor='rgba(0,0,0,0)',
            showline=True,
            linewidth=0.2,
            linecolor='rgba(255, 255, 255, 0.1)',
            tickformat=",.0f",
            tickprefix="",
            ticksuffix="%",
            ticks="inside"
        ),
        showlegend=False,
        margin=dict(
            t=60,  # Adjust the top margin to make room for the logo
            b=60, l=40, r=40  # Adjust the bottom, left, and right margins as needed
        ),
        images=[dict(
            source='data:image/png;base64,{}'.format(encoded_logo.decode()),
            xref="paper", yref="paper",
            x=0.5, y=1,  # You can adjust the position of the logo here
            sizex=0.2, sizey=0.2,  # You can adjust the size of the logo here
            xanchor="center", yanchor="bottom",
            layer="above"
        )]
    )

    fig.update_traces(textposition='top center', textfont_size=10)

    return fig, clicked_category


if __name__ == '__main__':
    app.run_server(debug=True)
