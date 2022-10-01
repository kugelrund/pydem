import format
import messages


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
