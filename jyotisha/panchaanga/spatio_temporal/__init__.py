#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import os
import sys

import swisseph as swe

from jyotisha.custom_transliteration import sexastr2deci
from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

# from scipy.optimize import brentq

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Defining "bits" for rsmi in swe.rise_trans per documentation on https://www.astro.com/swisseph/swephprg.htm#_Toc505244865

#     The variable rsmi can have the following values:

#     /* for swe_rise_trans() and swe_rise_trans_true_hor() */
#     #define SE_CALC_RISE            1
#     #define SE_CALC_SET             2
#     #define SE_CALC_MTRANSIT   4       /* upper meridian transit (southern for northern geo. latitudes) */
#     #define SE_CALC_ITRANSIT     8       /* lower meridian transit (northern, below the horizon) */
#     /* the following bits can be added (or’ed) to SE_CALC_RISE or SE_CALC_SET */
#     #define SE_BIT_DISC_CENTER         256     /* for rising or setting of disc center */
#     #define SE_BIT_DISC_BOTTOM      8192     /* for rising or setting of lower limb of disc */
#     #define SE_BIT_GEOCTR_NO_ECL_LAT 128 /* use topocentric position of object and ignore its ecliptic latitude */
#     #define SE_BIT_NO_REFRACTION    512      /* if refraction is not to be considered */
#     #define SE_BIT_CIVIL_TWILIGHT    1024    /* in order to calculate civil twilight */
#     #define SE_BIT_NAUTIC_TWILIGHT 2048    /* in order to calculate nautical twilight */
#     #define SE_BIT_ASTRO_TWILIGHT   4096    /* in order to calculate astronomical twilight */
#     #define SE_BIT_FIXED_DISC_SIZE (16*1024) /* neglect the effect of distance on disc size */
#     #define SE_BIT_HINDU_RISING (SE_BIT_DISC_CENTER|SE_BIT_NO_REFRACTION|SE_BIT_GEOCTR_NO_ECL_LAT)
#                                                                      /* risings according to Hindu astrology */

CALC_RISE = 897  # 512 + 256 + 128 + 1
CALC_SET = 898  # 512 + 256 + 128 + 2


class City(JsonObject):
  """This class enables the construction of a city object
    """

  def __init__(self, name, latitude, longitude, timezone):
    """Constructor for city"""
    super(City, self).__init__()
    if name is None or name == "":
      self.name = str([latitude, longitude])
    else:
      self.name = name
    if ":" in str(latitude):
      self.latitude = sexastr2deci(latitude)
      self.longitude = sexastr2deci(longitude)
    else:
      self.latitude = float(latitude)
      self.longitude = float(longitude)
    self.timezone = timezone

  def get_timezone_obj(self):
    from jyotisha.panchaanga.temporal.time import Timezone
    return Timezone(timezone_id=self.timezone)

  @classmethod
  def from_address(cls, address, api_key, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.GoogleV3(api_key=api_key, timeout=timeout)
    location = geolocator.geocode(address)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude,
                timezone=location.timezone().zone)
    return city

  @classmethod
  def from_address_and_timezone(cls, address, timezone_str, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.ArcGIS()
    location = geolocator.geocode(query=address, timeout=timeout)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude, timezone=timezone_str)
    return city

  @classmethod
  def get_city_from_db(cls, name):
    import pandas
    df = pandas.read_csv(os.path.join(os.path.dirname(__file__), "data", "places_lat_lon_tz_db.tsv"), sep="\t", index_col="Name")
    city = City(name=name, latitude=df.at[name, "Lat"], longitude=df.at[name, "Long"], timezone=df.at[name, "Timezone"])
    return city

  def __repr__(self):
    return self.name

  def get_rising_time(self, julian_day_start, body):
    from jyotisha.panchaanga.temporal.body import Graha
    graha = Graha.singleton(body)
    # rise_trans expects UT time
    return swe.rise_trans(
      jd_start=julian_day_start, body=graha._get_swisseph_id(),
      lon=self.longitude, lat=self.latitude,
      rsmi=CALC_RISE)[1][0]

  def get_setting_time(self, julian_day_start, body):
    from jyotisha.panchaanga.temporal.body import Graha
    graha = Graha.singleton(body)
    # rise_trans expects UT time
    return swe.rise_trans(
      jd_start=julian_day_start, body=graha._get_swisseph_id(),
      lon=self.longitude, lat=self.latitude,
      rsmi=CALC_SET)[1][0]

  def get_solar_eclipse_time(self, jd_start):
    return swe.sol_eclipse_when_loc(julday=jd_start, lon=self.longitude, lat=self.latitude)

  def get_lunar_eclipse_time(self, jd_start):
    return swe.lun_eclipse_when_loc(jd_start, lon=self.longitude, lat=self.latitude)

  def get_zodiac_longitude_eastern_horizon(self, jd):
    """ Get the ID of the raashi what is currently rising.
    
    :param jd: 
    :return: 
    """
    return swe.houses_ex(jd, self.latitude, self.longitude)[1][0]

  def get_lagna_float(self, jd, offset=0, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, debug=False):
    """Returns the rising rAshi at a given location.

      Args:
        :param jd: The Julian Day at which the lagnam is to be computed
        :param offset: Used by internal functions for bracketing
        :param debug

      Returns:
        float lagna
    """

    lcalc = self.get_zodiac_longitude_eastern_horizon(jd=jd) - Ayanamsha.singleton(ayanaamsha_id=ayanaamsha_id).get_offset(jd=jd)
    lcalc = lcalc % 360

    if offset == 0:
      return lcalc / 30

    else:
      if debug:
        logging.debug(debug)
        logging.debug(('offset:', offset))
        logging.debug(('lcalc/30', lcalc / 30))
        logging.debug(('lcalc/30 + offset = ', lcalc / 30 + offset))

      # The max expected value is somewhere between 2 and -2, with bracketing

      if (lcalc / 30 + offset) >= 3:
        return (lcalc / 30) + offset - 12
      elif (lcalc / 30 + offset) <= -3:
        return (lcalc / 30)
      else:
        return (lcalc / 30) + offset

  def get_sunsets_in_period(self, jd_start, jd_end):
    if jd_start > jd_end:
      raise ValueError((jd_start, jd_end))
    jd = jd_start
    sunset_jds = []
    while jd < jd_end:
      from jyotisha.panchaanga.temporal.body import Graha
      jd_setting = self.get_setting_time(julian_day_start=jd, body=Graha.SUN)
      if jd_setting < jd_end:
        sunset_jds.append(jd_setting)
      # Assume that night lasts atleast 30 minutes!
      jd = jd_setting + 1/48.0
    return sunset_jds


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  import doctest

  doctest.testmod(verbose=True)
