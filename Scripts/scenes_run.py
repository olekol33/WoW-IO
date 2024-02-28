import os
from time import time
from typing import List, Optional
import multiprocessing as mp

from Modules import *


def run_scene(scene_num: int, output_folder: str, keep_output: bool, compress: int, pos: int = 0, seed: int = None, minutes_limit: int = None, debug_test: bool = False, debug_avatar_ids: Optional[List[str]] = None) -> None:
    """
    build and run the scene, and generate ios.
    :param scene_num: scene num
    :param output_folder: folder for the outputted ios.
    :param compress: gzip compression level, None for no compression.
    :param pos: index of the tqdm line.
    :param seed: random seed for the scene. None will set the seed to the scene_num for each scene.
    :param minutes_limit: run (create ios) for a limited number of minutes. None will run until scene is over.
    :param debug_test: if True: saves the avatar,loc,guild test-dicts to a pickle. (to be used with "test").
    :param debug_avatar_ids: create a path-follow gif for these avatars throughout the run. None won't create a gif.
    """
    w = World()
    scene = Scene(scene_num, output_folder, pos, w, debug_test=debug_test, seed=seed, scene_minutes_limit=minutes_limit if minutes_limit is not None else None,
                  debug_avatar_ids=set(debug_avatar_ids) if debug_avatar_ids is not None else None)
    scene.run(keep_output, compress)


def run_scenes(scene_nums: List[int], output_folder: str, keep_output: bool, compress: int, num_procs: int = 1, seed: int = None, minutes_limit: int = None, debug_test: bool = False, debug_avatar_ids: Optional[List[str]] = None) -> None:
    """
    build and run the scenes, and generate ios.
    if num_procs > 1: multiple processes will work on the scenes in parallel.
    :param scene_nums: list of scene nums.
    :param output_folder: folder for the outputted ios.
    :param compress: gzip compression level, None for no compression.
    :param num_procs: number of processes to work on these scenes in parallel.
    :param seed: random seed for all scenes. None will set the seed to the scene_num for each scene.
    :param minutes_limit: run (create ios) each scene for a limited number of minutes. None will run until the scenes are over.
    :param debug_test: if True: saves the avatar,loc,guild test-dicts to a pickle. (to be used with "test").
    :param debug_avatar_ids: create path-follow gifs for these avatars throughout the runs. None won't create a gif.
    """
    start_time = time()
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    scene_nums = list(dict.fromkeys(scene_nums))
    if num_procs == 1:
        for pos, scene_num in enumerate(scene_nums):
            run_scene(scene_num, output_folder, keep_output, compress, pos, seed, minutes_limit, debug_test, debug_avatar_ids)
    else:
        pool = mp.Pool(processes=min(num_procs, len(scene_nums)))
        pool.starmap(run_scene, ((scene_num, output_folder, keep_output, compress, pos, seed, minutes_limit, debug_test, debug_avatar_ids) for pos, scene_num in enumerate(scene_nums)))
    print('\033[K')
    print(f'\033[KDone. Total time: {time() - start_time :.2f}s')
