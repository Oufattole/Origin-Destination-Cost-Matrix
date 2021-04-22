import arcpy
from arcpy import env
import os

arcpy.CheckOutExtension('Network')
arcpy.CheckOutExtension("Highways")
"""
Directory Information ***EDIT FOR YOUR CONFIGURATION***
"""
env.workspace = "C:\data" # directory with your "large roads speeds" and "tracts centroids" subdirectories
env.overwriteOutput = True

centroid_folder = 'tracts centroids' #relative path from env.workspace path
network_dataset_shp = 'large roads speeds\large_roads_speeds.shp' #relative path from env.workspace path
network_dataset_nd = 'large roads speeds\large_roads_speeds_ND.nd' #relative path from env.workspace path
"""
In command prompt run 'Run  C:\Python27\ArcGIS10.8\python.exe "C:\Data\python code (OD)\od_script.py"'
The last directory should be changed to this python script's directory
"""
"""
Setup Indexes Helper Functions
"""
def verify_network_dataset_shp_indices(network_dataset_shp):
    '''
    Return True if Network Dataset has the spatial and attribute Indices added
    '''
    #helper functions
    def check_2_fields(fields):
        if len(fields) != 2:
            return False
        for field in fields:
            if len(field) != 1:
                return False
    def extract(fields):
        return [fields[0][0], fields[1][0]]
    indexes = arcpy.ListIndexes(network_dataset_shp)
    fields =  [index.fields for index in indexes]
    def check_fields(spatial_field, attribute_field):
        if spatial_field.name == "Shape" and spatial_field.type == "Geometry":
            if attribute_field.name == "seconds" and attribute_field.type == "Double":
                return True
        return False
    
    #check index fields are the correct format
    if check_2_fields(fields) == False:
        return False
    fields = extract(fields)
    return check_fields(fields[0], fields[1]) or check_fields(fields[1], fields[0])

def verify_centroid_indices(centroid):
    '''
    Return True if centroid has the spatial Index added
    '''
    indexes = arcpy.ListIndexes(centroid)
    if len(indexes) != 1:
        return False
    field = indexes[0].fields[0]
    return field.name == "Shape" and field.type == "Geometry"

def index_setup(network_dataset_shp, centroid):
    if not verify_network_dataset_shp_indices(network_dataset_shp):
        #ND seconds atribute spatial index
        arcpy.AddIndex_management(network_dataset_shp, "seconds")
        #ND spatial index
        arcpy.AddSpatialIndex_management(network_dataset_shp, "")
        assert(verify_network_dataset_shp_indices(network_dataset_shp))
    print("indexes successfully set for network dataset")
    if not verify_centroid_indices(centroid):
        #centroid spatial index
        arcpy.AddSpatialIndex_management(centroid, "")
        assert(verify_centroid_indices(centroid))
    print("indexes successfully set for centroid")
"""
Setup OD Inputs Helper Functions
"""
def setup_od_inputs(centroid, centroid_directory, network_dataset_nd):
    #Origins setup
    inOrigins = centroid
    inDestinations = inOrigins
    #Network Dataset setup
    inNetworkDataset = network_dataset_nd
    #Output setup
    out_folder_path = centroid_directory
    out_name = "od_output.gdb"
    arcpy.CreateFileGDB_management(out_folder_path, out_name)
    outGeodatabase = os.path.join(out_folder_path, out_name)
    return inOrigins, inDestinations, inNetworkDataset, outGeodatabase
"""
Generate OD Matrix in Geodatabase
"""
def generate_od_matrix(inOrigins, inDestinations, inNetworkDataset, outGeodatabase):
    arcpy.na.GenerateOriginDestinationCostMatrix(inOrigins, inDestinations, inNetworkDataset, outGeodatabase,
                                                  Origin_Destination_Line_Shape='NO_LINES', Save_Output_Network_Analysis_Layer = "NO_SAVE_OUTPUT_LAYER",
                                                Maximum_Snap_Tolerance = 25000)
    #"NO_LINES" boosts performance
    #the output is stored in output.gdb so we don't need the network_analysis_layer.
    print 'completed od matrix successfully'
"""
Convert OD Matrix From Geodatabase to CSV
"""
def output_csv(centroid_directory, outGeodatabase):
    inTable = os.path.join(outGeodatabase, "ODLines")
    outLocation = centroid_directory
    outTable = "od_output.csv"
    arcpy.TableToTable_conversion(inTable, outLocation, outTable)
"""
Find Centroid Files Helper
"""
def find_centroid(centroid_folder):
    for directory, _, files in os.walk(os.path.join(env.workspace, centroid_folder)):
        for file in files:
            if ".shp" == file[-4:]:
                centroid_directory = directory
                centroid_shp = os.path.join(directory, file)
                print(centroid_shp)
                yield centroid_directory, centroid_shp
"""
Find Total Centroids Helper
"""
def calculate_total_centroids():
    total_centroids = 0
    for _, _ in find_centroid(centroid_folder):
        total_centroids+=1
    print 'total_centroids: ' + str(total_centroids)
    return total_centroids
"""
Run The Script
"""
if __name__ == "__main__":
    total_centroids = calculate_total_centroids()
    count = 0
    for centroid_directory, centroid_shp in find_centroid(centroid_folder):
        index_setup(network_dataset_shp, centroid_shp)
        inOrigins, inDestinations, inNetworkDataset, outGeodatabase = setup_od_inputs(centroid_shp, centroid_directory, network_dataset_nd)
        generate_od_matrix(inOrigins, inDestinations, inNetworkDataset, outGeodatabase) # 16 minutes
        output_csv(centroid_directory, outGeodatabase) # 2 minutes
        count+=1
        print "completed " + str(count) + " out of " + str(total_centroids)