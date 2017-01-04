'''
Created on Apr 1, 2016

@author: caleb kandoro
'''

import data
from tabulator import general_tabulation, horizontal_tabulation,create_row, simple_table
import datetime 
import time
import jinja2
import os
import math
from statistics import stdev, mean
from builtins import round

DIR = os.path.abspath(os.getcwd())

templates = jinja2.Environment(loader= jinja2.FileSystemLoader \
                               (os.path.join(DIR, "certificates\\templates")))


"""this module contains the base class for all certificates modelled around the template
design pattern. It also includes the classes for the  """
    
class certificate():
    
    def __init__(self, _id, initials, by, temp, humidity):
        
        
        '''THE BASE object from which common certificate features are abstracted
        the __init__ function obtains the row from the table where the data is 
        recorded
        the class refers to the table from which all database queries will be 
        made. NB the databases use the serial number as a primary key'''

        self.id = _id
        self.today = datetime.date.today()
        self.initials = initials
        self.certificate_number(self.initials)
        self.template = None
        self.calibrator = by
        self.temp = temp
        self.humidity =humidity
        
        
    def certificate_number(self, initials):
        now = datetime.datetime.now()
        self.certificate_number= "{}{}".format(now.strftime("%Y%m%d%H%M%S"),
                               self.initials)
        
    def corrections_table(self):
        if self.data.corrections:
            data = {"Indicated":[], "Input":[]}
            rows =self.data.corrections.split(";")
            for i in rows:
                input, indicated  = i.split(":")
                data["Indicated"].append(indicated)
                data["Input"].append(input)
            self.corrections_table= "<p>Corrections:</p>" + simple_table(data,["Input", "Indicated"], False)        
        else:
            self.corrections_table=""
            
    def get_data(self, table, key):
        self.data = data.session.query(table).get(key)
        def get_standard_data(self):
            try:
                #get standards data
                d = data.session.query(data.general_standards).get(self.data.standards)
                self.standard = create_row([d.name, 
                                    d.serial,
                                    d.certificate])
                self.traceability = d.traceability
            except:
                try:
                    self.standard = create_row([self.data.standards, " ", " "])# to fill the other empty spaces
                except:
                    self.standard=""
                self.traceability= ""
        get_standard_data(self)
            
    def extract_readings(self):
        '''each table has a readings string may be able to generalize 
        it with time, but for now stick with individual implementations
        each implementation interface must take a set of input readings 
        extracted and place them in the self.input list whether 
        or not the input is going to be modified'''
        table = self.data.readings
        rows = table.split(";")
        self.indicated = []
        self.input = []
        for row in rows:
            cells = row.split(":")
            self.indicated.append(float(cells[1]))
            self.input.append(float(cells[0]))
                
    def calculate(self):
        '''all the calculations are performed in this method
        if they are many they can be implemented in their own methods 
        and called from here
        the calculations use self.calculator_input list based on readings
        and iterate calculations on that list, placing the results in 
        self.calculator_output'''
        self.output = self.input

    def uncertainty(self):
        '''all uncertainty calculations are performed in this method
        will calculate the uncertainty based on the recorded data
        it is the sum of the square of the resolution and the sum of the 
        squares of the individual measurement errors'''
        self.corrections = []
        for i in range(len(self.indicated)):
            difference = abs(self.output[i] - self.indicated[i])
            self.corrections.append(round(difference, 2))
            
        self._uncertainty = "{:0.4f}".format(math.sqrt(math.pow(float(self.data.resolution), 2) +
                                     sum([math.pow(i, 2) for i in self.corrections])))
                                    
            
    def generate_table(self):
        data = {"Input": self.input,
                "Indicated": self.indicated,
                "Correction": self.corrections}
        
        self.table = simple_table(data, ["Input", "Indicated", "Correction"], False)
        if self.data.corrections == "":
            self.corrections_table = ""
        else:
            corrections_data = self.data.corrections.split(";")
            indicated = [i.split(":")[0] for i in corrections_data]
            input = [i.split(":")[1] for i in corrections_data]
            data = {"Input": input,
                    "Indicated": indicated}
            
            content= ["<br />\n<p>Corrections:</p>"]
            content.append(simple_table(data, ["Input", "Indicated"], False))
            self.corrections_table= "\n".join(content)                        
            
    def process(self):
        '''override if not using general'''
        self.get_data(data.general, self.id)
        self.extract_readings()
        self.calculate()
        self.uncertainty()
        self.generate_table()
    
    def generate_certificate(self):
        certificate= templates.get_template(self.template)
        self.process()
        outFile = open("{}\\certificates\\completed\\{}.html".format(DIR,
                                                     self.certificate_number),
                        "w")
        
        
        outFile.write(certificate.render(certificate_number=self.certificate_number,
                                         date=self.data.date,
                                         by= self.calibrator,
                                         due= self.data.due,
                                         customer=self.data.customer.upper(),
                                         type=self.data.name_of_instrument.upper(),
                                         manufacturer=self.data.manufacturer.upper(),
                                         serial=self.data.serial,
                                         range=self.data.range,
                                         units= self.data.units.upper(),
                                         resolution=self.data.resolution,
                                         location=self.data.location,
                                         temperature=self.temp,
                                         humidity=self.humidity,
                                         fields = self.table,
                                         standard = self.standard,
                                         corrections= self.corrections_table,
                                         uncertainty= self._uncertainty,
                                         traceability=self.traceability,
                                         comments=self.data.comments
                                         ))
        outFile.close()

class autoclave_certificate(certificate):    
        
    def extract_temp(self):
        temp_table = self.data.temp
        rows = temp_table.split(";")
        self.temp_actual = []
        self.temp_indicated = []
        for row in rows:
            cells = row.split(":")
            self.temp_actual.append(cells[0])
            self.temp_indicated.append(cells[1])
    
    def extract_pressure(self):
        pressure_table = self.data.pressure
        rows = pressure_table.split(";")
        self.p_applied = []
        self.p_calculated = []
        self.p_indicated = []
        
        for row in rows:
            cells = row.split(":")
            self.p_applied.append(cells[0])
            self.p_calculated.append(cells[1])
            self.p_indicated.append(cells[2])
            
    def extract_readings(self):
        self.extract_pressure()
        self.extract_temp()
                
    def pressure_uncertainty(self):
        self.corrections = []
        for i in range(len(self.p_indicated)):
            self.corrections.append(abs(float(
                            self.p_indicated[i])- float(
                                        self.p_calculated[i])))
            
        squared = [math.pow(i, 2) for i in self.corrections]
        squared.append(math.pow(float(self.data.resolution_p), 2))
        self.uncertainty_p = "{:0.4f}".format(math.sqrt(sum(squared)))    
    
    
    def temp_uncertainty(self):
        self.temp_corrections = []
        for i in range(len(self.temp_indicated)):
            self.temp_corrections.append(abs(float(
                    self.temp_actual[i])-float(
                            self.temp_indicated[i]))) 
        squared = [math.pow(i, 2) for i in self.temp_corrections]
        squared.append(math.pow(float(self.data.resolution_temp), 2))
        self.uncertainty_temp="{:0.4f}".format(math.sqrt(sum(squared)))
        
    def uncertainty(self):
        self.pressure_uncertainty()
        self.temp_uncertainty()    
    
    def pressure_table(self):
        rows = []
        for i in range(len(self.p_applied)):
            rows.append(create_row([self.p_applied[i], self.p_calculated[i], 
                                    self.p_indicated[i], self.corrections[i]]))
        self.p_table = "".join(rows)
        
    def temp_table(self):
        rows = []
        for i in range(len(self.temp_indicated)):
            rows.append(create_row([self.temp_actual[i], self.temp_indicated[i], 
                                    self.temp_corrections[i]]))
    
        self.t_table = "".join(rows)

    def generate_table(self):
        self.temp_table()
        self.pressure_table()
        
    def process(self):
        self.get_data(data.autoclave, self.id)
        self.extract_readings()
        #NO CALCULATE
        self.uncertainty()
        self.generate_table()
        
    def generate_certificate(self):
        certificate= templates.get_template("autoclave.html")
        self.process()
        outFile = open("{}\\certificates\\completed\\{}.html".format(DIR,
                                                     self.certificate_number),
                        "w")
        self.data.date = datetime.date(2016, 2, 22)
        due = self.data.date + datetime.timedelta(weeks=26)
        outFile.write(certificate.render(certificate_number=self.certificate_number,
                                         date=self.data.date.strftime("%d/%m/%Y"),
                                         by= self.calibrator,
                                         due= due.strftime("%d/%m/%Y"),
                                         customer=self.data.customer.upper(),
                                         type="AUTOCLAVE",
                                         manufacturer=self.data.manufacturer.upper(),
                                         serial=self.data.serial,
                                         range="{}({})".format(self.data.range_p,self.data.range_temp),
                                         units= "{}({})".format(self.data.units_p, self.data.units_temp),
                                         resolution="{}({})".format(self.data.resolution_p,
                                                                    self.data.resolution_temp),
                                         location=self.data.location,
                                         temperature=self.temp,
                                         humidity=self.humidity,
                                         fields = self.p_table,
                                         fields_temperature= self.t_table,
                                         uncertainty= self.uncertainty_p,
                                         uncertainty_temperature = self.uncertainty_temp  
                                         ))
        outFile.close()

        
        
class volume_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'volume.html'

class conductivity_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = "conductivity.html"
        
class current_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'current.html'
    
    def generate_table(self):
        rows = []
        for i in range(len(self.input)):
            rows.append(create_row([self.input[i], 
                                    self.indicated[i],
                                    float(self.corrections[i]),
                                    (math.sqrt(math.pow(float(self.corrections[i]), 2) *
                                        math.pow(float(self.data.resolution), 2)))]))
            
        self.table = "".join(rows)
        self.corrections_table()
        
class voltage_certificate(current_certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'voltage.html'
        
class ph_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'ph.html'
        
    def generate_table(self):
        rows = []
        for i in range(len(self.input)):
            rows.append(create_row([self.input[i], 
                                    self.indicated[i],
                                    float(self.corrections[i])]))
            
        self.table = "".join(rows)
        self.corrections_table()
        
class tds_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'tds.html'
        
class flow_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'flow.html'

class length_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'length.html'
        
class temperature_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'temperature.html'
        
class mass_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = 'mass_pieces.html'
        
    def calculate(self):
        self.st = data.session.query(data.general_standards).get(self.data.standards)
        
        self.std_reading = []
        self.uut_reading = []
        self.uut_actual = []
        for i in self.data.readings.split(";"):
            row = i.split(":")
            self.std_reading.append(float(row[0]))
            self.uut_reading.append(float(row[1]))
            self.uut_actual.append(float(self.st.actual_values)- float(row[0]) + float(row[1]))
            
        self.uut_actual_mass = mean(self.uut_actual)
        self.dev = stdev(self.uut_actual)
    
    def uncertainty(self):
        r_factor=float(self.data.resolution)/ 2 
        res_factor = r_factor / math.sqrt(3)
        std_factor = 0.003 / 2
        normal_uncertainty = math.sqrt(
                        math.pow(res_factor, 2) + math.pow(
                                std_factor, 2) + math.pow(self.dev, 2))
         
        self._uncertainty = round((normal_uncertainty * 2), 6)
        
    def generate_table(self):
        standard_details = "<table>" + create_row("Actual Mass of standard",
                        self.st.actual_values,
                        "Uncertainty of standard",
                        self.st.uncertainty) + "</table>"
                    
        data = {"Reading #":range(len(self.std_reading)),
                "Standard Reading": self.std_reading,
                "UUT Reading": self.uut_reading[i],
                "Actual Mass": self.uut_actual[i]}
        readings=simple_table(data, ["Reading #", "Standard Reading", "UUT Reading",
                            "Actual Mass"], False)
        summary=simple_table({"Actual Mass of UUT": self.uut_actual_mass,
                      "Standard Deviation of readings": self.dev,
                      "Uncertainty of Readings": self._uncertainty},
                     ["Actual Mass of UUT", "Standard Deviation of readings",
                      "Uncertainty of readings"], True)
        self._table = "\n".join([standard_details, readings, summary])      
        self.corrections_table = ""

if __name__=="__main__":
   a=ph_certificate("_8", "CK", "Caleb Kandoro", "28", "35")
   a.generate_certificate()