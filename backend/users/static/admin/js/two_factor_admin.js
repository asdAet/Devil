(function () {
  "use strict";

  function getCookie(name) {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === name + "=") {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  function getUserId() {
    var match = window.location.pathname.match(/\/user\/(\d+)\/change\//);
    return match ? match[1] : null;
  }

  function twofaToggle(btn) {
    var action = btn.getAttribute("data-action");
    var userId = getUserId();
    if (!userId) return;

    var url = "/admin/users/user/" + userId + "/twofa-toggle/";
    var formData = new FormData();
    formData.append("action", action);
    formData.append("csrfmiddlewaretoken", getCookie("csrftoken"));

    fetch(url, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        if (data.error) {
          alert(data.error);
          return;
        }

        var statusEl = document.getElementById("twofa_status");
        var qrEl = document.getElementById("twofa_qr");
        var actionsEl = document.getElementById("twofa_actions");

        if (statusEl) statusEl.innerHTML = data.status;
        if (qrEl) qrEl.innerHTML = data.qr;
        if (actionsEl) actionsEl.innerHTML = data.actions;

        bindButtons();
      })
      .catch(function () {
        alert("Ошибка сети");
      });
  }

  function bindButtons() {
    var buttons = document.querySelectorAll(".twofa-toggle");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].removeEventListener("click", onClick);
      buttons[i].addEventListener("click", onClick);
    }
  }

  function onClick(e) {
    e.preventDefault();
    twofaToggle(this);
  }

  document.addEventListener("DOMContentLoaded", bindButtons);
})();
