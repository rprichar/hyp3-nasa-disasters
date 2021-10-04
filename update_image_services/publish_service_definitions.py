# This script takes as input a geodatabase generated using the MDCS scripts
# and creates the necessary structure of mosaic datasets required for
# publishing services to ASF's Image Server.
# It then generates the draft service definition for each referenced MD,
# and stages a service definition.
#
# For each of the services to be published:
# 1. A derived mosaic dataset is generated by copying the source mosaic dataset
# 2. The overviews are removed from the source mosaic dataset
# 3. A referenced mosaic dataset is generated from the derived mosaic dataset
# 4. A draft service definition is generated from the referenced mosaic dataset
# 5. A final service definition is staged
#
# This script must be run on the input geodatabase after it has been uploaded to the server.

import arcpy
import os

# Set geodatabase to use as starting point
ingdb = ['path to the source gdb uploaded to the image server']

# Set path to ags to use for publishing the dataset
agspath = ['path to the ags file to arcgis on gis.asf.alaska.edu.ags']

# Format source, derived and referenced mosaic datasets for each service
for md in ['rgb', 'sar_comp', 'watermap_extent']:
    mdpath = ingdb + '\\' + md
    md_der = mdpath + '_derived'
    md_ref = mdpath + '_referenced'

    # Generate derived mosaic dataset from original source mosaic dataset
    arcpy.management.Copy(mdpath, md_der)
    arcpy.AddMessage('Created ' + md_der + ' from ' + mdpath)
    print('Created ' + md_der + ' from ' + mdpath)
    arcpy.management.RemoveRastersFromMosaicDataset(mdpath, "Category = 2", "NO_BOUNDARY",
                                                    "MARK_OVERVIEW_ITEMS", "DELETE_OVERVIEW_IMAGES",
                                                    "DELETE_ITEM_CACHE", "REMOVE_MOSAICDATASET_ITEMS",
                                                    "NO_CELL_SIZES")

    # Remove overviews from original source mosaic dataset
    arcpy.AddMessage('Removed overviews from ' + md + ' source mosaic dataset')
    print('Removed overviews from ' + md + ' source mosaic dataset')
    arcpy.management.CreateReferencedMosaicDataset(md_der, md_ref,
                                                   'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",'
                                                   'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
                                                   'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                                                   'PRIMEM["Greenwich",0.0],'
                                                   'UNIT["Degree",0.0174532925199433]],'
                                                   'PROJECTION["Mercator_Auxiliary_Sphere"],'
                                                   'PARAMETER["False_Easting",0.0],'
                                                   'PARAMETER["False_Northing",0.0],'
                                                   'PARAMETER["Central_Meridian",0.0],'
                                                   'PARAMETER["Standard_Parallel_1",0.0],'
                                                   'PARAMETER["Auxiliary_Sphere_Type",0.0],'
                                                   'UNIT["Meter",1.0]]',
                                                   None, '', '', None, None, "SELECT_USING_FEATURES", None, None, None,
                                                   None, "BUILD_BOUNDARY")

    # Create referenced mosaic dataset from derived mosaic dataset
    arcpy.AddMessage('Created reference mosaic dataset from ' + md_der)
    print('Created reference mosaic dataset from ' + md_der)

    # Generate draft service definition from the dataset
    dirpath = os.path.dirname(ingdb)
    tag = os.path.splitext(os.path.basename(ingdb))[0]
    if md == 'rgb':
        ds = 'RGB'
    elif md == 'sar_comp':
        ds = 'RTC'
    elif md == 'watermap_extent':
        ds = 'WM'
    else:
        ds = 'NONE'
        print('No matching dataset name')
    sd_draft = dirpath + '\\' + tag + '_' + ds + '.sdd'
    sname = 'ASF_S1_'+ds

    arcpy.AddMessage('Generating draft service definition for ' + ds + '...')
    print('Generating draft service definition for ' + ds + '...')
    arcpy.CreateImageSDDraft(md_ref, sd_draft, sname, "ARCGIS_SERVER", agspath, "FALSE")

    # Stage a service definition
    arcpy.AddMessage('Draft SD generated. Staging service definition for ' + ds + '...')
    print('Draft SD generated. Staging service definition for ' + ds + '...')
    sdd_draft = sd_draft+'raft'
    sd_stage = sd_draft[:-1]
    arcpy.server.StageService(sdd_draft, sd_stage, None)
    arcpy.AddMessage('Service definition staged for ' + ds + '.')
    print('Service definition staged for ' + ds + '.')
