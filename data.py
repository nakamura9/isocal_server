'''
Created on Mar 29, 2016
yes
@author: caleb kandoro


'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
import sqlite3
import datetime
import time
from sqlalchemy import Date, Time, DateTime
import random
from sqlalchemy.pool import NullPool
from sqlalchemy.orm.scoping import scoped_session


BASE= declarative_base()

class users(BASE):
    __tablename__ = "users"
    inx = sqa.Column(sqa.Integer())
    full_name = sqa.Column(sqa.String(128))# handle length wxceptions
    user_name = sqa.Column(sqa.String(64), primary_key=True)#implement a foreign key here
    profile= sqa.Column(sqa.String(32))
    password = sqa.Column(sqa.String(64))#encrypt one day
          

class customers(BASE):
    __tablename__="customers"
    name= sqa.Column(sqa.String(128), primary_key=True)
    address= sqa.Column(sqa.String(128))
    email = sqa.Column(sqa.String(128))
    phone=sqa.Column(sqa.Integer())

#
#The list of calibrations 
#	
class autoclave(BASE):
    __tablename__ = "autoclave"
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    customer = sqa.Column(sqa.String(32))
    start_time = sqa.Column(sqa.String(32))
    end_time = sqa.Column(sqa.String(32))
    date = sqa.Column(sqa.String(32))
    due = sqa.Column(sqa.String(32))
    serial = sqa.Column(sqa.String(24))
    immersion_depth = sqa.Column(sqa.String(24))
    manufacturer = sqa.Column(sqa.String(64))
    model = sqa.Column(sqa.String(64))
    range_temp = sqa.Column(sqa.String(12))
    range_p = sqa.Column(sqa.String(12))
    resolution_temp =sqa.Column(sqa.String(12))
    resolution_p = sqa.Column(sqa.String(12))
    units_temp = sqa.Column(sqa.String(12))
    units_p = sqa.Column(sqa.String(12))
    standards= sqa.Column(sqa.String(64))
    location = sqa.Column(sqa.String(32))
    comments = sqa.Column(sqa.String(256))
    temp = sqa.Column(sqa.String(256))
    pressure= sqa.Column(sqa.String(256))
 
class general(BASE):
    __tablename__ = "general"
    
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    customer = sqa.Column(sqa.String(32))
    _type = sqa.Column(sqa.String(32))
    start_time = sqa.Column(sqa.String(32))
    end_time = sqa.Column(sqa.String(32))
    date = sqa.Column(sqa.String(32))
    due = sqa.Column(sqa.String(32))
    name_of_instrument = sqa.Column(sqa.String(32))
    serial = sqa.Column(sqa.String(24))
    immersion_depth = sqa.Column(sqa.String(24))
    manufacturer = sqa.Column(sqa.String(64))
    model = sqa.Column(sqa.String(64))
    range = sqa.Column(sqa.String(12))
    resolution = sqa.Column(sqa.String(12))
    units = sqa.Column(sqa.String(12))
    standards= sqa.Column(sqa.String(64))
    location = sqa.Column(sqa.String(32))
    comments = sqa.Column(sqa.String(256))
    readings = sqa.Column(sqa.String(256))
    corrections= sqa.Column(sqa.String(256))
    

class balance(BASE):
    __tablename__= "balance"
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    customer = sqa.Column(sqa.String(128))
    start_time = sqa.Column(sqa.String(32))
    end_time = sqa.Column(sqa.String(32))
    date = sqa.Column(sqa.String(32))
    due = sqa.Column(sqa.String(32))
    serial = sqa.Column(sqa.String(64))
    manufacturer = sqa.Column(sqa.String(64))
    model = sqa.Column(sqa.String(64))
    range = sqa.Column(sqa.String(64))
    resolution = sqa.Column(sqa.String(64))
    units = sqa.Column(sqa.String(64))
    location = sqa.Column(sqa.String(64))
    procedure = sqa.Column(sqa.String(32))
    standard = sqa.Column(sqa.String(32))
    comments = sqa.Column(sqa.String(256))
    warm_up_nominal= sqa.Column(sqa.String(64)) # single value
    nominal_mass = sqa.Column(sqa.String(172)) # list
    settling_time = sqa.Column(sqa.String(128)) #list
    off_center_mass = sqa.Column(sqa.String(64)) # single value

class balance_before_calibration(BASE):
    __tablename__="before_calibration"
    _id = sqa.Column(sqa.String(32),primary_key = True )
    nominal_value = sqa.Column(sqa.String(128))
    linearity_up = sqa.Column(sqa.String(128))
    actual = sqa.Column(sqa.String(128))
    
class balance_linearity_after(BASE):
    __tablename__="linearity_after"
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    linearity_up = sqa.Column(sqa.String(128))
    linearity_Down= sqa.Column(sqa.String(128))
    linearity_uup= sqa.Column(sqa.String(128))
    
    
class balance_tare(BASE):
    __tablename__="tare"
    _id = sqa.Column(sqa.String(32), primary_key = True)
    tare= sqa.Column(sqa.String(128))
    indicated= sqa.Column(sqa.String(128))
    
    
class balance_repeatability(BASE):
    __tablename__="repeatability"
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    half_reading= sqa.Column(sqa.String(128))
    full_reading= sqa.Column(sqa.String(128))
    
class balance_off_center(BASE):
    __tablename__="off_center"
    _id = sqa.Column(sqa.String(32), primary_key = True)
    a= sqa.Column(sqa.String(18))
    b= sqa.Column(sqa.String(18))
    c= sqa.Column(sqa.String(18))
    d= sqa.Column(sqa.String(18))
    e= sqa.Column(sqa.String(18))
    
    
class completed(BASE):
    __tablename__ ="completed"
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    name_of_instrument = sqa.Column(sqa.String(32))
    customer = sqa.Column(sqa.String(128))
    serial = sqa.Column(sqa.String(64))
    date = sqa.Column(Date(), default = datetime.date.today())
    
    
class outstanding(BASE):
    __tablename__ = "outstanding"
    _type= sqa.Column(sqa.String(24))
    _id = sqa.Column(sqa.String(32),  primary_key = True)
    name_of_instrument = sqa.Column(sqa.String(32))
    customer = sqa.Column(sqa.String(128))
    serial = sqa.Column(sqa.String(64))
    date = sqa.Column(Date(), default = datetime.date.today())


class general_standards(BASE):
    __tablename__ ="general_standards"
    name = sqa.Column(sqa.String(32), primary_key=True)
    _type = sqa.Column(sqa.String(32))
    certificate = sqa.Column(sqa.String(256))
    serial=sqa.Column(sqa.String(32))
    traceability = sqa.Column(sqa.String(256))
    nominal_values = sqa.Column(sqa.String(256))
    actual_values = sqa.Column(sqa.String(256))
    uncertainty = sqa.Column(sqa.String(256))


#    
#the tables that provide the list of measured data
#


engine = sqa.create_engine("sqlite:///isocal.db", poolclass = NullPool)#dont forget to change!    
BASE.metadata.create_all(engine)
SESSION = sqa.orm.sessionmaker(bind=engine)
session = scoped_session(SESSION)

if __name__ == "__main__":
    pass