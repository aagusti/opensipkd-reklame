from ..ws import (auth_from_rpc, LIMIT, CODE_OK, CODE_NOT_FOUND, CODE_DATA_INVALID, 
                   CODE_INVALID_LOGIN, CODE_NETWORK_ERROR)
from pyramid_rpc.jsonrpc import jsonrpc_method
from ...models import DBSession
from ...models.reklame import (Transaksi, Njop, JenisNssr, Nssr, Ketinggian, Sudut,Lokasi,
                              FaktorLain,KelasJalan,JenisReklame, Jalan)
from ...models.reklame import (Kecamatan, Kelurahan)
from datetime import datetime

def hitung_pajak(row):
    row.luas = row.panjang * row.lebar
    row.jml_luas         = row.luas*row.muka*row.jumlah_titik
    
    tmp_row           = JenisReklame.get_by_id(row.jenis_reklame_id)
    row.masa_pajak_id = tmp_row.masa_pajaks.id
    row.pembagi       = tmp_row.masa_pajaks.pembagi
    row.accres        = tmp_row.masa_pajaks.accres
    
    row.jenis_reklame_ni = Njop.search_by_luas(
                            row.jenis_reklame_id, row.luas).nilai
    
    row.jenis_reklame_ni = Njop.search_by_luas(
                            row.jenis_reklame_id, row.luas).nilai
    row.ketinggian_ni    = Ketinggian.get_by_id(row.ketinggian_id).nilai
    row.jml_ketinggian   = round(row.tinggi*row.ketinggian_ni)
    row.nssr_ni          = Nssr.search_by_luas(row.jenis_nssr_id,row.luas).nilai
    row.kelas_jalan_ni   = KelasJalan.get_by_id(row.kelas_jalan_id).nilai
    row.sudut_pandang_ni = Sudut.get_by_id(row.sudut_pandang_id).nilai
    row.lokasi_pasang_ni = Lokasi.get_by_id(row.lokasi_pasang_id).nilai
    row.nssr             = (row.kelas_jalan_ni+row.sudut_pandang_ni
                           +row.lokasi_pasang_ni)*row.nssr_ni
                                    
    row.faktor_lain_ni   = FaktorLain.get_by_id(row.faktor_lain_id).tarif
                                    
    row.nsr            = row.jenis_reklame_ni+row.nssr+row.jml_ketinggian
    if row.pembagi>1:
        row.nsr = round(row.nsr/row.pembagi)
    if row.accres>0:
        row.nsr = round(row.nsr + row.accres*row.nsr/100)
        
    row.dasar          = round(row.nsr*row.jml_luas)
    row.tarif          = JenisReklame.get_by_id(row.jenis_reklame_id).tarif
    row.pokok          = round(row.dasar*row.tarif/100)
    row.denda          = 0
    row.bunga          = 0
    row.kompensasi     = row.faktor_lain_ni<0 and row.faktor_lain_ni/100*row.pokok or 0
    row.kenaikan       = row.faktor_lain_ni>0 and row.faktor_lain_ni/100*row.pokok or 0
    row.lain           = 0
    row.jml_terhutang  = row.pokok+row.denda+row.bunga+row.kenaikan+row.lain-row.kompensasi
    row.status         = 1
    row.kode = "{no}-{id}".format(
                  no = row.no_permohonan,
                  id = str(row.id_permohonan).rjust(3,'0')
                  )
    row.nama_wp = row.nama_pemohon
    return row
            
@jsonrpc_method(method='set_izin', endpoint='ws_reklame')
def set_izin(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
    #if 1==1:
        ret_data =[]
        for r in data:
            query = DBSession.query(Transaksi).\
                       filter_by(no_permohonan=r['no_permohonan'],
                                 id_permohonan=str(r['id_permohonan']))
            row = query.first()
            if row:
                if row.no_skpd: #Jika sudah ditetapkan di skip
                    ret_data.append(dict(no_permohonan = row.no_permohonan,
                                     id_permohonan = row.id_permohonan,
                                     command       = r['command'],
                                     status        = -1,
                                     message       = 'Data Sudah Ditetapkan'))
                    continue 
                elif int(r['command'])==1:
                    ret_data.append(dict(no_permohonan = row.no_permohonan,
                                     id_permohonan = row.id_permohonan,
                                     command       = r['command'],
                                     status        = -1,
                                     message       = 'Data Sudah Ada'))
                    continue                  
                elif int(r['command'])==2:
                    row.update_uid = user.id
                    row.updated    = datetime.now()
                    
                elif int(r['command'])==3:
                    query.delete()
                    ret_data.append(dict(no_permohonan = row.no_permohonan,
                                         id_permohonan = row.id_permohonan,
                                         command       = r['command'],
                                         status        = 0))
                    continue 
                    
            else:
                if int(r['command'])==1:
                    row = Transaksi()
                    row.create_uid = user.id
                    row.created    = datetime.now()
                else:
                    ret_data.append(dict(no_permohonan = r['no_permohonan'],
                                     id_permohonan = r['id_permohonan'],
                                     command       = r['command'],
                                     status        = -2,
                                     message       = "Data Tidak Ditemukan"))
                    continue 
            row.from_dict(r)
            row.nama = r['naskah']
            row = hitung_pajak(row)
            ret_data.append(dict(no_permohonan = row.no_permohonan,
                             id_permohonan = row.id_permohonan,
                             jml_terhutang = row.jml_terhutang,
                             command       = r['command'],
                             status        = 0,
                             message       = "Sukses"))
            DBSession.add(row)
        DBSession.flush()

    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_izin', endpoint='ws_reklame')
def get_izin(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        for r in data:
            query = DBSession.query(Transaksi).\
                       filter_by(no_permohonan=r['no_permohonan'],
                                 id_permohonan=str(r['id_permohonan']))
            row = query.first()
            if not row:
                ret_data.append(dict(no_permohonan = r['no_permohonan'],
                                 id_permohonan = r['id_permohonan'],
                                 command       = r['command'],
                                 status        = -2,
                                 message       = "Data Tidak Ditemukan"))
            else:
                dicted =dict( status        = 0,
                             message       = "Success")
                dicted.update(row.to_dict())
                ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)


@jsonrpc_method(method='set_skpd', endpoint='ws_reklame')
def set_skpd(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    #try:
    if 1==1:
        ret_data =[]
        for r in data:
            row = DBSession.query(Transaksi).\
                       filter_by(no_permohonan=r['no_permohonan'],
                                 id_permohonan=str(r['id_permohonan'])).first()
            if not row:
                return dict(code=CODE_DATA_INVALID, message='Data Tidak Ada')
                
            row.from_dict(r)
            DBSession.add(row)
            ret_data.append(dict(no_permohonan=row.no_permohonan,
                                 id_permohonan=row.id_permohonan,
                                 #jml_terhutang=round(row.jml_terhutang),
                                 status = CODE_OK,
                                ))
        DBSession.flush()

    #except:
    #    return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_skpd', endpoint='ws_reklame')
def get_skpd(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    return get_izin(request,data)
    
@jsonrpc_method(method='get_tirek', endpoint='ws_reklame')
def get_tirek(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        for r in data:
            query = DBSession.query(Reklame).\
                       filter_by(kode=r['kode'])
            row = query.first()
            if not row:
                ret_data.append(dict(no_permohonan = r['no_permohonan'],
                                 id_permohonan = r['id_permohonan'],
                                 command       = r['command'],
                                 status        = -2,
                                 message       = "Data Tidak Ditemukan"))
            else:
                dicted =dict( status        = 0,
                             message       = "Success")
                dicted.update(row.to_dict())
                ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)
    
@jsonrpc_method(method='get_jenis_reklame', endpoint='ws_reklame')
def get_jenis_reklame(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(JenisReklame.id,JenisReklame.kode,JenisReklame.nama).\
                         order_by(JenisReklame.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_ketinggian', endpoint='ws_reklame')
def get_ketinggian(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(Ketinggian.id,Ketinggian.kode,Ketinggian.nama).\
                         order_by(Ketinggian.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_nssr', endpoint='ws_reklame')
def get_nssr(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
    #if 1==1:
        ret_data=[]
        rows = DBSession.query(JenisNssr.id,JenisNssr.kode,JenisNssr.nama).\
                         order_by(JenisNssr.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)
    
@jsonrpc_method(method='get_lokasi', endpoint='ws_reklame')
def get_lokasi(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(Lokasi.id,Lokasi.kode,Lokasi.nama).\
                         order_by(Lokasi.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)
    
@jsonrpc_method(method='get_sudut_pandang', endpoint='ws_reklame')
def get_sudut_pandang(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(Sudut.id,Sudut.kode,Sudut.nama).\
                         order_by(Sudut.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)
    
@jsonrpc_method(method='get_kelas_jalan', endpoint='ws_reklame')
def get_kelas_jalan(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(KelasJalan.id,KelasJalan.kode,KelasJalan.nama).\
                         order_by(KelasJalan.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_faktor_lain', endpoint='ws_reklame')
def get_faktor_lain(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(FaktorLain.id,FaktorLain.kode,FaktorLain.nama).\
                         order_by(FaktorLain.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)

@jsonrpc_method(method='get_kecamatan', endpoint='ws_reklame')
def get_kecamatan(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(Kecamatan.id,Kecamatan.kode,Kecamatan.nama).\
                         order_by(Kecamatan.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)
    

@jsonrpc_method(method='get_kelurahan', endpoint='ws_reklame')
def get_kelurahan(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    try:
        ret_data=[]
        rows = DBSession.query(Kelurahan.id,Kelurahan.kode,Kelurahan.nama, Kelurahan.kecamatan_id).\
                         order_by(Kelurahan.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    except:
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)    

@jsonrpc_method(method='get_jalan', endpoint='ws_reklame')
def get_jalan(request, data):
    resp,user = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    #try:
    if 1==1:
        ret_data=[]
        rows = DBSession.query(Jalan.id,Jalan.kode,Jalan.nama, Jalan.kelas_jalan_id).\
                         order_by(Jalan.id)
        keys = rows.first().keys()
        for row in rows.all():
            dicted ={}
            for i in range(0, len(keys)):
                dicted[keys[i]]=row[i]
            ret_data.append(dicted)
    #except:
    #    return dict(code=CODE_DATA_INVALID, message='Data Invalid')
    params=dict(data=ret_data)
    return dict(code=CODE_OK, message='Data Submitted',params=params)    
    