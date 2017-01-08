from certificates import certificate, find_round_value
import data
from tabulator import general_tabulation, horizontal_tabulation, create_row, simple_table
import datetime 
import time
import jinja2
import os
import math
from builtins import round

class pressure_certificate(certificate):
    def __init__(self, *args):
        super().__init__(*args)
        self.template = "pressure.html"
        
    def extract_readings(self):
        '''each table has a readings string may be able to generalize 
        it with time, but for now stick with individual implementations
        each implementation interface must take a set of input readings 
        extracted and place them in the self.calculator_input list whether 
        or not the input is going to be modified'''
        table = self.data.readings
        rows = table.split(";")
        self.indicated = []
        self.calculated = []
        self.applied_mass = []
        if table == "":
            self.errors.append("The submitted data does not contain any readings")
            raise ValueError("No readings in the record")
        elif ":" in table:
            for row in rows:
                cells = row.split(":")
                if len(cells) == 3:
                    self.indicated.append(float(cells[2]))
                    self.calculated.append(float(cells[1]))
                    self.applied_mass.append(float(cells[0]))
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
       pass
        
    def uncertainty(self):
        '''all uncertainty calculations are performed in this method
        will calculate the uncertainty based on the recorded data'''
        self.corrections = []
        for i in range(len(self.indicated)):
            difference = abs(self.calculated[i] - self.indicated[i])
            self.corrections.append(round(difference, 
                                    find_round_value(self.data.resolution)))
            
        self._uncertainty = round(math.sqrt(math.pow(float(self.data.resolution), 2) +
                                     sum([math.pow(i, 2) for i in self.corrections])),
                                     find_round_value(self.data.resolution))
    
    def generate_table(self):
        data = []
        for i in range(len(self.indicated)):
            data.append(create_row([self.applied_mass[i],
                                   self.calculated[i],
                                   self.indicated[i],
                                   round(self.corrections[i], 
                                   find_round_value(self.data.resolution))]))
            
        self.table = "".join(data)

if __name__ == "__main__":
    p = pressure_certificate("_1", "CK", "Caleb Kandoro", "25", "45")
    p.generate_certificate()