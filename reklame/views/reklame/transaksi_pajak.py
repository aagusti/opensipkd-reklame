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
    Kecamatan, Kelurahan, KelasJalan, Jalan, Pemilik, Rekening, OPreklame, TransaksiPajak
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now,_DTnumberformat,_DTstrftime

SESS_ADD_FAILED = 'Transaksi Pajak add failed'
SESS_EDIT_FAILED = 'Transaksi Pajak edit failed'

########                    
# List #
########    
@view_config(route_name='reklame-transaksi', renderer='templates/transaksi/list.pt',
             permission='reklame-transaksi')
def view_list(request):
    return dict(project='Pajak Reklame')
    
##########                    
# Action #
##########    
@view_config(route_name='reklame-transaksi-act', renderer='json',
             permission='reklame-transaksi-act')
def transaksi_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('tahun'))
        columns.append(ColumnDT('nopd'))
        columns.append(ColumnDT('no_skpd'))
        columns.append(ColumnDT('op_reklames.nama'))
        columns.append(ColumnDT('periode_awal',  filter=_DTstrftime))
        columns.append(ColumnDT('periode_akhir', filter=_DTstrftime))
        columns.append(ColumnDT('jumlah_byr',    filter=_DTnumberformat))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(TransaksiPajak)
        rowTable = DataTables(req, TransaksiPajak, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('tahun'))
        columns.append(ColumnDT('nopd'))
        columns.append(ColumnDT('no_skpd'))
        columns.append(ColumnDT('op_reklames.nama'))
        columns.append(ColumnDT('periode_awal',  filter=_DTstrftime))
        columns.append(ColumnDT('periode_akhir', filter=_DTstrftime))
        columns.append(ColumnDT('jumlah_byr',    filter=_DTnumberformat))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(TransaksiPajak
                        ).join(OPreklame
                        ).filter(TransaksiPajak.op_reklame_id == OPreklame.id,
                                 or_(TransaksiPajak.kode.ilike('%%%s%%' % cari),
                                     TransaksiPajak.nama.ilike('%%%s%%' % cari),
                                     OPreklame.nama.ilike('%%%s%%' % cari),
                                     )
                        )
        rowTable = DataTables(req, TransaksiPajak, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon_transaksi':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(TransaksiPajak.id, 
                               TransaksiPajak.kode, 
                               TransaksiPajak.nama, 
                               TransaksiPajak.nopd, 
                               TransaksiPajak.no_skpd
                       ).filter(TransaksiPajak.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['nopd']    = k[3]
            d['skpd']    = k[4]
            r.append(d)
        return r   
           
    elif url_dict['act']=='hok_transaksi':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(TransaksiPajak.id, 
                               TransaksiPajak.kode, 
                               TransaksiPajak.nama, 
                               TransaksiPajak.nopd, 
                               TransaksiPajak.no_skpd
                       ).filter(TransaksiPajak.kode.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['nopd']    = k[3]
            d['skpd']    = k[4]
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
        q = DBSession.query(TransaksiPajak).filter_by(id=uid)
        transaksi = q.first()
    else:
        transaksi = None
        
    q = DBSession.query(TransaksiPajak).filter_by(kode=value['kode'])
    found = q.first()
    if transaksi:
        if found and found.id != transaksi.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = TransaksiPajak.get_by_nama(value['nama'])
        if transaksi:
            if found and found.id != transaksi.id:
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
                    title = "Kode",)
    nama          = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Uraian",)
    op_reklame_id = colander.SchemaNode(
                    colander.Integer(),
                    oid="op_reklame_id",
                    missing=colander.drop)
    op_reklame_nm = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="op_reklame_nm",
                    title="Objek",)
    tahun         = colander.SchemaNode(
                    colander.Integer(),
                    oid="tahun",
                    missing=colander.drop,
                    title="Tahun",)
    nopd          = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="nopd",
                    title="NOPD",)
    npwpd         = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="npwpd",
                    title="NPWPD",)
    periode_awal  = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="periode_awal",
                    title="Periode")
    periode_akhir = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="periode_akhir",
                    title="Tgl akhir")
    no_skpd       = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="no_skpd",
                    title="No.SKPD")
    tgl_skpd      = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="tgl_skpd",
                    title="Tanggal")
    no_bayar      = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="no_bayar",
                    title="No.Bayar")
    tgl_bayar     = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="tgl_bayar",
                    title="Tanggal")
    no_permohonan = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="no_permohonan",
                    title="Nomor")
    id_permohonan = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="id_permohonan",
                    title="Permohonan")
    tgl_permohonan = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="tgl_permohonan",
                    title="Tanggal")
    no_sk_ipr     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="no_sk_ipr",
                    title="No.SK IPR")
    tgl_sk_ipr    = colander.SchemaNode(
                    colander.Date(),
                    #missing=colander.drop,
                    oid="tgl_sk_ipr",
                    title="Tanggal")
    nilai_pjk     = colander.SchemaNode(
                    colander.Integer(),
                    #missing=colander.drop,
                    oid="nilai_pjk",
                    title="Nilai",
                    default=1)
    denda_pjk     = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="denda_pjk",
                    title="Denda",
                    default=0)
    jumlah_byr    = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="jumlah_byr",
                    title="Jumlah.Bayar")
    wp_nama       = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="wp_nama",
                    title="WP",)
    wp_alamat     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="wp_alamat",
                    title="Alamat WP",)
    jumlah_op     = colander.SchemaNode(
                    colander.Integer(),
                    missing=colander.drop,
                    oid="jumlah_op",
                    title="Jumlah",
                    default=1)
    naskah        = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="naskah",
                    title="Naskah",)
    disabled      = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status)

class EditSchema(AddSchema):
    id = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))

def save_request2(row1=None):
    row1 = OPreklame()
    return row1
    
def save(values, user, row=None):
    if not row:
        row = TransaksiPajak()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    
    row.from_dict(values) 

    if not row.jumlah_byr:
        a = "%s" % row.nilai_pjk
        b = "%s" % row.denda_pjk
        d = int(a)
        e = int(b)
        c = d + e
        row.jumlah_byr = c 
        print '-------nilai-------',a
        print '-------denda-------',b
        print '-------jumlah------',c
        
    DBSession.add(row)
    DBSession.flush()
    
    #Untuk update disabled pada Objek Pajak Reklame
    a = row.op_reklame_id
    row1 = DBSession.query(OPreklame).filter(OPreklame.id==a).first()   
    row1.disabled=1
    save_request2(row1)
    
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Transaksi Pajak %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('reklame-transaksi'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='reklame-transaksi-add', renderer='templates/transaksi/add.pt',
             permission='reklame-transaksi-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)				
                return HTTPFound(location=request.route_url('reklame-transaksi-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(TransaksiPajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Transaksi Pajak ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='reklame-transaksi-edit', renderer='templates/transaksi/edit.pt',
             permission='reklame-transaksi-edit')
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
    values['op_reklame_nm'] = row and row.op_reklames.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='reklame-transaksi-delete', renderer='templates/transaksi/delete.pt',
             permission='reklame-transaksi-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Transaksi Pajak ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,form=form.render())
