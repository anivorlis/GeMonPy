import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import matplotlib.colors as colors

from tools.geodata import GeophysicalTimeSeries


def plot_raw_data(data: GeophysicalTimeSeries, type_of_plot: str, path: str):

    valid_types = {'resistance', 'apres', 'chargeability'}
    ylabels = {'resistance': 'Resistance [Ohm]',
               'apres': 'App. Resistivity [Ohm.m.]',
               'chargeability': 'Chargeability [mV/V]'}
    
    if type_of_plot in valid_types:
        values = getattr(data.raw, type_of_plot)
        try:
            values_filtered = getattr(data.filtered, type_of_plot)
        except AttributeError:
            values_filtered = None
    else:
        print('No valid type_of_plot')
        return

    dates = data.raw.dates
    dates_filtered = data.filtered.dates
    number_of_measurements = values.shape[0]

    for index in range(number_of_measurements):
        fname = os.path.join(path, str(index)+'.png')
        if os.path.exists(fname):
            continue
        print(index)
        plt.figure()
        plt.plot(dates, values[index, :], 'ko', markersize=2)
        if values_filtered is not None:
            plt.plot(dates_filtered, values_filtered[index, :], 'g--', linewidth=1)
            plt.legend(['raw', 'filtered'])
        dpid = data.raw.geometry_lookuptable_reverse[index]
        plt.title("DPID={} K={:.2f} \nA={:1f} B={:1f} M={:1f} N={:1f}".format(
            dpid, data.raw.dpid_geometric_factor_lookup[dpid], *data.raw.dpid_abmn_lookup[dpid]))
        plt.xlabel('Date')
        plt.ylabel(ylabels[type_of_plot])
        plt.xticks(rotation=15)
        plt.grid('on')
        plt.savefig(fname, dpi=300)
        plt.close()
    

def plot_decays(data: GeophysicalTimeSeries, path: str):

    values = data.raw.decay
    number_of_measurements = values.shape[0]
    for meas_id in range(number_of_measurements):
        ax = plt.axes(projection='3d')
        print(meas_id)
        # Data for three-dimensional scattered points
        time = np.array([0.03, 0.07, 0.13, 0.21, 0.31, 0.45, 0.63, 0.89, 1.29, 1.89, 2.77, 3.97])
        xdata = []
        ydata = []
        zdata = []
        
        for i in range(len(data.raw.dates)):
            for j in range(12):
                xdata.append(time[j])
                ydata.append(i)
                zdata.append(values[meas_id, i, j])
        
        ax.scatter3D(xdata, ydata, zdata, c=zdata, cmap='jet');
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Measurement Date")
        ax.set_zlabel("Chargeability (mV/V)")
        plt.savefig('Line4_{:04d}_3d_decay'.format(meas_id), dpi=400, figsize=(1400, 800))

def plot_2d_section(x: np.ndarray, y: np.ndarray, c: np.ndarray, filename: str, 
                    vmin: int, vmax: int, max_depth: int = 0, log: bool = True) -> None: 

    # Convert to negative
    if min(y) > 0:
        y = -y
    # Find bounds
    x1, x2 = min(x), max(x)
    y1, y2 = min(y), max(y)
    if max_depth == 0:
        y2 = max_depth
    # Grid the data for plotting
    xgrid = np.linspace(x1, x2, 100)
    ygrid = np.linspace(y1, y2, 100)
    xgrid, ygrid = np.meshgrid(xgrid, ygrid)
    cgrid = griddata((x, y), c, (xgrid, ygrid), method='linear')
    
    fig = plt.figure(figsize=(12, 8), facecolor='w')
    if log:
        pcm = plt.pcolormesh(xgrid, ygrid, cgrid,
                             norm=colors.SymLogNorm(linthresh=0.03, linscale=0.03,
                                                    vmin=vmin, vmax=vmax), cmap='jet')
        #fig.colorbar(pcm, orientation="horizontal", extend='both')
    else:
        pcm = plt.pcolormesh(xgrid, ygrid, cgrid, cmap='jet', vmin=vmin, vmax=vmax)
        #fig.colorbar(pcm, orientation="horizontal", extend='both')
    
    # 'beauty' plots
    plt.xlabel('X (m)')
    plt.ylabel('Z (m)')
    plt.title('Inverted Model')
    plt.axis((x1, x2, y1, y2))
    plt.axis('scaled')
    plt.savefig(filename, dpi=300)
    plt.close()