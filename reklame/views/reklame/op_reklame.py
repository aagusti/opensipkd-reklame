from email.utils import parseaddr
from sqlalchemy import not_, or_
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ...models import(
    DBSession,
    )
from ...models.reklame import (
    Kecamatan, Kelurahan, KelasJalan, Jalan, Sudut, Lokasi, Pemilik, 
    Rekening, Jenis, Ketinggian, Reklame, Transaksi
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now,_DTnumberformat

SESS_ADD_FAILED = 'Objek Pajak add failed'
SESS_EDIT_FAILED = 'Objek Pajak edit failed'

########                    
# List #
########    
@view_config(route_name='reklame-opreklame', renderer='templates/op_reklame/list.pt',
             permission='reklame-opreklame')
def view_list(request):
    return dict(project='Pajak Reklame')
    
##########                    
# Action #
##########    
@view_config(route_name='reklame-opreklame-act', renderer='json',
             permission='reklame-opreklame-act')
def opreklame_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('rekenings.nama'))
        columns.append(ColumnDT('kelurahans.nama'))
        columns.append(ColumnDT('jalans.nama'))
        columns.append(ColumnDT('jenis_reklames.nama'))
        columns.append(ColumnDT('luas'))
        columns.append(ColumnDT('status'))
        
        query = DBSession.query(Reklame)
        rowTable = DataTables(req, Reklame, query, columns)
        return rowTable.output_result()
       
    elif url_dict['act']=='hon_op':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Reklame.id,           # 0
                               Reklame.kode,         # 1
                               Reklame.nama,         # 2
                               Reklame.jumlah_titik, # 3
                               Reklame.rekening_id,  # 4
                               Rekening.nama,        # 5
                               Reklame.jalan_id,     # 6
                               Reklame.jenis_reklame_id,     # 6
                               Jenis.nama,           # 7
                               Jenis.nilai,          # 8
                               Reklame.sudut_id,     # 9
                               Sudut.kode,           # 10
                               Sudut.nama,           # 11
                               Reklame.panjang,      # 12
                               Reklame.lebar,        # 13
                               Reklame.luas,         # 14
                               Reklame.tinggi,       # 15
                               Reklame.muka,         # 16
                               Reklame.lahan_id,     # 17
                               Reklame.bersinar,     # 18
                               Reklame.menempel,     # 19
                               Reklame.dalam_ruang,  # 20
                               Reklame.lokasi_id,    # 21
                               Lokasi.kode,          # 22
                               Lokasi.nama,          # 23
                               Reklame.pemilik_id,   # 24
                       ).join(Rekening, Jenis, Sudut, Lokasi, Pemilik
                       ).filter(Reklame.rekening_id == Rekening.id,
                                Reklame.jenis_reklame_id    == JenisReklame.id,
                                Reklame.sudut_id    == Sudut.id,
                                Reklame.lokasi_id   == Lokasi.id,
                                Reklame.pemilik_id  == Pemilik.id,
                                Reklame.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d=k.todict()
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['jml']     = k[3]
            # --------------- #
            # d['rek_id']  = k[4]
            # d['rek_nm']  = k[5]
            # d['jal_id']  = k[6]
            # d['jen_id']  = k[7]
            # d['jen_nm']  = k[7]
            # d['jen_ni']  = k[8]
            # d['sud_id']  = k[9]
            # d['sud_kd']  = k[10]
            # d['sud_nm']  = k[11]
            # d['lok_id']  = k[21]
            # d['lok_kd']  = k[22]
            # d['lok_nm']  = k[23]
            # d['pem_id']  = k[24]
            # # ---------------- #
            # d['panjang'] = k[12]
            # d['lebar']   = k[13]
            # d['luas']    = k[14]
            # d['tinggi']  = k[15]
            # d['muka']    = k[16]
            # d['lahan']   = k[17]
            # d['sinar']   = k[18]
            # d['nempel']  = k[19]
            # d['druang']  = k[20]
            
            r.append(d)
        return r   
           
    elif url_dict['act']=='hok_op':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Reklame.id, 
                               Reklame.kode, 
                               Reklame.nama, 
                               Reklame.jumlah_titik
                       ).filter(Reklame.kode.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['jml']     = k[3]
            r.append(d)
        return r    
             
    
#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))
    def err_nama():
        raise colander.Invalid(form,
            'Nama %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Reklame).filter_by(id=uid)
        opreklame = q.first()
    else:
        opreklame = None
        
    #q = DBSession.query(Reklame).filter_by(kode=value['kode'])
    #found = q.first()
    #if opreklame:
    #    if found and found.id != opreklame.id:
    #        err_kode()
    #elif found:
    #    err_kode()
        
    if 'nama' in value: # optional
        found = Reklame.get_by_nama(value['nama'])
        if opreklame:
            if found and found.id != opreklame.id:
                err_nama()
        elif found:
            err_nama()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )     

# Untuk pilihan Sudut Pandang Reklame    
@colander.deferred    
def deferred_sudut(node, kw):
    values = kw.get('is_sudut', [])
    return widget.SelectWidget(values=values)
    
IS_SUDUT = (
    ('1 Arah', '1 Arah'),
    ('2 Arah', '2 Arah'),
    ('3 Arah', '3 Arah'),
    ('4 Arah', '4 Arah'),
    ('>4 Arah', '>4 Arah'),
    ('Berjalan/Kendaraan', 'Berjalan/Kendaraan'),
    ('Indoor', 'Indoor'),
    )
    
# Untuk pilihan Bersinar
@colander.deferred
def deferred_bersinar(node, kw):
    values = kw.get('daftar_bersinar', [])
    return widget.SelectWidget(values=values)
    
IS_BERSINAR = (
    (0, 'Tidak'),
    (1, 'Ya'),
    )     
    
# Untuk pilihan Menempel
@colander.deferred
def deferred_menempel(node, kw):
    values = kw.get('daftar_menempel', [])
    return widget.SelectWidget(values=values)
    
IS_MENEMPEL = (
    (0, 'Tidak'),
    (1, 'Ya'),
    )
    
# Untuk pilihan Dalam Ruang
@colander.deferred
def deferred_druang(node, kw):
    values = kw.get('daftar_druang', [])
    return widget.SelectWidget(values=values)
    
IS_DRUANG = (
    (0, 'Tidak'),
    (1, 'Ya'),
    )     
    
# Untuk pilihan Lahan
@colander.deferred
def deferred_lahan(node, kw):
    values = kw.get('daftar_lahan', [])
    return widget.SelectWidget(values=values)
    
IS_LAHAN = (
    (1, 'Pemda'),
    (2, 'Swasta'),
    )     


class AddSchema(colander.Schema):
    kode          = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "NOPR",
                    missing=colander.drop)
    nama          = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Keterangan",)
    pemilik_id    = colander.SchemaNode(
                    colander.Integer(),
                    oid="pemilik_id",
                    missing=colander.drop)
    pemilik_kd    = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="pemilik_kd",
                    title="Pemilik",)
    pemilik_nm    = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="pemilik_nm",
                    title="Pemilik",)
    rekening_id   = colander.SchemaNode(
                    colander.Integer(),
                    oid="rekening_id",
                    missing=colander.drop)
    rekening_nm   = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="rekening_nm",
                    title="Rekening",)
    lokasi_id     = colander.SchemaNode(
                    colander.Integer(),
                    oid="lokasi_id",
                    missing=colander.drop)
    lokasi_kd     = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="lokasi_kd",
                    title="Lokasi",)
    lokasi_nm     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="lokasi_nm",
                    title="Lokasi",)
    jenis_reklame_id      = colander.SchemaNode(
                    colander.Integer(),
                    oid="jenis_reklame_id",
                    missing=colander.drop)
    jenis_reklame_nm = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="jenis_reklame_nm",
                    title="Jenis Reklame",)
    kecamatan_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="kecamatan_id",
                    missing=colander.drop)
    kecamatan_kd  = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="kecamatan_kd",
                    title="Kecamatan",)
    kecamatan_nm  = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kecamatan_nm",
                    title="Kecamatan",)
    kelurahan_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="kelurahan_id",
                    missing=colander.drop)
    kelurahan_kd  = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="kelurahan_kd",
                    title="Kelurahan",)
    kelurahan_nm  = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kelurahan_nm",
                    description='pop up',
                    title="Kelurahan",)
    jalan_id      = colander.SchemaNode(
                    colander.Integer(),
                    oid="jalan_id",
                    missing=colander.drop)
                    
                    
    jalan_kd      = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="jalan_kd",
                    title="Jalan",)
    jalan_nm      = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="jalan_nm",
                    title="Jalan",)
    kelas_jalan_id= colander.SchemaNode(
                    colander.Integer(),
                    oid="kelas_jalan_id",
                    missing=colander.drop)
    kelas_jalan_kd= colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="kelas_jalan_kd",
                    title="Kelas Jalan",)
    kelas_jalan_nm= colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kelas_jalan_nm",
                    title="Kelas Jalan",)
                    
    ketinggian_id= colander.SchemaNode(
                    colander.Integer(),
                    oid="ketinggian_id",
                    missing=colander.drop)
    ketinggian_kd= colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="ketinggian_kd",
                    title="Ketinggian",)
    ketinggian_nm= colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="ketinggian_nm",
                    title="Ketinggian",)
    #alamat        = colander.SchemaNode(
    #                colander.String(),
    #                missing=colander.drop,
    #                oid="alamat",
    #                title="Alamat",)
    no_urut       = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="no_urut",
                    title="No. Urut",)
    panjang       = colander.SchemaNode(
                    colander.Float(),
                    widget = widget.MoneyInputWidget(
                                 options={'allowZero':True, 'precision':1}),
                    oid="panjang",
                    title="Panjang",
                    default=1)
    lebar         = colander.SchemaNode(
                    colander.Float(),
                    widget = widget.MoneyInputWidget(
                                 options={'allowZero':True, 'precision':1}),
                    oid="lebar",
                    title="Lebar",
                    default=1)
    luas          = colander.SchemaNode(
                    colander.Float(),
                    widget = widget.MoneyInputWidget(
                                 options={'allowZero':True, 'precision':1}),
                    missing=colander.drop,
                    default = 1.0,
                    oid="luas",
                    title="Luas")
    tinggi        = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="tinggi",
                    title="Tinggi",
                    default=1)
    muka          = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="muka",
                    title="Muka",
                    default=1)
    sudut_id      = colander.SchemaNode(
                    colander.Integer(),
                    oid="sudut_id",
                    missing=colander.drop)
    sudut_kd      = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="sudut_kd",
                    title="Sdt Pandang",)
    sudut_nm      = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="sudut_nm",
                    title="Sdt Pandang",)
    jumlah_titik  = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="jumlah_titik",
                    title="Jumlah",
                    default=1)
    koordinat_x   = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="koordinat_x",
                    title="Koordinat:X",
                    default=0)
    koordinat_y   = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="koordinat_y",
                    title="Y",
                    default=0)
    lahan_id      = colander.SchemaNode(
                    colander.Integer(),
                    oid="lahan",
                    title="Lahan",
                    widget=deferred_lahan)
    bersinar      = colander.SchemaNode(
                    colander.Integer(),
                    oid="bersinar",
                    title="Bersinar",
                    widget=deferred_bersinar)
    menempel      = colander.SchemaNode(
                    colander.Integer(),
                    oid="menempel",
                    title="Menempel",
                    widget=deferred_menempel)
    dalam_ruang   = colander.SchemaNode(
                    colander.Integer(),
                    oid="dalam_ruang",
                    title="Dalam Ruang",
                    widget=deferred_druang)
    status      = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status)

class EditSchema(AddSchema):
    id = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_lahan=IS_LAHAN,
                         daftar_bersinar=IS_BERSINAR,
                         daftar_menempel=IS_MENEMPEL,
                         daftar_druang=IS_DRUANG,)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))

# Untuk update status status #    
def save_request1(row1=None):
    row1 = Pemilik()
    return row1    
    
def save_request2(row2=None):
    row2 = Rekening()
    return row2    
    
def save_request3(row3=None):
    row3 = Kelurahan()
    return row3    
    
def save_request4(row4=None):
    row4 = Jalan()
    return row4    
    
#def save_request5(row5=None):
#    row5 = Ketinggian()
#    return row5    
    
def save_request6(row6=None):
    row6 = Jenis()
    return row6
    
def save_request7(row7=None):
    row7 = Lokasi()
    return row7    
    
def save_request8(row8=None):
    row8 = Sudut()
    return row8
#------------------------------#    
    
def save(values, user, row=None):
    if not row:
        row = Reklame()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    
    row.from_dict(values) 
    
    if not row.no_urut:
        row.no_urut = Reklame.max_no_urut(row.kelurahan_id, row.jalan_id)+1;
    
    if not row.kode:
        r_kel = DBSession.query(Kelurahan).filter(Kelurahan.id == row.kelurahan_id).first()
        jal   = DBSession.query(Jalan).filter(Jalan.id == row.jalan_id).first()
        row.kode = "{kec}.{kel}.{jal}.{nomor}".format(
                        kec = r_kel.kecamatans.kode,
                        kel = r_kel.kode,
                        jal = jal.kode,
                        nomor = str(row.no_urut).rjust(4,'0'),
                        )       
    DBSession.add(row)
    DBSession.flush()
    
    
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Objek Pajak %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('reklame-opreklame'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='reklame-opreklame-add', renderer='templates/op_reklame/add.pt',
             permission='reklame-opreklame-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)				
                return HTTPFound(location=request.route_url('reklame-opreklame-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Reklame).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Objek Pajak ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='reklame-opreklame-edit', renderer='templates/op_reklame/edit.pt',
             permission='reklame-opreklame-edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['pemilik_kd']    = row and row.pemiliks.kode       or ''
    values['pemilik_nm']    = row and row.pemiliks.nama       or ''
    values['rekening_nm']   = row and row.rekenings.nama      or ''
    values['kecamatan_kd']  = row and row.kecamatans.kode     or ''
    values['kecamatan_nm']  = row and row.kecamatans.nama     or ''
    values['kelurahan_kd']  = row and row.kelurahans.kode     or ''
    values['kelurahan_nm']  = row and row.kelurahans.nama     or ''
    values['lokasi_kd']     = row and row.lokasi_pasangs.kode or ''
    values['lokasi_nm']     = row and row.lokasi_pasangs.nama or ''
    values['sudut_kd']      = row and row.sudut_pandangs.kode or ''
    values['sudut_nm']      = row and row.sudut_pandangs.nama or ''
    values['jalan_kd']      = row and row.jalans.kode         or ''
    values['jalan_nm']      = row and row.jalans.nama         or ''
    values['jenis_reklame_nm']  = row and row.jenis_reklames.nama          or ''
    values['kelas_jalan_kd']      = row and row.kelas_jalans.kode         or ''
    values['kelas_jalan_nm']      = row and row.kelas_jalans.nama         or ''
    values['kelas_jenis_id']      = row and row.kelas_jalans.id          or ''
    values['ketinggian_kd']      = row and row.ketinggians.kode         or ''
    values['ketinggian_nm']      = row and row.ketinggians.nama         or ''
    values['ketinggian_id']      = row and row.ketinggians.id          or ''
    
    #values['jenis_ni']      = row and row.jenis.nilai         or 0
    #values['ketinggian_nm'] = row and row.ketinggians.nama    or ''
    #values['ketinggian_ni'] = row and row.ketinggians.nilai   or 0
    
    #x = DBSession.query(Kecamatan.kode).filter(Kecamatan.nama==values['kecamatan']).first()   
    #values['kecamatan_kd'] = "%s" % x
    
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='reklame-opreklame-delete', renderer='templates/OP_reklame/delete.pt',
             permission='reklame-opreklame-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    uid = row.id
    
    if not row:
        return id_not_found(request)
        
    a = DBSession.query(Transaksi).filter(Transaksi.reklame_id==uid).first()
    if a:
        request.session.flash('Data tidak bisa dihapus, karena sudah masuk di Transaksi Pajak.', 'error')
        return route_list(request)

    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Objek Pajak ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,form=form.render())
