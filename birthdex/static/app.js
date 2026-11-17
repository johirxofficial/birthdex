/* BirthDex — tiny front-end, no dependencies. */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const el = {
    alert: $("alert"),
    searchForm: $("search-form"),
    searchBtn: $("search-btn"),
    resetBtn: $("reset-btn"),
    number: $("number"),
    dob: $("dob"),
    dobLabel: $("dob-label"),
    captchaPanel: $("captcha-panel"),
    captchaImage: $("captcha-image"),
    captchaForm: $("captcha-form"),
    captcha: $("captcha"),
    captchaBtn: $("captcha-btn"),
    refreshCaptcha: $("refresh-captcha"),
    resultPanel: $("result-panel"),
    resultTitle: $("result-title"),
    resultTag: $("result-tag"),
    record: $("record"),
    copyJson: $("copy-json"),
    newSearch: $("new-search"),
  };

  const state = {
    type: "birth",
    captchaId: null,
    record: null,
    busy: false,
  };

  const LABELS = {
    name_bn: "Name (Bangla)",
    name_en: "Name (English)",
    date_of_birth: "Date of birth",
    birth_registration_number: "Registration number",
    sex: "Sex",
    birth_place_bn: "Place of birth (Bangla)",
    birth_place_en: "Place of birth",
    father_name_bn: "Father's name (Bangla)",
    father_name_en: "Father's name",
    mother_name_bn: "Mother's name (Bangla)",
    mother_name_en: "Mother's name",
    father_nationality_bn: "Father's nationality (Bangla)",
    father_nationality_en: "Father's nationality",
    mother_nationality_bn: "Mother's nationality (Bangla)",
    mother_nationality_en: "Mother's nationality",
    registration_date: "Registration date",
    registration_office: "Registration office",
    issuance_date: "Issue date",
  };

  const PREFERRED_ORDER = [
    "name_bn", "name_en", "date_of_birth", "birth_registration_number", "sex",
    "birth_place_bn", "birth_place_en",
    "father_name_bn", "father_name_en", "mother_name_bn", "mother_name_en",
    "father_nationality_bn", "father_nationality_en",
    "mother_nationality_bn", "mother_nationality_en",
    "registration_date", "registration_office", "issuance_date",
  ];

  function showAlert(message, kind = "error") {
    if (!message) {
      el.alert.hidden = true;
      el.alert.textContent = "";
      return;
    }
    el.alert.hidden = false;
    el.alert.textContent = message;
    el.alert.className = "alert " + kind;
  }

  function setBusy(busy) {
    state.busy = busy;
    [el.searchBtn, el.captchaBtn, el.refreshCaptcha].forEach((button) => {
      button.disabled = busy;
    });
    el.searchForm.setAttribute("aria-busy", busy ? "true" : "false");
    el.captchaForm.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function buildUrl(extra = {}) {
    const params = new URLSearchParams({
      type: state.type,
      number: el.number.value.replace(/\s+/g, ""),
      dob: el.dob.value,
      ...extra,
    });
    return "/api/verify?" + params.toString();
  }

  async function request(url) {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    let body = null;
    try {
      body = await res.json();
    } catch (_) {
      body = { message: "The server returned an unreadable response." };
    }
    return { status: res.status, body: body || {} };
  }

  function showCaptcha(payload, message, kind) {
    state.captchaId = payload.captcha ? payload.captcha.id : null;
    if (payload.captcha && payload.captcha.image_url) {
      el.captchaImage.src = payload.captcha.image_url;
      el.captchaImage.hidden = false;
    }
    el.resultPanel.hidden = true;
    el.captchaPanel.hidden = false;
    el.captcha.value = "";
    el.captcha.focus();
    showAlert(message || "", kind || "info");
    el.captchaPanel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function clearCaptcha() {
    state.captchaId = null;
    el.captchaPanel.hidden = true;
    el.captchaImage.removeAttribute("src");
  }

  function renderRecord(data) {
    const keys = PREFERRED_ORDER.filter((key) => data[key])
      .concat(Object.keys(data).filter((key) => !PREFERRED_ORDER.includes(key) && data[key]));

    el.record.textContent = "";
    keys.forEach((key) => {
      const dt = document.createElement("dt");
      dt.textContent = LABELS[key] || key.replace(/_/g, " ");
      const dd = document.createElement("dd");
      dd.textContent = String(data[key]);
      el.record.append(dt, dd);
    });

    el.resultTitle.textContent =
      state.type === "birth" ? "Birth record" : "Death record";
    el.resultTag.textContent = "Verified";
    el.resultPanel.hidden = false;
    el.captchaPanel.hidden = true;
    showAlert("");
    el.resultPanel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function handleFailure(status, body) {
    if (body.captcha) {
      showCaptcha(body, body.message, status === 422 ? "warn" : "info");
      return;
    }
    if (status === 410) clearCaptcha();
    showAlert(body.message || "Request failed with HTTP " + status + ".", "error");
  }

  async function submitSearch() {
    if (state.busy) return;
    if (!el.number.value.trim() || !el.dob.value) {
      showAlert("Enter both the registration number and the date.", "error");
      return;
    }
    setBusy(true);
    showAlert("");
    try {
      const { status, body } = await request(buildUrl());
      if (status === 200 && body.data) {
        state.record = body;
        renderRecord(body.data);
      } else {
        handleFailure(status, body);
      }
    } catch (error) {
      showAlert("Network error: " + error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function submitCaptcha() {
    if (state.busy) return;
    const answer = el.captcha.value.trim();
    if (!answer) {
      el.captcha.focus();
      return;
    }
    if (!state.captchaId) {
      showAlert("The captcha session is missing. Start again.", "error");
      return;
    }
    setBusy(true);
    showAlert("");
    try {
      const { status, body } = await request(
        buildUrl({ captcha_id: state.captchaId, captcha: answer })
      );
      if (status === 200 && body.data) {
        state.record = body;
        renderRecord(body.data);
      } else {
        handleFailure(status, body);
      }
    } catch (error) {
      showAlert("Network error: " + error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  function resetAll() {
    state.type = document.querySelector('input[name="type"]:checked').value;
    el.dobLabel.textContent =
      state.type === "birth" ? "Date of birth" : "Date of death";
    state.captchaId = null;
    state.record = null;
    el.number.value = "";
    el.dob.value = "";
    el.captcha.value = "";
    el.resultPanel.hidden = true;
    clearCaptcha();
    showAlert("");
    el.number.focus();
  }

  el.searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitSearch();
  });

  el.captchaForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitCaptcha();
  });

  el.refreshCaptcha.addEventListener("click", async () => {
    if (state.busy) return;
    setBusy(true);
    try {
      const { status, body } = await request(buildUrl());
      if (body.captcha) {
        showCaptcha(body, "", "info");
      } else {
        handleFailure(status, body);
      }
    } catch (error) {
      showAlert("Network error: " + error.message, "error");
    } finally {
      setBusy(false);
    }
  });

  document.querySelectorAll('input[name="type"]').forEach((input) => {
    input.addEventListener("change", () => {
      state.type = input.value;
      el.dobLabel.textContent =
        state.type === "birth" ? "Date of birth" : "Date of death";
      el.resultPanel.hidden = true;
      clearCaptcha();
      showAlert("");
    });
  });

  el.resetBtn.addEventListener("click", () => {
    // The reset event fires after the fields are cleared.
    setTimeout(resetAll, 0);
  });

  el.newSearch.addEventListener("click", resetAll);

  el.copyJson.addEventListener("click", async () => {
    if (!state.record) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(state.record, null, 2));
      el.copyJson.textContent = "Copied";
      setTimeout(() => { el.copyJson.textContent = "Copy JSON"; }, 1600);
    } catch (_) {
      showAlert("Copy failed — your browser blocked clipboard access.", "warn");
    }
  });

  el.captcha.addEventListener("input", () => showAlert(""));
})();
