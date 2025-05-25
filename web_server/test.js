var strong = document.querySelectorAll("strong")[0];
var allow_submit = true;


function lengthCheck() {
    var value = this.getAttribute("value");
    allow_submit = value.length <= 100;
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

function print(){
    console.log("test")
}
setTimeout(print, 5000)

const xhr = new XMLHttpRequest();
xhr.open("GET", "https://run.mocky.io/v3/cb699e5b-844f-4806-8060-69646b71b8d7", true);
xhr.onload = function () {
    console.log(xhr.responseText)
}
xhr.send();