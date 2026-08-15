function passRateClass(rate) {
  if (rate >= 0.8) return "rate-high";
  if (rate >= 0.5) return "rate-mid";
  return "rate-low";
}

async function loadLeaderboard() {
  const body = document.getElementById("leaderboard-body");

  let rows;
  try {
    const res = await fetch("/api/leaderboard");
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

loadLeaderboard();
