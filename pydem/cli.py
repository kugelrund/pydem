import argparse
import os

from . import cinematic
from . import cleanup
from . import format
from . import smoothing
from . import spawnparams
from . import stats


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('demos', type=str, nargs='*', help="Path to input demo files.")
    parser.add_argument('--fadein', type=float, default=0.0,
        help="Add fade from black to start of demo with a given duration in seconds")
    parser.add_argument('--fadeout', type=float, default=0.0,
        help="Add fade to black to end of demo with a given duration in seconds")
    parser.add_argument('--fix_intermission_lag', action='store_true',
        help="Fix intermissions that start too late in coop demos due to "
             "network lag, which can cause a wrong final time to be shown.")
    parser.add_argument('--instant_skin_color', action='store_true',
        help="Workaround to make player skin color be applied instantly at the "
             "start of a demo. Especially useful for coop demos.")
    parser.add_argument('--remove_grenade_counter', action='store_true')
    parser.add_argument('--remove_pauses', action='store_true',
        help="Remove pauses from demo. Also copies entity updates and "
             "viewangles from after the pause to throughout the pause to avoid "
             "jumps due to pauses at the start of a demo.")
    parser.add_argument('--remove_prints', type=str, action='append',
        help="Removes notification prints that contain the given text.")
    parser.add_argument('--remove_sounds', type=str, action='append',
        help="Removes sounds whose name contains the given text.")
    parser.add_argument('--smooth_viewangles', action='store_true')
    parser.add_argument('--spawnparams', action='store_true',
        help="Write .cfg files for spawnparams")
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--coop', dest='coop_demos', action='append', type=str,
                        nargs='*', default=[],
                        help="Path to corresponding demo files for another player.")
    args = parser.parse_args()

    # this is a list of size "number of players" where each element is a list of
    # size len(args.demos) that contains paths to the demos for the
    # corresponding player
    foreach_player_paths = [args.demos] + [d for d in args.coop_demos]
    # this is a list of size len(args.demos) where each element is a list of
    # size "number of players" that contains the path to the corresponding demo
    # for each player
    paths_per_player = list(zip(*foreach_player_paths, strict=True))
    # this is a list of size len(args.demos) where each element is a list of
    # size "num players" that contains the corresponding demo for each player
    demos_per_player = [[parse_demo(path) for path in path_per_player]
                        for path_per_player in paths_per_player]

    if args.stats:
        demo_previous_per_player = demos_per_player[0]
        for demo_path_per_player, demo_per_player in zip(paths_per_player[1:],
                                                         demos_per_player[1:]):
            print("========== Fixing stats for " + ', '.join(demo_path_per_player) + " ==========")
            new_stats_per_player = [spawnparams.nextmap(d.get_final_client_stats())
                                   for d in demo_previous_per_player]
            stats.apply_new_start_stats(new_stats_per_player, demo_per_player,
                                        is_coop=args.coop_demos)
            demo_previous_per_player = demo_per_player

    if args.spawnparams:
        for demo_path_per_player, demo_per_player in zip(paths_per_player,
                                                         demos_per_player):
            cfg_path = demo_path_per_player[0].replace('.dem', '_end.cfg')
            spawnparams.write_cfg(cfg_path, demo_per_player)

    # forget about distinction of belonging to different players, as this is not
    # important anymore for further operations: i.e. flatten the lists of lists
    demo_paths = [path for path_per_player in paths_per_player
                  for path in path_per_player]
    demos = [demo for demo_per_player in demos_per_player
             for demo in demo_per_player]

    for demo in demos:
        if args.fix_intermission_lag:
            cleanup.fix_intermission_lag(demo)
        if args.instant_skin_color:
            cleanup.instant_skin_color(demo)
        if args.remove_grenade_counter:
            cleanup.remove_grenade_counter(demo)
        if args.remove_pauses:
            cleanup.remove_pauses(demo)
        if args.remove_prints:
            cleanup.remove_prints(demo, args.remove_prints)
        if args.remove_sounds:
            cleanup.remove_sounds(demo, args.remove_sounds)
        if args.smooth_viewangles:
            smoothing.smooth_viewangles(demo)
        if args.fadein > 0.0:
            cinematic.fadein(demo, args.fadein)
        if args.fadeout > 0.0:
            cinematic.fadeout(demo, args.fadeout)

    for path, demo in zip(demo_paths, demos):
        with open(os.path.splitext(path)[-2] + '_out.dem', 'wb') as f:
            demo.write(f)
