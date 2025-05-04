import numpy as np

def link_budget(distance, freq, bitrate, transmit_pwr, transmit_gain, transmit_loss, required_err_bit_rate, reciver_gain, receive_loss, noise_temp, point_loss):
    transmit_power = 10*np.log10(1000*transmit_pwr)
    EIRP = transmit_power + transmit_gain - transmit_loss - point_loss
    noise_figure = 10*np.log10((1.38*10**-23)*1000*noise_temp)
    path_loss = 10*np.log10((4*np.pi*distance*1000*freq*10**6/(3*10**8))**2)
    receive_power = EIRP-path_loss+reciver_gain
    receive_eb = receive_power-noise_figure-(10*np.log10(bitrate*10**6))
    link_margin = receive_eb-required_err_bit_rate-receive_loss-point_loss
    return link_margin

def distance_to_data(distance):
    min_dist = 54600000 #km
    max_dist = 401000000 #km
    max_data = 267 #Mbps
    min_data = 150 #Mbps

    data = max_data - (max_data-min_data)*((distance-min_dist)/(max_dist-min_dist))
    return data