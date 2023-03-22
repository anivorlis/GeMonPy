import os
import pickle

import numpy as np
import pandas as pd

from abc import ABC, abstractmethod
from itertools import repeat

from tools.lib import db_connect, geometric_factor, focus_point
from tools.database_io import read_task, read_dpid_mapper, read_geometry_mapper, read_task_mapper
from tools.geodata import GeophysicalTimeSeries, GeophysicalTimeSeriesRaw

from settings.config import PATH_TO_PICKLE


class GeneralReader(ABC):

    @abstractmethod
    def read_data(self, path_to_data: str):
        pass

    @abstractmethod
    def extend(self, path_to_data: str, data: GeophysicalTimeSeriesRaw) -> GeophysicalTimeSeriesRaw:
        pass


class TerrameterDatabase(GeneralReader):

    def __init__(self, task_ids: tuple[int] = (1), structure_database: str = ''):
        self.task_ids = task_ids
        self.structure_database = structure_database
        self.data = GeophysicalTimeSeries()

    def read_data(self, path_to_data: str):

        root, dirs, files = next(os.walk(path_to_data))

        # Get structure from specific database
        if self.structure_database == '':
            self.structure_database = os.path.join(root, dirs[0], 'project.db')
        
        # full path to each folder
        fullpath_dirs = list(map(os.path.join, repeat(root), dirs))
        self.data.raw = self.make_data(fullpath_dirs)

    def extend(self, path_to_data: str) -> None:
        # Read the folder with ALL available dates
        root, dirs, files = next(os.walk(path_to_data))
        # Find the dates that are not included in data 
        new_dirs = [fpathdir for fpathdir in dirs if np.datetime64(pd.to_datetime(fpathdir, format='%Y%m%d_%H%M%S')) not in self.data.raw.dates]
        fullpath_dirs = list(map(os.path.join, repeat(root), new_dirs))
        if len(fullpath_dirs) == 0:
            print('No new data available!')
        else:
            # Make a new GeophysicalTimesSeries object
            new_data = self.make_data(fullpath_dirs)
            # Merge the old and new GeophysicalTimeSeries to a new object
            self.data.raw.extend(new_data)

    def extend_single(self, fullpath_directory: str) -> None:
        name = os.path.basename(fullpath_directory)
        # Make a new GeophysicalTimesSeries object
        new_data = self.make_data([fullpath_directory,])
        # Merge the old and new GeophysicalTimeSeries to a new object
        self.data.raw.extend(new_data)

    def save_data(self, filename: str):
        outfile = os.path.join(PATH_TO_PICKLE, filename)
        self.data.save(outfile)

    def load_data(self, filename: str):
        infile = os.path.join(PATH_TO_PICKLE, filename)
        if os.path.isfile(infile):
            self.data = GeophysicalTimeSeries.load(infile)

    def querry_ip_window_list(self, database: str):
        # Return a list with delay time + IP window widths
        with db_connect(database) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT Value From AcqSettings \
                            WHERE Setting='IP_WindowSecList' \
                            AND key2={}".format(self.task_ids[0]))
            result = cursor.fetchall()
            if result is None:
                return None
            elif len(result) == 1:
                widths = list(map(float, result[0][0].split(' ')))
                return widths
            return None
        
    def make_data(self, fullpath_dirs: str) -> GeophysicalTimeSeries :
        
        if self.structure_database != '':
            # Read structure
            task_dpid_lookup, task_dpid_lookup_reverse = read_task_mapper(self.structure_database, self.task_ids)
            dpid_abmn_lookup = read_dpid_mapper(self.structure_database, self.task_ids)
            geometry_lookuptable, geometry_lookuptable_reverse = read_geometry_mapper(
                self.structure_database, self.task_ids)
            # Calculate geometric factor and focus points
            dpid_geometric_factor_lookup = {dpid: geometric_factor(*dpid_abmn_lookup[dpid]) for dpid in dpid_abmn_lookup.keys()}
            focus_point_lookup = {dpid: focus_point(*dpid_abmn_lookup[dpid]) for dpid in dpid_abmn_lookup.keys()}
            # Get array sizes
            number_of_measurements = len(geometry_lookuptable)
            number_of_days = len(fullpath_dirs)
            number_of_ip_windows = len(self.querry_ip_window_list(self.structure_database)) - 1
            focus_x = np.empty([number_of_measurements])
            focus_z = np.empty([number_of_measurements])
            for key in focus_point_lookup:
                x, z = focus_point_lookup[key]
                index = geometry_lookuptable[key]
                focus_x[index] = x
                focus_z[index] = z
        elif self.data.raw is not None:  # Read structure from data
            number_of_measurements, _, number_of_ip_windows = self.data.raw.decay.shape
            number_of_days = len(fullpath_dirs)
            geometry_lookuptable = self.data.raw.geometry_lookuptable
            geometry_lookuptable_reverse = self.data.raw.geometry_lookuptable_reverse
            task_dpid_lookup = self.data.raw.task_dpid_lookup
            task_dpid_lookup_reverse = self.data.raw.task_dpid_lookup_reverse
            dpid_abmn_lookup = self.data.raw.dpid_abmn_lookup
            dpid_geometric_factor_lookup = self.data.raw.dpid_geometric_factor_lookup
            focus_x = self.data.raw.focus_x
            focus_z = self.data.raw.focus_z
        else:
            print('Initialize the object before you can extend it!')
            return None
        
        # Initialize numpy arrays
        voltage = np.empty([number_of_measurements, number_of_days])
        current = np.empty([number_of_measurements, number_of_days])
        resistance = np.empty([number_of_measurements, number_of_days])
        apres = np.empty([number_of_measurements, number_of_days])
        chargeability = np.empty([number_of_measurements, number_of_days])
        decay = np.empty([number_of_measurements, number_of_days, number_of_ip_windows])
        dates = np.empty(number_of_days, dtype='datetime64[s]')
        
        # Read each database in pandas dataframe and fill in the numpy matrices
        # this part can be optimized for speed
        for project_index, directory in enumerate(fullpath_dirs):
            dt = pd.to_datetime(os.path.basename(directory), format='%Y%m%d_%H%M%S')
            dates[project_index] = dt
            project = os.path.join(directory, 'project.db')
            print(project)
            df = read_task(project, ids=self.task_ids)
            if df is None:
                continue
            ipstart = df.columns.get_loc('IP1')
            ipend = df.columns.get_loc('SDev')
            for row_index, row in df.iterrows():
                key = row["DPID"]
                if key in geometry_lookuptable:
                    meas_id = geometry_lookuptable[key]
                    voltage[meas_id, project_index] = row['volt']
                    current[meas_id, project_index] = row['current']
                    resistance[meas_id, project_index] = row['res']
                    apres[meas_id, project_index] = row['apres']
                    chargeability[meas_id, project_index] = row['charg']
                    decay[meas_id, project_index, :] = row[ipstart:ipend].values
                    #print(geometry_lookuptable[key])
                else:
                    print('Measurement is a ghost!')

        data = GeophysicalTimeSeriesRaw(dates, geometry_lookuptable, geometry_lookuptable_reverse, 
                                        task_dpid_lookup, task_dpid_lookup_reverse, dpid_abmn_lookup, dpid_geometric_factor_lookup, focus_x, focus_z,
                                        voltage, current, resistance, apres, chargeability, decay)
        return data


def read_res2dinv_xyz_single(filename: str) -> np.ndarray:
    with open(filename, 'r') as fin:
        for _ in range(5):
            next(fin)
        number_of_values = next(fin).split()  # 6 has ip
        x = []
        z = []
        res = []
        charg = []  # only if the file has chargeability! If not, it is the conductivity
        for line in fin.readlines():
            if line.startswith('/'):
                break
            values = [float(x) for x in line.split()]
            x.append(values[0])
            z.append(values[1])
            res.append(values[2])
            charg.append(values[-1])
    return np.array(x), np.array(z), np.array(res), np.array(charg)
