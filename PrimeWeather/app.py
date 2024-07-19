# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(autoload_with=engine)


# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    return (
        f"Welcome to the Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - relativedelta(years=1)

    precipitation_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago)
        .order_by(Measurement.date)
        .all()
    )

    session.close()

    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    stations_data = session.query(Station.station).all()
    session.close()

    stations_list = list(np.ravel(stations_data))
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_active_station = (
        session.query(Measurement.station, func.count(Measurement.station).label('count'))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()
    )[0]

    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - relativedelta(years=1)

    temperature_data = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.station == most_active_station)
        .filter(Measurement.date >= one_year_ago)
        .order_by(Measurement.date)
        .all()
    )

    session.close()

    temperature_list = list(np.ravel(temperature_data))
    return jsonify(temperature_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    session = Session(engine)
    
    if not end:
        end = session.query(func.max(Measurement.date)).scalar()

    temperature_data = (
        session.query(
            func.min(Measurement.tobs).label("min_temp"),
            func.avg(Measurement.tobs).label("avg_temp"),
            func.max(Measurement.tobs).label("max_temp")
        )
        .filter(Measurement.date >= start)
        .filter(Measurement.date <= end)
        .all()
    )

    session.close()

    temperature_dict = {
        "start_date": start,
        "end_date": end,
        "min_temp": temperature_data[0].min_temp,
        "avg_temp": temperature_data[0].avg_temp,
        "max_temp": temperature_data[0].max_temp
    }
    return jsonify(temperature_dict)

if __name__ == "__main__":
    app.run(debug=True)