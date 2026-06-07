#!/usr/bin/env python3
"""
Create OWUS-compatible files from OzFlux master dataset.
This script adapts OzFlux data to match the expected format for OWUS_australia codebase.
"""

import pandas as pd
import os

def create_sel_sites():
    """Extract sel_sites.csv from ozflux_MASTER_dataset.csv"""
    print("=" * 60)
    print("Creating sel_sites.csv...")
    print("=" * 60)
    
    master_file = "sanjay data creation/master_files/ozflux_MASTER_dataset.csv"
    
    if not os.path.exists(master_file):
        print(f"ERROR: {master_file} not found!")
        return False
    
    # Load master dataset
    master = pd.read_csv(master_file)
    print(f"Loaded {len(master)} sites from master dataset")
    
    # Extract required columns for OWUS format
    required_cols = [
        "siteID", "lat", "lon", "climate", "pft_0", "pft", "IGBP",
        "soil_tex_id", "Soil_TEX", "swc_i", "Zm"
    ]
    
    # Check all columns exist
    missing = [col for col in required_cols if col not in master.columns]
    if missing:
        print(f"ERROR: Missing columns in master dataset: {missing}")
        return False
    
    # Create sel_sites
    sel_sites = master[required_cols].copy()
    
    # Save
    output_file = "sel_sites.csv"
    sel_sites.to_csv(output_file, index=False)
    print(f"✓ Created {output_file} with {len(sel_sites)} sites")
    print(f"  Columns: {', '.join(sel_sites.columns)}")
    
    return True


def fix_pft_params():
    """Rename k_xl_max to kl_max in PFT parameters file"""
    print("\n" + "=" * 60)
    print("Fixing PFT parameters column names...")
    print("=" * 60)
    
    pft_file = "sanjay data creation/master_files/selected_pft_params_refs.csv"
    
    if not os.path.exists(pft_file):
        print(f"ERROR: {pft_file} not found!")
        return False
    
    # Load PFT params
    pft_params = pd.read_csv(pft_file)
    print(f"Original columns: {', '.join(pft_params.columns)}")
    
    # Rename k_xl_max to kl_max if needed
    if 'k_xl_max' in pft_params.columns:
        pft_params.rename(columns={'k_xl_max': 'kl_max'}, inplace=True)
        
        # Save with new column name
        pft_params.to_csv(pft_file, index=False)
        print(f"✓ Renamed k_xl_max → kl_max")
        print(f"  Updated columns: {', '.join(pft_params.columns)}")
    elif 'kl_max' in pft_params.columns:
        print("✓ Column 'kl_max' already exists - no changes needed")
    else:
        print("WARNING: Neither 'k_xl_max' nor 'kl_max' found in PFT params!")
        return False
    
    return True


def create_data_management_ozflux():
    """Create a modified data_management.py for OzFlux"""
    print("\n" + "=" * 60)
    print("Creating data_management_ozflux.py...")
    print("=" * 60)
    
    # Read original file
    original_file = "data_management.py"
    if not os.path.exists(original_file):
        print(f"ERROR: {original_file} not found!")
        return False
    
    with open(original_file, 'r') as f:
        content = f.read()
    
    # Update file paths (lines 19-21)
    content = content.replace(
        "soil_params_file_RUC = '../../DATA/WUS//NLDAS_soilParams_RUC.csv'",
        "soil_params_file_RUC = 'sanjay data creation/master_files/NLDAS_soilParams_RUC.csv'"
    )
    content = content.replace(
        "pft_params = pd.read_csv( '../../DATA/WUS//selected_pft_params_refs.csv')",
        "pft_params = pd.read_csv('sanjay data creation/master_files/selected_pft_params_refs.csv')"
    )
    
    # Save modified version
    output_file = "data_management_ozflux.py"
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✓ Created {output_file}")
    print("  Updated file paths to point to OzFlux master_files directory")
    print("\n  NOTE: This file still expects FLUXNET CSV format.")
    print("  You'll need to adapt data loading functions for NetCDF format.")
    
    return True


def main():
    """Run all compatibility fixes"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  OzFlux → OWUS Compatibility Script                     ║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    success = True
    
    # Step 1: Create sel_sites.csv
    if not create_sel_sites():
        success = False
    
    # Step 2: Fix PFT parameters
    if not fix_pft_params():
        success = False
    
    # Step 3: Create modified data_management.py
    if not create_data_management_ozflux():
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL COMPATIBILITY FIXES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Review the created files:")
        print("   - sel_sites.csv")
        print("   - data_management_ozflux.py")
        print("\n2. Ensure NLDAS_soilParams_RUC.csv exists in master_files/")
        print("\n3. Adapt data loading functions to read OzFlux NetCDF files")
        print("   (This is a major refactoring - see compatibility_analysis.md)")
    else:
        print("✗ SOME FIXES FAILED - Check error messages above")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
