document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-close").forEach(button => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });

  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", event => {
      if (!window.confirm(form.dataset.confirm || "Are you sure?")) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener("change", () => {
      const min = input.min === "" ? null : Number(input.min);
      const max = input.max === "" ? null : Number(input.max);
      let value = Number(input.value);
      if (!Number.isFinite(value)) value = min ?? 1;
      if (min !== null && value < min) value = min;
      if (max !== null && value > max) value = max;
      input.value = String(value);
    });
  });
});
