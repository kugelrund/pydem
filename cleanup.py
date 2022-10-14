import format
import messages


def instant_skin_color(demo: format.Demo):
    for block in demo.blocks:
        for m in [m for m in block.messages
                  if isinstance(m, messages.UpdateColorsMessage)]:
            block.messages.append(messages.EntityUpdateMessage(
                messages.UpdateFlags.SIGNAL, m.player_id + 1, None, None, None,
                None, None, None, None, None, None, None, None, None, None))


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
