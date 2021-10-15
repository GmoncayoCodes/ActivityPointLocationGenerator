# -*- coding: utf-8 -*-
"""
@author: Giovanny Moncayo
"""
# =============================================================================
# COMPUTATION STAGE SCRIPT
# Script to compute Activity Points Location (APL) 
# Pre-requisites to run Script: 
#   Run 01JSON-Transformation.py script
#   Copy python script in code directory
#   Set folder code as your working directory
# =============================================================================

# Clean variables
from IPython import get_ipython
get_ipython().magic('reset -sf')

# =============================================================================
# PACKAGE IMPORTS
# =============================================================================
import pandas as pd
import geopandas as gpd
import movingpandas as mpd
import skmob as skm
from skmob.preprocessing import filtering as skm_filter
from skmob.preprocessing import compression as skm_compression
from skmob.measures.individual import distance_straight_line as skm_distance
from skmob.preprocessing import detection as skm_detection
from skmob.preprocessing import clustering as skm_clustering
# =============================================================================
# OTHER UTILITIES
# =============================================================================
import datetime as dt
import os, platform, logging, sys

# =============================================================================
# # CONSTANTS DEFINITION
# =============================================================================
# Minimum number observations to process APL computation
MIN_NUMBER_OBSERVATIONS = 100

# Filter (scikit-mobility)
# Filter out the trajectory points that are considered noise or outliers
# Delete a trajectory point if the speed (in km/h) from the previous point is higher than MAX_SPEED_KMH
MAX_SPEED_KMH = 200 #200 km/h

# Compression (scikit-mobility)
# Reduce the number of points in a trajectory for each individual
# The minimum distance (in km) between consecutive compressed points is MIN_SPATIAL_RADIUS_KM
MIN_SPATIAL_RADIUS_KM = 0.05 #50 meters

# Trajectories (MovingPandas)
# Create Trajectory from GeoDataFrame
# The minimum length of Trajectory is MIN_LENGTH_TRAJ_MTR 
MIN_LENGTH_TRAJ_MTR = 200 #200 meters 

# Trips (MovingPandas)
# Split trajectories into subtrajectories whenever there is a gap in the observations
# The minimum gap is MIN_TIME_TRIP_GAP_THRESHOLD_MINUTES and minimum length of trip is MIN_LENGTH_TRIP_MTR
MIN_TIME_TRIP_GAP_THRESHOLD_MINUTES = 30 #30 minutes
MIN_LENGTH_TRIP_MTR = 100 #100 meters

# Activity Point Location (scikit-mobility)
# Detect stops for each individual in a Trip. 
# A stop is detected when the individual spends at least MIN_MINUTES_FOR_A_STOP minutes within a distance MIN_STOP_RADIUS_FACTOR * MIN_SPATIAL_RADIUS_KM_STOP km 
# The stop’s coordinates are the median latitude and longitude values of the points found within the specified distance
MIN_MINUTES_FOR_A_STOP = 5 #5 Minutes
MIN_STOP_RADIUS_FACTOR = 1
MIN_SPATIAL_RADIUS_KM_STOP = 1 #1*1 = 1 km 

# Clusters (scikit-mobility)
# Cluster the stops of each individual
# Cluster correspond to visits to the same location at different times, based on spatial proximity. Minimum points are MIN_SAMPLES_CLUSTER and proximity MIN_CLUSTER_RADIUS_KM
# The clustering algorithm used is DBSCAN
MIN_SAMPLES_CLUSTER=1
MIN_CLUSTER_RADIUS_KM = 0.05 #50 meters


# =============================================================================
# Algorithm to compute APL
# =============================================================================

try:
    # Create URL access to project directories
    urlWorkingDirectory = os.getcwd()
    if urlWorkingDirectory.endswith('code') :
        # Create URL access to project directories
        urlProjectDirectory = os.path.abspath(os.path.join(urlWorkingDirectory, os.pardir))
        #urlDataTransform = urlProjectDirectory + '\\dataTransform\\'
        urlDataTransform = '{}\\dataTransform'.format(urlProjectDirectory)
        #urlDataFinal = urlProjectDirectory + '\\dataFinal\\'
        urlDataFinal = '{}\\dataFinal\\'.format(urlProjectDirectory)
        #urlLog = urlProjectDirectory + '\\log\\'
        urlLog = '{}\\log\\'.format(urlProjectDirectory)
        # Define log file
        now = str(dt.datetime.now()).replace(':', '')[0:17]
        logFile = 'log-Processing'+ now +'.log'
        if platform.platform().startswith('Windows'):
            fichero_log = os.path.join(urlLog,logFile)
        else:
            fichero_log = os.path.join(os.getenv('HOME'), logFile)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s',
                            filename = fichero_log, filemode = 'w',)
        msg = "*** START PROCESSING ***"
        print(msg)
        logging.debug(msg)

        # =============================================================================
        # Algorithm to Process CSV files and Compute APL
        # =============================================================================
        try:
            # Validate file exists in dataJSON directory
            if(len(os.listdir(urlDataTransform)) >= 1):
                # Read CSV file        
                csvFileName = os.listdir(urlDataTransform)[0]
                msg = 'Processing File: {}'.format(csvFileName) 
                print(msg)
                logging.info(msg)
                # Validate CSV file extension
                if(csvFileName.endswith('.csv')):
                    idFile = csvFileName[0:len(csvFileName)-4]
                    urlFile = "{}\\{}".format(urlDataTransform, csvFileName)
                    # Read CSV file
                    dfSource = pd.read_csv (urlFile)
                    df = dfSource
                    df['idFile'] = idFile
                    df = df[['idFile','datetime', 'latitude', 'longitude']]
                    msg = "Source Dataset contains {} records ".format(len(df))
                    print(msg)
                    logging.info(msg)
                    if len(df) >= MIN_NUMBER_OBSERVATIONS:
                        dfSkmob = skm.TrajDataFrame(df, user_id='idFile', datetime='datetime', longitude='longitude', latitude='latitude')
                        
                        # =============================================================================
                        # FILTERING
                        # Filter out all points with a speed (in km/h) from the previous point higher than 200 km/h
                        # =============================================================================
                        dfSkmob = skm_filter.filter(dfSkmob, max_speed_kmh=MAX_SPEED_KMH, include_loops=True)
                
                        # =============================================================================
                        # COMPRESSION        
                        # Compress the number of points in a trajectory for each individual in a TrajDataFrame. 
                        # All points within a radius of `spatial_radius_km` kilometers from a given initial point are 
                        # compressed into a single point that has the median coordinates of all points and 
                        # the time of the initial point. - 50m 
                        # =============================================================================
                        dfSkmob = skm_compression.compress(dfSkmob, spatial_radius_km=MIN_SPATIAL_RADIUS_KM)
                        
                        # =============================================================================
                        # TRAJECTORIES
                        # Compute weekly Trajectories
                        # Desired minimum length of trajectories 200m
                        # =============================================================================
                        dfSkmob= dfSkmob.rename(columns = {'datetime': 'timestamp'})
                        dfSkmob['t'] = pd.to_datetime(dfSkmob['timestamp'])
                        dfSkmob = dfSkmob.set_index('t').tz_localize(None)
                        dfSkmob['idWeek'] = dfSkmob.index.to_period('W')
                        dfSkmob = gpd.GeoDataFrame(dfSkmob, geometry=gpd.points_from_xy(dfSkmob.lng, dfSkmob.lat))
                        dfSkmob = dfSkmob.set_crs(epsg=4326)
                        msg = "Filter dataset contains {} records ".format(len(dfSkmob))
                        print(msg)
                        logging.info(msg)
                        msg = "Dataset covers the time between {} and {}.".format(dfSkmob.index.min(), dfSkmob.index.max())
                        print(msg)
                        logging.info(msg)
                        msg = "That's {}".format(dfSkmob.index.max() - dfSkmob.index.min())
                        print(msg)
                        logging.info(msg)      
                        dfTrajCollection = mpd.TrajectoryCollection(dfSkmob, traj_id_col='idWeek', min_length=MIN_LENGTH_TRAJ_MTR)
                        msg = "Dataset contain {} of {} weeks with trajectories".format(len(dfTrajCollection), len(dfSkmob['idWeek'].unique()))
                        print(msg)
                        logging.info(msg)
                        
                        # =============================================================================
                        # TRIPS
                        # Compute Trips in each trajectory
                        # Time gap threshold - 30 minutes
                        # Minimun distance for trips 100 mtr
                        # =============================================================================
                        dfTrajTrips = pd.DataFrame()
                        for i in range(0,len(dfTrajCollection)):
                            dfTraj = dfTrajCollection.trajectories[i]
                            dfTrajDf = dfTraj.df
                            dfTrajDf['numWeek'] = i
                            dfTripsTraj = mpd.ObservationGapSplitter(dfTraj).split(gap=dt.timedelta(minutes=MIN_TIME_TRIP_GAP_THRESHOLD_MINUTES), min_length=MIN_LENGTH_TRIP_MTR)              
                            dfTripTotal = pd.DataFrame()
                            for j in range(0,len(dfTripsTraj)):
                                dfTrip = dfTripsTraj.trajectories[j]
                                dfTripDf = dfTrip.df 
                                dfTripDf['idTrip'] = j
                                dfTripTotal = dfTripTotal.append(dfTripDf)
                            dfTrajTrips = dfTrajTrips.append(dfTripTotal)
                        
                        dfTrajTrips = dfTrajTrips.sort_index()   
                        arrayWeeks = dfTrajTrips.idWeek.unique()
                        
                        #Trips Summary
                        dfTrajTripsSummary = pd.DataFrame(columns=['idFile', 'idWeek', 'numWeek', 'idTrip', 'tripTimeMin', 'tripLenKm', 'GPSPoints'])
                        for numWeek in arrayWeeks:
                            dfConsolidado = dfTrajTrips[dfTrajTrips['idWeek'] == numWeek]
                            arrayTrips = dfConsolidado.idTrip.unique()
                            for numTrip in arrayTrips:
                                dfEachTrip = dfConsolidado[dfConsolidado['idTrip'] == numTrip]
                                t = dfEachTrip.reset_index().t
                                dfEachTrip = dfEachTrip.assign(delta_t=t.diff().values)
                                dfEachTrip['delta_t_m'] = dfEachTrip['delta_t'].dt.total_seconds()/60
                                dfEachTripTmp = skm.TrajDataFrame(dfEachTrip, latitude='lat', longitude='lng', datetime='timestamp', user_id='uid')
                                dfEachTripLen = skm_distance(dfEachTripTmp, show_progress=False)
                                dfEachTrip=dfEachTrip.reset_index()
                                tripFile = dfEachTrip.at[0,'uid']
                                tripIdWeek = dfEachTrip.loc[0]['idWeek']
                                tripNumWeek = dfEachTrip.loc[0]['numWeek']
                                tripIdTrip = dfEachTrip.loc[0]['idTrip']
                                tripTimeMin = dfEachTrip['delta_t_m'].sum()
                                tripLenKm = dfEachTripLen.at[0,'distance_straight_line']
                                gpsPoints = dfEachTrip['idTrip'].count()
                                tripSerie = {'idFile':tripFile, 'idWeek':tripIdWeek, 'numWeek':tripNumWeek, 'idTrip':tripIdTrip, 'tripTimeMin':tripTimeMin, 'tripLenKm':tripLenKm, 'GPSPoints':gpsPoints}
                                dfTrajTripsSummary = dfTrajTripsSummary.append(tripSerie,ignore_index=True) 
                        
                        # =============================================================================
                        # ACTIVITY POINT LOCATIONS
                        # Detect the stops (APL) for each individual in a TrajDataFrame (each Trip in a Trajectory). 
                        # APL is detected when the individual spends at least MINUTES_FOR_A_STOP minutes (5 minutes)
                        # within a distance `stop_radius_factor * spatial_radius` km from a given trajectory point. 
                        # The stop's coordinates are the median latitude and longitude values of the points found 
                        # within the specified distance
                        # =============================================================================
                        dfTrajTripsStops = pd.DataFrame()
                        for numWeek in arrayWeeks:
                          dfTrajTripsWeek = dfTrajTrips[dfTrajTrips['idWeek'] == numWeek]
                          arrayTrips = dfTrajTripsWeek.idTrip.unique()
                          for numTrip in arrayTrips:
                              dfTrajTripsTmp = dfTrajTripsWeek[dfTrajTripsWeek['idTrip'] == numTrip]
                              destinationTripPoint = dfTrajTripsTmp.reset_index()
                              destinationTripPoint = destinationTripPoint.iloc[-1:]
                              destinationTripPoint = destinationTripPoint.drop(['t'], axis=1)
                              destinationTripPoint = destinationTripPoint.rename(columns = {'timestamp': 'datetime'})
                              dfTrajTripsTmp = skm.TrajDataFrame(dfTrajTripsTmp, latitude='lat', longitude='lng', datetime='timestamp', user_id='uid')
                              dfTrajTripsTmp = skm_detection.stops(dfTrajTripsTmp, minutes_for_a_stop=MIN_MINUTES_FOR_A_STOP, 
                                                                   stop_radius_factor=MIN_STOP_RADIUS_FACTOR, spatial_radius_km=MIN_SPATIAL_RADIUS_KM_STOP, 
                                                                   leaving_time=False)
                              dfTrajTripsTmp = dfTrajTripsTmp.append(destinationTripPoint)
                              if(len(dfTrajTripsTmp) > 0):
                                  dfTrajTripsStops = dfTrajTripsStops.append(dfTrajTripsTmp)
                                  
                        # =============================================================================
                        # CLUSTER 
                        # Cluster APL of each individual in a TrajDataFrame. 
                        # The Cluster correspond to visit same location at different times, based on spatial proximity (50 meters)
                        # The Clustering algorithm used is DBSCAN.
                        # =============================================================================
                        dfTrajTripsStopsClusters = dfTrajTripsStops
                        try:
                            dfTrajTripsStopsClusters = skm.TrajDataFrame(dfTrajTripsStopsClusters, latitude='lat', longitude='lng', datetime='datetime', user_id='uid')
                            dfTrajTripsStopsClusters = skm_clustering.cluster(dfTrajTripsStopsClusters, cluster_radius_km=MIN_CLUSTER_RADIUS_KM, min_samples=MIN_SAMPLES_CLUSTER)       
                        except:
                            dfTrajTripsStopsClusters['cluster']=0
                            msg = 'Not possible to compute clusters'
                            print(msg)
                            logging.warning(msg)    
                        
                        dfFinal = dfTrajTripsStopsClusters
                        
                        #Stops and Cluster Summary
                        dfTmp= dfFinal.rename(columns = {'datetime': 'timestamp'})
                        dfTmp = dfTmp.sort_index()
                        arrayWeeks = dfTmp.idWeek.unique()    
                        dfStopClusterSummary = pd.DataFrame(columns=['idFile', 'idWeek', 'numWeek', 'idTrip', 'APLs', 'clusters'])
                        for numWeek in arrayWeeks:
                            dfConsolidado = dfTmp[dfTmp['idWeek'] == numWeek]
                            arrayTrips = dfConsolidado.idTrip.unique()
                            for numTrip in arrayTrips:
                                dfEachTrip = dfConsolidado[dfConsolidado['idTrip'] == numTrip]
                                dfEachTrip=dfEachTrip.reset_index()
                                tripFile = dfEachTrip.at[0,'uid']
                                tripIdWeek = dfEachTrip.loc[0]['idWeek']
                                tripNumWeek = dfEachTrip.loc[0]['numWeek']
                                tripIdTrip = dfEachTrip.loc[0]['idTrip']
                                apls = dfEachTrip['idTrip'].count()
                                clus = dfEachTrip['cluster'].nunique()
                                aplSerie = {'idFile':tripFile, 'idWeek':tripIdWeek, 'numWeek':tripNumWeek, 'idTrip':tripIdTrip, 'APLs':apls, 'clusters':clus}
                                dfStopClusterSummary = dfStopClusterSummary.append(aplSerie,ignore_index=True) 
                        
                        #Join Summary Data
                        dfFinalSummary = pd.merge(dfTrajTripsSummary, dfStopClusterSummary, on=['idFile','idWeek','numWeek','idTrip'], how='outer')
                        
                        # =============================================================================
                        # Export Data before Anonymisation
                        # =============================================================================
                        dfFinal = dfFinal.rename(columns = {'uid': 'idFile', 'lng':'lon'})
                        dfFinal = dfFinal[['idFile', 'idWeek', 'idTrip', 'datetime','lat', 'lon', 'cluster']]
                        exportFile = 'APLData_'
                        dfFinal.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfFinal.to_pickle(urlDataFinal + exportFile + '.dat')
                        
                        dfTrajTrips = dfTrajTrips.rename(columns = {'uid': 'idFile', 'timestamp':'datetime', 'lng':'lon'})
                        dfTrajTrips = dfTrajTrips[['idFile', 'idWeek', 'idTrip', 'datetime','lat', 'lon']]
                        exportFile = 'TrajectoryTripsData_'
                        dfTrajTrips.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfTrajTrips.to_pickle(urlDataFinal + exportFile + '.dat')
                        
                        dfFinalSummary = dfFinalSummary[['idFile', 'idWeek', 'idTrip', 'tripTimeMin', 'tripLenKm', 'GPSPoints', 'APLs', 'clusters']]
                        exportFile = 'TrajectoryTripsSummaryData_'
                        dfFinalSummary.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfFinalSummary.to_pickle(urlDataFinal + exportFile + '.dat')
                        
                        # =============================================================================
                        # ANONYMISATION
                        # Data Anonymisation is based on Clusters identification
                        # Most Visited Place (MVP) is Cluster 0
                        # Anonimyzation consist to MVP to the center of the world (0,0)
                        # subtracting the mean of latitudes and longitudes of Cluster 0 to all dataset
                        # =============================================================================
                        dfReferencePoint = dfFinal[dfFinal['cluster']==0]
                        lonForAnonymization = dfReferencePoint['lon'].mean()
                        latForAnonymization = dfReferencePoint['lat'].mean()
                        # Anonymise APL Dataframe
                        dfFinal['lon'] = dfFinal['lon'] - lonForAnonymization
                        dfFinal['lat'] = dfFinal['lat'] - latForAnonymization
                        # Anonymise TrajectoryTrips Dataframe
                        dfTrajTrips['lon'] = dfTrajTrips['lon'] - lonForAnonymization
                        dfTrajTrips['lat'] = dfTrajTrips['lat'] - latForAnonymization
                        
                        # =============================================================================
                        # Export Data after Anonymisation
                        # =============================================================================
                        exportFile = 'APLData'
                        dfFinal.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfFinal.to_pickle(urlDataFinal + exportFile + '.dat')
                        
                        exportFile = 'TrajectoryTripsData'
                        dfTrajTrips.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfTrajTrips.to_pickle(urlDataFinal + exportFile + '.dat')
                        
                        exportFile = 'TrajectoryTripsSummaryData'
                        dfFinalSummary.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                        dfFinalSummary.to_pickle(urlDataFinal + exportFile + '.dat')
                        msg = "Computation succed!! {} contains {} APL".format(csvFileName, len(dfFinal))
                        print(msg)
                        logging.info(msg)
                    else:
                      msg = "File {} has few observations: {}".format(csvFileName, len(df))
                      raise RuntimeError(msg) 
                else:
                    msg = 'Wrong CSV file extension ({})'.format(csvFileName)
                    raise RuntimeError(msg)
            else:
                msg = 'No File to process. Check your dataTransform directory'
                raise FileNotFoundError(msg)
            
            msg = "*** END PROCESSING ***"
            print(msg)
            logging.debug(msg)
            logging.shutdown()
        except:
            msg = '{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1])
            print(msg)
            logging.error(msg)
            logging.shutdown()
    else:
        msg = "Can't execute Script. Check your Working Directory is code directory!! Your current working directory is {}".format(urlWorkingDirectory)
        raise RuntimeError(msg)
except:
    msg = '{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1])
    print(msg)
    logging.error(msg)
    logging.shutdown()