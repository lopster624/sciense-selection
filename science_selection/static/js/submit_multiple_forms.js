for (const element of document.getElementsByClassName('maybe_submited')) {
    element.addEventListener('change', submit_form);
}

function submit_form(e) {
    let form = e.target.closest("form");
    form.submit();
}