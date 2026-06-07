import os
import glob
import netCDF4 as nc
import numpy as np
import scipy.io as sio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

L6_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/PyFluxPro/OzFlux-footprint/output_L6new"

def process_site(nc_file, out_mat_file):
    try:
        d = nc.Dataset(nc_file, 'r')
    except Exception as e:
        print(f"Error opening {nc_file}: {e}")
        return False
        
    if 'sumphi' not in d.variables:
        print(f"  No 'sumphi' found in {nc_file}")
        return False
        
    phi = d.variables['sumphi'][:]
    lon = d.variables['longitude'][:]
    lat = d.variables['latitude'][:]
    
    # sumphi is typically (time, longitude, latitude)
    if phi.ndim == 3:
        for t in range(phi.shape[0]):
            phi_2d = phi[t,:,:]
            if not np.all(phi_2d == 0) and not np.all(np.ma.getmaskarray(phi_2d)):
                break
        else:
            print(f"  No valid footprint data in {nc_file}")
            return False
    else:
        phi_2d = phi
        
    if isinstance(phi_2d, np.ma.MaskedArray):
        phi_2d = phi_2d.filled(0)
        
    # Get tower coordinates (center of grid)
    lon0 = lon[len(lon)//2]
    lat0 = lat[len(lat)//2]
    
    levels = [0.5, 0.6, 0.7, 0.8]
    contours_out = []
    
    max_len = 0
    
    # phi_2d is (len(lon), len(lat)). For matplotlib contour, Z must be (len(y), len(x)).
    # So we transpose phi_2d to (len(lat), len(lon))
    Z = phi_2d.T
    
    for lev in levels:
        fig, ax = plt.subplots()
        cs = ax.contour(lon, lat, Z, levels=[lev])
        
        c_xy = np.array([])
        for collection in cs.collections:
            paths = collection.get_paths()
            if paths:
                # Select the longest contiguous path (the main boundary)
                longest_path = max(paths, key=lambda p: len(p.vertices))
                
                # vertices are in (lon, lat)
                verts = longest_path.vertices
                c_lon = verts[:, 0]
                c_lat = verts[:, 1]
                
                # Convert back to local Cartesian (meters)
                x_m = (c_lon - lon0) * np.cos(lat0 * np.pi / 180.0) * 111320.0
                y_m = (c_lat - lat0) * 111320.0
                
                c_xy = np.column_stack((x_m, y_m))
                break
                
        plt.close(fig)
        contours_out.append(c_xy)
        if len(c_xy) > max_len:
            max_len = len(c_xy)
            
    if max_len == 0:
        print(f"  No contours found in {nc_file}")
        return False
        
    # Structure into an Nx8 matrix for MATLAB
    output_mat = np.full((max_len, 8), np.nan)
    
    for i, c in enumerate(contours_out):
        if len(c) > 0:
            output_mat[:len(c), 2*i:2*i+2] = c
            
    # Save the file
    os.makedirs(os.path.dirname(out_mat_file), exist_ok=True)
    sio.savemat(out_mat_file, {'output': output_mat})
    print(f"  SUCCESS: Exported {out_mat_file}")
    return True

if __name__ == '__main__':
    sites = sorted(os.listdir(L6_DIR))
    print("Starting MATLAB .mat footprint extraction...")
    
    count = 0
    # Directory where the _footprint.nc files are actually saved
    ROOT_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/PyFluxPro/OzFlux-footprint"
    
    for site in sites:
        site_dir = os.path.join(L6_DIR, site)
        if not os.path.isdir(site_dir) or site == 'controlfiles':
            continue
            
        nc_file = os.path.join(ROOT_DIR, f"{site}_footprint.nc")
        if not os.path.exists(nc_file):
            continue
            
        out_mat = os.path.join(site_dir, 'footprint_mat', f"{site}_fp.mat")
        print(f"Processing {nc_file}...")
        if process_site(nc_file, out_mat):
            count += 1
            
    print(f"Finished extracting footprints to .mat files. Total files successfully converted: {count}")
