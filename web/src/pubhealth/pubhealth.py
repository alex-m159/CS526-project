from . import create_app
from flask import render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import cross_origin
import clickhouse_connect
from clickhouse_connect.driver import httputil
from threading import Thread
import time
 
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

def ws_respond(query, emit): 
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    print('Running thread')
    clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    # clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!')
    # clickhouse = clickhouse_connect.get_client(pool_mgr=pool_manager)
    result = [ r for r in clickhouse.query(f"{query}").named_results()]
    # with clickhouse.query_row_block_stream(f'{query}') as stream:
    block = []
    with clickhouse.query_rows_stream(f'{query}') as stream:
        for (i, row) in enumerate(stream):
            # print(f'result so far: {i}')
            # if i % 20 == 0:
                # time.sleep(0.5)
            if len(block) >= 100:
                emit('data', {'data': block})
                block = []
            block.append(row)

def ws_respond_setup(query, emit): 
    # Clickhouse does not support the execution of concurrent queries 
    # on one client, and they recommend using one client per thread.
    print('Running thread')
    clickhouse = clickhouse_connect.get_client(host='hub.publichealthhq.xyz', port=18123, username='default', password='Password123!', pool_mgr=pool_manager)
    with clickhouse.query_row_block_stream(f'{query}') as stream:
        for (i, block) in enumerate(stream):
            emit('setup', {'data': block})

        
        
    

@socketio.on('query')
def ws_data(query):
    print('received query') 
    t = Thread(target=ws_respond, args=(query, emit)) 
    t.daemon = True
    t.run()


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



@app.route("/query", methods=['POST'])
def provide_data():
    result = [ r for r in clickhouse.query(f"{request.data}").named_results()]
    return jsonify({'data': result})
    

if __name__ == "__main__":
    print("Running socketio")
    socketio.run(app)
