
import csv
import os
import re
import subprocess
import time
import urllib.parse

# Configuration
base_dir = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
csv_file_path = os.path.join(base_dir, 'site_paths.csv')
pic_base_dir = os.path.join(base_dir, 'pic')
index_file_path = os.path.join(base_dir, 'test_index.html')
ozflux_base_url = 'http://www.ozflux.org.au/monitoringsites/'

def get_page_content(url):
    try:
        # Use wget to get content
        result = subprocess.run(['wget', '-qO-', url], capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_image(url, save_path):
    try:
        subprocess.run(['wget', '-q', '-O', save_path, url], check=True, timeout=10)
        return True
    except subprocess.CalledProcessError:
        return False


def parse_index_for_urls(index_content):
    # Map AU-XXX -> URL
    id_map = {}
    
    # Split by '</tr>' or similar block delimiters might be safer, but </a> is checking the link text.
    # The structure is usually: <strong><a href="...">Name<br />[ID]</a></strong>
    # regex findall might be better for the whole tag.
    
    # Regex to find <a href="...">...[AU-xxx]...</a>
    # We use non-greedy matching for the content.
    pattern = re.compile(r'<a\s+href="([^"]+)"[^>]*>.*?\[(AU-[A-Za-z0-9]+|NZ-[A-Za-z0-9]+)\].*?</a>', re.IGNORECASE | re.DOTALL)
    
    matches = pattern.findall(index_content)
    for href, site_id in matches:
         full_url = urllib.parse.urljoin(ozflux_base_url, href)
         id_map[site_id] = full_url
         # print(f"Mapped {site_id} -> {full_url}")

    return id_map

def main():
    # 1. Parse Index
    print("Parsing index file...")
    with open(index_file_path, 'r') as f:
        index_content = f.read()
    
    id_map = parse_index_for_urls(index_content)
    print(f"Found {len(id_map)} site maps.")

    # 2. Read CSV
    print(f"Reading {csv_file_path}...")
    sites = []
    with open(csv_file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sites.append(row)

    # 3. Process Sites
    for row in sites:
        site_id = row['siteID']
        original_site = row['original_site']
        
        if not site_id: continue
        
        print(f"Processing {site_id} ({original_site})...")
        target_dir = os.path.join(pic_base_dir, site_id)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Determine Site URL
        site_url = id_map.get(site_id)
        
        if not site_url:
            # Heuristics
            clean_name = original_site.lower().replace(' ', '')
            site_url = f"http://www.ozflux.org.au/monitoringsites/{clean_name}/index.html"
            print(f"  ID match failed, trying heuristic URL: {site_url}")
        else:
             print(f"  Found mapped URL: {site_url}")

        # Fetch Page
        page_content = get_page_content(site_url)
        if not page_content or '404 Not Found' in page_content:
             print(f"  Failed to fetch page or 404.")
             # Try another common heuristic: {site_name_lowercase} without 'pasture' or 'forest' etc?
             # No, simple fallback for now.
             continue

        # Extract Images
        img_matches = re.findall(r'<img[^>]+src="([^"]+)"', page_content)
        
        valid_images = []
        for img_rel in img_matches:
            img_lower = img_rel.lower()
            
            # Filter standard icons and logos
            # Key change: strict filtering of logo keywords
            excluded_keywords = [
                'external_link', 'pagetop', 'ozflux-banner', 'partner_organisations', 
                'tern-ncris', 'fluxnetlogo', 'logo', 'icon', 'favicon', 'map', 'footer',
                'header', 'template', 'button', 'menu'
            ]
            
            if any(keyword in img_lower for keyword in excluded_keywords):
                continue
            
            if not (img_lower.endswith('.jpg') or img_lower.endswith('.png') or img_lower.endswith('.jpeg')):
                continue
            
            # Construct full URL
            full_img_url = urllib.parse.urljoin(site_url, img_rel)
            
            # Check if we already have this URL
            if full_img_url in valid_images:
                continue
                
            valid_images.append(full_img_url)

        print(f"  Found {len(valid_images)} potential images.")
        
        # Download top 3
        count = 0
        sources_file = os.path.join(target_dir, 'sources.txt')
        
        # 'a' mode to append if we run multiple passes, but 'w' is fine here as we cleaned up.
        with open(sources_file, 'w') as src_f: 
            for img_url in valid_images:
                if count >= 3: break
                
                # Try to keep original extension
                ext = os.path.splitext(img_url)[1]
                if not ext: ext = '.jpg'
                
                fname = f"image_{count + 1}{ext}"
                save_path = os.path.join(target_dir, fname)
                
                print(f"    Downloading {img_url}...")
                if download_image(img_url, save_path):
                    # Check file size to avoid tiny blank images that passed filters
                    try:
                        size = os.path.getsize(save_path)
                        if size < 5000: # < 5KB is likely an icon or spacer
                            print(f"    Skipping small file ({size} bytes).")
                            os.remove(save_path)
                            continue
                    except OSError:
                        pass
                        
                    src_f.write(f"{fname}: {img_url}\n")
                    count += 1
                else:
                    print("    Failed to download.")

        if count == 0:
            print("  No images collected.")

if __name__ == "__main__":
    main()
