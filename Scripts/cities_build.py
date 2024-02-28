import random
from copy import deepcopy
from typing import MutableMapping, Tuple, List, Set

import pandas as pd
import os
from Modules.city import CityType
from Modules.continent import ContinentName
from collections import defaultdict

# dictionaries of WoW instances and capitals found in the database, to the zone they appear in.
instances: MutableMapping[str, str] = {'Deadmines': 'Westfall', 'Blackfathom Deeps': 'Ashenvale', 'Ragefire Chasm': 'Durotar', 'Razorfen Downs': 'Thousand Needles', 'Razorfen Kraul': 'The Barrens', 'Shadowfang Keep': 'Silverpine Forest', 'Uldaman': 'Badlands', "Zul'Farrak": 'Tanaris', 'Wailing Caverns': 'The Barrens', 'Naxxramas': 'Eastern Plaguelands', "Onyxia's Lair": 'Dustwallow Marsh', "The Temple of Atal'Hakkar": 'Swamp of Sorrows', 'Maraudon': 'Desolace', 'Scarlet Monastery': 'Tirisfal Glades', 'Blackrock Depths': 'Burning Steppes', 'Warsong Gulch': 'The Barrens', "Ruins of Ahn'Qiraj": "Ahn'Qiraj", 'Dire Maul': 'Feralas', 'Scholomance': 'Western Plaguelands', 'Stratholme': 'Eastern Plaguelands', 'Blackwing Lair': 'Burning Steppes', 'Blackrock Spire': 'Burning Steppes', 'Alterac Valley': 'Hillsbrad Foothills', 'Arathi Basin': 'Arathi Highlands', 'Molten Core': 'Burning Steppes', "Zul'Gurub": 'Stranglethorn Vale', 'Old Hillsbrad Foothills': 'Tanaris', 'Karazhan': 'Deadwind Pass', 'Sunwell Plateau': "Isle of Quel'Danas", "Magisters' Terrace": "Isle of Quel'Danas", 'The Blood Furnace': 'Hellfire Peninsula', 'Hellfire Ramparts': 'Hellfire Peninsula', "Blade's Edge Arena": "Blade's Edge Mountains", 'Serpentshrine Cavern': 'Zangarmarsh', 'Auchenai Crypts': 'Terokkar Forest', 'Black Temple': 'Shadowmoon Valley', 'Nagrand Arena': 'Nagrand', 'The Arcatraz': 'Netherstorm', 'Sethekk Halls': 'Terokkar Forest', "Magtheridon's Lair": 'Hellfire Peninsula', 'Eye of the Storm': 'Netherstorm', 'The Underbog': 'Zangarmarsh', "Gruul's Lair": "Blade's Edge Mountains", 'The Botanica': 'Netherstorm', 'The Shattered Halls': 'Hellfire Peninsula', 'Steamvault': 'Zangarmarsh', 'The Steamvault': 'Zangarmarsh', 'The Mechanar': 'Netherstorm', 'Auchindoun: Shadow Labyrinth': 'Terokkar Forest', 'Mana-Tombs': 'Terokkar Forest', 'Coilfang: The Slave Pens': 'Zangarmarsh', 'Hyjal': 'Felwood', 'Tempest Keep': 'Netherstorm'}
capitals: MutableMapping[str, str] = {"Shattrath City": "Terokkar Forest", "Silvermoon City": "Eversong Woods", "Orgrimmar": "Durotar", 'Undercity': 'Tirisfal Glades', 'The Exodar': 'Azuremyst Isle', 'Thunder Bluff': 'Mulgore', 'Ironforge': 'Dun Morogh', 'Stormwind City': 'Elwynn Forest', 'Gnomeregan': 'Dun Morogh'}

rows: List[MutableMapping[str, str]] = []

# each of the city-dicts inside holds all the (x,y) locations for that kind of city to be created,
# without colliding with the cities created beforehand.
zones_loc: MutableMapping[CityType, MutableMapping[str, List[Tuple[int, int]]]] = {}


# returns random available city coordinates from "zones_loc", and updates it (removes now-colliding places).
def random_coords(zone: str, city_type: CityType) -> Tuple[int, int]:
    coord_x, coord_y = random.choice(zones_loc[city_type][zone])
    # print(f'chosen: {coord_x}, {coord_y}')    # used for debugging
    for t, d in zones_loc.items():
        # old: Set[Tuple[int, int]] = set(d[zone])  # used for debugging
        d[zone]: List[Tuple[int, int]] = [(x, y) for x, y in d[zone] if not (coord_x - t.value[0] + 1 <= x < coord_x + city_type.value[0] and coord_y - t.value[1] + 1 <= y < coord_y + city_type.value[1])]
        # print(f'  deleting ({t}) - {len(old - set(d[zone]))}: {old - set(d[zone])}')  # used for debugging
    return coord_x, coord_y


# insert a new city
def insert(city: str, zone: str, city_type_str: str, city_type: CityType) -> None:
    print(f'Adding: {city} -> {zone}   ({city_type_str})')
    tl_x, tl_y = random_coords(zone, city_type)
    d: MutableMapping[str, str] = {
        'name': city,
        'tl_x': tl_x,
        'tl_y': tl_y,
        'zone': zone,
        'type': city_type_str
    }
    rows.append(d)


def build_cities(seed: int) -> None:
    """
    build random cities location (using "seed" as seed) and saves it to ./Maps/{continent_name}.csv for the 3 continents.
    :param seed: random seed.
    """
    global zones_loc, rows
    random.seed(seed)
    rows = []

    zones: pd.DataFrame = pd.DataFrame()
    for continent in ContinentName:
        zones = zones.append(pd.read_csv(os.path.join('Maps', f"{continent.value}.csv"), index_col='name', header=0))
    zones.dropna(inplace=True)
    int_fields: List[str] = ['tl_x', 'tl_y', 'br_x', 'br_y', 'capitals', 'major cities', 'minor cities']
    zones[int_fields] = zones[int_fields].astype(int)

    zones_minor_loc: MutableMapping[str, List[Tuple[int, int]]] = defaultdict(lambda: [])
    for _, zone in zones.iterrows():
        for x in range(zone.tl_x, zone.br_x):
            for y in range(zone.tl_y, zone.br_y):
                zones_minor_loc[str(zone.name)].append((x, y))

    zones_loc = {
        CityType.Capital: deepcopy(zones_minor_loc),
        CityType.Major: deepcopy(zones_minor_loc),
        CityType.Minor: zones_minor_loc,
        CityType.Instance:  deepcopy(zones_minor_loc)
    }

    for capital, zone in capitals.items():
        insert(capital, zone, "capital", CityType.Capital)
        zones.at[zone, 'capitals'] -= 1
    for instance, zone in instances.items():
        insert(instance, zone, 'instance', CityType.Instance)

    assert zones['capitals'].min() >= 0, "negative count in capitals"
    assert zones['major cities'].min() >= 0, "negative count in major cities"
    assert zones['minor cities'].min() >= 0, "negative count in minor cities"

    for _, zone in zones.iterrows():
        for _ in range(zone['capitals']):
            insert('NO NAME', str(zone.name), "capital", CityType.Capital)
        for _ in range(zone['major cities']):
            insert('NO NAME', str(zone.name), "major city", CityType.Major)
        for _ in range(zone['minor cities']):
            insert('NO NAME', str(zone.name), "minor city", CityType.Minor)

    df = pd.DataFrame(rows)
    # noinspection PyTypeChecker
    df.to_csv(os.path.join('Maps', f'cities.csv'), index=False)
