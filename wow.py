import argparse
import os
import wget

from Scripts.maps_build import create_maps
from Scripts.stats_calc import calc_stats
from Scripts.cities_build import build_cities
from Scripts.debug_test import test_scene
from Scripts.io_multiply import multiply_scenes
from Scripts.scenes_build import build_scenes
from Scripts.scenes_run import run_scenes
from Modules.continent import ContinentName

dataset_url = "http://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/wow/wowah.rar"
catalina_dataset_path = '/nfs_share/storage-simulations/org-traces/WoWAH'


def colored(s: str):
    return f'\033[92m{s}\033[0m'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='commands', dest='command', required=True)

    download_help = f'Download the WoWAH dataset.'
    download = subparser.add_parser('download', help=download_help, description=download_help)

    stats_help = 'Show statistics of gaps and scene lengths in the WoWAH dataset.'
    stats = subparser.add_parser('stats', help=stats_help, description=stats_help)
    stats.add_argument('-d', "--dataset", type=str, metavar='PATH', default=catalina_dataset_path,
                       help=f"path to dataset folder (default={catalina_dataset_path})")
    stats.add_argument('-r', "--records", type=int, default=135, help="minimum records in day (default=135records)")
    stats.add_argument('-g', "--gap", type=int, metavar='MINUTES', default=25,
                       help="maximum minutes gap allowed in-scene (default=25minutes)")
    stats.add_argument('-o', "--output", type=str, metavar='PATH', default='Graphs',
                       help='output graphs folder (default=./Graphs/)')
    stats.add_argument('-w', '--show', action='store_true', help='show the graphs')

    build_help = 'Build the scenes’ csv files from the WoWAH dataset.'
    build = subparser.add_parser('build', help=build_help, description=build_help)
    build.add_argument('-d', "--dataset", type=str, metavar='PATH', default=catalina_dataset_path,
                       help=f"path to dataset folder (default={catalina_dataset_path})")
    build.add_argument('-l', "--length", type=int, metavar='MINUTES', default=1440,
                       help="minimum minutes to create a scene (default=1440minutes, a day)")
    build.add_argument('-g', "--gap", type=int, metavar='MINUTES', default=25,
                       help="maximum minutes gap allowed in-scene (default=25minutes)")

    maps_help = 'Creates the continents maps divided into zones.'
    maps = subparser.add_parser('maps', help=maps_help, description=maps_help)
    maps.add_argument('-w', '--show', action='store_true', help="show the continents' maps")

    cities_help = 'Creates random city locations (Maps/cities.csv).'
    cities = subparser.add_parser('cities', help=cities_help, description=cities_help)
    cities.add_argument('-s', "--seed", type=int, default=0, help='seed for random location of cities (default=0)')

    run_help = 'Run and generate IOs of the scenes.'
    run = subparser.add_parser('run', help=run_help, description=run_help)
    run.add_argument('scene_nums', type=int, metavar='SCENE', nargs='+', help='run and generate IO from these scenes')
    run.add_argument('-p', '--procs', type=int, default=1, help='number of processes to use')
    run.add_argument('-t', '--test', action='store_true', help='collect extra information for testing')
    run.add_argument('-g', '--gif', nargs='+', type=int, metavar='AVATAR',
                     help="create gif follows these avatars' path")
    run.add_argument('-s', "--seed", type=int, default=None,
                     help='seed for random steps of the avatars in the scenes (default=scene_num)')
    run.add_argument('-l', "--limit", type=int, metavar='MINUTES', default=None, help='time limit in minutes for scene')
    run.add_argument('-o', "--output", type=str, metavar='PATH', default='IOs',
                     help='output folder path (default=./IOs/)')
    run.add_argument('-c', "--compress", type=int, choices=range(10), metavar='0-9', default=None, nargs='?', const=5,
                     help="output compression level (defualt=5), no compression if not specified.")
    run.add_argument('-k', "--keep", action='store_true', help="don't empty the output folder before running")

    test_help = 'Test that the IOs generated should’ve been generated.'
    test = subparser.add_parser('test', help=test_help, description=test_help)
    test.add_argument('scene_num', type=int, metavar='SCENE', help='scene number to test')
    test.add_argument('-i', "--input", type=str, metavar='PATH', default='IOs',
                      help='input folder path (default=./IOs/)')

    multiply_help = 'Multiply each IO to increase the number of IOs/second.'
    multiply = subparser.add_parser('multiply', help=multiply_help, description=multiply_help)
    multiply.add_argument('scene_nums', type=int, metavar='SCENE', nargs='+', help='scene numbers to multiply')
    multiply.add_argument('-p', '--procs', type=int, default=1, help='number of processes to use')
    multiply.add_argument('-f', '--factor', type=int, required=True, help='multiply each IO by this factor')
    multiply.add_argument('-a', '--avatars', type=int, metavar='AVATAR', default=None, nargs='+',
                          help='avatars to be multiplied')
    multiply.add_argument('-s', "--seed", type=int, default=0, help='seed for time randomization (default=0)')
    multiply.add_argument('-o', "--output", type=str, metavar='PATH', default=None,
                          help='output folder path (default=the input path)')
    multiply.add_argument('-c', "--compress", type=int, choices=range(10), metavar='0-9', default=None, nargs='?',
                          const=5, help="output compression level (defualt=5), no compression if not specified.")
    multiply.add_argument('-i', "--input", type=str, metavar='PATH', default='IOs',
                          help='input folder path (default=./IOs/)')

    args = parser.parse_args()

    if args.command == 'download':
        print(f'Downloading dataset from: {colored(dataset_url)}')
        wget.download(dataset_url, out='wowah.rar')
        print(f'Download complete! Please extract the WoWAH folder from wowah.rar')

    elif args.command == 'build':
        if not os.path.isdir(args.dataset):
            print(
                f'ERROR: {args.dataset} folder does not exist. You can use the "{colored("download")}" command.')
            exit()
        build_scenes(args.dataset, args.length, args.gap)
    elif args.command == 'run':
        if not os.path.isdir("Scenes"):
            print(f'ERROR: Scenes folder does not exist, try to run "{colored("build")}" first')
            exit()
        for scene_num in args.scene_nums:
            scene_file = os.path.join('Scenes', f'scene{scene_num}.csv')
            if not os.path.isfile(scene_file):
                print(f'ERROR: {scene_file} does not exist')
                exit()
        cities_path = os.path.join("Maps", "cities.csv")
        if not os.path.isfile(cities_path):
            print(f'ERROR: {cities_path} does not exist, try to run "{colored("cities")}" first')
            exit()
        if args.gif and any(not os.path.isfile(os.path.join("Maps", f"{c.value}.pickle")) for c in ContinentName):
            print(f'ERROR: Continents maps are missing, try to run "{colored("maps")}" first')
            exit()
        if args.gif is not None:
            args.gif = [str(a) for a in args.gif]
        run_scenes(args.scene_nums, args.output, args.keep, args.compress, args.procs, args.seed, args.limit, args.test,
                   args.gif)
    elif args.command == 'maps':
        create_maps(args.show)
    elif args.command == 'stats':
        if not os.path.isdir(args.dataset):
            print(
                f'ERROR: {args.dataset} folder does not exist. You can use the "{colored("download")}" command.')
            exit()
        calc_stats(args.dataset, args.output, args.show, args.records, args.gap)
    elif args.command == 'cities':
        build_cities(args.seed)
    elif args.command == 'test':
        scene_folder = os.path.join(args.input, f'Scene{args.scene_num}')
        scene_test_data = os.path.join(scene_folder, f"test_data_scene{args.scene_num}.pickle")
        if not os.path.isdir(scene_folder):
            print(f'ERROR: {scene_folder} does not exist, try to run "{colored("run")}" first')
            exit()
        if not os.path.isfile(scene_test_data):
            print(f'ERROR: {scene_test_data} does not exist, try to run "{colored("run -t")}" first')
            exit()
        test_scene(args.scene_num, args.input)
    elif args.command == 'multiply':
        for scene_num in args.scene_nums:
            scene_folder = os.path.join(args.input, f'Scene{scene_num}')
            if not os.path.isdir(scene_folder):
                print(f'ERROR: {scene_folder} does not exist, try to run "{colored("run")}" first')
                exit()
        if args.output is None:
            args.output = args.input
        if args.avatars is not None:
            args.avatars = [str(a) for a in args.avatars]
        multiply_scenes(args.scene_nums, args.input, args.output, args.compress, args.factor, args.seed, args.procs,
                        args.avatars)
