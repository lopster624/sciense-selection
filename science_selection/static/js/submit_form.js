function submit_form() {
    let form = document.getElementById('form');
    form.submit();
}
document.getElementById('switch_submit').addEventListener('change', submit_form);