
let container = document.querySelector("#form-container")
let addButton = document.querySelector("#add-form")
let totalForms = document.querySelector("#id_form-TOTAL_FORMS")

addActionToBtn()
searchSpecialization()
searchEducation()
searchMilitaryCommissariat()

addButton.addEventListener('click', addEducationForm)
addButton.addEventListener('click', searchEducation)
addButton.addEventListener('click', searchSpecialization)
addButton.addEventListener('click', searchMilitaryCommissariat)

let edForm = document.querySelectorAll(".education-form")
edForm[edForm.length-1].style.display = 'none'

function addActionToBtn(e){
    let btns = document.querySelectorAll('.delete-form')
    btns.forEach(function(btn) {
        btn.addEventListener('click', deleteEducationForm)})
}

function addEducationForm(e){
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length-1 //Get the number of the last form on the page with zero-based indexing
    educationForm[formNum].style.display = ''
    e.preventDefault()

    let newForm = educationForm[formNum].cloneNode(true) //Clone the education form
    newForm.style.display = 'none'
    let formRegex = RegExp(`form-(\\d){1}-`,'g') //Regex to find all instances of the form number

    formNum++ //Increment the form number
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`) //Update the new form to have the correct form number
    container.insertBefore(newForm, addButton) //Insert the new form at the end of the list of forms

    totalForms.setAttribute('value', `${formNum+1}`) //Increment the number of total forms in the form management

    addActionToBtn()
}

function searchSpecialization(){
    $(".specialization").autocomplete({
        source: "/app/search/specialization/",
  });
}

function searchEducation(){
    $(".university").autocomplete({
        source: "/app/search/universities/",
  });
}

function searchMilitaryCommissariat(){
    $(".commissariat").autocomplete({
        source: "/app/search/commissariat/",
  });
}


function deleteEducationForm(e){
    let initial_forms = document.querySelector("#id_form-INITIAL_FORMS")
    let educationForm = document.querySelectorAll(".education-form")
    let formNum = educationForm.length
    totalForms.setAttribute('value', `${formNum-1}`)
    initial_forms.setAttribute('value', '0')

    let table_ed = event.target.closest('div.education-form')
    table_ed.remove()
}
