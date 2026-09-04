function escapeHTML(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Cyber Trade Clearinghouse - Client-Side Demonstration & WebCrypto Verification Engine
 */

class ClearinghouseApp {
  constructor() {
    this.registryData = {
      locals: [],
      employers: [],
      practitioners: [],
      safety_non_concurrences: []
    };
    this.currentBundle = null;
  }

  async init() {
    await this.loadRegistryData();
    this.renderPractitionersTable();
    this.renderEmployersTable();
        this.renderNonConcurrenceTable();
    this.renderActuarialManifest("PEC-EMP-2026-0001");
    this.setupEventListeners();
  }

  async loadRegistryData() {
    try {
      const res = await fetch("data/mock_registry.json");
      if (res.ok) {
        this.registryData = await res.json();
      }
    } catch (e) {
      console.warn("Using fallback mock registry data:", e);
    }
  }

  // WebCrypto SHA-256 helper
  async sha256Hex(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
  }

  // Chained Entry Hash
  async computeEntryHash(logId, prevHash, practitionerId, date, hours, coreDomain, artifactRef) {
    const prev = prevHash || "GENESIS_NODE_0000000000000000";
    const payload = `${logId}:${prev}:${practitionerId}:${date}:${Number(hours).toFixed(2)}:${coreDomain}:${artifactRef}`;
    return await this.sha256Hex(payload);
  }

  // Merkle Root calculation
  async computeMerkleRoot(entryHashes) {
    if (!entryHashes || entryHashes.length === 0) {
      return await this.sha256Hex("EMPTY_LEDGER_ROOT");
    }
    let currentLayer = entryHashes.map(h => h.startsWith("sha256:") ? h.slice(7) : h);
    while (currentLayer.length > 1) {
      const nextLayer = [];
      for (let i = 0; i < currentLayer.length; i += 2) {
        const left = currentLayer[i];
        const right = i + 1 < currentLayer.length ? currentLayer[i + 1] : left;
        const combined = await this.sha256Hex(`${left}:${right}`);
        nextLayer.push(combined);
      }
      currentLayer = nextLayer;
    }
    return currentLayer[0];
  }


  renderPractitionersTable() {
    const tbody = document.getElementById("practitioners-tbody");
    if (!tbody) return;
    tbody.textContent = "";

    const searchInput = document.getElementById("practitioner-search");
    const localFilter = document.getElementById("practitioner-local-filter");
    const modalityFilter = document.getElementById("practitioner-modality-filter");

    const q = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const loc = localFilter ? localFilter.value : "ALL";
    const mod = modalityFilter ? modalityFilter.value : "ALL";

    const filtered = (this.registryData.practitioners || []).filter(p => {
      const matchQ = !q || (
        p.trade_id.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        p.tier.toLowerCase().includes(q) ||
        (p.active_endorsements && p.active_endorsements.some(e => e.toLowerCase().includes(q)))
      );
      const matchLoc = loc === "ALL" || p.assigned_jatc_local === loc;
      const matchMod = mod === "ALL" || p.work_modality_preference === mod || p.work_modality_preference === "Any Modality";
      return matchQ && matchLoc && matchMod;
    });

    if (filtered.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 9;
      td.textContent = "No registered practitioners found matching search filters.";
      td.style.textAlign = "center";
      td.style.color = "var(--text-muted)";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    filtered.forEach(p => {
      const tr = document.createElement("tr");

      const tdId = document.createElement("td");
      tdId.className = "mono";
      tdId.textContent = p.trade_id;

      const tdName = document.createElement("td");
      tdName.textContent = p.name;
      tdName.style.fontWeight = "600";

      const tdTier = document.createElement("td");
      tdTier.textContent = p.tier;

      const tdEmployer = document.createElement("td");
      if (p.is_seeking_placement) {
        tdEmployer.innerHTML = `<span style="color:var(--accent-amber); font-weight:600;">Seeking Placement</span><br><span style="font-size:10px; color:var(--text-muted);">Available for Dispatch</span>`;
      } else {
        tdEmployer.innerHTML = `<span style="font-weight:600; color:#fff;">${escapeHTML(p.sponsoring_employer || "Registered Sponsor")}</span><br><span class="mono" style="font-size:10px; color:var(--accent-cyan);">${escapeHTML(p.sponsoring_pec_id || "PEC-EMP")}</span>`;
      }

      const tdLocal = document.createElement("td");
      tdLocal.className = "mono";
      tdLocal.textContent = p.assigned_jatc_local;

      const tdHours = document.createElement("td");
      tdHours.className = "mono";
      tdHours.textContent = `${p.total_verified_hours.toLocaleString()} hrs`;

      const tdEndorsements = document.createElement("td");
      if (p.active_endorsements && p.active_endorsements.length > 0) {
        p.active_endorsements.forEach(e => {
          const span = document.createElement("span");
          span.className = "badge badge-specialty";
          span.style.marginRight = "4px";
          span.textContent = e;
          tdEndorsements.appendChild(span);
        });
      } else {
        tdEndorsements.textContent = "Core Rotations";
        tdEndorsements.style.color = "var(--text-muted)";
      }

      const tdModality = document.createElement("td");
      tdModality.innerHTML = `<span style="color:var(--accent-cyan); font-weight:600;">${escapeHTML(p.work_modality_preference || "Any")}</span><br><span style="font-size:10px; color:var(--text-muted);">${escapeHTML(p.relocation_willingness || "Local Only")}</span>`;

      const tdStatus = document.createElement("td");
      const statusBadge = document.createElement("span");
      if (p.is_seeking_placement) {
        statusBadge.className = "badge badge-override";
        statusBadge.textContent = `Seeking (${p.days_seeking_placement}d)`;
      } else {
        statusBadge.className = "badge badge-active";
        statusBadge.textContent = "Active / Employed";
      }
      tdStatus.appendChild(statusBadge);

      tr.appendChild(tdId);
      tr.appendChild(tdName);
      tr.appendChild(tdTier);
      tr.appendChild(tdEmployer);
      tr.appendChild(tdLocal);
      tr.appendChild(tdHours);
      tr.appendChild(tdEndorsements);
      tr.appendChild(tdModality);
      tr.appendChild(tdStatus);

      tbody.appendChild(tr);
    });
  }

  renderEmployersTable() {
    const tbody = document.getElementById("employers-tbody");
    if (!tbody) return;
    tbody.textContent = "";

    (this.registryData.employers || []).forEach(emp => {
      const tr = document.createElement("tr");

      const tdEnterprise = document.createElement("td");
      tdEnterprise.innerHTML = `<strong>${escapeHTML(emp.name)}</strong><br><span class="mono" style="font-size:11px; color:var(--accent-cyan);">${escapeHTML(emp.pec_id)}</span> &bull; <span style="font-size:11px; color:var(--text-muted);">${escapeHTML(emp.division)}</span>`;

      const tdHubs = document.createElement("td");
      tdHubs.innerHTML = `<span style="color:#fff; font-size:12px;">${escapeHTML(emp.operating_hubs || "District 1")}</span>`;

      const tdMor = document.createElement("td");
      tdMor.innerHTML = `<div style="font-weight:700; color:#fff;">${escapeHTML(emp.designated_mor)}</div><div style="display:flex; align-items:center; gap:6px; margin-top:3px; flex-wrap:wrap;"><span class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHTML(emp.designated_mor_id || "CTP-MST")}</span><span class="badge badge-specialty" style="font-size:10px; padding:1px 5px;">${escapeHTML(emp.mor_status || "Full-Time MoR")}</span></div>`;

      const totalStaff = (emp.master_count || 1) + emp.journeyman_count + emp.apprentice_count;
      const tdStaffing = document.createElement("td");
      tdStaffing.innerHTML = `<span style="font-weight:700; color:#fff;">${totalStaff} Trade Operators</span><br><span style="font-size:11px; color:var(--text-secondary);">${emp.master_count || 1} Masters &bull; ${emp.journeyman_count} Journeymen &bull; ${emp.apprentice_count} Apprentices</span>`;

      const tdCompliance = document.createElement("td");
      const badgeClass = emp.ratio_compliance_score >= 0.95 ? "badge badge-active" : "badge badge-override";
      tdCompliance.innerHTML = `<span class="${badgeClass}">${(emp.ratio_compliance_score * 100).toFixed(1)}% (2:1 Ratio)</span><br><span style="font-size:11px; color:var(--accent-cyan); font-weight:600;">${emp.underwriter_tier}</span>`;

      tr.appendChild(tdEnterprise);
      tr.appendChild(tdHubs);
      tr.appendChild(tdMor);
      tr.appendChild(tdStaffing);
      tr.appendChild(tdCompliance);

      tbody.appendChild(tr);
    });
  }

  renderNonConcurrenceTable() {
    const tbody = document.getElementById("nonconcurrence-tbody");
    if (!tbody) return;
    tbody.textContent = "";

    (this.registryData.safety_non_concurrences || []).forEach(rec => {
      const tr = document.createElement("tr");

      const tdId = document.createElement("td");
      tdId.className = "mono";
      tdId.textContent = rec.record_id;

      const tdDate = document.createElement("td");
      tdDate.textContent = rec.timestamp.split("T")[0];

      const tdMor = document.createElement("td");
      tdMor.className = "mono";
      tdMor.textContent = rec.submitting_mor_id;

      const tdOrg = document.createElement("td");
      tdOrg.textContent = rec.enterprise_name;

      const tdHash = document.createElement("td");
      tdHash.className = "mono";
      tdHash.textContent = rec.payload_hash.slice(0, 20) + "...";
      tdHash.title = rec.payload_hash;

      const tdStatus = document.createElement("td");
      const b = document.createElement("span");
      if (rec.executive_override_received) {
        b.className = "badge badge-override";
        b.textContent = "Executive Override Executed";
      } else {
        b.className = "badge badge-active";
        b.textContent = "Active Refusal in Effect";
      }
      tdStatus.appendChild(b);

      tr.appendChild(tdId);
      tr.appendChild(tdDate);
      tr.appendChild(tdMor);
      tr.appendChild(tdOrg);
      tr.appendChild(tdHash);
      tr.appendChild(tdStatus);

      tbody.appendChild(tr);
    });
  }


  renderActuarialManifest(pecId) {
    const out = document.getElementById("actuarial-json-output");
    if (!out) return;

    const emp = (this.registryData.employers || []).find(e => e.pec_id === pecId) || (this.registryData.employers && this.registryData.employers[0]);
    if (!emp) return;

    const manifest = {
      "$schema": "https://cybertrade.org/schemas/v1/underwriter-attestation.json",
      "attestation_id": "urn:uuid:3c2b1a0e-9f4a-4c28-98e2-0d12e8b9f1a4",
      "reporting_period": {
        "start_date": "2026-06-01",
        "end_date": "2026-08-31"
      },
      "sponsoring_enterprise": {
        "pec_registration_id": emp.pec_id,
        "enterprise_name": emp.name,
        "industry_division": emp.division,
        "operating_jurisdictions": emp.operating_hubs || "District 1"
      },
      "compliance_summary": {
        "active_master_of_record": true,
        "mor_designation": `${escapeHTML(emp.designated_mor)} (${emp.designated_mor_id || 'CTP-MST'})`,
        "mor_status": emp.mor_status || "Full-Time MoR",
        "supervisory_ratio_compliance_score": emp.ratio_compliance_score,
        "mandatory_ratio_standard": "2:1 on-shift operational supervision",
        "active_workforce_headcount": {
          "master_practitioners": emp.master_count || 1,
          "licensed_journeymen": emp.journeyman_count,
          "registered_apprentices": emp.apprentice_count,
          "total_trade_operators": (emp.master_count || 1) + emp.journeyman_count + emp.apprentice_count
        },
        "total_verified_ojt_runtime_hours": emp.total_verified_hours,
        "unresolved_safety_non_concurrences": 0
      },
      "actuarial_incentive_tier": {
        "underwriting_risk_classification": emp.underwriter_tier,
        "cuaac_preferred_risk_credit": emp.ratio_compliance_score >= 0.98 ? "35% Preferred Premium Credit" : "25% Standard Premium Credit"
      },
      "clearinghouse_signature": {
        "issued_by": "National Cybersecurity Trade Board Clearinghouse",
        "signature": "MEQCIG9X...[NCTB Root Public Key Signature]...",
        "issued_timestamp": "2026-08-31T00:00:00Z"
      }
    };

    out.textContent = JSON.stringify(manifest, null, 2);
  }

  setupEventListeners() {
    const dropzone = document.getElementById("bundle-dropzone");
    const fileInput = document.getElementById("bundle-file-input");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
          this.handleFile(e.dataTransfer.files[0]);
        }
      });
      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.handleFile(e.target.files[0]);
        }
      });
    }

    const searchInput = document.getElementById("practitioner-search");
    const localFilter = document.getElementById("practitioner-local-filter");
    const modalityFilter = document.getElementById("practitioner-modality-filter");

    if (searchInput) {
      searchInput.addEventListener("input", () => this.renderPractitionersTable());
    }
    if (localFilter) {
      localFilter.addEventListener("change", () => this.renderPractitionersTable());
    }
    if (modalityFilter) {
      modalityFilter.addEventListener("change", () => this.renderPractitionersTable());
    }
  }

  handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target.result);
        this.processBundleJson(json);
      } catch (err) {
        alert("Invalid JSON file format.");
      }
    };
    reader.readAsText(file);
  }
}

function switchWorkspace(wsId) {
  document.querySelectorAll(".nav-ribbon .tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-workspace") === wsId);
  });
  document.querySelectorAll(".view-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === wsId);
  });
}

function switchSubView(wsId, subId) {
  const wsEl = document.getElementById(wsId);
  if (!wsEl) return;

  wsEl.querySelectorAll(".sub-pill-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-sub") === subId);
  });
  wsEl.querySelectorAll(".sub-view-panel").forEach(panel => {
    panel.style.display = panel.id === subId ? "block" : "none";
  });
}

window.switchWorkspace = switchWorkspace;
window.switchSubView = switchSubView;

window.addEventListener("DOMContentLoaded", () => {
  window.app = new ClearinghouseApp();
  window.app.init();
});


