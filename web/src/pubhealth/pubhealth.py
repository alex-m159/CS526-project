from . import create_app
from flask import render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from flask_cors import cross_origin
import clickhouse_connect
from clickhouse_connect.driver import httputil
from threading import Thread
import time
import polars as pl
 
pool_manager = httputil.get_pool_manager(maxsize=5, num_pools=5)


# client2 = clickhouse_connect.get_client(pool_mgr=pool_manager)



app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route("/", methods=['GET'])
def home():
    return render_template('pubhealth/dist/index.html')

@socketio.on('message')
def handle_message():
    print(f'Received socket IO message: ')
    emit('response', {'field': 'value'})

def ws_respond(query, name, emit): 
    clickhouse = clickhouse_connect.get_client(host='localhost', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    with clickhouse.query_row_block_stream(f'{query}') as stream:
        total_rows = stream.source.summary['total_rows_to_read']
        read_rows = 0
        for block in stream:
            read_rows += len(block)
            if read_rows == total_rows:
                emit('data', {'data': block, 'end': False, 'name': name})
            else:
                emit('data', {'data': block, 'end': True, 'name': name })


def ws_respond_setup(query, emit): 
    clickhouse = clickhouse_connect.get_client(host='localhost', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    with clickhouse.query_row_block_stream(f'{query}') as stream:
        for (i, block) in enumerate(stream):
            emit('setup', {'data': block})
            

        
        
    

@socketio.on('query')
def ws_data(query, name):
    ws_respond(query, name, emit)


@socketio.on('setup')
def ws_setup(query):
    """
    A websocket endpoint dedicated to getting setup data for a component's initial setup.
    It's exactly the same as ws_data in usage, but this makes it easy for the frontend
    to distinguish between message types.
    """
    t = Thread(target=ws_respond_setup, args=(query, emit)) 
    t.daemon = True
    t.run()


@socketio.on('neighbors')
def neighboring(low_income_perc, high_income_perc):
    clickhouse = clickhouse_connect.get_client(host='localhost', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    print(f'Running neighboring with {low_income_perc}, {high_income_perc}')
    res = clickhouse.query('''
        SELECT STATE_COUNTY_FIPS_left, GINI_left, AVG_AGI_left, STATE_COUNTY_FIPS_right, GINI_right, AVG_AGI_right 
        FROM cps_00004.neighboring_counties
    ''')
    df = pl.from_dicts(res.named_results(), infer_schema_length=400)
    df = df.select(
        pl.col('STATE_COUNTY_FIPS_left'), 
        pl.col('GINI_left'), 
        pl.col('AVG_AGI_left').cast(pl.Float64), 
        pl.col('STATE_COUNTY_FIPS_right'), 
        pl.col('GINI_right'), 
        pl.col('AVG_AGI_right').cast(pl.Float64)
    )
    poor = df['AVG_AGI_left'].quantile(0.10)
    rich = df['AVG_AGI_left'].quantile(0.90)

    poor_near_poor = df\
    .filter(pl.col('AVG_AGI_left') <= poor )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( AVG_AGI_right_max=pl.col('AVG_AGI_right').max() )\
    .filter( pl.col('AVG_AGI_right_max') <= poor )

    rich_near_rich = df\
    .filter( pl.col('AVG_AGI_left') >= rich )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( AVG_AGI_right_max=pl.col('AVG_AGI_right').max() )\
    .filter( pl.col('AVG_AGI_right_max') >= rich )

    poor_near_rich = df\
    .filter(pl.col('AVG_AGI_left') <= poor )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( AVG_AGI_right_max=pl.col('AVG_AGI_right').max() )\
    .filter( pl.col('AVG_AGI_right_max') >= rich )

    # Notice that this uses min in the agg, not max
    rich_near_poor = df\
    .filter(pl.col('AVG_AGI_left') >= rich )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( AVG_AGI_right_max=pl.col('AVG_AGI_right').min() )\
    .filter( pl.col('AVG_AGI_right_max') <= poor )

    pnp_fips = poor_near_poor.select(['STATE_COUNTY_FIPS_left'])
    renamed_pnp = df\
    .join(pnp_fips, on='STATE_COUNTY_FIPS_left', how='inner')\
    .rename({
        'STATE_COUNTY_FIPS_left': 'STATE_COUNTY_FIPS_focus',
        'GINI_left': 'GINI_focus',
        'AVG_AGI_left': 'AVG_AGI_focus',
        'STATE_COUNTY_FIPS_right': 'STATE_COUNTY_FIPS_adj',
        'GINI_right': 'GINI_adj',
        'AVG_AGI_right': 'AVG_AGI_adj'
    })

    rnr_fips = rich_near_rich.select(['STATE_COUNTY_FIPS_left'])
    renamed_rnr = df\
    .join(rnr_fips, on='STATE_COUNTY_FIPS_left', how='inner')\
    .rename({
        'STATE_COUNTY_FIPS_left': 'STATE_COUNTY_FIPS_focus',
        'GINI_left': 'GINI_focus',
        'AVG_AGI_left': 'AVG_AGI_focus',
        'STATE_COUNTY_FIPS_right': 'STATE_COUNTY_FIPS_adj',
        'GINI_right': 'GINI_adj',
        'AVG_AGI_right': 'AVG_AGI_adj'
    })

    pnr_fips = poor_near_rich.select(['STATE_COUNTY_FIPS_left'])
    renamed_pnr = df\
    .join(pnr_fips, on='STATE_COUNTY_FIPS_left', how='inner')\
    .rename({
        'STATE_COUNTY_FIPS_left': 'STATE_COUNTY_FIPS_focus',
        'GINI_left': 'GINI_focus',
        'AVG_AGI_left': 'AVG_AGI_focus',
        'STATE_COUNTY_FIPS_right': 'STATE_COUNTY_FIPS_adj',
        'GINI_right': 'GINI_adj',
        'AVG_AGI_right': 'AVG_AGI_adj'
    })

    rnp_fips = rich_near_poor.select(['STATE_COUNTY_FIPS_left'])
    renamed_rnp = df\
    .join(rnp_fips, on='STATE_COUNTY_FIPS_left', how='inner')\
    .rename({
        'STATE_COUNTY_FIPS_left': 'STATE_COUNTY_FIPS_focus',
        'GINI_left': 'GINI_focus',
        'AVG_AGI_left': 'AVG_AGI_focus',
        'STATE_COUNTY_FIPS_right': 'STATE_COUNTY_FIPS_adj',
        'GINI_right': 'GINI_adj',
        'AVG_AGI_right': 'AVG_AGI_adj'
    })

    emit(
        'neighbors_result', 
        {
            'pnp': renamed_pnp.rows(),
            'rnr': renamed_rnr.rows(),
            'pnr': renamed_pnr.rows(),
            'rnp': renamed_rnp.rows()
        }
    )



@app.route("/query", methods=['POST'])
def provide_data():
    result = [ r for r in clickhouse.query(f"{request.data}").named_results()]
    return jsonify({'data': result})
    


if __name__ == "__main__":
    print("Running socketio")
    socketio.run(app)
