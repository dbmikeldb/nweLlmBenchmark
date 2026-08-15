function passRateClass(rate) {
  if (rate >= 0.8) return "rate-high";
  if (rate >= 0.5) return "rate-mid";
  return "rate-low";
}

async function loadLeaderboard(date) {
  const body = document.getElementById("leaderboard-body");

  let rows;
  try {
    const url = date ? `/api/leaderboard?date=${date}` : "/api/leaderboard";
    const res = await fetch(url);
    rows = await res.json();
  } catch (err) {
    body.innerHTML = `<tr><td colspan="5">Failed to load leaderboard: ${err}</td></tr>`;
    return;
  }

  if (rows.length === 0) {
    body.innerHTML = `<tr><td colspan="5">No results yet.</td></tr>`;
    return;
  }

  body.innerHTML = rows.map(row => `
    <tr>
      <td>${row.model}</td>
      <td>${row.vendor} / ${row.os_train}</td>
      <td>${row.category}</td>
      <td><span class="badge ${passRateClass(row.pass_rate)}">${Math.round(row.pass_rate * 100)}%</span></td>
      <td>${row.passes}/${row.runs}</td>
    </tr>
  `).join("");
}

async function loadDates() {
  const select = document.getElementById("date-filter");

  let dates;
  try {
    const res = await fetch("/api/dates");
    dates = await res.json();
  } catch (err) {
    return;
  }

  for (const date of dates) {
    const option = document.createElement("option");
    option.value = date;
    option.textContent = date;
    select.appendChild(option);
  }

  select.addEventListener("change", () => loadLeaderboard(select.value));
}

loadDates();
loadLeaderboard();
