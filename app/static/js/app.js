// Presentation Content Builder AI - Frontend Application Controller

let currentDeck = null;
let currentSlideIndex = 0;
let documentsList = [];

// Initialize application on DOM load
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  fetchHealth();
  fetchDocuments();
  initDefaultDeck();
});

// Switch active navigation tab
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-tab").forEach(el => {
    el.classList.remove("active");
    el.classList.add("text-slate-400");
  });

  const activeContent = document.getElementById(`tab-${tabId}`);
  const activeBtn = document.getElementById(`tab-btn-${tabId}`);

  if (activeContent) activeContent.classList.remove("hidden");
  if (activeBtn) {
    activeBtn.classList.add("active");
    activeBtn.classList.remove("text-slate-400");
  }

  if (tabId === "knowledge") {
    fetchDocuments();
  }
}

function updateSlideCountLabel(val) {
  document.getElementById("num-slides-label").innerText = `${val} Slides`;
}

function toggleElement(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("hidden");
}

function showLoading(title, subtitle) {
  const overlay = document.getElementById("loading-overlay");
  document.getElementById("loading-title").innerText = title || "Processing...";
  document.getElementById("loading-subtitle").innerText = subtitle || "Please wait";
  overlay.classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loading-overlay").classList.add("hidden");
}

// Check vector store health
async function fetchHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const stats = data.vector_store;
    const chipText = document.getElementById("vector-status-text");
    if (chipText) {
      chipText.innerText = `ChromaDB (${stats.total_chunks} chunks, ${stats.total_documents} docs)`;
    }
  } catch (err) {
    console.error("Health check error:", err);
  }
}

// Fetch all ingested documents
async function fetchDocuments() {
  try {
    const res = await fetch("/api/documents");
    documentsList = await res.json();
    renderDocumentsTable(documentsList);
    
    // Update count badge
    const badge = document.getElementById("kb-badge-count");
    if (badge) badge.innerText = documentsList.length;
  } catch (err) {
    console.error("Fetch documents error:", err);
  }
}

function renderDocumentsTable(docs) {
  const tbody = document.getElementById("documents-table-body");
  if (!tbody) return;

  if (docs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500">
          No documents indexed yet. Upload a document above or click "Load Sample Knowledge Bases".
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = docs.map(doc => {
    const sizeKb = (doc.file_size_bytes / 1024).toFixed(1);
    return `
      <tr class="hover:bg-dark-850/50 transition">
        <td class="py-3 px-4 font-medium text-white flex items-center space-x-2">
          <i data-lucide="file-text" class="w-4 h-4 text-brand-400"></i>
          <span>${escapeHtml(doc.filename)}</span>
        </td>
        <td class="py-3 px-4 uppercase font-mono text-[10px] text-slate-400">${escapeHtml(doc.file_type)}</td>
        <td class="py-3 px-4 font-mono text-[11px] text-slate-400">${sizeKb} KB</td>
        <td class="py-3 px-4 font-mono text-brand-400 font-semibold">${doc.chunk_count}</td>
        <td class="py-3 px-4 font-mono text-slate-400">${doc.total_characters.toLocaleString()}</td>
        <td class="py-3 px-4 text-slate-500 text-[11px]">${doc.upload_timestamp}</td>
        <td class="py-3 px-4 text-right">
          <button onclick="deleteDocument('${doc.doc_id}')" class="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition" title="Delete Document">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

// Handle file selection and upload
async function handleFileSelect(files) {
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const chunkSize = document.getElementById("chunk-size-input").value || "800";
  const chunkOverlap = document.getElementById("chunk-overlap-input").value || "150";

  formData.append("chunk_size", chunkSize);
  formData.append("chunk_overlap", chunkOverlap);

  showLoading("Parsing & Indexing Documents...", "Extracting text, computing recursive chunks, and saving to ChromaDB");

  try {
    const res = await fetch("/api/documents/upload", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    alert(`Success: Ingested ${data.documents.length} document(s) with ${data.total_chunks_created} vector chunks!`);
    fetchDocuments();
    fetchHealth();
  } catch (err) {
    alert("Error uploading documents: " + err.message);
  } finally {
    hideLoading();
  }
}

// Delete document
async function deleteDocument(docId) {
  if (!confirm("Are you sure you want to delete this document from the vector store?")) return;

  try {
    const res = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
    if (res.ok) {
      fetchDocuments();
      fetchHealth();
    }
  } catch (err) {
    alert("Error deleting document: " + err.message);
  }
}

// Clear all knowledge base documents
async function clearAllKnowledge() {
  if (!confirm("Wipe all documents and vector embeddings from ChromaDB?")) return;

  try {
    const res = await fetch("/api/documents/clear", { method: "POST" });
    if (res.ok) {
      fetchDocuments();
      fetchHealth();
    }
  } catch (err) {
    alert("Error clearing knowledge base: " + err.message);
  }
}

// Load built-in sample documents
async function loadSampleDocuments() {
  showLoading("Loading Sample Knowledge Datasets...", "Ingesting AI Agent Architecture, Cloud Financial Report, and RAG Playbook");
  try {
    // Generate sample files on the fly and upload
    const samples = [
      {
        name: "Enterprise_Agentic_RAG_Architecture.txt",
        content: `ENTERPRISE AGENTIC RAG SYSTEM ARCHITECTURE
Author: DeepMind / Google Antigravity Architecture Team
Version: 2.4 - Production Specification

1. EXECUTIVE SUMMARY & PROBLEM STATEMENT
Traditional Retrieval-Augmented Generation (RAG) suffers from static single-turn retrieval failures, context fragmentation, and low semantic density. Modern enterprise knowledge environments require Agentic RAG: autonomous query decomposition, recursive multi-hop vector retrieval, and structured JSON synthesis.
Key business outcomes:
- 78% reduction in presentation and report synthesis latency across executive strategy teams.
- 99.4% factual verification grounding against primary documentation.
- Elimination of hallucinated metrics through citation-bounded generation.

2. CORE ARCHITECTURAL PILLARS
Pillar 1: Multi-Format Document Ingestion & Recursive Chunking
The ingestion pipeline leverages PDF layout parsers (pdfplumber, PyPDF2) and docx structural extractors. Context is chunked using recursive character boundaries with semantic heading preservation (default: 800 characters, 150 character overlap). Every chunk carries source page, document ID, and section lineage.

Pillar 2: Semantic Vector Storage & Low-Latency Retrieval
Vector indexing is handled by ChromaDB using HuggingFace all-MiniLM-L6-v2 embeddings (384-dimensional cosine similarity space) or OpenAI text-embedding-3-small. Multi-query expansion retrieves context from diverse thematic angles: Context, Problem Mechanics, Core Pillars, Impact Metrics, and Future Roadmap.

Pillar 3: Adaptive LLM Orchestration & Structured JSON Synthesis
The orchestration engine binds retrieved chunks into a strict SlideDeck JSON contract. It enforces action-oriented titles, distinct core takeaways, dense quantitative bullets, visual layout suggestions (e.g. split_2_column, 3_pillar_cards, kpi_highlight), and comprehensive speaker delivery notes.

3. MEASURABLE PERFORMANCE & BENCHMARKS
- Retrieval Latency: Sub-45ms average vector search latency for top-5 chunks.
- Export Fidelity: 100% programmatic PowerPoint (python-pptx) generation in 16:9 widescreen format.
- Cross-Functional Adoption: Deployed across engineering, finance, and product strategy teams.`
      },
      {
        name: "Q3_Cloud_Financial_Performance.md",
        content: `# Q3 ENTERPRISE CLOUD FINANCIAL & OPERATIONAL REPORT
Reporting Period: Q3 FY2026 | Prepared by: Strategic Finance & Operations

## 1. FINANCIAL HIGHLIGHTS & REVENUE EXPANSION
- Total Cloud Solutions Revenue reached $4.82 Billion, representing a 28.4% year-over-year increase.
- Gross Margin expanded by 340 basis points to 71.2%, driven by infrastructure optimization and intelligent workload scheduling.
- Annual Recurring Revenue (ARR) surpassed $18.5 Billion with net revenue retention at 124%.

## 2. CAPITAL ALLOCATION & INFRASTRUCTURE INVESTMENT
- Invested $1.2 Billion in next-generation AI accelerator infrastructure and vector retrieval pipelines.
- Energy efficiency initiatives reduced data center power utilization effectiveness (PUE) to 1.14, outperforming industry averages.
- Free cash flow generated in Q3 stood at $1.45 Billion, up 31% year-over-year.

## 3. STRATEGIC PRIORITIES FOR Q4 & FY2027
1. Enterprise AI Integration: Scale automated presentation content generation and real-time knowledge synthesis across 50,000 corporate seats.
2. Global Sovereign Cloud Expansion: Launch localized compliance clusters across EMEA and APAC.
3. Cost Governance: Implement automated tiering for cold vector archives, targeting an additional $85M in annual operational savings.`
      }
    ];

    const formData = new FormData();
    for (const sample of samples) {
      const blob = new Blob([sample.content], { type: "text/plain" });
      formData.append("files", blob, sample.name);
    }
    formData.append("chunk_size", "800");
    formData.append("chunk_overlap", "150");

    const res = await fetch("/api/documents/upload", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      alert("Sample datasets successfully indexed into ChromaDB!");
      fetchDocuments();
      fetchHealth();
    } else {
      throw new Error("Failed to upload samples");
    }
  } catch (err) {
    alert("Error loading samples: " + err.message);
  } finally {
    hideLoading();
  }
}

// Preset sample topics
function applySampleTopic(type) {
  const topicInput = document.getElementById("gen-topic");
  const audienceSelect = document.getElementById("gen-audience");
  const toneSelect = document.getElementById("gen-tone");

  if (type === "ai_rag") {
    topicInput.value = "Enterprise Agentic RAG Architecture & Presentation Synthesis";
    audienceSelect.value = "Technical Architects & Engineers";
    toneSelect.value = "Technical";
  } else if (type === "cloud_q3") {
    topicInput.value = "Q3 Cloud Financial Growth & Strategic Capital Allocation";
    audienceSelect.value = "Executive Leadership & Board";
    toneSelect.value = "Executive";
  } else if (type === "ai_governance") {
    topicInput.value = "Enterprise AI Governance, Security & Knowledge Integrity";
    audienceSelect.value = "Product Managers & Business Stakeholders";
    toneSelect.value = "Executive";
  }
}

// Generate Slide Deck via RAG Engine
async function triggerGenerateDeck() {
  const topic = document.getElementById("gen-topic").value.trim();
  if (!topic) {
    alert("Please enter a presentation topic.");
    return;
  }

  const audience = document.getElementById("gen-audience").value;
  const numSlides = parseInt(document.getElementById("gen-num-slides").value, 10);
  const tone = document.getElementById("gen-tone").value;
  const provider = document.getElementById("gen-provider").value;
  const customInstructions = document.getElementById("gen-custom-instructions").value.trim();

  showLoading("Synthesizing Presentation Deck...", "Performing multi-aspect vector retrieval and structuring slides");

  try {
    const payload = {
      topic: topic,
      target_audience: audience,
      num_slides: numSlides,
      deck_tone: tone,
      llm_provider: provider,
      custom_instructions: customInstructions || null
    };

    const res = await fetch("/api/generate-deck", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Generation failed");
    }

    currentDeck = await res.json();
    currentSlideIndex = 0;
    renderDeck();
  } catch (err) {
    alert("Error generating slide deck: " + err.message);
  } finally {
    hideLoading();
  }
}

// Render the active deck
function renderDeck() {
  if (!currentDeck || !currentDeck.slides || currentDeck.slides.length === 0) return;

  // Update header titles
  document.getElementById("deck-display-title").innerText = currentDeck.deck_title;
  document.getElementById("deck-display-subtitle").innerText = `Target Audience: ${currentDeck.target_audience}`;

  // Render thumbnails
  renderThumbnails();

  // Render active slide
  renderActiveSlide();

  // Render indicator dots
  renderDots();
}

function renderThumbnails() {
  const container = document.getElementById("thumbnails-container");
  if (!container) return;

  container.innerHTML = currentDeck.slides.map((slide, idx) => {
    const isActive = idx === currentSlideIndex;
    return `
      <div onclick="goToSlide(${idx})" class="thumb-card ${isActive ? 'active' : ''} p-2.5 rounded-xl bg-dark-900 border border-slate-800 hover:border-slate-700 cursor-pointer transition">
        <div class="flex items-center justify-between text-[10px] font-mono mb-1">
          <span class="text-brand-400 font-bold">#${slide.slide_number}</span>
          <span class="text-slate-500 uppercase">${escapeHtml(slide.visual_layout_suggestion || 'standard')}</span>
        </div>
        <p class="text-xs font-semibold text-slate-200 line-clamp-1">${escapeHtml(slide.title)}</p>
        <p class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${escapeHtml(slide.core_takeaway)}</p>
      </div>
    `;
  }).join("");
}

function renderActiveSlide() {
  if (!currentDeck || !currentDeck.slides[currentSlideIndex]) return;

  const slide = currentDeck.slides[currentSlideIndex];
  const total = currentDeck.slides.length;

  document.getElementById("slide-indicator").innerText = `${currentSlideIndex + 1} of ${total}`;
  document.getElementById("slide-number-pill").innerText = `SLIDE ${String(slide.slide_number).padStart(2, '0')}`;
  document.getElementById("slide-layout-pill").innerText = (slide.visual_layout_suggestion || "STANDARD").toUpperCase().replace('_', ' ');

  // Update title & takeaway
  document.getElementById("slide-canvas-title").innerText = slide.title;
  document.getElementById("slide-canvas-takeaway").innerText = slide.core_takeaway;

  // Bullets
  const bulletsContainer = document.getElementById("slide-canvas-bullets");
  bulletsContainer.innerHTML = (slide.bullet_points || []).map((bullet, bIdx) => `
    <div class="flex items-start space-x-2.5 group">
      <div class="w-5 h-5 rounded-md bg-brand-500/10 text-brand-400 border border-brand-500/20 flex items-center justify-center text-[10px] font-bold font-mono shrink-0 mt-0.5">
        0${bIdx + 1}
      </div>
      <p contenteditable="true" onblur="updateCurrentSlideBullet(${bIdx}, this.innerText)"
         class="text-xs sm:text-sm text-slate-300 outline-none hover:bg-white/5 rounded px-1.5 py-0.5 flex-1 transition">
        ${escapeHtml(bullet)}
      </p>
    </div>
  `).join("");

  // Sources
  const sourcesContainer = document.getElementById("slide-canvas-sources");
  const sources = slide.retrieved_sources && slide.retrieved_sources.length > 0
    ? slide.retrieved_sources
    : ["Internal Knowledge Base"];

  sourcesContainer.innerHTML = sources.map(s => `
    <span class="px-2 py-0.5 rounded-full bg-dark-800 border border-slate-700/80 text-[10px] text-slate-300 font-mono">
      ${escapeHtml(s)}
    </span>
  `).join("");

  // Speaker notes
  document.getElementById("slide-canvas-notes").value = slide.speaker_notes || "";

  renderThumbnails();
  renderDots();
}

function renderDots() {
  const container = document.getElementById("slide-dots");
  if (!container || !currentDeck) return;

  container.innerHTML = currentDeck.slides.map((_, idx) => `
    <button onclick="goToSlide(${idx})" class="w-2 h-2 rounded-full transition ${idx === currentSlideIndex ? 'bg-brand-500 scale-125' : 'bg-slate-700 hover:bg-slate-500'}"></button>
  `).join("");
}

function goToSlide(idx) {
  if (!currentDeck || idx < 0 || idx >= currentDeck.slides.length) return;
  currentSlideIndex = idx;
  renderActiveSlide();
}

function nextSlide() {
  if (!currentDeck) return;
  if (currentSlideIndex < currentDeck.slides.length - 1) {
    currentSlideIndex++;
    renderActiveSlide();
  }
}

function prevSlide() {
  if (!currentDeck) return;
  if (currentSlideIndex > 0) {
    currentSlideIndex--;
    renderActiveSlide();
  }
}

// Inline editing updates to state
function updateCurrentSlideTitle(newText) {
  if (currentDeck && currentDeck.slides[currentSlideIndex]) {
    currentDeck.slides[currentSlideIndex].title = newText.trim();
    renderThumbnails();
  }
}

function updateCurrentSlideTakeaway(newText) {
  if (currentDeck && currentDeck.slides[currentSlideIndex]) {
    currentDeck.slides[currentSlideIndex].core_takeaway = newText.trim();
    renderThumbnails();
  }
}

function updateCurrentSlideBullet(bIdx, newText) {
  if (currentDeck && currentDeck.slides[currentSlideIndex]) {
    currentDeck.slides[currentSlideIndex].bullet_points[bIdx] = newText.trim();
  }
}

function updateCurrentSlideNotes(newText) {
  if (currentDeck && currentDeck.slides[currentSlideIndex]) {
    currentDeck.slides[currentSlideIndex].speaker_notes = newText.trim();
  }
}

// Download PPTX
async function downloadPPTX() {
  if (!currentDeck) {
    alert("Please generate a presentation deck first.");
    return;
  }

  const theme = document.getElementById("gen-theme").value || "modern_indigo";

  showLoading("Generating PowerPoint File...", "Rendering slides, styled shapes, and speaker notes with python-pptx");

  try {
    const res = await fetch("/api/export-pptx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        deck: currentDeck,
        theme: theme
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "PPTX export failed");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const safeTitle = (currentDeck.deck_title || "Presentation").replace(/[^a-zA-Z0-9_\-]/g, "_").slice(0, 30);
    a.download = `${safeTitle}.pptx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Error downloading presentation: " + err.message);
  } finally {
    hideLoading();
  }
}

// Download JSON
function downloadJSON() {
  if (!currentDeck) return;
  const str = JSON.stringify(currentDeck, null, 2);
  const blob = new Blob([str], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const safeTitle = (currentDeck.deck_title || "Deck").replace(/[^a-zA-Z0-9_\-]/g, "_");
  a.download = `${safeTitle}_schema.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

// Schema Modal
function openRawJSONModal() {
  if (!currentDeck) return;
  const codeEl = document.getElementById("raw-json-code");
  codeEl.innerText = JSON.stringify(currentDeck, null, 2);
  document.getElementById("raw-json-modal").classList.remove("hidden");
}

function closeRawJSONModal() {
  document.getElementById("raw-json-modal").classList.add("hidden");
}

function copyRawJSON() {
  const codeText = document.getElementById("raw-json-code").innerText;
  navigator.clipboard.writeText(codeText).then(() => {
    const btnText = document.getElementById("copy-json-btn-text");
    btnText.innerText = "Copied!";
    setTimeout(() => { btnText.innerText = "Copy JSON"; }, 2000);
  });
}

// Semantic Search Explorer
async function triggerSearch() {
  const query = document.getElementById("search-query-input").value.trim();
  if (!query) return;

  const topK = parseInt(document.getElementById("search-top-k").value, 10);
  const container = document.getElementById("search-results-container");
  container.innerHTML = `<div class="p-6 text-center text-slate-500">Searching ChromaDB vector store...</div>`;

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, top_k: topK })
    });

    const data = await res.json();
    if (!data.results || data.results.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-slate-500">No matching chunks found. Upload more documents to the knowledge base.</div>`;
      return;
    }

    container.innerHTML = data.results.map((r, idx) => {
      const pct = Math.round(r.similarity_score * 100);
      return `
        <div class="p-4 rounded-xl bg-dark-950 border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-xs">
            <div class="flex items-center space-x-2">
              <span class="w-6 h-6 rounded-md bg-brand-500/10 text-brand-400 font-mono font-bold flex items-center justify-center text-[10px]">#${idx + 1}</span>
              <span class="font-semibold text-slate-200">${escapeHtml(r.source_filename)}</span>
              <span class="text-[10px] text-slate-500 font-mono">Page ${r.page_number} • Chunk ${r.chunk_index}</span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-[11px] font-mono text-emerald-400 font-semibold">${pct}% Match</span>
              <div class="w-16 h-1.5 bg-dark-800 rounded-full overflow-hidden">
                <div class="h-full bg-emerald-500 rounded-full" style="width: ${pct}%"></div>
              </div>
            </div>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed font-sans bg-dark-900/60 p-3 rounded-lg border border-slate-800/60">
            ${escapeHtml(r.content)}
          </p>
        </div>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    container.innerHTML = `<div class="p-6 text-center text-red-400">Search error: ${err.message}</div>`;
  }
}

// Initial demonstration deck
function initDefaultDeck() {
  currentDeck = {
    deck_title: "Enterprise Agentic RAG Architecture & Presentation Synthesis",
    target_audience: "Technical Architects & Enterprise Leaders",
    slides: [
      {
        slide_number: 1,
        title: "Enterprise Agentic RAG Architecture: Strategic Blueprint",
        core_takeaway: "An evidence-backed framework transitioning legacy vector search into dynamic, multi-agent presentation synthesis.",
        bullet_points: [
          "Eliminates single-turn context fragmentation through recursive semantic document chunking.",
          "Synthesizes verified knowledge base citations into structured, presentation-ready JSON schemas.",
          "Delivers end-to-end programmatic 16:9 widescreen PowerPoint generation via python-pptx."
        ],
        visual_layout_suggestion: "title_hero",
        speaker_notes: "Welcome team. Today we explore our production RAG presentation engine. Our core takeaway is that grounding LLM orchestration with semantic chunking provides unprecedented accuracy and automated slide generation.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 1)"]
      },
      {
        slide_number: 2,
        title: "Strategic Context & Critical Challenges in Legacy RAG",
        core_takeaway: "Standard vector retrieval lacks multi-aspect decomposition and reliable output schema enforcement.",
        bullet_points: [
          "Legacy pipelines fail to structure complex information into high-density slide takeaways.",
          "Manual slide assembly consumes over 12 hours per executive deck across strategy teams.",
          "Unverified generative output introduces brand risk and ungrounded factual hallucinations."
        ],
        visual_layout_suggestion: "split_2_column",
        speaker_notes: "On this slide, highlight the productivity bottleneck facing cross-functional teams today. Notice how our split layout isolates the core takeaway on the left while contrasting operational pain points on the right.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 1)"]
      },
      {
        slide_number: 3,
        title: "Core Architectural & Operational Pillars",
        core_takeaway: "Three tightly integrated subsystems guarantee latency, accuracy, and presentation-ready deliverables.",
        bullet_points: [
          "Pillar 1: Multi-format parsing (PDF, DOCX, MD) with recursive character text splitters.",
          "Pillar 2: ChromaDB persistent vector storage powered by all-MiniLM-L6-v2 embeddings.",
          "Pillar 3: LLM function calling and Pydantic validation enforcing the SlideDeck JSON contract."
        ],
        visual_layout_suggestion: "3_pillar_cards",
        speaker_notes: "Walk the architecture committee through the three pillars. Emphasize that our storage layer persists locally on disk while our schema validation guarantees zero malformed decks.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 2)"]
      },
      {
        slide_number: 4,
        title: "Measurable Impact & Quantifiable Performance Metrics",
        core_takeaway: "Directly correlates semantic vector retrieval with accelerated time-to-decision and verified ROI.",
        bullet_points: [
          "78% reduction in presentation generation latency across enterprise strategy teams.",
          "99.4% factual verification grounding against ingested source documentation.",
          "Sub-45ms average vector search query latency across ChromaDB collections."
        ],
        visual_layout_suggestion: "kpi_highlight",
        speaker_notes: "Review these verified benchmarks with executive leadership. The 78% latency reduction is our headline metric, unlocked by our optimized indexing pipeline.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 3)"]
      },
      {
        slide_number: 5,
        title: "Phased Execution & Implementation Roadmap",
        core_takeaway: "Structured rollout roadmap designed to drive enterprise adoption across three operational phases.",
        bullet_points: [
          "Phase 1: Knowledge ingestion & ChromaDB collection configuration.",
          "Phase 2: LLM orchestration integration & custom presenter prompt tuning.",
          "Phase 3: Automated PowerPoint styling and template customization rollout."
        ],
        visual_layout_suggestion: "timeline_flow",
        speaker_notes: "Conclude our sequence by stepping through the implementation roadmap. Each milestone is verified with automated test suites before general availability.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 3)"]
      },
      {
        slide_number: 6,
        title: "Key Recommendations & Strategic Next Steps",
        core_takeaway: "Institutionalize automated presentation synthesis as the enterprise standard for data-driven decks.",
        bullet_points: [
          "Integrate company-wide knowledge repositories into persistent ChromaDB stores.",
          "Standardize team presentations on the modern 16:9 widescreen theme palette.",
          "Incorporate presenter notes into all executive briefing packages automatically."
        ],
        visual_layout_suggestion: "bullet_list",
        speaker_notes: "Provide the team with clear, actionable next steps. Emphasize that all generated presentations can be exported to .pptx or modified directly in this studio.",
        retrieved_sources: ["Enterprise_Agentic_RAG_Architecture.txt (p. 3)"]
      }
    ]
  };

  currentSlideIndex = 0;
  renderDeck();
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

