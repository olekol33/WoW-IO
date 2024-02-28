from pathlib import Path
from datetime import datetime, date
from typing import List, Optional

from tqdm import tqdm
import os
import matplotlib.pyplot as plt

DAY: int = 1440


def calc_stats(data_path: str, output_folder: str, show: bool, min_day_records: int, max_gap_minutes: int) -> None:
    """
    outputs statistics about gaps, scene lengths, and scene length graphs (saved as images, and optionally presented to the user).
    :param data_path: path to the original database.
    :param output_folder: path to the output folder (the graph images will be saved there).
    :param show: present the graph to the user (the graph images will be saved anyway).
    :param min_day_records: a day with fewer records than this variable will be tagged as a bad day.
    :param max_gap_minutes: max minutes between consecutive data record to not be considered a gap.
    """
    total_avg: List[int] = []
    other_problem_avg: List[int] = []
    thursdays_problem_avg: List[int] = []
    gaps_avg: List[int] = []
    missing_days: int = 0
    prev_day: Optional[date] = None
    prev_time: Optional[datetime] = None
    init_time: Optional[datetime] = None
    scene_lens: List[int] = []
    last_problematic_thursday: Optional[date] = None
    thursday_counter: int = 0

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    for root, _, unsorted_files in tqdm(sorted(list(os.walk(data_path, topdown=False)))):
        files: List[str] = sorted(list(unsorted_files))
        if files:
            day: date = datetime.strptime(Path(root).name, '%Y-%m-%d').date()
            total_avg.append(len(files))
            if prev_day and (day - prev_day).days > 1:
                missing_days += (day - prev_day).days - 1
                print(f'WARNING: missing {(day - prev_day).days -1} days between {prev_day} - {day}')
            prev_day = day
            if len(files) < min_day_records:
                if day.weekday() != 3:
                    other_problem_avg.append(len(files))
                    print(f'WARNING: {day} ({day.strftime("%A")}) has only {len(files)} records ')
                else:
                    thursdays_problem_avg.append(len(files))

        for f in files:
            try:
                cur_time: datetime = datetime.strptime(f"{Path(root).name} {str(f).rstrip('.txt')}", '%Y-%m-%d %H-%M-%S')
                if init_time is None:
                    init_time = cur_time
                if prev_time and ((cur_time - prev_time).total_seconds() // 60) > max_gap_minutes:
                    gap: int = int((cur_time - prev_time).total_seconds() // 60)
                    if cur_time.weekday() == 3 and gap >= 120 and cur_time.date() != last_problematic_thursday:
                        thursday_counter += 1
                        last_problematic_thursday = cur_time.date()
                    else:
                        gaps_avg.append(gap)
                        scene_len = prev_time - init_time
                        scene_lens.append(int(scene_len.total_seconds() // 60))
                        print(f'Scene: {init_time} - {prev_time}. ({scene_len})')
                        init_time = cur_time
                prev_time = cur_time
            except Exception as e:
                print(e)
                pass

    print()
    print()
    print('STATISTICS:')

    print()
    print(f'Total files: {len(total_avg)}')
    print(f'Thursdays with problems: {thursday_counter}, {thursday_counter / len(total_avg) * 100 :.2f}% ')
    print(f'Other Problems: {len(other_problem_avg)}, {len(other_problem_avg) / len(total_avg) * 100 :.2f}%')
    print(f'Avg files per day: {sum(total_avg) / len(total_avg) :.2f}')
    print(f'Avg files per problems day: {sum(other_problem_avg) / len(other_problem_avg) :.2f}')
    print(f'Avg files per problems thursdays: {sum(thursdays_problem_avg) / len(thursdays_problem_avg) :.2f}')

    print()
    print(f'Missing days: {missing_days}')
    print(f'Gaps: {len(gaps_avg)}')
    if len(gaps_avg) > 0:
        print(f'Avg Gaps: {sum(gaps_avg)/len(gaps_avg) :.2f} minutes')

    plt.bar(range(len(scene_lens)), scene_lens, width=1)
    plt.ylabel('scene length [minutes]')
    plt.xlabel('scene number')
    plt.margins(0)
    plt.title(f'scene length bar - threshold {max_gap_minutes} minutes')
    plt.savefig(str(os.path.join(output_folder,  f'bar_{max_gap_minutes}.png')))
    if show:
        plt.show()
    else:
        plt.clf()

    print()
    print(f'more than a week:  {len(list(filter(lambda x: x >= DAY*7,  scene_lens))):3}')
    print(f'more than 6 days:  {len(list(filter(lambda x: x >= DAY*6,  scene_lens))):3}')
    print(f'more than 5 days:  {len(list(filter(lambda x: x >= DAY*5,  scene_lens))):3}')
    print(f'more than 4 days:  {len(list(filter(lambda x: x >= DAY*4,  scene_lens))):3}')
    print(f'more than 3 days:  {len(list(filter(lambda x: x >= DAY*3,  scene_lens))):3}')
    print(f'more than 2 days:  {len(list(filter(lambda x: x >= DAY*2,  scene_lens))):3}')
    print(f'more than a day:   {len(list(filter(lambda x: x >= DAY,    scene_lens))):3}')
    print(f'more than 1/2 day: {len(list(filter(lambda x: x >= DAY//2, scene_lens))):3}')
    print(f'total no. scenes:  {len(scene_lens):3}')

    plt.hist(scene_lens, color='green', bins=range(0, max(scene_lens), 100))
    plt.ylabel('number of scenes')
    plt.xlabel('scene length [minutes]')
    plt.margins(0)
    plt.title(f'scene length histogram - threshold {max_gap_minutes} minutes')
    plt.savefig(str(os.path.join(output_folder, f'hist_{max_gap_minutes}.png')))
    if show:
        plt.show()
    else:
        plt.clf()

    bins: List[int] = list(range(0, max(scene_lens), 100))
    longer_than: List[int] = [len(list(filter(lambda x: x >= thresh, scene_lens))) for thresh in bins[:-1]]

    plt.bar(bins[:-1], longer_than, color='red', width=100)
    plt.ylabel('number of scenes longer than')
    plt.xlabel('minimum length [minutes]')
    plt.margins(0)
    plt.title(f'total no. scenes longer than - threshold {max_gap_minutes} minutes')
    plt.savefig(str(os.path.join(output_folder, f'longer_than_{max_gap_minutes}.png')))
    if show:
        plt.show()
    else:
        plt.clf()
