import argparse
import copy
import os

import matplotlib.pyplot as plt
import numpy

import stats
import format
from messages import ItemFlags
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
    args = parser.parse_args()

    demo = parse_demo(args.demos[0])
    for i in range(len(args.demos) - 1):
        demo_next = parse_demo(args.demos[i+1])

        #smooth(demo)


        client_stats_list = demo.get_client_stats()
        final_client_stats = [client_stats for client_stats in client_stats_list if client_stats][-1]
        next_client_stats = next_spawnparams(final_client_stats)
        print(f'{args.demos[i]} ends with {next_client_stats}')

        client_stats_list = demo_next.get_client_stats()
        first_client_stats = [client_stats for client_stats in client_stats_list if client_stats][0]
        print(f'{args.demos[i+1]} starts with {first_client_stats}')

        is_coop = True
        new_client_stats_list, actual_collections = stats.rebuild_stats(
            next_client_stats, client_stats_list,
            stats.get_backpack_collections(demo_next),
            stats.get_static_collections(demo_next),
            stats.get_possible_collections(demo_next),
            stats.get_damage(demo_next), is_coop)
        #for a, b in zip(client_stats_list, new_client_stats_list):
        #    assert a == b
        demo_next.set_client_stats(new_client_stats_list)
        stats.fix_collection_events(actual_collections, demo_next)

        with open(os.path.splitext(args.demos[i+1])[-2] + '_out.dem', 'wb') as f:
            demo_next.write(f)
        demo = demo_next


if __name__ == "__main__":
    main()
