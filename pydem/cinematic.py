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
        opacity = numpy.clip(1.0 - (time_elapsed / duration), 0.0, 1.0)
        opacity_byte = int(round(255 * opacity))
        b.messages.append(messages.StuffTextMessage(f"v_cshift 0 0 0 {opacity_byte}\n".encode()))
        if opacity_byte <= 0:
            break
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


def merge_pair(demo, demo_other):
    time = demo.get_time()
    time_other = demo_other.get_time()
    i = 0
    for i_other, _ in enumerate(demo_other.blocks):
        while time_other[i_other] > time[i]:
            i += 1
            if i >= len(demo.blocks):
                return

        if time[i] != time_other[i_other]:
            # The starts are usually different between host and client,
            # everything else should line up.
            continue

        ent_msgs = [m for m in demo.blocks[i].messages
                    if isinstance(m, messages.EntityUpdateMessage)]
        ent_msgs_other = [m for m in demo_other.blocks[i_other].messages
                          if isinstance(m, messages.EntityUpdateMessage)]
        for msg_other in ent_msgs_other:
            msg = [m for m in ent_msgs if m.num == msg_other.num]
            if msg:
                msg, = msg
                if msg != msg_other:
                    raise ValueError("Demos to be merged do not match")
            else:
                demo.blocks[i].messages.append(msg_other)


def merge(demos):
    demo_base = demos[0]
    for demo in demos[1:]:
        merge_pair(demo_base, demo)
    return demo_base
