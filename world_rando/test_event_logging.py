from .coord import Coord
from .event_logging import *

def test_eventfile():
    inter1 = EventFile("../output/test.events")
    object_manager = ObjectManager(inter1)
    # Make two dicts
    # manager, name, parent, interpretation, kv types
    l = LogDict(object_manager, "d1", None, None, {"key_type": "int", "value_type": "int"})
    l2 = LogDict(object_manager, "d2", "d1", None, {"key_type": "int", "value_type": "int"})
    # Do some stuff
    l[0] = 1
    l2[1] = 3
    l[1] = 2
    l2[4] = 8
    # Create a second ObjectManager and replay the events
    inter2 = EventList()
    object_manager2 = ObjectManager(inter2, inter1)
    # Make sure the data matches after replay
    assert object_manager.objects["d1"].data == object_manager2.objects["d1"].data


def test_encoding_basic():
    #TODO: test it with event file
    event_interface = EventList()
    manager = ObjectManager(event_interface)
    l_c = LogDict(manager, "coord_dict", None, None, {"key_type": "Coord", "value_type": "Set(Coord)"})
    l_c[Coord(3,5)] = set([Coord(2,7), Coord(3,4)])
    m2 = ObjectManager(EventList(), manager.ei)
    assert m2.objects["coord_dict"][Coord(3,5)] == l_c[Coord(3,5)]

def test_encoding_pointers():
    # Testing pointer encoding
    manager = ObjectManager(EventList())
    dict_layer_1 = LogDict(manager, "dl1", None, None, {"key_type": "Coord", "value_type": "LPointer"})
    dict_layer_2 = LogDict(manager, "dl2", None, None, {"key_type": "Coord", "value_type": "Coord"})
    dict_layer_1[Coord(2,3)] = dict_layer_2
    dict_layer_1[Coord(2,3)][Coord(3,4)] = Coord(4,5)
    m2 = ObjectManager(EventList(), manager.ei)
    assert m2.objects["dl1"][Coord(2,3)] == m2.objects["dl2"]
    assert m2.objects["dl1"][Coord(2,3)][Coord(3,4)] == dict_layer_1[Coord(2,3)][Coord(3,4)]
    # Make sure the "pointer" part is working
    m2.objects["dl2"][Coord(5,6)] = Coord(6,7)
    assert m2.objects["dl1"][Coord(2,3)][Coord(5,6)] == Coord(6,7)

