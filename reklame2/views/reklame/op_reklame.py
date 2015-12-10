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
    Kecamatan, Kelurahan, KelasJalan, Jalan, Pemilik, Rekening, Nsr, Ketinggian, OPreklame, TransaksiPajak
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now

SESS_ADD_FAILED = 'Objek Pajak add failed'
SESS_EDIT_FAILED = 'Objek Pajak edit failed'

########                    
# List #
########    
@view_config(route_name='reklame-opreklame', renderer='templates/OP_reklame/list.pt',
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
        columns.append(ColumnDT('rek_nsr.nilai'))
        columns.append(ColumnDT('jumlah'))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(OPreklame)
        rowTable = DataTables(req, OPreklame, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('rekenings.nama'))
        columns.append(ColumnDT('kelurahans.nama'))
        columns.append(ColumnDT('jalans.nama'))
        columns.append(ColumnDT('rek_nsr.nilai'))
        columns.append(ColumnDT('jumlah'))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(OPreklame
                        ).join(Kelurahan, Jalan, Rekening, Pemilik
                        ).filter(OPreklame.pemilik_id    == Pemilik.id,
                                 OPreklame.rekening_id   == Rekening.id,
                                 OPreklame.rek_nsr_id    == Nsr.id,
                                 OPreklame.kelurahan_id  == Kelurahan.id,
                                 OPreklame.jalan_id      == Jalan.id,
                                 OPreklame.ketinggian_id == Ketinggian.id,
                                 or_(OPreklame.kode.ilike('%%%s%%' % cari),
                                     OPreklame.nama.ilike('%%%s%%' % cari),
                                     Rekening.nama.ilike('%%%s%%' % cari),
                                     Kelurahan.nama.ilike('%%%s%%' % cari),
                                     Jalan.nama.ilike('%%%s%%' % cari),
                                     )
                        )
        rowTable = DataTables(req, OPreklame, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon_op':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(OPreklame.id, 
                               OPreklame.kode, 
                               OPreklame.nama, 
                               OPreklame.jumlah
                       ).filter(OPreklame.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['jml']     = k[3]
            r.append(d)
        return r   
           
    elif url_dict['act']=='hok_op':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(OPreklame.id, 
                               OPreklame.kode, 
                               OPreklame.nama, 
                               OPreklame.jumlah
                       ).filter(OPreklame.kode.ilike('%%%s%%' % term) 
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
        q = DBSession.query(OPreklame).filter_by(id=uid)
        opreklame = q.first()
    else:
        opreklame = None
        
    #q = DBSession.query(OPreklame).filter_by(kode=value['kode'])
    #found = q.first()
    #if opreklame:
    #    if found and found.id != opreklame.id:
    #        err_kode()
    #elif found:
    #    err_kode()
        
    if 'nama' in value: # optional
        found = OPreklame.get_by_nama(value['nama'])
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
    (0, 'Inactive'),
    (1, 'Active'),
    )     

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

class AddSchema(colander.Schema):
    kode          = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "NOPR",
                    missing=colander.drop)
    nama          = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Uraian",)
    pemilik_id    = colander.SchemaNode(
                    colander.Integer(),
                    oid="pemilik_id",
                    missing=colander.drop)
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
    rek_nsr_id   = colander.SchemaNode(
                    colander.Integer(),
                    oid="rek_nsr_id",
                    missing=colander.drop)
    rek_nsr_nm   = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="rek_nsr_nm",
                    title="NSR",)
    rek_nsr_ni   = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="rek_nsr_ni",
                    title="Nilai",)
    kelurahan_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="kelurahan_id",
                    missing=colander.drop)
    kelurahan_nm  = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kelurahan_nm",
                    description='pop up',
                    title="Kelurahan",)
    kecamatan     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kecamatan",
                    title="Kecamatan",)
    kecamatan_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="kecamatan_id",
                    missing=colander.drop)
    kabupaten     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="kabupaten",
                    title="Kabupaten",)
    provinsi      = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="provinsi",
                    title="Provinsi",)
    jalan_id      = colander.SchemaNode(
                    colander.Integer(),
                    oid="jalan_id",
                    missing=colander.drop)
    jalan_nm      = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="jalan_nm",
                    title="Jalan",)
    alamat        = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="alamat",
                    title="Alamat",)
    no_urut       = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="no_urut",
                    title="No. Urut",)
    panjang       = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="panjang",
                    title="Panjang",
                    default=1)
    lebar         = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="lebar",
                    title="Lebar",
                    default=1)
    luas          = colander.SchemaNode(
                    colander.Float(),
                    missing=colander.drop,
                    oid="luas",
                    title="Luas")
    muka          = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="muka",
                    title="Muka",
                    default=1)
    sudut_pandang = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="sudut_pandang",
                    title="Sudut.Pandang",
                    widget=deferred_sudut)
    jumlah        = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="jumlah",
                    title="Jumlah",
                    default=1)
    ketinggian_id = colander.SchemaNode(
                    colander.Integer(),
                    oid="ketinggian_id",
                    missing=colander.drop)
    ketinggian_nm = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="ketinggian_nm",
                    title="Ketinggian",)
    ketinggian_ni = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="ketinggian_ni",
                    title="Nilai",)
    koordinat_x   = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="koordinat_x",
                    title="Koordinat",
                    default=0)
    koordinat_y   = colander.SchemaNode(
                    colander.Float(),
                    #missing=colander.drop,
                    oid="koordinat_y",
                    title="Koordinat Y",
                    default=0)
    disabled      = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status)

class EditSchema(AddSchema):
    id = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,is_sudut=IS_SUDUT)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))

# Untuk update status disabled #    
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
    
def save_request5(row5=None):
    row5 = Ketinggian()
    return row5    
    
def save_request6(row6=None):
    row6 = Nsr()
    return row6
#------------------------------#    
    
def save(values, user, row=None):
    if not row:
        row = OPreklame()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    
    row.from_dict(values) 
    
    if not row.no_urut:
        row.no_urut = OPreklame.max_no_urut(row.kelurahan_id, row.jalan_id)+1;
    
    if not row.kode:
        a = DBSession.query(Kelurahan.kode.label('kel'),
                            Kecamatan.kode.label('kec'),
                     ).join(Kecamatan
                     ).filter(Kelurahan.id == row.kelurahan_id,
                              Kelurahan.kecamatan_id == Kecamatan.id
                     ).first()
        kec = a.kec
        kel = a.kel 
        
        b = DBSession.query(Jalan.kode.label('jal'),
                     ).filter(Jalan.id == row.jalan_id,
                     ).first()
        jal = b.jal
        
        no_urut  = row.no_urut
        no       = "000%d" % no_urut
        nomor    = no[-4:] 
        
        #kecamatan + kelurahan + jalan + no_urut (007.001.001-0001)
        row.kode = "%s" % kec + ".%s" % kel + ".%s" % jal+ "-%s" % nomor        
    
    if not row.luas:
        a = "%s" % row.panjang
        b = "%s" % row.lebar
        c = float(a) * float(b) 
        row.luas = c 
        print '-------panjang-------',a
        print '--------lebar--------',b
        print '---------luas--------',c
        
    DBSession.add(row)
    DBSession.flush()
    
    a = row.pemilik_id
    b = row.rekening_id
    c = row.kelurahan_id
    d = row.jalan_id
    e = row.ketinggian_id
    f = row.rek_nsr_id
    
    #Untuk update disabled pada Pemilik
    row1 = DBSession.query(Pemilik).filter(Pemilik.id==a).first()   
    row1.disabled=1
    save_request1(row1)
    
    #Untuk update disabled pada Rekening
    row2 = DBSession.query(Rekening).filter(Rekening.id==b).first()   
    row2.disabled=1
    save_request2(row2)
    
    #Untuk update disabled pada Kelurahan
    row3 = DBSession.query(Kelurahan).filter(Kelurahan.id==c).first()   
    row3.disabled=1
    save_request3(row3)
    
    #Untuk update disabled pada Jalan
    row4 = DBSession.query(Jalan).filter(Jalan.id==d).first()   
    row4.disabled=1
    save_request4(row4)
    
    #Untuk update disabled pada Ketinggian
    row5 = DBSession.query(Ketinggian).filter(Ketinggian.id==e).first()   
    row5.disabled=1
    save_request5(row5)
    
    #Untuk update disabled pada NSR
    row6 = DBSession.query(Nsr).filter(Nsr.id==f).first()   
    row6.disabled=1
    save_request6(row6)
    
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
    
@view_config(route_name='reklame-opreklame-add', renderer='templates/OP_reklame/add.pt',
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
    return DBSession.query(OPreklame).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Objek Pajak ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='reklame-opreklame-edit', renderer='templates/OP_reklame/edit.pt',
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
    values['pemilik_nm']    = row and row.pemiliks.nama     or ''
    values['rekening_nm']   = row and row.rekenings.nama    or ''
    values['kelurahan_nm']  = row and row.kelurahans.nama   or ''
    values['jalan_nm']      = row and row.jalans.nama       or ''
    values['ketinggian_nm'] = row and row.ketinggians.nama  or ''
    values['ketinggian_ni'] = row and row.ketinggians.nilai or 0
    values['rek_nsr_nm']    = row and row.rek_nsr.nama      or ''
    values['rek_nsr_ni']    = row and row.rek_nsr.nilai     or 0
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
        
    a = DBSession.query(TransaksiPajak).filter(TransaksiPajak.op_reklame_id==uid).first()
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
