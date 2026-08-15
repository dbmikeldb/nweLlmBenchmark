function passRateClass(rate) {
  if (rate >= 0.8) return "rate-high";
  if (rate >= 0.5) return "rate-mid";
  return "rate-low";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function statusBadge(record) {
  if ("error" in record) return `<span class="badge rate-low">ERROR</span>`;
  return record.grading.pass
    ? `<span class="badge rate-high">PASS</span>`
    : `<span class="badge rate-low">FAIL</span>`;
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

async function loadRuns(date) {
  const body = document.getElementById("runs-body");

  let runs;
  try {
    const url = date ? `/api/runs?date=${date}` : "/api/runs";
    const res = await fetch(url);
    runs = await res.json();
  } catch (err) {
    body.innerHTML = `<tr><td colspan="5">Failed to load runs: ${err}</td></tr>`;
    return;
  }

  if (runs.length === 0) {
    body.innerHTML = `<tr><td colspan="5">No runs yet.</td></tr>`;
    return;
  }

  body.innerHTML = runs.map(run => `
    <tr class="run-row" data-run-id="${run.run_id}">
      <td>${run.title}</td>
      <td>${run.vendor} / ${run.os_train}</td>
      <td>${run.timestamp}</td>
      <td>${run.models}</td>
      <td>${run.errors}</td>
    </tr>
  `).join("");

  for (const row of body.querySelectorAll(".run-row")) {
    row.addEventListener("click", () => loadRunDetail(row.dataset.runId));
  }
}

async function loadRunDetail(runId) {
  const section = document.getElementById("run-detail");
  const title = document.getElementById("run-detail-title");
  const body = document.getElementById("run-detail-body");

  let run;
  try {
    const res = await fetch(`/api/runs/${runId}`);
    run = await res.json();
  } catch (err) {
    return;
  }

  section.classList.remove("hidden");
  title.textContent = `${run.title} — ${run.run_id}`;

  body.innerHTML = run.records.map(record => {
    const details = "error" in record
      ? escapeHtml(record.error)
      : `${escapeHtml(record.response)}\n\n${escapeHtml(JSON.stringify(record.grading, null, 2))}`;

    return `
      <tr>
        <td>${record.model}</td>
        <td>${statusBadge(record)}</td>
        <td>${record.cost_usd != null ? "$" + record.cost_usd : "—"}</td>
        <td>${record.latency_ms != null ? Math.round(record.latency_ms) + "ms" : "—"}</td>
        <td><details><summary>view</summary><pre>${details}</pre></details></td>
      </tr>
    `;
  }).join("");
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

  select.addEventListener("change", () => {
    loadLeaderboard(select.value);
    loadRuns(select.value);
    document.getElementById("run-detail").classList.add("hidden");
  });
}

loadDates();
loadLeaderboard();
loadRuns();
