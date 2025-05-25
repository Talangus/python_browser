console = { log: function(x) { call_python("log", x); } }
document = { 
    querySelectorAll: function(s) {
        var handles = call_python("querySelectorAll", s);
        return handles.map(function(h) { return new Node(h) });
    },
    createElement: function(tagName){
        var handle = call_python("create_element", tagName)
        return new Node(handle)
    }    

}
Object.defineProperty(document, 'cookie', {
    set: function(s) {
        call_python("cookie_set", s.toString());
    },
    get: function() {
        return call_python("cookie_get");
    }
});

LISTENERS = {}
function Node(handle) { this.handle = handle; }
Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
}
Node.prototype.setAttribute = function(key, value) {
    return call_python("setAttribute", this.handle, key, value);
}
Node.prototype.addEventListener = function(type, listener) {
    if (!LISTENERS[this.handle]) LISTENERS[this.handle] = {};
    var dict = LISTENERS[this.handle];
    if (!dict[type]) dict[type] = [];
    var list = dict[type];
    list.push(listener);
}
Node.prototype.dispatchEvent = function(evt) {
    var type = evt.type
    var handle = this.handle;
    var list = (LISTENERS[handle] && LISTENERS[handle][type]) || [];
    for (var i = 0; i < list.length; i++) {
        list[i].call(this, evt);
    }
    return evt;
}
Node.prototype.appendChild = function(node) {
    call_python("append_child", this.handle, node.handle)
}
Node.prototype.insertBefore = function(newNode, referenceNode) {
    call_python("insert_before", this.handle, newNode.handle, referenceNode.handle)
}
Node.prototype.removeChild = function(childNode) {
    removed_handle = call_python("remove_child", this.handle, childNode.handle)
    if (removed_handle){
        return childNode
    }
}
Object.defineProperty(Node.prototype, 'outerHTML', {
    get: function() {
        return call_python("outerHTML_get", this.handle);
    }
});
Object.defineProperty(Node.prototype, 'innerHTML', {
    set: function(s) {
        call_python("innerHTML_set", this.handle, s.toString());
    },
    get: function() {
        return call_python("innerHTML_get", this.handle);
    }
});
Object.defineProperty(Node.prototype, 'children', {
    get: function() {
        var handles = call_python("children_get", this.handle);
        return handles.map(function(h) { return new Node(h) });
    }
});

function Event(type) {
    this.type = type
    this.do_default = true;
    this.propogate = true
}
Event.prototype.preventDefault = function() {
    this.do_default = false;
}

Event.prototype.stopPropagation = function() {
    this.propogate = false;
}

XHR_REQUESTS = {}

function XMLHttpRequest() {
    this.handle = Object.keys(XHR_REQUESTS).length;
    XHR_REQUESTS[this.handle] = this;
}

XMLHttpRequest.prototype.open = function(method, url, is_async) {
    this.is_async = is_async;
    this.method = method;
    this.url = url;
}

XMLHttpRequest.prototype.send = function(body) {
    this.responseText = call_python("XMLHttpRequest_send",
        this.method, this.url, body, this.is_async, this.handle);
}

function __runXHROnload(body, handle) {
    var obj = XHR_REQUESTS[handle];
    var evt = new Event('load');
    obj.responseText = body;
    if (obj.onload)
        obj.onload(evt);
}

SET_TIMEOUT_REQUESTS = {}

function setTimeout(callback, time_delta) {
    var handle = Object.keys(SET_TIMEOUT_REQUESTS).length;
    SET_TIMEOUT_REQUESTS[handle] = callback;
    call_python("setTimeout", handle, time_delta)
}

function __runSetTimeout(handle) {
    var callback = SET_TIMEOUT_REQUESTS[handle]
    callback();
}

