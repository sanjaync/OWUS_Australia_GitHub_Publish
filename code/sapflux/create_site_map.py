
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

# Output Directory
OUTPUT_DIR = 'analysis_output_final'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Site Coordinates (Decimal Degrees)
# Cow Bay: 16°14'01.6"S, 145°25'03.7"E
# 16 + 14/60 + 1.6/3600 = 16.233778
# 145 + 25/60 + 3.7/3600 = 145.417694
lat_cb = -16.2338
lon_cb = 145.4177

# Robson Creek: 17°07'01.5"S, 145°38'02.4"E (Assuming typo 70 -> 07, 380 -> 38)
# 17 + 7/60 + 1.5/3600 = 17.117083
# 145 + 38/60 + 2.4/3600 = 145.634000
lat_rc = -17.1171
lon_rc = 145.6340

# Wombat State Forest (Standard FluxNet Coords)
# Approx: 37.4222° S, 144.0944° E
lat_wom = -37.4222
lon_wom = 144.0944

# Create Plot
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Features
ax.add_feature(cfeature.LAND, facecolor='#f5f5f5')
ax.add_feature(cfeature.OCEAN, facecolor='#cbf1f5')
ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
ax.add_feature(cfeature.STATES, linestyle=':', edgecolor='gray')

# Extent (Full Australia)
ax.set_extent([110, 156, -45, -9], crs=ccrs.PlateCarree())

# Plot Sites
sites = [
    {'name': 'Cow Bay (Tropical)', 'lat': lat_cb, 'lon': lon_cb, 'color': 'red'},
    {'name': 'Robson Creek (Tropical)', 'lat': lat_rc, 'lon': lon_rc, 'color': 'orange'},
    {'name': 'Wombat State Forest (Sclerophyll)', 'lat': lat_wom, 'lon': lon_wom, 'color': 'blue'}
]

for site in sites:
    ax.plot(site['lon'], site['lat'], marker='o', color=site['color'], markersize=8, 
            transform=ccrs.PlateCarree(), markeredgecolor='black', zorder=5)
    
    # Offset text slightly
    offset_x = 0.5
    offset_y = 0
    if 'Wombat' in site['name']:
        offset_x = 0.5
        offset_y = -0.5
        
    ax.text(site['lon'] + offset_x, site['lat'] + offset_y, site['name'],
            transform=ccrs.PlateCarree(), fontsize=10, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))

# Gridlines
gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

plt.title("Sapflux Site Validation", fontsize=16, pad=10)

# Save
out_path = os.path.join(OUTPUT_DIR, "site_map.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Map saved to {out_path}")
