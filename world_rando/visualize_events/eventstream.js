import { EventManager, create_node } from "./events.js";
import { mk_viewer_constructor } from "./data_viewers.js";

// EventStream modes
// Step by Event
// Step by Tick
// Play by Event
// Play by Tick

// Default speed for event update
const DEFAULT_EVENT = 1000;
// Default speed for tick update
const DEFAULT_TICK = 1000;

const tick_speeds = {
};

export function update_progressname(stream) {
    return; //TODO
}

export function event_progressbar(stream) {
    var progress = (stream.index / stream.n_events) * 100;
    var progress_percent = Math.trunc(progress) + "%";
    var bar = document.getElementById("progress_bar");
    bar.style.width = progress_percent;
    if (stream.index === stream.n_events) {
        //console.log("Done!");
        bar.style.background = "#04AA6D";
    } else {
        // Change it back, in case we finished then reset
        bar.style.background = "rgb(96 139 168)";
    }
}

export function tick_progressbar(stream) {
    //TODO: this might have an off-by-one error
    var progress = (stream.tick_index / stream.n_ticks) * 100;
    var progress_percent = Math.trunc(progress) + "%";
    var bar = document.getElementById("progress_bar");
    bar.style.width = progress_percent;
}

export class EventStream {
    
    constructor(event_list) {
        // Our index into the event list
        this.index = 0;
        this.event_list = event_list;
        this.tick_index = 0;
        this.n_events = event_list.length;
        this.n_ticks = 0;
        // Count the ticks. This is important for the progress bar.
        for (let e of event_list) {
            if (e["action"] === "tick") {
                this.n_ticks += 1;
            }
        }
        this.paused = true;
        this.manager = new EventManager();
        this.event_play = null;
        this.tick_play = null;
        // Register a callback here. This function will be called after an event plays
        this.event_callback = null;
        this.tick_callback = null;
        // Key - name
        // Value - "node"-class element containing the named data structure's stuff
        this.element_table = {};
        // Key - name
        // Value - data_viewers/DataViewer object
        this.viewer_table = {}
    }

    // Play one event
    //TODO: skip and play another event if it's a Tick?
    step_once() {
        // Nothing happens if we are past the end of the event list
        if (this.index >= this.n_events) {
            return false;
        }
        var e = this.event_list[this.index];
        if (e["action"] === "create") {
            var node = create_node(e);
            this.element_table[e["name"]] = node;
            // Create the DataViewer for this node (if an appropriate viewer is available)
            var viewer_constructor = mk_viewer_constructor(e);
            if (viewer_constructor) {
                var data_viewer = viewer_constructor(node, e, this.manager);
                this.viewer_table[e["name"]] = data_viewer;
            }
        }
        if (e["action"] === "tick") {
            //TODO: run the tick callback if we see a tick event?
            this.tick_index += 1;
        }
        // This is not good for the tick progressbar, but is good for using the tick names
        this.manager.replay(e);
        // Update the visualizer
        var viewer = this.viewer_table[e["name"]];
        if (viewer) {
            viewer.replay(e);
        }
        this.index += 1;
        if (this.event_callback) {
            this.event_callback(this);
        }
        return true;
    }

    // Play one tick
    tick_once() {
        if (this.index >= this.n_events) {
            return false;
        }
        // Stop at the next tick
        while (this.event_list[this.index]["action"] != "tick") {
            this.step_once();
            // Reached the end of the event list without seeing a tick
            if (this.index >= this.n_events) {
                return false;
            }
        }
        // Skip the tick event
        this.index += 1;
        this.tick_index += 1;
        if (this.tick_callback) {
            //TODO: have the callback set the tick message
            this.tick_callback(this)
        }
        return true;
    }

    // Play events continuously until told to stop (this.pause_playback())
    //TODO: keep track of time elapsed during the update; only wait for the /remaining/ time
    play_events() {
        // If play_events() is called while a play_ticks() is waiting, it should cancel the play_ticks()
        //console.log(this);
        this.pause_playback();
        this.paused = false;
        // If step_once() returns true, there are still events to process
        //TODO: this actually tries one more time since you only get false when there are no events left
        if (this.step_once()) {
            // Use .bind to keep "this" around
            // Recursively play the next event
            // This is better than SetInterval because SetInterval calls can overlap
            this.event_play = setTimeout(this.play_events.bind(this), DEFAULT_EVENT);
        }
    }

    // Play ticks continuously until told to stop
    play_ticks() {
        // Cancel other playback
        this.pause_playback();
        this.paused = false;
        // If tick_once returns true, there are still events to process
        if (this.tick_once()) {
            this.tick_play = setTimeout(this.play_ticks.bind(this), DEFAULT_TICK);
        }
    }

    pause_playback() {
        this.paused = true;
        if (this.event_play) {
            clearInterval(this.event_play);
            this.event_play = null;
        }
        if (this.tick_play) {
            clearInterval(this.tick_play);
            this.tick_play = null;

        }
    }

    // Reset the event-related state
    reset() {
        this.index = 0;
        this.tick_index = 0;
        // Stop any pending playback
        this.pause_playback()
        this.manager = new EventManager();
        // Remove all the DOM elements that we are responsible for
        for (var k in this.element_table) {
            var el = this.element_table[k];
            el.remove();
        }
        this.element_table = {};
        // Update external stuff
        if (this.event_callback) {
            this.event_callback(this);
        }
        if (this.tick_callback) {
            this.tick_callback(this);
        }
    }
}
