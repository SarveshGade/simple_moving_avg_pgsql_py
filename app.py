from flask import Flask, render_template, url_for, request
import psycopg2
from psycopg2 import sql
import pandas as pd
import pandas.io.sql as sqlio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import base64
import dotenv
from sqlalchemy import create_engine

app = Flask(__name__)

# The hashmap with each ticker and corresponding table
stock_map = {'aapl' : "aapl_price",
                'msft' : "msft_price",
                'nvda' : "nvda_price",
                'tsla' : "tsla_price",
                'goog' : "goog_price",
                'amzn' : 'amzn_price',
                'meta' : "meta_price",
                'btc' : "btc_price",
                'eth' : "eth_price",
                'avax' : "avax_price",
                'sol' : "sol_price"}

def setStock(my_stock):
    """
    Maps user input to a specific table name which is used to display the respective plot
    """
    return stock_map.get(my_stock)

def get_db_connection():
    """
    Sets the db connection
    """
    conn = psycopg2.connect(host="localhost", database=
                        "stock_price_db", user=os.environ.get('postgresUSER'), password=os.environ.get('postgresPASSWORD'))
    return conn

@app.route('/')

def ask_user():
    """
    Asks the user what stock/crypto they want a graph for
    """
    return render_template('ask_user.html')

@app.route('/display')
def index():
    # Receive input
    my_stock = request.args.get('stock', '')
    if my_stock not in stock_map:
        return render_template('incorrect_input.html')

    # Set connection and cursor
    conn = get_db_connection()
    cur = conn.cursor()

    # Create engine
    engine = create_engine('postgresql+psycopg2://postgres:ProspectDisc123!@localhost/stock_price_db')

    # Sets up the query for table_df to read
    table_name = setStock(my_stock=my_stock).lower()
    query = sql.SQL("""SELECT date_time, price, CAST(AVG(price)
                    OVER (ORDER BY date_time ROWS BETWEEN 9 PRECEDING AND CURRENT ROW)
                    AS numeric(10,2)) AS price_sma_1hr, CAST(AVG(price) 
                    OVER (ORDER BY date_time ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) 
                    AS numeric(10,2)) AS price_sma_15m FROM {} WHERE date_time::date=now()::date;""").format(sql.Identifier(table_name))
    query_str = query.as_string(conn)

    # Create DataFrame using pandas dataframe
    table_df = pd.read_sql_query(query_str, con=engine)

    # Make figure
    fig = Figure(figsize=(15, 8))
    axis = fig.add_subplot(1,1,1)
    axis.plot('date_time', 'price', data=table_df, marker='', color='olive', linewidth=1)
    axis.plot( 'date_time', 'price_sma_1hr', data=table_df, marker='', color='blue', linewidth=1)
    axis.plot( 'date_time', 'price_sma_15m', data=table_df, marker='', color='red', linewidth=1)
    axis.legend()

    # Set title
    axis.set_title("Simple Moving Average for " + my_stock.upper())

    # Set axes labels
    axis.set_ylabel("Price (USD)")
    axis.set_xlabel("Date and Time")

    # Convert plot to PNG
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)

    # Encode PNG to base64
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    # Return html wit da image
    return render_template("index.html", image=pngImageB64String)

if __name__ =="__main__":
    app.run(debug=True)