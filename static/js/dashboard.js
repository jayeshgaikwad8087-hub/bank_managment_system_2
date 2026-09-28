// Animate numeric counters (used on dashboards for balance / stat cards)
function animateCounter(el, endValue, duration = 900, prefix = "") {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = start + (endValue - start) * eased;
    el.textContent = prefix + value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-counter]").forEach((el) => {
    const target = parseFloat(el.dataset.counter);
    const prefix = el.dataset.prefix || "";
    if (!isNaN(target)) animateCounter(el, target, 1000, prefix);
  });
});

// Live EMI preview on the calculator / apply-loan forms
function liveEmiPreview(principalId, rateId, tenureId, outputId) {
  const p = document.getElementById(principalId);
  const r = document.getElementById(rateId);
  const t = document.getElementById(tenureId);
  const out = document.getElementById(outputId);
  if (!p || !r || !t || !out) return;

  function recalc() {
    const principal = parseFloat(p.value) || 0;
    const rate = parseFloat(r.value) || 0;
    const tenure = parseInt(t.value) || 1;
    const monthlyRate = rate / 12 / 100;
    let emi;
    if (monthlyRate === 0) {
      emi = principal / tenure;
    } else {
      const factor = Math.pow(1 + monthlyRate, tenure);
      emi = (principal * monthlyRate * factor) / (factor - 1);
    }
    out.textContent = "₹" + (emi || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  }
  [p, r, t].forEach((el) => el.addEventListener("input", recalc));
  recalc();
}
