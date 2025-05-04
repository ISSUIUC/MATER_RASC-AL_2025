from skyfield.api import load, utc
from datetime import datetime
import numpy as np
from calculators import link_budget

class MarsOrbit_Relay:

    def __init__(self, name, id, mass, max_pwr, pwr_production, pwr_store, safe_mode_duty, standby_duty, experiment_duty, a, e, i, RAAN, omega, M0, start_date):
        """
        name = name of payload (string)
        id = number inditfier (int)
        max_pwr = max power consumption in kWe (float)
        pwr_production = if power is produce, how much in kWe (float)
        pwr_store = if there is stored power how many kW (float)
        safe_mode_duty = duty cycle for power in safe 0-100 % (float)
        stanby_duty = duty cycle for power in stanby 0-100 % (float)
        experiment_duty = duty cycle for power in experiment 0-100 % (float)
        a = semimajor axis (km)
        e = ecentricity 
        i = inclination (degs)
        RAAN = right acension of the ascending node (degs)
        omega = argument of periaps (degs)
        M0 = mean enomaly at epoch (degs)
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
        self.a = a
        self.e = e
        self.i = np.radians(i)
        self.RAAN = np.radians(RAAN)
        self.omega = np.radians(omega)
        self.M0 = np.radians(M0)
        self.start_date = start_date
        self.position = self.get_position(start_date)
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

    
    def get_position(self, date):
        """
        returns satellite position
        t = time since begning in seconds
        """
        t =  (datetime.strptime(date,'%Y-%m-%d-%H-%M-%S') - datetime.strptime(self.start_date, '%Y-%m-%d-%H-%M-%S')).total_seconds()
        def kepler_E(M, e, tol=1e-10, max_iter=1000):
            """Solve Kepler's Equation for Eccentric Anomaly E using Newton-Raphson."""
            E = M if e < 0.8 else np.pi
            for _ in range(max_iter):
                f = E - e * np.sin(E) - M
                f_prime = 1 - e * np.cos(E)
                delta_E = -f / f_prime
                E += delta_E
                if abs(delta_E) < tol:
                    break
            return E

        mu = 42828.3  
        n = np.sqrt(mu / self.a**3)  
        M = self.M0 + n * (t )  
        M = M % (2 * np.pi)  

        E = kepler_E(M, self.e)
        nu = 2 * np.arctan2(np.sqrt(1 + self.e) * np.sin(E / 2),
                            np.sqrt(1 - self.e) * np.cos(E / 2))
        r = self.a * (1 - self.e * np.cos(E))

   
        x_orb = r * np.cos(nu)
        y_orb = r * np.sin(nu)
        z_orb = 0

  
        cos_raan = np.cos(self.RAAN)
        sin_raan = np.sin(self.RAAN)
        cos_i = np.cos(self.i)
        sin_i = np.sin(self.i)
        cos_argp = np.cos(self.omega)
        sin_argp = np.sin(self.omega)

        R = np.array([
            [cos_raan*cos_argp - sin_raan*sin_argp*cos_i, -cos_raan*sin_argp - sin_raan*cos_argp*cos_i, sin_raan*sin_i],
            [sin_raan*cos_argp + cos_raan*sin_argp*cos_i, -sin_raan*sin_argp + cos_raan*cos_argp*cos_i, -cos_raan*sin_i],
            [sin_argp*sin_i,                               cos_argp*sin_i,                                cos_i]
        ])

        position_orb = np.array([x_orb, y_orb, z_orb])
        position_eci = R @ position_orb
        self.position = position_eci
        return position_eci
    
    def get_view(self, mars_pos, earth_pos):
        MARS_RADIUS_KM = 3389.5             
        AU_IN_KM = 149_597_870.7            

        """
        Checks if Earth is visible from a satellite around Mars using heliocentric positions.

        Parameters:
        - sat_pos_km: (3,) np.array, satellite position in Mars-centered coordinates [km]
        - mars_pos_au: (3,) np.array, Mars position in the solar system frame [AU]
        - earth_pos_au: (3,) np.array, Earth position in the solar system frame [AU]

        Returns:
        - True if Earth is above the satellite's horizon, False otherwise
        """

        sat_pos_au_relative = self.position / AU_IN_KM

        sat_pos_au = mars_pos+ sat_pos_au_relative

        sat_to_earth_au = earth_pos - sat_pos_au

        mars_to_sat_au = sat_pos_au_relative
        sat_up = mars_to_sat_au / np.linalg.norm(mars_to_sat_au)

        angle_cosine = np.dot(sat_to_earth_au, sat_up) / np.linalg.norm(sat_to_earth_au)
        elevation_angle_rad = np.arccos(angle_cosine)

        sat_distance_au = np.linalg.norm(mars_to_sat_au)
        horizon_angle_rad = np.arcsin((MARS_RADIUS_KM / AU_IN_KM) / sat_distance_au)

        return elevation_angle_rad < (np.pi / 2 - horizon_angle_rad)
    
    def mars_link_margin_down(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,63,3,50,0)
    
    def mars_link_margin_up(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,63,3,50,0)

