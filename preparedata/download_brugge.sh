#! /bin/bash

mkdir brugge
cd brugge
#rm *.geojson
ts-node ~/git/MapComplete/scripts/generateCache.ts cycle_infra 14 ./ 51.24537192501262 3.1767990605678165 51.181919442410845 3.265679709426962 --force-zoom-level 15 --clip
cd -
python3 prepare-highways.py                                                                                                      
