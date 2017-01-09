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
        self.errors = []
        
        
    def certificate_number(self, initials):
        now = datetime.datetime.now()
        self.certificate_number= "{}{}".format(now.strftime("%Y%m%d%H%M%S"),
                               self.initials)

            
    def get_data(self, table, key):
        self.data = data.session.query(table).get(key)
        if not self.data:
            self.errors.append("The provided id for the calibration does not"
                                    "correspond with a valid database entry")
            raise KeyError("The databse query did not return a row")
        def get_standard_data(self):
            try:
                d = data.session.query(data.general_standards).get(self.data.standards)
            except:
                self.errors.append("The named standard could not be found in the database")
                raise KeyError("standard not found")
            else:
                self.standard = create_row([d.name, 
                                    d.serial,
                                    d.certificate])
                self.traceability = d.traceability
        
        get_standard_data(self)
            
    def extract_readings(self):
        '''each table has a readings string may be able to generalize 
        it with time, but for now stick with individual implementations
        each implementation interface must take a set of input readings 
        extracted and place them in the self.input list whether 
        or not the input is going to be modified'''
        table = self.data.readings
        self.indicated = []
        self.input = []
        rows = table.split(";")
        if table == "":
            self.errors.append("The submitted data does not contain any readings")
            raise ValueError("No readings in the record")
        elif ":" in table:
            for row in rows:
                cells = row.split(":")
                if len(cells) == 2:
                    self.indicated.append(float(cells[1]))
                    self.input.append(float(cells[0]))
                else:
                    self.errors.append("The readings are unbalanced please manually check the data using"
                                        "sqlstudio")
                    raise ValueError("incomplete data")
            
        else:
            self.errors.append("The data supplied as readings cannot be "
                                    "interpreated by the certificates engine"
                                    "please rectify the errors manually using SQLStudio")
            raise ValueError("malformed data")


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
        if len(self.indicated) == len(self.output):
            for i in range(len(self.indicated)):
                difference = abs(self.output[i] - self.indicated[i])
                self.corrections.append(round(difference, 
                        find_round_value(self.data.resolution)))
        else:
            self.errors.append("The data provided as readings is unbalanced"
                                "check the readings column to ensure the variables"
                                "are of the same length")
            raise ValueError("malformed data")

        self._uncertainty = round(math.sqrt(math.pow(float(self.data.resolution), 2) +
                                     sum([math.pow(i, 2) for i in self.corrections])),
                                    find_round_value(self.data.resolution))


    def generate_table(self):
        data = {"Input": self.input,
                "Indicated": self.indicated,
                "Correction": self.corrections}

        self.table = simple_table(data, ["Input", "Indicated", "Correction"], False)
        

    def process(self):
        '''override if not using general'''
        self.get_data(data.general, self.id)
        if self.data.resolution == "":
            self.errors.append("many calculations depend on resolution. Please add one manually"
                                "through SQLSTUDIO")
            raise ValueError("no resolution defined")

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
                                         due=self.data.due,
                                         by= self.calibrator,
                                         customer=self.data.customer,
                                         type=self.data.name_of_instrument,
                                         manufacturer=self.data.manufacturer,
                                         serial=self.data.serial,
                                         range=self.data.range,
                                         units= self.data.units,
                                         resolution=self.data.resolution,
                                         location=self.data.location,
                                         immersion=self.data.immersion_depth,
                                         temperature=self.temp,
                                         humidity=self.humidity,
                                         fields = self.table,
                                         standard = self.standard,
                                         uncertainty= self._uncertainty,
                                         traceability=self.traceability,
                                         comments=self.data.comments
                                         ))
        outFile.close()

class autoclave_certificate(certificate):
    def get_data(self, table, key):
        self.data = data.session.query(table).get(key)
        if not self.data:
            self.errors.append("The provided id for the calibration does not"
                                    "correspond with a valid database entry")
            raise KeyError("The databse query did not return a row")
        def get_standard_data(self):
            try:
                temp = data.session.query(data.general_standards).get(self.data.standard_temp)
                p = data.session.query(data.general_standards).get(self.data.standard_p)
            except:
                self.errors.append("The named standard could not be found in the database")
                raise KeyError("standard not found")
            else:
                self.standard = create_row([temp.name, temp.serial,
                                            temp.certificate]) + "\n" + \
                                    create_row([p.name, p.serial,
                                                p.certificate])
                self.traceability = temp.traceability + "\n" + p.traceability
        
        get_standard_data(self)
        
    def extract_temp(self):
        temp_table = self.data.temp
        rows = temp_table.split(";")
        self.temp_actual = []
        self.temp_indicated = []
        
        if temp_table == "":
            self.errors.append("The submitted data does not contain any readings")
            raise ValueError("No readings in the record")
        elif ":"in temp_table:
            for row in rows:
                cells = row.split(":")
                if len(cells) == 2:
                    self.temp_indicated.append(float(cells[1]))
                    self.temp_actual.append(float(cells[0]))
                else:
                    self.errors.append("The readings are unbalanced please manually check the data using"
                                        "sqlstudio")
                    raise ValueError("incomplete data")
        else:
            self.errors.append("The data supplied as readings cannot be "
                                    "interpreated by the certificates engine"
                                    "please rectify the errors manually using SQLStudio")
            raise ValueError("malformed data")
            
        
        
    
    def extract_pressure(self):
        pressure_table = self.data.pressure
        rows = pressure_table.split(";")
        self.p_applied = []
        self.p_calculated = []
        self.p_indicated = []
        if pressure_table == "":
            self.errors.append("The submitted data does not contain any readings")
            raise ValueError("No readings in the record")
        elif ":" in pressure_table: 
            for row in rows:
                cells = row.split(":")
                if len(cells) == 3:
                    self.p_applied.append(cells[0])
                    self.p_calculated.append(cells[1])
                    self.p_indicated.append(cells[2])
                else:
                    self.errors.append("The readings are unbalanced. Check manually using"
                                        "sqlStudio")
                    raise ValueError("incomplete data")
        else:
            self.errors.append("The data supplied as readings cannot be "
                                    "interpreated by the certificates engine"
                                    "please rectify the errors manually using SQLStudio")
            raise ValueError("malformed data")

    def extract_readings(self):
        self.extract_pressure()
        self.extract_temp()
                
    def pressure_uncertainty(self):
        
        self.corrections = []
        #no need to check the length of the data as it is 
        #checked when extracted from the tables
        for i in range(len(self.p_indicated)):
            self.corrections.append(abs(float(
                            self.p_indicated[i])- float(
                                        self.p_calculated[i])))
        self.corrections = [round(i, find_round_value(self.data.resolution_p)) for i in \
                                    self.corrections]
        squared = [math.pow(i, 2) for i in self.corrections]
        squared.append(math.pow(float(self.data.resolution_p), 2))
        self.uncertainty_p = round(math.sqrt(sum(squared)), 
                                    find_round_value(self.data.resolution_p))    
    
    
    def temp_uncertainty(self):
        self.temp_corrections = []
        #no need to check the length of the data as it is 
        #checked when extracted from the tables
        for i in range(len(self.temp_indicated)):
            self.temp_corrections.append(abs(float(
                    self.temp_actual[i])-float(
                            self.temp_indicated[i]))) 
        squared = [math.pow(i, 2) for i in self.temp_corrections]
        squared.append(math.pow(float(self.data.resolution_temp), 2))
        self.uncertainty_temp= round(math.sqrt(sum(squared)),
                                    find_round_value(self.data.resolution_temp))
        
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
            round(self.temp_corrections[i], find_round_value(self.data.resolution_temp))]))
    
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
        
        outFile.write(certificate.render(certificate_number=self.certificate_number,
                                         date=self.data.date,
                                         by= self.calibrator,
                                         due= self.data.due,
                                         customer=self.data.customer,
                                         immersion=self.data.immersion_depth,
                                         type="AUTOCLAVE",
                                         manufacturer=self.data.manufacturer,
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
                                    round((math.sqrt(math.pow(float(self.corrections[i]), 2) *
                                    math.pow(float(self.data.resolution), 2))), 
                                    find_round_value(self.data.resolution))]))
            
        self.table = "".join(rows)
        
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
         
        self._uncertainty = round((normal_uncertainty * 2), 
                                find_round_value(self.data.resolution))
        
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
        self._table = "".join([standard_details, readings, summary])      
        self.corrections_table = ""


def find_round_value(val):
    if "." in val:
        num_digits = len(val.split(".")[1])
    else:
        num_digits = -len(val)
    return num_digits

if __name__=="__main__":
   a=ph_certificate("_8", "CK", "Caleb Kandoro", "28", "35")
   a.generate_certificate()