# -*- coding: utf-8 -*-
"""
@author: Giovanny Moncayo
"""
# =============================================================================
# DATA PROCESSING SCRIPT
# Script to compute Activity Point Locations (APL)
# Clone the code from Github 
# git@github.com:GmoncayoCodes/ActivityPointLocationGenerator.git 
# This script is automatically executed from script 01JSON-Transformation.py
#
# Pre-requisites to run the script separately: 
#   1. Check or create folders in your python directory: code, dataTransform, dataFinal, log 
#   2. Copy script 02APL-Processing.py in the code directory
#   3. Copy CSV file in the dataTransform directory
#   4. Set the folder code as your working directory
#   5. Run script
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
import numpy as np
import skmob as skm
from skmob.preprocessing import filtering as skm_filter
from skmob.preprocessing import compression as skm_compression
from skmob.measures.individual import distance_straight_line as skm_distance
from skmob.preprocessing import detection as skm_detection
from skmob.preprocessing import clustering as skm_clustering

# =============================================================================
# UTILITY PACKAGE IMPORTS
# =============================================================================
import datetime as dt
import logging, os, platform, sys

# =============================================================================
# # CONSTANTS DEFINITION
# =============================================================================
# Minimum number observations to process APL computation
MIN_NUMBER_OBSERVATIONS = 100

# Data zone limits (Ecuador)
TOP_LAT =  1.426548
LOW_LAT = -5.012636
LEFT_LON = -81.011268
RIGHT_LON = -75.199536

# COVID start date
COVID_DATE = '2020-03-01'

# COVID Restriction Levels 
# First Period - Full Restrictions(Level 3)
CRL_P1_START = '2020-03-01'
CRL_P1_END = '2020-06-01'
# Second Period - Middle restrictions(Level 2)
CRL_P2_START = '2020-06-01'
CRL_P2_END = '2020-07-01'
# Third Period - Low restrictions(Level 1)
CRL_P3_START = '2020-07-01'
CRL_P3_END = '2020-12-01'
# Fourth Period - Middle restrictions(Level 2)
CRL_P4_START = '2020-12-01'
CRL_P4_END = '2021-06-01'

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
        msg = "*** START PROCESSING STAGE ***"
        print(msg)
        logging.debug(msg)

        # =============================================================================
        # Algorithm to Process CSV files and Compute APL
        # =============================================================================
        try:
            # Validate dataTransform directory is not empty
            if(os.listdir(urlDataTransform)):
                # Reference first CSV file in dataJSON directory
                csvFileName = os.listdir(urlDataTransform)[0]
                msg = 'Processing File: {}'.format(csvFileName) 
                print(msg)
                logging.info(msg)
                # Validate CSV file extension
                if(csvFileName.endswith('.csv')):
                    idFile = csvFileName[0:len(csvFileName)-4]
                    urlFile = "{}\\{}".format(urlDataTransform, csvFileName)
                    # Read CSV file and store in a Dataframe
                    dfSource = pd.read_csv (urlFile)
                    # Validate CSV file has data
                    if(not dfSource.empty):
                        # Validate columns datetime, latitude and longitude exists in CSV structure
                        if(('datetime' in dfSource.columns) and ('latitude' in dfSource.columns) and ('longitude' in dfSource.columns)):
                            df = dfSource
                            # Zone filter
                            df = df[df.latitude.between(LOW_LAT, TOP_LAT)]
                            df = df[df.longitude.between(LEFT_LON, RIGHT_LON)]
                            df['idFile'] = idFile
                            df['covidStatus'] = np.where(df.datetime < COVID_DATE, 0, 1)
                            df['restrictionLevel'] = np.where(df.datetime < COVID_DATE, 0, 
                                   (np.where(df.datetime.between(CRL_P1_START, CRL_P1_END),3,
                                             np.where(df.datetime.between(CRL_P2_START, CRL_P2_END),2,
                                                      np.where(df.datetime.between(CRL_P3_START, CRL_P3_END),1,
                                                               np.where(df.datetime.between(CRL_P4_START, CRL_P4_END),2,1))))))
                            df = df[['idFile','datetime', 'latitude', 'longitude','covidStatus','restrictionLevel']]
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
                                # FIRST DATASET GPSTrackingData
                                # =============================================================================
                                dfGPSTracking = dfSkmob
                                dfGPSTracking = dfGPSTracking.rename(columns = {'uid': 'idFile', 'lng': 'lon'})
                                dfGPSTracking = dfGPSTracking[['idFile','datetime', 'lat', 'lon','covidStatus','restrictionLevel']]
                                # =============================================================================
                                # Export Data before Anonymisation
                                # ============================================================================= 
                                exportFile = 'GPSTrackingData_'
                                dfGPSTracking.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                                # =============================================================================
                                # GRAVITY ANONYMISATION
                                # Data Anonymisation is based on Gravity Point
                                # Gravity point (GP) is the mean latitute and longitude of all dataset
                                # Anonimyzation consist to move GP to the center of the world (0,0)
                                # =============================================================================
                                # Gravity point
                                lonGravityPointAnonymization = dfGPSTracking['lon'].mean()
                                latGravityPointAnonymization = dfGPSTracking['lat'].mean()
                                # Anonymise Data
                                dfGPSTracking['lon'] = dfGPSTracking['lon'] - lonGravityPointAnonymization
                                dfGPSTracking['lat'] = dfGPSTracking['lat'] - latGravityPointAnonymization
                                # =============================================================================
                                # Export Data after Anonymisation
                                # =============================================================================
                                exportFile = 'GPSTrackingData'
                                dfGPSTracking.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                                
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
                                
                                # =============================================================================
                                # ACTIVITY POINT LOCATIONS
                                # Detect the stops (APL) for each individual in a TrajDataFrame (each Trip in a Trajectory). 
                                # APL is detected when the individual spends at least MINUTES_FOR_A_STOP minutes (5 minutes)
                                # within a distance `stop_radius_factor * spatial_radius` km from a given trajectory point. 
                                # The stop's coordinates are the median latitude and longitude values of the points found 
                                # within the specified distance
                                # =============================================================================
                                dfTrajTripsStops = pd.DataFrame()
                                arrayWeeks = dfTrajTrips.idWeek.unique()
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
                                
                                # =============================================================================
                                # SECOND DATASET APLData
                                # =============================================================================
                                dfAPL = dfTrajTripsStopsClusters
                                
                                # =============================================================================
                                # THIRD DATASET SummaryData
                                # =============================================================================
                                # Stops and Cluster Summary
                                dfTmp = dfAPL.rename(columns = {'datetime': 'timestamp'})
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
                                
                                # Trips Summary
                                dfTrajTripsSummary = pd.DataFrame(columns=['idFile', 'idWeek', 'numWeek', 'idTrip', 'tripTimeMin', 'tripLenKm', 'GPSPoints', 'covidStatus', 'restrictionLevel'])
                                arrayWeeks = dfTrajTrips.idWeek.unique()
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
                                        covidStatus = dfEachTrip.at[0,'covidStatus']
                                        restrictionLevel = dfEachTrip.at[0,'restrictionLevel']
                                        tripSerie = {'idFile':tripFile, 'idWeek':tripIdWeek, 'numWeek':tripNumWeek, 'idTrip':tripIdTrip, 'tripTimeMin':tripTimeMin, 'tripLenKm':tripLenKm, 'GPSPoints':gpsPoints, 'covidStatus':covidStatus, 'restrictionLevel':restrictionLevel}
                                        dfTrajTripsSummary = dfTrajTripsSummary.append(tripSerie,ignore_index=True) 
                                
                                # Join Summary Data
                                dfSummary = pd.merge(dfTrajTripsSummary, dfStopClusterSummary, on=['idFile','idWeek','numWeek','idTrip'], how='outer')
                                
                                # =============================================================================
                                # Export Data before Anonymisation
                                # =============================================================================
                                dfAPL = dfAPL.rename(columns = {'uid': 'idFile', 'lng':'lon'})
                                dfAPL = dfAPL[['idFile', 'idWeek', 'idTrip', 'datetime','lat', 'lon', 'cluster', 'covidStatus', 'restrictionLevel']]
                                exportFile = 'APLData_'
                                dfAPL.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                                # =============================================================================
                                # CLUSTER ANONYMISATION
                                # Data Anonymisation is based on Clusters identification
                                # Most Visited Place (MVP) is Cluster 0
                                # Anonimyzation consist to translate MVP to the center of the world (0,0)
                                # =============================================================================
                                # Cluster point
                                dfReferencePoint = dfAPL[dfAPL['cluster']==0]
                                lonClusterAnonymization = dfReferencePoint['lon'].mean()
                                latClusterAnonymization = dfReferencePoint['lat'].mean()
                                # Anonymise APL Dataframe
                                dfAPL['lon'] = dfAPL['lon'] - lonClusterAnonymization
                                dfAPL['lat'] = dfAPL['lat'] - latClusterAnonymization
                                # =============================================================================
                                # Export Data after Anonymisation
                                # =============================================================================
                                exportFile = 'APLData'
                                dfAPL.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                                # =============================================================================
                                # Export Summary Data
                                # =============================================================================
                                dfSummary = dfSummary[['idFile', 'idWeek', 'idTrip', 'GPSPoints', 'APLs', 'clusters', 'covidStatus', 'restrictionLevel']]
                                exportFile = 'SummaryData'
                                dfSummary.to_csv(urlDataFinal + exportFile + '.csv', header=True, index = False)
                                msg = "Computation succed!! {} contains {} APL".format(csvFileName, len(dfAPL))
                                print(msg)
                                logging.info(msg)
                            else:
                              msg = "File {} has few observations: {}".format(csvFileName, len(df))
                              raise RuntimeError(msg)
                        else:
                            msg = 'No columns datetime, latitude or longitude in CSV File'
                            raise RuntimeError(msg)
                    else:
                        msg = 'Empty JSON file'
                        raise RuntimeError(msg)
                else:
                    msg = 'Wrong CSV file extension ({})'.format(csvFileName)
                    raise RuntimeError(msg)
            else:
                msg = 'No File to process. Check your dataTransform directory'
                raise FileNotFoundError(msg)
            
            msg = "*** END PROCESSING STAGE ***"
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