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
    this.renderLocalsAndDispatch();
    this.renderRequisitionsTable();
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

  renderLocalsAndDispatch() {
    const grid = document.getElementById("locals-card-grid");
    if (grid) {
      grid.textContent = "";
      (this.registryData.locals || []).forEach(loc => {
        const card = document.createElement("div");
        card.style.background = "var(--bg-secondary)";
        card.style.border = "1px solid var(--border-color)";
        card.style.borderRadius = "var(--radius-md)";
        card.style.padding = "1.1rem";

        const title = document.createElement("div");
        title.style.fontWeight = "700";
        title.style.fontSize = "14px";
        title.style.color = "#fff";
        title.style.marginBottom = "3px";
        title.textContent = loc.name;

        const territory = document.createElement("div");
        territory.style.fontSize = "11px";
        territory.style.color = "var(--text-secondary)";
        territory.style.marginBottom = "8px";
        territory.textContent = loc.jurisdiction_territory;

        const zoneSchedule = document.createElement("div");
        zoneSchedule.style.background = "rgba(0,0,0,0.25)";
        zoneSchedule.style.border = "1px solid rgba(255,255,255,0.05)";
        zoneSchedule.style.borderRadius = "var(--radius-sm)";
        zoneSchedule.style.padding = "8px 10px";
        zoneSchedule.style.fontSize = "11px";
        zoneSchedule.style.marginBottom = "8px";
        zoneSchedule.style.lineHeight = "1.5";
        zoneSchedule.innerHTML = `
          <div style="font-weight:700; color:var(--text-primary); margin-bottom:4px;">Local MSA Zone Wage Schedule:</div>
          <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
            <span>&bull; Zone 1 (Metro Core - ${loc.zone_1_examples}):</span>
            <span style="color:var(--accent-emerald); font-weight:700;">$${loc.zone_1_rate.toFixed(2)}/hr</span>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
            <span>&bull; Zone 2 (Secondary Metro - ${loc.zone_2_examples}):</span>
            <span style="color:var(--accent-cyan); font-weight:700;">$${loc.zone_2_rate.toFixed(2)}/hr</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span>&bull; Zone 3 (Non-Metro / Rural Floor):</span>
            <span style="color:var(--text-primary); font-weight:700;">$${loc.zone_3_rate.toFixed(2)}/hr Floor</span>
          </div>
        `;

        const metaRow = document.createElement("div");
        metaRow.style.display = "flex";
        metaRow.style.justifyContent = "space-between";
        metaRow.style.fontSize = "11px";
        metaRow.innerHTML = `<span style="color:var(--accent-cyan); font-weight:600;">Active Trade Staffing:</span><span class="mono" style="color:#fff; font-weight:600;">${loc.active_master_count || 0} Masters &bull; ${loc.active_journeyman_count} Journeymen &bull; ${loc.active_apprentice_count} Apprentices</span>`;

        card.appendChild(title);
        card.appendChild(territory);
        card.appendChild(zoneSchedule);
        card.appendChild(metaRow);
        grid.appendChild(card);
      });
    }

    const queueTbody = document.getElementById("dispatch-queue-tbody");
    if (queueTbody) {
      queueTbody.textContent = "";
      const seeking = (this.registryData.practitioners || [])
        .filter(p => p.is_seeking_placement)
        .sort((a, b) => b.days_seeking_placement - a.days_seeking_placement);

      seeking.forEach((p, idx) => {
        const tr = document.createElement("tr");

        const tdPos = document.createElement("td");
        tdPos.className = "mono";
        tdPos.style.fontWeight = "700";
        tdPos.style.color = idx === 0 ? "var(--accent-emerald)" : "var(--text-primary)";
        tdPos.textContent = `#${idx + 1} ${idx === 0 ? "(Next Referral)" : ""}`;

        const tdName = document.createElement("td");
        tdName.innerHTML = `<strong>${p.name}</strong><br><span class="mono" style="font-size:11px; color:var(--text-muted);">${p.trade_id}</span>`;

        const tdTier = document.createElement("td");
        let tierHtml = `<strong>${escapeHTML(p.tier)}</strong>`;
        if (p.seeking_mor_role) {
          tierHtml += `<br><span class="badge badge-specialty" style="font-size:10px; padding:1px 5px; margin-top:2px;">${escapeHTML(p.mor_availability || "Available as MoR")}</span>`;
        }
        tdTier.innerHTML = tierHtml;

        const tdLocal = document.createElement("td");
        tdLocal.className = "mono";
        tdLocal.textContent = p.assigned_jatc_local;

        const tdMobility = document.createElement("td");
        tdMobility.innerHTML = `<span style="color:var(--accent-cyan);">${p.work_modality_preference}</span><br><span style="font-size:10px; color:var(--text-muted);">${p.security_clearance || "Unclassified"}</span>`;

        const tdDays = document.createElement("td");
        tdDays.className = "mono";
        tdDays.style.fontWeight = "700";
        if (p.days_seeking_placement >= 30) {
          tdDays.style.color = "var(--accent-rose)";
          tdDays.innerHTML = `${p.days_seeking_placement} days<br><span class="badge badge-specialty" style="background:rgba(244,63,94,0.15); color:var(--accent-rose); border-color:rgba(244,63,94,0.3); font-size:9px; padding:1px 4px;">Aging Alert (30+d)</span>`;
        } else {
          tdDays.style.color = "var(--accent-amber)";
          tdDays.textContent = `${p.days_seeking_placement} days`;
        }

        const tdBook = document.createElement("td");
        const bookBadge = document.createElement("span");
        bookBadge.className = "badge badge-active";
        bookBadge.textContent = p.dispatch_book || "Book 1 (Resident)";
        tdBook.appendChild(bookBadge);

        tr.appendChild(tdPos);
        tr.appendChild(tdName);
        tr.appendChild(tdTier);
        tr.appendChild(tdLocal);
        tr.appendChild(tdMobility);
        tr.appendChild(tdDays);
        tr.appendChild(tdBook);

        queueTbody.appendChild(tr);
      });
    }
  }
  renderRequisitionsTable() {
    const tbody = document.getElementById("requisitions-tbody");
    if (!tbody) return;
    tbody.textContent = "";

    const reqs = this.registryData.labor_requisitions || [];
    if (reqs.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 7;
      td.textContent = "No pending labor requisitions currently on file.";
      td.style.textAlign = "center";
      td.style.color = "var(--text-muted)";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    reqs.forEach(r => {
      const tr = document.createElement("tr");

      const tdId = document.createElement("td");
      tdId.className = "mono";
      tdId.innerHTML = `<strong>${escapeHTML(r.requisition_id)}</strong><br><span style="font-size:10px; color:var(--text-muted);">${escapeHTML(r.date_submitted || "2026-09-01")}</span>`;

      const tdEmp = document.createElement("td");
      tdEmp.innerHTML = `<strong>${escapeHTML(r.employer_name)}</strong><br><span style="font-size:11px; color:var(--text-secondary);">${escapeHTML(r.requisition_title || "Standard Operational Requisition")}</span>`;

      const tdTier = document.createElement("td");
      tdTier.textContent = r.required_tier;

      const tdMor = document.createElement("td");
      if (r.requires_mor) {
        tdMor.innerHTML = `<span class="badge badge-specialty" style="background:rgba(56,189,248,0.15); color:var(--accent-cyan); border-color:rgba(56,189,248,0.3); font-size:10px; padding:2px 6px;">MoR Mandatory</span><br><span style="font-size:10px; color:var(--text-muted);">${escapeHTML(r.mor_engagement_type)}</span>`;
      } else {
        tdMor.innerHTML = `<span style="font-size:11px; color:var(--text-muted);">Standard Staffing</span>`;
      }

      const tdSpec = document.createElement("td");
      tdSpec.innerHTML = `<span class="mono" style="font-size:11px; color:var(--accent-emerald);">${escapeHTML(r.required_endorsement || "Core Rotations")}</span><br><span style="font-size:10px; color:var(--text-muted);">${escapeHTML(r.work_modality || "Any Modality")}</span>`;

      const tdLocal = document.createElement("td");
      tdLocal.className = "mono";
      tdLocal.textContent = r.target_local_id || "LOCAL-101";

      const tdAction = document.createElement("td");
      const btn = document.createElement("button");
      btn.className = "btn btn-primary btn-sm";
      btn.style.fontSize = "11px";
      btn.style.padding = "4px 8px";
      btn.textContent = "Evaluate in Console";
      btn.onclick = () => {
        this.loadRequisitionIntoConsole(r);
      };
      tdAction.appendChild(btn);

      tr.appendChild(tdId);
      tr.appendChild(tdEmp);
      tr.appendChild(tdTier);
      tr.appendChild(tdMor);
      tr.appendChild(tdSpec);
      tr.appendChild(tdLocal);
      tr.appendChild(tdAction);

      tbody.appendChild(tr);
    });
  }

  loadRequisitionIntoConsole(req) {
    if (typeof window.switchSubView === "function") {
      window.switchSubView("ws-dispatch", "sub-matcher");
    }

    const empSelect = document.getElementById("sim-req-employer");
    const tierSelect = document.getElementById("sim-req-tier");
    const morSelect = document.getElementById("sim-req-mor");
    const localSelect = document.getElementById("sim-req-local");
    const endorsementSelect = document.getElementById("sim-req-endorsement");
    const modalitySelect = document.getElementById("sim-req-modality");

    if (empSelect) empSelect.value = req.employer_pec_id;
    if (tierSelect) tierSelect.value = req.required_tier;
    if (morSelect) morSelect.value = req.requires_mor ? (req.mor_engagement_type || "Full-Time MoR") : "NONE";
    if (localSelect) localSelect.value = req.target_local_id || "ALL";
    if (endorsementSelect) endorsementSelect.value = req.required_endorsement || "ANY";
    if (modalitySelect) modalitySelect.value = req.work_modality || "Any Modality";

    this.simulateDispatch();
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

  simulateDispatch() {
    const employerSelect = document.getElementById("sim-req-employer");
    const tierSelect = document.getElementById("sim-req-tier");
    const morSelect = document.getElementById("sim-req-mor");
    const localSelect = document.getElementById("sim-req-local");
    const endorsementSelect = document.getElementById("sim-req-endorsement");
    const modalitySelect = document.getElementById("sim-req-modality");
    const resultBox = document.getElementById("sim-dispatch-result");

    if (!resultBox) return;

    const empName = employerSelect ? employerSelect.options[employerSelect.selectedIndex].text : "Sponsoring Enterprise";
    const tier = tierSelect ? tierSelect.value : "Licensed Journeyman";
    const morReq = morSelect ? morSelect.value : "NONE";
    const localReq = localSelect ? localSelect.value : "ALL";
    const end = endorsementSelect ? endorsementSelect.value : "ANY";
    const mod = modalitySelect ? modalitySelect.value : "Any Modality";

    const matchesTier = (practitionerTier, requestedTier) => {
      const pClean = practitionerTier.toLowerCase().trim();
      const rClean = requestedTier.toLowerCase().trim();
      for (const num of ["1", "2", "3", "4"]) {
        const marker = `tier ${num}`;
        if (rClean.includes(marker)) return pClean.includes(marker);
      }
      if (rClean.includes("journeyman")) {
        return pClean.includes("journeyman") && !pClean.includes("master");
      }
      if (rClean.includes("master")) {
        return pClean.includes("master");
      }
      return pClean.includes(rClean);
    };

    const candidates = (this.registryData.practitioners || [])
      .filter(p => p.is_seeking_placement)
      .filter(p => matchesTier(p.tier, tier))
      .filter(p => {
        if (morReq === "NONE") return true;
        if (!p.seeking_mor_role) return false;
        if (morReq === "Full-Time MoR") return p.mor_availability === "Full-Time MoR" || p.mor_availability === "Any";
        if (morReq === "Fractional MoR (vMoR)") return p.mor_availability === "Fractional MoR (vMoR)" || p.mor_availability === "Any";
        return true;
      })
      .filter(p => {
        if (localReq === "ALL") return true;
        return p.assigned_jatc_local === localReq || p.relocation_willingness === "National / Willing to Relocate";
      })
      .filter(p => end === "ANY" || (p.active_endorsements && p.active_endorsements.includes(end)))
      .filter(p => {
        if (mod === "Any Modality") return true;
        if (mod === "Remote") return p.work_modality_preference in { "Remote Only": 1, "Any Modality": 1 };
        if (mod === "Hybrid") return p.work_modality_preference in { "Hybrid": 1, "Any Modality": 1 };
        if (mod === "On-Site") return p.work_modality_preference in { "On-Site": 1, "Any Modality": 1, "Hybrid": 1 };
        return true;
      })
      .sort((a, b) => {
        const aSafe = (a.dispatch_book || "").includes("Priority Safe Harbor") ? 1 : 0;
        const bSafe = (b.dispatch_book || "").includes("Priority Safe Harbor") ? 1 : 0;
        if (aSafe !== bSafe) return bSafe - aSafe;
        return b.days_seeking_placement - a.days_seeking_placement;
      });

    resultBox.style.display = "block";

    if (candidates.length === 0) {
      resultBox.innerHTML = `<span style="color:var(--accent-rose); font-weight:700;">[NO CANDIDATE MATCHED IN LOCAL DISPATCH INVENTORY]</span>\n` +
        `The Talent Clearinghouse Dispatch Officer reviewed the Out-of-Work queue and determined:\n` +
        `• Required Tier:        ${tier}\n` +
        `• MoR Role Requirement: ${morReq}\n` +
        `• Specialty Endorsement:${end}\n` +
        `• Modality & Local:     ${mod} | ${localReq}\n\n` +
        `[DISPATCHER ACTION]: Labor requisition escalated to Multi-District Inter-Local Reciprocal Broadcast (Book 2 Regional Travelers).`;
      return;
    }

    const match = candidates[0];
    const agingAlert = match.days_seeking_placement >= 30
      ? `\n\n<span style="color:var(--accent-rose); font-weight:700;">[AGING QUEUE INTERVENTION TRIGGERED]</span> Candidate has waited ${match.days_seeking_placement} days on active books. Dispatch Officer prioritized contact to prevent training/career dormancy.`
      : "";

    const morNotice = morReq !== "NONE"
      ? `\nStatutory Role:         Designated Master of Record (${morReq})\nPillar VII Warranty:    Qualifies Sponsoring Enterprise for CUAAC Preferred Risk Warranty Rate`
      : "";

    resultBox.innerHTML = `<span style="color:var(--accent-emerald); font-weight:700;">[DISPATCH REFERRAL SLIP ISSUED &bull; CRAFT GUILD DISPATCH HALL]</span>\n` +
      `Dispatch Officer:       Desk Officer (JATC Local 101 Referral Desk)\n` +
      `Requisitioning Employer:${empName}\n` +
      `Dispatched Candidate #1:${match.name} (${match.trade_id})\n` +
      `Qualification Tier:     ${match.tier} (${match.total_verified_hours.toLocaleString()} verified hours)${morNotice}\n` +
      `Specialties:            ${match.active_endorsements.join(", ") || "Core Rotations"}\n` +
      `Home Local Chapter:     ${match.assigned_jatc_local}\n` +
      `Modality Preference:    ${match.work_modality_preference} (${match.relocation_willingness})\n` +
      `Seniority Standing:     ${match.days_seeking_placement} days on active queue (FIFO Rank #1 / ${candidates.length} qualified in pool)\n` +
      `Commercial Recruiter Fee:$0.00 (Protected under Multi-Employer Collective Bargaining Accord)${agingAlert}`;
  }


  async processBundleJson(bundle) {
    const resultBox = document.getElementById("bundle-result-card");
    const resultStatus = document.getElementById("bundle-result-status");
    const resultDetails = document.getElementById("bundle-result-details");
    const merkleChainBox = document.getElementById("merkle-chain-nodes");

    if (!resultBox || !bundle) return;

    resultBox.style.display = "block";
    merkleChainBox.textContent = "";

    const entries = bundle.entries || [];
    if (entries.length === 0) {
      resultStatus.textContent = "[FAIL] Submission Bundle contains 0 logbook entries.";
      resultStatus.style.color = "var(--accent-rose)";
      return;
    }

    let prevHash = null;
    const entryHashes = [];
    let totalHrs = 0;
    const domainHours = {};

    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const hrs = e.runtime_execution.hours_logged;
      totalHrs += hrs;
      const dom = e.runtime_execution.core_domain;
      domainHours[dom] = (domainHours[dom] || 0) + hrs;

      const art = (e.verification_artifacts && e.verification_artifacts[0]) ? e.verification_artifacts[0].artifact_reference : "NO_ARTIFACT";

      const h = await this.computeEntryHash(
        e.log_id,
        prevHash,
        e.practitioner.trade_id,
        e.runtime_execution.date,
        hrs,
        dom,
        art
      );
      entryHashes.push(h);

      const nodeEl = document.createElement("div");
      nodeEl.className = i === 0 ? "merkle-node genesis" : "merkle-node";

      const nodeHeader = document.createElement("div");
      nodeHeader.className = "node-header";

      const nodeTitle = document.createElement("span");
      nodeTitle.textContent = `Entry #${i + 1}: ${e.log_id} (${hrs}h in ${dom})`;

      const nodeDate = document.createElement("span");
      nodeDate.className = "node-hash";
      nodeDate.textContent = e.runtime_execution.date;

      nodeHeader.appendChild(nodeTitle);
      nodeHeader.appendChild(nodeDate);

      const nodeHashDiv = document.createElement("div");
      nodeHashDiv.className = "node-hash";
      nodeHashDiv.textContent = `Node SHA-256: ${h}`;

      nodeEl.appendChild(nodeHeader);
      nodeEl.appendChild(nodeHashDiv);
      merkleChainBox.appendChild(nodeEl);

      prevHash = h;
    }

    const computedRoot = await this.computeMerkleRoot(entryHashes);
    const declaredRoot = bundle.merkle_root_hash.startsWith("sha256:") ? bundle.merkle_root_hash.slice(7) : bundle.merkle_root_hash;
    const isMatch = computedRoot.toLowerCase() === declaredRoot.toLowerCase();

    if (isMatch) {
      resultStatus.textContent = "[PASS] Cryptographic Merkle Chain Integrity Verified (100% Match)";
      resultStatus.style.color = "var(--accent-emerald)";
    } else {
      resultStatus.textContent = "[FAIL] Merkle Root Discrepancy Detected!";
      resultStatus.style.color = "var(--accent-rose)";
    }

    resultDetails.textContent = `Practitioner: ${bundle.practitioner_name} (${bundle.practitioner_id})\n` +
      `Sponsoring Employer: Ellingson Mineral Corp (PEC-EMP-2026-0042)\n` +
      `Total Operational Runtime: ${totalHrs.toFixed(1)} hrs across ${entries.length} audited entries\n` +
      `Declared Root: sha256:${declaredRoot}\n` +
      `Computed Root: sha256:${computedRoot}\n` +
      `JATC Ingestion Status: ${isMatch ? "ACCREDITED FOR STATUTORY WAGE ELEVATION" : "REJECTED - HASH DISCREPANCY"}`;

    const wageSeal = document.getElementById("bundle-wage-seal");
    const sealTier = document.getElementById("bundle-seal-tier");
    const sealRate = document.getElementById("bundle-seal-rate");
    const sealHours = document.getElementById("bundle-seal-hours");
    const sealHash = document.getElementById("bundle-seal-hash");

    if (wageSeal) {
      if (isMatch) {
        wageSeal.style.display = "block";
        if (sealTier) sealTier.textContent = (bundle.current_tier || "DEVELOPING APPRENTICE (TIER 2)").toUpperCase();
        if (sealRate) sealRate.textContent = "60% RJPB STATUTORY WAGE FLOOR";
        if (sealHours) sealHours.textContent = `Total Verified Runtime: 2,480 Operational Hours (${totalHrs.toFixed(1)} hrs in this submission)`;
        if (sealHash) sealHash.textContent = `SEAL-ID: NCTB-SEAL-2480-${new Date().toISOString().slice(0,10)}`;
      } else {
        wageSeal.style.display = "none";
      }
    }
  }


  loadSampleBundle() {
    const sample = {
      "$schema": "https://cybertrade.org/schemas/v1/submission-bundle.json",
      "bundle_id": "BUNDLE-DADE-MURPHY-2026-Q3",
      "created_at": "2026-08-30T16:00:00Z",
      "practitioner_id": "CTP-APP-2026-0884",
      "practitioner_name": "Dade Murphy",
      "current_tier": "Tier 2 Apprentice",
      "merkle_root_hash": "",
      "entry_count": 3,
      "entries": [
        {
          "log_id": "LOG-2026-001",
          "practitioner": { "trade_id": "CTP-APP-2026-0884", "name": "Dade Murphy", "tier": "Tier 2 Apprentice" },
          "supervisor": { "trade_id": "CTP-JRN-2024-0192", "license_status": "Active", "supervision_ratio_compliant": true },
          "runtime_execution": { "date": "2026-08-25", "hours_logged": 6.0, "core_domain": "D1_PERIMETER_CLOUD" },
          "verification_artifacts": [{ "artifact_type": "git_commit_hash", "artifact_reference": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "sanitized_summary": "Terraform IAM policy hardening" }]
        },
        {
          "log_id": "LOG-2026-002",
          "practitioner": { "trade_id": "CTP-APP-2026-0884", "name": "Dade Murphy", "tier": "Tier 2 Apprentice" },
          "supervisor": { "trade_id": "CTP-JRN-2024-0192", "license_status": "Active", "supervision_ratio_compliant": true },
          "runtime_execution": { "date": "2026-08-26", "hours_logged": 7.5, "core_domain": "D2_DETECTION_SOC" },
          "verification_artifacts": [{ "artifact_type": "change_ticket_id", "artifact_reference": "CR-90412", "sanitized_summary": "Surge SOC incident triage" }]
        },
        {
          "log_id": "LOG-2026-003",
          "practitioner": { "trade_id": "CTP-APP-2026-0884", "name": "Dade Murphy", "tier": "Tier 2 Apprentice" },
          "supervisor": { "trade_id": "CTP-JRN-2024-0192", "license_status": "Active", "supervision_ratio_compliant": true },
          "runtime_execution": { "date": "2026-08-27", "hours_logged": 5.0, "core_domain": "D4_VULN_ATTACK" },
          "verification_artifacts": [{ "artifact_type": "vulnerability_id", "artifact_reference": "VULN-2026-8812", "sanitized_summary": "Verified remediation of unauthenticated API gateway flaw" }]
        }
      ]
    };

    (async () => {
      let prev = null;
      const hashes = [];
      for (const e of sample.entries) {
        const h = await this.computeEntryHash(e.log_id, prev, e.practitioner.trade_id, e.runtime_execution.date, e.runtime_execution.hours_logged, e.runtime_execution.core_domain, e.verification_artifacts[0].artifact_reference);
        hashes.push(h);
        prev = h;
      }
      sample.merkle_root_hash = await this.computeMerkleRoot(hashes);
      this.processBundleJson(sample);
    })();
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


