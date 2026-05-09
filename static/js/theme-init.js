/* Theme initialization — must run before page render to prevent flash */
(function() {
    var t = localStorage.getItem('jobclass:theme');
    if (t) document.documentElement.setAttribute('data-theme', t);
})();
