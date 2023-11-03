#!/usr/bin/python3

from shapely.geometry import Polygon
import geopandas


continents = [
    {'name': 'Africa', 'osmUrl': 'https://download.geofabrik.de/africa-latest.osm.pbf'},
    {'name': 'Asia', 'osmUrl': 'https://download.geofabrik.de/asia-latest.osm.pbf'},
    {'name': 'Australia Oceanica', 'osmUrl': 'https://download.geofabrik.de/australia-oceania-latest.osm.pbf'},
    {'name': 'Europe', 'osmUrl': 'https://download.geofabrik.de/europe-latest.osm.pbf'},
    {'name': 'North America', 'osmUrl': 'https://download.geofabrik.de/north-america-latest.osm.pbf'},
    {'name': 'South America', 'osmUrl': 'https://download.geofabrik.de/south-america-latest.osm.pbf'}
]

# Bounding boxes: long_min, lat_min, long_max, lat_max

regions = [
    {'continent': 'Africa', 'name': 'Botswana', 'bbox': [19.98745, -26.91539, 29.38549, -17.76871], 'country': 'Botswana'},
    {'continent': 'Africa', 'name': 'Canary Islands', 'bbox': [-18.92352, 26.36117, -12.47875, 30.25648], 'country': 'Spain'},
    {'continent': 'Africa', 'name': 'Kenya', 'bbox': [33.8679, -4.816276, 41.97685, 4.629931], 'country': 'Kenya'},
    {'continent': 'Africa', 'name': 'Madagascar', 'bbox': [42.30124, -26.5823, 51.14843, -11.36225], 'country': 'Madagascar'},
    {'continent': 'Africa', 'name': 'Mauritius', 'bbox': [53.54727, -22.2411, 64.54151, -9.183617], 'country': 'Mauritius'},
    {'continent': 'Africa', 'name': 'Namibia', 'bbox': [9.784615, -30.07236, 25.29929, -16.91682], 'country': 'Namibia'},
    {'continent': 'Africa', 'name': 'South Africa', 'bbox': [15.99606, -47.58493, 39.24259, -22.11736], 'country': 'South Africa'},

    {'continent': 'Asia', 'name': 'Bahrain', 'bbox': [50.2597, 25.5325, 50.9381, 26.6941], 'country': 'Bahrain'},
    {'continent': 'Asia', 'name': 'Japan', 'bbox': [122.5607, 21.20992, 153.8901, 45.80245], 'country': 'Japan'},
    {'continent': 'Asia', 'name': 'Laos', 'bbox': [100.115987583, 13.88109101, 107.564525181, 22.4647531194], 'country': 'Laos'},
    {'continent': 'Asia', 'name': 'Nepal', 'bbox': [80.02361, 26.31982, 88.22574, 30.47746], 'country': 'Nepal'},
    {'continent': 'Asia', 'name': 'Qatar', 'bbox': [50.554, 24.467, 52.646, 26.446], 'country': 'Qatar'},
    {'continent': 'Asia', 'name': 'Sri Lanka', 'bbox': [79.16416, 5.621275, 82.64612, 10.07153], 'country': 'Sri Lanka'},
    {'continent': 'Asia', 'name': 'United Arab Emirates', 'bbox': [51.394, 22.594, 56.635, 26.155], 'country': 'United Arab Emirates'},

    {'continent': 'Australia Oceanica', 'name': 'Australia', 'bbox': [109.9694, -45.95665, 169.0016, -8.937109], 'country': 'Australia'},
    {'continent': 'Australia Oceanica', 'name': 'New Zealand', 'bbox': [162.096, -48.77, 179.8167, -32.667], 'country': 'New Zealand'},
    {'continent': 'Australia Oceanica', 'name': 'Vanuatu', 'bbox': [166.5415638, -20.254446647, 170.23828392, -13.071706876], 'country': 'Vanuatu'},

    {'continent': 'Europe', 'name': 'Albania', 'bbox': [19.13709, 39.59972, 21.06846, 42.66562], 'country': 'Albania'},
    {'continent': 'Europe', 'name': 'Austria', 'bbox': [9.52678, 46.36851, 17.16273, 49.02403], 'country': 'Austria'},
    {'continent': 'Europe', 'name': 'Belgium', 'bbox': [2.340725, 49.49196, 6.411619, 51.59839], 'country': 'Belgium'},
    {'continent': 'Europe', 'name': 'Bosnia and Herzegovina', 'bbox': [15.73639, 42.56583, 19.62176, 45.26595], 'country': 'Bosnia and Herzegovina'},
    {'continent': 'Europe', 'name': 'Bulgaria', 'bbox': [22.34875, 41.22681, 29.18819, 44.22477], 'country': 'Bulgaria'},
    {'continent': 'Europe', 'name': 'Croatia', 'bbox': [13.08916, 42.16483, 19.45911, 46.56498], 'country': 'Croatia'},
    {'continent': 'Europe', 'name': 'Cyprus', 'bbox': [31.95244, 34.23374, 34.96147, 36.00323], 'country': 'Cyprus'},
    {'continent': 'Europe', 'name': 'Czech Republic', 'bbox': [12.08477, 48.54292, 18.86321, 51.06426], 'country': 'Czechia'},
    {'continent': 'Europe', 'name': 'Denmark', 'bbox': [7.7011, 54.44065, 15.65449, 58.06239], 'country': 'Denmark'},
    {'continent': 'Europe', 'name': 'Estonia', 'bbox': [20.85166, 57.49764, 28.21426, 59.99705], 'country': 'Estonia'},
    {'continent': 'Europe', 'name': 'Finland', 'bbox': [19.02427, 59.28783, 31.60089, 70.09959], 'country': 'Finland'},
    {'continent': 'Europe', 'name': 'France', 'bbox': [-6.3, 41.27688, 9.8, 51.32937], 'country': 'France'},
    {'continent': 'Europe', 'name': 'Germany', 'bbox': [5.864417, 47.26543, 15.05078, 55.14777], 'country': 'Germany'},
    {'continent': 'Europe', 'name': 'Great Britain', 'bbox': [-9.408655, 49.00443, 2.25, 61.13564], 'country': 'United Kingdom'},
    {'continent': 'Europe', 'name': 'Greece', 'bbox': [19.15881, 34.59111, 29.65683, 41.74954], 'country': 'Greece'},
    {'continent': 'Europe', 'name': 'Hungary', 'bbox': [16.11262, 45.73218, 22.90201, 48.58766], 'country': 'Hungary'},
    {'continent': 'Europe', 'name': 'Iceland', 'bbox': [-25.7, 62.84553, -12.41708, 67.50085], 'country': 'Iceland'},
    {'continent': 'Europe', 'name': 'Ireland', 'bbox': [-12.57937, 49.60002, -5.059265, 56.64261], 'country': 'Ireland'},
    {'continent': 'Europe', 'name': 'Italy', 'bbox': [6.602696, 35.07638, 19.12499, 47.10169], 'country': 'Italy'},
    {'continent': 'Europe', 'name': 'Latvia', 'bbox': [20.79407, 55.66886, 28.24116, 58.08231], 'country': 'Latvia'},
    {'continent': 'Europe', 'name': 'Liechtenstein', 'bbox': [9.471078, 47.04774, 9.636217, 47.27128], 'country': 'Liechtenstein'},
    {'continent': 'Europe', 'name': 'Lithuania', 'bbox': [20.63822, 53.89605, 26.83873, 56.45106], 'country': 'Lithuania'},
    {'continent': 'Europe', 'name': 'Luxembourg', 'bbox': [5.733033, 49.44553, 6.532249, 50.18496], 'country': 'Luxembourg'},
    {'continent': 'Europe', 'name': 'Malta', 'bbox': [14.0988, 35.77776, 14.61755, 36.11909], 'country': 'Malta'},
    {'continent': 'Europe', 'name': 'Moldova', 'bbox': [26.61889, 45.4689, 30.16374, 48.49017], 'country': 'Moldova'},
    {'continent': 'Europe', 'name': 'Montenegro', 'bbox': [18.17282, 41.61621, 20.36638, 43.55504], 'country': 'Montenegro'},
    {'continent': 'Europe', 'name': 'Netherlands', 'bbox': [2.992192, 50.74753, 7.230455, 54.01786], 'country': 'Netherlands'},
    {'continent': 'Europe', 'name': 'Northern Ireland', 'bbox': [-8.37516, 53.88797, -5.15067, 55.43195], 'country': 'United Kingdom'},
    {'continent': 'Europe', 'name': 'Norway', 'bbox': [-11.36801, 57.55323, 35.52711, 81.05195], 'country': 'Norway'},
    {'continent': 'Europe', 'name': 'Poland', 'bbox': [14.0998, 48.98568, 24.16522, 55.09949], 'country': 'Poland'},
    {'continent': 'Europe', 'name': 'Portugal', 'bbox': [-31.5, 32.0, -6.179513, 42.1639], 'country': 'Portugal'},
    {'continent': 'Europe', 'name': 'Romania', 'bbox': [20.24181, 43.59703, 30.27896, 48.28633], 'country': 'Romania'},
    {'continent': 'Europe', 'name': 'Serbia', 'bbox': [18.82347, 42.24909, 23.00617, 46.19125], 'country': 'Republic of Serbia'},
    {'continent': 'Europe', 'name': 'Slovakia', 'bbox': [16.8284, 47.72646, 22.57051, 49.6186], 'country': 'Slovakia'},
    {'continent': 'Europe', 'name': 'Slovenia', 'bbox': [13.36653, 45.41273, 16.61889, 46.88667], 'country': 'Slovenia'},
    {'continent': 'Europe', 'name': 'Spain', 'bbox': [-9.779014, 35.73509, 5.098525, 44.14855], 'country': 'Spain'},
    {'continent': 'Europe', 'name': 'Sweden', 'bbox': [10.54138, 55.02652, 24.22472, 69.06643], 'country': 'Sweden'},
    {'continent': 'Europe', 'name': 'Switzerland', 'bbox': [5.952882, 45.81617, 10.49584, 47.81126], 'country': 'Switzerland'},

    {'continent': 'North America', 'name': 'Canada West', 'bbox': [-141.7761, 46.41459, -88.12183, 60.00678], 'country': 'Canada'},
    {'continent': 'North America', 'name': 'Canada East', 'bbox': [-95.15965, 41.6377, -51.66101, 62.59], 'country': 'Canada'},
    {'continent': 'North America', 'name': 'Canada North', 'bbox': [-141.2389, 51.06002, -54.82473, 84.95198], 'country': 'Canada'},
    {'continent': 'North America', 'name': 'USA Midwest', 'bbox': [-104.0588, 35.98507, -80.50521, 49.40714], 'country': 'United States of America'},
    {'continent': 'North America', 'name': 'USA Northeast', 'bbox': [-80.52632, 38.77178, -66.87576, 47.48423], 'country': 'United States of America'},
    {'continent': 'North America', 'name': 'USA Pacific', 'bbox': [-179.9965, 15.98281, -129.7998, 72.98845], 'country': 'United States of America'},
    {'continent': 'North America', 'name': 'USA South', 'bbox': [-106.6494, 24.20031, -71.50981, 40.64636], 'country': 'United States of America'},
    {'continent': 'North America', 'name': 'USA West', 'bbox': [-133.0637, 31.32659, -102.041, 49.45605], 'country': 'United States of America'},

    {'continent': 'South America', 'name': 'Argentina', 'bbox': [-73.61453, -55.68296, -53.59024, -21.72575], 'country': 'Argentina'},
    {'continent': 'South America', 'name': 'Brazil', 'bbox': [-74.09056, -35.46552, -27.67249, 5.522895], 'country': 'Brazil'},
    {'continent': 'South America', 'name': 'Colombia', 'bbox': [-79.68074, -4.230484, -66.86983, 13.11676], 'country': 'Colombia'},
    {'continent': 'South America', 'name': 'Falkland Islands', 'bbox': [-63.11192, -53.38141, -56.11363, -50.35743], 'country': 'United Kingdom'}
]

print('Read country boundary file')
worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.dbf' )


def bufferedBoundary(region):
    """Returns polygons that contain a given region, with a 20km buffer around the region boundaries

    :param region: Entry of the array 'regions'

    :returns: geopandas geometry
    """

    # Get the boundary of the country
    countryGDF = worldCountryMap[worldCountryMap.SOVEREIGNT == region["country"]]
    if countryGDF.size == 0:
        print('Error in bufferedBoundary(), country is empty: ' + region["country"])
        exit(-1)

    # Intersect the boundary with the bounding box of the region
    bbox = Polygon([(region['bbox'][0],region['bbox'][1]), (region['bbox'][0],region['bbox'][3]), (region['bbox'][2],region['bbox'][3]), (region['bbox'][2],region['bbox'][1])])
    bboxSeries = geopandas.GeoSeries([bbox])
    bboxSeries.set_crs("EPSG:4326")
    countryGDF = countryGDF.intersection(bbox)

    # Compute and return buffer
    return countryGDF.to_crs(crs=3857).buffer(20000).to_crs(crs=4326)
