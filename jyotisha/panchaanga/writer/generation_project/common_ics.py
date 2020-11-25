import os

import jyotisha
from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer import ics

output_dir = os.path.join(os.path.dirname(jyotisha.__file__), "output")


def dump_common(year, city):
  computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
  tropical_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=year, computation_system=computation_system)
  ics_calendar = ics.compute_calendar(tropical_panchaanga)
  output_file = os.path.join(output_dir, city.name, str(computation_system), "shaka_year", '%d.ics' % (year))
  ics.write_to_file(ics_calendar, output_file)


def dump_kauNDinyAyana(year, city):
  computation_system = ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180
  computation_system.options.fest_repos = [RulesRepo(name="gRhya/general")]
  tropical_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=year, computation_system=computation_system, allow_precomputed=False)
  ics_calendar = ics.compute_calendar(tropical_panchaanga)
  output_file = os.path.join(output_dir, city.name, str(computation_system), "shaka_year", '%d.ics' % (year))
  ics.write_to_file(ics_calendar, output_file)


if __name__ == '__main__':
  bengaLUru = spatio_temporal.City.get_city_from_db("bengaLUru-snagar")
  # dump_common(year=1942, city=bengaLUru)
  dump_kauNDinyAyana(year=1942, city=bengaLUru)