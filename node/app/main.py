from typing import Union

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse

import os
import shutil
import humanfriendly
import requests
import yaml

app = FastAPI()
config = yaml.safe_load(open('app/nodes.yml'))

dist_URL = 'http://'+config['nodes']['dist']['host'] + ':' + str(config['nodes']['dist']['port'])

storagePath = '/storage/'
maxStorage = humanfriendly.parse_size(os.environ.get('MAX_STORAGE', '0M'))
statsPath = '/sys/fs/cgroup/'

@app.get("/")
def read_root():
    return {"node": "storage"}


@app.post("/store")
async def store(uri: str, file: UploadFile = File(...)):
    
    try:
        # Store content
        with open(os.path.join(storagePath, file.filename), 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        fs = await file.read()
        
        #content = await Content.objects.create(filename=file.filename, size=len(fs), uri=uri)
        
        # Request to dist node to create metadata
        params = {
            'filename': file.filename,
            'size': len(fs),
            'uri':uri
        }
        url = dist_URL + '/content/new'
        resp = requests.post(url=url, params=params)
        content = resp.json()

        if content['status'] == 'OK':
            return {"id": content['id'], "message": f"Content successfully uploaded. ID: {content['id']}"}
        else:
            return content['message']

    except Exception as ex:
        return {"message": "There was an error uploading the content: "+str(ex)}
    finally:
        file.file.close()    
    


@app.get("/retrieve/{id}")
async def retrieve(id: int):
    #content = await Content.objects.get_or_none(id=id)

    url = dist_URL + '/content/'+str(id)
    resp = requests.get(url=url)
    content = resp.json()

    if content['status'] == 'OK':
        file_path = os.path.join(storagePath, content['filename'])
        return FileResponse(file_path, media_type='application/octet-stream', filename=content['filename'])
    

    return {"message": 'Could not find requested content.'}


@app.put("/update")
async def update(id: int, uri: str, file: UploadFile = File(...)):
    #content = await Content.objects.get_or_none(id=id)
    url = dist_URL + '/content/'+str(id)
    resp = requests.get(url=url)
    content = resp.json()

    if content['status'] == 'OK':
        try:
            
            #file_path = os.path.join(storagePath, content.filename) 
            #os.remove(file_path)

            # Remove old content
            request_url = content['uri'] + '/delete/'+str(content['id'])
            params = {'metadata': 0} # Delete only the content
            resp = requests.delete(url=request_url, params=params)
            respj = resp.json()

            if respj['status'] == 'OK':
                # Store new content
                with open(os.path.join(storagePath, file.filename), 'wb') as f:
                    shutil.copyfileobj(file.file, f)
                
                fs = await file.read()

                # Update content metadata
                #content.filename = file.filename
                #content.size = len(fs)
                #content.uri = uri

                #await content.update()

                url = dist_URL + '/content/'+str(id)
                params = {
                    'filename': file.filename, 
                    'size': len(fs),
                    'uri': uri
                }
                resp = requests.put(url=url, params=params)
                content = resp.json()

                if content['status'] == 'OK':
                    return {"id": content['id'], "message": f"Content successfully updated. ID: {content['id']}"}
                else:
                    return {"status": "ERROR", "message": "Could not update content metadata."}
                
            else:
                return {"message": 'Could not delete old content.'}

        except Exception as ex:
            return {"message": "There was an error uploading the content: "+str(ex)}
        finally:
            file.file.close()
    else:
        return {"message": 'Could not find requested content.'}
        
    


@app.delete("/delete/{id}")
async def delete(id: int, metadata: int = 1):
    #content = await Content.objects.get_or_none(id=id)
    url = dist_URL + '/content/'+str(id)
    resp = requests.get(url=url)
    content = resp.json()

    if content['status'] == 'OK':
        # Remove content from disk
        file_path = os.path.join(storagePath, content['filename']) 
        os.remove(file_path)

        if metadata == 1:
            #await content.delete()
            url = dist_URL + '/content/'+str(content['id'])
            resp = requests.delete(url=url)
            content = resp.json()

            if not content['status'] == 'OK':
                return {"status":"ERROR", "message": 'Could not delete content metadata.'}
        
        return {"status":"OK","message": 'Content deteled successfully.'}
    
    return {"status":"ERROR", "message": 'Could not delete requested content.'}


@app.get("/stats/")
def stats():
    memory = 0
    storage = 0
    try:
        # Get current node stats
        f = open(os.path.join(statsPath, 'memory.current'), encoding = 'utf-8')
        memory = int(f.readline())
        storage = storage_size()
        storagep = storage * 100 / maxStorage # % of usage

    finally:
        f.close()

    return {'memory': memory, 'storage': storage , 'storagep': storagep, 'max_storage': maxStorage}


def storage_size():
    # assign size
    size = 0
    
    # get size
    for path, dirs, files in os.walk(storagePath):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    
    return size

