import re

from . import format
from . import messages


def fix_intermission_lag(demo: format.Demo):
    pattern = rb"The recorded time was (?:(\d)*:)?([0-5]?\d.\d{5})"
    for i, block in enumerate(demo.blocks):
        if not any(isinstance(m, messages.IntermissionMessage)
                   for m in block.messages):
            continue

        for following_block in demo.blocks[i:]:
            text = b''.join(m.text for m in following_block.messages
                            if isinstance(m, messages.PrintMessage))
            match = re.search(pattern, text)
            if match:
                minutes = int(match.group(1)) if match.group(1) else 0
                seconds = float(match.group(2))
                assert seconds < 60
                correct_intermission_time = minutes * 60 + seconds
                break

        for preceding_block in reversed(demo.blocks[:i]):
            time_messages = [m for m in preceding_block.messages
                             if isinstance(m, messages.TimeMessage)]
            if not time_messages:
                continue
            assert len(time_messages) == 1

            current_time = time_messages[0].time
            if abs(current_time - correct_intermission_time) < 1e-5:
                if preceding_block != demo.blocks[i-1]:
                    print(f"Shifting intermission to {current_time}")
                    messages_to_shift = [m for m in block.messages
                        if (isinstance(m, messages.IntermissionMessage) or
                            isinstance(m, messages.CdTrackMessage))]
                    for message_to_shift in messages_to_shift:
                        block.messages.remove(message_to_shift)
                        preceding_block.messages.append(message_to_shift)
                break
            elif current_time < correct_intermission_time:
                raise ValueError("Could not find correct intermission time")


def fix_intermission_transition(demo: format.Demo):
    reinsert_data = []
    for i, block in enumerate(demo.blocks):
        intermission_messages = [m for m in block.messages if
                                 isinstance(m, messages.IntermissionMessage)]
        if not intermission_messages:
            continue

        new_block_index = demo.get_previous_block_index_with_time_message(i)
        if not any(isinstance(m, messages.SetAngleMessage)
                   for m in demo.blocks[new_block_index].messages):
            print("Warning: could not find expected setangle message, "
                  "not fixing intermission transition")
            continue

        for m in intermission_messages:
            block.messages.remove(m)
        reinsert_data.append((new_block_index, intermission_messages))

    for (i, intermission_messages) in reversed(reinsert_data):
        demo.blocks.insert(i, format.Block(demo.blocks[i].viewangles,
                                           intermission_messages))


def instant_skin_color(demo: format.Demo):
    for block in demo.blocks:
        for m in [m for m in block.messages
                  if isinstance(m, messages.UpdateColorsMessage)]:
            block.messages.append(messages.EntityUpdateMessage(
                messages.UpdateFlags.SIGNAL, m.player_id + 1, None, None, None,
                None, None, None, None, None, None, None, None, None, None))


def remove_grenade_counter(demo: format.Demo):
    for block in demo.blocks:
        grenade_counter_messages = [m for m in block.messages
            if (isinstance(m, messages.CenterPrintMessage) and
                m.text.startswith(b"Grenade"))]
        for m in grenade_counter_messages:
            block.messages.remove(m)


def remove_pauses(demo: format.Demo):
    is_paused_list = []
    is_paused = False
    for block in demo.blocks:
        for m in [m for m in block.messages
                  if isinstance(m, messages.SetPauseMessage)]:
            is_paused = m.paused
            block.messages.remove(m)
        is_paused_list.append(is_paused)

    for block, is_paused in zip(reversed(demo.blocks), reversed(is_paused_list)):
        if is_paused:
            block.viewangles = viewangles_after_unpause
            for m in [m for m in block.messages
                      if isinstance(m, messages.EntityUpdateMessage)]:
                block.messages.remove(m)
            # we are adding these even on the earliest blocks now (for example
            # before spawnbaseline even happened), which might not be that nice.
            # on the other hand it also fixes interpolation of items on the
            # first frame, so maybe not too bad? or is that a joequake bug?
            block.messages.extend(entity_updates_after_unpause)
        else:
            viewangles_after_unpause = block.viewangles
            entity_updates = [m for m in block.messages
                              if isinstance(m, messages.EntityUpdateMessage)]
            if entity_updates:
                entity_updates_after_unpause = entity_updates


def remove_prints(demo: format.Demo, exclude_patterns=list[str]):
    for block in demo.blocks:
        print_messages = [m for m in block.messages
                          if isinstance(m, messages.PrintMessage)]
        for m in print_messages:
            if any(pattern.encode('ascii') in m.text for pattern in exclude_patterns):
                block.messages.remove(m)


def remove_sounds(demo: format.Demo, exclude_patterns=list[str]):
    _, sounds_precache = demo.get_precaches()
    for block in demo.blocks:
        sound_messages = [m for m in block.messages
                          if isinstance(m, messages.SoundMessage)]
        for m in sound_messages:
            if any(pattern.encode('ascii') in sounds_precache[m.sound_num]
                   for pattern in exclude_patterns):
                block.messages.remove(m)


def cut_end_after(demo: format.Demo, duration: float, end_kind: str):
    if end_kind == 'intermission':
        message_type = messages.IntermissionMessage
    elif end_kind == 'finale':
        message_type = messages.FinaleMessage
    else:
        raise ValueError(f"Unsupported kind of end '{end_kind}'")

    times = demo.get_time()
    time_end = None
    for i, block in enumerate(demo.blocks):
        if any(isinstance(m, message_type) for m in block.messages):
            time_end = times[i]
            break
    if not time_end:
        print(f"Warning: no {end_kind} found, not cutting anything")
        return

    i_first_to_remove = next(
        (i for (i, t) in enumerate(times) if t > time_end + duration),
        len(demo.blocks))
    if i_first_to_remove == len(demo.blocks):
        print(f"Warning: {end_kind} is shorter than duration to cut to!")
    # assuming that last block is disconnect message
    del demo.blocks[i_first_to_remove:-1]


def replace_sound(demo: format.Demo, replacement_pairs: list[list[str]]):
    replacement_pairs_bytes = [[x.encode('utf-8') for x in pair]
                               for pair in replacement_pairs]
    _, sounds_precache = demo.get_precaches()
    for block in demo.blocks:
        for m in block.messages:
            if not isinstance(m, messages.SoundMessage):
                continue
            for old_sound, new_sound in replacement_pairs_bytes:
                if sounds_precache[m.sound_num] == old_sound:
                    m.sound_num = sounds_precache.index(new_sound)


def replace_weaponmodel(demo: format.Demo, replacement_pairs: list[list[str]]):
    replacement_pairs_bytes = [[x.encode('utf-8') for x in pair]
                               for pair in replacement_pairs]
    models_precache, _ = demo.get_precaches()
    for block in demo.blocks:
        for m in block.messages:
            if not isinstance(m, messages.ClientDataMessage):
                continue
            for old_weaponmodel, new_weaponmodel in replacement_pairs_bytes:
                if models_precache[m.weapon] == old_weaponmodel:
                    m.weapon = models_precache.index(new_weaponmodel)