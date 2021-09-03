function submit_form() {
    let form = document.getElementById('form');
    form.submit();
}
document.getElementById('select_direction').addEventListener('change', submit_form);