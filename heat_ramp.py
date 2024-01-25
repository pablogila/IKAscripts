# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 12:17:32 2024

@author: QBSM
"""


import time
try:
    from ika.magnetic_stirrer import MagneticStirrer
except:
    print('ERROR: Failed to load ika.magnetic_stirrer. Install from https://gitlab.com/heingroup/ika')


log_file = 'heat_ramp_log.txt'


def get_current_date():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def get_sensor_T():
    port = 'COM4'
    plate = MagneticStirrer(device_port = port)
    return float(plate.read_actual_external_sensor_value().split()[0])


def write_log(start_time, target_T, print_log = True):
    f = open(log_file, 'a')
    log = str((time.time() - start_time) / 60) + '\t' + str(target_T) + '\t' + str(get_sensor_T())+'\n'
    f.write(log)
    f.close()
    if print_log:
        print(log)
    return


def is_close_to_target_T(target_T, increasing = None, sensibility = 0.2):
    if increasing == True:
        return (target_T - sensibility) <= get_sensor_T()
    elif increasing == False:
        return get_sensor_T() <= (target_T + sensibility)
    else:
        return (target_T - sensibility) <= get_sensor_T() <= (target_T + sensibility)


def set_to_T_and_wait(target_T, wait_time = 120):

    port = 'COM4'
    plate = MagneticStirrer(device_port = port)

    message_init = 'Aiming to ' + str(target_T) + 'ºC...'
    print(message_init)
    f = open(log_file, 'a')
    f.write('# ' + message_init + '\n')
    f.close()

    plate.target_temperature = int(target_T)
    plate.start_heating()
    plate.start_stirring()

    start_time = time.time()
    ready = False
    while not ready:
        while not is_close_to_target_T(target_T):
            time.sleep(1)
        time.sleep(wait_time)
        if is_close_to_target_T(target_T):
            ready = True

    message_final = 'Stabilized at target T after ' + time.time() - start_time + ' seconds'
    print(message_final)
    f = open(log_file, 'a')
    f.write('# ' + message_final + '\n')
    f.close()
    return


# total_time in minutes, T in ºC
def heat_ramp(total_time = 60, start_T = 25, final_T = 45, increasing = True, keep_heating = True, delta_T = 2):
    
    date = get_current_date()
    start_message_1 = 'Starting new heat ramp on ' + date
    start_message_2 = 'total_time=' + str(total_time) + ', start_T=' + str(start_T) + ', final_T=' + str(final_T) + ', increasing=' + increasing + ', delta_T=' + str(delta_T)
    
    print(start_message_1)
    print(start_message_2)
    f = open(log_file, 'w')
    f.write('# ' + start_message_1 + '\n')
    f.write('# ' + start_message_2 + '\n')
    f.write('# Log format: minutes    target_T    sensor_T\n')
    f.close()

    target_T = start_T
    delta_time = (total_time / ((final_T - start_T) / delta_T)) * 60 # in seconds

    if increasing == False:
        delta_T = - delta_T

    port = 'COM4'
    plate = MagneticStirrer(device_port = port)
    plate.target_stir_rate = 600
    plate.target_temperature = int(target_T)
    plate.start_heating()
    plate.start_stirring()

    set_to_T_and_wait(target_T)

    start_time = time.time()
    waiting_time = 0

    while get_sensor_T() <= final_T:

        if is_close_to_target_T(target_T, increasing):
            write_log(start_time, target_T)

            target_T += delta_T
            plate.target_temperature = int(target_T)
            
            new_delta_time = delta_time - waiting_time
            if new_delta_time < 0:
                new_delta_time = 0
            time.sleep(new_delta_time)
            waiting_time = 0
        
        else:
            time.sleep(1)
            waiting_time += 1

    final_time = (time.time() - start_time) / 60 # in minutes
    final_message = 'Finished heat ramp from' + str(start_T) + ' to ' + str(final_T) + ' in ' + str(final_time) + ' minutes'
    print(final_message)
    f = open(log_file, 'a')
    f.write('# ' + final_message + '\n')
    f.close()

    if keep_heating == True:
        print('Keeping at ' + str(final_T) + 'ºC')
        plate.target_temperature = int(final_T)
    else:
        plate.stop_heating()
        plate.stop_stirring()
        plate.disconnect()
    
    return


if __name__ == "__main__":
    heat_ramp(120, 70, 130)

