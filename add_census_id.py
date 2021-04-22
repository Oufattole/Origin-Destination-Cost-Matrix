import arcpy
from arcpy import env
import os
import pandas as pd
import od_script

env.workspace = od_script.env.workspace #"C:\data" # directory with your "large roads speeds" and "tracts centroids" subdirectories
env.overwriteOutput = True

# Run with command:
# C:\Python27\ArcGIS10.8\python.exe "C:\Data\python code (OD)\add_census_id.py"

centroid_folder = od_script.centroid_folder

def find_centroids_with_od_output(centroid_folder):
    for directory, _, files in os.walk(os.path.join(env.workspace, centroid_folder)):
        for file in files:
            if "od_output.csv" in files:
                if ".shp" == file[-4:]:
                    centroid_directory = directory
                    centroid_shp = os.path.join(directory, file)
                    yield centroid_directory, centroid_shp
def count_total():
    count = 0
    for each,_ in find_centroids_with_od_output(centroid_folder):
        count += 1
    return count

def add_census_id_to_od_matrix(centroid_folder):
    total = str(count_total())
    print("There are " + total + " matrices to update")
    count = 0
    for centroid_directory, centroid_shp in find_centroids_with_od_output(centroid_folder):
        output_df = pd.read_csv(os.path.join(centroid_directory, "od_output.csv"))
        rows=arcpy.SearchCursor(centroid_shp)
        ids = []
        #retrieve all the census IDs
        for row in rows:
            OID = row.getValue("FID")
            census_id=row.getValue("geo2010")
            ids.append([OID, census_id])
        centroid_df =  pd.DataFrame(data=ids, columns = ["OID","census_id"])
        #create origin and destination matrix to merge with output
        origins = centroid_df.rename(columns={"census_id":"census_origin", "OID":"OriginOID"}).astype("int64")
        destinations = centroid_df.rename(columns={"census_id":"census_destination", "OID":"DestinationOID"}).astype("int64")
        #merge origin and destination census_ids with OD_matrix
        result = output_df.merge(origins, how="left").merge(destinations, how="left")
        #store new csv
        output_file = os.path.join(centroid_directory, "OD_matrix.csv")
        output_columns = ["Total_Time", "Total_Distance", "OriginOID", "DestinationOID", "census_origin", "census_destination"]
        result[output_columns].to_csv(output_file)
        count+= 1
        print(str(count) + "/" + total + " complete")

if __name__ == "__main__":
    add_census_id_to_od_matrix(centroid_folder)