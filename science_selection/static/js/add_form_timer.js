
const end_time = JSON.parse(document.getElementById('end_time').textContent);
var remaining_time = Date.parse(new Date(end_time)) - Date.parse(new Date());
var deadline = new Date(Date.parse(new Date(end_time)));

setTimeout(function sub(){
    let form = document.querySelector("#form-container");
    form.submit();
}, remaining_time);

function getTimeRemaining(endtime){
    var t = Date.parse(endtime) - Date.parse(new Date());
    var seconds = Math.floor((t / 1000) % 60);
    var minutes = Math.floor((t / 1000 / 60) % 60);
    var hours = Math.floor((t / 1000 / 60 / 60) % 60);
    return {
        total: t,
        hours: hours,
        minutes: minutes,
        seconds: seconds
    };
}

function initializeClock(id, endtime) {
    var clock = document.getElementById(id);
    var hoursSpan = clock.querySelector(".hours");
    var minutesSpan = clock.querySelector(".minutes");
    var secondsSpan = clock.querySelector(".seconds");

    function updateClock() {
        var t = getTimeRemaining(endtime);
        hoursSpan.innerHTML = ("0" + t.hours).slice(-2);
        minutesSpan.innerHTML = ("0" + t.minutes).slice(-2);
        secondsSpan.innerHTML = ("0" + t.seconds).slice(-2);
    }
    updateClock();
    setInterval(updateClock, 1000);
}

initializeClock("countdown", deadline);
