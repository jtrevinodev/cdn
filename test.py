import requests, os, uuid, random, io
import re

client_dir = 'client_data/'
dist_url = 'http://127.0.0.1:8000'

def main():
    init_storage()
    test()

def test():
    # Generate sample file
    fpath = generate_file(1024*1024, 10*1024*1024) # G3 medium-size files between 1 MB and 10MB)
    print('File generated: ', fpath)

    file_size = os.path.getsize(fpath)

    ##########################################################
    # Request storage URL
    ##########################################################
    request_url = dist_url + '/request_store/?size='+str(file_size)
    resp = requests.get(url=request_url)
    
    node = resp.json()

    if node['status'] == 'OK':
        ##########################################################
        # Upload and store file
        ##########################################################
        url = node['url'] + '/store'

        print('Store URL: ', url)

        file = {'file': open(fpath, 'rb')}
        params = {'uri': node['url']}
        resp = requests.post(url=url, params=params, files=file)
        content = resp.json()
        print(content)

        ##########################################################
        # Locate file URL
        ##########################################################
        request_url = dist_url + '/locate/'+str(content['id'])
        resp = requests.get(url=request_url)
        
        uri = resp.json()

        ##########################################################
        # Retrieve uploaded file
        ##########################################################
        request_url = uri['uri'] + '/retrieve/'+str(content['id'])

        with requests.get(request_url, stream=True) as r:
            r.raise_for_status()
            d = r.headers['content-disposition']
            print(r.headers)

            filename = re.findall("filename=(.+)", d)[0]
            filename = filename.replace("\"", "")

            fpath = os.path.join('tmp/', filename)

            with open(fpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        
            print("File retrieved. Stored at: ", fpath)
        
        ##########################################################
        # Update content
        ##########################################################
        # generate new sample file
        fpath = generate_file(1024*1024, 10*1024*1024) # G3 medium-size files between 1 MB and 10MB)
        print('File generated: ', fpath)

        file_size = os.path.getsize(fpath)
        
        ##########################################################
        # Request storage URL for the new content
        ##########################################################
        request_url = dist_url + '/request_store/?size='+str(file_size)
        resp = requests.get(url=request_url)
        
        node = resp.json()

        if node['status'] == 'OK':
            ##########################################################
            # Upload and store new file
            ##########################################################
            url = node['url'] + '/update'

            print('New Store URL: ', url)
            
            file = {'file': open(fpath, 'rb')}
            params = {'id': content['id'], 'uri': node['url']}
            resp = requests.put(url=url, params=params, files=file)
            new_content = resp.json()
            print(new_content)

            ##########################################################
            # Locate updated file URL
            ##########################################################
            request_url = dist_url + '/locate/'+str(content['id'])
            resp = requests.get(url=request_url)
            uri = resp.json()
            print(uri)

            print('Updated file located at: ', uri['uri'])

            ##########################################################
            # Delete uploaded file
            ##########################################################
            # request_url = uri['uri'] + '/delete/'+str(content['id'])
            # resp = requests.delete(url=request_url)
            # print(resp.json())


    else:
        print(node['message'])



def generate_file(min_size, max_size):
    # Generate file
    filename = str(uuid.uuid1())
    file_path = os.path.join(client_dir, filename) #file_path = os.path.join(dir_path, filename)
    size = random.randint(min_size, max_size)

    with io.open(file_path,'w',encoding='utf8') as f:
        f.write('0' * size)

    
    return file_path


def init_storage():
    # create storage dir if not exists
    if not os.path.exists(client_dir):
        os.makedirs(client_dir)

main()