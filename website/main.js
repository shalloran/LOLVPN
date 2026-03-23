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
  const elApiTracked = document.getElementById("api-tracked");

  const elVpnGrid = document.getElementById("vpn-grid");
  const elVpnFilter = document.getElementById("vpn-filter");
  const elVpnCount = document.getElementById("vpn-count");
  const elVpnErr = document.getElementById("vpn-load-error");

  document.getElementById("link-pr").href = `${repoBase}/pulls`;
  document.getElementById("link-issues").href = `${repoBase}/issues/new/choose`;
  document.getElementById("link-repo").href = repoBase;
  const prof = document.getElementById("link-profile");
  prof.href = profileUrl;
  prof.textContent = `GitHub @${site.githubUsername}`;
  const profFooter = document.getElementById("link-profile-text");
  profFooter.href = profileUrl;
  profFooter.textContent = `@${site.githubUsername}`;

  const baseUrl = window.location.href;
  if (elApi) {
    elApi.href = new URL("api/queries.json", baseUrl).href;
  }
  if (elApiTracked) {
    elApiTracked.href = new URL("api/tracked-vpns.json", baseUrl).href;
  }

  let rows = [];
  let vpnBrands = [];
  let browseByQueryId = {};

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function initialsFromName(name) {
    const parts = name
      .replace(/[^a-z0-9]+/gi, " ")
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (parts.length === 0) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
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

  function uniqueQueryIds(refs) {
    const seen = new Set();
    const out = [];
    for (const r of refs || []) {
      if (!seen.has(r.id)) {
        seen.add(r.id);
        out.push(r.id);
      }
    }
    return out;
  }

  function renderVpns(list) {
    elVpnGrid.innerHTML = list
      .map((b) => {
        const tokenSpans = (b.tokens || [])
          .map((t) => `<span class="vpn-token" title="${esc(t)}">${esc(t)}</span>`)
          .join("");
        const qids = uniqueQueryIds(b.queries).sort();
        const qLinksInner = qids.length
          ? qids
              .map((id) => {
                const href = browseByQueryId[id] || `${repoBase}/tree/main/queries/${id}`;
                return `<a class="vpn-query-link" href="${esc(href)}">${esc(id)}</a>`;
              })
              .join("")
          : '<span class="vpn-queries-none">—</span>';
        const logo = b.logoUrl
          ? `<img src="${esc(b.logoUrl)}" alt="" width="46" height="46" loading="lazy" decoding="async" data-fallback="${esc(initialsFromName(b.name))}" />`
          : "";
        const markInner = logo
          ? logo
          : `<span class="vpn-mark-fallback">${esc(initialsFromName(b.name))}</span>`;
        return `<article class="vpn-card" data-id="${esc(b.id)}">
          <div class="vpn-card-head">
            <div class="vpn-mark">${markInner}</div>
            <h3>${esc(b.name)}</h3>
          </div>
          <p class="vpn-tokens-label">Detection literals</p>
          <div class="vpn-tokens">${tokenSpans || `<span class="vpn-token">—</span>`}</div>
          <div class="vpn-queries">
            <span class="vpn-queries-prefix">Queries</span>
            ${qLinksInner}
          </div>
        </article>`;
      })
      .join("");

    elVpnGrid.querySelectorAll(".vpn-mark img").forEach((img) => {
      img.addEventListener("error", () => {
        const fb = img.getAttribute("data-fallback") || "?";
        const wrap = img.parentElement;
        if (wrap) {
          wrap.innerHTML = `<span class="vpn-mark-fallback">${esc(fb)}</span>`;
        }
      });
    });

    elVpnCount.textContent = `${list.length} vendor${list.length === 1 ? "" : "s"}`;
  }

  function applyVpnFilter() {
    const q = (elVpnFilter.value || "").trim().toLowerCase();
    if (!q) {
      renderVpns(vpnBrands);
      return;
    }
    renderVpns(
      vpnBrands.filter((b) => {
        const hay = [
          b.id,
          b.name,
          ...(b.tokens || []),
          ...(b.queries || []).map((r) => `${r.id} ${r.array}`),
        ]
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      }),
    );
  }

  Promise.all([
    fetch(new URL("api/queries.json", baseUrl).href).then((r) => {
      if (!r.ok) throw new Error(`queries.json HTTP ${r.status}`);
      return r.json();
    }),
    fetch(new URL("api/tracked-vpns.json", baseUrl).href).then((r) => {
      if (!r.ok) throw new Error(`tracked-vpns.json HTTP ${r.status}`);
      return r.json();
    }),
  ])
    .then(([queries, tracked]) => {
      if (!Array.isArray(queries)) throw new Error("invalid queries json");
      rows = queries;
      browseByQueryId = Object.fromEntries(rows.map((q) => [q.id, q.githubBrowse]));

      elTable.hidden = false;
      render(rows);
      elFilter.addEventListener("input", applyFilter);

      const brands = tracked && Array.isArray(tracked.brands) ? tracked.brands : [];
      vpnBrands = brands;
      elVpnGrid.hidden = false;
      renderVpns(vpnBrands);
      elVpnFilter.addEventListener("input", applyVpnFilter);
    })
    .catch((e) => {
      elErr.hidden = false;
      elErr.textContent = `Could not load site data (${e.message}). For local file:// preview, run: python scripts/build_site_data.py`;
      if (elVpnErr) {
        elVpnErr.hidden = false;
        elVpnErr.textContent = elErr.textContent;
      }
    });
})();
