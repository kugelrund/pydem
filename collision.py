def extend_bounds_collectable(absmin: list[float], absmax: list[float]):
    # following SV_LinkEdict
    return ([absmin[0] - 15.0, absmin[1] - 15.0, absmin[2]],
            [absmax[0] + 15.0, absmax[1] + 15.0, absmax[2]])

def extend_bounds_player(absmin: list[float], absmax: list[float]):
    # following SV_LinkEdict
    return [x - 1.0 for x in absmin], [x + 1.0 for x in absmax]

def bounds(pos: list[float], mins: list[float], maxs: list[float]):
    absmin = [x + x_mins for x, x_mins in zip(pos, mins)]
    absmax = [x + x_maxs for x, x_maxs in zip(pos, maxs)]
    return absmin, absmax

def bounds_collectable(pos: list[float], mins: list[float], maxs: list[float]):
    absmin, absmax = bounds(pos, mins, maxs)
    return extend_bounds_collectable(absmin, absmax)

def interval_distance(interval1, interval2):
    a1, b1 = interval1
    a2, b2 = interval2
    return max(a1 - b2, a2 - b1)

def distance(bounds1, bounds2):
    absmin1, absmax1 = bounds1
    absmin2, absmax2 = bounds2
    return max([interval_distance((a1, b1), (a2, b2)) for a1, b1, a2, b2
                in zip(absmin1, absmax1, absmin2, absmax2)])


class PlayerBounds:
    mins, maxs = [-16.0, -16.0, -24.0], [16.0, 16.0, 32.0]
    @staticmethod
    def bounds(pos: list[float]):
        absmin, absmax = bounds(pos, PlayerBounds.mins, PlayerBounds.maxs)
        return extend_bounds_player(absmin, absmax)

    @staticmethod
    def center(pos: list[float]):
        return [a + 0.5*(b+c) for a, b, c in
                zip(pos, PlayerBounds.mins, PlayerBounds.maxs)]

def bounds_player(pos: list[float]):
    return PlayerBounds.bounds(pos)
