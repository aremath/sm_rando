
// Node structure
//<div class="node">
//  <div class="node_info">
//    <div class="node_name">NODE_NAME</div>
//    optional: <div class="node_data">NODE_DATA</div>
//  </div>
//  optional: <div class="children>
//      <div class="node">...</div>
//      <div class="node">...</div>
//      ...
//  </div>

export function toggle_data_default(el) {
    // "node_info" div containing this "node_name"
    var node_info = el.parentNode.parentNode.parentNode;
    // Can be a solo "node_name" with no "node_data"
    if (node_info.children.length < 2) {
        return;
    }
    var data = node_info.children[1];
    if (data.style.display === "none") {
        data.style.display = "block";
    } else {
        data.style.display = "none";
    }
    
}

// Change the icon
export function toggle_eye(el) {
    if (el.children[0].className === "eye_invisible") {
        el.children[0].src="eye-20-solid.svg";
        el.children[0].className = "eye_visible";
    } else {
        el.children[0].src="eye-slash-20-solid.svg";
        el.children[0].className = "eye_invisible";
    }
}

export function toggle_children(el) {
    // The "node" div containing this node_info
    var node = el.parentNode.parentNode;
    // Leaf nodes will not have a children_container
    if (node.children.length < 3) {
        return;
    }
    var children_container = node.children[2];
    //console.log(children[1]);
    //console.log(children_container.style.display);
    // Initially, it's null, so the else branch triggers
    // After that, it will be one or the other and toggle visibility appropriately
    //TODO: display=hidden vs. display=none
    if (children_container.style.display === "none") {
        children_container.style.display = "block";
    } else {
        children_container.style.display = "none";
    }
}

// node is a "node_info" class element
export function add_child_toggle_button(node) {
    var d = document.createElement("div");
    var b = document.createElement("button");
    var img = document.createElement("img");
    img.src = "eye-20-solid.svg";
    img.width = "10";
    //el.appendChild(b);
    node.insertAdjacentElement("afterend", d);
    d.appendChild(b);
    // Each button toggles its own children
    b.addEventListener("click", event => toggle_children(b));
    b.addEventListener("click", event => toggle_eye(b));
    b.appendChild(img);
}

//TODO: make the expected element passed consistent between add_child and add_data
// node is a "node_name" class element
export function add_data_toggle_button(node, toggle_data) {
    //console.log(node);
    var d = document.createElement("div");
    var b = document.createElement("button");
    var img = document.createElement("img");
    //TODO: different image for the data toggle
    img.src = "eye-20-solid.svg";
    img.className="eye_visible"
    img.width = "10";
    node.appendChild(d);
    d.appendChild(b);
    //TODO: add a separate listener to update the button icon
    // since this will always be the same regardless of what operation actually hides the data
    b.addEventListener("click", event => toggle_data(b));
    b.addEventListener("click", event => toggle_eye(b));
    b.appendChild(img);
}

export function get_classchild(node, classname) {
    for (let child of node.children) {
        //console.log(child);
        //console.log(child.className);
        // Why would it be called className when it's called class in HTML???
        if (child.className === classname) {
            return child;
        }
    }
}

// It's stupid, but I need it
export function get_children(node) {
    for (let child of node.children) {
        //console.log(child);
        //console.log(child.className);
        // Why would it be called className when it's called class in HTML???
        if (child.className === "children") {
            return child;
        }
    }
}

export function get_node_info(node) {
    for (let child of node.children) {
        //console.log(child);
        //console.log(child.className);
        // Why would it be called className when it's called class in HTML???
        if (child.className === "node_info") {
            return child;
        }
    }

}

export function add_children(node) {
    var empty_children = document.createElement("div");
    empty_children.className = "children";
    node.appendChild(empty_children);
    return empty_children;
}
