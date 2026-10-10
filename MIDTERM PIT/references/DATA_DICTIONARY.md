# Data Dictionary

## `standard_assignment_locations.csv`
Exact Standard/PPT input.

Columns: vertex, name, latitude, longitude, role, data_status, Google Maps URL, source note.

`data_status = FROZEN_PPT_DATA` is intentional: the file clearly distinguishes the reproducible teaching coordinates from live road data.

## `psgc_cdo_barangays_2025.csv`
Official CDO administrative catalog based on the Philippine Statistics Authority PSGC page. Contains all 80 official barangays.

## `cdo_master_catalog.csv`
Interactive selection catalog: 80 barangays plus 21 selected landmarks/facilities. The large catalog provides citywide choice; one Brute Force run uses only a manageable selected subset.
