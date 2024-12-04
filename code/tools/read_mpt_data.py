import numpy as np
from io import StringIO


def read_mpt_data(filename):

    file=open(filename,'r')
    lines_all=file.readlines()
    file.close()
    first_elec=0
    first_meas=0

    for i in range(0,len(lines_all)):
        lines = lines_all[i]
        if lines[0:11]=='#elec_start':
            k=i
            k=k+1
            lines = lines_all[k]  # get header
            k=k+1
            lines = lines_all[k]
            while lines[0:9]!='#elec_end':
                tmp=lines[7:].replace(',','.')
                lines=lines[:7]+tmp
                tmp=lines.replace(',',' ')

                tmp=np.loadtxt(StringIO(tmp))
                if first_elec==0:
                    elec=np.c_[tmp[1],tmp[2],tmp[3],tmp[4]]
                    first_elec=1
                else:
                    elec=np.r_[elec,np.c_[tmp[1],tmp[2],tmp[3],tmp[4]]]
                k=k+1
                lines=lines_all[k]
        elif lines[0:11]=='#data_start':
            k=i
            k=k+1
            lines = lines_all[k]  # get header
            k=k+1 
            lines = lines_all[k]  # get header
            k=k+1 
            lines = lines_all[k]  # get header
            while (lines[0:9]!='#data_end') &  (lines[0:9]!='Run Compl'):
                   tmp=lines[35:].replace(',','.')
                   lines=lines[:35]+tmp
                   tmp=lines.replace(',',' ')
                   tmp=tmp.replace('CH','00')
                   tmp=tmp.replace('GN','00')
                   tmp=tmp.replace('*','00')
                   tmp=tmp.replace('TX','00')
                   tmp=tmp.replace('Resist.','00')
                   tmp=tmp.replace('out','00')
                   tmp=tmp.replace('of','00')
                   tmp=tmp.replace('range','00')
                   tmp=tmp.replace('Error_Zero_Current','00')
                   tmp=tmp.replace('Raw_Voltages:','00')
                   tmp = tmp.replace('_','.')

                   tmp=np.loadtxt(StringIO(tmp))
                   if len(tmp)<23:
                       add=22-len(tmp)
                       tmp=np.r_[tmp,np.zeros((add,))]
                   if first_meas==0:
                       #a bm n 
                       meas=np.c_[tmp[2],tmp[4],tmp[6],tmp[8],tmp[9],tmp[10],tmp[11],tmp[14],tmp[15],tmp[18]]
                       first_meas=1   
                   else:
                       meas=np.r_[meas,np.c_[tmp[2],tmp[4],tmp[6],tmp[8],tmp[9],tmp[10],tmp[11],tmp[14],tmp[15],tmp[18]]]
                   k=k+1
                   lines=lines_all[k]
    return meas,elec   


def read_mpt_data_fast(filename: str) -> np.ndarray:
    
    with open(filename, 'r')as fin:
        
        # Find electrode start
        while True:
            line = fin.readline()
            if line.startswith('#elec_start'):
                # skip next line and break
                fin.readline()
                break
            
        # Read electrodes
        elecs = []
        elec_dict = {}
        while True:
            line = fin.readline()
            if line.startswith("#"):
                break
            else:
                tmp = line.strip().split(' ')
                elecs.append((float(tmp[1]), float(tmp[2]), float(tmp[3])))
                elec_dict[tmp[0]] = int(tmp[5])
        # Find measurement start
        while True:
            line = fin.readline()
            if line.startswith("#data_start"):
                fin.readline()
                fin.readline()
                break
        # Read measurements
        data = []
        while True:
            line = fin.readline()
            if line.startswith("#data_end"):
                break
            else:
                line = line.replace('Error_Zero_Current, ','00')
                line = line.replace('Raw_Voltages:','00')
                tmp = line.strip().split(' ')
                id_a = elec_dict[tmp[1]]
                id_b = elec_dict[tmp[2]]
                id_m = elec_dict[tmp[3]]
                id_n = elec_dict[tmp[4]]
                apres = float(tmp[5])
                res = float(tmp[6])
                res_std = float(tmp[7])
                volt = float(tmp[8])
                volt_std = float(tmp[9])
                amp = float(tmp[10])
                rs = float(tmp[11])
                data.append([id_a, id_b, id_m, id_n, apres, res, res_std, volt, volt_std, amp, rs])
        # convert to numpy arrays and return
        return np.array(data), np.array(elecs)
