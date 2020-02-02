# Super Metroid World Randomizer Version 0.1.1
Door and item randomization of Super Metroid.

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
There isn't a simple way to edit your starting reserve tanks. The program will give you a warning if you try to add a starting item that isn't implemented, and not give you that item.

If you have graphviz, the `--graph` command-line option will also generate a room graph showing the ways the rooms are connected in this seed. Minibosses are colored green, bosses are colored red, Samus' ship is colored blue, the golden statues room is colored yellow, and the end of Tourian escape (and the beginning of the rest of escape) is colored purple.

The `--g8` command-line option changes the Crateria map station into another copy of the Golden 4 room in order to make Tourian slightly easier to find. Note, however, that leaving Tourian by the elevator leaves you in the actual Golden 4 room. This change does not currently impact the logic.

The `--hard_mode` command-line option will switch to the harder logic preset, potentially requiring a lot of difficult tricks to complete a seed.

The `--debug` option will let you see the generated door transitions as they are created. If you don't include `--debug` you will see a neat progress bar that shows how many of the rooms have been placed.

The `--noescape` option disables soft-resetting during the escape sequence. This comes with some danger as if you softlock during escape you will have to reset to your save before Mother Brain. That said, the escape sequence is a lot of fun in door randomizer, so this option can make for an exciting final sequence. To console you, Start+Select will refill your ammo during escape.

The randomizer also provides a spoiler file with the same name as your rom but with `.spoiler.txt` appended.

## Miscellaneous Information
The bottom of the output from `door_rando.py` will tell you whether your seed is completable (and what the seed is, just to confirm). If you get a `Completable: False`, do not expect to be able to complete the game!

While each completable seed should have a path that allows you to complete the game, it is possible to become stuck by using a different path. To get unstuck, you can press Start+Select together to soft-reset to Samus' spaceship. This feature can be disabled during the escape sequence by using the `--noescape` option.

The short answer as to why there are so many softlocks is that I can check completability with a relatively simple search algorithm that works very quickly. Checking whether a node can be a softlock is much more complicated since I would have to consider all possible paths that reach that node with different item sets. This is computationally infeasible and even if the algorithm could detect a softlock location, it might not be easy to rearrange the rooms in order to fix it.

There will also likely be parts where both ammo and energy will be a major concern. You may want to use the `--starting_items` option or SMILE to start with some extra e-tanks.

Finally, you can load the ROM into a [multitroid](www.multitroid.com) instance and play with friends! This makes the game both faster to complete and more fun!

## Advice
One simple heuristic that can get you far in figuring out these seeds is that the logic will often place items "near" where you need to use them. If you get supers early on, then the next item is likely to be behind a Super Missile door. If you find yourself in an area with a lot of missile expansions, it might be worth it to backtrack and try a different part of the map.

If you're wondering if a given door is on the logic, read `encoding/rooms.txt`. It's long, and the syntax is a little weird, but all of the logic is there as to whether you're "allowed" to cross a given edge with your items. For the most part, I require you to do some wall jumping and some basic suitless stuff, but "speedrun tech" like Green Gate Glitch, Shortcharge, or Mockball isn't required. You can do a little more suitless Maridia than usual, since sand no longer traps you if you don't have Gravity Suit.

Be careful when you're going through doors. Doors can easily drop you into Golden Torizo's Room, and if you're going too fast, those fall blocks aren't going to forgive you.

In general, Energy Tanks aren't technically required to cross most edges. Also, you only need one ammo of each type to cross those edges. If you're low on energy or ammo, dropping into an "off-logic" area of the game can often fill you up.

When traveling through sand pits, stay centered to avoid getting stuck in the wall. (I will try to fix this at some point...)

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

This will reduce the number of times it places each normal item to once instead of the default of twice. If (for example) you want two Hi-Jumps, but not two of every other major item, you can keep `"starting"` at 1, and add a key `"HJ": 1` to the `"extra"` dictionary. As you might notice, this `items.set` has a slight problem -- it is only 79 items. If you try to run with this settings file, it will complain that you have not provided enough items. Make sure that your settings will place exactly 100 items.

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

## You Can Help!
* If you notice a bug, or have some advice, open an issue on the github, and I'll try to check it periodically and make improvements. I'm somewhat busy, so I might not be able to consistently provide support, but I'll do what I can.
* Let me know if there are some cool features you've thought up!
* If you notice a problem with `rooms.txt`, let me know! I would like to know when it generates a seed that was marked as completable, but actually wasn't. The best thing to do would be to create an issue on the github page and include the spoiler file as well as where you could no longer make progress.

## In Progress
This is just a list of things I'm working on: bugs to fix, features to implement, etc. If you have an insight into how to make one of them happen, let me know!
* Fix the boss screen scroll glitch / make the other side of the boss room a grey door.
* Make the algorithm better at avoiding softlocks.
* Fix sand pits.

## Acknowledgements
Thanks to everyone who helped with this project. If you listened to me harp about completability or graphs, you know who you are and thank you for putting up with me, and giving me support and ideas.

Additionally, I'd like to thank the Super Metroid community. The motivation for this (and the idea behind it) came out of a love for Super Metroid, but that's also partially due to the great community that's passionate about this game.

A lot of the technical basis was in the [Item Randomizer](https://dessyreqt.github.io/smrandomizer/), for which `Dessyreqt` and many others are responsible. I also got some mileage out of the code for the logic-less [Door Randomizer](https://smdoor.codeplex.com/). I used [SMILE](http://metroidconstruction.com/resource.php?id=63) and [SMILE RF](http://forum.metroidconstruction.com/index.php?topic=3575.0) to do a lot of the testing, so `Scyzer` and `Jathys` deserve recognition, as well as `begrimed` who wrote the incredible [guide](http://www.metroidconstruction.com/SMMM/). The `#smhacking` channel of the Super Metroid discord was also helpful, and answered some hacking questions.
