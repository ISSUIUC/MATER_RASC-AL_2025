class Payload:

    def __init__(self, name, id, mass, max_pwr, pwr_production, share_pwr, pwr_store, x_dim, y_dim, z_dim, safe_mode_duty, standby_duty, experiment_duty, x_pos, y_pos, z_pos, location):
        """
        name = name of payload (string)
        id = number inditfier (int)
        max_pwr = max power consumption in kWe (float)
        pwr_production = if power is produce, how much in kWe (float)
        share_pwr = does the power get shared with the rest of the system (True) or is the power stored in on board batteries (False) (boolean)
        pwr_store = if there is stored power how many kW (float)
        x_dim = x dimension of payload in meters (float)
        y_dim = y dimension of payload in meters (float)
        z_dim = z dimension of payload in meters (float)
        safe_mode_duty = duty cycle for power in safe 0-100 % (float)
        stanby_duty = duty cycle for power in stanby 0-100 % (float)
        experiment_duty = duty cycle for power in experiment 0-100 % (float)
        x_pos = x position in meters (float) 
        y_pos = y position in meters (float) 
        z_pos = z position in meters (float)
        location = what is payload attached to? Options: Starship, *another payload name*, ground (string)
        """

        self.name = name
        self.id = id
        self.mass = mass
        self.max_pwr = max_pwr
        self.pwr_production = pwr_production
        self.share_pwr = share_pwr
        self.pwr_store = pwr_store
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.z_dim = z_dim
        self.safe_mode_duty = safe_mode_duty
        self.standby_duty = standby_duty
        self.experiment_duty = experiment_duty
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.z_pos = z_pos
        self.location = location
        self.mode = 0                           

        pass

    def get_specs(self):
        """
        Returns payload data
        """
        return [self.name, self.id, self.mass, self.max_pwr, self.pwr_production, self.share_pwr, self.pwr_store, 
                self.x_dim, self.y_dim, self.z_dim, self.safe_mode_duty, self.standby_duty, self.experiment_duty]

    def set_mode(self, mode):
        """
        Sets mode of payload
        mode = 0 = Safe (int)
        mode = 1 = Standby (int)
        mode = 2 = Experiment (int)
        """
        if mode == "Active":
            self.mode = 2
        elif mode == "Standby":
            self.mode = 1
        else:
            self.mode = 0
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
        
    def set_position(self,x,y,mesh):
        """
        Updates the position of a payload
        x = new x position in meters (float)
        y = new y position in meters (float)
        surface_heightmap = surface in meters
        """
        res = mesh[0]
        surface_heightmap = mesh[1]
        if 0 <= y < surface_heightmap.shape[0] and 0 <= x < surface_heightmap.shape[1]:
            z = surface_heightmap[int(y), int(x)]
        else:
            z = 0  
        self.x_pos = float(x)
        self.y_pos = float(y)
        self.z_pos = float(z)
        pass

    def get_position(self):
        """
        Returns the current position of a payload
        """
        return [self.x_pos, self.y_pos, self.z_pos]
    
    def set_location(self,location):
        """
        Updates the location of the payload
        location = what is payload attached to? Options: Starship, *another payload name*, ground (string)
        """
        self.location = location
        pass

    def get_location(self):
        """
        returns current location
        """
        return self.location
    

    
