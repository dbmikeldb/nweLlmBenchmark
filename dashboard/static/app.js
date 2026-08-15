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

async function loadRunOptions(date) {
  const select = document.getElementById("run-filter");
  document.getElementById("run-detail").classList.add("hidden");

  if (!date) {
    select.innerHTML = `<option value="">Select a date first</option>`;
    select.disabled = true;
    return;
  }

  let runs;
  try {
    const res = await fetch(`/api/runs?date=${date}`);
    runs = await res.json();
  } catch (err) {
    select.innerHTML = `<option value="">Failed to load runs</option>`;
    select.disabled = true;
    return;
  }

  if (runs.length === 0) {
    select.innerHTML = `<option value="">No runs on this date</option>`;
    select.disabled = true;
    return;
  }

  select.innerHTML = `<option value="">All runs</option>` + runs.map(run =>
    `<option value="${run.run_id}">${run.title} — ${run.timestamp}${run.errors ? ` (${run.errors} errors)` : ""}</option>`
  ).join("");
  select.disabled = false;
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
    loadRunOptions(select.value);
  });
}

function setupRunFilter() {
  const select = document.getElementById("run-filter");
  select.addEventListener("change", () => {
    if (select.value) {
      loadRunDetail(select.value);
    } else {
      document.getElementById("run-detail").classList.add("hidden");
    }
  });
}

loadDates();
loadLeaderboard();
setupRunFilter();
