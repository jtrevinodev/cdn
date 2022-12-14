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


#############################################################
# METADATA MODULE
#############################################################

# Create metadata
@app.post("/content/new")
async def content_new(
    filename: str,
    size: int,
    uri: str
):
    content = await Content.objects.create(filename=filename, size=size, uri=uri)
    if not content:
        return {"status": "ERROR", "message": "Error creating content metadata."}
    
    content_json = content.dict()
    content_json['status'] = 'OK'

    return content_json

# Get metadata
@app.get("/content/{id}")
async def content_get(
    id: int
):
    content = await Content.objects.get_or_none(id=id)
    
    if not content:
        return {"status": "ERROR", "message": "Could not find content."}
    
    content_json = content.dict()
    content_json['status'] = 'OK'

    return content_json

# Update metadata
@app.put("/content/{id}")
async def content_update(
    id: int,
    filename: str,
    size: int,
    uri: str
):
    content = await Content.objects.get_or_none(id=id)
    
    if not content:
        return {"status": "ERROR", "message": "Could not find content."}
    
    # Update
    content.filename = filename
    content.size = size
    content.uri = uri
    
    await content.update()

    content_json = content.dict()
    content_json['status'] = 'OK'

    return content_json

# Get metadata
@app.delete("/content/{id}")
async def content_delete(
    id: int
):
    content = await Content.objects.get_or_none(id=id)
    
    if not content:
        return {"status": "ERROR", "message": "Could not find content."}
    
    await content.delete()

    resp = {}
    resp['status'] = 'OK'

    return resp

#############################################################

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
    
    for name,node in config['nodes'].items():
        if name != 'dist':
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