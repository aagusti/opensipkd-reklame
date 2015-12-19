import sys
import requests
import json
from tools import json_rpc_header

argv = sys.argv

# def main(argv=sys.argv):
url = 'http://localhost:6543/ws/reklame'
if argv[1:]:
    pass
else:
    from config import (
        username,
        pass_encrypted,
    )

headers = json_rpc_header(username, pass_encrypted)
def upload(method):
    params = dict(data='')
    data = dict(jsonrpc = '2.0',
                method = method,
                params = params,
                id = 1)
    jsondata = json.dumps(data, ensure_ascii=False)
    print('Send to {url}'.format(url=url))
    print(jsondata)          
    rows = requests.post(url, data=jsondata, headers=headers)
    print('Result:')
    a = json.loads(rows.text)
    print(a)
    return a['result']

b = upload('get_jenis_reklame')

if b['code'] == 0:
    b = upload('get_ketinggian')
if b['code'] == 0:
    b = upload('get_lokasi')
if b['code'] == 0:
    b = upload('get_nssr')
if b['code'] == 0:
    b = upload('get_sudut_pandang')
if b['code'] == 0:
    b = upload('get_kelas_jalan')
if b['code'] == 0:
    b = upload('get_faktor_lain')
if b['code'] == 0:
    b = upload('get_kecamatan')
if b['code'] == 0:
    b = upload('get_kelurahan')
if b['code'] == 0:
    b = upload('get_jalan')

