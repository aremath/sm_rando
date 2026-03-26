import { get_node_info, get_classchild, add_data_toggle_button } from "./dom_edit.js";

// Abstract
export class DataViewer {
    element;
    name;
    visible = true;

    // Set up any necessary data (uses the "create" event)
    constructor(node, e, event_manager) {
        this.manager = event_manager;
        this.name = e["name"];
    }

    // Default visibility is simply changing the display style on the element
    toggle_visible() {
        if (this.visible) {
            this.element.style.display = "none";
            this.visible = false;
        } else {
            this.element.style.display = "block";
            this.visible = true;
        }
    }

    // What happens when an event triggers?
    // Use the event
    replay(e) {

    }

    // Remove any necessary elements (that are not children of the data node being removed)
    remove() {

    }
}

export class DefaultDictViewer extends DataViewer {
    
    // node is the node-class element that was created for the creation event
    constructor(node, e, event_manager) {
        super(node, e, event_manager);
        // Add the data element
        var node_info = get_node_info(node);
        var node_name = get_classchild(node_info, "node_name");
        var element = document.createElement("div");
        element.className = "node_data";
        element.innerHTML = "{}";
        this.element = element;
        node_info.appendChild(element);
        // Add the toggle button
        var toggle_fn = _ => this.toggle_visible();
        add_data_toggle_button(node_name, toggle_fn);
    }
    
    // Simply read the dict from the object table and stringify
    // No need to store a second copy of the dict here
    replay(e) {
        this.element.innerHTML = JSON.stringify(this.manager.objects[this.name]);
    }
}

// Which viewer is appropriate depends on the type and interpretation of the create event
// To make a new viewer:
// 1. Write the appropriate viewer class
// 2. Create logic here to output its constructor when the appropriate create event is replayed
export function mk_viewer_constructor(e) {
    if (e["type"] === "dict") {
        return (a, b, c) => new DefaultDictViewer(a, b, c);
    }
}
