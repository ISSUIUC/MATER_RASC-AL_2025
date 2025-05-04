from skyfield.api import load, utc
from datetime import datetime, timedelta
import numpy as np
from calculators import link_budget

AU_to_km = 1.496e+8

class SunMarsL4_Relay:

    def __init__(self, name, id, mass, max_pwr, pwr_production, pwr_store, safe_mode_duty, standby_duty, experiment_duty):
        """
        name = name of payload (string)
        id = number inditfier (int)
        max_pwr = max power consumption in kWe (float)
        pwr_production = if power is produce, how much in kWe (float)
        pwr_store = if there is stored power how many kW (float)
        safe_mode_duty = duty cycle for power in safe 0-100 % (float)
        stanby_duty = duty cycle for power in stanby 0-100 % (float)
        experiment_duty = duty cycle for power in experiment 0-100 % (float)
        """
      
        self.name = name
        self.id = id
        self.mass = mass
        self.max_pwr = max_pwr
        self.pwr_production = pwr_production
        self.pwr_store = pwr_store
        self.safe_mode_duty = safe_mode_duty
        self.standby_duty = standby_duty
        self.experiment_duty = experiment_duty
        self.mode = 0                      

        pass
        
    def get_specs(self):
        """
        Returns satalite data
        """
        return [self.name, self.id, self.mass, self.max_pwr, self.pwr_production, self.pwr_store, self.safe_mode_duty, self.standby_duty, self.experiment_duty]

    def set_mode(self, mode):
        """
        Sets mode of payload
        mode = 0 = Safe (int)
        mode = 1 = Standby (int)
        mode = 2 = Experiment (int)
        """
        self.mode = mode
        pass
    
    def get_mode(self):
        """
        Gets mode of payload
        """
        return self.mode
    
    def consume_power(self, dt, override_duty = False, duty_overide = 0):
        """
        Returns how much power is consumed by the payload in a given time
        dt = seconds (float)
        override_duty = custom duty cycle? (boolean)
        duty_overide = value for custom power duty cycle 0-100 % (float)
        """
        if override_duty:
            return dt*(duty_overide/100)*self.max_pwr
        elif self.mode == 0:
            return dt*(self.safe_mode_duty/100)*self.max_pwr
        elif self.mode == 1:
            return dt*(self.standby_duty/100)*self.max_pwr
        elif self.mode == 2:
            return dt*(self.experiment_duty/100)*self.max_pwr
        else:
            return 0
        
    def get_Mars_distance(self, date):
        """
        Returns distance for Sun Mars L4 to Mars
        """
        planets = load('de421.bsp')
        sun, mars = planets['sun'], planets['mars']
        ts = load.timescale()
        d = (datetime.strptime(date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)
        
        l4_offset_days = 686.98 / 6  # ~114.5

        mars_now = mars.at(date).position.au
        mars_l4_date = ts.utc(d + timedelta(days=l4_offset_days))
        mars_l4 = mars.at(mars_l4_date).position.au

        sun_pos = sun.at(date).position.au

        mars_vec = mars_now - sun_pos
        L4_position = mars_l4 - sun_pos
        
        distance = np.linalg.norm(L4_position - mars_now)
        return distance * AU_to_km
    
    def get_Earth_distance(self, date):
        """
        Returns distance for Sun Mars L4 to earth
        """
        planets = load('de421.bsp')
        sun, mars, earth = planets['sun'], planets['mars'], planets['earth']
        ts = load.timescale()
        d = (datetime.strptime(date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)
        
        earth_position = earth.at(date).position.au
        
        l4_offset_days = 686.98 / 6  

        mars_now = mars.at(date).position.au
        mars_l4_date = ts.utc(d + timedelta(days=l4_offset_days))
        mars_l4 = mars.at(mars_l4_date).position.au

        sun_pos = sun.at(date).position.au

        mars_vec = mars_now - sun_pos
        L4_position = mars_l4 - sun_pos
        
        distance = np.linalg.norm(L4_position - earth_position)
        return distance * AU_to_km
    
    def get_position(self,cur_date):
        """
        Returns L4 position
        """
        planets = load('de421.bsp')
        sun, mars, earth = planets['sun'], planets['mars'], planets['earth']
        ts = load.timescale()
        d = (datetime.strptime(cur_date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)
        
        l4_offset_days = 686.98 / 6  

        mars_now = mars.at(date).position.au
        mars_l4_date = ts.utc(d + timedelta(days=l4_offset_days))
        mars_l4 = mars.at(mars_l4_date).position.au

        sun_pos = sun.at(date).position.au

        mars_vec = mars_now - sun_pos
        self.L4_position = mars_l4 - sun_pos
        return self.L4_position

    def mars_link_margin_down(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,63,3,50,0)
    
    def mars_link_margin_up(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,63,3,50,0)
    
    def earth_link_margin_up(self,distance):
        return link_budget(distance,28650,1,300,80,3,15,63,3,50,0)

    def earth_link_margin_down(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,80,3,50,0)
    
    def get_earth_eclipse(self, earth_pos, sun_pos):
        err = .99

        L4_position_np = np.array(self.L4_position)
        Earth_position_np = np.array(earth_pos)
        Sun_position_np = np.array(sun_pos)
        vec_earth = (Earth_position_np - L4_position_np)
        vec_sun = (Sun_position_np - L4_position_np)

        vec_earth_norm = vec_earth / np.linalg.norm(vec_earth)
        vec_sun_norm = vec_sun / np.linalg.norm(vec_sun)


        dot = np.dot(vec_earth_norm, vec_sun_norm)


        return dot > 1*err