import os
from typing import Optional, List, MutableMapping, Set, IO

import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta, date
from pathlib import Path

# bad values in the db. will be omitted.
bad_races: Set[str] = {'373族', '547人', '3033', '27410', '74622妖'}
bad_classes: Set[str] = {'482', '2400', '3485伊'}
removes: Set[str] = {'1007城', 'The Great Sea', '15641', '2029', '1608峽谷', 'GM Island', '8585', '監獄', '達納蘇斯', '時光洞穴', '未知',
           '毒牙沼澤', 'The Veiled Sea', 'Twisting Nether', '龍骨荒野', 'The North Sea', "Drak'Tharon Keep", '1231崔茲',
           '61477', '麥克那爾', 'The Forbidding Sea', '北方海岸', }

# places inside a zone (while not a city/instance). will be replaced with the zone name.
replaces: MutableMapping[str, str] = {"Quel'thalas": "Eversong Woods", "The Black Morass": "Swamp of Sorrows", 'Ruins of Lordaeron': 'Tirisfal Glades', 'Blackrock Mountain': 'Burning Steppes', "Gates of Ahn'Qiraj": "Ahn'Qiraj", 'Deeprun Tram': 'Dun Morogh','Hall of Legends': 'Durotar', }

# files without the data we seek.
bad_files: Set[str] = {'00-00-00--srvcombine.txt', '20-39-00--dataloss.txt', '10-05-00----從此開始分組改變.txt'}


THURSDAY_GAP: int = 120
DAY: int = 1440

init_time: Optional[datetime] = None                # time of first good record in this scene
prev_time: Optional[datetime] = None                # time of last good record
last_problematic_thursday: Optional[date] = None    # date of last thursday - so not to count the same thursday twice.
rows: List[MutableMapping[str, str]] = []           # list of good records - {virtual time, avatar id, guild id, zone}.
scene_num: int = 0          # number of last scene (first scene will be Scene1)
virtual_time: int = 0       # current virtual time (num. of records in the current scene up to this point).
total_counter: int = 0      # number of good records in current scene.


# process a line (string, record) from the file
#  if it's a good record - append {virtual time, avatar id, guild id, zone} to "rows"
def process_line(line: str) -> None:
    global total_counter
    row: List[str] = line.split('"')[1].split(',')
    # query_sequence_number: str = row[2].strip()
    avatar_id: str = row[3].strip()
    guild: str = row[4].strip()
    # level: str = row[5].strip()
    race: str = row[6].strip()
    class_: str = row[7].strip()
    place: str = row[8].strip()

    if race in bad_races:
        return
    if class_ in bad_classes:
        return
    if place in removes:
        return
    if place in replaces:
        place = replaces[place]
    if not guild:
        guild = 'NO'

    d: MutableMapping[str, str] = {
        'virtual_time': virtual_time,
        'avatar_id': avatar_id,
        'guild': guild,
        'place': place,
    }
    rows.append(d)
    total_counter += 1


# if the gap between the current and the previous file is longer then "max_gap_minutes" minutes - start a new scene.
#  if the current scene is longer than "min_scene_minute_len" minutes - save it (with a new scene number).
# we get cur_time from the current file name ("filename")
def check_end_of_scene(filename: str, summary_file: IO, min_scene_minute_len: int, max_gap_minutes: int) -> None:
    global init_time, last_problematic_thursday, prev_time, rows, scene_num, virtual_time
    cur_time: datetime = datetime.strptime(f"{Path(filename).parent.name} {Path(filename).name}", '%Y-%m-%d %H-%M-%S.txt')
    if init_time is None:
        init_time = cur_time
    if prev_time and (cur_time - prev_time).total_seconds() > 60 * max_gap_minutes:
        gap = int((cur_time - prev_time).total_seconds() // 60)
        if cur_time.weekday() == 3 and gap >= THURSDAY_GAP and cur_time.date() != last_problematic_thursday:
            last_problematic_thursday = cur_time.date()
        else:
            scene_len = prev_time - init_time
            if (scene_len.total_seconds() // 60) >= min_scene_minute_len:
                scene_num += 1
                print(f'\nScene {scene_num}: {init_time} - {prev_time} ({scene_len})')
                df = pd.DataFrame(rows)
                # noinspection PyTypeChecker
                df.to_csv(os.path.join('Scenes', f'scene{scene_num}.csv'), index=False)
                summary_file.write(f'Scene {scene_num}: {init_time} - {prev_time} ({scene_len})\n')
            rows.clear()
            init_time = cur_time
            virtual_time = 0
    prev_time = cur_time


# process all the entries from this file. might build some scenes through the process.
# scene is at-least "min_scene_minute_len" minutes, and with no gaps longer then "max_gap_minutes" minutes.
def process_file(filename: str, summary_file: IO, min_scene_minute_len: int, max_gap_minutes: int) -> None:
    global virtual_time
    if Path(filename).name in bad_files:
        return
    check_end_of_scene(filename, summary_file, min_scene_minute_len, max_gap_minutes)
    try:
        with open(filename, 'r', encoding='utf8') as file:
            data: List[str] = file.read().split('{\n')[1].split('}')[0].replace('\t', '').split('\n')[:-1]
            for line in data:
                process_line(line)
        virtual_time += 1
    except Exception as e:
        print(f'ERROR: in {filename}, {e}')


def build_scenes(data_path: str, min_scene_minute_len: int, max_gap_minutes: int) -> None:
    """
    build scenes (to the ./Scenes folder) from the database, with minimum length and without any gaps.
    :param data_path: the original database.
    :param min_scene_minute_len: minimum non-gaps minute-length to be considered a scene.
    :param max_gap_minutes: max minutes between consecutive data record to not be considered a gap.
    """
    global init_time, prev_time, last_problematic_thursday, rows, scene_num, virtual_time, total_counter
    init_time = None
    prev_time = None
    last_problematic_thursday = None
    rows = []
    scene_num = 0
    virtual_time = 0
    total_counter = 0

    if os.path.isdir('Scenes'):
        for file in os.listdir('Scenes'):
            os.remove(os.path.join('Scenes', file))
    else:
        os.mkdir('Scenes')

    last_date: datetime = datetime(year=2008, month=11, day=1)
    with open(os.path.join('Scenes', 'scenes_summary.txt'), 'w') as summary_file:
        summary_file.write(f'SCENES SUMMARY (min_len: {min_scene_minute_len} minutes, max_gap: {max_gap_minutes} minutes):\n\n')
        for root, _, unsorted_files in tqdm(sorted(list(os.walk(data_path, topdown=False)))):
            for f in sorted(unsorted_files):
                if datetime.strptime(Path(root).name, '%Y-%m-%d') < last_date:
                    process_file(os.path.join(root, f), summary_file, min_scene_minute_len, max_gap_minutes)
        if prev_time:
            # noinspection PyTypeChecker
            end_time: datetime = prev_time + timedelta(minutes=max_gap_minutes + 100)
            check_end_of_scene(os.path.join(end_time.strftime("%Y-%m-%d"), end_time.strftime("%H-%M-%S.txt")), summary_file, min_scene_minute_len, max_gap_minutes)

    print(f'There is a total of {total_counter} lines.')
