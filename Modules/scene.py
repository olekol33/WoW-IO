from __future__ import annotations

import os
import pickle
from collections import defaultdict
from typing import MutableMapping, ValuesView, List, TextIO, Set, Tuple, Iterable, Iterator
import pandas as pd
from matplotlib import pyplot as plt, gridspec
from tqdm import tqdm
import random
import matplotlib.animation as ani
import numpy as np
import gzip

from Modules import *
from conf import include_writes


# The scene is where it all happens.


class Scene:
    # initialize all avatars, the world, create the location & guild Changes()
    def __init__(self, scene_num: int, output_folder: str, pos: int = 0, world: World = None, seed: int = None, scene_minutes_limit: int = None,
                 debug_avatar_ids: Set[str] = None, debug_test: bool = False):
        self._pbar: tqdm = tqdm(total=1, position=pos, desc=f'Scene {scene_num} - Initializing scene')
        self._seed: int = seed if seed is not None else scene_num
        self._world: World = world if world else World()
        self._output_folder = output_folder

        self._avatars: MutableMapping[str, Avatar] = {}
        self._guilds: MutableMapping[str, Guild] = {}
        self._zones: MutableMapping[str, Zone] = self._world.get_zones()
        self._scene_num: int = scene_num
        self._pos: int = pos

        # test data
        # loc_dict:     (time, loc)     -> {ao1, ao2, ao3, ..}
        # guild_dict:   (time, guild)   -> {ao1, ao2, ao3, ..}
        # avatar_dict:  (time, avatar)  -> (loc, guild)
        self._debug_test: bool = debug_test
        self._test_loc_dict:    MutableMapping[Tuple[int, str], Set[str]] = defaultdict(lambda: set())
        self._test_guild_dict:  MutableMapping[Tuple[int, str], Set[str]] = defaultdict(lambda: set())
        self._test_avatar_dict: MutableMapping[Tuple[int, str], Tuple[str, str]] = {}

        #for writes
        self._loc_updates: MutableMapping[int, Set[Location]] = {}
        self._guild_updates = set()

        # read scene from csv

        dtypes = {'virtual_time': int, 'avatar_id': str, 'place': str, 'guild': str}
        self._scene_df: pd.DataFrame = pd.read_csv(os.path.join("Scenes", f"scene{scene_num}.csv"), header=0, dtype=dtypes)

        self._total_vtime: int = self._scene_df['virtual_time'].max() + 1
        if scene_minutes_limit is None:
            scene_minutes_limit = self._total_vtime * MINUTES_IN_VTIME
        if self._total_vtime * MINUTES_IN_VTIME < scene_minutes_limit:
            print(
                f'\nWARNING: specified time ({scene_minutes_limit}m) is longer than scene length ({self._total_vtime * MINUTES_IN_VTIME}m). Scene length is being used!\n')
        self._actual_minutes_len: int = min(scene_minutes_limit, self._total_vtime * MINUTES_IN_VTIME)

        self._scene_df: pd.DataFrame = self._scene_df[
            self._scene_df['virtual_time'] < ((self._actual_minutes_len - 1) // MINUTES_IN_VTIME) + 1]
        self._clock: int = -1

        # get all avatars/guilds ids

        self._avatar_ids:   Iterable[str] = self._scene_df['avatar_id'].unique()
        self._guild_ids:    Iterable[str] = self._scene_df['guild'][self._scene_df['guild'] != 'NO'].unique()

        all_avatars = set(self._avatar_ids)

        # initial debugging structures
        self._debug_avatar_ids: Set[str] = debug_avatar_ids & all_avatars if debug_avatar_ids else set()
        self._debug_figs = []
        self._debug_avatars_xs: MutableMapping[str, MutableMapping[ContinentName, List[int]]] = defaultdict(
            lambda: {cont: [] for cont in ContinentName})
        self._debug_avatars_ys: MutableMapping[str, MutableMapping[ContinentName, List[int]]] = defaultdict(
            lambda: {cont: [] for cont in ContinentName})

        # set process bar description
        self._pbar.set_description(f'Scene {self._scene_num} - creating guilds')

        # create guilds

        for gid in self._guild_ids:
            self._guilds[gid] = Guild(gid)

        # create all guild/location changes

        guilds_changes: MutableMapping[str, Changes[Guild]] = {}
        places_changes: MutableMapping[str, Changes[Place]] = {}
        for aid in self._avatar_ids:
            guilds_changes[aid] = Changes(aid)
            places_changes[aid] = Changes(aid)

        last_vtime = -1
        self._pbar.set_description(f'Scene {self._scene_num} - reading scene')
        self._pbar.reset(total=len(self._scene_df))

        for _, row in self._scene_df.iterrows():
            if row.virtual_time > last_vtime:
                for aid in all_avatars:     # set all non-active avatars' location to None
                    places_changes[aid].register_change(last_vtime, None)
                all_avatars = set(self._avatar_ids)
                last_vtime = row.virtual_time
            all_avatars.discard(row.avatar_id)

            # register changes
            if row.guild != 'NO':
                guilds_changes[row.avatar_id].register_change(row.virtual_time, self._guilds[row.guild])
            else:
                guilds_changes[row.avatar_id].register_change(row.virtual_time, None)
            places_changes[row.avatar_id].register_change(row.virtual_time, self._world.get_place(row.place))

            self._pbar.update()

        for aid in all_avatars:     # set all non-active avatars' location to None
            places_changes[aid].register_change(last_vtime, None)

        # create all avatars (with changes).
        self._pbar.set_description(f'Scene {self._scene_num} - creating avatars')
        for aid in self._avatar_ids:
            self._avatars[aid] = Avatar(aid, guilds_changes[aid], places_changes[aid], self._world, debug=(aid in self._debug_avatar_ids))
        self.reset()

    # reset scene
    def reset(self) -> None:
        random.seed(self._seed)
        self._clock = -1
        self._world.reset()
        for a in self._avatars.values():
            assert a.clock() == -1, f'{a.get_id()} clock is not synced'

    # all avatars take a step.
    # if debug_test is on - record the current state for testing purposes.
    # if following avatars with "_debug_avatar_ids" and SECONDS_IN_VTIME seconds passed since the last time -
    #  create an updated gif.
    def step(self) -> None:
        for a in self._avatars.values():
            # assert a.clock() == self._clock, f'{a.get_id()} clock is not synced'
            a.step()
        self._clock += 1
        self._merge_loc_updates()
        self.merge_guild_updates()

        if self._debug_test:
            self._update_debug_data()

        if self._debug_avatar_ids and self._clock % SECONDS_IN_VTIME == 0:
            self._debug_gif()

    # generate all ios from this second, and write it to the output_file.
    def generate_io(self, output_file: TextIO) -> None:
        io: List[str] = []
        if include_writes:
            io.extend(self.generate_io_sys())
        for a in self._avatars.values():
            io.extend(a.generate_io())
        output_file.write(''.join(io))

    # run the scene. Each second take a step and generate all ios. Save all ios to output files under scene_dir/.
    #  for example, Scene7/scene_10-19.txt.
    # updates a tqdm progress bar.
    def run(self, keep_output: bool = False, compress: int = None) -> None:
        self.reset()
        if not os.path.isdir(self._output_folder):
            os.mkdir(self._output_folder)
        scene_dir: str = os.path.join(self._output_folder, f'Scene{self._scene_num}')
        test_data_path = os.path.join(scene_dir, f"test_data_scene{self._scene_num}.pickle")
        if not os.path.isdir(scene_dir):
            os.mkdir(scene_dir)
        elif not keep_output:
            for file in os.listdir(scene_dir):
                os.remove(os.path.join(scene_dir, file))

        if not keep_output and os.path.isfile(test_data_path):
            os.remove(test_data_path)

        self._pbar.reset(total=self._actual_minutes_len)
        self._pbar.set_description(f'Scene {self._scene_num}')
        ext = 'txt' if compress is None else 'txt.gz'
        pad = len(str(self._actual_minutes_len - 1))

        for start_time in range(0, self._actual_minutes_len, MINUTES_IN_VTIME):
            self._loc_updates.clear()
            end_time: int = min(start_time + MINUTES_IN_VTIME, self._actual_minutes_len)
            pad_start_time = str(start_time).zfill(pad)
            pad_end_time = str(end_time - 1).zfill(pad)
            path: str = os.path.join(scene_dir, f'scene{self._scene_num}_{pad_start_time}-{pad_end_time}.{ext}')

            with open(path, 'w') if compress is None else gzip.open(path, 'wt', compresslevel=compress) as f:
                for _ in range(start_time * MINUTE, end_time * MINUTE):
                    self.step()
                    self.generate_io(f)

            self._pbar.update((end_time - start_time))
            self._pbar.refresh()

        self._pbar.close()

        if self._debug_test:
            with open(test_data_path, 'wb') as pickle_f:
                pickle.dump((self._test_avatar_dict, dict(self._test_loc_dict), dict(self._test_guild_dict)), pickle_f)
            print(f'Test debug data saved!  ({test_data_path})')

    # takes loc_updates from each avatar and merges into a single dict.
    # make fast and efficient as possible
    def _merge_loc_updates(self):
        if self._clock % SECONDS_IN_VTIME != 0:
            return
        for a in self._avatars.values():
            for time, loc in a.loc_updates.items():
                self._loc_updates.setdefault(time + self._clock, set()).add(loc)
            a.loc_updates.clear()

    # get guild updates for each avatar and collect into a single set.
    def merge_guild_updates(self):
        self._guild_updates.clear()
        for a in self._avatars.values():
            self._update_guild(a)


    # iterator if all ios the player should read is this second.
    # this routine generates the writes made by the system
    def generate_io_sys(self) -> Iterator[str]:
        updates = self._loc_updates.get(self._clock, set())
        updates.update(self._guild_updates)

        prefix = f'sys, {self._clock}.0, '
        return (f'{prefix}{obj.id}, WRITE\n' for obj in updates)

    # Guild object write occurs if there was update at a guild member list
    # Update probability is # guild members / #avatars
    def _update_guild(self, a: Avatar) -> None:
        for g in a.guild_updates:
            guild_avatar_share = len(g.get_avatars_dict().keys()) / len(self._avatars)
            update_prob = random.uniform(0, 1)
            if update_prob < guild_avatar_share or self._clock == 0:
                self._guild_updates.add(g)

    def get_world(self) -> World:
        return self._world

    def get_avatars(self) -> ValuesView[Avatar]:
        return self._avatars.values()

    def get_zones(self) -> ValuesView[Zone]:
        return self._zones.values()

    def get_guilds(self) -> ValuesView[Guild]:
        return self._guilds.values()

    # create (or update the already created) gif following the current path of "self._debug_avatar_ids"
    def _debug_gif(self):
        fig = plt.figure(figsize=(4, 6))
        gs = gridspec.GridSpec(3, 2)
        ka_ax = fig.add_subplot(gs[0:2, 0:1])
        ek_ax = fig.add_subplot(gs[0:2, 1:2])
        ol_ax = fig.add_subplot(gs[2:3, 0:2])
        str_loc = ''
        colors: List[str] = ['k', 'dimgrey', 'darkviolet', 'g', 'm']
        conts = [
            (ka_ax, ContinentName.Kalimdor),
            (ek_ax, ContinentName.EasternKingdoms),
            (ol_ax, ContinentName.Outland)
        ]

        for j, aid in enumerate(sorted(self._debug_avatar_ids)):
            color: str = colors[j % len(colors)]
            xs: MutableMapping[ContinentName, List[int]] = self._debug_avatars_xs[aid]
            ys: MutableMapping[ContinentName, List[int]] = self._debug_avatars_ys[aid]
            last_loc = None
            for last_loc in self._avatars[aid].debug_path[-SECONDS_IN_VTIME:]:
                if last_loc is not None:
                    x, y = last_loc.get_coords()
                    xs[last_loc.get_continent().get_name()].append(x)
                    ys[last_loc.get_continent().get_name()].append(y)

            for ax, cont_type in conts:
                with open(os.path.join('Maps', f"{cont_type.value}.pickle"), 'rb') as pickle_f:
                    cont = pickle.load(pickle_f)[0]
                ax.matshow(cont.data, interpolation='none', cmap='jet')
                ax.set_title(cont_type.value)
                ax.scatter(xs[cont_type], ys[cont_type], marker='o', color=color, s=10)
                if last_loc and last_loc.get_continent().get_name() == cont_type:
                    ax.scatter(last_loc.get_coords()[0], last_loc.get_coords()[1], marker='o', facecolors=color,
                               edgecolor='w', s=50)
                ax.set_xlim([0, cont.shape[1]])
                ax.set_ylim([0, cont.shape[0]])
                ax.set_aspect('equal')
                ax.axes.xaxis.set_visible(False)
                ax.axes.yaxis.set_visible(False)
                ax.axis('off')
                ax.invert_yaxis()

            str_loc += f'\n{last_loc.get_continent().get_name().value}: ' \
                       f'{last_loc.get_zone().get_name()} ' \
                       f'{last_loc.get_coords()}' if last_loc else '\nLOGGED OFF'

        fig.suptitle(f'VClock: {(self._clock // SECONDS_IN_VTIME) + 1}{str_loc}')
        fig.subplots_adjust(wspace=0, hspace=0)
        fig.tight_layout()
        fig.canvas.draw()
        image_from_plot = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        image_from_plot = image_from_plot.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        self._debug_figs.append(image_from_plot)

        if self._actual_minutes_len // MINUTES_IN_VTIME == len(self._debug_figs) or len(self._debug_figs) % 5 == 0:
            fig = plt.figure(figsize=(4, 6))
            fig.tight_layout()
            frames = [[plt.imshow(p)] for p in self._debug_figs]
            plt.axis('off')
            animator = ani.ArtistAnimation(fig, frames, blit=True)
            writer = ani.PillowWriter(fps=3)
            # noinspection PyTypeChecker
            animator.save(os.path.join(self._output_folder, f'Scene{self._scene_num}',
                                       f'avatars-{"_".join(aid for aid in sorted(self._debug_avatar_ids))}.gif'), writer=writer)

    # record the current state (avatars, locations and guilds) for the testing data.
    def _update_debug_data(self):
        for a in self._avatars.values():
            time = self._clock
            aid = a.get_id()
            lid = a.get_location().get_id() if a.get_location() else None
            gid = a.get_guild().get_id() if a.get_guild() else None

            self._test_avatar_dict[(time, a.get_device_name())] = (lid, gid)
            if lid:
                self._test_loc_dict[(time, lid)].add(aid)
            if gid:
                self._test_guild_dict[(time, gid)].add(aid)
