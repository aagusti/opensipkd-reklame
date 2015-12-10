from email.utils import parseaddr
from sqlalchemy import not_
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
from ...models.pemda import (
    Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now

SESS_ADD_FAILED = 'urusan add failed'
SESS_EDIT_FAILED = 'urusan edit failed'

########                    
# List #
########    
@view_config(route_name='urusan', renderer='templates/urusan/list.pt',
             permission='urusan')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='Pajak Reklame')
    
##########                    
# Action #
##########    
@view_config(route_name='urusan-act', renderer='json',
             permission='urusan-act')
def urusan_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(Urusan)
        rowTable = DataTables(req, Urusan, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='headofnama':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Urusan.id, Urusan.nama
                       ).filter(Urusan.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r     
		
    elif url_dict['act']=='headofkode':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Urusan.id, Urusan.kode
                       ).filter(Urusan.kode.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
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
        q = DBSession.query(Urusan).filter_by(id=uid)
        urusan = q.first()
    else:
        urusan = None
        
    q = DBSession.query(Urusan).filter_by(kode=value['kode'])
    found = q.first()
    if urusan:
        if found and found.id != urusan.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = Urusan.get_by_nama(value['nama'])
        if urusan:
            if found and found.id != urusan.id:
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

class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "Kode",)
    nama = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Uraian",)

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = Urusan()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Urusan %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('urusan'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='urusan-add', renderer='templates/urusan/add.pt',
             permission='urusan-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #req.session[SESS_ADD_FAILED] = e.render()    
                return dict(form=form)	                  
                return HTTPFound(location=request.route_url('urusan-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    #return dict(form=form.render())
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Urusan).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Urusan ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='urusan-edit', renderer='templates/urusan/edit.pt',
             permission='urusan-edit')
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
    #return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='urusan-delete', renderer='templates/urusan/delete.pt',
             permission='urusan-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Urusan ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())

