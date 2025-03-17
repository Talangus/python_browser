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

var xhr = new XMLHttpRequest();
var url = "https://run.mocky.io/v3/7cb77135-e065-4da3-a073-39b220eccb8b";

xhr.open("GET", url, false);
xhr.send();
console.log(xhr.responseText)