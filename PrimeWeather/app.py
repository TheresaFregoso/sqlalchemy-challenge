# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker

#################################################
# Flask Setup
#################################################
# Initialize a Flask application
app = Flask(__name__)

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
# Map classes
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a scoped session
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Ensure the session is removed after each request
@app.teardown_appcontext
def remove_session(exception=None):
    Session.remove()

# Function to get dynamic dates
def get_dynamic_dates():
    most_recent_date = Session.query(func.max(Measurement.date)).first()[0]
    most_recent_date = dt.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - relativedelta(years=1)
    return most_recent_date.strftime("%Y-%m-%d"), one_year_ago.strftime("%Y-%m-%d")

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    most_recent_date, one_year_ago = get_dynamic_dates()
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/{one_year_ago}<br/>"
        f"/api/v1.0/{one_year_ago}/{most_recent_date}<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year ago from today
    most_recent_date, one_year_ago = get_dynamic_dates()

    # Query the last 12 months of precipitation data
    precipitation_data = (
        Session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago)
        .order_by(Measurement.date)
        .all()
    )

    # Convert the query results to a dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Query all stations
    results = Session.query(Station.station).all()

    # Convert the query results to a list
    stations_list = [station[0] for station in results]
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date one year ago from today
    most_recent_date, one_year_ago = get_dynamic_dates()

    # Identify the most active station
    active_station = (
        Session.query(Measurement.station, func.count(Measurement.station).label('count'))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()[0]
    )

    # Query the temperature observations of the most active station for the last year
    results = (
        Session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.station == active_station)
        .filter(Measurement.date >= one_year_ago)
        .all()
    )

    # Convert the query results to a list of dictionaries with date and tobs
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in results]
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
def temperature_stats_start(start):
    try:
        start_date = dt.strptime(start, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400

    results = (
        Session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))
        .filter(Measurement.date >= start_date)
        .all()
    )

    temp_stats = list(np.ravel(results))
    return jsonify(temp_stats)

@app.route("/api/v1.0/<start>/<end>")
def temperature_stats_start_end(start, end):
    try:
        start_date = dt.strptime(start, "%Y-%m-%d")
        end_date = dt.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400

    results = (
        Session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))
        .filter(Measurement.date >= start_date)
        .filter(Measurement.date <= end_date)
        .all()
    )

    temp_stats = list(np.ravel(results))
    return jsonify(temp_stats)

if __name__ == "__main__":
    app.run(debug=True)
