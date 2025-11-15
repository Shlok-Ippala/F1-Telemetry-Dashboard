# In app.py (the main file in your root project folder)

import dash
from dash import dcc, html, Input, Output
import fastf1

# Import the layouts from your page files
from pages import home, lap_comparison, race_comparison

# Enable FastF1 caching (do this once in your main app file)
fastf1.Cache.enable_cache('data/cache')

# Initialize the Dash app
# suppress_callback_exceptions is needed because we are rendering pages dynamically
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "F1 Analytics Dashboard"
server = app.server

# Define the main layout of the app
app.layout = html.Div([
    # This component holds the URL of the page
    dcc.Location(id='url', refresh=False),

    # This component is where the page content will be rendered
    html.Div(id='page-content')
])

# This callback changes the 'page-content' based on the URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/lap-comparison':
        return lap_comparison.layout
    elif pathname == '/race-comparison':
        return race_comparison.layout
    else:
        # The default page is the home page
        return home.layout

# Run the app
if __name__ == '__main__':
    app.run(debug=True)