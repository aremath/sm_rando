# Super Metroid World Randomizer Version 0.0.4
Door and item randomization of Super Metroid. If you've played route rando before, it is kind of like that.

You need a Super Metroid [JU] ROM and Python 3.

If you want to make spoiler graphs, you'll need [graphviz](https://graphviz.gitlab.io/) and the [graphviz python module](https://pypi.python.org/pypi/graphviz). You can install these using `pip`.

Note that this is still a rough draft - there may be bugs and strange behavior.

## Usage:
Once you've downloaded the script, just point it at the rom you're interested in randomizing, like this:

    python3 door_rando.py --clean ~/sm.smc --create ~/sm_rando.smc

The file paths are an example here, but the `--clean` file is the one that already exists (and is ostensibly "clean", though the randomization process is probably compatible with a bunch of other hacks). The --create file is a file that the randomizer will create. The randomizer will choose the seed at random and print it out. Right now, making that seed again is buggy, so you might want to use

    python door_rando.py --clean ~/sm.smc --create ~/sm_rando.smc --seed hello

Which will set the randomization seed to `hello`. There's another option called `--completable`, which will keep generating seeds until it finds one that's completable. To use this, just do

    python door_rando.py --clean ~/sm.smc --create ~/sm_rando.smc --completable

You can use the `--seed` option with `--completable`, in which case it will try the suggested seed first. However, the `--completable` option will need to re-seed the RNG if it turns out that your seed wasn't completable, so there's no real reason to do this.

Another useful command-line option is `--starting_items`. This command edits what items Samus will start with when you land on Zebes. The syntax for the command looks like this:

    python door_rando.py --clean ~/sm.smc --create ~/sm_rando.smc --starting_items "B S10 E500 WB"

This example gives you Bombs, 10 Super Missiles, 500 Energy, and Wave Beam on starting the game (why you'd want bombs without morph ball beats me). The quotes around the list of items you want to start with are important.
The algorithm will take your starting items into account when deciding if a seed is completable and deciding what rooms to place where.
This means that the same seed with different starting items can produce different results! The names for all the items are in `encoding/rooms.txt`.
Currently, I haven't figured out a way to edit your starting missiles, or your starting reserve tanks. The program will give you a warning about that, and not give you those items.

If you have graphviz, the `--graph` command-line option will also generate a room graph showing the ways the rooms are connected in this seed. Minibosses are colored green, bosses are colored red, Samus' ship is colored blue, the golden statues room is colored yellow, and the end of Tourian escape (and the beginning of the rest of escape) is colored purple.

Finally, the `--debug` option will let you see the generated door transitions as they are created. If you don't include `--debug` you will see a neat progress bar that shows how many of the rooms have been placed.

The randomizer also provides a spoiler file with the same name as your rom but with `.spoiler.txt` appended. This spoiler file is a work in progress: right now it only contains the shortest path to escape Zebes and the list of door changes.

## Miscellaneous Information
The bottom of the output from `door_rando.py` will tell you whether your seed is completable (and what the seed is, just to confirm). If you get a `Completable: False`, do not expect to be able to complete the game!

Emphasis on completable! These seeds will troll you, and it's very east to softlock. I'm working on making this less common, but for now I recommend caution and a lot of save states. Another way to approach this problem is to load the ROM into a [multitroid](www.multitroid.com) instance so that you can play with friends or at least reset without losing progress if you are playing by yourself. The short answer as to why there are so many softlocks is that I can check completability with a relatively simple search algorithm that works very quickly. Checking whether a node can be a softlock is much more complicated since I would have to consider all possible paths that reach that node with different item sets. This is computationally infeasible and there isn't an easy way to fix it even if the algorithm finds a softlock location.
There will also likely be parts where both ammo and energy will be a major concern. I'm also working on tweaking the drop rates to make this less of a problem, but you might want to use the `--starting_items` option or SMILE to start with some extra e-tanks.

## Advice
One simple heuristic that can get you far in figuring out at least the beginnings of these seeds is that the logic will place items "near" where you need to use them. If you get supers early on, then the next item is likely to be behind a Super Missile door. If you find yourself in an area with a lot of missile expansions, it might be worth it to backtrack and try a different part of the map.

If you're wondering if a given door is on the logic, read `encoding/rooms.txt`. It's long, and the syntax is a little weird, but all of the logic is there as to whether you're "allowed" to cross a given edge with your items. For the most part, I require you to do some wall jumping and some basic suitless stuff, but "speedrun tech" like Green Gate Glitch, Shortcharge, or Mockball isn't required. You can do a little more suitless Maridia than usual, since sand no longer traps you if you don't have Gravity Suit.

Be careful when you're going through doors. Doors can easily drop you into Golden Torizo's Room, and if you're going too fast, those fall blocks aren't going to forgive you.

In general, Energy Tanks aren't technically required to cross most edges. Also, you only need one ammo of each type to cross those edges. If you're low on energy or ammo, dropping into an "off-logic" area of the game can often fill you up.

When traveling through sand pits, stay centered to avoid a bug where you can get stuck in the wall.

## Advanced Usage
If you are interested in fine-tuning the settings, you can edit things like what items will be placed and how much time you are allotted during escape using JSON files. If you read `door_rando/settings.py`, you can see what the syntax for the various settings dictionaries is. The `--settings` option allows you to specify where you are storing your custom settings files:

    python door_rando.py --settings ../settings --clean ../sm_guinea_pig.smc --create ...

It will look in `../settings/` for files named `items.set` and `escape.set` which edit the item placement and escape timings respectively. It will only take settings from files that are present. It expects your custom settings in JSON format. You can basically copy the syntax from the `settings.py` file like this:

    {
    "starting": 1,
    "extra":    {"M": 22,
                "S":  12,
                "PB": 10,
                "E":  14}
    }

This will reduce the number of times it places each normal item to once instead of the default of twice. Currently you can't specify that you want Hi-Jump Boots twice but X-Ray Scope only once. This `items.set` has a slight problem though -- it is only 79 items. If you try to run with this settings file, it will complain that you have not provided enough items. Make sure that your settings will place exactly 100 items.

You can also edit the escape times in a similar fashion using a file named `escape.set` which goes into your settings folder along with `items.set`. Using this you can edit the time needed to escape Tourian, the time needed for each node (there are two nodes per room), and the time you need if it requires you to fight bosses during the escape. One thing to note is that it only replaces the keys it finds. If my `escape.set` looks like:

    {
    "tourian": 45
    }

Then this will lower the default Tourian escape time to 45s while keeping all of the other escape timings the same.

As a final note, the current settings do not interact with the RNG used to decide the map. This means that you can use different settings with the same seed to create the same placement of rooms and progression items with a different amount and placement of ancillary items, as well as a different amount of time for escape.

## Known Bugs
* There are sometimes graphical glitches entering some Crateria rooms, when loading a save to Landing Site, and when leaving Kraid. Pressing Start should clear up the Kraid ones. The others disappear when they go offscreen.
* If you enter Crocomire, Shaktool, and a couple of other boss rooms through the wrong door, the screen glitches out. Don't panic! If you can navigate the room without being able to see, you should be able to shoot the door and make it back out.
* The Zip Tube room in Maridia does not appear in the randomizer because the player can't move after going through it! I need to do some door ASM edits to get it to work, and there are some higher priorities.
* Sometimes you get stuck in the wall when moving from one sand pit to another.
* The room where you get morph ball is weird - The items might not appear until Zebes is awake, but might disappear if you visit it before Zebes is awake. As far as the logic is concerned, the items in the morph ball room are never reachable.

## You Can Help!
* If you notice a bug, or have some advice, open an issue on the github, and I'll try to check it periodically and make improvements. I'm somewhat busy, so I might not be able to consistently provide support, but I'll do what I can.
* If you're interested, one task that I probably won't get around to for a while is writing a "speedrun" version of rooms.txt. Feel free to include some High-Jump-less Lava Dive :). However, Make sure that your strats are contained within a single room. You can't use speedbooster to cross Coliseum if you can't charge a shinespark in the room before. I tried to make the encoding of rooms.txt fairly straightforward to understand, but if you have a question, I'm happy to help.
* If you have some romhacking advice, I'm new at this! Let me know if there are some cool features you've thought of!
* If you notice a problem with `rooms.txt`, let me know! Without a proper spoiler it's hard to know when the logic is asking you to do something is possible, but I'd like to know about it if I generated a seed that I told you was completable, but actually wasn't.

## In Progress
This is just a list of things I'm working on: bugs to fix, features to implement, etc. If you have an insight into how to make one of them happen, let me know!
* Fix the boss screen scroll glitch / make the other side of the boss room a grey door.
* Make the algorithm better at avoiding softlocks.
* Figure out what to do about Zebes awake-/asleep-ness
* Make the spoiler file more descriptive and more useful
* Keep your ammo after the Mother Brain fight.

## Acknowledgements
Thanks to everyone who helped with this project. If you listened to me harp about completability or graphs, you know who you are and thank you for putting up with me, and giving me support and ideas.

Additionally, I'd like to thank the Super Metroid community. The motivation for this (and the idea behind it) came out of a love for Super Metroid, but that's also partially due to the great community that's passionate about this game.

A lot of the technical basis was in the [Item Randomizer](https://dessyreqt.github.io/smrandomizer/), for which `Dessyreqt` and many others are responsible. I also got some mileage out of the code for the logic-less [Door Randomizer](https://smdoor.codeplex.com/). I used [SMILE](http://metroidconstruction.com/resource.php?id=63) and [SMILE RF](http://forum.metroidconstruction.com/index.php?topic=3575.0) to do a lot of the testing, so `Scyzer` and `Jathys` deserve recognition, as well as `begrimed` who wrote the incredible [guide](http://www.metroidconstruction.com/SMMM/). The `#smhacking` channel of the Super Metroid discord was also helpful, and answered some hacking questions.
