# SMRando Version 0.0.1
Tools for door and item randomization of Super Metroid.

You need a Super Metroid [JU] ROM.

You'll also need python 2.7 because I'm silly.

If you want to make spoiler graphs, you'll need [graphviz](https://graphviz.gitlab.io/) and the [graphviz python module](https://pypi.python.org/pypi/graphviz).

Note that this is a very rough draft - expect bugs and strange behavior.

## Usage:
Once you've downloaded the script, just point it at the rom you're interested in randomizing, like this:

    python main.py --clean ~/sm.smc --create ~/sm_rando.smc

The file paths are an example here, but the `--clean` file is the one that already exists (and hopefully is "clean", but the randomization process is probably compatible with a bunch of other hacks if you really want). The --create file is a file that the randomizer will create. The randomizer will choose the seed at random and print it out. Right now, making that seed again is buggy, so you might want to use

    python main.py --clean ~/sm.smc --create ~/sm_rando.smc --seed hello

Which will set the randomization seed to `hello`. There's another option called `--completable`, which will keep generating seeds until it finds one that's completable. To use this, just do

    python main.py --clean ~/sm.smc --create ~/sm_rando.smc --completable

You can use the `--seed` option with `--completable`, in which case it will try the suggested seed first. However, the `--completable` option will need to re-seed the RNG if it turns out that your seed wasn't completable, so there's no real reason to do this.

Another useful command-line option is `--starting_items`. This command edits what items Samus will start with when you land on Ceres station. The syntax for the command looks like this:

    python main.py --clean ~/sm.smc --create ~/sm_rando.smc --starting items B S10 E500 WB

This example gives you Bombs, 10 Super Missiles, 500 Energy, and Wave Beam on starting the game (why you'd want bombs without morph ball beats me). The algorithm will take your starting items into account when deciding if a seed is completable and deciding what rooms to place where. This means that the same seed with different starting items can produce different results! The names for all the items are in `encoding/rooms.txt`. Currently, I haven't figured out a way to edit your starting missiles, or your starting reserve tanks. The program will give you a warning about that, and not give you those items.

If you have graphviz, the `--graph` command-line option will also generate a room graph showing the ways the rooms are connected in this seed. Minibosses are colored green, bosses are colored red, the starting point is colored blue, Samus' ship is colored blue, the golden statues room is colored yellow, and the end of Tourian escape (and the beginning of the rest of escape) is colored purple.

The randomizer also provides a spoiler file with the same name as your rom but with `.spoiler.txt` appended. This spoiler file is a work in progress: right now it only contains the shortest path to escape Zebes and the list of door changes.

## Miscellaneous Information
The bottom of the output from `main.py` will tell you whether your seed is completable (and what the seed is, just to confirm). If you get a `Completable: False`, do not expect to be able to complete the game!

Emphasis on completable! These seeds will troll you, and it's entirely possible to get stuck and have to start over. I'm working on making this less common, but for now I recommend caution and a lot of save states. There will also likely be parts where both ammo and energy will be a major concern. I'm also working on tweaking the drop rates to make this less of a problem, but you might want to use the `--starting_items` option or SMILE to start with some extra e-tanks.

## Advice
One simple heuristic that can get you far in figuring out at least the beginnings of these seeds is that the logic will place items "near" where you need to use them. If you get supers early on, then the next item is likely to be behind a Super Missile door. If you find yourself in an area with a lot of missile expansions, it might be worth it to backtrack and try a different part of the map.

If you're wondering if a given door is on the logic, read `encoding/rooms.txt`. It's long, and the syntax is a little weird, but all of the logic is there as to whether you're "allowed" to cross a given edge with your items. For the most part, I require you to do some wall jumping and some basic suitless stuff, but "speedrun tech" like Green Gate Glitch, Shortcharge, or Mockball isn't required. You can do a little more suitless Maridia than usual, since sand no longer traps you if you don't have Gravity Suit.

Be careful when you're going through doors. Doors can easily drop you into Golden Torizo's Room, and if you're going to fast, those fall blocks aren't going to forgive you.

In general, Energy Tanks aren't technically required to cross most edges. Also, you only need one ammo of each type to cross those edges. If you're low on energy or ammo, dropping into an "off-logic" area of the game can often fill you up.

When traveling through sand pits, try to stay centered to avoid a bug where you can get stuck in the wall.

## Known Bugs
* The algorithm sometimes places multiple copies of items. It's not harmful to pick up multiple copies of an item, but it is weird.
* There are sometimes graphical glitches entering some Crateria Rooms, and when leaving Kraid. Pressing Start should clear these up.
* If you enter Crocomire, Shaktool, and a couple of other boss rooms through the wrong door, the screen glitches out. Don't panic! If you can navigate the room without being able to see, you should be able to shoot the door and make it back out.
* The logic can force you to fight Spore Spawn or other bosses (or even wait for Shaktool) during escape. I'm working on a way to make sure it gives you enough time for these events :)
* The Zip Tube room in Maridia does not appear in the randomizer because the player can't move after going through it!
* Sometimes you get stuck in the wall when moving from one sand pit to another.
* The room where you get morph ball is weird - The items might not appear until Zebes is awake, but might disappear if you visit it before Zebes is awake, and I'm not even sure what the Zebes awake trigger is.
* Saving does not work except in Tourian: reloading a save even after a death will glitch things out.
* Getting the Morph Ball item can give you Spring Ball instead. Use the `--starting_items MB` command-line option for now.

## You Can Help!
* If you notice a bug, or have some advice, open an issue on the github, and I'll try to check it periodically and make improvements. I'm somewhat busy, so I might not be able to consistently provide support, but I'll do what I can.
* If you're interested, one task that I probably won't get around to for a while is writing a "speedrun" version of rooms.txt. Feel free to include some High-Jump-less Lava Dive :). However, Make sure that your strats are contained within a single room. You can't use speedbooster to cross Coliseum if you can't charge a shinespark in the room before. I tried to make the encoding of rooms.txt fairly straightforward to understand, but if you have a question, I'm happy to help.
* If you have some romhacking advice, I'm new at this! There's some features I thought of, like making the back door to Kraid, Crocomore, etc. into a grey door to prevent the graphical errors problem, but that I don't really have the expertise for.
* If you notice a problem with `rooms.txt`, let me know! Without a proper spoiler it's hard to know when the logic is asking you to do something is possible, but I'd like to know about it if I generated a seed that I told you was completable, but actually wasn't.

## In Progress
This is just a list of things I'm working on: bugs to fix, features to implement, etc.
* Stop placing multiple copies of items
* Change the overall balance of items: More Supers and PBs, fewer Missiles
* Fix the boss screen scroll glitch
* Make the RNG seed easier to use: make the randomly generated seed possible to copy/paste
* Make the algorithm better at avoiding softlocks.
* Figure out how to skip Ceres. The "normal" way to skip it is bugged :(
* Figure out what to do about Zebes awake-/asleep-ness
* Make the spoiler file more descriptive and more useful

## Acknowledgements
Thanks to everyone who helped with this project. If you listened to me harp about completability or graphs, you know who you are and thank you for putting up with me, and giving me support and ideas.

Additionally, I'd like to thank the Super Metroid community. The motivation for this (and the idea behind it) came out of a love for Super Metroid, but that's also partially due to the great community that's passionate about this game.

A lot of the technical basis was in the [Item Randomizer](https://dessyreqt.github.io/smrandomizer/), for which `Dessyreqt` and many others are responsible. I also got some mileage out of the code for the logic-less [Door Randomizer](https://smdoor.codeplex.com/). I used [SMILE](http://metroidconstruction.com/resource.php?id=63) and [SMILE RF](http://forum.metroidconstruction.com/index.php?topic=3575.0) to do a lot of the testing, so `Scyzer` and `Jathys` deserve recognition, as well as `begrimed` who wrote the incredible [guide](http://www.metroidconstruction.com/SMMM/). The `#smhacking` channel of the Super Metroid discord was also helpful, and answered some hacking questions.
