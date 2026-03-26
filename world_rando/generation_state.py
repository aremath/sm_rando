from world_rando.event_logging import ObjectManager, EventFile

class GenerationState(object):

    def __init__(self, settings):
        # Used to tell the current generator what to name itself (among other things)
        self.current_region = None
        self.current_room = None
        out_f = settings.output_settings["output"]
        #TODO: should we have a generation NAME?
        # Then put everything in output/name/...
        # So e.g. output/tiny/crateria, output/default/crateria, etc.?
        events_fname = f"{out_f}/generate.events"
        ei = EventFile(events_fname)
        # Empty OM
        self.manager = ObjectManager(ei)

