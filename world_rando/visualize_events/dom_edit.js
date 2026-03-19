
export function toggle_children(el) {
    // The "node" div containing this node_name
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
        // Change the icon
        el.children[0].src="eye-20-solid.svg";
    } else {
        children_container.style.display = "none";
        el.children[0].src="eye-slash-20-solid.svg";
    }
}

export function add_child_toggle_button(node) {
    var d = document.createElement("div");
    var b = document.createElement("button");
    var img = document.createElement("img");
    img.src = "eye-20-solid.svg"
    //el.appendChild(b);
    node.insertAdjacentElement("afterend", d);
    d.appendChild(b);
    // Each button toggles its own children
    b.addEventListener("click", event => toggle_children(b));
    b.appendChild(img);
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

export function get_node_name(node) {
    for (let child of node.children) {
        //console.log(child);
        //console.log(child.className);
        // Why would it be called className when it's called class in HTML???
        if (child.className === "node_name") {
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
