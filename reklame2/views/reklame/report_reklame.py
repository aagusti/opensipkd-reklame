import os
import unittest
import os.path
import uuid
import urlparse

from datetime import datetime
from sqlalchemy import *
from sqlalchemy.sql.expression import literal_column
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
    
from datatables import ColumnDT, DataTables

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from ...models import DBSession, User
from ...models.reklame import *
from ...models.pemda import *
from ...views.base_view import _DTstrftime
from datetime import datetime

def get_rpath(filename):
    a = AssetResolver('reklame')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
angka = {1:'satu',2:'dua',3:'tiga',4:'empat',5:'lima',6:'enam',7:'tujuh',\
         8:'delapan',9:'sembilan'}
b = ' puluh '
c = ' ratus '
d = ' ribu '
e = ' juta '
f = ' milyar '
g = ' triliun '
def Terbilang(x):   
    y = str(x)         
    n = len(y)        
    if n <= 3 :        
        if n == 1 :   
            if y == '0' :   
                return ''   
            else :         
                return angka[int(y)]   
        elif n == 2 :
            if y[0] == '1' :                
                if y[1] == '1' :
                    return 'sebelas'
                elif y[0] == '0':
                    x = y[1]
                    return Terbilang(x)
                elif y[1] == '0' :
                    return 'sepuluh'
                else :
                    return angka[int(y[1])] + ' belas'
            elif y[0] == '0' :
                x = y[1]
                return Terbilang(x)
            else :
                x = y[1]
                return angka[int(y[0])] + b + Terbilang(x)
        else :
            if y[0] == '1' :
                x = y[1:]
                return 'seratus ' + Terbilang(x)
            elif y[0] == '0' : 
                x = y[1:]
                return Terbilang(x)
            else :
                x = y[1:]
                return angka[int(y[0])] + c + Terbilang(x)
    elif 3< n <=6 :
        p = y[-3:]
        q = y[:-3]
        if q == '1' :
            return 'seribu' + Terbilang(p)
        elif q == '000' :
            return Terbilang(p)
        else:
            return Terbilang(q) + d + Terbilang(p)
    elif 6 < n <= 9 :
        r = y[-6:]
        s = y[:-6]
        return Terbilang(s) + e + Terbilang(r)
    elif 9 < n <= 12 :
        t = y[-9:]
        u = y[:-9]
        return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewReklameLap():
    def __init__(self, context, request):
        self.context = context
        self.request = request
		
    # Laporan Reklame
    @view_config(route_name="reklame-opreklame-report", renderer="templates/report_reklame/reklame_report.pt", permission="reklame-opreklame-report")
    def reklame(self):
        params = self.request.params
        return dict()

    @view_config(route_name="reklame-opreklame-report-act", renderer="json", permission="reklame-opreklame-report-act")
    def reklame_act(self):
        global mulai, selesai, unit
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        unit         = 'unit'         in params and params['unit']         or 0
        rek          = 'rek'          in params and params['rek']        or 0
        jenis        = 'jenis'        in params and params['jenis']        or 0
        mulai        = 'mulai'        in params and params['mulai']        or 0
        selesai      = 'selesai'      in params and params['selesai']      or 0
        opreklame_id = 'opreklame_id' in params and params['opreklame_id'] or 0
        transaksi_id = 'transaksi_id' in params and params['transaksi_id'] or 0
        
		# Khusus untuk modul master #
        kec_id     = 'kec_id'     in params and params['kec_id']     or 0
        kel_id     = 'kel_id'     in params and params['kel_id']     or 0
        kls_jln_id = 'kls_jln_id' in params and params['kls_jln_id'] or 0
        jalan_id   = 'jalan_id'   in params and params['jalan_id']   or 0
        pemilik_id = 'pemilik_id' in params and params['pemilik_id'] or 0
        tinggi_id  = 'tinggi_id'  in params and params['tinggi_id']  or 0
        nsr_id     = 'nsr_id'     in params and params['nsr_id']     or 0
		
        if url_dict['act']=='laporan' :
            # Jenis laporan pajak reklame #
            if jenis == '1' :
                query = DBSession.query(OPreklame.kode.label('op_kd'),
                                        OPreklame.nama.label('op_nm'),
                                        Pemilik.nama.label('pem_nm'),
                                        Rekening.nama.label('rek_nm'),
                                        Kelurahan.nama.label('kel_nm'),
                                        Jalan.nama.label('jln_nm'),
                                        Nsr.nilai.label('op_nsr'),
                                        OPreklame.muka.label('op_mk'),
                                        OPreklame.jumlah.label('op_jml'),
                                        OPreklame.luas.label('op_ls'),
                                        case([(OPreklame.disabled==0,"N"),
                                              (OPreklame.disabled==1,"Y")], else_="").label('dis'),
                                ).join(Pemilik, Rekening, Jalan, Kelurahan, Ketinggian
                                ).filter(OPreklame.rekening_id   == rek,
                                         OPreklame.rekening_id   == Rekening.id, 
                                         OPreklame.pemilik_id    == Pemilik.id, 
                                         OPreklame.kelurahan_id  == Kelurahan.id, 
                                         OPreklame.jalan_id      == Jalan.id,
                                         OPreklame.rek_nsr_id    == Nsr.id, 
                                         OPreklame.ketinggian_id == Ketinggian.id, 
                                ).order_by(OPreklame.kode, 	 			 	 										 
                                ).all()
                generator = laporan_objek_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(TransaksiPajak.kode.label('tr_kd'),
                                        TransaksiPajak.nama.label('tr_nm'),
                                        TransaksiPajak.tahun.label('tr_th'),
                                        TransaksiPajak.nopd.label('tr_nopd'),
                                        TransaksiPajak.npwpd.label('tr_npwpd'),
                                        TransaksiPajak.no_skpd.label('tr_skpd'),
                                        TransaksiPajak.no_bayar.label('tr_byr'),
                                        TransaksiPajak.no_sk_ipr.label('tr_ipr'),
                                        TransaksiPajak.periode_awal.label('tr_aw'),
                                        TransaksiPajak.periode_akhir.label('tr_ak'),
                                        TransaksiPajak.jumlah_byr.label('tr_jml'),
                                        OPreklame.nama.label('op_nm'),
                                        case([(TransaksiPajak.disabled==0,"N"),
                                              (TransaksiPajak.disabled==1,"Y")], else_="").label('dis'),
                                ).join(OPreklame
                                ).filter(TransaksiPajak.op_reklame_id == OPreklame.id,
                                         or_(TransaksiPajak.periode_awal.between(mulai,selesai),
                                             TransaksiPajak.periode_akhir.between(mulai,selesai)),
                                ).order_by(TransaksiPajak.kode, 	 					 	 										 
                                ).all()
                generator = laporan_transaksi_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            
        elif url_dict['act']=='opreklame' :
            query = DBSession.query(OPreklame.kode.label('op_kd'),
                                    OPreklame.nama.label('op_nm'),
                                    Pemilik.nama.label('pem_nm'),
                                    Rekening.nama.label('rek_nm'),
                                    Kelurahan.nama.label('kel_nm'),
                                    Jalan.nama.label('jln_nm'),
                                    Nsr.nilai.label('op_nsr'),
                                    OPreklame.muka.label('op_mk'),
                                    OPreklame.jumlah.label('op_jml'),
                                    OPreklame.luas.label('op_ls'),
                                    case([(OPreklame.disabled==0,"N"),
                                          (OPreklame.disabled==1,"Y")], else_="").label('dis'),
                            ).join(Pemilik, Rekening, Jalan, Kelurahan
                            ).filter(OPreklame.id           == opreklame_id,
                                     OPreklame.pemilik_id   == Pemilik.id, 
                                     OPreklame.rekening_id  == Rekening.id, 
                                     OPreklame.kelurahan_id == Kelurahan.id, 
                                     OPreklame.jalan_id     == Jalan.id,   
                                     OPreklame.rek_nsr_id   == Nsr.id,                           
                            ).order_by(OPreklame.kode, 	 			 	 										 
                            ).all()
            generator = opreklame_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='opreklame2' :
            query = DBSession.query(OPreklame.kode.label('op_kd'),
                                    OPreklame.nama.label('op_nm'),
                                    Pemilik.nama.label('pem_nm'),
                                    Rekening.nama.label('rek_nm'),
                                    Kelurahan.nama.label('kel_nm'),
                                    Jalan.nama.label('jln_nm'),
                                    Nsr.nilai.label('op_nsr'),
                                    OPreklame.muka.label('op_mk'),
                                    OPreklame.jumlah.label('op_jml'),
                                    OPreklame.luas.label('op_ls'),
                                    case([(OPreklame.disabled==0,"N"),
                                          (OPreklame.disabled==1,"Y")], else_="").label('dis'),
                            ).join(Pemilik, Rekening, Jalan, Kelurahan
                            ).filter(OPreklame.pemilik_id   == Pemilik.id, 
                                     OPreklame.rekening_id  == Rekening.id, 
                                     OPreklame.kelurahan_id == Kelurahan.id, 
                                     OPreklame.jalan_id     == Jalan.id, 
                                     OPreklame.rek_nsr_id   == Nsr.id,                                  
                            ).order_by(OPreklame.kode, 	 					 	 										 
                            ).all()
            generator = opreklame2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='transaksi' :
            query = DBSession.query(TransaksiPajak.kode.label('tr_kd'),
                                    TransaksiPajak.nama.label('tr_nm'),
                                    TransaksiPajak.tahun.label('tr_th'),
                                    TransaksiPajak.nopd.label('tr_nopd'),
                                    TransaksiPajak.npwpd.label('tr_npwpd'),
                                    TransaksiPajak.no_skpd.label('tr_skpd'),
                                    TransaksiPajak.no_bayar.label('tr_byr'),
                                    TransaksiPajak.no_sk_ipr.label('tr_ipr'),
                                    TransaksiPajak.periode_awal.label('tr_aw'),
                                    TransaksiPajak.periode_akhir.label('tr_ak'),
                                    TransaksiPajak.jumlah_byr.label('tr_jml'),
                                    OPreklame.nama.label('op_nm'),
                                    case([(TransaksiPajak.disabled==0,"N"),
                                          (TransaksiPajak.disabled==1,"Y")], else_="").label('dis'),
                            ).join(OPreklame
                            ).filter(TransaksiPajak.id == transaksi_id,
                                     TransaksiPajak.op_reklame_id == OPreklame.id,                            
                            ).order_by(TransaksiPajak.kode, 	 					 	 										 
                            ).all()
            generator = transaksi_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='transaksi2' :
            query = DBSession.query(TransaksiPajak.kode.label('tr_kd'),
                                    TransaksiPajak.nama.label('tr_nm'),
                                    TransaksiPajak.tahun.label('tr_th'),
                                    TransaksiPajak.nopd.label('tr_nopd'),
                                    TransaksiPajak.npwpd.label('tr_npwpd'),
                                    TransaksiPajak.no_skpd.label('tr_skpd'),
                                    TransaksiPajak.no_bayar.label('tr_byr'),
                                    TransaksiPajak.no_sk_ipr.label('tr_ipr'),
                                    TransaksiPajak.periode_awal.label('tr_aw'),
                                    TransaksiPajak.periode_akhir.label('tr_ak'),
                                    TransaksiPajak.jumlah_byr.label('tr_jml'),
                                    OPreklame.nama.label('op_nm'),
                                    case([(TransaksiPajak.disabled==0,"N"),
                                          (TransaksiPajak.disabled==1,"Y")], else_="").label('dis'),
                            ).join(OPreklame
                            ).filter(TransaksiPajak.op_reklame_id == OPreklame.id,                       
                            ).order_by(TransaksiPajak.kode, 	 					 	 										 
                            ).all()
            generator = transaksi2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        ###############################		
		## Khusus untuk modul master ##
        ###############################	
		
        elif url_dict['act']=='kecamatan' :
            query = DBSession.query(Kecamatan.kode.label('kec_kd'),
                                    Kecamatan.nama.label('kec_nm'),
                                    case([(Kecamatan.disabled==0,"N"),
                                          (Kecamatan.disabled==1,"Y")], else_="").label('dis'),
                            ).filter(Kecamatan.id == kec_id, 	  	 		 										 
                            ).all()
            generator = master_kecamatan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='kecamatan2' :
            query = DBSession.query(Kecamatan.kode.label('kec_kd'),
                                    Kecamatan.nama.label('kec_nm'),
                                    case([(Kecamatan.disabled==0,"N"),
                                          (Kecamatan.disabled==1,"Y")], else_="").label('dis'),	
                            ).order_by(Kecamatan.kode, 				 		 										 
                            ).all()
            generator = master_kecamatan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='kelurahan' :
            query = DBSession.query(Kelurahan.kode.label('kel_kd'),
                                    Kelurahan.nama.label('kel_nm'),
                                    Kecamatan.nama.label('kec_nm'),
                                    case([(Kelurahan.disabled==0,"N"),
                                          (Kelurahan.disabled==1,"Y")], else_="").label('dis'),
                            ).join(Kecamatan
                            ).filter(Kelurahan.id == kel_id, 
                                     Kelurahan.kecamatan_id == Kecamatan.id                            
                            ).all()
            generator = master_kelurahan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='kelurahan2' :
            query = DBSession.query(Kelurahan.kode.label('kel_kd'),
                                    Kelurahan.nama.label('kel_nm'),
                                    Kecamatan.nama.label('kec_nm'),
                                    case([(Kelurahan.disabled==0,"N"),
                                          (Kelurahan.disabled==1,"Y")], else_="").label('dis'),	
                            ).join(Kecamatan
                            ).filter(Kelurahan.kecamatan_id == Kecamatan.id 	
                            ).order_by(Kelurahan.kode, 	 				 										 
                            ).all()
            generator = master_kelurahan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='kelas_jalan' :
            query = DBSession.query(KelasJalan.kode.label('kls_kd'),
                                    KelasJalan.nama.label('kls_nm'),
                                    KelasJalan.nilai.label('kls_ni'),
                                    case([(KelasJalan.disabled==0,"N"),
                                          (KelasJalan.disabled==1,"Y")], else_="").label('dis'),
                            ).filter(KelasJalan.id == kls_jln_id, 						
                            ).all()
            generator = master_kelas_jalan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
			
        elif url_dict['act']=='kelas_jalan2' :
            query = DBSession.query(KelasJalan.kode.label('kls_kd'),
                                    KelasJalan.nama.label('kls_nm'),
                                    KelasJalan.nilai.label('kls_ni'),
                                    case([(KelasJalan.disabled==0,"N"),
                                          (KelasJalan.disabled==1,"Y")], else_="").label('dis'),
                            ).order_by(KelasJalan.kode, 						
                            ).all()
            generator = master_kelas_jalan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='jalan' :
            query = DBSession.query(Jalan.kode.label('jln_kd'),
                                    Jalan.nama.label('jln_nm'),
                                    KelasJalan.nama.label('kls_nm'),
                                    case([(Jalan.disabled==0,"N"),
                                          (Jalan.disabled==1,"Y")], else_="").label('dis'),
                            ).join(KelasJalan
                            ).filter(Jalan.id == jalan_id, 
                                     Jalan.kelas_jalan_id == KelasJalan.id                            
                            ).all()
            generator = master_jalan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='jalan2' :
            query = DBSession.query(Jalan.kode.label('jln_kd'),
                                    Jalan.nama.label('jln_nm'),
                                    KelasJalan.nama.label('kls_nm'),
                                    case([(Jalan.disabled==0,"N"),
                                          (Jalan.disabled==1,"Y")], else_="").label('dis'),
                            ).join(KelasJalan
                            ).filter(Jalan.kelas_jalan_id == KelasJalan.id 	
                            ).order_by(Jalan.kode, 	 				 										 
                            ).all()
            generator = master_jalan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='pemilik' :
            query = DBSession.query(Pemilik.kode.label('p_kd'),
                                    Pemilik.nama.label('p_nm'),
                                    Pemilik.alamat.label('p_almt'),
                                    Pemilik.no_telp.label('p_nt'),
                                    Pemilik.no_fax.label('p_nf'),
                                    Pemilik.no_hp.label('p_nh'),
                                    Pemilik.email.label('p_em'),
                                    Pemilik.kd_pos.label('p_pos'),
                                    case([(Pemilik.disabled==0,"N"),
                                          (Pemilik.disabled==1,"Y")], else_="").label('dis'),
                            ).filter(Pemilik.id == pemilik_id, 						
                            ).all()
            generator = master_pemilik_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
			
        elif url_dict['act']=='pemilik2' :
            query = DBSession.query(Pemilik.kode.label('p_kd'),
                                    Pemilik.nama.label('p_nm'),
                                    Pemilik.alamat.label('p_almt'),
                                    Pemilik.no_telp.label('p_nt'),
                                    Pemilik.no_fax.label('p_nf'),
                                    Pemilik.no_hp.label('p_nh'),
                                    Pemilik.email.label('p_em'),
                                    Pemilik.kd_pos.label('p_pos'),
                                    case([(Pemilik.disabled==0,"N"),
                                          (Pemilik.disabled==1,"Y")], else_="").label('dis'),
                            ).order_by(Pemilik.nama, 						
                            ).all()
            generator = master_pemilik2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
			
        elif url_dict['act']=='ketinggian' :
            query = DBSession.query(Ketinggian.kode.label('ket_kd'),
                                    Ketinggian.nama.label('ket_nm'),
                                    Ketinggian.nilai.label('ket_ni'),
                                    case([(Ketinggian.disabled==0,"N"),
                                          (Ketinggian.disabled==1,"Y")], else_="").label('dis'),
                            ).filter(Ketinggian.id == tinggi_id, 						
                            ).all()
            generator = master_ketinggian_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
			
        elif url_dict['act']=='ketinggian2' :
            query = DBSession.query(Ketinggian.kode.label('ket_kd'),
                                    Ketinggian.nama.label('ket_nm'),
                                    Ketinggian.nilai.label('ket_ni'),
                                    case([(Ketinggian.disabled==0,"N"),
                                          (Ketinggian.disabled==1,"Y")], else_="").label('dis'),
                            ).order_by(Ketinggian.kode, 						
                            ).all()
            generator = master_ketinggian2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response			
		
        elif url_dict['act']=='nsr' :
            query = DBSession.query(Nsr.kode.label('nsr_kd'),
                                    Nsr.nama.label('nsr_nm'),
                                    Nsr.nilai.label('nsr_ni'),
                                    Rekening.nama.label('rek_nm'),
                                    case([(Nsr.disabled==0,"N"),
                                          (Nsr.disabled==1,"Y")], else_="").label('dis'),
                            ).join(Rekening
                            ).filter(Nsr.id == nsr_id, 
                                     Nsr.rekening_id == Rekening.id                            
                            ).all()
            generator = master_nsr_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='nsr2' :
            query = DBSession.query(Nsr.kode.label('nsr_kd'),
                                    Nsr.nama.label('nsr_nm'),
                                    Nsr.nilai.label('nsr_ni'),
                                    Rekening.nama.label('rek_nm'),
                                    case([(Nsr.disabled==0,"N"),
                                          (Nsr.disabled==1,"Y")], else_="").label('dis'),
                            ).join(Rekening
                            ).filter(Nsr.rekening_id == Rekening.id 	
                            ).order_by(Nsr.kode, 	 				 										 
                            ).all()
            generator = master_nsr2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
	
			
######################################################################			
#########################  JASPER GENERATOR  #########################
######################################################################	
		
# Objek Pajak #
class opreklame_Generator(JasperGenerator):
    def __init__(self):
        super(opreklame_Generator, self).__init__()
        self.reportname = get_rpath('Transaksi_objek_pajak.jrxml')
        self.xpath = '/opreklame/objek_pajak'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'objek_pajak')
            ET.SubElement(xml_greeting, "op_kd").text   = row.op_kd
            ET.SubElement(xml_greeting, "op_nm").text   = row.op_nm
            ET.SubElement(xml_greeting, "pem_nm").text  = row.pem_nm
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kel_nm").text  = row.kel_nm
            ET.SubElement(xml_greeting, "jln_nm").text  = row.jln_nm
            ET.SubElement(xml_greeting, "op_nsr").text  = unicode(row.op_nsr)
            ET.SubElement(xml_greeting, "op_mk").text   = unicode(row.op_mk)
            ET.SubElement(xml_greeting, "op_jml").text  = unicode(row.op_jml)
            ET.SubElement(xml_greeting, "op_ls").text   = unicode(row.op_ls)
            ET.SubElement(xml_greeting, "dis").text     = unicode(row.dis)
        return self.root		
        
# Objek Pajak (all) #
class opreklame2_Generator(JasperGenerator):
    def __init__(self):
        super(opreklame2_Generator, self).__init__()
        self.reportname = get_rpath('Transaksi_objek_pajak_all.jrxml')
        self.xpath = '/opreklame/objek_pajak_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'objek_pajak_all')
            ET.SubElement(xml_greeting, "op_kd").text   = row.op_kd
            ET.SubElement(xml_greeting, "op_nm").text   = row.op_nm
            ET.SubElement(xml_greeting, "pem_nm").text  = row.pem_nm
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kel_nm").text  = row.kel_nm
            ET.SubElement(xml_greeting, "jln_nm").text  = row.jln_nm
            ET.SubElement(xml_greeting, "op_nsr").text  = unicode(row.op_nsr)
            ET.SubElement(xml_greeting, "op_mk").text   = unicode(row.op_mk)
            ET.SubElement(xml_greeting, "op_jml").text  = unicode(row.op_jml)
            ET.SubElement(xml_greeting, "op_ls").text   = unicode(row.op_ls)
            ET.SubElement(xml_greeting, "dis").text     = unicode(row.dis)
        return self.root	
        
# Transaksi Pajak #
class transaksi_Generator(JasperGenerator):
    def __init__(self):
        super(transaksi_Generator, self).__init__()
        self.reportname = get_rpath('Transaksi_pajak.jrxml')
        self.xpath = '/opreklame/transaksi'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'transaksi')
            ET.SubElement(xml_greeting, "tr_kd").text     = row.tr_kd
            ET.SubElement(xml_greeting, "tr_nm").text     = row.tr_nm
            ET.SubElement(xml_greeting, "tr_th").text     = unicode(row.tr_th)
            ET.SubElement(xml_greeting, "tr_nopd").text   = row.tr_nopd
            ET.SubElement(xml_greeting, "tr_npwpd").text  = row.tr_npwpd
            ET.SubElement(xml_greeting, "tr_skpd").text   = row.tr_skpd
            ET.SubElement(xml_greeting, "tr_byr").text    = row.tr_byr
            ET.SubElement(xml_greeting, "tr_ipr").text    = row.tr_ipr
            ET.SubElement(xml_greeting, "tr_aw").text     = unicode(row.tr_aw)
            ET.SubElement(xml_greeting, "tr_ak").text     = unicode(row.tr_ak)
            ET.SubElement(xml_greeting, "tr_jml").text    = unicode(row.tr_jml)
            ET.SubElement(xml_greeting, "op_nm").text     = row.op_nm
            ET.SubElement(xml_greeting, "dis").text       = unicode(row.dis)
        return self.root
        
# Transaksi Pajak (all) #
class transaksi2_Generator(JasperGenerator):
    def __init__(self):
        super(transaksi2_Generator, self).__init__()
        self.reportname = get_rpath('Transaksi_pajak_all.jrxml')
        self.xpath = '/opreklame/transaksi_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'transaksi_all')
            ET.SubElement(xml_greeting, "tr_kd").text     = row.tr_kd
            ET.SubElement(xml_greeting, "tr_nm").text     = row.tr_nm
            ET.SubElement(xml_greeting, "tr_th").text     = unicode(row.tr_th)
            ET.SubElement(xml_greeting, "tr_nopd").text   = row.tr_nopd
            ET.SubElement(xml_greeting, "tr_npwpd").text  = row.tr_npwpd
            ET.SubElement(xml_greeting, "tr_skpd").text   = row.tr_skpd
            ET.SubElement(xml_greeting, "tr_byr").text    = row.tr_byr
            ET.SubElement(xml_greeting, "tr_ipr").text    = row.tr_ipr
            ET.SubElement(xml_greeting, "tr_aw").text     = unicode(row.tr_aw)
            ET.SubElement(xml_greeting, "tr_ak").text     = unicode(row.tr_ak)
            ET.SubElement(xml_greeting, "tr_jml").text    = unicode(row.tr_jml)
            ET.SubElement(xml_greeting, "op_nm").text     = row.op_nm
            ET.SubElement(xml_greeting, "dis").text       = unicode(row.dis)
        return self.root	
        
# Laporan Objek Pajak #
class laporan_objek_Generator(JasperGenerator):
    def __init__(self):
        super(laporan_objek_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_objek_pajak.jrxml')
        self.xpath = '/opreklame/objek_pajak_lap'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'objek_pajak_lap')
            ET.SubElement(xml_greeting, "op_kd").text   = row.op_kd
            ET.SubElement(xml_greeting, "op_nm").text   = row.op_nm
            ET.SubElement(xml_greeting, "pem_nm").text  = row.pem_nm
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kel_nm").text  = row.kel_nm
            ET.SubElement(xml_greeting, "jln_nm").text  = row.jln_nm
            ET.SubElement(xml_greeting, "op_nsr").text  = unicode(row.op_nsr)
            ET.SubElement(xml_greeting, "op_mk").text   = unicode(row.op_mk)
            ET.SubElement(xml_greeting, "op_jml").text  = unicode(row.op_jml)
            ET.SubElement(xml_greeting, "op_ls").text   = unicode(row.op_ls)
            ET.SubElement(xml_greeting, "dis").text     = unicode(row.dis)
        return self.root	
        
# Laporan Transaksi Pajak #
class laporan_transaksi_Generator(JasperGenerator):
    def __init__(self):
        super(laporan_transaksi_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_transaksi_pajak.jrxml')
        self.xpath = '/opreklame/transaksi_lap'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'transaksi_lap')
            ET.SubElement(xml_greeting, "tr_kd").text     = row.tr_kd
            ET.SubElement(xml_greeting, "tr_nm").text     = row.tr_nm
            ET.SubElement(xml_greeting, "tr_th").text     = unicode(row.tr_th)
            ET.SubElement(xml_greeting, "tr_nopd").text   = row.tr_nopd
            ET.SubElement(xml_greeting, "tr_npwpd").text  = row.tr_npwpd
            ET.SubElement(xml_greeting, "tr_skpd").text   = row.tr_skpd
            ET.SubElement(xml_greeting, "tr_byr").text    = row.tr_byr
            ET.SubElement(xml_greeting, "tr_ipr").text    = row.tr_ipr
            ET.SubElement(xml_greeting, "tr_aw").text     = unicode(row.tr_aw)
            ET.SubElement(xml_greeting, "tr_ak").text     = unicode(row.tr_ak)
            ET.SubElement(xml_greeting, "tr_jml").text    = unicode(row.tr_jml)
            ET.SubElement(xml_greeting, "op_nm").text     = row.op_nm
            ET.SubElement(xml_greeting, "dis").text       = unicode(row.dis)
        return self.root		
        
###############################		
## Khusus untuk modul master ##
###############################						

# Master Kecamatan #
class master_kecamatan_Generator(JasperGenerator):
    def __init__(self):
        super(master_kecamatan_Generator, self).__init__()
        self.reportname = get_rpath('Master_kecamatan.jrxml')
        self.xpath = '/opreklame/kecamatan'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kecamatan')
            ET.SubElement(xml_greeting, "kec_kd").text     = row.kec_kd
            ET.SubElement(xml_greeting, "kec_nm").text     = row.kec_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Kecamatan All #
class master_kecamatan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_kecamatan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_kecamatan_all.jrxml')
        self.xpath = '/opreklame/kecamatan_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kecamatan_all')
            ET.SubElement(xml_greeting, "kec_kd").text     = row.kec_kd
            ET.SubElement(xml_greeting, "kec_nm").text     = row.kec_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root
        
# Master Kelurahan #
class master_kelurahan_Generator(JasperGenerator):
    def __init__(self):
        super(master_kelurahan_Generator, self).__init__()
        self.reportname = get_rpath('Master_kelurahan.jrxml')
        self.xpath = '/opreklame/kelurahan'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kelurahan')
            ET.SubElement(xml_greeting, "kel_kd").text     = row.kel_kd
            ET.SubElement(xml_greeting, "kel_nm").text     = row.kel_nm
            ET.SubElement(xml_greeting, "kec_nm").text     = row.kec_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Kelurahan All #
class master_kelurahan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_kelurahan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_kelurahan_all.jrxml')
        self.xpath = '/opreklame/kelurahan_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kelurahan_all')
            ET.SubElement(xml_greeting, "kel_kd").text     = row.kel_kd
            ET.SubElement(xml_greeting, "kel_nm").text     = row.kel_nm
            ET.SubElement(xml_greeting, "kec_nm").text     = row.kec_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root
        
# Master Kelas Jalan #
class master_kelas_jalan_Generator(JasperGenerator):
    def __init__(self):
        super(master_kelas_jalan_Generator, self).__init__()
        self.reportname = get_rpath('Master_kelas_jalan.jrxml')
        self.xpath = '/opreklame/kelas_jalan'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kelas_jalan')
            ET.SubElement(xml_greeting, "kls_kd").text     = row.kls_kd
            ET.SubElement(xml_greeting, "kls_nm").text     = row.kls_nm
            ET.SubElement(xml_greeting, "kls_ni").text     = unicode(row.kls_ni)
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Kelas Jalan All #
class master_kelas_jalan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_kelas_jalan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_kelas_jalan_all.jrxml')
        self.xpath = '/opreklame/kelas_jalan_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'kelas_jalan_all')
            ET.SubElement(xml_greeting, "kls_kd").text     = row.kls_kd
            ET.SubElement(xml_greeting, "kls_nm").text     = row.kls_nm
            ET.SubElement(xml_greeting, "kls_ni").text     = unicode(row.kls_ni)
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root
        
# Master Jalan #
class master_jalan_Generator(JasperGenerator):
    def __init__(self):
        super(master_jalan_Generator, self).__init__()
        self.reportname = get_rpath('Master_jalan.jrxml')
        self.xpath = '/opreklame/jalan'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'jalan')
            ET.SubElement(xml_greeting, "jln_kd").text     = row.jln_kd
            ET.SubElement(xml_greeting, "jln_nm").text     = row.jln_nm
            ET.SubElement(xml_greeting, "kls_nm").text     = row.kls_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Jalan All #
class master_jalan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_jalan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_jalan_all.jrxml')
        self.xpath = '/opreklame/jalan_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'jalan_all')
            ET.SubElement(xml_greeting, "jln_kd").text     = row.jln_kd
            ET.SubElement(xml_greeting, "jln_nm").text     = row.jln_nm
            ET.SubElement(xml_greeting, "kls_nm").text     = row.kls_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root
        
# Master Pemilik #
class master_pemilik_Generator(JasperGenerator):
    def __init__(self):
        super(master_pemilik_Generator, self).__init__()
        self.reportname = get_rpath('Master_pemilik.jrxml')
        self.xpath = '/opreklame/pemilik'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pemilik')
            ET.SubElement(xml_greeting, "p_kd").text     = row.p_kd
            ET.SubElement(xml_greeting, "p_nm").text     = row.p_nm
            ET.SubElement(xml_greeting, "p_almt").text   = row.p_almt
            ET.SubElement(xml_greeting, "p_nt").text     = row.p_nt
            ET.SubElement(xml_greeting, "p_nf").text     = row.p_nf
            ET.SubElement(xml_greeting, "p_nh").text     = row.p_nh
            ET.SubElement(xml_greeting, "p_em").text     = row.p_em
            ET.SubElement(xml_greeting, "p_pos").text    = row.p_pos
            ET.SubElement(xml_greeting, "dis").text      = unicode(row.dis)
        return self.root		
		
# Master Pemilik All #
class master_pemilik2_Generator(JasperGenerator):
    def __init__(self):
        super(master_pemilik2_Generator, self).__init__()
        self.reportname = get_rpath('Master_pemilik_all.jrxml')
        self.xpath = '/opreklame/pemilik_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pemilik_all')
            ET.SubElement(xml_greeting, "p_kd").text     = row.p_kd
            ET.SubElement(xml_greeting, "p_nm").text     = row.p_nm
            ET.SubElement(xml_greeting, "p_almt").text   = row.p_almt
            ET.SubElement(xml_greeting, "p_nt").text     = row.p_nt
            ET.SubElement(xml_greeting, "p_nf").text     = row.p_nf
            ET.SubElement(xml_greeting, "p_nh").text     = row.p_nh
            ET.SubElement(xml_greeting, "p_em").text     = row.p_em
            ET.SubElement(xml_greeting, "p_pos").text    = row.p_pos
            ET.SubElement(xml_greeting, "dis").text      = unicode(row.dis)
        return self.root
        
# Master Ketinggian #
class master_ketinggian_Generator(JasperGenerator):
    def __init__(self):
        super(master_ketinggian_Generator, self).__init__()
        self.reportname = get_rpath('Master_ketinggian.jrxml')
        self.xpath = '/opreklame/ketinggian'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'ketinggian')
            ET.SubElement(xml_greeting, "ket_kd").text     = row.ket_kd
            ET.SubElement(xml_greeting, "ket_nm").text     = row.ket_nm
            ET.SubElement(xml_greeting, "ket_ni").text     = unicode(row.ket_ni)
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Ketinggian All #
class master_ketinggian2_Generator(JasperGenerator):
    def __init__(self):
        super(master_ketinggian2_Generator, self).__init__()
        self.reportname = get_rpath('Master_ketinggian_all.jrxml')
        self.xpath = '/opreklame/ketinggian_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'ketinggian_all')
            ET.SubElement(xml_greeting, "ket_kd").text     = row.ket_kd
            ET.SubElement(xml_greeting, "ket_nm").text     = row.ket_nm
            ET.SubElement(xml_greeting, "ket_ni").text     = unicode(row.ket_ni)
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root
        
# Master Nilai Sewa Reklame #
class master_nsr_Generator(JasperGenerator):
    def __init__(self):
        super(master_nsr_Generator, self).__init__()
        self.reportname = get_rpath('Master_nsr.jrxml')
        self.xpath = '/opreklame/nsr'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'nsr')
            ET.SubElement(xml_greeting, "nsr_kd").text     = row.nsr_kd
            ET.SubElement(xml_greeting, "nsr_nm").text     = row.nsr_nm
            ET.SubElement(xml_greeting, "nsr_ni").text     = unicode(row.nsr_ni)
            ET.SubElement(xml_greeting, "rek_nm").text     = row.rek_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root		
		
# Master Nilai Sewa Reklame All #
class master_nsr2_Generator(JasperGenerator):
    def __init__(self):
        super(master_nsr2_Generator, self).__init__()
        self.reportname = get_rpath('Master_nsr_all.jrxml')
        self.xpath = '/opreklame/nsr_all'
        self.root = ET.Element('opreklame') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'nsr_all')
            ET.SubElement(xml_greeting, "nsr_kd").text     = row.nsr_kd
            ET.SubElement(xml_greeting, "nsr_nm").text     = row.nsr_nm
            ET.SubElement(xml_greeting, "nsr_ni").text     = unicode(row.nsr_ni)
            ET.SubElement(xml_greeting, "rek_nm").text     = row.rek_nm
            ET.SubElement(xml_greeting, "dis").text        = unicode(row.dis)
        return self.root