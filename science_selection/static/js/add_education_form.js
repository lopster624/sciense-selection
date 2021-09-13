
let container = document.querySelector("#form-container")
let addButton = document.querySelector("#add-form")
let totalForms = document.querySelector("#id_form-TOTAL_FORMS")

addButton.addEventListener('click', addForm)
addActionToBtn()

function addActionToBtn(e){
    let btns = document.querySelectorAll('.delete-form')
    btns.forEach(function(btn) {
        btn.addEventListener('click', deleteForm)})
}

function addForm(e){
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length-1 //Get the number of the last form on the page with zero-based indexing
    e.preventDefault()
    let countForm = educationForm.length-1

    let newForm = educationForm[countForm].cloneNode(true) //Clone the education form
    let formRegex = RegExp(`form-(\\d){1}-`,'g') //Regex to find all instances of the form number

    formNum++ //Increment the form number
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`) //Update the new form to have the correct form number
    container.insertBefore(newForm, addButton) //Insert the new form at the end of the list of forms

    totalForms.setAttribute('value', `${formNum+1}`) //Increment the number of total forms in the form management

    let btns = document.querySelectorAll('.delete-form')
    btns.forEach(function(btn) {
        btn.addEventListener('click', deleteForm)})

}

function deleteForm(e){
    let total_forms = document.querySelector("#id_form-TOTAL_FORMS")
    let initial_forms = document.querySelector("#id_form-INITIAL_FORMS")
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length
    totalForms.setAttribute('value', `${formNum-1}`)
    initial_forms.setAttribute('value', '0')
    console.log(total_forms)

    let table_ed = event.target.closest('div.education-form')
    table_ed.remove()
}
