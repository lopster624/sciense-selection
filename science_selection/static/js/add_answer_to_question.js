
let container = document.querySelector("#form-container")
let addButton = document.querySelector("#add-answer")
let totalForms = document.querySelector("#id_form-TOTAL_FORMS")

addActionToBtn()

addButton.addEventListener('click', addAnswerForm)

let ansForm = document.querySelectorAll(".answer-form")
ansForm[ansForm.length-1].classList.add("visually-hidden");

function addActionToBtn(e){
    let btns = document.querySelectorAll('.delete-form')
    btns.forEach(function(btn) {
        btn.addEventListener('click', deleteAnswerForm)})
}

function addAnswerForm(e){
    let ansForm = document.querySelectorAll(".answer-form")
    let formNum = ansForm.length-1 //Get the number of the last form on the page with zero-based indexing
    ansForm[formNum].classList.remove('visually-hidden')
    e.preventDefault()

    let newForm = ansForm[formNum].cloneNode(true) //Clone the education form
    newForm.classList.add("visually-hidden")
    let formRegex = RegExp(`form-(\\d){1}-`,'g') //Regex to find all instances of the form number

    formNum++ //Increment the form number
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`) //Update the new form to have the correct form number
    container.insertBefore(newForm, addButton) //Insert the new form at the end of the list of forms

    totalForms.setAttribute('value', `${formNum+1}`) //Increment the number of total forms in the form management

    addActionToBtn()
}

function deleteAnswerForm(e){
    let initial_forms = document.querySelector("#id_form-INITIAL_FORMS")
    let answerForm = document.querySelectorAll(".answer-form")
    let formNum = answerForm.length
    totalForms.setAttribute('value', `${formNum-1}`)
    initial_forms.setAttribute('value', '0')

    let table_answer = event.target.closest('div.answer-form')
    let table_answer_hidden = table_answer.nextSibling.nextSibling

    table_answer.remove()
    table_answer_hidden.remove()
}


$(document).ready(function() {
    $('.alert-success').show(0).delay(2000).fadeOut();
});
