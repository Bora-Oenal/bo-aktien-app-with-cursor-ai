// frontend/script.js
document.addEventListener("DOMContentLoaded", () => {
  const loadBtn = document.getElementById("loadBtn");
  const table   = document.getElementById("stocksTable");
  const tbody   = table.querySelector("tbody");

  loadBtn.addEventListener("click", async () => {
    loadBtn.disabled  = true;
    loadBtn.textContent = "Lade …";

    try {
      const resp = await fetch("/api/stocks/");
      if (!resp.ok) throw new Error("Server " + resp.status);
      const stocks = await resp.json();

      tbody.innerHTML = "";
      stocks.forEach(row => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-gray-100 text-sm";

        tr.innerHTML = `
          <td class="border p-2">${row.name ?? ""}</td>
          <td class="border p-2 text-right">${fmt(row.current_price)}</td>

          <td class="border p-2 text-right">${fmt(row.growth_5y_percent,1)}</td>
          <td class="border p-2 text-right">${fmt(row.eps_in_5y)}</td>
          <td class="border p-2 text-right">${row.target_pe_ratio ?? "-"}</td>
          <td class="border p-2 text-right">${fmt(row.price_in_5y)}</td>
          <td class="border p-2 text-right">${fmt(row.fair_value)}</td>
          <td class="border p-2 text-right">${fmt(row.price_diff)}</td>
          <td class="border p-2 text-right">${fmt(row.potential_percent,1)}</td>
        `;
        tbody.appendChild(tr);
      });

      table.classList.remove("hidden");
    } catch (err) {
      alert("Fehler beim Laden: " + err.message);
    } finally {
      loadBtn.disabled  = false;
      loadBtn.textContent = "Aktien laden";
    }
  });

  // Zahl formatieren – zeigt "-" für null/undefined
  function fmt(num, decimals = 2) {
    return (num || num === 0) ? num.toFixed(decimals) : "-";
  }
});
