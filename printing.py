import format
import messages
import re


def fix_intermission_lag(demo: format.Demo):
    pattern = b"The recorded time was (?:(\d)*:)?([0-5]?\d.\d{5})"
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
                    messages_to_shift = [m for m in block.messages
                        if (isinstance(m, messages.IntermissionMessage) or
                            isinstance(m, messages.CdTrackMessage))]
                    for message_to_shift in messages_to_shift:
                        block.messages.remove(message_to_shift)
                        preceding_block.messages.append(message_to_shift)
                break
            elif current_time < correct_intermission_time:
                raise ValueError("Could not find correct intermission time")


def remove_grenade_counter(demo: format.Demo):
    for block in demo.blocks:
        grenade_counter_messages = [m for m in block.messages
            if (isinstance(m, messages.CenterPrintMessage) and
                m.text.startswith(b"Grenade"))]
        for m in grenade_counter_messages:
            block.messages.remove(m)


def remove_prints(demo: format.Demo, exclude_patterns=list[str]):
    for block in demo.blocks:
        print_messages = [m for m in block.messages
                          if isinstance(m, messages.PrintMessage)]
        for m in print_messages:
            if any(pattern.encode('ascii') in m.text for pattern in exclude_patterns):
                block.messages.remove(m)
