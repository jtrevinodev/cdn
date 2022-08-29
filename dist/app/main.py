from typing import Union

from fastapi import FastAPI, File, UploadFile
from app.db import database, Content

import shutil
import requests
import yaml
import json

app = FastAPI()
config = yaml.safe_load(open('app/nodes.yml'))

@app.get("/")
def read_root():
    return {"node": "dist"}


@app.get("/request_store/")
def request_store(
    size: int,
):
    stats = get_stats()

    # Test policy
    min_storage = float('inf')
    index = -1
    i = 0
    for node in stats:
        if node['storagep'] < min_storage and size < (node['max_storage'] - node['storage']):
            min_storage = node['storagep']
            index = i
        
        i += 1
    
    if index < 0:
        return {"url": '', 'status': 'STORAGE_OVERFLOW', 'message': 'Could not store content. Filesize exceeds capacity.'}
    
        
    return {"url": stats[index]['node'], 'status': 'OK', 'message': 'Store URL assigned.'}


@app.get("/locate/{id}")
async def locate(id: int):
    content = await Content.objects.get_or_none(id=id)
    if content:
        return {"uri": content.uri}
    else:
        return {"message": "Could not locate requested content."}


@app.get("/nodes")
def get_nodes():
    return {"nodes": config['nodes']}


@app.get("/stats")
def stats():
    stats = get_stats()

    return {"stats": stats}

def get_stats():
    endpoint = '/stats'
    stats = []
    
    for _,node in config['nodes'].items():
        # REQUEST NODE STATS
        node_url = 'http://'+node['host']+':'+str(node['port'])
        url = node_url + endpoint
        
        resp = requests.get(url=url)
        print(resp.json())
        
        resp_json = resp.json()
        resp_json['node'] = node_url

        stats.append(resp_json)
    
    return stats




@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()


@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()