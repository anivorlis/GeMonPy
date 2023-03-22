import os

import numpy as np

from tools.geodata import GeophysicalTimeSeries

def write_dat(data: GeophysicalTimeSeries, filename: str, task_id: int,
              include_chargeability: bool = True, index_to_write: int = -1) -> None:

    dpids = data.raw.task_dpid_lookup[task_id]
    number_of_measurements = len(dpids)
    spacing = 1
    ip_delay = 0.020
    pulse_length = 4
    with open(filename, 'w') as fout:
        # Write Header
        fout.writelines(os.path.basename(filename) + '\n')  # FileName
        fout.writelines(str(spacing) + '\n')  # SpacingX
        fout.writelines('11\n')  # General Array File
        fout.writelines('0\n')  # ArrayCode
        fout.writelines('Type of measurement (0=app.resistivity,1=resistance)\n')
        fout.writelines('1\n')
        fout.writelines(str(number_of_measurements) + '\n')
        fout.writelines('2\n')
        if include_chargeability:
            fout.writelines('1\n')
            fout.writelines('Chargeability\n')
            fout.writelines('mV/V\n')
            fout.writelines('{} {}\n'.format(ip_delay, pulse_length))
            for dpid in dpids:
                # Write Data with IP
                meas_index = data.raw.geometry_lookuptable[dpid]
                abmn = data.raw.dpid_abmn_lookup[dpid]
                fout.writelines('4 {} 0 {} 0 {} 0 {} 0 {} {}\n'.format(*abmn, 
                    data.raw.resistance[meas_index, index_to_write],
                    data.raw.chargeability[meas_index, index_to_write]))
        else:
            fout.writelines('0\n')
            for dpid in dpids:
                # Write Data without IP
                meas_index = data.raw.geometry_lookuptable[dpid]
                abmn = data.raw.dpid_abmn_lookup[dpid]
                fout.writelines('4 {} 0 {} 0 {} 0 {} 0 {}\n'.format(*abmn, 
                    data.raw.resistance[meas_index, index_to_write]))


def write_dat_timelapse(data: GeophysicalTimeSeries, filename: str, task_id: int,
                        include_chargeability: bool = True, 
                        index_to_write: int = -1,
                        index_for_baseline: int = 0) -> None:

    dpids = data.raw.task_dpid_lookup[task_id]
    number_of_measurements = len(dpids)
    spacing = 1
    ip_delay = 0.020
    pulse_length = 4
    with open(filename, 'w') as fout:
        # Write Header
        fout.writelines(os.path.basename(filename) + '\n')  # FileName
        fout.writelines(str(spacing) + '\n')  # SpacingX
        fout.writelines('11\n')  # General Array File
        fout.writelines('0\n')  # ArrayCode
        fout.writelines('Type of measurement (0=app.resistivity,1=resistance)\n')
        fout.writelines('1\n')
        fout.writelines('Type of geometric factor (0=Horizontal distance,1=Linear distance)\r\n')
        fout.writelines('0\r\n')
        fout.writelines(str(number_of_measurements) + '\n')
        fout.writelines('2\n')
        if include_chargeability:
            fout.writelines('1\n')
            fout.writelines('Chargeability\n')
            fout.writelines('mV/V\n')
            fout.writelines('{} {}\n'.format(ip_delay, pulse_length))
        else:
            fout.writelines('0\n')
        fout.writelines('Time sequence data \n')
        fout.writelines('Number of time sections \n')
        fout.writelines('2 \n')
        fout.writelines('Time unit \n')
        fout.writelines('Day \n')
        fout.writelines('Second time section interval \n')
        fout.writelines('1 \n')
        # Write data
        if include_chargeability:
            for dpid in dpids:
                # Write Data with IP
                meas_index = data.raw.geometry_lookuptable[dpid]
                abmn = data.raw.dpid_abmn_lookup[dpid]
                fout.writelines('4 {} 0 {} 0 {} 0 {} 0 {} {} {} {}\n'.format(*abmn, 
                    data.raw.resistance[meas_index, index_to_write],
                    data.raw.resistance[meas_index, index_for_baseline],
                    data.raw.chargeability[meas_index, index_to_write],
                    data.raw.chargeability[meas_index, index_for_baseline]))
        else:
            for dpid in dpids:
                # Write Data without IP
                meas_index = data.raw.geometry_lookuptable[dpid]
                abmn = data.raw.dpid_abmn_lookup[dpid]
                fout.writelines('4 {} 0 {} 0 {} 0 {} 0 {} {}\n'.format(*abmn, 
                    data.raw.resistance[meas_index, index_to_write],
                    data.raw.resistance[meas_index, index_for_baseline]))
        fout.writelines('0\r\n')
        fout.writelines('0\r\n')
        fout.writelines('0\r\n')
        fout.writelines('0\r\n')
