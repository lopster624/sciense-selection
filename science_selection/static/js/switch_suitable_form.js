function switch_unsuitable() {
    let form = document.getElementById('form_unsuitable');
    form.submit();
}
document.getElementById('switch_unsuitable_submit').addEventListener('change', switch_unsuitable);
