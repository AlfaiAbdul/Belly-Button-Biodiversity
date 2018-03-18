
# Dependencies

import pandas as pd
import numpy as np

# Flask (Server)
from flask import Flask, jsonify, render_template, request, flash, redirect

# SQL Alchemy 
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc,select


# Setups for Database

engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite")

# reflection of Database
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
Base.classes.keys()
# Reference to the tables
OTU = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata= Base.classes.samples_metadata

# Creating session from Python to the DB
session = Session(engine)


# Flask 
app = Flask(__name__)

# Returns the dashboard homepage
@app.route("/")
def index():
    return render_template("index.html")


# Returns a list of sample names
@app.route('/names')
def names():
    """Return a list of sample names."""

    # Pandas for sql query
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    df.set_index('otu_id', inplace=True)

    # Returning list of the column names (sample names)
    return jsonify(list(df.columns))


# Returning list of OTU descriptions 
@app.route('/otu')
def otu():
    """Return a list of OTU descriptions."""
    results = session.query(OTU.lowest_taxonomic_unit_found).all()

    # Use numpy ravel to extract list of tuples into a list of OTU descriptions
    otu_list = list(np.ravel(results))
    return jsonify(otu_list)


# Returns a json dictionary of sample metadata 
@app.route('/metadata/<sample>')
def sample_metadata(sample):
    """Return the MetaData for a given sample."""
    sel = [Samples_Metadata.SAMPLEID, Samples_Metadata.ETHNICITY,
           Samples_Metadata.GENDER, Samples_Metadata.AGE,
           Samples_Metadata.LOCATION, Samples_Metadata.BBTYPE]

    # sample[3:] strips the `BB_` prefix from the sample name to match
    # the numeric value of `SAMPLEID` from the database
    results = session.query(*sel).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()

    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata['SAMPLEID'] = result[0]
        sample_metadata['ETHNICITY'] = result[1]
        sample_metadata['GENDER'] = result[2]
        sample_metadata['AGE'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['BBTYPE'] = result[5]

    return jsonify(sample_metadata)


# Returning int for weekly washing frequency 
@app.route('/wfreq/<sample>')
def sample_wfreq(sample):
    """Return the Weekly Washing Frequency as a number."""

    # "sample[3:]" to strip  "BB_" 
    results = session.query(Samples_Metadata.WFREQ).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()
    wfreq = np.ravel(results)

    # Returning first int for washing frequency
    return jsonify(int(wfreq[0]))


# Returning list of dictionaries containing (otu_ids, sample_values)
@app.route('/samples/<sample>')
def samples(sample):
    """Return a list dictionaries containing `otu_ids` and `sample_values`."""
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)

    # testing to ensure samples were found in the columns, otherwise (error)
    if sample not in df.columns:
        return jsonify(f"Error! Sample: {sample} Not Found!"), 400

    # Returning samples greater than 1
    df = df[df[sample] > 1]

    # Sort by descending 
    df = df.sort_values(by=sample, ascending=0)

    # sending data as json after formating
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)
if __name__ == "__main__":
    app.run(debug=True)