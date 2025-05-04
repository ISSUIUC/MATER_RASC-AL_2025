from skyfield.api import load, utc
from datetime import datetime, timedelta
import numpy as np
from calculators import link_budget
from stl import mesh
from scipy.interpolate import griddata


AU_to_km = 1.496e+8

class Base:
    
    def __init__(self, start_date, base_latitude, base_longitude, ground_res, ground_size):
        """
        start_date = date to define intial postions (string) YYYY-MM-DD-HH-MM-SS
        base_longitude = base longitude 
        base_latitude = base latitude
        self.date = is the current date (string) YYYY-MM-DD-HH-MM-SS
        self.Earth_pos = Earth x, y ,z position
        self.Mars_pos = Mars x, y ,z position
        ground_res = how many meters is an index
        ground_size = how many indexs are the x and y dimenstions
        """
        
                      
        planets = load('de421.bsp')
        earth, mars, sun = planets['earth'], planets['mars'], planets['sun']
        ts = load.timescale()
        d = (datetime.strptime(start_date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)

        self.date = start_date
        self.base_long = base_longitude
        self.base_lat = base_latitude
        self.Earth_pos = earth.at(date).position.au
        self.Mars_pos = mars.at(date).position.au
        self.Sun_pos = sun.at(date).position.au
        self.surface = np.zeros((ground_size,ground_size))
        self.surface_res = ground_res
        
        pass

    def get_date(self):
        """
        get date
        """
        return self.date

    def update(self,dt):
        """
        dt = time in seconds to step (float)
        """
        self.date = (datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S') + timedelta(seconds=dt)).strftime('%Y-%m-%d-%H-%M-%S')

        planets = load('de421.bsp')
        earth, mars = planets['earth'], planets['mars']
        ts = load.timescale()
        d = (datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)
        
        self.Earth_pos = earth.at(date).position.au
        self.Mars_pos = mars.at(date).position.au
        pass

    def get_Earth_pos(self):
        """
        returns Earth positions
        """
        return self.Earth_pos
    
    def get_Mars_pos(self):
        """
        returns Mars positions
        """
        return self.Mars_pos
    
    def get_Sun_pos(self):
        """
        returns Sun positions
        """
        return self.Sun_pos
    
    
    def get_Earth_view(self):
        
        mars_to_earth = self.Earth_pos - self.Mars_pos
        mars_to_earth_unit = mars_to_earth / np.linalg.norm(mars_to_earth)

        mars_rotation_period = 1.02749125  
        mars_seconds_per_degree = (mars_rotation_period * 24 * 3600) / 360.0
        

        base_date = datetime(2000, 1, 6)  
        date_dt = datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S')
        delta_days = (date_dt - base_date).total_seconds() / (24 * 3600)
        mars_rotation_angle = (delta_days * 360 / mars_rotation_period) % 360
        
        adjusted_longitude = (self.base_long - mars_rotation_angle) % 360
        
        prime_meridian_vector = np.array([np.cos(np.radians(adjusted_longitude)), np.sin(np.radians(adjusted_longitude)), 0])
        
        alignment = np.dot(mars_to_earth_unit, prime_meridian_vector) 
        

        return alignment > 0 
    
    def get_earth_eclipse(self):
        err = .99

        Mars_position_np = np.array(self.Mars_pos)
        Earth_position_np = np.array(self.Earth_pos)
        Sun_position_np = np.array(self.Sun_pos)
        vec_earth = (Earth_position_np - Mars_position_np)
        vec_sun = (Sun_position_np - Mars_position_np)

        vec_earth_norm = vec_earth / np.linalg.norm(vec_earth)
        vec_sun_norm = vec_sun / np.linalg.norm(vec_sun)


        dot = np.dot(vec_earth_norm, vec_sun_norm)


        return dot > 1*err

    def get_earth_distance(self):
        """
        returns distance in kilometers
        """
        distance = np.linalg.norm(abs(self.Earth_pos - self.Mars_pos))
        return distance*AU_to_km
    
    def get_L4_view(self):
        Sun = load('de421.bsp')
        sun = Sun['sun']
        ts = load.timescale()
        d = (datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S')).replace(tzinfo=utc)
        date = ts.utc(d)
        sun_position = sun.at(date).position.au
        sun_to_mars = self.Mars_pos - sun_position
        
        theta = np.radians(60)
        rotation_matrix = np.array([[np.cos(theta), -np.sin(theta), 0],
                                    [np.sin(theta), np.cos(theta), 0],
                                    [0, 0, 1]])
        L4_position = sun_position + rotation_matrix @ sun_to_mars

        mars_to_L4 = L4_position - self.Mars_pos
        mars_to_L4_unit = mars_to_L4 / np.linalg.norm(mars_to_L4)

        mars_rotation_period = 1.02749125  
        mars_seconds_per_degree = (mars_rotation_period * 24 * 3600) / 360.0
        
        base_date = datetime(2000, 1, 6)  
        date_dt = datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S')
        delta_days = (date_dt - base_date).total_seconds() / (24 * 3600)
        mars_rotation_angle = (delta_days * 360 / mars_rotation_period) % 360
        
        adjusted_longitude = (self.base_long - mars_rotation_angle) % 360
        
        prime_meridian_vector = np.array([np.cos(np.radians(adjusted_longitude)), np.sin(np.radians(adjusted_longitude)), 0])
        
        alignment = np.dot(mars_to_L4_unit, prime_meridian_vector) 
        

        return alignment > 0
    
    def link_budget(self):
        distance = self.get_earth_distance()
        view = self.get_Earth_view

        if not(view):
            return -100
        

        link_margin = distance

        return link_margin
    
    def get_mars_angle(self):
        sun_eclipse_margin=90
        mars_to_earth = self.Earth_pos - self.Mars_pos
        mars_to_earth_unit = mars_to_earth / np.linalg.norm(mars_to_earth)

        mars_to_sun = self.Sun_pos - self.Mars_pos
        mars_to_sun_unit = mars_to_sun / np.linalg.norm(mars_to_sun)

        eclipse_cos_threshold = np.cos(np.radians(sun_eclipse_margin))
        eclipse_alignment = np.dot(mars_to_earth_unit, mars_to_sun_unit)
        eclipse = eclipse_alignment > eclipse_cos_threshold

        mars_rotation_period = 1.02749125 
        mars_seconds_per_degree = (mars_rotation_period * 24 * 3600) / 360.0

        base_date = datetime(2000, 1, 6)  
        date_dt = datetime.strptime(self.date, '%Y-%m-%d-%H-%M-%S')
        delta_days = (date_dt - base_date).total_seconds() / (24 * 3600)
        mars_rotation_angle = (delta_days * 360 / mars_rotation_period) % 360

        adjusted_longitude = (self.base_long - mars_rotation_angle) % 360

        prime_meridian_vector = np.array([
            np.cos(np.radians(adjusted_longitude)), 
            np.sin(np.radians(adjusted_longitude)), 
            0
        ])
        return(prime_meridian_vector)
    
    
    def get_satellite_visible(self, sat_pos):
        """
        Determines if a satellite is visible from a location on Mars.
        
        Parameters:
        - sat_pos_km: numpy array, [x, y, z] position of satellite in km (Mars ECEF)
        - observer_lat, observer_lon: latitude and longitude on Mars (degrees)
        - observer_alt_km: altitude above Mars surface in km

        Returns:
        - True if satellite is above horizon, False otherwise
        """
        MARS_RADIUS_KM = 3389.5
        def latlon_to_ecef(lat_deg, lon_deg, alt_km=0):
            """Converts lat/lon/alt to ECEF coordinates for Mars."""
            lat = np.radians(lat_deg)
            lon = np.radians(lon_deg)
            
            r = MARS_RADIUS_KM + alt_km
            x = r * np.cos(lat) * np.cos(lon)
            y = r * np.cos(lat) * np.sin(lon)
            z = r * np.sin(lat)
            
            return np.array([x, y, z])

        observer_pos = latlon_to_ecef(self.base_lat, self.base_long)
        
        sat_vector = sat_pos - observer_pos
        observer_up = observer_pos / np.linalg.norm(observer_pos)
        
        dot_product = np.dot(sat_vector, observer_up)
        
        return dot_product > 0  
    
    def earth_link_margin_up(self,distance):
        return link_budget(distance,28650,1,300,80,3,15,63,3,50,0)

    def earth_link_margin_down(self,distance):
        return link_budget(distance,28650,1,300,63,3,15,80,3,50,0)
    
    def get_satellite_distance(self, sat_pos):
        """
        Determines if a satellite is visible from a location on Mars.
        
        Parameters:
        - sat_pos_km: numpy array, [x, y, z] position of satellite in km (Mars ECEF)
        - observer_lat, observer_lon: latitude and longitude on Mars (degrees)
        - observer_alt_km: altitude above Mars surface in km

        Returns:
        - True if satellite is above horizon, False otherwise
        """
        MARS_RADIUS_KM = 3389.5
        def latlon_to_ecef(lat_deg, lon_deg, alt_km=0):
            """Converts lat/lon/alt to ECEF coordinates for Mars."""
            lat = np.radians(lat_deg)
            lon = np.radians(lon_deg)
            
            r = MARS_RADIUS_KM + alt_km
            x = r * np.cos(lat) * np.cos(lon)
            y = r * np.cos(lat) * np.sin(lon)
            z = r * np.sin(lat)
            
            return np.array([x, y, z])

        observer_pos = latlon_to_ecef(self.base_lat, self.base_long)
        
        sat_vector = sat_pos - observer_pos

        return np.linalg.norm(sat_vector)
    
    def get_surface(self):
        return self.surface_res, self.surface
    
    def set_surface(self, surface_mesh_path):

        mesh_data = mesh.Mesh.from_file(surface_mesh_path)
        matrix_size = len(self.surface)
        all_points = mesh_data.vectors.reshape(-1, 3)

        min_x, min_y = np.min(all_points[:, 0]), np.min(all_points[:, 1])
        max_x, max_y = np.max(all_points[:, 0]), np.max(all_points[:, 1])

        norm_x = (all_points[:, 0] - min_x) / (max_x - min_x)
        norm_y = (all_points[:, 1] - min_y) / (max_y - min_y)

        points = np.vstack((norm_x, norm_y)).T
        values = all_points[:, 2]

        grid_x, grid_y = np.meshgrid(
            np.linspace(0, 1, matrix_size),
            np.linspace(0, 1, matrix_size)
        )

        Z_matrix = griddata(points, values, (grid_x, grid_y), method='cubic')

        Z_matrix = np.nan_to_num(Z_matrix)
        self.surface = Z_matrix
        pass

    
    