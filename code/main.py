import os

from shutil import copyfile

import numpy as np
import pandas as pd

from reader import TerrameterDatabase, read_res2dinv_xyz_single
from tools.lib import my_timer

import filtering as flt
import plotter as p
import writter as w

from inverter import invert_batch_file

from tools.geodata import GeophysicalTimeSeries

from settings.config import PATH_TO_DATA, PATH_TO_PLOT, PATH_TO_PSEUDO, PATH_TO_PICKLE, PATH_TO_INVERSION_OUTPUT, INVERSION_PARAMS
from settings.config import TASK_IDS, PICKLE_NAME

PICKLE_FULLPATH = os.path.join(PATH_TO_PICKLE, PICKLE_NAME)

@my_timer
def read_data():
    reader = TerrameterDatabase(TASK_IDS)

    path = PATH_TO_DATA

    reader.read_data(path)
    reader.save_data(PICKLE_NAME)

@my_timer
def extend_data():
    reader = TerrameterDatabase(TASK_IDS)

    path = PATH_TO_DATA

    reader.load_data(PICKLE_NAME)
    reader.extend(path)
    reader.save_data(PICKLE_NAME)

@my_timer
def filterr():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    # Fill Strategy
    fill = flt.FillMissingData()
    data.filtered.dates, data.filtered.resistance = fill.filter(
        data.raw.dates, data.raw.resistance)
    _, data.filtered.apres = fill.filter(
        data.raw.dates, data.raw.apres)
    _, data.filtered.chargeability = fill.filter(
        data.raw.dates, data.raw.chargeability)
    # Store object
    data.save(PICKLE_FULLPATH)

@my_timer
def plot():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    p.plot_raw_data(data, 'resistance', os.path.join(PATH_TO_PLOT, 'resistance'))
    p.plot_raw_data(data, 'apres', os.path.join(PATH_TO_PLOT, 'apres'))
    p.plot_raw_data(data, 'chargeability', os.path.join(PATH_TO_PLOT, 'chargeability'))


@my_timer
def write_dats_indivual():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'individual')
    if not os.path.exists(fullpath):
        os.mkdir(fullpath)

    for task_id in TASK_IDS:
        files_written = []
        task = f"task_{task_id}"
        if not os.path.exists(os.path.join(fullpath, task)):
            os.mkdir(os.path.join(fullpath, task))
        # Write Res2DInv dat files
        for index_day in range(data.raw.resistance.shape[1]):
            dt = data.raw.dates[index_day]
            filename = os.path.join(fullpath, task, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00.dat')
            if os.path.isfile(filename[:-4] + '.xyz'):
                continue
            files_written.append(filename)
            w.write_dat(data, filename, task_id, index_to_write=index_day)
        # Copy inversion parameters file (if not there already)
        params_file = os.path.join(fullpath, task, os.path.basename(INVERSION_PARAMS))
        if not os.path.isfile(params_file):
            copyfile(INVERSION_PARAMS, params_file)
        # Write Res2DInv Batch File (if at least 1 new file present)
        if len(files_written) > 0:
            batch_file = os.path.join(fullpath, task, 'batch.bth')
            with open(batch_file, 'w') as fout:
                fout.writelines(str(len(files_written)) + '\n')
                fout.writelines('INVERSION PARAMETERS FILES USED \n')
                for index_file in range(len(files_written)):
                    fout.writelines(f'DATA FILE {index_file} \n')
                    fout.writelines(files_written[index_file] + '\n')
                    fout.writelines(files_written[index_file].replace('.dat', '.inv') + '\n')
                    fout.writelines(params_file + '\n')


@my_timer
def write_dats_timelapse():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'timelapse')
    if not os.path.exists(fullpath):
        os.mkdir(fullpath)

    for task_id in TASK_IDS:
        files_written = []
        task = f"task_{task_id}"
        if not os.path.exists(os.path.join(fullpath, task)):
            os.mkdir(os.path.join(fullpath, task))
        # Write Res2DInv dat files
        for index_day in range(5, data.raw.resistance.shape[1]):
            dt = data.raw.dates[index_day]
            filename = os.path.join(fullpath, task, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00.dat')
            if os.path.isfile(filename[:-4] + '.xyz'):
                continue
            files_written.append(filename)
            w.write_dat_timelapse(data, filename, task_id,
                                index_to_write=index_day,
                                index_for_baseline=0)
        # Copy inversion parameters file (if not there already)
        params_file = os.path.join(fullpath, task, os.path.basename(INVERSION_PARAMS))
        if not os.path.isfile(params_file):
            copyfile(INVERSION_PARAMS, params_file)
        # Write Res2DInv Batch File (if at least 1 new file present)
        if len(files_written) > 0:
            batch_file = os.path.join(fullpath, task, 'batch.bth')
            params_file = os.path.join(fullpath, task, os.path.basename(INVERSION_PARAMS))
            with open(batch_file, 'w') as fout:
                fout.writelines(str(len(files_written)) + '\n')
                fout.writelines('INVERSION PARAMETERS FILES USED \n')
                for index_file in range(len(files_written)):
                    fout.writelines(f'DATA FILE {index_file} \n')
                    fout.writelines(files_written[index_file] + '\n')
                    fout.writelines(files_written[index_file].replace('.dat', '.inv') + '\n')
                    fout.writelines(params_file + '\n')



@my_timer
def invert_single():

    for task_id in TASK_IDS:
        task = f"task_{task_id}"
        fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'individual')
        batch_file = os.path.join(fullpath, task, 'batch.bth')
        if os.path.isfile(batch_file):
            invert_batch_file(batch_file)
            os.remove(batch_file)

@my_timer
def invert_timelapse():

    for task_id in TASK_IDS:
        task = f"task_{task_id}"
        fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'timelapse')
        batch_file = os.path.join(fullpath, task, 'batch.bth')
        if os.path.isfile(batch_file):
            invert_batch_file(batch_file)
            os.remove(batch_file)


@my_timer
def read_results_single():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    for task_id in TASK_IDS:
        task = f"task_{task_id}"

        fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'individual', task)
        root, dirs, files = next(os.walk(fullpath))

        xyz_files = []
        for f in files:
            if f.endswith('.xyz'):
                xyz_files.append(os.path.join(root, f))

        new_dirs = [fpathdir for fpathdir in xyz_files if np.datetime64(pd.to_datetime(os.path.basename(fpathdir)[:-4], format='%Y_%m_%d_%H_%M_%S')) not in data.inverted[task_id].dates]
        if len(new_dirs) == 0:
            print('No files to process in the path!')
        else:
            if len(data.inverted[task_id].dates) == 0:
                # Get the first file from the list
                filename = new_dirs.pop(0)
                x, z, res, charg = read_res2dinv_xyz_single(filename)
                data.inverted[task_id].dates = np.array([pd.to_datetime(os.path.basename(filename)[:-4], format='%Y_%m_%d_%H_%M_%S')], dtype='datetime64[h]')
                data.inverted[task_id].x = x
                data.inverted[task_id].depth = z
                data.inverted[task_id].resistivity = res
                data.inverted[task_id].chargeability = charg
            for filename in new_dirs:
                dt = np.array([pd.to_datetime(os.path.basename(filename)[:-4], format='%Y_%m_%d_%H_%M_%S')], dtype='datetime64[h]')
                _, _, res, charg = read_res2dinv_xyz_single(filename)
                data.inverted[task_id].extend(dt, res, charg)

    data.save(PICKLE_FULLPATH)

@my_timer
def plot_pseudo_single():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    for task_id in TASK_IDS:
        task = f"task_{task_id}"

        fullpath = os.path.join(PATH_TO_PSEUDO, task)
        root, dirs, files = next(os.walk(fullpath))

        dpids = data.raw.task_dpid_lookup[task_id]
        indices = np.sort([data.raw.geometry_lookuptable[dpid] for dpid in dpids])
        for index, dt in enumerate(data.raw[task_id].dates):
            res_filename = os.path.join(fullpath, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00_res.png')
            charg_filename = os.path.join(fullpath, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00_charg.png')
            x = data.raw.focus_x[indices]
            depth = data.raw.focus_z[indices]
            res = data.raw.apres[indices, index]
            charg = data.raw.charg[indices, index]
            title = str(dt)
            if not os.path.isfile(res_filename):
                p.plot_2d_section(x, depth, res, res_filename, vmin=10, vmax=300)
            if not os.path.isfile(charg_filename):
                p.plot_2d_section(x, depth, charg, charg_filename, vmin=1, vmax=8, title=title, log=False)
    data.save(PICKLE_FULLPATH)

@my_timer
def plot_results_single():

    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    for task_id in TASK_IDS:
        task = f"task_{task_id}"

        fullpath = os.path.join(PATH_TO_INVERSION_OUTPUT, 'individual', task)
        root, dirs, files = next(os.walk(fullpath))

        for index, dt in enumerate(data.inverted[task_id].dates):
            res_filename = os.path.join(fullpath, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00_res.png')
            charg_filename = os.path.join(fullpath, np.datetime_as_string(dt, unit='h').replace('-', '_').replace('T', '_') + '_00_00_charg.png')
            x = data.inverted[task_id].x
            depth = data.inverted[task_id].depth
            res = data.inverted[task_id].resistivity[:, index]
            charg = data.inverted[task_id].chargeability[:, index]
            title = str(dt)
            if not os.path.isfile(res_filename):
                p.plot_2d_section(x, depth, res, res_filename, vmin=10, vmax=300)
            if not os.path.isfile(charg_filename):
                p.plot_2d_section(x, depth, charg, charg_filename, vmin=1, vmax=8, title=title, log=False)
    data.save(PICKLE_FULLPATH)


@my_timer
def data_to_csv():
    data = GeophysicalTimeSeries.load(PICKLE_FULLPATH)

    # data-raw
    filename_raw = os.path.join(PATH_TO_PICKLE, 'data_raw.csv')
    with open(filename_raw, 'w') as fout:
        fout.writelines("dt,dpid,tid,fx,fz,apres,charg\n")
        number_of_data, number_of_days = data.raw.apres.shape
        for index_day in range(number_of_days):
            for index_data in range(number_of_data):
                dpid = data.raw.geometry_lookuptable_reverse[index_data]
                fout.writelines("{},{},{},{},{},{},{}\n".format(
                    np.datetime_as_string(data.raw.dates[index_day], unit='h').replace('T', ' ') + ':00:00',
                    dpid, data.raw.task_dpid_lookup_reverse[dpid],
                    data.raw.focus_x[index_data],
                    data.raw.focus_z[index_data],
                    data.raw.apres[index_data, index_day],
                    data.raw.chargeability[index_data, index_day]
                ))
    # data-filtered
    filename_filtered = os.path.join(PATH_TO_PICKLE, 'data_filtered.csv')
    with open(filename_filtered, 'w') as fout:
        fout.writelines("dt,dpid,tid,fx,fz,apres,charg\n")
        number_of_data, number_of_days = data.filtered.apres.shape
        for index_day in range(number_of_days):
            for index_data in range(number_of_data):
                dpid = data.raw.geometry_lookuptable_reverse[index_data]
                fout.writelines("{},{},{},{},{},{}\n".format(
                    np.datetime_as_string(data.filtered.dates[index_day], unit='h').replace('T', ' ') + ':00:00',
                    dpid, data.raw.task_dpid_lookup_reverse[dpid],
                    data.raw.focus_x[index_data],
                    data.raw.focus_z[index_data],
                    data.filtered.apres[index_data, index_day],
                    data.filtered.chargeability[index_data, index_day]
                ))
    # data-inverted
    filename_inverted = os.path.join(PATH_TO_PICKLE, 'data_inverted.csv')
    with open(filename_inverted, 'w') as fout:
        fout.writelines("dt,tid,x,z,resistivity,chargeability\n")
        for task_id in TASK_IDS:
            number_of_data, number_of_days = data.inverted[task_id].resistivity.shape
            for index_day in range(number_of_days):
                for index_data in range(number_of_data):
                    fout.writelines("{},{},{},{},{},{}\n".format(
                        np.datetime_as_string(data.inverted[task_id].dates[index_day], unit='h').replace('T', ' ') + ':00:00',
                        task_id,
                        data.inverted[task_id].x[index_data],
                        data.inverted[task_id].depth[index_data],
                        data.inverted[task_id].resistivity[index_data, index_day],
                        data.inverted[task_id].chargeability[index_data, index_day]
                    ))

def process_new_data():
    extend_data()
    filterr()
    write_dats_indivual()
    write_dats_timelapse()
    invert_single()
    invert_timelapse()
    read_results_single()
    plot_pseudo_single()
    plot_results_single()
    data_to_csv()


if __name__ == "__main__":
    #read_data()
    extend_data()
    filterr()
    plot()
    write_dats_indivual()
    write_dats_timelapse()
    invert_single()
    invert_timelapse()
    read_results_single()
    plot_pseudo_single()
    plot_results_single()
    data_to_csv()
