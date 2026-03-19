import { get_children, get_node_name, add_children, add_child_toggle_button } from "./dom_edit.js";

export function create_node(event) {
    // Find the parent node
    var parent_name;
    if (event["parent"] == null) {
        parent_name = "root";
    } else {
        parent_name = event["parent"];
    }
    console.log(`${parent_name}`);
    //TODO: what happens if there is no corresponding node?
    var parent_node = document.getElementById(`node_${parent_name}`);
    var parent_children;
    // Leaf nodes do not have a children
    if (parent_node.children.length < 2) {
        add_child_toggle_button(get_node_name(parent_node));
        parent_children = add_children(parent_node);
    } else {
        parent_children = get_children(parent_node);
    }
    console.log(parent_children);
    var this_node = document.createElement("div");
    var node_str = event["name"];
    this_node.className = "node"
    this_node.id = `node_${node_str}`;
    var node_name = document.createElement("div");
    node_name.className = "node_name";
    node_name.innerHTML = node_str;
    this_node.appendChild(node_name);
    parent_children.appendChild(this_node);
}

class EventManager {
    constructor() {
        // Stores the data for each object
        this.objects = {};
        // Stores the node for each object
        this.nodes = {}
    }

    replay(event) {
        if (event["action"] === "create") {
            constructor = type_dict[event["type"]];
            object = new constructor(event);
            this.objects[event["name"]] = object;

        } else if (event["action"] === "tick") {
            // Nothing happens for a tick action.
            // The ManagerManager will use ticks to determine where to stop replay
        } else {
            this.objects[event["name"]].replay(event);
        }
    }
}

class LogDict {
    dict;

    constructor(event) {
        this.dict = {}

    }

    replay(event) {
        switch (event["action"]) {
            case "deleteitem":
                var key = event["key"];
                delete this.dict[key];
            case "setitem":
                var key = event["key"];
                var value = event["value"];
                this.dict[key] = value;
        }
    }
}

var type_dict = {
    "dict": LogDict
}
