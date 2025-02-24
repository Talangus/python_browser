function changeColor_out(event) {
    console.log("in listener")
    this.setAttribute('class', "outer blue")
   
}

function changeColor_mid(event) {
    console.log("in listener")
    this.setAttribute('class', "middle blue")
   
}

function changeColor_in(event) {
    console.log("in listener")
    this.setAttribute('class', "inner blue")
    event.stopPropagation()
   
}

outer.addEventListener('click', changeColor_out);
middle.addEventListener('click', changeColor_mid);
inner.addEventListener('click', changeColor_in)