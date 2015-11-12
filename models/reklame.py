import os
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    Date,
    SmallInteger,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    func,
    extract,
    case
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )
from sqlalchemy.sql.functions import concat
from ..models import (
    Base,
    DefaultModel,
    DBSession,
    osBaseModel,
    osExtendModel,
    User
    )
from ..models.pemda import (
    Unit, Urusan, UserUnit
    )
from ..tools import (
    create_now, get_settings,
    )

## Kecamatan ##
class Kecamatan(Base, osExtendModel):
    __tablename__  = 'kecamatans'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
## Kelurahan ##
class Kelurahan(Base, osExtendModel):
    __tablename__  = 'kelurahans'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',}
    
    kecamatan_id   = Column(Integer, ForeignKey("reklame.kecamatans.id"), nullable=False)   
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
    kecamatans     = relationship("Kecamatan", backref=backref('kelurahans'))
   
## Kelas Jalan ##
class KelasJalan(Base, osExtendModel):
    __tablename__  = 'kelas_jalans'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 
    nilai          = Column(Float)
    disabled       = Column(SmallInteger, nullable=False, default=0)
       
## Jalan ##
class Jalan(Base, osExtendModel):
    __tablename__  = 'jalans'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',}
    
    kelas_jalan_id = Column(Integer, ForeignKey("reklame.kelas_jalans.id"), nullable=False) 
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
    kelas_jalans   = relationship("KelasJalan", backref=backref('jalans'))
    
## Pemilik ##
class Pemilik(Base, osExtendModel):
    __tablename__  = 'pemiliks'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',}   
    
    alamat     = Column(String(255))
    no_telp    = Column(String(20))
    no_fax     = Column(String(20))
    no_hp      = Column(String(20))
    email      = Column(String(100))
    kd_pos     = Column(String(5))
    disabled   = Column(SmallInteger, nullable=False, default=0)

## Rekening ##
class Rekening(Base, osExtendModel):
    __tablename__  = 'rekenings'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 
	
    id         = Column(Integer, primary_key=True)
    header_id  = Column(Integer, ForeignKey("reklame.rekenings.id"), nullable=True)	
    level_id   = Column(SmallInteger, default=1)
    is_summary = Column(SmallInteger, default=1)
    defsign    = Column(SmallInteger, default=1)
    disabled   = Column(SmallInteger, nullable=False, default=0)
	
    header     = relationship("Rekening", backref=backref('rekenings'), remote_side=[id])
	
    @classmethod
    def get_next_level(cls,id):
        return cls.query_id(id).first().level_id+1
     
## Ketinggian ##
class Ketinggian(Base, osExtendModel):
    __tablename__  = 'ketinggians'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 
    nilai          = Column(Float)
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
## NSR ##
class Nsr(Base, osExtendModel):
    __tablename__  = 'rek_nsr'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',}
    
    rekening_id    = Column(Integer, ForeignKey("reklame.rekenings.id"), nullable=False) 
    nilai          = Column(Float)
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
    rekenings      = relationship("Rekening", backref=backref('rek_nsr'))
    
## Objek Pajak Reklame ##
class OPreklame(Base, osExtendModel):
    __tablename__  = 'op_reklames'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 

    #kode          = Column(String(32)) || kecamatan + kelurahan + jalan + no_urut (007.001.001-0001)
    pemilik_id     = Column(Integer, ForeignKey("reklame.pemiliks.id"),   nullable=False) 
    rekening_id    = Column(Integer, ForeignKey("reklame.rekenings.id"),  nullable=False)
    rek_nsr_id     = Column(Integer, ForeignKey("reklame.rek_nsr.id"),    nullable=False)
    provinsi       = Column(String(64))
    kabupaten      = Column(String(64))
    kecamatan      = Column(String(64)) 
    kelurahan_id   = Column(Integer, ForeignKey("reklame.kelurahans.id"), nullable=False) 
    jalan_id       = Column(Integer, ForeignKey("reklame.jalans.id"),     nullable=False)	
    alamat         = Column(String(255)) 
    no_urut        = Column(Integer, nullable=True)
    panjang        = Column(Float)
    lebar          = Column(Float)
    luas           = Column(Float)
    muka           = Column(Integer)
    sudut_pandang  = Column(String(64)) 
    jumlah         = Column(Integer) 
    ketinggian_id  = Column(Integer, ForeignKey("reklame.ketinggians.id"), nullable=False)
    koordinat_x    = Column(Float) 
    koordinat_y    = Column(Float)
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
    pemiliks       = relationship("Pemilik",    backref=backref('op_reklames'))
    rekenings      = relationship("Rekening",   backref=backref('op_reklames'))
    rek_nsr        = relationship("Nsr",        backref=backref('op_reklames'))
    kelurahans     = relationship("Kelurahan",  backref=backref('op_reklames'))
    jalans         = relationship("Jalan",      backref=backref('op_reklames'))
    ketinggians    = relationship("Ketinggian", backref=backref('op_reklames'))
   
    @classmethod
    def max_no_urut(cls, kel_id, jln_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.kelurahan_id == kel_id,
                        cls.jalan_id     == jln_id
                ).scalar() or 0
 	
## Transaksi Pajak Reklame ##
class TransaksiPajak(Base, osExtendModel):
    __tablename__  = 'transaksi_pajaks'
    __table_args__ = {'extend_existing':True, 'schema' : 'reklame',} 

    op_reklame_id  = Column(Integer, ForeignKey("reklame.op_reklames.id"), nullable=False) 
    tahun          = Column(Integer, nullable=False, default=0)
    nopd           = Column(String(32))
    npwpd          = Column(String(32))
    periode_awal   = Column(Date)
    periode_akhir  = Column(Date)
    no_skpd        = Column(String(32))
    tgl_skpd       = Column(Date)
    no_bayar       = Column(String(32))
    tgl_bayar      = Column(Date)
    no_permohonan  = Column(String(255)) 
    id_permohonan  = Column(Integer, default=0)
    tgl_permohonan = Column(Date)
    no_sk_ipr      = Column(String(64))
    tgl_sk_ipr     = Column(Date)
    nilai_pjk      = Column(BigInteger)
    denda_pjk      = Column(BigInteger)
    jumlah_byr     = Column(BigInteger)
    wp_nama        = Column(String(64))
    wp_alamat      = Column(String(255)) 
    jumlah_op      = Column(BigInteger) 
    naskah         = Column(String(255)) 
    disabled       = Column(SmallInteger, nullable=False, default=0)
    
    op_reklames    = relationship("OPreklame",   backref=backref('transaksi_pajaks'))