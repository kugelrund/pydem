import argparse
import copy
import os

import matplotlib.pyplot as plt
import numpy

import stats
import format
from messages import ItemFlags
import printing
import smoothing


class MemoryBuffer:
    def __init__(self, buffer):
        self.__buffer = buffer
        self.length = len(buffer)
        self.pos = 0

    def read(self, num=None):
        if self.pos < 0 or self.pos > self.length:
            raise IndexError("Read position out of bounds!")
        if self.pos == self.length:
            return b''
        if num is None:
            ret = self.__buffer[self.pos:]
            self.pos = self.length
            return ret
        else:
            if num < 0:
                raise IndexError("Amount to read has to be positive!")
            if self.pos + num > self.length:
                raise IndexError("Can't read that many bytes!")
            ret = self.__buffer[self.pos:self.pos+num]
            self.pos += num
            return ret

    def tell(self):
        return self.pos

    def seek(self, offset, from_what=0):
        if from_what == 0:
            self.pos = offset
        elif from_what == 1:
            self.pos += offset
        elif from_what == 2:
            self.pos = self.length - offset

def parse_demo(filepath_demo):
    with open(filepath_demo, 'rb', buffering=0) as f:
        memory_stream = MemoryBuffer(f.read())
    return format.Demo.parse(memory_stream)


def smooth(demo):
    # TODO: some blocks dont have time message and those seem to always repeat
    # the exact same viewangles. should get rid of those before smoothing and
    # then assign them properly afterwards
    time = demo.get_time()
    yaw = demo.get_yaw()
    pitch = demo.get_pitch()
    fixangle_indices = demo.get_fixangle_indices()
    split_indices = [-1] + fixangle_indices + [len(time)-1]

    yaw_smoothed = numpy.array(yaw)
    pitch_smoothed = numpy.array(pitch)
    for i, _ in enumerate(split_indices[:-1]):
        begin = split_indices[i] + 1
        end = split_indices[i+1] + 1
        if begin + 5 > end:
            continue  # dont smooth very short segments
        yaw_smoothed[begin:end] = smoothing.smooth(time[begin:end], yaw[begin:end])
        pitch_smoothed[begin:end] = smoothing.smooth(time[begin:end], pitch[begin:end])

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(time, yaw, '.', markersize=6)
    ax.plot(time, yaw_smoothed, '.', markersize=3)
    ax.plot(time, pitch, '.', markersize=6)
    ax.plot(time, pitch_smoothed, '.', markersize=3)
    ax.plot(time[fixangle_indices], yaw[fixangle_indices], 'x')
    ax.plot(time[fixangle_indices], pitch[fixangle_indices], 'x')
    plt.show()

    demo.set_yaw(yaw_smoothed)
    demo.set_pitch(pitch_smoothed)


def next_spawnparams(stats: format.ClientStats) -> format.ClientStats:
    new_stats = copy.deepcopy(stats)
    new_stats.items = stats.items & ~(stats.items & (
        ItemFlags.SUPERHEALTH|ItemFlags.KEY1|ItemFlags.KEY2|
        ItemFlags.INVISIBILITY|ItemFlags.INVULNERABILITY|ItemFlags.SUIT|
        ItemFlags.QUAD))
    new_stats.health = min(max(stats.health, 50), 100)
    new_stats.shells = max(stats.shells, 25)
    return new_stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('demos', type=str, nargs='*', help="Path to input demo files.")
    parser.add_argument('--remove_grenade_counter', action='store_true')
    parser.add_argument('--remove_prints', type=str, action='append',
                        help="Removes notification prints that contain the given text.")
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--coop', dest='coop_demos', action='append', type=str, nargs='*',
                        help="Path to corresponding demo files for another player.")
    args = parser.parse_args()
    if args.coop_demos:
        assert args.stats  # TODO: Better error message

    demo_paths = []
    demos = []

    if args.stats:
        demo_paths_per_player = [args.demos]
        if args.coop_demos:
            demo_paths_per_player += args.coop_demos

        demo_previous_per_player = None
        for demo_path_per_player in zip(*demo_paths_per_player, strict=True):
            if not demo_previous_per_player:
                demo_previous_per_player = [parse_demo(paths[0])
                                           for paths in demo_paths_per_player]
                demo_paths.extend(demo_path_per_player)
                demos.extend(demo_previous_per_player)
                continue
            print("========== Fixing stats for " + ', '.join(demo_path_per_player) + " ==========")
            demo_per_player = [parse_demo(p) for p in demo_path_per_player]

            new_stats_per_player = [next_spawnparams(d.get_final_client_stats())
                                   for d in demo_previous_per_player]
            stats.apply_new_start_stats(new_stats_per_player, demo_per_player,
                                        is_coop=args.coop_demos)

            demo_paths.extend(demo_path_per_player)
            demos.extend(demo_per_player)
            demo_previous_per_player = demo_per_player
    else:
        demo_paths = args.demos
        demos = [parse_demo(path) for path in demo_paths]


    for demo in demos:
        if args.remove_grenade_counter:
            printing.remove_grenade_counter(demo)
        if args.remove_prints:
            printing.remove_prints(demo, args.remove_prints)


    for path, demo in zip(demo_paths, demos):
        with open(os.path.splitext(path)[-2] + '_out.dem', 'wb') as f:
            demo.write(f)


if __name__ == "__main__":
    main()
