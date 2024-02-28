from __future__ import annotations

import gzip
import os
import random
from time import time
from typing import Tuple, List, Set, Optional, Iterator
import multiprocessing as mp
from tqdm import tqdm


# iterator of all ios (aid, (int)time, obj_id, type) in file.
def ios(input_file: str) -> Iterator[Tuple[str, float, str, str]]:
    is_compressed = input_file.split('.')[-1] == 'gz'
    with gzip.open(input_file, 'rt') if is_compressed else open(input_file) as f:
        for l in f:
            if l:
                # example line: A_0, 0.0, AO_226, 0\n
                line: List[str] = l.split(', ')     # the last element ends with newline
                # assert line[3][-1] == '\n', (line, input_file)
                yield line[0], float(line[1]), line[2], line[3]


# get number of minutes in current scene.
def get_scene_length(scene_num: int, input_folder: str) -> int:
    folder: str = os.path.join(input_folder, f'Scene{scene_num}')
    scene_files: Iterator[str] = (file for file in os.listdir(folder) if file.startswith(f'scene{scene_num}_'))
    return max((int(x.split('_')[1].split('-')[1].split('.')[0]) for x in scene_files), default=-1) + 1


# iterator of list[io], all ios per second in file
def io_per_sec(input_file: str, aids_set: Optional[Set[str]]) -> Iterator[List[Tuple[str, float, str, str]]]:
    sec_io: List[Tuple[str, float, str, str]] = []
    curr_sec: Optional[float] = None
    for io in ios(input_file):
        if curr_sec is None:
            curr_sec = io[1]
        if io[1] > curr_sec:
            yield sec_io
            # assert curr_sec + 1 == io[1]
            sec_io.clear()
            curr_sec += 1
        if aids_set is None or io[0] in aids_set:
            sec_io.append(io)
    yield sec_io


# return the new list[io] created (multiplied by factor, then sorted) from the input ios.
def multiply_sec(io_sec: List[Tuple[str, float, str, str]], factor: int) -> List[Tuple[str, float, str, str]]:
    multiplied_sec: List[Tuple[str, float, str, str]] = []
    for aid, time, obj, io_tid in io_sec:
        for _ in range(factor):
            multiplied_sec.append((aid, time+random.random(), obj, io_tid))
    # assert len(io_sec) * factor == len(multiplied_sec)
    return sorted(multiplied_sec, key=lambda x: x[1])


def multiply_scene(scene_num: int, input_folder: str, output_folder: str, compress: int, pos: int = 0, factor: int = 3, seed: int = 0, aids: Optional[List[str]] = None) -> None:
    """
    multiply "factor" times the ios generated by the input scene, by "aids" avatars.
    :param scene_num: scene number
    :param input_folder: the scenes folder
    :param output_folder: output-ios folder
    :param compress: gzip compression level, None for no compression.
    :param pos: index of the tqdm line.
    :param factor: multiply factor
    :param seed: random seed
    :param aids: list of avatar ids to be followed (io will be generated for the ios the created).
                 if None - all avatars will be followed.
    """
    random.seed(seed)
    i_folder: str = os.path.join(input_folder, f'Scene{scene_num}')
    o_folder: str = os.path.join(output_folder, f'Scene{scene_num}')
    if not os.path.isdir(o_folder):
        os.mkdir(o_folder)

    scene_files: Iterator[str] = (file for file in os.listdir(i_folder) if file.startswith(f'scene{scene_num}_'))
    sec_num = 0
    ext = 'txt' if compress is None else 'txt.gz'
    with tqdm(total=get_scene_length(scene_num, input_folder), position=pos, desc=f'Scene {scene_num}') as pbar:
        for file in sorted(scene_files, key=lambda x: int(x.split('_')[1].split('-')[0])):
            file_ext = f"{file.split('.')[0]}.{ext}"
            output_file = os.path.join(o_folder, f'multiplied-{factor}-{file_ext}')
            with open(output_file, 'w') if compress is None else gzip.open(output_file, 'wt', compresslevel=compress) as f:
                for io_sec in io_per_sec(os.path.join(i_folder, file), set(f'A_{aid}' for aid in aids) if aids else None):
                    multiplied_sec = multiply_sec(io_sec, factor)
                    f.write(''.join(f"{aid}, {time:.6f}, {obj}, {io_tid}" for aid, time, obj, io_tid in multiplied_sec))    # io_tid ends with newline
                    sec_num += 1
                    if sec_num % 60 == 0:
                        pbar.update(1)


def multiply_scenes(scene_nums: List[int], input_folder: str, output_folder: str, compress: int, factor: int, seed: int, num_procs: int = 1, aids: Optional[List[str]] = None) -> None:
    """
    multiply "factor" times the ios generated by the input scenes, by "aids" avatars.
    :param scene_nums: scene numbers
    :param input_folder: the scenes folder
    :param output_folder: output-ios folder
    :param compress: gzip compression level, None for no compression.
    :param factor: multiply factor
    :param seed: random seed
    :param aids: list of avatar ids to be followed (io will be generated for the ios the created).
                 if None - all avatars will be followed.
    """
    start_time = time()
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    scene_nums = list(dict.fromkeys(scene_nums))
    if num_procs == 1:
        for pos, scene_num in enumerate(scene_nums):
            multiply_scene(scene_num, input_folder, output_folder, compress, pos, factor, seed, aids)
    else:
        pool = mp.Pool(processes=min(num_procs, len(scene_nums)))
        pool.starmap(multiply_scene, ((scene_num, input_folder, output_folder, compress, pos, factor, seed, aids) for pos, scene_num in enumerate(scene_nums)))
    print('\033[K')
    print(f'\033[KDone. Total time: {time() - start_time :.2f}s')
