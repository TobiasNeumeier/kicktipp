import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd

from firebase_utils import read_dataframe_from_firestore

# Initialize the Dash app
app = dash.Dash(__name__)

# prepare data
df = (
	read_dataframe_from_firestore("all_bets")
	.groupby("Name")["Tip"].agg(**{
		"Total Tips Submitted": "count",
		"V-Mann Count": lambda x: ((x == "2:1") | (x == "1:2")).sum()
	}).assign(**{
		"Total Tips Possible": lambda _df: max(_df["Total Tips Submitted"]),
		"V-Mann Relative Frequency": lambda _df: _df["V-Mann Count"] / _df["Total Tips Possible"]
	})
	.sort_values("V-Mann Count", ascending=False)
)

# Create a horizontal bar chart
trace = go.Bar(
	x=df['V-Mann Relative Frequency'],
	y=df.index,
	orientation='h',
	marker=dict(color='rgba(50, 171, 96, 0.6)')
)

layout = go.Layout(
	title="Wer ist der V-Mann des Games?",
	xaxis=dict(title="Wie krass V-Mann"),
	margin=dict(l=150)  # Adjust margin to accommodate longer labels
)

fig = go.Figure(data=[trace], layout=layout)

# Define the layout of the app
app.layout = html.Div(children=[
	html.H1(children='Darkest Tippspiel'),
	dcc.Graph(
		id='v-mann',
		figure=fig
	)
])

# Expose the Flask server (app.server) for WSGI
server = app.server

# Run the app
if __name__ == '__main__':
	app.run_server(debug=True)
