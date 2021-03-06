import struct
from struct import unpack_from


class OcdDem:
    def analyze(ofilemeta):
        file = open(ofilemeta.file_path, "rb")
        #
        header = file.read(65)
        file.close()
        #
        struc_string = "<b8shx10i"
        unpacked = unpack_from(struc_string, header)
        #
        ofilemeta.meta_version = unpacked[2]
        ofilemeta.raster_pixelsize = str(unpacked[3]) + "x" + str(unpacked[4])
        ofilemeta.raster_coordinate_bottomleft = str(unpacked[5]) + ", " + str(unpacked[7])
        ofilemeta.raster_coordinate_topright = str(unpacked[6]) + ", " + str(unpacked[8])
        ofilemeta.raster_pixel_minvalue = unpacked[9]
        ofilemeta.raster_pixel_maxvalue = unpacked[10]
        ofilemeta.raster_pixel_pixelsize_in_x = unpacked[11]
        ofilemeta.raster_pixel_pixelsize_in_y = unpacked[12]
        #
        return (ofilemeta)


class Ocd:
    def analyze(ofilemeta):
        file = open(ofilemeta.file_path, "rb")

        # header

        class header:
            pass

        record_format = "<hbbhbbIIiiIIIIIIIII"
        unpacked = struct.unpack_from(record_format, file.read(100))
        header.ocad_mark = unpacked[0]
        header.file_type = unpacked[1]
        header.file_status = unpacked[2]
        header.version = unpacked[3]
        header.subversion = unpacked[4]
        header.subsubversion = unpacked[5]
        header.first_symbol_index_blk = unpacked[6]
        header.object_index_block = unpacked[7]
        header.offline_sync_serial = unpacked[8]
        header.current_file_version = unpacked[9]
        header.internal1 = unpacked[10]
        header.internal2 = unpacked[11]
        header.first_string_index_blk = unpacked[12]
        header.file_name_pos = unpacked[13]
        header.file_name_size = unpacked[14]
        header.internal3 = unpacked[15]
        header.res1 = unpacked[16]
        header.res2 = unpacked[17]
        header.mr_start_block_position = unpacked[18]

        # header to ofiles-meta
        type_dict = {0: "map", 1: "cs", 2: "map", 3: "cs", 7: "map", 8: "server"}
        ofilemeta.meta_type = type_dict[header.file_type]

        ofilemeta.meta_version = str(header.version)

        if int(header.version) <= 9:
            version_long = str(header.version) + "." + str(header.subversion)
        else:
            version_long = str(header.version) + "." + str(header.subversion) + "." + str(header.subsubversion)
        # ofilemeta.meta_verion_long = version_long

        # strings
        string_index_block_list = []
        next_index_block = header.first_string_index_blk  # this is actually the first
        while next_index_block > 0:
            string_index_block_list.append(next_index_block)
            file.seek(next_index_block)
            next_index_block = _int_rhex(file.read(4))

        for index_block in string_index_block_list:
            for i in range(0, 256):
                file.seek(index_block + 4 + i * 16)
                pos = _int_rhex(file.read(4))
                length = _int_rhex(file.read(4))
                rectype = _int_rhex(file.read(4))
                objindex = _int_rhex(file.read(4))
                if rectype != 0:
                    file.seek(pos)
                    string = file.read(length).decode("utf-8", errors='ignore')
                    string = string.strip("\x00")
                    split_string = string.split("\t")
                    i = 0
                    string_dict = {}
                    for codevalue in split_string:
                        if i == 0:
                            code = "First"
                            value = codevalue
                        else:
                            code = codevalue[0:1]
                            value = codevalue[1:]
                        string_dict[code] = value
                        i += 1
                    if rectype == 1061:
                        ofilemeta.meta_note = string_dict["First"]
                    elif rectype == 1039:
                        ofilemeta.map_crs_code = ocad_grid_id_2_epsg[int(string_dict["i"])]["epsg"]
                        ofilemeta.map_crs_name = ocad_grid_id_2_epsg[int(string_dict["i"])]["name"]
                        ofilemeta.map_scale = string_dict["m"]
                    elif rectype == 9:
                        ofilemeta._add_color(
                            number=int(string_dict["n"]),
                            name=string_dict["First"],
                            cyan=int(string_dict["c"]),
                            magenta=int(string_dict["m"]),
                            yellow=int(string_dict["y"]),
                            black=int(string_dict["k"]),
                            # overprint = string_dict["o"]
                            opacity=int(string_dict["t"]))

        return (ofilemeta)


def _rhex(byte):
    """converts bytecode to hex, while reading from right to left"""
    return (byte[::-1].hex())


def _int_rhex(byte):
    """same as _rhex but returns integer instead of hex"""
    int_rhex = int(_rhex(byte), 16)
    return (int_rhex)


def _string_dict(string):
    """splits a OCAD-string and returns a dict"""
    split_string = string.split("\t")
    i = 0
    string_dict = {}
    for codevalue in split_string:
        if i == 0:
            code = "First"
            value = codevalue
        else:
            code = codevalue[0:1]
            value = codevalue[1:]
        string_dict[code] = value
        i += 1
    return (string_dict)


def _boolean(string_int):
    """returns True or False, for 1 or 0"""
    if int(string_int) == 0:
        return (False)
    elif int(string_int) == 1:
        return (True)
    else:
        raise ValueError("Only 0 or 1 allowed")


ocad_grid_id_2_epsg = {
    -2060: {
        'epsg': 32760,
        'name': 'WGS 84 / UTM zone 60S'
    },
    -2059: {
        'epsg': 32759,
        'name': 'WGS 84 / UTM zone 59S'
    },
    -2058: {
        'epsg': 32758,
        'name': 'WGS 84 / UTM zone 58S'
    },
    -2057: {
        'epsg': 32757,
        'name': 'WGS 84 / UTM zone 57S'
    },
    -2056: {
        'epsg': 32756,
        'name': 'WGS 84 / UTM zone 56S'
    },
    -2055: {
        'epsg': 32755,
        'name': 'WGS 84 / UTM zone 55S'
    },
    -2054: {
        'epsg': 32754,
        'name': 'WGS 84 / UTM zone 54S'
    },
    -2053: {
        'epsg': 32753,
        'name': 'WGS 84 / UTM zone 53S'
    },
    -2052: {
        'epsg': 32752,
        'name': 'WGS 84 / UTM zone 52S'
    },
    -2051: {
        'epsg': 32751,
        'name': 'WGS 84 / UTM zone 51S'
    },
    -2050: {
        'epsg': 32750,
        'name': 'WGS 84 / UTM zone 50S'
    },
    -2049: {
        'epsg': 32749,
        'name': 'WGS 84 / UTM zone 49S'
    },
    -2048: {
        'epsg': 32748,
        'name': 'WGS 84 / UTM zone 48S'
    },
    -2047: {
        'epsg': 32747,
        'name': 'WGS 84 / UTM zone 47S'
    },
    -2046: {
        'epsg': 32746,
        'name': 'WGS 84 / UTM zone 46S'
    },
    -2045: {
        'epsg': 32745,
        'name': 'WGS 84 / UTM zone 45S'
    },
    -2044: {
        'epsg': 32744,
        'name': 'WGS 84 / UTM zone 44S'
    },
    -2043: {
        'epsg': 32743,
        'name': 'WGS 84 / UTM zone 43S'
    },
    -2042: {
        'epsg': 32742,
        'name': 'WGS 84 / UTM zone 42S'
    },
    -2041: {
        'epsg': 32741,
        'name': 'WGS 84 / UTM zone 41S'
    },
    -2040: {
        'epsg': 32740,
        'name': 'WGS 84 / UTM zone 40S'
    },
    -2039: {
        'epsg': 32739,
        'name': 'WGS 84 / UTM zone 39S'
    },
    -2038: {
        'epsg': 32738,
        'name': 'WGS 84 / UTM zone 38S'
    },
    -2037: {
        'epsg': 32737,
        'name': 'WGS 84 / UTM zone 37S'
    },
    -2036: {
        'epsg': 32736,
        'name': 'WGS 84 / UTM zone 36S'
    },
    -2035: {
        'epsg': 32735,
        'name': 'WGS 84 / UTM zone 35S'
    },
    -2034: {
        'epsg': 32734,
        'name': 'WGS 84 / UTM zone 34S'
    },
    -2033: {
        'epsg': 32733,
        'name': 'WGS 84 / UTM zone 33S'
    },
    -2032: {
        'epsg': 32732,
        'name': 'WGS 84 / UTM zone 32S'
    },
    -2031: {
        'epsg': 32731,
        'name': 'WGS 84 / UTM zone 31S'
    },
    -2030: {
        'epsg': 32730,
        'name': 'WGS 84 / UTM zone 30S'
    },
    -2029: {
        'epsg': 32729,
        'name': 'WGS 84 / UTM zone 29S'
    },
    -2028: {
        'epsg': 32728,
        'name': 'WGS 84 / UTM zone 28S'
    },
    -2027: {
        'epsg': 32727,
        'name': 'WGS 84 / UTM zone 27S'
    },
    -2026: {
        'epsg': 32726,
        'name': 'WGS 84 / UTM zone 26S'
    },
    -2025: {
        'epsg': 32725,
        'name': 'WGS 84 / UTM zone 25S'
    },
    -2024: {
        'epsg': 32724,
        'name': 'WGS 84 / UTM zone 24S'
    },
    -2023: {
        'epsg': 32723,
        'name': 'WGS 84 / UTM zone 23S'
    },
    -2022: {
        'epsg': 32722,
        'name': 'WGS 84 / UTM zone 22S'
    },
    -2021: {
        'epsg': 32721,
        'name': 'WGS 84 / UTM zone 21S'
    },
    -2020: {
        'epsg': 32720,
        'name': 'WGS 84 / UTM zone 20S'
    },
    -2019: {
        'epsg': 32719,
        'name': 'WGS 84 / UTM zone 19S'
    },
    -2018: {
        'epsg': 32718,
        'name': 'WGS 84 / UTM zone 18S'
    },
    -2017: {
        'epsg': 32717,
        'name': 'WGS 84 / UTM zone 17S'
    },
    -2016: {
        'epsg': 32716,
        'name': 'WGS 84 / UTM zone 16S'
    },
    -2015: {
        'epsg': 32715,
        'name': 'WGS 84 / UTM zone 15S'
    },
    -2014: {
        'epsg': 32714,
        'name': 'WGS 84 / UTM zone 14S'
    },
    -2013: {
        'epsg': 32713,
        'name': 'WGS 84 / UTM zone 13S'
    },
    -2012: {
        'epsg': 32712,
        'name': 'WGS 84 / UTM zone 12S'
    },
    -2011: {
        'epsg': 32711,
        'name': 'WGS 84 / UTM zone 11S'
    },
    -2010: {
        'epsg': 32710,
        'name': 'WGS 84 / UTM zone 10S'
    },
    -2009: {
        'epsg': 32709,
        'name': 'WGS 84 / UTM zone 9S'
    },
    -2008: {
        'epsg': 32708,
        'name': 'WGS 84 / UTM zone 8S'
    },
    -2007: {
        'epsg': 32707,
        'name': 'WGS 84 / UTM zone 7S'
    },
    -2006: {
        'epsg': 32706,
        'name': 'WGS 84 / UTM zone 6S'
    },
    -2005: {
        'epsg': 32705,
        'name': 'WGS 84 / UTM zone 5S'
    },
    -2004: {
        'epsg': 32704,
        'name': 'WGS 84 / UTM zone 4S'
    },
    -2003: {
        'epsg': 32703,
        'name': 'WGS 84 / UTM zone 3S'
    },
    -2002: {
        'epsg': 32702,
        'name': 'WGS 84 / UTM zone 2S'
    },
    -2001: {
        'epsg': 32701,
        'name': 'WGS 84 / UTM zone 1S'
    },
    2001: {
        'epsg': 32601,
        'name': 'WGS 84 / UTM zone 1N'
    },
    2002: {
        'epsg': 32602,
        'name': 'WGS 84 / UTM zone 2N'
    },
    2003: {
        'epsg': 32603,
        'name': 'WGS 84 / UTM zone 3N'
    },
    2004: {
        'epsg': 32604,
        'name': 'WGS 84 / UTM zone 4N'
    },
    2005: {
        'epsg': 32605,
        'name': 'WGS 84 / UTM zone 5N'
    },
    2006: {
        'epsg': 32606,
        'name': 'WGS 84 / UTM zone 6N'
    },
    2007: {
        'epsg': 32607,
        'name': 'WGS 84 / UTM zone 7N'
    },
    2008: {
        'epsg': 32608,
        'name': 'WGS 84 / UTM zone 8N'
    },
    2009: {
        'epsg': 32609,
        'name': 'WGS 84 / UTM zone 9N'
    },
    2010: {
        'epsg': 32610,
        'name': 'WGS 84 / UTM zone 10N'
    },
    2011: {
        'epsg': 32611,
        'name': 'WGS 84 / UTM zone 11N'
    },
    2012: {
        'epsg': 32612,
        'name': 'WGS 84 / UTM zone 12N'
    },
    2013: {
        'epsg': 32613,
        'name': 'WGS 84 / UTM zone 13N'
    },
    2014: {
        'epsg': 32614,
        'name': 'WGS 84 / UTM zone 14N'
    },
    2015: {
        'epsg': 32615,
        'name': 'WGS 84 / UTM zone 15N'
    },
    2016: {
        'epsg': 32616,
        'name': 'WGS 84 / UTM zone 16N'
    },
    2017: {
        'epsg': 32617,
        'name': 'WGS 84 / UTM zone 17N'
    },
    2018: {
        'epsg': 32618,
        'name': 'WGS 84 / UTM zone 18N'
    },
    2019: {
        'epsg': 32619,
        'name': 'WGS 84 / UTM zone 19N'
    },
    2020: {
        'epsg': 32620,
        'name': 'WGS 84 / UTM zone 20N'
    },
    2021: {
        'epsg': 32621,
        'name': 'WGS 84 / UTM zone 21N'
    },
    2022: {
        'epsg': 32622,
        'name': 'WGS 84 / UTM zone 22N'
    },
    2023: {
        'epsg': 32623,
        'name': 'WGS 84 / UTM zone 23N'
    },
    2024: {
        'epsg': 32624,
        'name': 'WGS 84 / UTM zone 24N'
    },
    2025: {
        'epsg': 32625,
        'name': 'WGS 84 / UTM zone 25N'
    },
    2026: {
        'epsg': 32626,
        'name': 'WGS 84 / UTM zone 26N'
    },
    2027: {
        'epsg': 32627,
        'name': 'WGS 84 / UTM zone 27N'
    },
    2028: {
        'epsg': 32628,
        'name': 'WGS 84 / UTM zone 28N'
    },
    2029: {
        'epsg': 32629,
        'name': 'WGS 84 / UTM zone 29N'
    },
    2030: {
        'epsg': 32630,
        'name': 'WGS 84 / UTM zone 30N'
    },
    2031: {
        'epsg': 32631,
        'name': 'WGS 84 / UTM zone 31N'
    },
    2032: {
        'epsg': 32632,
        'name': 'WGS 84 / UTM zone 32N'
    },
    2033: {
        'epsg': 32633,
        'name': 'WGS 84 / UTM zone 33N'
    },
    2034: {
        'epsg': 32634,
        'name': 'WGS 84 / UTM zone 34N'
    },
    2035: {
        'epsg': 32635,
        'name': 'WGS 84 / UTM zone 35N'
    },
    2036: {
        'epsg': 32636,
        'name': 'WGS 84 / UTM zone 36N'
    },
    2037: {
        'epsg': 32637,
        'name': 'WGS 84 / UTM zone 37N'
    },
    2038: {
        'epsg': 32638,
        'name': 'WGS 84 / UTM zone 38N'
    },
    2039: {
        'epsg': 32639,
        'name': 'WGS 84 / UTM zone 39N'
    },
    2040: {
        'epsg': 32640,
        'name': 'WGS 84 / UTM zone 40N'
    },
    2041: {
        'epsg': 32641,
        'name': 'WGS 84 / UTM zone 41N'
    },
    2042: {
        'epsg': 32642,
        'name': 'WGS 84 / UTM zone 42N'
    },
    2043: {
        'epsg': 32643,
        'name': 'WGS 84 / UTM zone 43N'
    },
    2044: {
        'epsg': 32644,
        'name': 'WGS 84 / UTM zone 44N'
    },
    2045: {
        'epsg': 32645,
        'name': 'WGS 84 / UTM zone 45N'
    },
    2046: {
        'epsg': 32646,
        'name': 'WGS 84 / UTM zone 46N'
    },
    2047: {
        'epsg': 32647,
        'name': 'WGS 84 / UTM zone 47N'
    },
    2048: {
        'epsg': 32648,
        'name': 'WGS 84 / UTM zone 48N'
    },
    2049: {
        'epsg': 32649,
        'name': 'WGS 84 / UTM zone 49N'
    },
    2050: {
        'epsg': 32650,
        'name': 'WGS 84 / UTM zone 50N'
    },
    2051: {
        'epsg': 32651,
        'name': 'WGS 84 / UTM zone 51N'
    },
    2052: {
        'epsg': 32652,
        'name': 'WGS 84 / UTM zone 52N'
    },
    2053: {
        'epsg': 32653,
        'name': 'WGS 84 / UTM zone 53N'
    },
    2054: {
        'epsg': 32654,
        'name': 'WGS 84 / UTM zone 54N'
    },
    2055: {
        'epsg': 32655,
        'name': 'WGS 84 / UTM zone 55N'
    },
    2056: {
        'epsg': 32656,
        'name': 'WGS 84 / UTM zone 56N'
    },
    2057: {
        'epsg': 32657,
        'name': 'WGS 84 / UTM zone 57N'
    },
    2058: {
        'epsg': 32658,
        'name': 'WGS 84 / UTM zone 58N'
    },
    2059: {
        'epsg': 32659,
        'name': 'WGS 84 / UTM zone 59N'
    },
    2060: {
        'epsg': 32660,
        'name': 'WGS 84 / UTM zone 60N'
    },
    3028: {
        'epsg': 31257,
        'name': 'MGI / Austria GK M28'
    },
    3031: {
        'epsg': 31258,
        'name': 'MGI / Austria GK M31'
    },
    3034: {
        'epsg': 31259,
        'name': 'MGI / Austria GK M34'
    },
    3035: {
        'epsg': 31254,
        'name': 'MGI / Austria GK West'
    },
    3036: {
        'epsg': 31255,
        'name': 'MGI / Austria GK Central'
    },
    3038: {
        'epsg': 31256,
        'name': 'MGI / Austria GK East'
    },
    4001: {
        'epsg': 31300,
        'name': 'Belge 1972 / Belge Lambert 72'
    },
    4002: {
        'epsg': 3447,
        'name': 'ETRS89 / Belgian Lambert 2005'
    },
    4003: {
        'epsg': 3812,
        'name': 'ETRS89 / Belgian Lambert 2008'
    },
    5000: {
        'epsg': 27700,
        'name': 'OSGB 1936 / British National Grid'
    },
    6001: {
        'epsg': 2391,
        'name': 'KKJ / Finland zone 1'
    },
    6002: {
        'epsg': 2392,
        'name': 'KKJ / Finland zone 2'
    },
    6003: {
        'epsg': 2393,
        'name': 'KKJ / Finland Uniform Coordinate System'
    },
    6004: {
        'epsg': 2394,
        'name': 'KKJ / Finland zone 4'
    },
    6005: {
        'epsg': 3067,
        'name': 'ETRS89 / TM35FIN(E,N)'
    },
    6006: {
        'epsg': 3873,
        'name': 'ETRS89 / GK19FIN'
    },
    6007: {
        'epsg': 3874,
        'name': 'ETRS89 / GK20FIN'
    },
    6008: {
        'epsg': 3875,
        'name': 'ETRS89 / GK21FIN'
    },
    6009: {
        'epsg': 3876,
        'name': 'ETRS89 / GK22FIN'
    },
    6010: {
        'epsg': 3877,
        'name': 'ETRS89 / GK23FIN'
    },
    6011: {
        'epsg': 3878,
        'name': 'ETRS89 / GK24FIN'
    },
    6012: {
        'epsg': 3879,
        'name': 'ETRS89 / GK25FIN'
    },
    6013: {
        'epsg': 3880,
        'name': 'ETRS89 / GK26FIN'
    },
    6014: {
        'epsg': 3881,
        'name': 'ETRS89 / GK27FIN'
    },
    6015: {
        'epsg': 3882,
        'name': 'ETRS89 / GK28FIN'
    },
    6016: {
        'epsg': 3883,
        'name': 'ETRS89 / GK29FIN'
    },
    6017: {
        'epsg': 3884,
        'name': 'ETRS89 / GK30FIN'
    },
    6018: {
        'epsg': 3885,
        'name': 'ETRS89 / GK31FIN'
    },
    6019: {
        'epsg': 3126,
        'name': 'ETRS89 / ETRS-GK19FIN'
    },
    6020: {
        'epsg': 3127,
        'name': 'ETRS89 / ETRS-GK20FIN'
    },
    6021: {
        'epsg': 3128,
        'name': 'ETRS89 / ETRS-GK21FIN'
    },
    6022: {
        'epsg': 3129,
        'name': 'ETRS89 / ETRS-GK22FIN'
    },
    6023: {
        'epsg': 3130,
        'name': 'ETRS89 / ETRS-GK23FIN'
    },
    6024: {
        'epsg': 3131,
        'name': 'ETRS89 / ETRS-GK24FIN'
    },
    6025: {
        'epsg': 3132,
        'name': 'ETRS89 / ETRS-GK25FIN'
    },
    6026: {
        'epsg': 3133,
        'name': 'ETRS89 / ETRS-GK26FIN'
    },
    6027: {
        'epsg': 3134,
        'name': 'ETRS89 / ETRS-GK27FIN'
    },
    6028: {
        'epsg': 3135,
        'name': 'ETRS89 / ETRS-GK28FIN'
    },
    6029: {
        'epsg': 3136,
        'name': 'ETRS89 / ETRS-GK29FIN'
    },
    6030: {
        'epsg': 3137,
        'name': 'ETRS89 / ETRS-GK30FIN'
    },
    6031: {
        'epsg': 3138,
        'name': 'ETRS89 / ETRS-GK31FIN'
    },
    6032: {
        'epsg': 3387,
        'name': 'KKJ / Finland zone 5'
    },
    7001: {
        'epsg': 27591,
        'name': 'NTF_Paris_Nord_France'
    },  # EPSG-Code not found
    7002: {
        'epsg': 27581,
        'name': 'NTF_Paris_France_I'
    },  # EPSG-Code not found
    7003: {
        'epsg': 27592,
        'name': 'NTF_Paris_Centre_France'
    },  # EPSG-Code not found
    7004: {
        'epsg': 27572,
        'name': 'NTF (Paris) / Lambert zone II'
    },
    7005: {
        'epsg': 27593,
        'name': 'NTF_Paris_Sud_France'
    },  # EPSG-Code not found
    7006: {
        'epsg': 27583,
        'name': 'NTF_Paris_France_III'
    },  # EPSG-Code not found
    7007: {
        'epsg': 27594,
        'name': 'NTF_Paris_Corse'
    },  # EPSG-Code not found
    7008: {
        'epsg': 27584,
        'name': 'NTF_Paris_France_IV'
    },  # EPSG-Code not found
    7009: {
        'epsg': 2154,
        'name': 'RGF93 / Lambert-93'
    },
    7010: {
        'epsg': 3942,
        'name': 'RGF93 / CC42'
    },
    7011: {
        'epsg': 3943,
        'name': 'RGF93 / CC43'
    },
    7012: {
        'epsg': 3944,
        'name': 'RGF93 / CC44'
    },
    7013: {
        'epsg': 3945,
        'name': 'RGF93 / CC45'
    },
    7014: {
        'epsg': 3946,
        'name': 'RGF93 / CC46'
    },
    7015: {
        'epsg': 3947,
        'name': 'RGF93 / CC47'
    },
    7016: {
        'epsg': 3948,
        'name': 'RGF93 / CC48'
    },
    7017: {
        'epsg': 3949,
        'name': 'RGF93 / CC49'
    },
    7018: {
        'epsg': 3950,
        'name': 'RGF93 / CC50'
    },
    8002: {
        'epsg': 31466,
        'name': 'DHDN / 3-degree Gauss-Kruger zone 2'
    },
    8003: {
        'epsg': 31467,
        'name': 'DHDN / 3-degree Gauss-Kruger zone 3'
    },
    8004: {
        'epsg': 31468,
        'name': 'DHDN / 3-degree Gauss-Kruger zone 4'
    },
    8005: {
        'epsg': 31469,
        'name': 'DHDN / 3-degree Gauss-Kruger zone 5'
    },
    8006: {
        'epsg': 25831,
        'name': 'ETRS89 / UTM zone 31N'
    },
    8007: {
        'epsg': 25832,
        'name': 'ETRS89 / UTM zone 32N'
    },
    8008: {
        'epsg': 25833,
        'name': 'ETRS89 / UTM zone 33N'
    },
    8009: {
        'epsg': 0,
        'name': 'ETRS89 32N 7Stellen'
    },  # EPSG-Code not found
    8010: {
        'epsg': 0,
        'name': 'ETRS89 33N 7Stellen'
    },  # EPSG-Code not found
    8011: {
        'epsg': 0,
        'name': 'ETRS89 32N 8Stellen'
    },  # EPSG-Code not found
    8012: {
        'epsg': 0,
        'name': 'ETRS89 33N 8Stellen'
    },  # EPSG-Code not found
    8013: {
        'epsg': 3068,
        'name': 'DHDN / Soldner Berlin'
    },
    8014: {
        'epsg': 3068,
        'name': 'DHDN / Soldner Berlin'
    },
    9001: {
        'epsg': 29902,
        'name': 'TM65 / Irish Grid'
    },
    9002: {
        'epsg': 29903,
        'name': 'TM75 / Irish Grid'
    },
    9003: {
        'epsg': 2157,
        'name': 'IRENET95 / Irish Transverse Mercator'
    },
    11001: {
        'epsg': 30161,
        'name': 'Tokyo / Japan Plane Rectangular CS I'
    },
    11002: {
        'epsg': 30162,
        'name': 'Tokyo / Japan Plane Rectangular CS II'
    },
    11003: {
        'epsg': 30163,
        'name': 'Tokyo / Japan Plane Rectangular CS III'
    },
    11004: {
        'epsg': 30164,
        'name': 'Tokyo / Japan Plane Rectangular CS IV'
    },
    11005: {
        'epsg': 30165,
        'name': 'Tokyo / Japan Plane Rectangular CS V'
    },
    11006: {
        'epsg': 30166,
        'name': 'Tokyo / Japan Plane Rectangular CS VI'
    },
    11007: {
        'epsg': 30167,
        'name': 'Tokyo / Japan Plane Rectangular CS VII'
    },
    11008: {
        'epsg': 30168,
        'name': 'Tokyo / Japan Plane Rectangular CS VIII'
    },
    11009: {
        'epsg': 30169,
        'name': 'Tokyo / Japan Plane Rectangular CS IX'
    },
    11010: {
        'epsg': 30170,
        'name': 'Tokyo / Japan Plane Rectangular CS X'
    },
    11011: {
        'epsg': 30171,
        'name': 'Tokyo / Japan Plane Rectangular CS XI'
    },
    11012: {
        'epsg': 30172,
        'name': 'Tokyo / Japan Plane Rectangular CS XII'
    },
    11013: {
        'epsg': 30173,
        'name': 'Tokyo / Japan Plane Rectangular CS XIII'
    },
    11014: {
        'epsg': 30174,
        'name': 'Tokyo / Japan Plane Rectangular CS XIV'
    },
    11015: {
        'epsg': 30175,
        'name': 'Tokyo / Japan Plane Rectangular CS XV'
    },
    11016: {
        'epsg': 30176,
        'name': 'Tokyo / Japan Plane Rectangular CS XVI'
    },
    11017: {
        'epsg': 30177,
        'name': 'Tokyo / Japan Plane Rectangular CS XVII'
    },
    11018: {
        'epsg': 30178,
        'name': 'Tokyo / Japan Plane Rectangular CS XVIII'
    },
    11019: {
        'epsg': 30179,
        'name': 'Tokyo / Japan Plane Rectangular CS XIX'
    },
    11020: {
        'epsg': 2443,
        'name': 'JGD2000 / Japan Plane Rectangular CS I'
    },
    11021: {
        'epsg': 2444,
        'name': 'JGD2000 / Japan Plane Rectangular CS II'
    },
    11022: {
        'epsg': 2445,
        'name': 'JGD2000 / Japan Plane Rectangular CS III'
    },
    11023: {
        'epsg': 2446,
        'name': 'JGD2000 / Japan Plane Rectangular CS IV'
    },
    11024: {
        'epsg': 2447,
        'name': 'JGD2000 / Japan Plane Rectangular CS V'
    },
    11025: {
        'epsg': 2448,
        'name': 'JGD2000 / Japan Plane Rectangular CS VI'
    },
    11026: {
        'epsg': 2449,
        'name': 'JGD2000 / Japan Plane Rectangular CS VII'
    },
    11027: {
        'epsg': 2450,
        'name': 'JGD2000 / Japan Plane Rectangular CS VIII'
    },
    11028: {
        'epsg': 2451,
        'name': 'JGD2000 / Japan Plane Rectangular CS IX'
    },
    11029: {
        'epsg': 2452,
        'name': 'JGD2000 / Japan Plane Rectangular CS X'
    },
    11030: {
        'epsg': 2453,
        'name': 'JGD2000 / Japan Plane Rectangular CS XI'
    },
    11031: {
        'epsg': 2454,
        'name': 'JGD2000 / Japan Plane Rectangular CS XII'
    },
    11032: {
        'epsg': 2455,
        'name': 'JGD2000 / Japan Plane Rectangular CS XIII'
    },
    11033: {
        'epsg': 2456,
        'name': 'JGD2000 / Japan Plane Rectangular CS XIV'
    },
    11034: {
        'epsg': 2457,
        'name': 'JGD2000 / Japan Plane Rectangular CS XV'
    },
    11035: {
        'epsg': 2458,
        'name': 'JGD2000 / Japan Plane Rectangular CS XVI'
    },
    11036: {
        'epsg': 2459,
        'name': 'JGD2000 / Japan Plane Rectangular CS XVII'
    },
    11037: {
        'epsg': 2460,
        'name': 'JGD2000 / Japan Plane Rectangular CS XVIII'
    },
    11039: {
        'epsg': 2461,
        'name': 'JGD2000 / Japan Plane Rectangular CS XIX'
    },
    12001: {
        'epsg': 27391,
        'name': 'NGO 1948 (Oslo) / NGO zone I'
    },
    12002: {
        'epsg': 27392,
        'name': 'NGO 1948 (Oslo) / NGO zone II'
    },
    12003: {
        'epsg': 27393,
        'name': 'NGO 1948 (Oslo) / NGO zone III'
    },
    12004: {
        'epsg': 27394,
        'name': 'NGO 1948 (Oslo) / NGO zone IV'
    },
    12005: {
        'epsg': 27395,
        'name': 'NGO 1948 (Oslo) / NGO zone V'
    },
    12006: {
        'epsg': 27396,
        'name': 'NGO 1948 (Oslo) / NGO zone VI'
    },
    12007: {
        'epsg': 27397,
        'name': 'NGO 1948 (Oslo) / NGO zone VII'
    },
    12008: {
        'epsg': 27398,
        'name': 'NGO 1948 (Oslo) / NGO zone VIII'
    },
    12009: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    12010: {
        'epsg': 23032,
        'name': 'ED50 / UTM zone 32N'
    },
    12011: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    12012: {
        'epsg': 23034,
        'name': 'ED50 / UTM zone 34N'
    },
    12013: {
        'epsg': 23035,
        'name': 'ED50 / UTM zone 35N'
    },
    12014: {
        'epsg': 23036,
        'name': 'ED50 / UTM zone 36N'
    },
    13001: {
        'epsg': 6124,
        'name': 'WGS 84 / EPSG Arctic zone 4-12'
    },
    13002: {
        'epsg': 3006,
        'name': 'SWEREF99 TM'
    },
    13003: {
        'epsg': 3007,
        'name': 'SWEREF99 12 00'
    },
    13004: {
        'epsg': 3008,
        'name': 'SWEREF99 13 30'
    },
    13005: {
        'epsg': 3009,
        'name': 'SWEREF99 15 00'
    },
    13006: {
        'epsg': 3010,
        'name': 'SWEREF99 16 30'
    },
    13007: {
        'epsg': 3011,
        'name': 'SWEREF99 18 00'
    },
    13008: {
        'epsg': 3012,
        'name': 'SWEREF99 14 15'
    },
    13009: {
        'epsg': 3013,
        'name': 'SWEREF99 15 45'
    },
    13010: {
        'epsg': 3014,
        'name': 'SWEREF99 17 15'
    },
    13011: {
        'epsg': 3015,
        'name': 'SWEREF99 18 45'
    },
    13012: {
        'epsg': 3016,
        'name': 'SWEREF99 20 15'
    },
    13013: {
        'epsg': 3017,
        'name': 'SWEREF99 21 45'
    },
    13014: {
        'epsg': 3018,
        'name': 'SWEREF99 23 15'
    },
    14001: {
        'epsg': 21781,
        'name': 'CH1903 / LV03'
    },
    14002: {
        'epsg': 2056,
        'name': 'CH1903+ / LV95'
    },
    15001: {
        'epsg': 3912,
        'name': 'MGI 1901 / Slovene National Grid'
    },
    15002: {
        'epsg': 3794,
        'name': 'Slovenia 1996 / Slovene National Grid'
    },
    16001: {
        'epsg': 4685,
        'name': ''
    },  # EPSG-Code not found
    16002: {
        'epsg': 4686,
        'name': 'MAGNA-SIRGAS'
    },  # EPSG-Code not found
    16003: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    16004: {
        'epsg': 23032,
        'name': 'ED50 / UTM zone 32N'
    },
    16005: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    16006: {
        'epsg': 23034,
        'name': 'ED50 / UTM zone 34N'
    },
    16007: {
        'epsg': 25832,
        'name': 'ETRS89 / UTM zone 32N'
    },
    16008: {
        'epsg': 25833,
        'name': 'ETRS89 / UTM zone 33N'
    },
    16009: {
        'epsg': 6707,
        'name': 'RDN2008 / UTM zone 32N (N-E)'
    },
    16010: {
        'epsg': 6708,
        'name': 'RDN2008 / UTM zone 33N (N-E)'
    },
    16011: {
        'epsg': 6875,
        'name': 'RDN2008 / Italy zone (N-E)'
    },
    16012: {
        'epsg': 6876,
        'name': 'RDN2008 / Zone 12 (N-E)'
    },
    17001: {
        'epsg': 2206,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 9'
    },
    17002: {
        'epsg': 2207,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 10'
    },
    17003: {
        'epsg': 2208,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 11'
    },
    17004: {
        'epsg': 2209,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 12'
    },
    17005: {
        'epsg': 2210,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 13'
    },
    17006: {
        'epsg': 2211,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 14'
    },
    17007: {
        'epsg': 2212,
        'name': 'ED50 / 3-degree Gauss-Kruger zone 15'
    },
    17008: {
        'epsg': 7006,
        'name': 'Nahrwan 1934 / UTM zone 38N'
    },
    18001: {
        'epsg': 2046,
        'name': 'Hartebeesthoek94 / Lo15'
    },
    18002: {
        'epsg': 2047,
        'name': 'Hartebeesthoek94 / Lo17'
    },
    18003: {
        'epsg': 2048,
        'name': 'Hartebeesthoek94 / Lo19'
    },
    18004: {
        'epsg': 2049,
        'name': 'Hartebeesthoek94 / Lo21'
    },
    18005: {
        'epsg': 2050,
        'name': 'Hartebeesthoek94 / Lo23'
    },
    18006: {
        'epsg': 2051,
        'name': 'Hartebeesthoek94 / Lo25'
    },
    18007: {
        'epsg': 2052,
        'name': 'Hartebeesthoek94 / Lo27'
    },
    18008: {
        'epsg': 2053,
        'name': 'Hartebeesthoek94 / Lo29'
    },
    18009: {
        'epsg': 2054,
        'name': 'Hartebeesthoek94 / Lo31'
    },
    18010: {
        'epsg': 2055,
        'name': 'Hartebeesthoek94 / Lo33'
    },
    19000: {
        'epsg': 2193,
        'name': 'NZGD2000 / New Zealand Transverse Mercator 2000'
    },
    20001: {
        'epsg': 28348,
        'name': 'GDA94 / MGA zone 48'
    },
    20002: {
        'epsg': 28349,
        'name': 'GDA94 / MGA zone 49'
    },
    20003: {
        'epsg': 28350,
        'name': 'GDA94 / MGA zone 50'
    },
    20004: {
        'epsg': 28351,
        'name': 'GDA94 / MGA zone 51'
    },
    20005: {
        'epsg': 28352,
        'name': 'GDA94 / MGA zone 52'
    },
    20006: {
        'epsg': 28353,
        'name': 'GDA94 / MGA zone 53'
    },
    20007: {
        'epsg': 28354,
        'name': 'GDA94 / MGA zone 54'
    },
    20008: {
        'epsg': 28355,
        'name': 'GDA94 / MGA zone 55'
    },
    20009: {
        'epsg': 28356,
        'name': 'GDA94 / MGA zone 56'
    },
    20010: {
        'epsg': 28357,
        'name': 'GDA94 / MGA zone 57'
    },
    20011: {
        'epsg': 28358,
        'name': 'GDA94 / MGA zone 58'
    },
    20012: {
        'epsg': 3112,
        'name': 'GDA94 / Geoscience Australia Lambert'
    },
    21001: {
        'epsg': 23032,
        'name': 'ED50 / UTM zone 32N'
    },
    21002: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    21003: {
        'epsg': 25832,
        'name': 'ETRS89 / UTM zone 32N'
    },
    21004: {
        'epsg': 25833,
        'name': 'ETRS89 / UTM zone 33N'
    },
    23001: {
        'epsg': 0,
        'name': 'South Africa rotated WG15'
    },  # EPSG-Code not found
    23002: {
        'epsg': 0,
        'name': 'South Africa rotated WG17'
    },  # EPSG-Code not found
    23003: {
        'epsg': 0,
        'name': 'South Africa rotated WG19'
    },  # EPSG-Code not found
    23004: {
        'epsg': 0,
        'name': 'South Africa rotated WG21'
    },  # EPSG-Code not found
    23005: {
        'epsg': 0,
        'name': 'South Africa rotated WG23'
    },  # EPSG-Code not found
    23006: {
        'epsg': 0,
        'name': 'South Africa rotated WG25'
    },  # EPSG-Code not found
    23007: {
        'epsg': 0,
        'name': 'South Africa rotated WG27'
    },  # EPSG-Code not found
    23008: {
        'epsg': 0,
        'name': 'South Africa rotated WG29'
    },  # EPSG-Code not found
    23009: {
        'epsg': 0,
        'name': 'South Africa rotated WG31'
    },  # EPSG-Code not found
    23010: {
        'epsg': 0,
        'name': 'South Africa rotated WG33'
    },  # EPSG-Code not found
    24000: {
        'epsg': 4272,
        'name': 'NZGD49'
    },
    26000: {
        'epsg': 3346,
        'name': 'LKS94 / Lithuania TM'
    },
    27000: {
        'epsg': 3301,
        'name': 'Estonian Coordinate System of 1997'
    },
    28000: {
        'epsg': 3059,
        'name': 'LKS92 / Latvia TM'
    },
    29000: {
        'epsg': 2100,
        'name': 'GGRS87 / Greek Grid'
    },
    30001: {
        'epsg': 23028,
        'name': 'ED50 / UTM zone 28N'
    },
    30002: {
        'epsg': 23029,
        'name': 'ED50 / UTM zone 29N'
    },
    30003: {
        'epsg': 23030,
        'name': 'ED50 / UTM zone 30N'
    },
    30004: {
        'epsg': 23030,
        'name': 'ED50 / UTM zone 30N'
    },
    30005: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    30006: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    31005: {
        'epsg': 7009,
        'name': 'Croatia'
    },  # EPSG-Code not found
    31006: {
        'epsg': 7010,
        'name': ''
    },  # EPSG-Code not found
    31007: {
        'epsg': 3765,
        'name': 'HTRS96 / Croatia TM'
    },
    32000: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    33001: {
        'epsg': 2169,
        'name': 'Luxembourg 1930 / Gauss'
    },
    33002: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    34000: {
        'epsg': 29902,
        'name': 'TM65 / Irish Grid'
    },
    35000: {
        'epsg': 2462,
        'name': 'Albanian 1987 / Gauss-Kruger zone 4'
    },
    36001: {
        'epsg': 25833,
        'name': 'ETRS89 / UTM zone 33N'
    },
    36002: {
        'epsg': 25834,
        'name': 'ETRS89 / UTM zone 34N'
    },
    37001: {
        'epsg': 25834,
        'name': 'ETRS89 / UTM zone 34N'
    },
    37002: {
        'epsg': 25835,
        'name': 'ETRS89 / UTM zone 35N'
    },
    38001: {
        'epsg': 0,
        'name': 'Iceland UTM HJ1955 26N'
    },  # EPSG-Code not found
    38002: {
        'epsg': 0,
        'name': 'Iceland UTM HJ1955 27N'
    },  # EPSG-Code not found
    38003: {
        'epsg': 0,
        'name': 'Iceland UTM HJ1955 28N'
    },  # EPSG-Code not found
    38004: {
        'epsg': 3057,
        'name': 'ISN93 / Lambert 1993'
    },
    39000: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    40000: {
        'epsg': 23032,
        'name': 'ED50 / UTM zone 32N'
    },
    41001: {
        'epsg': 28991,
        'name': 'Amersfoort / RD Old'
    },
    41002: {
        'epsg': 23031,
        'name': 'ED50 / UTM zone 31N'
    },
    41003: {
        'epsg': 23032,
        'name': 'ED50 / UTM zone 32N'
    },
    41004: {
        'epsg': 28992,
        'name': 'Amersfoort / RD New'
    },
    42001: {
        'epsg': 27493,
        'name': 'Datum 73 / Modified Portuguese Grid'
    },
    42002: {
        'epsg': 23028,
        'name': 'ED50 / UTM zone 28N'
    },
    43001: {
        'epsg': 0,
        'name': 'Romania S42 34N'
    },  # EPSG-Code not found
    43002: {
        'epsg': 0,
        'name': 'Romania S42 35N'
    },  # EPSG-Code not found
    44000: {
        'epsg': 23033,
        'name': 'ED50 / UTM zone 33N'
    },
    46001: {
        'epsg': 5514,
        'name': 'S-JTSK / Krovak East North'
    },
    46002: {
        'epsg': 28403,
        'name': 'Pulkovo_1942_GK_Zone_3'
    },
    47001: {
        'epsg': 5514,
        'name': 'S-JTSK / Krovak East North'
    },
    47002: {
        'epsg': 28403,
        'name': 'Pulkovo_1942_GK_Zone_3'
    },
    47003: {
        'epsg': 28404,
        'name': 'Pulkovo 1942 / Gauss-Kruger zone 4'
    },
    48001: {
        'epsg': 2180,
        'name': 'ETRS89 / Poland CS92'
    },
    48002: {
        'epsg': 2176,
        'name': 'ETRS89 / Poland CS2000 zone 5'
    },
    48003: {
        'epsg': 2177,
        'name': 'ETRS89 / Poland CS2000 zone 6'
    },
    48004: {
        'epsg': 2178,
        'name': 'ETRS89 / Poland CS2000 zone 7'
    },
    48005: {
        'epsg': 2179,
        'name': 'ETRS89 / Poland CS2000 zone 8'
    },
    49000: {
        'epsg': 23700,
        'name': 'HD72 / EOV'
    },
    50001: {
        'epsg': 26929,
        'name': 'NAD83 / Alabama East'
    },
    50002: {
        'epsg': 26930,
        'name': 'NAD83 / Alabama West'
    },
    50004: {
        'epsg': 26932,
        'name': 'NAD83 / Alaska zone 2'
    },
    50005: {
        'epsg': 26933,
        'name': 'NAD83 / Alaska zone 3'
    },
    50006: {
        'epsg': 26934,
        'name': 'NAD83 / Alaska zone 4'
    },
    50007: {
        'epsg': 26935,
        'name': 'NAD83 / Alaska zone 5'
    },
    50008: {
        'epsg': 26936,
        'name': 'NAD83 / Alaska zone 6'
    },
    50009: {
        'epsg': 26937,
        'name': 'NAD83 / Alaska zone 7'
    },
    50010: {
        'epsg': 26938,
        'name': 'NAD83 / Alaska zone 8'
    },
    50011: {
        'epsg': 26939,
        'name': 'NAD83 / Alaska zone 9'
    },
    50012: {
        'epsg': 26940,
        'name': 'NAD83 / Alaska zone 10'
    },
    50013: {
        'epsg': 26948,
        'name': 'NAD83 / Arizona East'
    },
    50014: {
        'epsg': 26949,
        'name': 'NAD83 / Arizona Central'
    },
    50015: {
        'epsg': 26950,
        'name': 'NAD83 / Arizona West'
    },
    50016: {
        'epsg': 26951,
        'name': 'NAD83 / Arkansas North'
    },
    50017: {
        'epsg': 26952,
        'name': 'NAD83 / Arkansas South'
    },
    50018: {
        'epsg': 26941,
        'name': 'NAD83 / California zone 1'
    },
    50019: {
        'epsg': 26942,
        'name': 'NAD83 / California zone 2'
    },
    50020: {
        'epsg': 26943,
        'name': 'NAD83 / California zone 3'
    },
    50021: {
        'epsg': 26944,
        'name': 'NAD83 / California zone 4'
    },
    50022: {
        'epsg': 26945,
        'name': 'NAD83 / California zone 5'
    },
    50023: {
        'epsg': 26946,
        'name': 'NAD83 / California zone 6'
    },
    50024: {
        'epsg': 26953,
        'name': 'NAD83 / Colorado North'
    },
    50025: {
        'epsg': 26954,
        'name': 'NAD83 / Colorado Central'
    },
    50026: {
        'epsg': 26955,
        'name': 'NAD83 / Colorado South'
    },
    50027: {
        'epsg': 26956,
        'name': 'NAD83 / Connecticut'
    },
    50028: {
        'epsg': 26957,
        'name': 'NAD83 / Delaware'
    },
    50029: {
        'epsg': 26958,
        'name': 'NAD83 / Florida East'
    },
    50030: {
        'epsg': 26959,
        'name': 'NAD83 / Florida West'
    },
    50031: {
        'epsg': 26960,
        'name': 'NAD83 / Florida North'
    },
    50032: {
        'epsg': 26966,
        'name': 'NAD83 / Georgia East'
    },
    50033: {
        'epsg': 26967,
        'name': 'NAD83 / Georgia West'
    },
    50034: {
        'epsg': 26961,
        'name': 'NAD83 / Hawaii zone 1'
    },
    50035: {
        'epsg': 26962,
        'name': 'NAD83 / Hawaii zone 2'
    },
    50036: {
        'epsg': 26963,
        'name': 'NAD83 / Hawaii zone 3'
    },
    50037: {
        'epsg': 26964,
        'name': 'NAD83 / Hawaii zone 4'
    },
    50038: {
        'epsg': 26965,
        'name': 'NAD83 / Hawaii zone 5'
    },
    50039: {
        'epsg': 26968,
        'name': 'NAD83 / Idaho East'
    },
    50040: {
        'epsg': 26969,
        'name': 'NAD83 / Idaho Central'
    },
    50041: {
        'epsg': 26970,
        'name': 'NAD83 / Idaho West'
    },
    50042: {
        'epsg': 26971,
        'name': 'NAD83 / Illinois East'
    },
    50043: {
        'epsg': 26972,
        'name': 'NAD83 / Illinois West'
    },
    50044: {
        'epsg': 26973,
        'name': 'NAD83 / Indiana East'
    },
    50045: {
        'epsg': 26974,
        'name': 'NAD83 / Indiana West'
    },
    50046: {
        'epsg': 26975,
        'name': 'NAD83 / Iowa North'
    },
    50047: {
        'epsg': 26976,
        'name': 'NAD83 / Iowa South'
    },
    50048: {
        'epsg': 26977,
        'name': 'NAD83 / Kansas North'
    },
    50049: {
        'epsg': 26978,
        'name': 'NAD83 / Kansas South'
    },
    50050: {
        'epsg': 26979,
        'name': 'NAD_1983_StatePlane_Kentucky_North_FIPS_1601'
    },  # EPSG-Code not found
    50051: {
        'epsg': 26980,
        'name': 'NAD83 / Kentucky South'
    },
    50052: {
        'epsg': 26981,
        'name': 'NAD83 / Louisiana North'
    },
    50053: {
        'epsg': 26982,
        'name': 'NAD83 / Louisiana South'
    },
    50054: {
        'epsg': 32199,
        'name': 'NAD83 / Louisiana Offshore'
    },
    50055: {
        'epsg': 26983,
        'name': 'NAD83 / Maine East'
    },
    50056: {
        'epsg': 26984,
        'name': 'NAD83 / Maine West'
    },
    50057: {
        'epsg': 26985,
        'name': 'NAD83 / Maryland'
    },
    50058: {
        'epsg': 26986,
        'name': 'NAD83 / Massachusetts Mainland'
    },
    50059: {
        'epsg': 26987,
        'name': 'NAD83 / Massachusetts Island'
    },
    50060: {
        'epsg': 26988,
        'name': 'NAD83 / Michigan North'
    },
    50061: {
        'epsg': 26989,
        'name': 'NAD83 / Michigan Central'
    },
    50062: {
        'epsg': 26990,
        'name': 'NAD83 / Michigan South'
    },
    50063: {
        'epsg': 26991,
        'name': 'NAD83 / Minnesota North'
    },
    50064: {
        'epsg': 26992,
        'name': 'NAD83 / Minnesota Central'
    },
    50065: {
        'epsg': 26993,
        'name': 'NAD83 / Minnesota South'
    },
    50066: {
        'epsg': 26994,
        'name': 'NAD83 / Mississippi East'
    },
    50067: {
        'epsg': 26995,
        'name': 'NAD83 / Mississippi West'
    },
    50068: {
        'epsg': 26996,
        'name': 'NAD83 / Missouri East'
    },
    50069: {
        'epsg': 26997,
        'name': 'NAD83 / Missouri Central'
    },
    50070: {
        'epsg': 26998,
        'name': 'NAD83 / Missouri West'
    },
    50071: {
        'epsg': 32100,
        'name': 'NAD83 / Montana'
    },
    50072: {
        'epsg': 32104,
        'name': 'NAD83 / Nebraska'
    },
    50073: {
        'epsg': 32107,
        'name': 'NAD83 / Nevada East'
    },
    50074: {
        'epsg': 32108,
        'name': 'NAD83 / Nevada Central'
    },
    50075: {
        'epsg': 32109,
        'name': 'NAD83 / Nevada West'
    },
    50076: {
        'epsg': 32110,
        'name': 'NAD83 / New Hampshire'
    },
    50077: {
        'epsg': 32111,
        'name': 'NAD83 / New Jersey'
    },
    50078: {
        'epsg': 32112,
        'name': 'NAD83 / New Mexico East'
    },
    50079: {
        'epsg': 32113,
        'name': 'NAD83 / New Mexico Central'
    },
    50080: {
        'epsg': 32114,
        'name': 'NAD83 / New Mexico West'
    },
    50081: {
        'epsg': 32115,
        'name': 'NAD83 / New York East'
    },
    50082: {
        'epsg': 32116,
        'name': 'NAD83 / New York Central'
    },
    50083: {
        'epsg': 32117,
        'name': 'NAD83 / New York West'
    },
    50084: {
        'epsg': 32118,
        'name': 'NAD83 / New York Long Island'
    },
    50085: {
        'epsg': 32119,
        'name': 'NAD83 / North Carolina'
    },
    50086: {
        'epsg': 32120,
        'name': 'NAD83 / North Dakota North'
    },
    50087: {
        'epsg': 32121,
        'name': 'NAD83 / North Dakota South'
    },
    50088: {
        'epsg': 32122,
        'name': 'NAD83 / Ohio North'
    },
    50089: {
        'epsg': 32123,
        'name': 'NAD83 / Ohio South'
    },
    50090: {
        'epsg': 32124,
        'name': 'NAD83 / Oklahoma North'
    },
    50091: {
        'epsg': 32125,
        'name': 'NAD83 / Oklahoma South'
    },
    50092: {
        'epsg': 32126,
        'name': 'NAD83 / Oregon North'
    },
    50093: {
        'epsg': 32127,
        'name': 'NAD83 / Oregon South'
    },
    50094: {
        'epsg': 32128,
        'name': 'NAD83 / Pennsylvania North'
    },
    50095: {
        'epsg': 32129,
        'name': 'NAD83 / Pennsylvania South'
    },
    50096: {
        'epsg': 32130,
        'name': 'NAD83 / Rhode Island'
    },
    50097: {
        'epsg': 32133,
        'name': 'NAD83 / South Carolina'
    },
    50098: {
        'epsg': 32134,
        'name': 'NAD83 / South Dakota North'
    },
    50099: {
        'epsg': 32135,
        'name': 'NAD83 / South Dakota South'
    },
    50100: {
        'epsg': 32136,
        'name': 'NAD83 / Tennessee'
    },
    50101: {
        'epsg': 32137,
        'name': 'NAD83 / Texas North'
    },
    50102: {
        'epsg': 32138,
        'name': 'NAD83 / Texas North Central'
    },
    50103: {
        'epsg': 32139,
        'name': 'NAD83 / Texas Central'
    },
    50104: {
        'epsg': 32140,
        'name': 'NAD83 / Texas South Central'
    },
    50105: {
        'epsg': 32141,
        'name': 'NAD83 / Texas South'
    },
    50106: {
        'epsg': 32142,
        'name': 'NAD83 / Utah North'
    },
    50107: {
        'epsg': 32143,
        'name': 'NAD83 / Utah Central'
    },
    50108: {
        'epsg': 32144,
        'name': 'NAD83 / Utah South'
    },
    50109: {
        'epsg': 32145,
        'name': 'NAD83 / Vermont'
    },
    50110: {
        'epsg': 32146,
        'name': 'NAD83 / Virginia North'
    },
    50111: {
        'epsg': 32147,
        'name': 'NAD83 / Virginia South'
    },
    50112: {
        'epsg': 32148,
        'name': 'NAD83 / Washington North'
    },
    50113: {
        'epsg': 32149,
        'name': 'NAD83 / Washington South'
    },
    50114: {
        'epsg': 32150,
        'name': 'NAD83 / West Virginia North'
    },
    50115: {
        'epsg': 32151,
        'name': 'NAD83 / West Virginia South'
    },
    50116: {
        'epsg': 32152,
        'name': 'NAD83 / Wisconsin North'
    },
    50117: {
        'epsg': 32153,
        'name': 'NAD83 / Wisconsin Central'
    },
    50118: {
        'epsg': 32154,
        'name': 'NAD83 / Wisconsin South'
    },
    50119: {
        'epsg': 32155,
        'name': 'NAD83 / Wyoming East'
    },
    50120: {
        'epsg': 32156,
        'name': 'NAD83 / Wyoming East Central'
    },
    50121: {
        'epsg': 32157,
        'name': 'NAD83 / Wyoming West Central'
    },
    50122: {
        'epsg': 32158,
        'name': 'NAD83 / Wyoming West'
    },
    50123: {
        'epsg': 32158,
        'name': 'NAD83 / Wyoming West'
    },
    51000: {
        'epsg': 0,
        'name': 'Gabon Datum GRS_1980'
    },  # EPSG-Code not found
    52001: {
        'epsg': 0,
        'name': 'Brazil UTM Corrego Alegre Fuso 18'
    },  # EPSG-Code not found
    52002: {
        'epsg': 0,
        'name': 'Brazil UTM Corrego Alegre Fuso 19'
    },  # EPSG-Code not found
    52003: {
        'epsg': 0,
        'name': 'Brazil UTM Corrego Alegre Fuso 20'
    },  # EPSG-Code not found
    52004: {
        'epsg': 22521,
        'name': 'Corrego Alegre 1970-72 / UTM zone 21S'
    },
    52005: {
        'epsg': 22522,
        'name': 'Corrego Alegre 1970-72 / UTM zone 22S'
    },
    52006: {
        'epsg': 22523,
        'name': 'Corrego Alegre 1970-72 / UTM zone 23S'
    },
    52007: {
        'epsg': 22524,
        'name': 'Corrego Alegre 1970-72 / UTM zone 24S'
    },
    52008: {
        'epsg': 22525,
        'name': 'Corrego Alegre 1970-72 / UTM zone 25S'
    },
    52009: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 18'
    },  # EPSG-Code not found
    52010: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 19'
    },  # EPSG-Code not found
    52011: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 20'
    },  # EPSG-Code not found
    52012: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 21'
    },  # EPSG-Code not found
    52013: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 22'
    },  # EPSG-Code not found
    52014: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 23'
    },  # EPSG-Code not found
    52015: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 24'
    },  # EPSG-Code not found
    52016: {
        'epsg': 0,
        'name': 'Brazil UTM SAD69 Fuso 25'
    },  # EPSG-Code not found
    52017: {
        'epsg': 31978,
        'name': 'SIRGAS 2000 / UTM zone 18S'
    },
    52018: {
        'epsg': 31979,
        'name': 'SIRGAS 2000 / UTM zone 19S'
    },
    52019: {
        'epsg': 31980,
        'name': 'SIRGAS 2000 / UTM zone 20S'
    },
    52020: {
        'epsg': 31981,
        'name': 'SIRGAS 2000 / UTM zone 21S'
    },
    52021: {
        'epsg': 31982,
        'name': 'SIRGAS 2000 / UTM zone 22S'
    },
    52022: {
        'epsg': 31983,
        'name': 'SIRGAS 2000 / UTM zone 23S'
    },
    52023: {
        'epsg': 31984,
        'name': 'SIRGAS 2000 / UTM zone 24S'
    },
    52024: {
        'epsg': 31985,
        'name': 'SIRGAS 2000 / UTM zone 25S'
    },
    53000: {
        'epsg': 2039,
        'name': 'Israel 1993 / Israeli TM Grid'
    },
    54001: {
        'epsg': 3375,
        'name': 'GDM2000 / Peninsula RSO'
    },
    54002: {
        'epsg': 3376,
        'name': 'GDM2000 / East Malaysia BRSO'
    },
    55000: {
        'epsg': 0,
        'name': 'UserDefined Lambert'
    },  # EPSG-Code not found
    56000: {
        'epsg': 900913,
        'name': 'Google Mercator'
    },  # EPSG-Code not found
    57000: {
        'epsg': 2041,
        'name': 'Abidjan 1987 / UTM zone 30N'
    },
    58001: {
        'epsg': 0,
        'name': 'Sri Lanka Datum 1999'
    },  # EPSG-Code not found
    58002: {
        'epsg': 0,
        'name': 'Sri Lanka Datum 1999'
    },  # EPSG-Code not found
    60000: {
        'epsg': 0,
        'name': 'UserDefined'
    },  # EPSG-Code not found
    61000: {
        'epsg': 2326,
        'name': 'Hong Kong 1980 Grid System'
    },
    62001: {
        'epsg': 26901,
        'name': 'NAD83 / UTM zone 1N'
    },
    62002: {
        'epsg': 26902,
        'name': 'NAD83 / UTM zone 2N'
    },
    62004: {
        'epsg': 26903,
        'name': 'NAD83 / UTM zone 3N'
    },
    62005: {
        'epsg': 26904,
        'name': 'NAD83 / UTM zone 4N'
    },
    62006: {
        'epsg': 26905,
        'name': 'NAD83 / UTM zone 5N'
    },
    62007: {
        'epsg': 26906,
        'name': 'NAD83 / UTM zone 6N'
    },
    62008: {
        'epsg': 26907,
        'name': 'NAD83 / UTM zone 7N'
    },
    62009: {
        'epsg': 26908,
        'name': 'NAD83 / UTM zone 8N'
    },
    62010: {
        'epsg': 26909,
        'name': 'NAD83 / UTM zone 9N'
    },
    62011: {
        'epsg': 26910,
        'name': 'NAD83 / UTM zone 10N'
    },
    62012: {
        'epsg': 26911,
        'name': 'NAD83 / UTM zone 11N'
    },
    62013: {
        'epsg': 26912,
        'name': 'NAD83 / UTM zone 12N'
    },
    62014: {
        'epsg': 26913,
        'name': 'NAD83 / UTM zone 13N'
    },
    62015: {
        'epsg': 26914,
        'name': 'NAD83 / UTM zone 14N'
    },
    62016: {
        'epsg': 26915,
        'name': 'NAD83 / UTM zone 15N'
    },
    62017: {
        'epsg': 26916,
        'name': 'NAD83 / UTM zone 16N'
    },
    62018: {
        'epsg': 26917,
        'name': 'NAD83 / UTM zone 17N'
    },
    62019: {
        'epsg': 26918,
        'name': 'NAD83 / UTM zone 18N'
    },
    62020: {
        'epsg': 26919,
        'name': 'NAD83 / UTM zone 19N'
    },
    62021: {
        'epsg': 26920,
        'name': 'NAD83 / UTM zone 20N'
    },
    62022: {
        'epsg': 26921,
        'name': 'NAD83 / UTM zone 21N'
    },
    62023: {
        'epsg': 26922,
        'name': 'NAD83 / UTM zone 22N'
    },
    62024: {
        'epsg': 26923,
        'name': 'NAD83 / UTM zone 23N'
    },
    63001: {
        'epsg': 25828,
        'name': 'ETRS89 / UTM zone 28N'
    },
    63002: {
        'epsg': 25829,
        'name': 'ETRS89 / UTM zone 29N'
    },
    63003: {
        'epsg': 25830,
        'name': 'ETRS89 / UTM zone 30N'
    },
    63004: {
        'epsg': 25831,
        'name': 'ETRS89 / UTM zone 31N'
    },
    63005: {
        'epsg': 25832,
        'name': 'ETRS89 / UTM zone 32N'
    },
    63006: {
        'epsg': 25833,
        'name': 'ETRS89 / UTM zone 33N'
    },
    63007: {
        'epsg': 25834,
        'name': 'ETRS89 / UTM zone 34N'
    },
    63008: {
        'epsg': 25835,
        'name': 'ETRS89 / UTM zone 35N'
    },
    63009: {
        'epsg': 25836,
        'name': 'ETRS89 / UTM zone 36N'
    },
    63010: {
        'epsg': 25837,
        'name': 'ETRS89 / UTM zone 37N'
    },
    63011: {
        'epsg': 25838,
        'name': 'ETRS_1989_UTM_Zone_38N'
    },  # EPSG-Code not found
    64000: {
        'epsg': 3785,
        'name': ''
    },  # EPSG-Code not found
    65000: {
        'epsg': 3857,
        'name': 'WGS 84 / Pseudo-Mercator'
    },
    66001: {
        'epsg': 102629,
        'name': 'NAD_1983_StatePlane_Alabama_East_FIPS_0101_Feet'
    },  # EPSG-Code not found
    66002: {
        'epsg': 102630,
        'name': 'NAD_1983_StatePlane_Alabama_West_FIPS_0102_Feet'
    },  # EPSG-Code not found
    66013: {
        'epsg': 2222,
        'name': 'NAD83 / Arizona East (ft)'
    },
    66014: {
        'epsg': 2223,
        'name': 'NAD83 / Arizona Central (ft)'
    },
    66015: {
        'epsg': 2224,
        'name': 'NAD83 / Arizona West (ft)'
    },
    66016: {
        'epsg': 3433,
        'name': 'NAD83 / Arkansas North (ftUS)'
    },
    66017: {
        'epsg': 3434,
        'name': 'NAD83 / Arkansas South (ftUS)'
    },
    66018: {
        'epsg': 2225,
        'name': 'NAD83 / California zone 1 (ftUS)'
    },
    66019: {
        'epsg': 2226,
        'name': 'NAD83 / California zone 2 (ftUS)'
    },
    66020: {
        'epsg': 2227,
        'name': 'NAD83 / California zone 3 (ftUS)'
    },
    66021: {
        'epsg': 2228,
        'name': 'NAD83 / California zone 4 (ftUS)'
    },
    66022: {
        'epsg': 2229,
        'name': 'NAD83 / California zone 5 (ftUS)'
    },
    66023: {
        'epsg': 2230,
        'name': 'NAD83 / California zone 6 (ftUS)'
    },
    66024: {
        'epsg': 2231,
        'name': 'NAD83 / Colorado North (ftUS)'
    },
    66025: {
        'epsg': 2232,
        'name': 'NAD83 / Colorado Central (ftUS)'
    },
    66026: {
        'epsg': 2233,
        'name': 'NAD83 / Colorado South (ftUS)'
    },
    66027: {
        'epsg': 2234,
        'name': 'NAD83 / Connecticut (ftUS)'
    },
    66028: {
        'epsg': 2235,
        'name': 'NAD83 / Delaware (ftUS)'
    },
    66029: {
        'epsg': 2236,
        'name': 'NAD83 / Florida East (ftUS)'
    },
    66030: {
        'epsg': 2237,
        'name': 'NAD83 / Florida West (ftUS)'
    },
    66031: {
        'epsg': 2238,
        'name': 'NAD83 / Florida North (ftUS)'
    },
    66032: {
        'epsg': 2239,
        'name': 'NAD83 / Georgia East (ftUS)'
    },
    66033: {
        'epsg': 2240,
        'name': 'NAD83 / Georgia West (ftUS)'
    },
    66036: {
        'epsg': 3759,
        'name': 'NAD83 / Hawaii zone 3 (ftUS)'
    },
    66039: {
        'epsg': 2241,
        'name': 'NAD83 / Idaho East (ftUS)'
    },
    66040: {
        'epsg': 2242,
        'name': 'NAD83 / Idaho Central (ftUS)'
    },
    66041: {
        'epsg': 2243,
        'name': 'NAD83 / Idaho West (ftUS)'
    },
    66042: {
        'epsg': 3435,
        'name': 'NAD83 / Illinois East (ftUS)'
    },
    66043: {
        'epsg': 3436,
        'name': 'NAD83 / Illinois West (ftUS)'
    },
    66044: {
        'epsg': 2244,
        'name': ''
    },  # EPSG-Code not found
    66045: {
        'epsg': 2245,
        'name': ''
    },  # EPSG-Code not found
    66046: {
        'epsg': 3417,
        'name': 'NAD83 / Iowa North (ftUS)'
    },
    66047: {
        'epsg': 3418,
        'name': 'NAD83 / Iowa South (ftUS)'
    },
    66048: {
        'epsg': 3419,
        'name': 'NAD83 / Kansas North (ftUS)'
    },
    66049: {
        'epsg': 3420,
        'name': 'NAD83 / Kansas South (ftUS)'
    },
    66050: {
        'epsg': 2246,
        'name': 'NAD83 / Kentucky North (ftUS)'
    },
    66051: {
        'epsg': 2247,
        'name': 'NAD83 / Kentucky South (ftUS)'
    },
    66052: {
        'epsg': 3451,
        'name': 'NAD83 / Louisiana North (ftUS)'
    },
    66053: {
        'epsg': 3452,
        'name': 'NAD83 / Louisiana South (ftUS)'
    },
    66054: {
        'epsg': 3453,
        'name': 'NAD83 / Louisiana Offshore (ftUS)'
    },
    66055: {
        'epsg': 26847,
        'name': 'NAD83 / Maine East (ftUS)'
    },
    66056: {
        'epsg': 26848,
        'name': 'NAD83 / Maine West (ftUS)'
    },
    66057: {
        'epsg': 2248,
        'name': 'NAD83 / Maryland (ftUS)'
    },
    66058: {
        'epsg': 2249,
        'name': 'NAD83 / Massachusetts Mainland (ftUS)'
    },
    66059: {
        'epsg': 2250,
        'name': 'NAD83 / Massachusetts Island (ftUS)'
    },
    66060: {
        'epsg': 2251,
        'name': 'NAD83 / Michigan North (ft)'
    },
    66061: {
        'epsg': 2252,
        'name': 'NAD83 / Michigan Central (ft)'
    },
    66062: {
        'epsg': 2253,
        'name': 'NAD83 / Michigan South (ft)'
    },
    66063: {
        'epsg': 26849,
        'name': 'NAD83 / Minnesota North (ftUS)'
    },
    66064: {
        'epsg': 26850,
        'name': 'NAD83 / Minnesota Central (ftUS)'
    },
    66065: {
        'epsg': 26851,
        'name': 'NAD83 / Minnesota South (ftUS)'
    },
    66066: {
        'epsg': 2254,
        'name': 'NAD83 / Mississippi East (ftUS)'
    },
    66067: {
        'epsg': 2255,
        'name': 'NAD83 / Mississippi West (ftUS)'
    },
    66068: {
        'epsg': 102696,
        'name': 'NAD_1983_StatePlane_Missouri_East_FIPS_2401_Feet'
    },  # EPSG-Code not found
    66069: {
        'epsg': 102697,
        'name': 'NAD_1983_StatePlane_Missouri_Central_FIPS_2402_Feet'
    },  # EPSG-Code not found
    66070: {
        'epsg': 102698,
        'name': 'NAD_1983_StatePlane_Missouri_West_FIPS_2403_Feet'
    },  # EPSG-Code not found
    66071: {
        'epsg': 2256,
        'name': 'NAD83 / Montana (ft)'
    },
    66072: {
        'epsg': 26852,
        'name': 'NAD83 / Nebraska (ftUS)'
    },
    66073: {
        'epsg': 3421,
        'name': 'NAD83 / Nevada East (ftUS)'
    },
    66074: {
        'epsg': 3422,
        'name': 'NAD83 / Nevada Central (ftUS)'
    },
    66075: {
        'epsg': 3423,
        'name': 'NAD83 / Nevada West (ftUS)'
    },
    66076: {
        'epsg': 3437,
        'name': 'NAD83 / New Hampshire (ftUS)'
    },
    66077: {
        'epsg': 3424,
        'name': 'NAD83 / New Jersey (ftUS)'
    },
    66078: {
        'epsg': 2257,
        'name': 'NAD83 / New Mexico East (ftUS)'
    },
    66079: {
        'epsg': 2258,
        'name': 'NAD83 / New Mexico Central (ftUS)'
    },
    66080: {
        'epsg': 2259,
        'name': 'NAD83 / New Mexico West (ftUS)'
    },
    66081: {
        'epsg': 2260,
        'name': 'NAD83 / New York East (ftUS)'
    },
    66082: {
        'epsg': 2261,
        'name': 'NAD83 / New York Central (ftUS)'
    },
    66083: {
        'epsg': 2262,
        'name': 'NAD83 / New York West (ftUS)'
    },
    66084: {
        'epsg': 2263,
        'name': 'NAD83 / New York Long Island (ftUS)'
    },
    66085: {
        'epsg': 2264,
        'name': 'NAD83 / North Carolina (ftUS)'
    },
    66086: {
        'epsg': 2265,
        'name': 'NAD83 / North Dakota North (ft)'
    },
    66087: {
        'epsg': 2266,
        'name': 'NAD83 / North Dakota South (ft)'
    },
    66088: {
        'epsg': 3734,
        'name': 'NAD83 / Ohio North (ftUS)'
    },
    66089: {
        'epsg': 3735,
        'name': 'NAD83 / Ohio South (ftUS)'
    },
    66090: {
        'epsg': 2267,
        'name': 'NAD83 / Oklahoma North (ftUS)'
    },
    66091: {
        'epsg': 2268,
        'name': 'NAD83 / Oklahoma South (ftUS)'
    },
    66092: {
        'epsg': 2269,
        'name': 'NAD83 / Oregon North (ft)'
    },
    66093: {
        'epsg': 2270,
        'name': 'NAD83 / Oregon South (ft)'
    },
    66094: {
        'epsg': 2271,
        'name': 'NAD83 / Pennsylvania North (ftUS)'
    },
    66095: {
        'epsg': 2272,
        'name': 'NAD83 / Pennsylvania South (ftUS)'
    },
    66096: {
        'epsg': 3438,
        'name': 'NAD83 / Rhode Island (ftUS)'
    },
    66097: {
        'epsg': 2273,
        'name': 'NAD83 / South Carolina (ft)'
    },
    66098: {
        'epsg': 3454,
        'name': ''
    },  # EPSG-Code not found
    66099: {
        'epsg': 3455,
        'name': 'NAD83 / South Dakota South (ftUS)'
    },
    66100: {
        'epsg': 2274,
        'name': 'NAD83 / Tennessee (ftUS)'
    },
    66101: {
        'epsg': 2275,
        'name': 'NAD83 / Texas North (ftUS)'
    },
    66102: {
        'epsg': 2276,
        'name': 'NAD83 / Texas North Central (ftUS)'
    },
    66103: {
        'epsg': 2277,
        'name': 'NAD83 / Texas Central (ftUS)'
    },
    66104: {
        'epsg': 2278,
        'name': 'NAD83 / Texas South Central (ftUS)'
    },
    66105: {
        'epsg': 2279,
        'name': 'NAD83 / Texas South (ftUS)'
    },
    66106: {
        'epsg': 3560,
        'name': 'NAD83 / Utah North (ftUS)'
    },
    66107: {
        'epsg': 3566,
        'name': 'NAD83 / Utah Central (ftUS)'
    },
    66108: {
        'epsg': 3567,
        'name': 'NAD83 / Utah South (ftUS)'
    },
    66109: {
        'epsg': 102745,
        'name': 'NAD_1983_StatePlane_Vermont_FIPS_4400_Feet'
    },  # EPSG-Code not found
    66110: {
        'epsg': 2283,
        'name': 'NAD83 / Virginia North (ftUS)'
    },
    66111: {
        'epsg': 2284,
        'name': 'NAD83 / Virginia South (ftUS)'
    },
    66112: {
        'epsg': 2285,
        'name': 'NAD83 / Washington North (ftUS)'
    },
    66113: {
        'epsg': 2286,
        'name': 'NAD83 / Washington South (ftUS)'
    },
    66114: {
        'epsg': 26853,
        'name': 'NAD83 / West Virginia North (ftUS)'
    },
    66115: {
        'epsg': 26854,
        'name': 'NAD83 / West Virginia South (ftUS)'
    },
    66116: {
        'epsg': 2287,
        'name': 'NAD83 / Wisconsin North (ftUS)'
    },
    66117: {
        'epsg': 2288,
        'name': 'NAD83 / Wisconsin Central (ftUS)'
    },
    66118: {
        'epsg': 2289,
        'name': 'NAD83 / Wisconsin South (ftUS)'
    },
    66119: {
        'epsg': 3736,
        'name': 'NAD83 / Wyoming East (ftUS)'
    },
    66120: {
        'epsg': 3737,
        'name': 'NAD83 / Wyoming East Central (ftUS)'
    },
    66121: {
        'epsg': 3738,
        'name': 'NAD83 / Wyoming West Central (ftUS)'
    },
    66122: {
        'epsg': 3739,
        'name': 'NAD83 / Wyoming West (ftUS)'
    },
    66123: {
        'epsg': 102761,
        'name': 'NAD_1983_StatePlane_Puerto_Rico_Virgin_Islands_FIPS_5200_Feet'
    },  # EPSG-Code not found
    67000: {
        'epsg': 7392,
        'name': 'Kosovo'
    },  # EPSG-Code not found
    68000: {
        'epsg': 21037,
        'name': 'Arc 1960 / UTM zone 37S'
    },
    69000: {
        'epsg': 2586,
        'name': 'Pulkovo 1942 / 3-degree Gauss-Kruger CM 33E'
    },
    70000: {
        'epsg': 2019,
        'name': 'NAD27(76) / MTM zone 10'
    }
}
