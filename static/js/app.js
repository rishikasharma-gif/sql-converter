// Frontend JavaScript controller for SAP XML to BigQuery SQL Converter Agent
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const sampleList = document.getElementById("sample-list");
  const fileInput = document.getElementById("file-input");
  const uploadZone = document.getElementById("upload-zone");
  const loaderOverlay = document.getElementById("loader-overlay");
  const loaderStatus = document.getElementById("loader-status");
  
  const activeFileName = document.getElementById("active-file-name");
  const copyBtn = document.getElementById("copy-btn");
  const downloadBtn = document.getElementById("download-btn");
  
  const tabSql = document.getElementById("tab-sql");
  const tabXml = document.getElementById("tab-xml");
  const codeContent = document.getElementById("code-content");
  
  const complianceScore = document.getElementById("compliance-score");
  const fillRing = document.querySelector(".fill-ring");
  const complianceStatus = document.getElementById("compliance-status");
  const validationFieldsCount = document.getElementById("validation-fields-count");
  
  const validationNotesList = document.getElementById("validation-notes-list");
  const fieldsTableBody = document.getElementById("fields-table-body");
  
  // App state
  let currentConversionData = null;
  let currentActiveTab = "sql"; // 'sql' or 'xml'
  
  // Initialize
  loadSamples();
  setupEventListeners();
  
  // Load Sample Files
  async function loadSamples() {
    try {
      const response = await fetch("/api/samples");
      const samples = await response.json();
      
      if (samples.length === 0) {
        sampleList.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-secondary); text-align: center;">No sample XML files found in data/ folder.</p>';
        return;
      }
      
      sampleList.innerHTML = "";
      samples.forEach(sample => {
        const item = document.createElement("div");
        item.className = "sample-item";
        item.innerHTML = `
          <div class="sample-info">
            <h4>${sample.name}</h4>
            <p>${sample.size_kb} KB</p>
          </div>
          <span class="sample-tag">${sample.type}</span>
        `;
        item.addEventListener("click", () => triggerConversion({ sample_name: sample.name }));
        sampleList.appendChild(item);
      });
    } catch (error) {
      console.error("Failed to load samples:", error);
    }
  }
  
  // Setup Event Listeners
  function setupEventListeners() {
    // File Upload Click and Drag-Drop
    uploadZone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        triggerConversion({ file: e.target.files[0] });
      }
    });
    
    uploadZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadZone.style.borderColor = "var(--accent-pink)";
      uploadZone.style.background = "rgba(217, 70, 239, 0.05)";
    });
    
    uploadZone.addEventListener("dragleave", () => {
      uploadZone.style.borderColor = "rgba(139, 92, 246, 0.3)";
      uploadZone.style.background = "rgba(139, 92, 246, 0.02)";
    });
    
    uploadZone.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadZone.style.borderColor = "rgba(139, 92, 246, 0.3)";
      uploadZone.style.background = "rgba(139, 92, 246, 0.02)";
      
      if (e.dataTransfer.files.length > 0) {
        triggerConversion({ file: e.dataTransfer.files[0] });
      }
    });
    
    // Tabs Control
    tabSql.addEventListener("click", () => {
      if (currentConversionData) switchTab("sql");
    });
    tabXml.addEventListener("click", () => {
      if (currentConversionData) switchTab("xml");
    });
    
    // Copy/Download Controls
    copyBtn.addEventListener("click", copySqlToClipboard);
    downloadBtn.addEventListener("click", downloadSqlFile);
  }
  
  // Core Conversion Trigger
  async function triggerConversion({ file = null, sample_name = null }) {
    // Reset indicators
    loaderStatus.innerText = "Analyzing SAP XML Schema Structure...";
    loaderOverlay.classList.add("active");
    
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
      activeFileName.innerHTML = `Active File: <span>${file.name}</span>`;
    } else if (sample_name) {
      formData.append("sample_name", sample_name);
      activeFileName.innerHTML = `Active File: <span>${sample_name}</span>`;
    }
    
    try {
      // Simulate phases on loader status text
      setTimeout(() => {
        if (loaderOverlay.classList.contains("active")) {
          loaderStatus.innerText = "Connecting to Gemini translation model...";
        }
      }, 1500);
      
      setTimeout(() => {
        if (loaderOverlay.classList.contains("active")) {
          loaderStatus.innerText = "Synthesizing optimized BigQuery SQL (No Data Loss Mode)...";
        }
      }, 3500);
      
      const response = await fetch("/api/convert", {
        method: "POST",
        body: formData
      });
      
      const result = await response.json();
      
      if (!response.ok || !result.success) {
        throw new Error(result.error || "An error occurred during conversion");
      }
      
      currentConversionData = result;
      renderConversionResult();
      
    } catch (error) {
      alert("Conversion Error: " + error.message);
      activeFileName.innerHTML = '<span style="color: var(--danger-red);">Conversion failed</span>';
    } finally {
      loaderOverlay.classList.remove("active");
    }
  }
  
  // Render Result Panels
  function renderConversionResult() {
    if (!currentConversionData) return;
    
    // Enable controls
    copyBtn.removeAttribute("disabled");
    downloadBtn.removeAttribute("disabled");
    
    // Set tab values and switch to SQL
    switchTab("sql");
    
    // 1. Compliance Score Meter
    const report = currentConversionData.validation_report;
    const coverage = report.coverage;
    
    complianceScore.innerText = `${coverage}%`;
    complianceStatus.innerText = report.status === "PASSED" ? "Fully Compliant" : "Validation Warnings";
    complianceStatus.style.color = report.status === "PASSED" ? "var(--success-green)" : "var(--warning-amber)";
    validationFieldsCount.innerText = `${report.matched_fields} of ${report.total_xml_fields} fields matched`;
    
    // Animate circular meter ring
    // Total circumference for r=65 is 2 * pi * r = 408.4
    const offset = 408 - (408 * coverage) / 100;
    fillRing.style.strokeDashoffset = offset;
    
    // 2. Validation Notes
    validationNotesList.innerHTML = "";
    if (currentConversionData.validation_notes && currentConversionData.validation_notes.length > 0) {
      currentConversionData.validation_notes.forEach(note => {
        const item = document.createElement("div");
        item.className = "note-item";
        item.innerText = note;
        validationNotesList.appendChild(item);
      });
    } else {
      validationNotesList.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-secondary);">No special translation notes generated.</p>';
    }
    
    // 3. Field Compliance Checklist Table
    fieldsTableBody.innerHTML = "";
    if (report.results && report.results.length > 0) {
      report.results.forEach(res => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td style="font-weight: 500;">${res.xml_field}</td>
          <td style="color: var(--text-secondary);">${res.label}</td>
          <td>
            <span class="badge ${res.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}">
              ${res.status}
            </span>
          </td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${res.notes}</td>
        `;
        fieldsTableBody.appendChild(row);
      });
    } else {
      fieldsTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No fields analyzed.</td></tr>';
    }
  }
  
  // Tab Switcher
  function switchTab(tab) {
    currentActiveTab = tab;
    
    tabSql.classList.toggle("active", tab === "sql");
    tabXml.classList.toggle("active", tab === "xml");
    
    if (!currentConversionData) return;
    
    if (tab === "sql") {
      // Escape HTML in SQL to prevent script injection in representation
      const escapedSql = currentConversionData.sql
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      codeContent.innerHTML = `<pre><code class="language-sql">${escapedSql}</code></pre>`;
    } else {
      // Render beautiful JSON formatted metadata in place of raw massive XML for easier reading
      const metaJson = JSON.stringify(currentConversionData.metadata, null, 2);
      codeContent.innerHTML = `<pre><code class="language-json">${metaJson}</code></pre>`;
    }
  }
  
  // Actions
  function copySqlToClipboard() {
    if (!currentConversionData || !currentConversionData.sql) return;
    
    navigator.clipboard.writeText(currentConversionData.sql).then(() => {
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = '📋 Copied!';
      copyBtn.style.color = "var(--success-green)";
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
        copyBtn.style.color = "";
      }, 2000);
    }).catch(err => {
      alert("Failed to copy: " + err);
    });
  }
  
  function downloadSqlFile() {
    if (!currentConversionData || !currentConversionData.sql) return;
    
    const element = document.createElement("a");
    const file = new Blob([currentConversionData.sql], {type: "text/plain"});
    element.href = URL.createObjectURL(file);
    
    // Derive name
    let name = currentConversionData.filename.replace(".xml", "") + "_optimized.sql";
    element.download = name;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
});
