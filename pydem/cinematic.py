import numpy

from . import messages


def get_time_messages(block):
    return [m for m in block.messages if isinstance(m, messages.TimeMessage)]


def fade(demo, time_start, duration, backwards):
    time_previous = None
    for b in (reversed(demo.blocks) if backwards else demo.blocks):
        time_messages = get_time_messages(b)
        if not time_messages:
            continue
        time_current = numpy.average([m.time for m in time_messages])
        if time_current == time_previous:
            # do not repeat cshift command if same time
            continue
        time_elapsed = time_start - time_current if backwards else time_current - time_start
        opacity = min(1.0, 1.0 - (time_elapsed / duration))
        opacity_byte = int(round(255 * opacity))
        if opacity_byte <= 0:
            break
        b.messages.append(messages.StuffTextMessage(f"v_cshift 0 0 0 {opacity_byte}".encode()))
        time_previous = time_current


def fadein(demo, duration):
    time_messages = [m for b in demo.blocks for m in get_time_messages(b)]
    time_smallest = min(m.time for m in time_messages)
    time_second_smallest = min(m.time for m in time_messages if m.time > time_smallest)
    time_start = time_second_smallest
    fade(demo, time_start, duration, backwards=False)


def fadeout(demo, duration):
    time_messages = [m for b in demo.blocks for m in get_time_messages(b)]
    time_largest = max(m.time for m in time_messages)
    time_second_largest = max(m.time for m in time_messages if m.time < time_largest)
    time_end = time_second_largest
    fade(demo, time_end, duration, backwards=True)
