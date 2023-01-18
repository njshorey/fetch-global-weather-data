import numpy as np
import matplotlib.pyplot as plt #(removable for production)
from time import time
from netCDF4 import Dataset
from datetime import datetime, timedelta
import json
from PIL import Image

#make download changes here
RES = str('0p25_1hr') #adjust resolution of data here! '1p00' (1deg, 3hr projections), '0p50' (0.5deg, 3hr projections), '0p25' (0.25deg, 3hr projections), '0p25_1hr' (0.25deg, 1hr projections)
files_wanted= 72

start = time()
print(datetime.now().minute)
timestamp = datetime.utcnow() + timedelta(hours=-6)
rem = timestamp.hour%6
timestamp_iter = timestamp + timedelta(hours=-1*rem)
now = timestamp_iter.hour
YYYYMMDD = str(timestamp_iter.strftime("%Y%m%d"))
HH = str(now//1) if now >=10 else f"0{str(now//1)}"
print(YYYYMMDD, HH, RES)

def round_floats(o):
    if isinstance(o, float):
        return round(o, 5)
    if isinstance(o, dict):
        return {k: round_floats(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round_floats(x) for x in o]
    return o

url = 'http://nomads.ncep.noaa.gov:80/dods/gfs_{0}/gfs{1}/gfs_{0}_{2}z'.format(RES, YYYYMMDD, HH)
ds = Dataset(url)

lon1 = float(ds.variables['lon'][0])
lon2 = float(ds.variables['lon'][-1])
lat1_orig = float(ds.variables['lat'][0])
lat2_orig = float(ds.variables['lat'][-1])
nx = ds.dimensions['lon'].size
ny = ds.dimensions['lat'].size
nt = ds.dimensions['time'].size
dx = abs(lon2 - lon1) / (nx-1)
dy = abs(lat2_orig - lat1_orig) / (ny-1)
dt = abs(ds.variables['time'][-1]-ds.variables['time'][0]) / (nt-1)

timearray = ds.variables['time'][:int(files_wanted)]
timearray_min = min(timearray)
timearray = [x - timearray_min for x in timearray]
ugrd10m_base = ds.variables['ugrd10m'][:int(files_wanted),:,:]
vgrd10m_base = ds.variables['vgrd10m'][:int(files_wanted),:,:]
ds.close()
print('Download Successful')
print('dx:',dx,'dy:',dy,'dt:',dt, 'nx:',nx,'ny:',ny)
for i , tval in enumerate(timearray):
    timestamp = datetime.utcnow() + timedelta(hours=-6)
    rem = timestamp.hour%6
    timestamp_iter = timestamp + timedelta(days=tval, hours=-1*rem)
    now = timestamp_iter.hour
    YYYYMMDD = str(timestamp_iter.strftime("%Y%m%d"))
    HH = str(now//1) if now >=10 else f"0{str(now//1)}"
    if lat1_orig < lat2_orig:
        ugrd10m = round_floats( np.flipud(ugrd10m_base[i,:,:]).flatten().filled().tolist() )#round_floats( np.flipud(ds.variables['ugrd10m'][i,:,:]).flatten().filled().tolist() )
        vgrd10m = round_floats( np.flipud(vgrd10m_base[i,:,:]).flatten().filled().tolist() )#round_floats( np.flipud(ds.variables['vgrd10m'][i,:,:]).flatten().filled().tolist() )
        lat2 = lat1_orig
        lat1 = lat2_orig
    else:
        ugrd10m = round_floats( ugrd10m_base[i,:,:].flatten().filled().tolist() )#round_floats( ds.variables['ugrd10m'][i,:,:].flatten().filled().tolist() )
        vgrd10m = round_floats( vgrd10m_base[i,:,:].flatten().filled().tolist() )#round_floats( ds.variables['vgrd10m'][i,:,:].flatten().filled().tolist() )

    uComp = np.array(ugrd10m)
    vComp = np.array(vgrd10m)
    Mag = round_floats(np.sqrt(uComp*uComp+vComp*vComp).tolist()) #magnitude of vector
    # Angle = round_floats ((np.arctan2(-uComp,-vComp) * 180 / np.pi).tolist())#calculate angle of vector. (-uComp,-vComp) 0deg = north to south, 90deg = east to west. (vComp,uComp) 0deg = west to east, 90deg = south to north.
    # for i, angle in enumerate(Angle):
    #      Angle[i] = angle if angle>=0 else angle+360

    # lon_array = ds.variables['lon'][:].tolist()
    # lat_array = np.flip(ds.variables['lat'][:]).tolist()

    newdata = []
    img = Image.new('RGBA', (nx, ny), (0, 0, 0, 0))
    umin = min(ugrd10m)
    umax = max(ugrd10m)
    vmin = min(vgrd10m)
    vmax = max(vgrd10m)
    div = 255
    for i, val in enumerate(ugrd10m):
        uvalue = (val-umin)/(umax-umin)
        vvalue = (vgrd10m[i]-vmin)/(vmax-vmin)
        ones_ugrd = (div*uvalue)//1
        rem_ugrd = ((div*uvalue-ones_ugrd)*div)//1
        ones_vgrd = (div*vvalue)//1
        rem_vgrd = ((div*vvalue-ones_vgrd)*div)//1
        newdata.append((int(ones_ugrd),int(rem_ugrd),int(ones_vgrd),int(rem_vgrd)))
    png_string = './exports/png/'+YYYYMMDD+'_'+HH+'_'+RES.split("_")[0]+'.png'
    img.putdata(newdata)
    img.save(png_string, "PNG")

    view_data = []
    view_img = Image.new('RGBA', (nx,ny), (0,0,0,0))
    mmax= max(Mag)
    for val in Mag:
        r = 255*val/mmax
        g = 0
        b = 0
        a = 255
        view_data.append((int(r),g,b,a))
    view_string = './exports/pretty/'+YYYYMMDD+'_'+HH+'_'+RES.split("_")[0]+'.png'
    view_img.putdata(view_data)
    view_img.save(view_string,"PNG")

    #create json file from data
    header = {
        "RES":RES,
        "YYYYMMDD":YYYYMMDD,
        "HH":HH,
        "decoding":{
            "umin":umin,
            "umax":umax,
            "vmin":vmin,
            "vmax":vmax,
            "div":div
        },
        "lon":{
            "grads_dim":"x",
            "grads_size":nx,
            "units":"degrees_east",
            "maximum":lon2,
            "minimum":lon1,
            "resolution":dx,
        },
        "lat":{
            "grads_dim":"x",
            "grads_size":ny,
            "units":"degrees_north",
            "maximum":lat1,
            "minimum":lat2,
            "resolution":dy,
        },
    }
    json_string = "./exports/json/"+YYYYMMDD+'_'+HH+'_'+RES.split("_")[0]+'.json'
    with open(json_string, 'w') as json_file:
        json.dump({"header":header}, json_file)
        json_file.close()

    #plotting (removable for production)
    # longCord, latCord = np.meshgrid(lon_array,lat_array)
    # qq=plt.quiver(longCord, latCord, uComp, vComp, M, cmap=plt.cm.viridis)
    # plt.colorbar(qq, cmap=plt.cm.viridis)
    # plt.title("World Wind Map")
    # plt.xlabel("Longitude")
    # plt.ylabel("Latitude")
    # plt.show()

#print program run duration (removable for production)
end = time()
print('Duration:',end-start)
