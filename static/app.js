/**
 * GATE CSE Screenshot Organizer Frontend Client
 * Handles clipboard paste events, image previews, subject classification, and gallery views.
 */

// Application State
const state = {
  activeTab: 'capture',
  subjects: [],
  baseDir: '~/gate_cse_notes',
  currentScreenshot: null, // { base64, width, height, analysis }
  selectedGallerySubject: '',
  searchQuery: '',
  autoSave: localStorage.getItem('gate_auto_save') === 'true',
  activeModalItem: null
};

// DOM Elements
const elements = {
  tabCapture: document.getElementById('tabCapture'),
  tabExplorer: document.getElementById('tabExplorer'),
  tabStats: document.getElementById('tabStats'),
  sectionCapture: document.getElementById('sectionCapture'),
  sectionExplorer: document.getElementById('sectionExplorer'),
  sectionStats: document.getElementById('sectionStats'),

  pasteZone: document.getElementById('pasteZone'),
  fileInput: document.getElementById('fileInput'),
  btnBrowseFile: document.getElementById('btnBrowseFile'),
  btnPasteClipboard: document.getElementById('btnPasteClipboard'),
  autoSaveToggle: document.getElementById('autoSaveToggle'),

  processingCard: document.getElementById('processingCard'),
  reviewCard: document.getElementById('reviewCard'),
  previewImg: document.getElementById('previewImg'),
  imgDimensions: document.getElementById('imgDimensions'),
  btnDiscard: document.getElementById('btnDiscard'),
  btnCancelCapture: document.getElementById('btnCancelCapture'),
  btnSaveScreenshot: document.getElementById('btnSaveScreenshot'),

  subjectCodePill: document.getElementById('subjectCodePill'),
  detectedSubjectName: document.getElementById('detectedSubjectName'),
  detectedSubtopic: document.getElementById('detectedSubtopic'),
  confidenceScore: document.getElementById('confidenceScore'),
  targetFolderPath: document.getElementById('targetFolderPath'),
  subjectSelect: document.getElementById('subjectSelect'),
  keywordsChips: document.getElementById('keywordsChips'),
  inputSubtopic: document.getElementById('inputSubtopic'),
  inputTags: document.getElementById('inputTags'),
  inputNotes: document.getElementById('inputNotes'),
  ocrTextView: document.getElementById('ocrTextView'),
  aiBadge: document.getElementById('aiBadge'),

  storagePathBadge: document.getElementById('storagePathBadge'),
  btnOpenFolder: document.getElementById('btnOpenFolder'),
  totalScreenshotsCount: document.getElementById('totalScreenshotsCount'),
  recentGrid: document.getElementById('recentGrid'),

  searchNotesInput: document.getElementById('searchNotesInput'),
  filterSubjectSelect: document.getElementById('filterSubjectSelect'),
  btnRefreshExplorer: document.getElementById('btnRefreshExplorer'),
  subjectCardsGrid: document.getElementById('subjectCardsGrid'),
  galleryGrid: document.getElementById('galleryGrid'),
  galleryTitle: document.getElementById('galleryTitle'),
  gallerySubtitle: document.getElementById('gallerySubtitle'),
  galleryCountBadge: document.getElementById('galleryCountBadge'),
  galleryEmptyState: document.getElementById('galleryEmptyState'),

  statsBarsContainer: document.getElementById('statsBarsContainer'),

  // Modal
  lightboxModal: document.getElementById('lightboxModal'),
  modalImg: document.getElementById('modalImg'),
  modalTitle: document.getElementById('modalTitle'),
  modalSubjectPill: document.getElementById('modalSubjectPill'),
  modalSubjectName: document.getElementById('modalSubjectName'),
  modalSubtopic: document.getElementById('modalSubtopic'),
  modalDate: document.getElementById('modalDate'),
  modalOcrText: document.getElementById('modalOcrText'),
  modalMoveSelect: document.getElementById('modalMoveSelect'),
  btnModalMoveConfirm: document.getElementById('btnModalMoveConfirm'),
  btnCopyOcr: document.getElementById('btnCopyOcr'),
  modalBtnClose: document.getElementById('modalBtnClose'),
  modalBtnDownload: document.getElementById('modalBtnDownload'),
  modalBtnDelete: document.getElementById('modalBtnDelete'),

  // Settings
  btnSettings: document.getElementById('btnSettings'),
  settingsModal: document.getElementById('settingsModal'),
  btnCloseSettings: document.getElementById('btnCloseSettings'),
  settingBaseDir: document.getElementById('settingBaseDir'),
  settingGeminiKey: document.getElementById('settingGeminiKey'),
  geminiKeyStatus: document.getElementById('geminiKeyStatus'),
  btnSaveSettings: document.getElementById('btnSaveSettings'),

  toast: document.getElementById('toast'),
  toastMsg: document.getElementById('toastMsg'),
  toastIcon: document.getElementById('toastIcon')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  initIcons();
  setupEventListeners();
  elements.autoSaveToggle.checked = state.autoSave;
  await fetchSettings();
  await loadSubjects();
  await loadRecentScreenshots();
});

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// Event Listeners setup
function setupEventListeners() {
  // Navigation Tabs
  elements.tabCapture.addEventListener('click', () => switchTab('capture'));
  elements.tabExplorer.addEventListener('click', () => switchTab('explorer'));
  elements.tabStats.addEventListener('click', () => switchTab('stats'));

  // Global Paste Listener (Ctrl+V anywhere on window!)
  window.addEventListener('paste', handleGlobalPaste);

  // Drag and drop on Paste Zone
  elements.pasteZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.pasteZone.classList.add('paste-active');
  });
  elements.pasteZone.addEventListener('dragleave', () => {
    elements.pasteZone.classList.remove('paste-active');
  });
  elements.pasteZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.pasteZone.classList.remove('paste-active');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleImageFile(e.dataTransfer.files[0]);
    }
  });

  // Click on Paste Zone or buttons
  elements.pasteZone.addEventListener('click', (e) => {
    if (e.target.closest('#btnPasteClipboard') || e.target.closest('#btnBrowseFile')) return;
    elements.fileInput.click();
  });
  elements.btnBrowseFile.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.fileInput.click();
  });
  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleImageFile(e.target.files[0]);
    }
  });

  // Clipboard button (Navigator API)
  elements.btnPasteClipboard.addEventListener('click', async (e) => {
    e.stopPropagation();
    try {
      const clipboardItems = await navigator.clipboard.read();
      for (const item of clipboardItems) {
        for (const type of item.types) {
          if (type.startsWith('image/')) {
            const blob = await item.getType(type);
            handleImageFile(blob);
            return;
          }
        }
      }
      showToast('No screenshot found in clipboard. Press PrintScreen or Win+Shift+S first!', 'alert-circle', 'text-amber-400');
    } catch (err) {
      console.warn('Clipboard read error:', err);
      showToast('Clipboard access denied. Please press Ctrl+V directly instead!', 'alert-circle', 'text-amber-400');
    }
  });

  // Subject selector override change
  elements.subjectSelect.addEventListener('change', () => {
    const selectedId = elements.subjectSelect.value;
    updateTargetFolderPreview(selectedId);
  });

  // Auto-Save Toggle
  elements.autoSaveToggle.addEventListener('change', (e) => {
    state.autoSave = e.target.checked;
    localStorage.setItem('gate_auto_save', state.autoSave);
    showToast(state.autoSave ? 'Auto-Save Enabled: Screenshots will be saved instantly upon paste!' : 'Manual Review Mode: You can check subject before saving', 'check-circle', 'text-indigo-400');
  });

  // Save / Discard Actions
  elements.btnSaveScreenshot.addEventListener('click', saveCurrentScreenshot);
  elements.btnDiscard.addEventListener('click', discardCurrentCapture);
  elements.btnCancelCapture.addEventListener('click', discardCurrentCapture);

  // Keyboard shortcut: Press Enter to save when in review
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !elements.reviewCard.classList.contains('hidden') && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      saveCurrentScreenshot();
    }
  });

  // Explorer search & filters
  elements.searchNotesInput.addEventListener('input', debounce(() => {
    state.searchQuery = elements.searchNotesInput.value.trim();
    loadGallery();
  }, 300));

  elements.filterSubjectSelect.addEventListener('change', () => {
    state.selectedGallerySubject = elements.filterSubjectSelect.value;
    loadGallery();
  });

  elements.btnRefreshExplorer.addEventListener('click', () => {
    loadSubjects();
    loadGallery();
    showToast('Refreshed subject folders', 'refresh-cw', 'text-indigo-400');
  });

  // Open folder on desktop
  elements.btnOpenFolder.addEventListener('click', async () => {
    try {
      await fetch('/api/open-folder', { method: 'POST' });
      showToast(`Opened folder: ${state.baseDir}`, 'folder-check', 'text-emerald-400');
    } catch (e) {
      showToast(`Notes directory: ${state.baseDir}`, 'folder', 'text-indigo-400');
    }
  });

  // Modal actions
  elements.modalBtnClose.addEventListener('click', closeModal);
  elements.lightboxModal.addEventListener('click', (e) => {
    if (e.target === elements.lightboxModal) closeModal();
  });
  elements.btnCopyOcr.addEventListener('click', () => {
    navigator.clipboard.writeText(elements.modalOcrText.value);
    showToast('OCR text copied to clipboard!', 'copy', 'text-emerald-400');
  });
  elements.modalBtnDownload.addEventListener('click', () => {
    if (!state.activeModalItem) return;
    const a = document.createElement('a');
    a.href = `/api/screenshot-file?path=${encodeURIComponent(state.activeModalItem.relative_path)}`;
    a.download = state.activeModalItem.filename;
    a.click();
  });
  elements.modalBtnDelete.addEventListener('click', deleteActiveScreenshot);
  elements.btnModalMoveConfirm.addEventListener('click', moveActiveScreenshot);

  // Settings Modal
  elements.btnSettings.addEventListener('click', () => elements.settingsModal.classList.remove('hidden'));
  elements.btnCloseSettings.addEventListener('click', () => elements.settingsModal.classList.add('hidden'));
  elements.btnSaveSettings.addEventListener('click', saveSettings);
}

// Tab Switching
function switchTab(tab) {
  state.activeTab = tab;
  elements.tabCapture.classList.toggle('active', tab === 'capture');
  elements.tabExplorer.classList.toggle('active', tab === 'explorer');
  elements.tabStats.classList.toggle('active', tab === 'stats');

  elements.sectionCapture.classList.toggle('hidden', tab !== 'capture');
  elements.sectionExplorer.classList.toggle('hidden', tab !== 'explorer');
  elements.sectionStats.classList.toggle('hidden', tab !== 'stats');

  if (tab === 'explorer') {
    loadGallery();
  } else if (tab === 'stats') {
    renderStatsBars();
  }
}

// Global Paste Handler
function handleGlobalPaste(e) {
  // If user is pasting into a text field/input, do not hijack unless it contains an image file
  const items = (e.clipboardData || e.originalEvent.clipboardData).items;
  let imageFound = false;

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const blob = items[i].getAsFile();
      handleImageFile(blob);
      imageFound = true;
      e.preventDefault();
      break;
    }
  }

  if (imageFound && state.activeTab !== 'capture') {
    switchTab('capture');
  }
}

// Process Image Blob
function handleImageFile(blob) {
  if (!blob || !blob.type.startsWith('image/')) {
    showToast('Please paste a valid screenshot image file', 'alert-triangle', 'text-rose-400');
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64Data = e.target.result;
    
    // Create image to inspect dimensions
    const img = new Image();
    img.onload = async () => {
      state.currentScreenshot = {
        base64: base64Data,
        width: img.width,
        height: img.height,
        analysis: null
      };

      // Show preview
      elements.previewImg.src = base64Data;
      elements.imgDimensions.textContent = `${img.width}x${img.height} px`;

      if (state.autoSave) {
        await executeAutoSave(base64Data);
      } else {
        await analyzeScreenshot(base64Data);
      }
    };
    img.src = base64Data;
  };
  reader.readAsDataURL(blob);
}

// Call API to analyze screenshot
async function analyzeScreenshot(base64Data) {
  elements.processingCard.classList.remove('hidden');
  elements.reviewCard.classList.add('hidden');

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: base64Data, use_ai: true })
    });
    const result = await res.json();
    
    elements.processingCard.classList.add('hidden');
    elements.reviewCard.classList.remove('hidden');

    state.currentScreenshot.analysis = result;
    populateReviewCard(result);
  } catch (err) {
    elements.processingCard.classList.add('hidden');
    showToast('Analysis error: ' + err.message, 'alert-circle', 'text-rose-400');
  }
}

// 1-Click Auto Save Mode
async function executeAutoSave(base64Data) {
  elements.processingCard.classList.remove('hidden');
  elements.reviewCard.classList.add('hidden');

  try {
    const res = await fetch('/api/analyze-and-save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: base64Data, use_ai: true })
    });
    const data = await res.json();
    elements.processingCard.classList.add('hidden');

    if (data.success) {
      showToast(`Saved to ${data.analysis.subject_name}!`, 'check-circle', 'text-emerald-400');
      await loadSubjects();
      await loadRecentScreenshots();
    } else {
      showToast('Save failed: ' + (data.error || 'Unknown error'), 'alert-circle', 'text-rose-400');
    }
  } catch (err) {
    elements.processingCard.classList.add('hidden');
    showToast('Auto-save error: ' + err.message, 'alert-circle', 'text-rose-400');
  }
}

// Fill analysis review card
function populateReviewCard(data) {
  elements.subjectCodePill.textContent = data.subject_code || 'CSE';
  elements.subjectCodePill.style.backgroundColor = data.color || '#6366f1';
  elements.detectedSubjectName.textContent = data.subject_name || 'General Notes';
  elements.detectedSubtopic.textContent = data.subtopic || 'General Topic';
  elements.confidenceScore.textContent = `${Math.round(data.confidence || 75)}%`;

  if (data.source === 'gemini_ai') {
    elements.aiBadge.classList.remove('hidden');
  } else {
    elements.aiBadge.classList.add('hidden');
  }

  // Populate Subject Select Dropdown
  elements.subjectSelect.value = data.subject_id;
  updateTargetFolderPreview(data.subject_id);

  // Matched Keywords Chips
  elements.keywordsChips.innerHTML = '';
  if (data.matched_keywords && data.matched_keywords.length > 0) {
    data.matched_keywords.forEach(kw => {
      const chip = document.createElement('span');
      chip.className = 'text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700/80 font-mono';
      chip.textContent = kw;
      elements.keywordsChips.appendChild(chip);
    });
  } else {
    elements.keywordsChips.innerHTML = '<span class="text-xs text-slate-500 italic">No specific keyword triggers</span>';
  }

  // Form Fields
  elements.inputSubtopic.value = data.subtopic || '';
  elements.inputTags.value = '';
  elements.inputNotes.value = data.summary || '';
  elements.ocrTextView.value = data.ocr_text || '';

  initIcons();
}

function updateTargetFolderPreview(subjectId) {
  elements.targetFolderPath.textContent = `${state.baseDir}/${subjectId}/`;
}

// Save Current Screenshot to Designated Folder
async function saveCurrentScreenshot() {
  if (!state.currentScreenshot) return;

  const subjectId = elements.subjectSelect.value;
  const subtopic = elements.inputSubtopic.value.trim() || 'General';
  const tagsStr = elements.inputTags.value.trim();
  const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
  const notes = elements.inputNotes.value.trim();
  const ocrText = elements.ocrTextView.value;
  const confidence = state.currentScreenshot.analysis ? state.currentScreenshot.analysis.confidence : 0;

  elements.btnSaveScreenshot.disabled = true;
  elements.btnSaveScreenshot.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Saving...';
  initIcons();

  try {
    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: state.currentScreenshot.base64,
        subject_id: subjectId,
        subtopic: subtopic,
        ocr_text: ocrText,
        confidence: confidence,
        tags: tags,
        notes: notes
      })
    });

    const data = await res.json();
    if (data.success) {
      showToast(`Screenshot organized in ${subjectId}!`, 'folder-check', 'text-emerald-400');
      discardCurrentCapture();
      await loadSubjects();
      await loadRecentScreenshots();
    } else {
      showToast('Error saving: ' + (data.error || 'Unknown error'), 'alert-circle', 'text-rose-400');
    }
  } catch (err) {
    showToast('Failed to save screenshot: ' + err.message, 'alert-circle', 'text-rose-400');
  } finally {
    elements.btnSaveScreenshot.disabled = false;
    elements.btnSaveScreenshot.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i> Save to Subject Folder (<kbd class="px-1.5 py-0.5 bg-indigo-700 rounded text-[10px] font-mono">Enter</kbd>)';
    initIcons();
  }
}

function discardCurrentCapture() {
  state.currentScreenshot = null;
  elements.reviewCard.classList.add('hidden');
  elements.processingCard.classList.add('hidden');
}

// Load subjects list and populate dropdowns & stats
async function loadSubjects() {
  try {
    const res = await fetch('/api/subjects');
    const data = await res.json();
    state.subjects = data.subjects || [];
    state.baseDir = data.base_dir || state.baseDir;

    elements.storagePathBadge.textContent = state.baseDir;
    elements.settingBaseDir.value = state.baseDir;

    let totalScreenshots = 0;
    state.subjects.forEach(s => totalScreenshots += s.count);
    elements.totalScreenshotsCount.textContent = totalScreenshots;

    populateSubjectDropdowns();
    renderSubjectCards();
  } catch (err) {
    console.error('Failed to load subjects:', err);
  }
}

function populateSubjectDropdowns() {
  // Save Review Selector
  elements.subjectSelect.innerHTML = '';
  // Explorer Filter Selector
  elements.filterSubjectSelect.innerHTML = '<option value="">All Subjects</option>';
  // Modal Move Selector
  elements.modalMoveSelect.innerHTML = '';

  state.subjects.forEach(sub => {
    // 1. Review select
    const opt1 = document.createElement('option');
    opt1.value = sub.subject_id;
    opt1.textContent = `${sub.name} (${sub.code})`;
    elements.subjectSelect.appendChild(opt1);

    // 2. Filter select
    const opt2 = document.createElement('option');
    opt2.value = sub.subject_id;
    opt2.textContent = `${sub.name} (${sub.count})`;
    elements.filterSubjectSelect.appendChild(opt2);

    // 3. Modal move select
    const opt3 = document.createElement('option');
    opt3.value = sub.subject_id;
    opt3.textContent = sub.name;
    elements.modalMoveSelect.appendChild(opt3);
  });
}

// Render Subject Folder Grid Cards in Explorer
function renderSubjectCards() {
  elements.subjectCardsGrid.innerHTML = '';

  state.subjects.forEach(sub => {
    const card = document.createElement('div');
    card.className = `p-4 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900 transition-all cursor-pointer flex flex-col justify-between group ${state.selectedGallerySubject === sub.subject_id ? 'ring-2 ring-indigo-500' : ''}`;
    
    card.innerHTML = `
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-black uppercase px-2 py-0.5 rounded text-white" style="background-color: ${sub.color}">${sub.code}</span>
          <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-colors bg-slate-800/80 px-2 py-0.5 rounded-full">${sub.count} items</span>
        </div>
        <div>
          <h4 class="font-bold text-sm text-white group-hover:text-indigo-300 transition-colors">${sub.name}</h4>
          <p class="text-[11px] text-slate-400 line-clamp-2 mt-0.5">${sub.description || 'Subject folder for notes'}</p>
        </div>
      </div>
      <div class="pt-3 mt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
        <span>${sub.total_size > 0 ? formatBytes(sub.total_size) : 'Empty'}</span>
        <span class="text-indigo-400 group-hover:underline">View Folder →</span>
      </div>
    `;

    card.addEventListener('click', () => {
      state.selectedGallerySubject = sub.subject_id;
      elements.filterSubjectSelect.value = sub.subject_id;
      loadGallery();
      document.getElementById('galleryContainer').scrollIntoView({ behavior: 'smooth' });
    });

    elements.subjectCardsGrid.appendChild(card);
  });
}

// Load Gallery with optional filter and search
async function loadGallery() {
  let url = `/api/screenshots?limit=100`;
  if (state.selectedGallerySubject) {
    url += `&subject_id=${encodeURIComponent(state.selectedGallerySubject)}`;
  }
  if (state.searchQuery) {
    url += `&q=${encodeURIComponent(state.searchQuery)}`;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();
    const items = data.items || [];

    // Update Titles
    if (state.selectedGallerySubject) {
      const sub = state.subjects.find(s => s.subject_id === state.selectedGallerySubject);
      elements.galleryTitle.textContent = sub ? sub.name : state.selectedGallerySubject;
      elements.gallerySubtitle.textContent = `Showing screenshots in ${state.selectedGallerySubject}`;
    } else if (state.searchQuery) {
      elements.galleryTitle.textContent = `Search: "${state.searchQuery}"`;
      elements.gallerySubtitle.textContent = `Found ${items.length} matching screenshots`;
    } else {
      elements.galleryTitle.textContent = 'All Screenshots';
      elements.gallerySubtitle.textContent = 'Showing all saved screenshots across GATE CSE';
    }

    elements.galleryCountBadge.textContent = `${items.length} items`;
    renderGalleryItems(items);
  } catch (err) {
    console.error('Failed to load gallery:', err);
  }
}

// Render Gallery Cards
function renderGalleryItems(items) {
  elements.galleryGrid.innerHTML = '';
  if (items.length === 0) {
    elements.galleryEmptyState.classList.remove('hidden');
    return;
  }
  elements.galleryEmptyState.classList.add('hidden');

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'gallery-card bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden cursor-pointer flex flex-col group';
    
    const sub = state.subjects.find(s => s.subject_id === item.subject_id);
    const color = sub ? sub.color : '#6366f1';
    const code = sub ? sub.code : 'CSE';

    card.innerHTML = `
      <div class="relative bg-slate-950 h-36 flex items-center justify-center overflow-hidden">
        <img src="/api/screenshot-file?path=${encodeURIComponent(item.relative_path)}" loading="lazy" alt="${item.filename}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
        <span class="absolute top-2 left-2 text-[10px] font-black uppercase px-1.5 py-0.5 rounded text-white shadow" style="background-color: ${color}">${code}</span>
        <span class="absolute bottom-2 right-2 text-[10px] bg-slate-900/80 backdrop-blur px-1.5 py-0.5 rounded text-slate-300 font-mono">${formatDate(item.created_at)}</span>
      </div>
      <div class="p-3 flex-1 flex flex-col justify-between space-y-2">
        <div>
          <h5 class="text-xs font-bold text-white truncate" title="${item.subtopic}">${item.subtopic || 'General Topic'}</h5>
          <p class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${item.notes || item.ocr_text || 'No description'}</p>
        </div>
        <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800">
          <span class="truncate max-w-[120px] font-mono">${item.filename}</span>
          <span class="text-indigo-400 group-hover:underline">Inspect →</span>
        </div>
      </div>
    `;

    card.addEventListener('click', () => openModal(item));
    elements.galleryGrid.appendChild(card);
  });
}

// Load Recent Saves for Quick Bar
async function loadRecentScreenshots() {
  try {
    const res = await fetch('/api/screenshots?limit=6');
    const data = await res.json();
    const items = data.items || [];
    
    elements.recentGrid.innerHTML = '';
    if (items.length === 0) {
      elements.recentGrid.innerHTML = '<div class="col-span-full text-xs text-slate-500 py-4">No screenshots saved yet. Hit Ctrl+V to start!</div>';
      return;
    }

    items.forEach(item => {
      const thumb = document.createElement('div');
      thumb.className = 'group relative rounded-xl border border-slate-800 bg-slate-900 overflow-hidden cursor-pointer hover:border-indigo-500/50 transition-colors';
      thumb.innerHTML = `
        <div class="h-20 bg-slate-950 flex items-center justify-center overflow-hidden">
          <img src="/api/screenshot-file?path=${encodeURIComponent(item.relative_path)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform">
        </div>
        <div class="p-1.5 text-[10px]">
          <div class="font-bold text-white truncate">${item.subtopic || item.subject_name}</div>
          <div class="text-slate-400 truncate">${formatDate(item.created_at)}</div>
        </div>
      `;
      thumb.addEventListener('click', () => openModal(item));
      elements.recentGrid.appendChild(thumb);
    });
  } catch (err) {
    console.error('Failed to load recent screenshots:', err);
  }
}

// Lightbox Modal
function openModal(item) {
  state.activeModalItem = item;
  elements.modalImg.src = `/api/screenshot-file?path=${encodeURIComponent(item.relative_path)}`;
  elements.modalTitle.textContent = item.filename;

  const sub = state.subjects.find(s => s.subject_id === item.subject_id);
  elements.modalSubjectPill.textContent = sub ? sub.code : 'CSE';
  elements.modalSubjectPill.style.backgroundColor = sub ? sub.color : '#6366f1';
  elements.modalSubjectName.textContent = item.subject_name;
  elements.modalSubtopic.textContent = item.subtopic || 'General Topic';
  elements.modalDate.textContent = item.created_at ? new Date(item.created_at).toLocaleString() : '';
  elements.modalOcrText.value = item.ocr_text || '(No OCR text extracted)';
  elements.modalMoveSelect.value = item.subject_id;

  elements.lightboxModal.classList.remove('hidden');
  initIcons();
}

function closeModal() {
  elements.lightboxModal.classList.add('hidden');
  state.activeModalItem = null;
}

// Reassign / Move Screenshot
async function moveActiveScreenshot() {
  if (!state.activeModalItem) return;
  const newSubjectId = elements.modalMoveSelect.value;
  if (newSubjectId === state.activeModalItem.subject_id) return;

  try {
    const res = await fetch('/api/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_id: state.activeModalItem.id,
        new_subject_id: newSubjectId
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Moved to ${newSubjectId}!`, 'folder-check', 'text-emerald-400');
      closeModal();
      await loadSubjects();
      await loadGallery();
    }
  } catch (err) {
    showToast('Failed to move: ' + err.message, 'alert-circle', 'text-rose-400');
  }
}

// Delete Screenshot
async function deleteActiveScreenshot() {
  if (!state.activeModalItem) return;
  if (!confirm(`Delete screenshot "${state.activeModalItem.filename}"?`)) return;

  try {
    const res = await fetch(`/api/screenshot?file_id=${encodeURIComponent(state.activeModalItem.id)}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.success) {
      showToast('Screenshot deleted', 'trash-2', 'text-indigo-400');
      closeModal();
      await loadSubjects();
      await loadGallery();
      await loadRecentScreenshots();
    }
  } catch (err) {
    showToast('Failed to delete: ' + err.message, 'alert-circle', 'text-rose-400');
  }
}

// Render Stats Bars
function renderStatsBars() {
  elements.statsBarsContainer.innerHTML = '';
  let total = 0;
  state.subjects.forEach(s => total += s.count);

  if (total === 0) {
    elements.statsBarsContainer.innerHTML = '<div class="text-xs text-slate-500 py-6">No screenshots saved yet. Start pasting to track your GATE syllabus coverage!</div>';
    return;
  }

  // Sort by count descending
  const sorted = [...state.subjects].sort((a, b) => b.count - a.count);

  sorted.forEach(sub => {
    const pct = Math.round((sub.count / total) * 100) || 0;
    const row = document.createElement('div');
    row.className = 'space-y-1.5';
    row.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <span class="font-bold text-white flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${sub.color}"></span>
          ${sub.name} (${sub.code})
        </span>
        <span class="text-slate-400 font-mono">${sub.count} screenshots (${pct}%)</span>
      </div>
      <div class="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
        <div class="h-2.5 rounded-full transition-all duration-500" style="width: ${pct}%; background-color: ${sub.color}"></div>
      </div>
    `;
    elements.statsBarsContainer.appendChild(row);
  });
}

// Settings fetch & save
async function fetchSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    state.baseDir = data.base_dir;
    elements.settingBaseDir.value = data.base_dir;
    if (data.has_gemini_key) {
      elements.geminiKeyStatus.textContent = 'Active (AI Vision Enabled)';
      elements.geminiKeyStatus.className = 'text-[10px] text-emerald-400 font-medium';
    } else {
      elements.geminiKeyStatus.textContent = 'Offline (OCR + Keyword NLP)';
      elements.geminiKeyStatus.className = 'text-[10px] text-amber-400 font-medium';
    }
  } catch (err) {
    console.error('Settings fetch error:', err);
  }
}

async function saveSettings() {
  const baseDir = elements.settingBaseDir.value.trim();
  const geminiKey = elements.settingGeminiKey.value.trim();

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        base_dir: baseDir || null,
        gemini_api_key: geminiKey || null
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Settings saved successfully!', 'check-circle', 'text-emerald-400');
      elements.settingsModal.classList.add('hidden');
      await fetchSettings();
      await loadSubjects();
    }
  } catch (err) {
    showToast('Failed to save settings: ' + err.message, 'alert-circle', 'text-rose-400');
  }
}

// Toast helper
let toastTimeout;
function showToast(message, iconName = 'check-circle', iconColor = 'text-emerald-400') {
  clearTimeout(toastTimeout);
  elements.toastMsg.textContent = message;
  elements.toastIcon.setAttribute('data-lucide', iconName);
  elements.toastIcon.className = `w-4 h-4 ${iconColor}`;
  initIcons();

  elements.toast.classList.remove('translate-y-20', 'opacity-0');
  toastTimeout = setTimeout(() => {
    elements.toast.classList.add('translate-y-20', 'opacity-0');
  }, 3500);
}

// Utilities
function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
