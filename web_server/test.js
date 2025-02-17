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
console.log(document.querySelectorAll('form')[0].children[0].children[0].getAttribute('name'))
var p = document.createElement("p")
p.innerHTML = "test insert js"
form.appendChild(p)

var div = document.createElement('div')
div.innerHTML = 'test insert before'
p.insertBefore(div)