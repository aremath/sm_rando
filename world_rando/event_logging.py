import json
from typing import Dict, Iterator, MutableMapping, TypeVar, Iterable, Optional
KT = TypeVar("KT")
VT = TypeVar("VT")
from abc import ABC, abstractmethod
from collections.abc import Mapping

from .coord import Coord

class ActionException(Exception):
    def __init__(self, message):
        super().__init__(message)
# The nice thing about this is that different ObjectManagers can use different interfaces for the same underlying events!
class EventInterface(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def write_event(self, event) -> None:
        pass

    @abstractmethod
    def read_events(self) -> [dict[str, str]]:
        pass

    @abstractmethod
    def events_iter(selt) -> Iterator[dict[str, str]]:
        pass

# The most basic interface, simply represent the events in a list
class EventList(EventInterface):

    def __init__(self) -> None:
        self.events = []

    def write_event(self, event) -> None:
        self.events.append(event)

    def read_events(self) -> [dict[str, str]]:
        return self.events

    def events_iter(self) -> Iterator[dict[str, str]]:
        for e in self.events:
            yield e

# Writing the events to a file
#TODO: this won't work on everything
# For some types, json.loads(json.dumps(s)) != s
#TODO: this is not actually a JSON file!
# No comma delimiters between objects
# But, can't write the JSON file in an online way since the opening and closing brackets will not work properly
#TODO: self.jsonify() to add list brackets at the start and end of the file and commas at the end of each line.
class EventFile(EventInterface):

    # log_file should already be open(x, "rw")
    def __init__(self, log_path) -> None:
        # Leave the file open. If the program writes many events, opening and closing the file will create significant overhead.
        self.file = open(log_path, "w+")

    def write_event(self, event) -> None:
        self.file.write(json.dumps(event) + "\n")
        #self.file.flush() # I don't think it's necessary to flush the buffer for every event

    def read_events(self) -> [dict[str, str]]:
        events = []
        self.file.seek(0)
        for line in self.file.readlines():
            event = json.loads(line)
            events.append(event)
        # Return to the end of the file
        self.file.seek(0, 2)
        return events

    def events_iter(self) -> Iterator[dict[str, str]]:
        self.file.seek(0)
        for line in self.file.readlines():
            event = json.loads(line)
            yield event
        # Return to the end of the file
        self.file.seek(0, 2)

    # This breaks the object, of course
    def close(self):
        self.file.close()

class ObjectManager(object):

    def __init__(self, event_interface, ei_from=None) -> None:
        self.objects = {}
        self.ei = event_interface
        # Optionally replay events from a different EI
        if ei_from:
            for event in ei_from.events_iter():
                self.replay(event)

    # 'info' is a generic field to include other information needed to properly reconstruct the object
    # Logging classes will specify what fields info must have
    def create(self, object, type : str, info) -> None:
        if object.name in self.objects:
            raise ActionException(f"Object named {object.name} already exists!")
        self.objects[object.name] = object
        event = {
            "action" : "create",
            "name" : object.name,
            "parent" : object.parent,
            "interpretation" : object.interpretation,
            "type" : type,
            "info" : info
        }
        self.ei.write_event(event)

    def event(self, event):
        self.ei.write_event(event)

    def replay(self, event):
        # If it's a create action then we need to create a new object
        if event["action"] == "create":
            # Constructor for the new object will record the necessary "create" event
            event_type = event["type"]
            if event_type not in type_dict:
                raise ActionException(f"Tried to create an object with an unknown type: {event_type}")
            type_dict[event_type](self, event["name"], event["parent"], event["interpretation"], event["info"])
        # Ticks are merely for timing information, and do not affect Python World replay
        elif event["action"] == "tick":
            pass
        else:
            # Use the object dict to figure out which object should replay the event
            self.objects[event["name"]].replay(event)

    # Ticks are used to control the JS World replay
    # An algorithm can introduce ticks (for example) once per iteration
    # In JSWorld, the ticks are used for two things:
    # Step Mode can either be event-by-event or tick-by-tick (tick-by-tick is default)
    # Play Mode uses the tick operation annotation to know how long to pause during the tick.
    #TODO: is it maybe better to have a call stack?
    # So JSWorld can visualize the call stack
    # e.g.
    # Crateria Map Gen
    #   Subroom Creation
    #     Merging...
    # Seems annoying to maintain though...
    # Can also keep completed process names around marked in green...?
    def tick(self, operation):
        tick = {
            "action": "tick",
            "operation": operation,
        }
        self.ei.write_event(tick)

# Encoding and Decoding:
# When serializing an object to JSON, it may not be possible to represent the object directly in JSON
# Encoders / Decoders provide a way to serialize and deserialize non-JSON objects

# Treats it like a tuple and converts to list, so this operation is identity
# Still useful to write it like this for later, though
coord_encoder = lambda x: x
# Convert back from list using the Coord constructor
coord_decoder = lambda x: Coord(*x)
set_encoder = lambda x: list(x)
set_decoder = lambda x: set(x)
identity = lambda x: x

# If f is an encoder for X then setf_encoder(f) is an encoder for Set(X)
# Convert the set of encoded values to a list
setf_encoder = lambda encode: (lambda x: list([encode(y) for y in x]))
# Similarly, setf_decoder(f) is a decoder for Set(X) if f is a decoder for X
# Convert the list of decoded values to a set
setf_decoder = lambda decode: (lambda x: set([decode(y) for y in x]))

#NOTE: forces dicts to be "well-typed" i.e. only have one type of keys and one type of values
#NOTE: does not actually CHECK that dicts are well-typed, and in fact dicts that are not well-typed will not be reconstructed properly

# If you want to create a data structure with a new type, register the encoder / decoder here!
encoders = {
    "Set": set_encoder, # Generic encoder for sets of jsonables
    #TODO: ideally, would parse the type and apply the necessary encoders
    "Set(Coord)": setf_encoder(coord_encoder)
}
decoders = {
    "Coord": coord_decoder,
    "Set": set_decoder,
    "Set(Coord)": setf_decoder(coord_decoder)
}

# LPointer type:
# If a logging dict has a value which is another logging dict, in Python that is represented with a reference / pointer
# Obviously, that pointer cannot be serialized.
# However, the ObjectManager keeps track of object names in the object table
# During replay, the ObjectManager will have a reference to each reconstructed object stored by name
# So if we serialize the object name, we can recover the object reference, and pass that reference during assignment

# Generic encoder / decoder functions that depend on the type
def log_encode(x, type, manager):
    if type == "LPointer":
        return f"Pointer({x.name})"
    else:
        if type in encoders:
            encoder = encoders[type]
            return encoder(x)
        # If there's no encoder (for example, int), then the value can be serialized to JSON directly
        else:
            return x

def log_decode(x, type, manager):
    # Use the manager to follow the pointer and return the correct object
    # Nested logging pointers will take care of themselves
    if type == "LPointer":
        # Ugly way to find the name inside of the parens
        name = x.split("(")[1][:-1]
        # Trust that the object with the right name will have been created since the events are processed in order
        return manager.objects[name]
    else:
        if type in decoders:
            decoder = decoders[type]
            return decoder(x)
        else:
            return x

# https://stackoverflow.com/questions/61112684/how-to-subclass-a-dictionary-so-it-supports-generic-type-hints
class LogDict(MutableMapping[KT, VT]):

    def __init__(self, log : Optional[ObjectManager], name, parent, interpretation, info, dictionary=None, /, **kwargs) -> None:
        # info should contain "key_type" and "value_type" strs that index the encoders/decoders dicts
        self.name = name
        self.parent = parent
        self.interpretation = interpretation
        self.key_type = info["key_type"]
        self.value_type = info["value_type"]
        if log is not None:
            log.create(self, "dict", info)
        self.log = log
        # Save the ID in order to log correctly
        self.data: Dict[KT, VT] = {}
        if dictionary is not None:
            self.update(dictionary)
        if kwargs:
            print(kwargs)
            self.update(kwargs)

    def __contains__(self, key: VT) -> bool:
        return key in self.data

    def __delitem__(self, key: KT) -> None:
        if self.log is not None:
            event = {
                "name": self.name,
                "action": "deleteitem",
                "key": log_encode(key, self.key_type, self.log),
            }
            self.log.event(event)
        del self.data[key]

    def __getitem__(self, key: KT) -> VT:
        if key in self.data:
            return self.data[key]
        raise KeyError(key)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[KT]:
        return iter(self.data)

    def __setitem__(self, key: KT, value: VT) -> None:
        if self.log is not None:
            event = {
                "name": self.name,
                "action": "setitem",
                "key": log_encode(key, self.key_type, self.log),
                "value": log_encode(value, self.value_type, self.log),
            }
            self.log.event(event)
        self.data[key] = value

    @classmethod
    def fromkeys(cls, iterable: Iterable[KT], value: VT) -> "LogDict":
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    #TODO: some way to log a batch rather than logging each change separately?
    def update(self, other=(), /, **kwds) -> None:
        if isinstance(other, Mapping):
            for key in other:
                # Use self[key] so that it will be logged through __setitem__
                #self.data[key] = other[key]
                self[key] = other[key]
        elif hasattr(other, "keys"):
            for key in other.keys():
                #self.data[key] = other[key]
                self[key] = other[key]
        else:
            for key, value in other:
                #self.data[key] = value
                self[key] = value
        for key, value in kwds.items():
            #self.data[key] = value
            self[key] = value

    def replay(self, event):
        match event["action"]:
            case "deleteitem":
                key = log_decode(event["key"], self.key_type, self.log)
                del self[event["key"]]
            case "setitem":
                key = log_decode(event["key"], self.key_type, self.log)
                value = log_decode(event["value"], self.value_type, self.log)
                # Note: this will also create an event for the event replay, since it calls __setitem__
                self[key] = value
            case _:
                raise ActionException("Action Not Found")

    def __repr__(self):
        return f"L{self.data.__repr__()}"

# Type Dict
# For each Logging type, this is a table that stores the string name of the type with the constructor for that type
# When a "create" event is replayed, the ObjectManager uses this table to determine which constructor to call
# When creating a new Logging type, register it here!
# The string should match the value passed to ObjectManager.create() in the Logging type constructor
type_dict = {
    "dict" : LogDict
}
