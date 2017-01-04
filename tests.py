import unittest as ut
import server
import requests
import os
import data
from bs4 import BeautifulSoup
import random
class Server_tests(ut.TestCase):
    
    def test_create_certificate(self):
        
        s = requests.session()
        r = s.post("http://localhost:8080/authenticate", params={"user":"nomuri", 
                                                      "password": "123"})

       
        cert_mapping = {1:"pressure", 2:"mass", 3:"temperature",
                            4:"flow", 5:"volume", 6:"current", 7:"voltage",
                            8: "ph", 10: "length",  11:"conductivity", 
                            9:"tds", 12:"autoclave", 13:"balance"}
        for i in range(12):
            
            params = {"temp": "25",
                          "humidity": "45",
                          "id": "_{}".format(i+1),
                          "_type": cert_mapping[i+1],
                          "initials": "CK",
                          "username": "Caleb Kandoro"}
            r = s.post("http://localhost:8080/_create_certificate", data = params)
            print(r.text)
            returned_page = BeautifulSoup(r.text, "html.parser")
            self.assertEqual(returned_page.title.string, "Summary")
        
       
    
    
    
        
    #@ut.expectedFailure
    def test_upload_standard(self):
        params = {"name":"mybrass",
                  "number":"123", 
                  "nominal": "10|50|100|150|200", 
                  "traceability" : "repcal",
                  "actual":"9.9995|49.9899|100.0001|149.9997|200.0000", 
                  "uncertainty": "0.0015", 
                  "serial": "2433"}
        r = requests.post("http://localhost:8080/mobile/upload_standard", data= params)
        self.assertEqual(r.text, "success")
        params = {"name":"standard",
                  "number":"123", 
                  "nominal": "10|50|100|150|200", 
                  "traceability" : "repcal",
                  "actual":"9.9995|49.9899|100.0001|149.9997|200.0000", 
                  "uncertainty": "0.0015", 
                  "serial": "2433"}
        r = requests.post("http://localhost:8080/mobile/upload_standard", data= params)
        self.assertEqual(r.text, "success")
        
    #@ut.expectedFailure
    def test_upload_general(self):
        base = {
            "user": "nomuri",
            "customer":'delta',
            "start_time":"20:30",
            "end_time":"20:35",
            "date": "16/9/16",
            "due": "16/3/17",
            "sn": "0123",
            "immersion": "-",
            "man": "man",
            "model": "mod",
            "_range": "0-100",
            "resolution": "0.01",
            "standard": "standard",
            "location": "delta",
            "comments": "none"}
        
        pressure= {"id": "_1",
               "instrument": "pressure gauge",
               "readings": "0:0:0;2398:4.03:4",
               "corrections": "0:0:0;2398:4.03:4",
               "units": "bar",
               "_type": "pressure"}
    
        mass={"id": "_2",
          "instrument": "ohaus",
               "readings": "100.0001:100.0001;99.9999:99.9999",
               "units": "grams",
               "corrections": "",
               "_type": "mass"}
    
        temperature={"id": "_3",
                 "instrument": "water bath",
               "readings": "25:25;50:52",
               "corrections": "25:25;50:52",
               "units": "celcius",
               "_type": "temperature"}
    
        flow={"id": "_4",
          "instrument": "flow meter",
               "readings": "0.2:0.2;0.45:0.5",
               "corrections": "0.2:0.2;0.45:0.5",
               "units": "l/min",
               "_type": "flow"}
    
        volume={"id": "_5",
            "instrument": "micropippette",
               "readings": "10:10;50:50",
               "corrections": "10:10;50:50",
               "units": "ul",
               "_type": "volume"}
    
        current={"id": "_6",
             "instrument": "ammeter",
               "readings": "2:2;5:5",
               "corrections": "2:2;5:5",
               "units": "ampere",
               "_type": "current"}
    
        voltage= {"id": "_7",
              "instrument": "voltmeter",
               "corrections": "55:50;205:200",
               "readings": "55:50;205:200",
               "units": "volt",
               "_type": "voltage"}
        
        ph= {"id": "_8",
         "instrument": "PH meter",
         "corrections": "3.01:3.5;10.4:10",
         "readings": "3.01:3.5;10.4:10",
         "units": "ph",
         "_type": "ph"}
    
        tds={"id": "_9",
         "instrument": "TDS Meter",
               "readings": "205:200;800:807",
               "corrections": "205:200;800:807",
               "units": "ppt",
               "_type": "tds"}
    
        length={"id": "_10",
            "instrument": "Micrometer",
               "readings": "205:200;800:807",
               "corrections": "205:200;800:807",
               "units": "m",
               "_type": "length"}
    
        conductivity={"id": "_11",
                  "instrument": "conductivity meter",
               "readings": "0:0;23:25",
               "corrections": "0:0;23:25",
               "units": "siemens",
               "_type": "conductivity"}
        
        gen = [mass, pressure, voltage, current, ph, tds, length, volume, conductivity, flow, temperature]
    
        for i in gen:
            base.update(i) 
            r = requests.post("http://localhost:8080/mobile/upload_general", data=base)
            self.assertEqual(r.text, "success")
    
    #@ut.expectedFailure
    def test_upload_balance(self):
        payload = {"id":"_13",
              "customer":"delta",
              "start_time":"20:00",
              "end_time":"20:30",
              "date": "16/9/16",
              "sn":"0123",
              "man":"man",
              "model":"mod",
              "_range":"0-600",
              "resolution":"0.0001",
              "units":"grams",
              "location":"delta",
              "procedure":"pg02",
              "standard":"mybrass",
              "comments":"stuff to comment about",
              "warm_up_nominal": "50",
              "nominal_mass":"10|50|100|150|200",
              "settling_time":"2|2.5|3|2|1.8",
              "off_center_mass":"50", 
              "before_nominal":"10|50|100|150|200",
              "before_up":"9.9999|50.0001|99.9599|149.9979|200.0000",
              "before_actual":"10.0000|50.0000|100.0000|150.0000|200.0000",
              "after_up":"10.0005|50.0003|100.0005|150.0001|200.0002",
              "after_down":"10|50|100|150|200",
              "after_uup":"9.9999|49.9995|99.9989|149.9992|199.9999",
              "tare":"10|50|100|150|200",
              "tare_indicated":"10|50|100|150|200",
              "repeat_half":"99.9995|100.0001|99.9999|100.0005|100.0000",
              "repeat_full":"200.0005|199.9999|199.9995|200.0000|199.9989",
              "off_center":"50.0012|50.0009|49.9999|49.9995|50.0000"}
        for key, value in payload.items():
            r= requests.post("http://localhost:8080/mobile/upload_balance", data={"key": key,
                                                                                      "value": value})
            
        if r.text != "pending":
            self.assertEqual(r.text, "success")
    
    #@ut.expectedFailure  
    def test_upload_autoclave(self):
        payload =  {"id": "_12",
                    "user": "nomuri",
            "customer": "delta",
            "start_time": "20:05",
            "end_time": "20:10",
            "date": "16/9/16",
            "serial":"789",
            "immersion_depth": "-",
            "manufacturer": "man",
            "model": "mod",
            "range_temp": "0-100",
            "range_p": "0-10",
            "resolution_temp": "0.1",
            "resolution_p": "0.5",
            "units_temp": "C",
            "units_p": "bar",
            "standards": "dead weight",
            "location": "delta",
            "comments": "ok",
            "temp": "10:10;50:52",
            "pressure": "1250:2.5:2;4600:7:7"}
        for key, value in payload.items():
            r = requests.post("http://localhost:8080/mobile/upload_autoclave", data= {"key":key,
                                                                                          "value":value})
        if r.text != "pending":
            self.assertEqual(r.text, "success")
    def test_server_running(self):
        r = requests.get("http://localhost:8080")
        self.assertEqual(r.status_code, 200)
        
        
    def test_login(self):
        r = requests.post("http://localhost:8080/authenticate", params={"user":"nomuri", 
                                                      "password": "123"})
        self.assertEqual(r.status_code, 200)
        returned_page = BeautifulSoup(r.text, "html.parser")
        self.assertEqual(returned_page.title.string, "Summary")
    
    def test_create_user(self):
        d = {"name": "caleb kandoro",
                "user": "nomuri",
                "profile": "metrologist",
                "password": "123"}
        requests.get("http://localhost:8080/validate_user", params= d )
        user = data.session.query(data.users).get("nomuri")
        self.assertIsInstance(user, data.users)    
    
ut.main()
