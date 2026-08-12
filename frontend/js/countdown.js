// ============================================
// Festival Countdown Timer
// Keep these two dates in sync with
// backend/festival_schedule.py
// ============================================

(function () {

    var FESTIVAL_START = new Date("2026-09-14T00:00:00+05:30");
    var FESTIVAL_END = new Date("2026-09-19T23:59:59+05:30");

    var gridEl = document.getElementById("countdown-grid");
    var labelEl = document.getElementById("countdown-label");
    var messageEl = document.getElementById("countdown-message");

    var daysEl = document.getElementById("cd-days");
    var hoursEl = document.getElementById("cd-hours");
    var minsEl = document.getElementById("cd-mins");
    var secsEl = document.getElementById("cd-secs");

    function pad(n) {
        return n < 10 ? "0" + n : String(n);
    }

    function renderCountdown(diffMs) {

        var totalSeconds = Math.floor(diffMs / 1000);

        var days = Math.floor(totalSeconds / 86400);
        var hours = Math.floor((totalSeconds % 86400) / 3600);
        var mins = Math.floor((totalSeconds % 3600) / 60);
        var secs = totalSeconds % 60;

        daysEl.textContent = pad(days);
        hoursEl.textContent = pad(hours);
        minsEl.textContent = pad(mins);
        secsEl.textContent = pad(secs);
    }

    function tick() {

        var now = new Date();

        // ----------------------------
        // Before the festival
        // ----------------------------
        if (now < FESTIVAL_START) {

            labelEl.textContent = "🎉 Festival Begins In";
            gridEl.style.display = "flex";
            messageEl.textContent = "";

            renderCountdown(FESTIVAL_START - now);
            return;
        }

        // ----------------------------
        // During the festival
        // ----------------------------
        if (now >= FESTIVAL_START && now <= FESTIVAL_END) {

            var msPerDay = 86400000;
            var dayNumber =
                Math.floor((now - FESTIVAL_START) / msPerDay) + 1;

            var totalDays =
                Math.round(
                    (FESTIVAL_END - FESTIVAL_START) / msPerDay
                ) + 1;

            labelEl.textContent = "🙏 Ganapathi Bappa Morya!";
            gridEl.style.display = "none";
            messageEl.textContent =
                "Festival Day " + dayNumber + " of " + totalDays +
                " is here — join in today's celebrations!";

            return;
        }

        // ----------------------------
        // After the festival
        // ----------------------------
        labelEl.textContent = "🙏 Ganapathi Bappa Morya!";
        gridEl.style.display = "none";
        messageEl.textContent =
            "This year's festival has concluded. " +
            "Thank you for celebrating with us — see you next year!";
    }

    tick();
    setInterval(tick, 1000);

})();