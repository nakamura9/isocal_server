'''
Created on Mar 29, 2016

@author: caleb kandoro

This server provides the forms necessary to create a certificate 
It supplies an interface for viewing and organizing certificates 
? sending preliminary certificates 
It generates a word document based certificate from a template(write a separate 
module for that )

the structure of the server is that there is a folder that stores the
databases and the data modules. There is also a folder that contains the 
templates for both the html files served and the certificate templates generated. 

the server provides an admin interface that controls the users and allows various 
other features

'''

import cherrypy
from jinja2 import Template, Environment
import jinja2
import datetime
import time
import sqlalchemy as sqa 
import os
import data
import certificates, pressure_certificate, balance_certificate
import datasheets
from tabulator import general_tabulation,  horizontal_tabulation
import tabulator as t
from utilities import readings_formatter, get_initials
from _datetime import date
root_dir = os.path.abspath(os.getcwd())
data_is_persistent = True

class CertificateServer():
    "the root application object from which all files are served"
    
    
    def __init__(self):
        '''sets up the template environment from which all templates are served'''
        self.templates = Environment \
        (loader= jinja2.FileSystemLoader(os.path.join(root_dir, "templates")))
    
    
    #
    # User management pages
    #
    @cherrypy.expose
    def index(self, user="", password=""):
        """use session information to redirect to the home screen if the user is already
        logged in"""
        Login = self.templates.get_template("login.html")
        return Login.render(user=user, password=password)
    
    
    
    @cherrypy.expose    
    def authenticate(self, user, password):
        '''this method checks the user input from the login page and returns the
        appropriate page'''
        user_name_list = data.session.query(data.users.user_name).all()
        client = data.session.query(data.users).get(user)
        users = [i[0] for i in user_name_list]
        if user in users:
            if password == client.password:
                cherrypy.session["logged_in"] = True
                cherrypy.session["user"] = user
                cherrypy.session["user_name"] = client.full_name
                print("THis is the session: ", cherrypy.session)
                return self.summary()

            else:
                return self.index(password="the password is incorrect")
        else:
            return self.index(user="the user name is not stored in the database")
    
    
    
    
    @cherrypy.expose
    def signup(self, user="", type=""):
        '''used to provide server side responses to attempts to signup
        and to render the initial sign up form'''
        Signup = self.templates.get_template("signup.html")
        return Signup.render(user=user, type=type)
    
    @cherrypy.expose
    def validate_user(self, name, user, profile, password):
        '''used to check the information entered in the signup form,
        client side validation is also carried out with javascript'''
        clients= data.session.query(data.users.user_name).all()
        
        
        if user in clients:
            return self.signup(user="the username already exists")
        
        
        client = data.users(full_name = name, 
                            user_name = user,
                            profile=profile,
                            password=password)
        data.session.add(client)
        data.session.commit()
        

        return self.summary()


    
        #
        # these are the main application pages accessible from the sidebar on the left
        #
    @cherrypy.expose
    def summary(self):
        '''the default location for a user who logs in to the application'''
        Home = self.templates.get_template("summary.html")
        
        cherrypy.session._data.get("logged_in", False)
        
        outstanding = data.session.query(data.outstanding).all()
        completed = data.session.query(data.completed).all()
        
        if session_check():
            return Home.render(date = datetime.date.today(),
                               outstanding= outstanding,
                               completed= completed)
        else:
            raise cherrypy.HTTPRedirect("index")
    
    
  
 
    
    @cherrypy.expose
    def generate_certificate(self, id, _type):
        form=self.templates.get_template("add.html")
        return form.render(id=id, _type=_type)
        
    @cherrypy.expose
    def create_certificate(self, temp, humidity, id, _type):
        initials = get_initials(cherrypy.session["user"])
        username = cherrypy.session["user_name"]
        if not initials:
            return "sesion variables not correctly initialized"     
        cert = self._create_certificate(temp, humidity, id, _type, initials, username)
        if cert:
            return self.summary()
        else: return "an error occurred"
            
    @cherrypy.expose 
    def _create_certificate(self, temp, humidity, id, _type, initials,
                            username):
        now = datetime.datetime.now()
        certificate_number= "{}{}".format(now.strftime("%Y%m%d%H%M%S"),
                               initials)
        
        _types= {"autoclave":certificates.autoclave_certificate,
                 "volume": certificates.volume_certificate,
                 "current": certificates.current_certificate,
                 "conductivity": certificates.conductivity_certificate,
                 "voltage": certificates.voltage_certificate,
                 "pressure": pressure_certificate.pressure_certificate,
                    "temperature": certificates.temperature_certificate,
                    "ph": certificates.ph_certificate,
                    "flow": certificates.flow_certificate,
                    'length': certificates.length_certificate,
                    "mass": certificates.mass_certificate,
                    "tds": certificates.tds_certificate,
                    "balance": balance_certificate.balance_certificate}
        
        if _type.lower() == "balance":
            balance_data= data.session.query(data.balance).get(id)
            if balance_data:
                customer = balance_data.customer
                name= "balance"
                datasheet_object= datasheets.balance_datasheet(id, initials)
                datasheet_object.generate_datasheet()
            else:
                print("there is no balance with the id: ", id)
                print("these are available: ", [i._id for i in data.session.query(data.balance).all()])
            
        elif _type.lower() == "autoclave":
            autoclave_data=data.session.query(data.autoclave).get(id)
            if autoclave_data:
                customer = autoclave_data.customer
                datasheet_object= datasheets.autoclave_datasheet(id, initials)
                datasheet_object.generate_datasheet()
                name = "autoclave"
            else:
                print("there is no autoclave with the id: ", id)
                #print("these are available: ", data.session.query(data.autoclave).all()._id)
        else:      
            general_data= data.session.query(data.general).get(id)
            if general_data:
                customer = general_data.customer
                name = general_data.name_of_instrument
                datasheet_object= datasheets.general_datasheet(id, initials)
                datasheet_object.generate_datasheet()
            else:
                print("there is no general certificate with the id: ", id)
                #print("these are available: ", data.session.query(data.autoclave).all()._id)
                
        #
        # Moving to completed 
        #
                
        completed =data.completed(_id = id,
                                   name_of_instrument=name,
                                   customer =customer,
                                   serial = certificate_number
                                      )
            
        cert= _types[_type.lower()](id, initials, username,
                                    temp, humidity)
        cert.generate_certificate()
            
        try:
            data.session.add(completed)
            data.session.delete(data.session.query(data.outstanding).get(id))
            data.session.commit()
        except Exception as e:
            data.session.rollback()
            print("this happened during commit: ", e)
            return 0
        
        return 1
            
    
    @cherrypy.expose
    def stop_server(self):
        stop_server()
    
#
# this function makes sure only logged in users can access certain pages
#
def session_check():   
    if "logged_in" in cherrypy.session:
        return cherrypy.session['logged_in']
    else:
        cherrypy.session["logged_in"] = False
        return False
    

class Mobile():
    def __init__(self):
        self.balance_count = 0
        self.autoclave_count = 0
        self.status = "pending"
        self.balance = {}
        self.autoclave={}
        
    @cherrypy.expose
    def index(self):
        return "success"
    
    @cherrypy.expose
    def upload_balance(self, key, value):
        self.balance[key] = value.replace("|", ":")
        print(value)
        self.balance_count += 1
        print(self.balance_count)
        self.status = "pending"
        if self.balance_count == 32:
            self.status = self.add_balance()
        return self.status
    
    def add_balance(self):
        try:
            print(self.balance)
            record = data.balance(_id= self.balance["id"],
                                          customer = self.balance["customer"],
                                          end_time = self.balance["end_time"],
                                          start_time = self.balance["start_time"],
                                          serial = self.balance["sn"],
                                          manufacturer = self.balance["man"],
                                          model = self.balance["model"],
                                          range = self.balance["_range"],
                                          resolution = self.balance["resolution"],
                                          units = self.balance["units"],
                                          location = self.balance["location"],
                                          procedure = self.balance["procedure"],
                                          comments = self.balance["comments"],
                                          standard = self.balance["standard"],
                                          warm_up_nominal = self.balance["warm_up_nominal"],
                                          off_center_mass = self.balance["off_center_mass"],
                                          nominal_mass = self.balance["nominal_mass"],
                                          settling_time = self.balance["settling_time"]
                                          )
                    
            bc= data.balance_before_calibration(_id = self.balance["id"],
                                                    nominal_value=self.balance["before_nominal"], 
                                                    linearity_up=self.balance["before_up"],
                                                    actual=self.balance["before_actual"])
                    
            la= data.balance_linearity_after(_id= self.balance["id"],
                                                 linearity_up= self.balance["after_up"],
                                                 linearity_Down=self.balance["after_down"],
                                                 linearity_uup=self.balance["after_uup"]
                                                 )
                    
            tare= data.balance_tare(_id=self.balance["id"],
                                      tare= self.balance["tare"],
                                      indicated=self.balance["tare_indicated"])
                    
            br= data.balance_repeatability(_id=self.balance["id"],
                                               half_reading=self.balance["repeat_half"],
                                               full_reading=self.balance["repeat_full"])
                    
            try:
                off = self.balance["off_center"].split(":")
                oc= data.balance_off_center(_id=self.balance["id"],
                                            a=off[0],
                                            b=off[1],
                                            c=off[2],
                                            d=off[3],
                                            e=off[4])
            except:
                oc= data.balance_off_center(_id = self.balance["id"],
                                            a="10",
                                            b="10",
                                            c="10",
                                            d="10",
                                            e="10")    
                    
            out = data.outstanding(_id = self.balance["id"],
                                   _type= "Balance",
                                   name_of_instrument= "Balance",
                                   customer = self.balance["customer"],
                                   serial = self.balance["sn"]
                                   )
                
            data.session.add(oc)
            data.session.add(br)
            data.session.add(tare)
            data.session.add(la)
            data.session.add(bc)
            data.session.add(record)
            data.session.add(out)
            data.session.commit()
            
        except Exception as e:
            data.session.rollback()
            print("error: ", e)
            self.balance = {}
            self.balance_count = 0
            
            return "failed"
        else:
            self.balance = {}
            self.balance_count = 0
            return "success"
        
    @cherrypy.expose
    def upload_autoclave(self, key, value):
        self.autoclave_count += 1
        self.autoclave[key] = value
        print(self.autoclave_count)
        self.status = "pending"
        if self.autoclave_count == 21:
            self.status = self.add_autoclave()
        return self.status
    
    def add_autoclave(self):
        try:
            auto = data.autoclave(_id=self.autoclave["id"],
                                  customer=self.autoclave["customer"],
                                  start_time=self.autoclave["start_time"],
                                  end_time=self.autoclave["end_time"],
                                  date=datetime.date.today(),
                                  serial=self.autoclave["serial"],
                                  immersion_depth=self.autoclave["immersion_depth"],
                                  manufacturer=self.autoclave["manufacturer"],
                                  model=self.autoclave["model"],
                                  range_temp=self.autoclave["range_temp"],
                                  range_p=self.autoclave["range_p"],
                                  resolution_temp=self.autoclave["resolution_temp"],
                                  resolution_p=self.autoclave["resolution_p"],
                                  units_temp=self.autoclave["units_temp"],
                                  units_p=self.autoclave["units_p"],
                                  standards=self.autoclave["standards"],
                                  location=self.autoclave["location"],
                                  comments=self.autoclave["comments"],
                                  temp=self.autoclave["temp"],
                                  pressure=self.autoclave["pressure"]
                                  )
            data.session.add(auto)
            out = data.outstanding(_id = self.autoclave["id"],
                                   _type= "autoclave",
                                   name_of_instrument= "Autoclave",
                                   customer = self.autoclave["customer"],
                                   serial = self.autoclave["serial"]
                                   )
            data.session.add(out)
            data.session.commit()
        except Exception as e:
            print("this happened ", e)
            data.session.rollback()
            return "failed"
        else:
            self.autoclave = {}
            self.autoclave_count = 0
            return "success"
    
    
    @cherrypy.expose
    def upload_general(self, user, customer, _type, id, date, due,instrument, sn, man, model,
                 _range, resolution, units, standard, location, start_time, end_time,
                 readings, corrections, immersion, comments):
        try:
            record = data.general(
                                _id = id,
                                customer=customer,
                                start_time= start_time,
                                end_time= end_time,
                                date = date,
                                due = due,
                                name_of_instrument= instrument,
                                serial = sn,
                                manufacturer = man,
                                model = model,
                                range =_range,
                                immersion_depth= immersion,
                                standards = standard,
                                resolution = resolution,
                                units = units.upper(),
                                location = location,
                                readings = readings,
                                corrections= corrections,
                                comments =comments
                                )
            data.session.add(record)
            out = data.outstanding(_id = id,
                                   _type = _type,
                                   name_of_instrument= instrument,
                                   customer = customer,
                                   serial = sn
                                   )
            
            data.session.add(out)
            data.session.commit()
        except Exception as e:
            data.session.rollback()
            return "failure"
        else:
            return "success"
    
    @cherrypy.expose  
    def upload_standard(self, name, number, nominal, traceability,
                        actual, uncertainty, serial):
        try:
            std = data.general_standards(name=name,
                                         _type="standard",
                                         certificate=number,
                                         serial=serial,
                                         traceability=traceability,
                                         nominal_values=nominal,
                                         actual_values=actual,
                                         uncertainty=uncertainty)
            data.session.add(std)
            data.session.commit()
        except Exception as e:
            data.session.rollback()
            return "failure"
        else:
            return "success"
            
    
            

def start_server():
    s = CertificateServer()
    s.mobile = Mobile()
    conf = {"global": {
                    "server.socket_port": 8080,
                    "server.socket_host": "0.0.0.0"
                },
            "/": {
              "tools.sessions.on" : True,
              "tools.staticdir.root": os.path.abspath(os.getcwd()),
              "tools.staticdir.on": True,
              "tools.staticdir.dir": "./Templates",
              "server.thread_pool": 10# will change one sqlalchemy is implemented
              }
        }
    cherrypy.quickstart(s,"/", conf)
    
def stop_server():
    cherrypy.engine.exit()
    
if __name__ == "__main__":
    start_server()
    
    
    
    