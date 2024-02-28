import os.path
from typing import Tuple, MutableMapping, List

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import random

colors: List[int] = []      # list of available colors for new zones
color_to_zone: MutableMapping[int, str] = {}    # dict from color to zone name


# add a new zone to this continent. check for collisions with other zones.
def add_zone(continent_mat: np.ndarray, name: str, tl: Tuple[int, int], br: Tuple[int, int]):
    tl_x, tl_y = tl
    br_x, br_y = br
    assert 0 <= tl_x <= br_x <= continent_mat.shape[1] and 0 <= tl_y <= br_y <= continent_mat.shape[0], f'ERROR: {name} range error.'
    assert (continent_mat[tl_y:br_y, tl_x: br_x] == 0).all(), f'ERROR: {name} is not on empty cells.'
    color: int = colors.pop()
    color_to_zone[color] = name
    continent_mat[tl_y:br_y, tl_x: br_x] = color
    print(f'  {name}:    ({tl_x}, {tl_y}) -> ({br_x}, {br_y})')


# verify that each spot in the continent is in a zone.
def verify_full_continent(continent_mat: np.ndarray) -> None:
    assert (continent_mat == 0).any(), print('ERROR: Not all locations are connected to a zone')


def add_continent(name: str, shape: Tuple[int, int], show: bool) -> None:
    """
    create a np matrix for all the zones in the continent's csv. each line is:
        name, top-left-x, top-left-y, bottom-right-x, bottom-right-y, num-of-capitals, num-of-major-cities, num-of-minor-cities.
    the matrix is checked to be fully initialized, and for no collisions between different zones.
    the matrix will be saved as a pickle, and a colored map will be saved as a png.
    :param name: continent's name
    :param shape: continent sizes (width, height) in 60*60 meters blocks.
    :param show: should the colored map be presented to the user.
    """
    global colors, color_to_zone
    color_to_zone.clear()
    width, height = shape

    df: pd.DataFrame = pd.read_csv(os.path.join('Maps', f'{name}.csv'), header=0)
    df.dropna(inplace=True)
    int_fields: List[str] = ['tl_x', 'tl_y', 'br_x', 'br_y', 'capitals', 'major cities', 'minor cities']
    df[int_fields] = df[int_fields].astype(int)

    colors = list(df.index)
    random.shuffle(colors)

    continent: np.ndarray = np.zeros((height, width), dtype=np.int32)

    print(f'{name}:')
    for _, zone in df.iterrows():
        add_zone(continent, zone['name'], (zone.tl_x, zone.tl_y), (zone.br_x, zone.br_y))
    print('finished')

    verify_full_continent(continent)

    with open(os.path.join('Maps', f"{name}.pickle"), 'wb') as pickle_f:
        pickle.dump((continent, color_to_zone), pickle_f)

    plt.matshow(continent.data, interpolation='none')
    plt.axis('off')
    plt.set_cmap('jet')
    plt.savefig(os.path.join('Maps', f"{name}.png"), bbox_inches='tight', pad_inches=0)
    if show:
        plt.title(name)
        plt.show()


def create_maps(show: bool) -> None:
    """
    create maps for the 3 continents. [colored .png] and [np matrix .pickle] will be created.
    :param show: should the colored maps be presented to the user.
    """
    random.seed(0)
    add_continent('kalimdor', (187, 421), show)  # according to height=25,246, ratio=187:421
    add_continent('eastern kingdoms', (148, 364), show)  # according to height=21869(83.11% of 26,312), ratio=148:364
    add_continent('outland', (300, 187), show)  # we assumed outland is that large
