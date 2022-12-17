# parsing and editing a rom

Create a `RomManager` object, then call `parse`

`parse()` gives you an `ObjNames` object which works like a dictionary

the details are in `rom_tools/rom_data_structures.py`

then you can access data members using `.`

so if you have a room header called `rh`, then `rh.state_chooser.default` is the room state object for that room header

if you have an `ObjNames`, you can compile it using `RomManager.compile()`

there's an example of how to do this in `notebooks/infinite_gauntlet.ipynb`

---

### Super Metroid Subversion rom hack

as far as I know, it doesn't work with the Super Metroid Subversion rom hack, but it's probably close to working with Subversion?

my guess is that the subversion save station tables are at a different address

if you know the address of the subversion save tables, you might be able to edit parse() so that it would work with subversion
