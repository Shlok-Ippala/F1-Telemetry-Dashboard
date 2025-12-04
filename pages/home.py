# In pages/home.py

print("--- Python is EXECUTING pages/home.py ---")

from dash import html, dcc

# Feature cards data
cards = [
    {
        'title': 'Qualifying Analysis',
        'description': 'Compare driver telemetry, lap deltas, and track dominance across qualifying sessions',
        'href': '/lap-comparison',
        'delay': '0s'
    },
    {
        'title': 'Weekend Analysis',
        'description': 'Analyze race lap times, tire strategies, and team aero performance',
        'href': '/race-comparison',
        'delay': '0.15s'
    },
    {
        'title': 'Year Analysis',
        'description': 'Track championship points progression and season-long driver performance',
        'href': '/year-analysis',
        'delay': '0.3s'
    }
]

def create_feature_card(card_data):
    return dcc.Link(
        html.Div([
            html.H3(card_data['title'], className='card-title'),
            html.P(card_data['description'], className='card-description')
        ], className='feature-card', style={'animationDelay': card_data['delay']}),
        href=card_data['href'],
        style={'textDecoration': 'none'}
    )

layout = html.Div([
    # Hero section
    html.Div([
        html.H1("F1 Analytics Dashboard", className='hero-title'),
        html.P("Dive deep into Formula 1 telemetry and statistics", className='hero-subtitle'),
    ], className='hero-section'),
    
    # Feature cards
    html.Div([
        create_feature_card(card) for card in cards
    ], className='cards-container')
], className='home-container')