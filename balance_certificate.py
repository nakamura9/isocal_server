from utilities import percent_difference
import datetime
import data
from tabulator import general_tabulation, horizontal_tabulation, create_row, simple_table
import time
import jinja2
import os
import math
from statistics import stdev, mean
from builtins import round               

DIR = os.path.abspath(os.getcwd())

templates = jinja2.Environment(loader= jinja2.FileSystemLoader \
                               (os.path.join(DIR, "certificates\\templates")))

"""balance certificate structure:
1. start with a results table that records the settling average,corner tests,
2. cold drift  and repeatability.
3. then comes the table for the first linearity measurements
4. next the statement of uncertainty
5. followed by general information about the instrument
6. numbered tables:
    a. standards table
    b. cold start table
    c. settling times table
    d. linearity table
    e. repeability table
    f. off center table
7. repeat of the standard uncertainty
"""
class balance_certificate():
    def __init__(self, _id, initials, by, temp, humidity):
        self.id = _id
        self.today = datetime.date.today()
        self.initials = initials
        self.temp= temp
        self.humidity = humidity
        self.certificate_number(self.initials)
        self.template = "balances.html"
        
        
    def certificate_number(self, initials):
        now = datetime.datetime.now()
        self.certificate_number= "{}{}".format(now.strftime("%Y%m%d%H%M%S"),
                               self.initials)
        
    def get_data(self):
        self.data = data.session.query(data.balance).get(self.id)
        self.tare = data.session.query(data.balance_tare).get(self.id)
        self.linearity_before = data.session.query(data.balance_before_calibration).get(self.id)
        self.linearity_after = data.session.query(data.balance_linearity_after).get(self.id)
        self.off = data.session.query(data.balance_off_center).get(self.id)
        self.repeatability = data.session.query(data.balance_repeatability).get(self.id)
        self.standard = data.session.query(data.general_standards).get(self.data.standard)
        
        self.round_value = self.get_round()# used to make sure rounding off is uniform
    def get_round(self):
        standard_vals= self.standard.actual_values.split("|")
        standard_res= len(standard_vals[0].split(".")[1])#gets the number of numbers after the decimal
        return standard_res
    
    def uncertainty(self):
        """overall uncertainty of the data derived from the uncertainty of the standards, the measurements
        drift, repeatbility """
        
        stds_uncertainty = [float(i) for i in self.standard.uncertainty.split("|")]
        def squareroot_of_sum_of_squares(l):
            squares = [math.pow(i, 2) for i in l]
            return math.sqrt(sum(squares))
        
        standard_u_contrib = squareroot_of_sum_of_squares(stds_uncertainty)
        res_contrib =  (float(self.data.resolution) / 2 ) / math.sqrt(3)
        drift_contrib = abs(self.cold_drift()) / math.sqrt(3)    
        repeat_contrib = squareroot_of_sum_of_squares(self.deviation)
        
        return round(squareroot_of_sum_of_squares([standard_u_contrib,
                                   res_contrib,
                                   drift_contrib,
                                   repeat_contrib]) * 2, self.round_value)
    
    #group of functions for the results table
    def settling_average(self):
        """used to fill the field of the settling table regarding average time"""
        settling = self.data.settling_time.split(":")
        settling = [float(i) for i in settling]
        return round(mean(settling), 2)
    
    def off_max_error(self):
        '''maximum corner errors'''
        return max([self.off.a, self.off.b, self.off.c, self.off.d, self.off.e])    
        
    def cold_drift(self):
        '''the total cold start readings
        average of maximum and minimum values
        test_weight value - ((max + min)/2) '''
        cold_values = [float(i) for i in self.data.nominal_mass.split(":")]#revert later :
        average_over_span = (min(cold_values) + max(cold_values)) / 2
        return round(abs(float(self.data.warm_up_nominal) - average_over_span), self.round_value)
        
    #end group    
    
    def nominal_table(self):
        nominal = self.linearity_before.nominal_value.split(":")
        actual =self.linearity_before.actual.split(":")
        lin_up = self.linearity_before.linearity_up.split(":")
        differences = []
        for i in range(len(nominal)):
            differences.append(abs(float(actual[i])-float(lin_up[i])))
        differences = [round(i, self.round_value) for i in differences]
        data = {"Nominal Mass": nominal,
                "Actual Mass": actual,
                "Linearity Up": lin_up, 
                "Difference": differences} 
        return simple_table(data, 
                            ["Nominal Mass", "Actual Mass", "Linearity Up", "Difference"],
                            True)
        
    def standards_table(self):
        table = "<table>{}</table>"
        table_content = []
        table_content.append(create_row(["Description", "Certificate Number",
                                         "Actual Mass", "Uncertainty"]))
         
        nom = self.standard.nominal_values.split("|")
        certificate = self.standard.certificate
        actual = self.standard.actual_values.split("|")
        uncertainty = self.standard.uncertainty.split("|")
        for i in range(len(nom)):
            table_content.append(create_row([nom[i], certificate,
                                            actual[i], uncertainty[i]]))
    	
        return table.format("".join(table_content))
			
    def cold_start_table(self):
        
        table = "<table>{}<table>"
        table_content = []
        table_content.append(create_row(["Test Weight(g)",
                                         self.data.warm_up_nominal]))
        table_content.append(create_row(["Test #", "Result"]))
        cold_values = self.data.nominal_mass.split(":")
        for i in range(len(cold_values)):
            table_content.append(create_row([i+1, cold_values[i]]))
        table_content.append(create_row(["Drift",
                                         self.cold_drift()]))

        return table.format("".join(table_content))
			
    def settling_table(self):
        data= {"Reading": ["1st", "2nd", "3rd", "4th", "5th"],
               "Settling Time": self.data.settling_time.split(":")}#take only first 5 values
        return simple_table(data, ["Reading", "Settling Time"], True)
		
    def linearity_table(self):
        def get_nominals(self):
            nom_list = []
            act_list = []
            lin_list =[float(i) for i in self.linearity_after.linearity_up.split(":")]
            std_nom = [float(i) for i in self.standard.nominal_values.split("|")]
            std_act = [float(i) for i in self.standard.actual_values.split("|")]
            for i in lin_list:
                for j in std_nom:
                    if percent_difference(i, j) < 1:
                        nom_list.append(j)
                        p = std_act[std_nom.index(j)]
                        act_list.append(p)
            return nom_list, act_list
        
        nom_list, act_list = get_nominals(self)
                    
        lin_up_list = [float(i) for i in self.linearity_after.linearity_up.split(":")]
        lin_uup_list = [float(i) for i in self.linearity_after.linearity_uup.split(":")]
        lin_down_list = [float(i) for i in self.linearity_after.linearity_Down.split(":")]
        
        # sort values
        nom_list.sort()
        act_list.sort()
        lin_up_list.sort()
        lin_down_list.sort()
        lin_uup_list.sort()
        
        average_list = []
        difference_list = []
        deviation_list = []
        
        for  p in range(len(lin_up_list)):# may have to put act_list
            average_list.append(mean([lin_down_list[p], lin_up_list[p], lin_uup_list[p]]))
            difference_list.append(abs(act_list[p]- average_list[p]))
            deviation_list.append(stdev([lin_down_list[p], lin_up_list[p], lin_uup_list[p]]))
           
        data = {"Nominal Value": nom_list,
                "Actual Value": act_list,
                "Linearity Up": lin_up_list,
                "Linearity Down": lin_down_list,
                "Linearity  Up": lin_uup_list,
                "Average Reading": [round(i,self.round_value) for i in average_list],
                "Difference": [round(i,self.round_value) for i in difference_list],
                "Standard Deviation": [round(i,self.round_value) for i in deviation_list]
                }
        return simple_table(data, ["Nominal Value", "Actual Value", "Linearity Up",
                                   "Linearity Down", "Linearity  Up", "Average Reading",
                                   "Difference", "Standard Deviation"], True)
        
    def repeatability_table(self):
        half_list =[float(i) for i in self.repeatability.half_reading.split(":")]
        full_list =[float(i) for i in self.repeatability.full_reading.split(":")]
       
        reference_values = [half_list[0], full_list[0]]
        standard_nominal_values = self.standard.nominal_values.split("|")
        nominal_values = []
        actual_values = []
        for i in standard_nominal_values:
            for j in reference_values:
                if percent_difference(float(i), float(j)) < 0.01:
                    nominal_values.append(i)
                    actual_values.append(self.standard.actual_values.split("|")[standard_nominal_values.index(i)])
        
        nominal_values.sort()
        actual_values.sort()
        self.deviation=[round(stdev(half_list), self.round_value), 
                                      round(stdev(full_list), self.round_value)]
        
        data = {" ": ["1/2 Load", "Full Load"],
                "Nominal Mass":["50", "100"],#fix later!!!
                "Actual Mass":["49.9995", "99.9995"],#fix later!!!
                "1st Reading":[half_list[0], full_list[0]],
                "2nd Reading":[half_list[1], full_list[1]],
                "3rd Reading":[half_list[2], full_list[2]],
                "4th Reading":[half_list[3], full_list[3]],
                "5th Reading":[half_list[4], full_list[4]],
                "Average Reading":[round(mean(half_list), self.round_value),
                                    round(mean(full_list), self.round_value)],
                "Standard Deviation":self.deviation
                }
        return simple_table(data, [" ", "Nominal Mass", "Actual Mass",
                                   "1st Reading", "2nd Reading", "3rd Reading",
                                   "4th Reading", "5th Reading", "Average Reading",
                                   "Standard Deviation"], True)
    
    def off_center_table(self):
        table = "<table>{}</table>"
        table_contents = []
        table_contents.append(create_row(["Test Weight", self.data.off_center_mass]))
        readings = [self.off.a, self.off.b, self.off.c, self.off.d, self.off.e]
        readings = [float(i) for i in readings]
        differences = [abs(float(self.data.off_center_mass) - i ) for i in readings ]
        differences = [round(i, self.round_value) for i in differences]
        data = {"Position": ["A", "B", "C", "D", "E",],
                "Reading": readings, 
                "Weight Difference": differences}
        table_contents.append('<tr><td colspan="2">' + simple_table(data, ["Position", "Reading",
                                             "Weight Difference"], False) + '</td></tr>') 
        table_contents.append(create_row(["Minimum Reading", min(readings)]))           
        table_contents.append(create_row(["Maximum Reading", max(readings)]))           
        table_contents.append(create_row(["Average Reading", round(mean(readings), self.round_value)]))           
        table_contents.append(create_row(["Minimum Corner Error", round(min(differences), self.round_value)]))#standard round value           
        table_contents.append(create_row(["Standard Deviation of Readings", round(stdev(readings), self.round_value)]))           
        return table.format("".join(table_contents))
    
    def generate_certificate(self):
        certificate= templates.get_template(self.template)
        self.get_data()
        outFile = open("{}\\certificates\\completed\\{}.html".format(DIR,
                                                     self.certificate_number),
                        "w")
        outFile.write(certificate.render(certificate_number=self.certificate_number,
                                        date=self.today.strftime("%d/%m/%Y"),
                                         customer=self.data.customer.upper(),
                                         type= "BALANCE",
                                         manufacturer=self.data.manufacturer.upper(),
                                         serial=self.data.serial,
                                         model = self.data.model.upper(),
                                         range=self.data.range,
                                         resolution=self.data.resolution,
                                         location=self.data.location,
                                         #
                                         # tables
                                         #
                                         nominal_table = self.nominal_table(),
                                         standards_table= self.standards_table(),
                                         cold_start_table= self.cold_start_table(),
                                         settling_table= self.settling_table(),
                                         repeatability_table= self.repeatability_table(),
                                         off_table= self.off_center_table(),
                                         linearity_table = self.linearity_table(),
                                         
                                         #
                                         # results table
                                         #
                                         settling_average=self.settling_average(),
                                         corner = self.data.off_center_mass,
                                         corner_error= self.off_max_error(),
                                         drift = self.cold_drift(),
                                         half_repeat = round(self.deviation[0], self.round_value),
                                         full_repeat = round(self.deviation[1], self.round_value),
                                         #
                                         # procedure
                                         #
                                         procedure= self.data.procedure,
                                         temperature=self.temp,
                                         humidity=self.humidity,
                                         units= self.data.units.upper(),
                                         uncertainty= round(self.uncertainty(), self.round_value),
                                         comments = self.data.comments
                                         ))
        outFile.close()
if __name__ == "__main__":
    pass