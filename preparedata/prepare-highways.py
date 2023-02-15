import json
import math
import os

def minc(geometry):
    if "geometry" in geometry:
        geometry = geometry["geometry"]
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return coordinates
    if geometry["type"] == "Polygon":
        coordinates = coordinates[0]
    if geometry["type"] == "MultiPolygon":
        coordinates = coordinates[0][0]
    lon = min(map(lambda c: c[0], coordinates))
    lat = min(map(lambda c: c[1], coordinates))
    return [lon, lat]

def maxc(geometry):
    if "geometry" in geometry:
        geometry = geometry["geometry"]
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return coordinates
    if geometry["type"] == "Polygon":
        coordinates = coordinates[0]
    if geometry["type"] == "MultiPolygon":
        coordinates = coordinates[0][0]
    lon = max(map(lambda c: c[0], coordinates))
    lat = max(map(lambda c: c[1], coordinates))
    return [lon, lat]

directory = "brugge"  # input("Please, enter the directory to scan: ")
target_directory = "../hackerhotel/mapdata/"
debug_data = "<svg >"

if not os.path.exists(target_directory):
    os.mkdir(target_directory)

# Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed
topleft_lon = 180
topleft_lat = -90
for file in os.listdir(directory):
    if not file.endswith(".geojson"):
        continue
    with open(directory+"/"+file, "r") as f:
        parsed = json.loads(f.read())
        for feature in parsed["features"]:
            [minlon, minlat] = minc(feature['geometry'])
            [maxlon, maxlat] = maxc(feature['geometry'])
            topleft_lon = min(minlon, topleft_lon)
            topleft_lat = max(maxlat, topleft_lat)

# Zoom determines the zoom factor and thus the precision
z = 20



def lonlat_to_xy(c):
    lon = c[0]
    lat = c[1]
    n = 2.0 ** z
    xtl = (topleft_lon + 180.0) / 360.0 * n
    self_lat_rad = math.radians(topleft_lat)
    ytl = (1.0 - math.asinh(math.tan(self_lat_rad)) / math.pi) / 2.0 * n
    xarg = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    yarg = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    x = (xarg - xtl) * 265
    y = (yarg - ytl) * 265
    return [math.floor(x), math.floor(y)]



def center(geometry):
    if "geometry" in geometry:
        geometry = geometry["geometry"]
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return coordinates
    if geometry["type"] == "Polygon":
        coordinates = coordinates[0]
    lon = sum(map(lambda c: c[0], coordinates)) / len(coordinates)
    lat = sum(map(lambda c: c[1], coordinates)) / len(coordinates)
    return [lon, lat]

def createMeta(type, count,keys):
    return type+","+str(count)+","+",".join(keys)

def exportLabels(features, keys, file, x, y):
    features = list(filter(lambda:f["geometry"]["type"] != "MultiPolygon" and keys[0] in f["properties"],  features))
    
    if len(features) == 0:
        return
    file = target_directory+"/"+str(x)+"_"+str(y)+"_"+file+".points"
    data = createMeta("point", len(features), keys)+ "\n"
    for f in features:
        label = f["properties"][keys[0]]
        if label.strip() == "":
            continue
        [lon, lat ] = center(f)
        [x, y] = lonlat_to_xy([lon, lat])
        data += str(x)+","+str(y)+","
        if("level" in f["properties"]):
            data += str(f["properties"]["level"])
        else:
            data += "*"
        
        for key in keys:
            data += ","
            if key in f["properties"]:
                data += f["properties"][key]
        data += "\n"
    f = open(file, "w")
    f.write(data)
    f.close()


def exportLines(features, keys, file, x, y):
    if len(features) == 0:
        return ""
    debug_data = ""
    file = target_directory+"/"+str(x)+"_"+str(y)+"_"+file+".lines"
    data = createMeta("line", len(features), keys)+ "\n"
    for f in features:
        geometry = f["geometry"]
        if geometry["type"] == "Point":
            continue
        if geometry["type"] == "MultiPolygon":
            continue
        coordinatess = geometry["coordinates"]
        if geometry["type"] != "Polygon":
            coordinatess = [coordinatess]
        for coordinates in coordinatess:
            coordinates = list(map(lonlat_to_xy, coordinates))
            data += ";".join(map(lambda c :str(c[0])+","+str(c[1]), coordinates))
            data += " "
            
            svg_path = "M"+str(coordinates[0][0])+" "+str(coordinates[0][1])+" "+" ".join(map(lambda c : "L"+str(c[0])+" "+str(c[1]), coordinates[1:]))
            debug_data += "\n<path stroke='black' stroke-width='0.3' d=\""+svg_path+"\" />"
            
            if("level" in f["properties"]):
                data += str(f["properties"]["level"])
            else:
                data += "*"
            for key in keys:
                data += ","
                if key in f["properties"]:
                    data += f["properties"][key]
            data += "\n"
            
    f = open(file, "w")
    f.write(data)
    f.close()
    return debug_data

    
def read_geojson(inputfile, mustHaveProperties):
    contents = open(inputfile).read()
    parsed = json.loads(contents)
    result = list()  

    for f in parsed['features']:
        hasAll = all(map(lambda mustHave: mustHave in f["properties"], mustHaveProperties))
        if not hasAll:
            continue
        result.append(f)
    return result

def tile2long(x, z) :
    return (x / (2 ** z)) * 360 - 180

def tile2lat(y, z) :
    n = math.pi - (2 * math.pi * y) / (2 ** z)
    return (180 / math.pi) * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


for file in os.listdir(directory):
    if not file.endswith(".geojson"):
        continue
    [z, x, y] = list(map(int, file[0:-len(".geojson")].split("_")[-3:]))
    lon = tile2long(x, z)
    lat = tile2lat(y, z)
    [x0, y0] = lonlat_to_xy([tile2long(x+1,z), tile2long(y+1, z)])
    [x, y] = lonlat_to_xy([lon, lat])
    print("Range between tiles is" + str([x0 - x, y0 - y]) )
    features = read_geojson(directory+"/"+ file, ["highway"])
    residential = list(filter(lambda f:  f["properties"]["highway"] in ["residential","living_street","unclassified"], features))
    debug_data += exportLines(residential, [], "residential", x, y)
    exportLabels(residential, ["name"], "residential", x, y)

    cycle = list(filter(lambda f:  f["properties"]["highway"] in ["cycleway","pedestrian"] , features))
    debug_data += exportLines(cycle, [], "cycleways", x, y)

    foot = list(filter(lambda f:  f["properties"]["highway"] in ["footway","path","steps","corridor"], features))
    debug_data += exportLines(foot, [], "footways", x, y)
    exportLabels(foot, ["name"], "footways", x, y)

    service = list(filter(lambda f:  f["properties"]["highway"] in ["service"], features))
    debug_data += exportLines(service, [], "service", x, y)

    tertiary = list(filter(lambda f: f["properties"]["highway"] in ["tertiary", "tertiary_link","secondary","secondary_link"], features))
    debug_data += exportLines(tertiary, [], "tertiary", x, y)

    motor = list(filter(lambda f: f["properties"]["highway"] in ["trunk","trunk_link","primary","primary_link"], features))
    debug_data += exportLines(motor, [], "motor", x, y)
    
all_files = os.listdir(target_directory)
all_files.sort()

if not os.path.exists(target_directory+"/debug"):
    os.mkdir(target_directory+"/debug")

f = open(target_directory+"/debug/debug.svg", "w")
debug_data += "\n</svg>\n"
f.write(debug_data)
f.close()



f = open(target_directory+"/all.txt", "w")
f.write(str(len(all_files))+"\n")
f.write("\n".join(all_files))
f.close()
