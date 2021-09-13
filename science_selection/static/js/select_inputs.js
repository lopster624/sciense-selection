for (const element of document.getElementsByClassName('main_choose')) {
    element.addEventListener('click', select);
}
function select() {
        for (const element of this.parentNode.parentNode.querySelectorAll('input[name=chosen_competences]')){
            element.checked = this.checked;
        }
    }

