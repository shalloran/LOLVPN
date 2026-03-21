(function () {
  const site = window.LOLVPN_SITE || {
    githubUsername: "shalloran",
    githubRepo: "shalloran/LOLVPN",
  };
  const repoBase = `https://github.com/${site.githubRepo}`;
  const profileUrl = `https://github.com/${site.githubUsername}`;

  const elTable = document.getElementById("query-table");
  const elBody = document.getElementById("query-tbody");
  const elFilter = document.getElementById("filter");
  const elCount = document.getElementById("query-count");
  const elErr = document.getElementById("load-error");
  const elApi = document.getElementById("api-json");

  document.getElementById("link-pr").href = `${repoBase}/pulls`;
  document.getElementById("link-issues").href = `${repoBase}/issues/new/choose`;
  document.getElementById("link-repo").href = repoBase;
  const prof = document.getElementById("link-profile");
  prof.href = profileUrl;
  prof.textContent = `GitHub @${site.githubUsername}`;
  const profFooter = document.getElementById("link-profile-text");
  profFooter.href = profileUrl;
  profFooter.textContent = `@${site.githubUsername}`;

  if (elApi) {
    elApi.href = new URL("api/queries.json", window.location.href).href;
  }

  let rows = [];

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function render(list) {
    elBody.innerHTML = list
      .map((q) => {
        const tags = (q.tags || [])
          .map((t) => `<span class="tag">${esc(t)}</span>`)
          .join("");
        const tables = (q.tables || []).join(", ");
        return `<tr data-id="${esc(q.id)}">
          <td><strong>${esc(q.title)}</strong><div class="muted" style="color:var(--muted);font-size:0.8rem;margin-top:0.25rem">${esc(q.id)} · v${esc(String(q.version))}</div></td>
          <td class="hide-sm">${esc(q.description || "—")}</td>
          <td><div class="tags">${tags || "—"}</div></td>
          <td class="hide-sm">${esc(tables || "—")}</td>
          <td class="actions"><a href="${esc(q.githubRawKql)}">raw kql</a><a href="${esc(q.githubBrowse)}">folder</a></td>
        </tr>`;
      })
      .join("");
    elCount.textContent = `${list.length} quer${list.length === 1 ? "y" : "ies"}`;
  }

  function applyFilter() {
    const q = (elFilter.value || "").trim().toLowerCase();
    if (!q) {
      render(rows);
      return;
    }
    render(
      rows.filter((r) => {
        const hay = [
          r.id,
          r.title,
          r.description,
          ...(r.tags || []),
          ...(r.tables || []),
        ]
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      }),
    );
  }

  fetch("api/queries.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((data) => {
      if (!Array.isArray(data)) throw new Error("invalid json");
      rows = data;
      elTable.hidden = false;
      render(rows);
      elFilter.addEventListener("input", applyFilter);
    })
    .catch((e) => {
      elErr.hidden = false;
      elErr.textContent = `Could not load query list (${e.message}). For local file:// preview, run: python scripts/build_site_data.py`;
    });
})();
