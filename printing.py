import format
import messages


def remove_grenade_counter(demo: format.Demo):
    for i in reversed(range(len(demo.blocks))):
        grenade_counter_messages = [m for m in demo.blocks[i].messages
            if (isinstance(m, messages.CenterPrintMessage) and
                m.text.startswith(b"Grenade"))]
        if len(grenade_counter_messages) == len(demo.blocks[i].messages):
            del demo.blocks[i]
        else:
            for m in grenade_counter_messages:
                demo.blocks[i].messages.remove(m)


def remove_prints(demo: format.Demo, exclude_patterns=list[str]):
    for block in demo.blocks:
        print_messages = [m for m in block.messages
                          if isinstance(m, messages.PrintMessage)]
        for m in print_messages:
            if any(pattern.encode('ascii') in m.text for pattern in exclude_patterns):
                block.messages.remove(m)
