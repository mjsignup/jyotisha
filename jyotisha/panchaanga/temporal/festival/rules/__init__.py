import logging
import os
import sys
from pathlib import Path

import methodtools
from indic_transliteration import sanscript
from jyotisha import custom_transliteration
from timebudget import timebudget

from sanskrit_data.schema import common


def transliterate_quoted_text(text, script):
  transliterated_text = text
  pieces = transliterated_text.split('`')
  if len(pieces) > 1:
    if len(pieces) % 2 == 1:
      # We much have matching backquotes, the contents of which can be neatly transliterated
      for i, piece in enumerate(pieces):
        if (i % 2) == 1:
          pieces[i] = custom_transliteration.tr(piece, script, titled=True)
      transliterated_text = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in string: %s' % transliterated_text)
  return transliterated_text



class HinduCalendarEventTiming(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEventTiming"]
      },
      "month_type": {
        "type": "string",
        "enum": ["lunar_month", "sidereal_solar_month", "tropical_month"],
        "description": "",
      },
      "month_number": {
        "type": "integer",
        "description": "",
      },
      "anga_type": {
        "type": "string",
        "enum": ["tithi", "nakshatra", "yoga", "day"],
        "description": "",
      },
      "anga_number": {
        "type": "integer",
        "description": "",
      },
      "kaala": {
        "type": "string",
        "description": "",
      },
      "priority": {
        "type": "string",
        "description": "",
      },
      "year_start": {
        "type": "integer",
        "description": "",
      },
      "anchor_festival_id": {
        "type": "string",
        "description": "A festival may be (say) 8 days before some other event xyz. The xyz is stored here.",
      },
      "offset": {
        "type": "integer",
        "description": "A festival may be 8 days before some other event xyz. The 8 is stored here.",
      },
    }
  }))

  @classmethod
  def from_details(cls, month_type, month_number, anga_type, anga_number, kaala, year_start):
    timing = HinduCalendarEventTiming()
    timing.month_type = month_type
    timing.month_number = month_number
    timing.anga_type = anga_type
    timing.anga_number = anga_number
    timing.kaala = kaala
    timing.year_start = year_start
    timing.validate_schema()
    return timing

  def get_kaala(self):
    return "sunrise" if self.kaala is None else self.kaala

  def get_priority(self):
    return "puurvaviddha" if self.priority is None else self.priority
    

# noinspection PyUnresolvedReferences
class HinduCalendarEvent(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEvent"]
      },
      "timing": HinduCalendarEventTiming.schema,
      "tags": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
      },
      "comments": {
        "type": "string",
        "description": "",
      },
      "image": {
        "type": "string",
        "description": "",
      },
      "description": {
        "type": "object",
        "description": "Language code to text mapping.",
      },
      "names": {
        "type": "object",
        "description": "Language code to text array mapping.",
      },
      "shlokas": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_primary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_secondary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
    }
  }))

  def get_storage_file_name(self, base_dir):
    return self.get_storage_file_name_granular(base_dir=base_dir)

  def get_storage_file_name_flat(self, base_dir):
    return "%(base_dir)s/%(id)s__info.toml"  % dict(
      base_dir=base_dir,
      id=self.id.replace('/','__').strip('{}')
    )

  def get_storage_file_name_granular(self, base_dir):
    if self.timing.anchor_festival_id is not None:
      path = "relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s__info.toml" % dict(
        anchor_festival_id=self.timing.anchor_festival_id.replace('/','__'),
        offset=self.timing.offset,
        id=self.id.replace('/','__').strip('{}')
      )
    elif self.timing is None or self.timing.month_number is None:
      tag_list = '/'.join(self.tags)
      path = "description_only/%(id)s__info.toml" % dict(
        tags=tag_list,
        id=self.id.replace('/','__').strip('{}')
      )
    else:
      try:
        path = "%(month_type)s/%(anga_type)s/%(month_number)02d/%(anga_number)02d/%(id)s__info.toml" % dict(
          month_type=self.timing.month_type,
          anga_type=self.timing.anga_type,
          month_number=self.timing.month_number,
          anga_number=self.timing.anga_number,
          id=self.id.replace('/','__').strip('{}')
        )
      except Exception:
        logging.error(str(self))
        raise 
    if base_dir.startswith("http"):
      from urllib.parse import quote
      path = quote(path)
    return "%s/%s" % (base_dir, path)

  def get_url(self):
    # encoded_url = "https://" + quote(self.path_actual.replace(self.repo.path, self.repo.base_url.replace("https://", "")))
    encoded_url = self.get_storage_file_name(base_dir=self.repo.base_url)
    # https://github.com/sanskrit-coders/jyotisha/runs/1229399248?check_suite_focus=true shows that ~ is being replaced there, which breaks tests. Hence the below.
    return encoded_url.replace("%7E", "~")

  def get_description_string(self, script, include_url=False, include_images=False, use_markup=False,
                             include_shlokas=False, is_brief=False, truncate=False):
    from jyotisha.panchaanga.temporal.festival.rules import summary
    final_description_string = summary.describe_fest(self, include_images, include_shlokas, include_url, is_brief, script,
    truncate, use_markup)

    return final_description_string



def get_festival_rules_map(dir_path, repo=None):
  toml_file_paths = sorted(Path(dir_path).glob("**/*.toml"))
  festival_rules = {}
  if len(toml_file_paths) == 0:
    logging.warning("No festival rule found at %s", dir_path)
    return festival_rules
  for file_path in toml_file_paths:
    event = HinduCalendarEvent.read_from_file(filename=str(file_path))
    event.path_actual = str(file_path)
    event.repo = repo
    festival_rules[event.id] = event
  return festival_rules


DATA_ROOT = os.path.join(os.path.dirname(__file__), "../data")


class RulesRepo(common.JsonObject):
  LUNAR_MONTH_DIR = "lunar_month"
  SIDEREAL_SOLAR_MONTH_DIR = "sidereal_solar_month"
  TROPICAL_MONTH_DIR = "tropical"
  GREGORIAN_MONTH_DIR = "gregorian"
  RELATIVE_EVENT_DIR = "relative_event"
  ERA_GREGORIAN = "gregorian"
  ERA_KALI = "kali"
  DAY_DIR = "day"
  TITHI_DIR = "tithi"
  NAKSHATRA_DIR = "nakshatra"
  YOGA_DIR = "yoga"

  def __init__(self, name, path=None, base_url='https://github.com/sanskrit-coders/adyatithi/tree/master'):
    super().__init__()
    self.name = name
    self.path = path
    self.base_url = os.path.join(base_url, name)

  def get_path(self):
    #  We don't set the path in __init__ so as to avoid storing machine-specific paths for canonical repos_tuple.
    return self.path if self.path is not None else os.path.join(DATA_ROOT, self.name)


rule_repos = (RulesRepo(name="general"), RulesRepo(name="gRhya/general"), RulesRepo(name="tamil"), RulesRepo(name="mahApuruSha/general"), RulesRepo(name="devatA/pitR"), RulesRepo(name="devatA/shaiva"), RulesRepo(name="devatA/umA"), RulesRepo(name="devatA/graha"), RulesRepo(name="devatA/nadI"), RulesRepo(name="devatA/shakti"), RulesRepo(name="devatA/gaNapati"),  RulesRepo(name="devatA/kaumAra"),  RulesRepo(name="devatA/vaiShNava"), RulesRepo(name="devatA/lakShmI"), RulesRepo(name="devatA/misc-fauna"), RulesRepo(name="devatA/misc-flora"), RulesRepo(name="mahApuruSha/kAnchI-maTha"), RulesRepo(name="mahApuruSha/ALvAr"), RulesRepo(name="mahApuruSha/vaiShNava-misc"), RulesRepo(name="mahApuruSha/mAdhva-misc"), RulesRepo(name="mahApuruSha/smArta-misc"), RulesRepo(name="mahApuruSha/sangIta-kRt"), RulesRepo(name="mahApuruSha/xatra"), RulesRepo(name="mahApuruSha/RShi"), RulesRepo(name="mahApuruSha/nAyanAr"), RulesRepo(name="temples/venkaTAchala"), RulesRepo(name="temples/Andhra"), RulesRepo(name="temples/Tamil"), RulesRepo(name="temples/Kerala"), RulesRepo(name="temples/Odisha"), RulesRepo(name="temples/North"), RulesRepo(name="time_focus/sankrAnti"), RulesRepo(name="time_focus/puShkara"), RulesRepo(name="time_focus/yugAdiH"), RulesRepo(name="time_focus/misc"),  RulesRepo(name="time_focus/Rtu"), RulesRepo(name="time_focus/nakShatra"), RulesRepo(name="time_focus/Eclipses"), RulesRepo(name="time_focus/misc_combinations"), RulesRepo(name="time_focus/monthly/amAvAsyA"), RulesRepo(name="time_focus/monthly/ekAdashI"), RulesRepo(name="time_focus/monthly/dvAdashI"), RulesRepo(name="time_focus/monthly/pradoSha"),)


class RulesCollection(common.JsonObject):
  def __init__(self, repos=rule_repos):
    super().__init__()
    self.repos = repos
    self.name_to_rule = {}
    self.tree = None 
    self.set_rule_dicts()

  @methodtools.lru_cache()  # the order is important!
  @classmethod
  def get_cached(cls, repos_tuple):
    return RulesCollection(repos=repos_tuple)

  def fix_filenames(self):
    for repo in self.repos:
      base_dir = repo.get_path()
      rules_map = get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path()), repo=repo)
      for rule in rules_map.values():
        expected_path = rule.get_storage_file_name(base_dir=base_dir)
        if "sa" in rule.names:
          rule.names["sa"] = [sanscript.transliterate(x, sanscript.HK, sanscript.DEVANAGARI).replace("~", "-") for x in rule.names["sa"]]
        if rule.path_actual != expected_path:
          logging.info(str((rule.path_actual, expected_path)))
          os.makedirs(os.path.dirname(expected_path), exist_ok=True)
          os.rename(rule.path_actual, expected_path)

  @timebudget
  def set_rule_dicts(self):
    for repo in self.repos:
      self.name_to_rule.update(get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path()), repo=repo))

      from sanskrit_data import collection_helper
      self.tree = collection_helper.tree_maker(leaves=self.name_to_rule.values(), path_fn=lambda x: x.get_storage_file_name_granular(base_dir="").replace("__info.toml", ""))

  def get_month_anga_fests(self, month_type, month, anga_type_id, anga):
    if int(month) != month:
      # Deal with adhika mAsas
      month_str = "%02d.5" % month
    else:
      month_str = "%02d" % month
    from jyotisha.panchaanga.temporal.zodiac import Anga
    if isinstance(anga, Anga):
      anga = anga.index
    try:
      return self.tree[month_type.lower()][anga_type_id.lower()][month_str]["%02d" % anga]
    except KeyError:
      return {}

  def get_possibly_relevant_fests(self, month_type, month, anga_type_id, angas):
    fest_dict = {}
    for anga in angas:
      from jyotisha.panchaanga.temporal.zodiac.angas import Tithi
      if isinstance(anga, Tithi) and month_type == RulesRepo.LUNAR_MONTH_DIR:
        month = anga.month.index
      for m in [month, 0]:
        fest_dict.update(self.get_month_anga_fests(month_type=month_type, month=m, anga_type_id=anga_type_id, anga=anga))
    return fest_dict



# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  rules_collection = RulesCollection.get_cached(repos_tuple=rule_repos)
  # rules_collection = RulesCollection(repos=[RulesRepo(name="general")])
  rules_collection.fix_filenames()
