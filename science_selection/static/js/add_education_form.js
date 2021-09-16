
let container = document.querySelector("#form-container")
let addButton = document.querySelector("#add-form")
let totalForms = document.querySelector("#id_form-TOTAL_FORMS")

addButton.addEventListener('click', addForm)
addButton.addEventListener('click', searchEducation)
addActionToBtn()
searchEducation()

let edForm = document.querySelectorAll(".education-form")
edForm[edForm.length-1].style.display = 'none'

function addActionToBtn(e){
    let btns = document.querySelectorAll('.delete-form')
    btns.forEach(function(btn) {
        btn.addEventListener('click', deleteForm)})
}

function addForm(e){
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length-1 //Get the number of the last form on the page with zero-based indexing
    e.preventDefault()

    let newForm = educationForm[formNum].cloneNode(true) //Clone the education form
    newForm.style.display = ''
    let formRegex = RegExp(`form-(\\d){1}-`,'g') //Regex to find all instances of the form number

    formNum++ //Increment the form number
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`) //Update the new form to have the correct form number
    container.insertBefore(newForm, addButton) //Insert the new form at the end of the list of forms

    totalForms.setAttribute('value', `${formNum+1}`) //Increment the number of total forms in the form management

    addActionToBtn()
}

function searchEducation(){
    $(".university").autocomplete({
        source: "/app/search/universities/",
  });
}

function deleteForm(e){
    let total_forms = document.querySelector("#id_form-TOTAL_FORMS")
    let initial_forms = document.querySelector("#id_form-INITIAL_FORMS")
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length
    totalForms.setAttribute('value', `${formNum-1}`)
    initial_forms.setAttribute('value', '0')

    let table_ed = event.target.closest('div.education-form')
    table_ed.remove()
}
