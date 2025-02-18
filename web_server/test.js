var strong = document.querySelectorAll("strong")[0];
var allow_submit = true;


function lengthCheck() {
    console.log("running length check")
    var value = this.getAttribute("value");
    allow_submit = value.length <= 10;
    if (!allow_submit) {
        strong.innerHTML = "Comment too long!";
    }
}

var inputs = document.querySelectorAll("input");
for (var i = 0; i < inputs.length; i++) {
    inputs[i].addEventListener("keydown", lengthCheck);
}

var form = document.querySelectorAll("form")[0];
form.addEventListener("submit", function(e) {
    if (!allow_submit) e.preventDefault();
});

var div1 = document.createElement("div");
div1.setAttribute('id',"container");

var div2 = document.createElement("div");
div2.setAttribute('id',"child1");
div2.setAttribute("color", "blue"); 

var div3 = document.createElement("div");
div3.setAttribute('id', "child2");

var div1_1 = document.createElement("div");
div1_1.setAttribute('id', "grandchild1");

div2.appendChild(div1_1);
div1.appendChild(div2);
div1.appendChild(div3);

console.log("calling query selector")
body = document.querySelectorAll['body']
// document.children[1].appendChild(div1);

// Step 2: Use child1 directly as a reference
// console.log(child1);
