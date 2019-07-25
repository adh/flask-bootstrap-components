from flask import Flask, Blueprint, flash, render_template
from flask_bootstrap_components import FlaskBootstrapComponents
from flask_bootstrap_components.tables import PlainTable, PagedTable

app = Flask(__name__)

app.config['SECRET_KEY'] = 'foo'
FlaskBootstrapComponents(app)

@app.route('/')
def index():
    table = PlainTable(["Column 1",
                        "column 2",
                        "Column 3"],
                       [[i, i, i] for i in range(30)],
                       classes=["table-sm", "table-striped"])
    
    paged_table = PagedTable(["Column 1",
                              "column 2",
                              "Column 3"],
                             [[i, i, i] for i in range(35)],
                             anchor="paged_table",
                             classes=["table-sm", "table-striped"])
    
    return render_template("example.html",
                           table=table,
                           paged_table=paged_table)
