import json
import math

# Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed
topleft_lon = 5.717937583679742
topleft_lat = 52.22148663376021
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

def exportLabels(features, keys, file):
    if not file.endswith(".points"):
        raise "File must end with .points"
    data = createMeta("point", len(features), keys)+ "\n"
    for f in features:
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

def exportLines(features, keys, file):
    if not file.endswith(".lines"):
        raise "File must end with .lines"
    data = createMeta("line", len(features), keys)+ "\n"
    for f in features:
        geometry = f["geometry"]
        if geometry["type"] == "Point":
            continue
        coordinatess = geometry["coordinates"]
        if geometry["type"] != "Polygon":
            coordinatess = [coordinatess]
        for coordinates in coordinatess:
            coordinates = map(lonlat_to_xy, coordinates)
            data += ";".join(map(lambda c :str(c[0])+","+str(c[1]), coordinates))
            data += " "
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
        
p = "../hackerhotel/"
exportLines(read_geojson("indoors.geojson", ["building"]), [], p + "buildings.lines")
exportLines(read_geojson("highways.geojson", []), [], "highways.lines")

exportLabels(read_geojson("addresses.geojson", ["addr:housenumber"]), ["addr:housenumber"], p +"addresses.points")

exportLines(read_geojson("indoors.geojson", ["indoor","name"]), ["name"], p +"rooms.lines")
exportLabels(read_geojson("indoors.geojson", ["indoor","name"]), ["name"], p +"rooms.points")