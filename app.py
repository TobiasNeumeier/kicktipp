import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output
from firebase_utils import read_dataframe_from_firestore

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(children=[
	html.H1(children='Darkest Tippspiel'),
	dcc.Graph(
		id='live-vmann-graph'
	),
	dcc.Interval(
		id='interval-component',
		interval=60 * 1000,  # Update every 15 minutes (in milliseconds)
		n_intervals=0  # Number of intervals that have passed
	)
])


# prepare data
def update_data() -> pd.DataFrame:
	return (
		read_dataframe_from_firestore("all_bets")
		.groupby("Name")["Tip"].agg(**{
			"Total Tips Submitted": "count",
			"V-Mann Count": lambda x: ((x == "2:1") | (x == "1:2")).sum()
		}).assign(**{
			"Total Tips Possible": lambda _df: max(_df["Total Tips Submitted"]),
			"V-Mann Relative Frequency": lambda _df: _df["V-Mann Count"] / _df["Total Tips Possible"]
		})
		.sort_values("V-Mann Count", ascending=True)
	)


@app.callback(
	Output('live-vmann-graph', 'figure'),
	Input('interval-component', 'n_intervals')
)
def update_bar_chart(n_intervals):
	df = update_data()
	# Create a horizontal bar chart
	trace = go.Bar(
		x=df['V-Mann Relative Frequency'],
		y=df.index,
		orientation='h',
		marker=dict(color='rgba(50, 171, 96, 0.6)')
	)
	
	layout = go.Layout(
		title="Wer ist der V-Mann des Games?",
		xaxis=dict(
			title="Wie krass V-Mann\n(2:1 Tipps in %)",
			range=[0, 1],
			tickformat=",.0%"
		),
		margin=dict(l=150),  # Adjust margin to accommodate longer labels
		bargap=0.4,
		yaxis=dict(
			title="Name",
			automargin=True,
			tickmode="array",
			tickvals=df.index,
			ticktext=df.index,
			tickfont=dict(size=14)
		)
	)
	fig = go.Figure(data=[trace], layout=layout)
	return fig


# Expose the Flask server (app.server) for WSGI
server = app.server

# Run the app
if __name__ == '__main__':
	app.run_server(debug=True)
