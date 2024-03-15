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

clickhouse = clickhouse_connect.get_client(host='localhost', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)

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
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    print('Running thread')
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!')
    # clickhouse = clickhouse_connect.get_client(pool_mgr=pool_manager)
    # result = [ r for r in clickhouse.query(f"{query}").named_results()]
    # with clickhouse.query_row_block_stream(f'{query}') as stream:
    # block = []
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
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    print('Running thread')
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    with clickhouse.query_row_block_stream(f'{query}') as stream:
        for (i, block) in enumerate(stream):
            emit('setup', {'data': block})
            

        
        
    

@socketio.on('query')
def ws_data(query, name):
    print('received query') 
    print('Running thread')
    # import pdb;pdb.set_trace()
    # print(app.routes())
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!')
    # clickhouse = clickhouse_connect.get_client(pool_mgr=pool_manager)
    # result = [ r for r in clickhouse.query(f"{query}").named_results()]
    # import pdb;pdb.set_trace()
    ws_respond(query, name, emit)
    # with clickhouse.query_row_block_stream(f'{query}') as stream:
    # block = []
    # with clickhouse.query_rows_stream(f'{query}') as stream:
    #     for (i, row) in enumerate(stream):
    #         # print(f'result so far: {i}')
    #         # if i % 20 == 0:
    #             # time.sleep(0.5)
    #         if len(block) >= 100:
    #             emit('data', {'data': block })
    #             block = []
    #         block.append(row)
    #     if block:
    #         emit('data', {'data': block})
    # t = Thread(target=ws_respond, args=(query, emit)) 
    # t.daemon = True
    # t.run()


@socketio.on('setup')
def ws_setup(query):
    """
    A websocket endpoint dedicated to getting setup data for a component's initial setup.
    It's exactly the same as ws_data in usage, but this makes it easy for the frontend
    to distinguish between message types.
    """
    print('received setup query') 
    t = Thread(target=ws_respond_setup, args=(query, emit)) 
    t.daemon = True
    t.run()


@socketio.on('neighboring')
def neighboring(low_income_perc, high_income_perc):
    res = clickhouse.query('''
        SELECT STATE_COUNTY_FIPS_left, GINI_left, AVG_AGI_left, STATE_COUNTY_FIPS_right, GINI_right, AVG_AGI_right 
        FROM neighboring_counties
    ''')
    df = pl.from_dicts(res.named_results(), infer_schema_length=400)
    poor = df['AVG_AGI_right'].quantile(0.10)
    rich = df['AVG_AGI_right'].quantile(0.90)

    poor_near_poor = df\
    .filter(pl.col('avg_agi_left') <= poor )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( avg_agi_right_max=pl.col('avg_agi_right').max() )\
    .filter( pl.col('avg_agi_right_max') <= poor )

    rich_near_rich = df\
    .filter( pl.col('avg_agi_left') >= rich )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( avg_agi_right_max=pl.col('avg_agi_right').max() )\
    .filter( pl.col('avg_agi_right_max') >= rich )

    poor_near_rich = df\
    .filter(pl.col('avg_agi_left') <= poor )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( avg_agi_right_max=pl.col('avg_agi_right').max() )\
    .filter( pl.col('avg_agi_right_max') >= rich )

    # Notice that this uses min in the agg, not max
    rich_near_poor = df\
    .filter(pl.col('avg_agi_left') >= rich )\
    .group_by('STATE_COUNTY_FIPS_left')\
        .agg( avg_agi_right_max=pl.col('avg_agi_right').min() )\
    .filter( pl.col('avg_agi_right_max') <= poor )
    emit(
        'neighbors_result', 
        {
            'pnp': poor_near_poor.rows(),
            'rnr': rich_near_rich.rows(),
            'pnr': poor_near_rich.rows(),
            'rnp': rich_near_poor.rows()
        }
    )



@app.route("/query", methods=['POST'])
def provide_data():
    result = [ r for r in clickhouse.query(f"{request.data}").named_results()]
    return jsonify({'data': result})
    


if __name__ == "__main__":
    print("Running socketio")
    socketio.run(app)
