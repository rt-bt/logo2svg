/**
 * Logo2SVG Creative Studio - Frontend Application Engine
 * Complete interactive suite: multi-source uploads, split inspection,
 * real-time parameter re-tracing, pan & zoom, brand palettes, and exports.
 */

(function () {
  'use strict';

  // --- Studio State ---
  const state = {
    file: null,              // File object if uploaded
    sampleName: null,        // Sample filename if loaded
    filename: 'logo',        // Base clean filename
    dataUrl: null,           // Base64 Data URL of raster source
    svgContent: null,        // Raw SVG XML content
    result: null,            // Conversion result payload
    zoom: 1.0,               // Zoom multiplier (0.25 to 16.0)
    panX: 0,                 // Pan horizontal offset
    panY: 0,                 // Pan vertical offset
    viewMode: 'split',       // 'split' | 'side' | 'vector' | 'raster' | 'onion'
    splitPercent: 50,        // 0 to 100
    isDraggingSplit: false,
    justDraggedSplit: false,
    isPanning: false,
    startPanX: 0,
    startPanY: 0,
    onionAlpha: 50,          // 0 to 100
    bgTheme: 'check-dark',   // 'check-dark' | 'check-light' | 'dark' | 'white' | 'grid'
    isDarkTheme: true,
  };

  // --- DOM Elements ---
  const el = {
    body: document.body,
    fileInput: document.getElementById('file-input'),
    btnBrowse: document.getElementById('btn-browse'),
    btnHeaderUpload: document.getElementById('btn-header-upload'),
    btnToolbarUpload: document.getElementById('btn-toolbar-upload'),
    btnChangeLogo: document.getElementById('btn-change-logo'),
    btnResetLogo: document.getElementById('btn-reset-logo'),
    btnClearSource: document.getElementById('btn-clear-source'),
    dropzone: document.getElementById('dropzone'),
    dropzoneContent: document.getElementById('dropzone-content'),
    dropzonePreview: document.getElementById('dropzone-preview'),
    thumbPreview: document.getElementById('thumb-preview'),
    activeFileActions: document.getElementById('active-file-actions'),
    sourceFileBadge: document.getElementById('source-file-badge'),
    btnConvert: document.getElementById('btn-convert'),
    
    // Engine Controls
    presetCards: document.querySelectorAll('.preset-card'),
    optBw: document.getElementById('opt-bw'),
    optAlpha: document.getElementById('opt-alpha'),
    optDenoise: document.getElementById('opt-denoise'),
    optMinify: document.getElementById('opt-minify'),
    optQuantizeToggle: document.getElementById('opt-quantize-toggle'),
    optColors: document.getElementById('opt-colors'),
    valColorsBadge: document.getElementById('val-colors-badge'),
    optScale: document.getElementById('opt-scale'),
    optPrecision: document.getElementById('opt-precision'),

    // Canvas & Viewport
    canvasViewport: document.getElementById('canvas-viewport'),
    canvasDragOverlay: document.getElementById('canvas-drag-overlay'),
    emptyState: document.getElementById('empty-state'),
    processingOverlay: document.getElementById('processing-overlay'),
    processingStatusText: document.getElementById('processing-status-text'),
    stageContainer: document.getElementById('stage-container'),
    viewTabs: document.querySelectorAll('.view-tab'),
    onionControl: document.getElementById('onion-control'),
    onionAlpha: document.getElementById('onion-alpha'),
    onionVal: document.getElementById('onion-val'),
    onionTopLayer: document.getElementById('onion-top-layer'),

    // View Modes Containers
    viewSplit: document.getElementById('view-split'),
    viewSide: document.getElementById('view-side'),
    viewVector: document.getElementById('view-vector'),
    viewRaster: document.getElementById('view-raster'),
    viewOnion: document.getElementById('view-onion'),

    // Split Slider
    splitRasterImg: document.getElementById('split-img-raster'),
    splitSvgHost: document.getElementById('split-svg-host'),
    splitVectorLayer: document.getElementById('split-vector-layer'),
    splitHandle: document.getElementById('split-handle'),

    // Side by Side
    sideRasterImg: document.getElementById('side-img-raster'),
    sideSvgHost: document.getElementById('side-svg-host'),
    sideRasterMeta: document.getElementById('side-raster-meta'),
    sideVectorMeta: document.getElementById('side-vector-meta'),

    // Single Views
    singleSvgHost: document.getElementById('single-svg-host'),
    singleRasterImg: document.getElementById('single-img-raster'),
    onionRasterImg: document.getElementById('onion-img-raster'),
    onionSvgHost: document.getElementById('onion-svg-host'),

    // Canvas Background & Zoom
    bgSwatches: document.querySelectorAll('.bg-swatch-btn'),
    zoomBadge: document.getElementById('zoom-badge'),
    btnZoomIn: document.getElementById('btn-zoom-in'),
    btnZoomOut: document.getElementById('btn-zoom-out'),
    btnZoomReset: document.getElementById('btn-zoom-reset'),
    btnZoomFit: document.getElementById('btn-zoom-fit'),
    dimBadge: document.getElementById('dim-badge'),

    // Metrics Dashboard
    metricSsim: document.getElementById('metric-ssim'),
    ssimMeterFill: document.getElementById('ssim-meter-fill'),
    ssimFidelityPill: document.getElementById('ssim-fidelity-pill'),
    qualityGradeBadge: document.getElementById('quality-grade-badge'),
    metricPsnr: document.getElementById('metric-psnr'),
    metricPaths: document.getElementById('metric-paths'),
    metricSplineType: document.getElementById('metric-spline-type'),
    metricRasterSize: document.getElementById('metric-raster-size'),
    metricSvgSize: document.getElementById('metric-svg-size'),
    sizeDeltaPill: document.getElementById('size-delta-pill'),
    paletteGrid: document.getElementById('palette-grid'),
    paletteCountBadge: document.getElementById('palette-count-badge'),

    // Export Actions
    btnDownloadSvg: document.getElementById('btn-download-svg'),
    btnCopySvg: document.getElementById('btn-copy-svg'),
    btnCopyJsx: document.getElementById('btn-copy-jsx'),
    btnCopyUri: document.getElementById('btn-copy-uri'),
    btnInspectCode: document.getElementById('btn-inspect-code'),

    // Modals
    modalSamples: document.getElementById('modal-samples'),
    modalSamplesGrid: document.getElementById('modal-samples-grid'),
    modalSamplesClose: document.getElementById('modal-samples-close'),
    btnSamplesModal: document.getElementById('btn-samples-modal'),

    modalCode: document.getElementById('modal-code'),
    modalSvgCode: document.getElementById('modal-svg-code'),
    codeMetaBadge: document.getElementById('code-meta-badge'),
    btnCopyCodeModal: document.getElementById('btn-copy-code-modal'),
    modalCodeClose: document.getElementById('modal-code-close'),

    modalShortcuts: document.getElementById('modal-shortcuts'),
    btnShortcuts: document.getElementById('btn-shortcuts'),
    modalShortcutsClose: document.getElementById('modal-shortcuts-close'),

    btnThemeToggle: document.getElementById('btn-theme-toggle'),
    btnLoadDemo: document.getElementById('btn-load-demo'),
    toastContainer: document.getElementById('toast-container'),
  };

  // --- Helper Utilities ---
  function formatBytes(bytes) {
    if (!bytes || bytes <= 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `studio-toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '✕';

    toast.innerHTML = `<span style="font-size:1.1em">${icon}</span><span>${message}</span>`;
    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 260);
    }, 3200);
  }

  // --- File Picker Trigger System ---
  function openFilePicker() {
    el.fileInput.value = '';
    el.fileInput.click();
  }

  // Wire up every upload button in the UI
  [el.btnBrowse, el.btnHeaderUpload, el.btnToolbarUpload, el.btnChangeLogo, el.dropzonePreview].forEach(elem => {
    if (elem) elem.addEventListener('click', openFilePicker);
  });

  // --- Reset Studio State ---
  function resetStudio() {
    state.file = null;
    state.sampleName = null;
    state.filename = 'logo';
    state.dataUrl = null;
    state.svgContent = null;
    state.result = null;
    state.zoom = 1.0;
    state.panX = 0;
    state.panY = 0;

    el.fileInput.value = '';
    el.dropzonePreview.style.display = 'none';
    el.dropzoneContent.style.display = 'flex';
    el.activeFileActions.style.display = 'none';
    el.sourceFileBadge.textContent = 'No File';
    el.btnClearSource.style.display = 'none';

    el.stageContainer.style.display = 'none';
    el.emptyState.style.display = 'block';

    // Reset metrics
    el.metricSsim.textContent = '--%';
    el.ssimMeterFill.style.width = '0%';
    el.qualityGradeBadge.textContent = 'STANDBY';
    el.metricPsnr.textContent = '-- dB';
    el.metricPaths.textContent = '--';
    el.metricRasterSize.textContent = '-- KB';
    el.metricSvgSize.textContent = '-- KB';
    el.paletteGrid.innerHTML = '<div class="palette-placeholder">Run conversion to extract brand colors</div>';
    el.paletteCountBadge.textContent = '0 Colors';
    el.dimBadge.textContent = '0 × 0 px';

    // Disable exports
    el.btnDownloadSvg.disabled = true;
    el.btnCopySvg.disabled = true;
    el.btnCopyJsx.disabled = true;
    el.btnCopyUri.disabled = true;
    el.btnInspectCode.disabled = true;

    showToast('Studio reset. Ready for new logo.', 'info');
  }

  if (el.btnResetLogo) el.btnResetLogo.addEventListener('click', resetStudio);
  if (el.btnClearSource) el.btnClearSource.addEventListener('click', resetStudio);

  // --- File Loading Handlers ---
  function loadUploadedFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      state.file = file;
      state.sampleName = null;
      state.filename = file.name.replace(/\.[^/.]+$/, '');
      state.dataUrl = ev.target.result;

      el.sourceFileBadge.textContent = file.name;
      el.btnClearSource.style.display = 'inline-block';
      el.thumbPreview.src = state.dataUrl;
      el.dropzonePreview.style.display = 'flex';
      el.dropzoneContent.style.display = 'none';
      el.activeFileActions.style.display = 'flex';

      runConversion();
    };
    reader.readAsDataURL(file);
  }

  el.fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) loadUploadedFile(file);
  });

  // --- Drag and Drop Everywhere ---
  let dragCounter = 0;

  window.addEventListener('dragenter', e => {
    e.preventDefault();
    dragCounter++;
    if (el.canvasDragOverlay) el.canvasDragOverlay.style.display = 'flex';
    el.dropzone.classList.add('dragover');
  });

  window.addEventListener('dragleave', e => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      if (el.canvasDragOverlay) el.canvasDragOverlay.style.display = 'none';
      el.dropzone.classList.remove('dragover');
    }
  });

  window.addEventListener('dragover', e => {
    e.preventDefault();
  });

  window.addEventListener('drop', e => {
    e.preventDefault();
    dragCounter = 0;
    if (el.canvasDragOverlay) el.canvasDragOverlay.style.display = 'none';
    el.dropzone.classList.remove('dragover');

    const files = e.dataTransfer ? e.dataTransfer.files : null;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/') || /\.(png|jpe?g|webp|bmp)$/i.test(file.name)) {
        loadUploadedFile(file);
      } else {
        showToast('Please drop a valid raster image (PNG, JPG, WEBP, BMP)', 'error');
      }
    }
  });

  // Global Clipboard Paste (Ctrl+V)
  window.addEventListener('paste', e => {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
    if (!items) return;
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          loadUploadedFile(new File([blob], 'pasted_logo.png', { type: blob.type }));
          showToast('Image pasted from clipboard!', 'success');
        }
        break;
      }
    }
  });

  // --- Sample Logos Handling ---
  function loadSample(sampleFilename) {
    state.file = null;
    state.sampleName = sampleFilename;
    state.filename = sampleFilename.replace(/\.[^/.]+$/, '');
    el.sourceFileBadge.textContent = sampleFilename;
    el.btnClearSource.style.display = 'inline-block';

    const tryFetch = (url) => fetch(url).then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.blob();
    });

    tryFetch(`/examples/${sampleFilename}`)
      .catch(() => tryFetch(`/api/sample/${sampleFilename}`))
      .then(blob => {
        const reader = new FileReader();
        reader.onload = ev => {
          state.dataUrl = ev.target.result;
          el.thumbPreview.src = state.dataUrl;
          el.dropzonePreview.style.display = 'flex';
          el.dropzoneContent.style.display = 'none';
          el.activeFileActions.style.display = 'flex';
          runConversion();
        };
        reader.readAsDataURL(blob);
      })
      .catch(err => {
        showToast(`Failed to load sample: ${err.message}`, 'error');
      });
  }

  document.querySelectorAll('.sample-chip').forEach(chip => {
    chip.addEventListener('click', e => {
      e.preventDefault();
      loadSample(chip.dataset.sample);
    });
  });

  if (el.btnLoadDemo) {
    el.btnLoadDemo.addEventListener('click', () => loadSample('geometric_logo.png'));
  }

  // --- Auto-Retrace Parameter System ---
  let retraceDebounceTimer = null;
  function triggerRetraceDebounced(delay = 120) {
    if (!state.file && !state.sampleName) return;
    clearTimeout(retraceDebounceTimer);
    retraceDebounceTimer = setTimeout(() => {
      runConversion();
    }, delay);
  }

  el.presetCards.forEach(card => {
    card.addEventListener('click', () => {
      el.presetCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      triggerRetraceDebounced(40);
    });
  });

  [el.optBw, el.optAlpha, el.optDenoise, el.optMinify].forEach(toggle => {
    if (toggle) {
      toggle.addEventListener('change', () => triggerRetraceDebounced(40));
    }
  });

  el.optQuantizeToggle.addEventListener('change', () => {
    const enabled = el.optQuantizeToggle.checked;
    el.optColors.disabled = !enabled;
    el.valColorsBadge.textContent = enabled ? `${el.optColors.value} Colors` : 'Full Colors';
    triggerRetraceDebounced(40);
  });

  el.optColors.addEventListener('input', () => {
    el.valColorsBadge.textContent = `${el.optColors.value} Colors`;
    triggerRetraceDebounced(250);
  });

  el.optScale.addEventListener('change', () => triggerRetraceDebounced(40));
  el.optPrecision.addEventListener('change', () => triggerRetraceDebounced(40));

  // --- API Conversion Execution ---
  async function runConversion() {
    if (!state.file && !state.sampleName) {
      showToast('Please upload a logo or select a sample first', 'error');
      return;
    }

    el.emptyState.style.display = 'none';
    el.processingOverlay.style.display = 'flex';
    el.btnConvert.disabled = true;

    const formData = new FormData();
    if (state.file) {
      formData.append('file', state.file);
    } else if (state.sampleName) {
      formData.append('sample', state.sampleName);
    }

    const activePreset = document.querySelector('input[name="preset"]:checked')?.value || 'logo';
    formData.append('preset', activePreset);
    formData.append('bw', el.optBw.checked ? 'true' : 'false');
    formData.append('keep_alpha', el.optAlpha.checked ? 'true' : 'false');
    formData.append('denoise', el.optDenoise.checked ? 'true' : 'false');
    formData.append('minify', el.optMinify.checked ? 'true' : 'false');

    if (el.optQuantizeToggle.checked) {
      formData.append('colors', el.optColors.value);
    }

    const scaleVal = el.optScale.value;
    if (scaleVal !== 'auto') {
      formData.append('scale', scaleVal);
    }

    formData.append('precision', el.optPrecision.value);

    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Vectorization failed');
      }

      state.result = data;
      state.svgContent = data.svg_content;
      state.dataUrl = data.original_data_url || state.dataUrl;

      renderResult(data);
    } catch (err) {
      console.error(err);
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      el.processingOverlay.style.display = 'none';
      el.btnConvert.disabled = false;
    }
  }

  el.btnConvert.addEventListener('click', runConversion);

  // --- Synchronized Pixel Alignment ---
  function synchronizeElements(origW, origH) {
    const stageW = el.canvasViewport.clientWidth || 850;
    const stageH = el.canvasViewport.clientHeight || 520;
    const padding = 80;
    const maxAvailW = Math.max(180, stageW - padding);
    const maxAvailH = Math.max(180, stageH - padding);

    const scaleFactor = Math.min(maxAvailW / origW, maxAvailH / origH, 1.0);
    const fitW = Math.round(origW * scaleFactor);
    const fitH = Math.round(origH * scaleFactor);

    // Split View Layers
    el.splitRasterImg.style.width = fitW + 'px';
    el.splitRasterImg.style.height = fitH + 'px';
    el.splitSvgHost.style.width = fitW + 'px';
    el.splitSvgHost.style.height = fitH + 'px';

    const splitSvg = el.splitSvgHost.querySelector('svg');
    if (splitSvg) {
      splitSvg.setAttribute('width', fitW);
      splitSvg.setAttribute('height', fitH);
      splitSvg.style.width = '100%';
      splitSvg.style.height = '100%';
    }

    // Onion View Layers
    el.onionRasterImg.style.width = fitW + 'px';
    el.onionRasterImg.style.height = fitH + 'px';
    el.onionSvgHost.style.width = fitW + 'px';
    el.onionSvgHost.style.height = fitH + 'px';

    const onionSvg = el.onionSvgHost.querySelector('svg');
    if (onionSvg) {
      onionSvg.setAttribute('width', fitW);
      onionSvg.setAttribute('height', fitH);
      onionSvg.style.width = '100%';
      onionSvg.style.height = '100%';
    }
  }

  // --- Render Result & Update Dashboard ---
  function renderResult(res) {
    el.stageContainer.style.display = 'flex';

    // 1. Dashboard Metrics
    const ssim = res.ssim_percentage;
    el.metricSsim.textContent = `${ssim.toFixed(2)}%`;
    el.ssimMeterFill.style.width = `${Math.min(ssim, 100)}%`;

    if (ssim >= 98.5) {
      el.qualityGradeBadge.textContent = 'S+ STUDIO GRADE';
      el.qualityGradeBadge.style.color = '#34d399';
      el.qualityGradeBadge.style.borderColor = 'var(--accent-emerald)';
      el.ssimFidelityPill.textContent = 'Ultra Fidelity';
    } else if (ssim >= 95.0) {
      el.qualityGradeBadge.textContent = 'A+ GRADE';
      el.qualityGradeBadge.style.color = '#38bdf8';
      el.qualityGradeBadge.style.borderColor = 'var(--accent-cyan)';
      el.ssimFidelityPill.textContent = 'High Match';
    } else {
      el.qualityGradeBadge.textContent = 'STANDARD';
      el.qualityGradeBadge.style.color = '#f59e0b';
      el.qualityGradeBadge.style.borderColor = 'var(--accent-amber)';
      el.ssimFidelityPill.textContent = 'Good Match';
    }

    el.metricPsnr.textContent = res.psnr_display;
    el.metricPaths.textContent = res.path_count;
    el.metricSplineType.textContent = `${res.options.preset.toUpperCase()} Splines`;

    const inSize = formatBytes(res.original_size_bytes);
    const outSize = formatBytes(res.svg_size_bytes);
    el.metricRasterSize.textContent = inSize;
    el.metricSvgSize.textContent = outSize;

    const [w, h] = res.original_dimensions;
    el.dimBadge.textContent = `${w} × ${h} px`;
    el.sideRasterMeta.textContent = `Raster • ${w}×${h} px`;
    el.sideVectorMeta.textContent = `${res.path_count} Paths • ${outSize}`;

    // 2. Render Stage Visuals
    const rasterSrc = state.dataUrl;
    const svgCode = res.svg_content;

    el.splitRasterImg.src = rasterSrc;
    el.splitSvgHost.innerHTML = svgCode;

    el.sideRasterImg.src = rasterSrc;
    el.sideSvgHost.innerHTML = svgCode;

    el.singleSvgHost.innerHTML = svgCode;
    el.singleRasterImg.src = rasterSrc;

    el.onionRasterImg.src = rasterSrc;
    el.onionSvgHost.innerHTML = svgCode;

    synchronizeElements(w, h);

    // 3. Render Brand Color Palette
    renderPalette(res.colors);

    // 4. Enable Export Buttons
    el.btnDownloadSvg.disabled = false;
    el.btnCopySvg.disabled = false;
    el.btnCopyJsx.disabled = false;
    el.btnCopyUri.disabled = false;
    el.btnInspectCode.disabled = false;

    setSplitPosition(50);
    applyZoom();
  }

  function renderPalette(colors) {
    el.paletteGrid.innerHTML = '';
    if (!colors || colors.length === 0) {
      el.paletteGrid.innerHTML = '<div class="palette-placeholder">No distinct colors detected</div>';
      el.paletteCountBadge.textContent = '0 Colors';
      return;
    }

    el.paletteCountBadge.textContent = `${colors.length} Colors`;

    colors.forEach(color => {
      const chip = document.createElement('button');
      chip.className = 'color-swatch-chip';
      chip.title = `Click to copy ${color}`;
      chip.innerHTML = `<span class="swatch-pip" style="background-color: ${color}"></span><span>${color}</span>`;
      chip.addEventListener('click', () => {
        navigator.clipboard.writeText(color);
        showToast(`Copied ${color} to clipboard!`, 'success');
      });
      el.paletteGrid.appendChild(chip);
    });
  }

  // --- View Mode Switching ---
  el.viewTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      setViewMode(tab.dataset.mode);
    });
  });

  function setViewMode(mode) {
    state.viewMode = mode;
    el.viewTabs.forEach(t => t.classList.toggle('active', t.dataset.mode === mode));

    el.viewSplit.style.display = mode === 'split' ? 'flex' : 'none';
    el.viewSide.style.display = mode === 'side' ? 'grid' : 'none';
    el.viewVector.style.display = mode === 'vector' ? 'flex' : 'none';
    el.viewRaster.style.display = mode === 'raster' ? 'flex' : 'none';
    el.viewOnion.style.display = mode === 'onion' ? 'flex' : 'none';

    el.onionControl.style.display = mode === 'onion' ? 'flex' : 'none';

    if (state.result) {
      const [w, h] = state.result.original_dimensions;
      synchronizeElements(w, h);
    }
  }

  // Onion skin slider
  el.onionAlpha.addEventListener('input', e => {
    const val = e.target.value;
    el.onionVal.textContent = `${val}%`;
    el.onionTopLayer.style.opacity = val / 100;
  });

  // --- Interactive Split-Screen Curtain Slider ---
  function setSplitPosition(pct) {
    pct = Math.max(0, Math.min(100, pct));
    state.splitPercent = pct;
    el.splitHandle.style.left = `${pct}%`;
    el.splitVectorLayer.style.clipPath = `polygon(${pct}% 0%, 100% 0%, 100% 100%, ${pct}% 100%)`;
  }

  function handleSplitDrag(clientX) {
    const rect = el.viewSplit.getBoundingClientRect();
    const offsetX = clientX - rect.left;
    const pct = (offsetX / rect.width) * 100;
    setSplitPosition(pct);
  }

  el.splitHandle.addEventListener('mousedown', e => {
    state.isDraggingSplit = true;
    state.justDraggedSplit = true;
    e.preventDefault();
  });

  window.addEventListener('mousemove', e => {
    if (!state.isDraggingSplit) return;
    handleSplitDrag(e.clientX);
  });

  window.addEventListener('mouseup', () => {
    if (state.isDraggingSplit) {
      state.isDraggingSplit = false;
      setTimeout(() => { state.justDraggedSplit = false; }, 80);
    }
  });

  el.splitHandle.addEventListener('touchstart', e => {
    state.isDraggingSplit = true;
  }, { passive: true });

  window.addEventListener('touchmove', e => {
    if (!state.isDraggingSplit || !e.touches[0]) return;
    handleSplitDrag(e.touches[0].clientX);
  }, { passive: true });

  window.addEventListener('touchend', () => {
    state.isDraggingSplit = false;
  });

  el.viewSplit.addEventListener('click', e => {
    if (state.justDraggedSplit || e.target.closest('#split-handle')) return;
    handleSplitDrag(e.clientX);
  });

  // --- Zoom & Pan Engine ---
  function setZoom(val) {
    state.zoom = Math.max(0.25, Math.min(16.0, val));
    if (state.zoom === 1.0) {
      state.panX = 0;
      state.panY = 0;
    }
    applyZoom();
  }

  function applyZoom() {
    el.zoomBadge.textContent = `${Math.round(state.zoom * 100)}%`;
    const scale = state.zoom;
    const transformStr = `translate(${state.panX}px, ${state.panY}px) scale(${scale})`;

    const targets = [
      el.splitRasterImg,
      el.splitSvgHost,
      el.sideRasterImg,
      el.sideSvgHost,
      el.singleSvgHost,
      el.singleRasterImg,
      el.onionRasterImg,
      el.onionSvgHost,
    ];

    targets.forEach(t => {
      if (t) {
        t.style.transform = transformStr;
        t.style.transformOrigin = 'center center';
        t.style.transition = state.isPanning ? 'none' : 'transform 0.12s ease-out';
      }
    });
  }

  el.btnZoomIn.addEventListener('click', () => setZoom(state.zoom * 1.25));
  el.btnZoomOut.addEventListener('click', () => setZoom(state.zoom / 1.25));
  el.btnZoomReset.addEventListener('click', () => {
    state.panX = 0;
    state.panY = 0;
    setZoom(1.0);
  });
  el.btnZoomFit.addEventListener('click', () => {
    state.panX = 0;
    state.panY = 0;
    setZoom(1.0);
  });

  // Mouse wheel zoom
  el.canvasViewport.addEventListener('wheel', e => {
    if (state.stageContainer.style.display !== 'none') {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 1.15 : 0.85;
      setZoom(state.zoom * delta);
    }
  }, { passive: false });

  // Pan when zoomed in
  el.canvasViewport.addEventListener('mousedown', e => {
    if (state.zoom > 1.0 && !state.isDraggingSplit && !e.target.closest('#split-handle')) {
      state.isPanning = true;
      state.startPanX = e.clientX - state.panX;
      state.startPanY = e.clientY - state.panY;
      el.canvasViewport.style.cursor = 'grabbing';
    }
  });

  window.addEventListener('mousemove', e => {
    if (state.isPanning) {
      state.panX = e.clientX - state.startPanX;
      state.panY = e.clientY - state.startPanY;
      applyZoom();
    }
  });

  window.addEventListener('mouseup', () => {
    if (state.isPanning) {
      state.isPanning = false;
      el.canvasViewport.style.cursor = 'default';
    }
  });

  // Window resize recalculates alignment
  window.addEventListener('resize', () => {
    if (state.result) {
      const [w, h] = state.result.original_dimensions;
      synchronizeElements(w, h);
    }
  });

  // --- Canvas Backgrounds ---
  el.bgSwatches.forEach(btn => {
    btn.addEventListener('click', () => {
      el.bgSwatches.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const bg = btn.dataset.bg;
      state.bgTheme = bg;
      el.canvasViewport.className = `canvas-viewport bg-${bg}`;
    });
  });

  // --- Export Actions ---
  el.btnDownloadSvg.addEventListener('click', () => {
    if (!state.svgContent) return;
    const blob = new Blob([state.svgContent], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.filename || 'logo'}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Saved ${state.filename}.svg!`, 'success');
  });

  el.btnCopySvg.addEventListener('click', () => {
    if (!state.svgContent) return;
    navigator.clipboard.writeText(state.svgContent);
    showToast('Clean SVG code copied to clipboard!', 'success');
  });

  el.btnCopyJsx.addEventListener('click', () => {
    if (!state.svgContent) return;
    let jsx = state.svgContent
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/xml:space="preserve"/g, '')
      .replace(/fill-rule=/g, 'fillRule=')
      .replace(/clip-rule=/g, 'clipRule=')
      .replace(/stroke-width=/g, 'strokeWidth=')
      .replace(/stroke-linecap=/g, 'strokeLinecap=')
      .replace(/stroke-linejoin=/g, 'strokeLinejoin=');

    const componentCode = `export default function Logo(props) {\n  return (\n    ${jsx.trim()}\n  );\n}\n`;
    navigator.clipboard.writeText(componentCode);
    showToast('React JSX component copied!', 'success');
  });

  el.btnCopyUri.addEventListener('click', () => {
    if (!state.svgContent) return;
    const encoded = encodeURIComponent(state.svgContent)
      .replace(/'/g, '%27')
      .replace(/"/g, '%22');
    const dataUri = `data:image/svg+xml;utf8,${encoded}`;
    navigator.clipboard.writeText(dataUri);
    showToast('CSS Data URI copied to clipboard!', 'success');
  });

  // Code Inspector Modal
  el.btnInspectCode.addEventListener('click', () => {
    if (!state.svgContent) return;
    el.modalSvgCode.textContent = state.svgContent;
    const lines = state.svgContent.split('\n').length;
    const bytes = formatBytes(new Blob([state.svgContent]).size);
    el.codeMetaBadge.textContent = `${lines} Lines • ${bytes}`;
    el.modalCode.style.display = 'flex';
  });

  el.btnCopyCodeModal.addEventListener('click', () => {
    if (!state.svgContent) return;
    navigator.clipboard.writeText(state.svgContent);
    showToast('SVG XML copied!', 'success');
  });

  el.modalCodeClose.addEventListener('click', () => {
    el.modalCode.style.display = 'none';
  });

  // Samples Modal
  el.btnSamplesModal.addEventListener('click', async () => {
    el.modalSamples.style.display = 'flex';
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      renderSamplesModal(data.samples || []);
    } catch (err) {
      el.modalSamplesGrid.innerHTML = `<div class="error">Failed to load samples: ${err.message}</div>`;
    }
  });

  function renderSamplesModal(samples) {
    el.modalSamplesGrid.innerHTML = '';
    samples.forEach(s => {
      const card = document.createElement('div');
      card.className = 'sample-modal-card';
      card.innerHTML = `
        <div class="sample-thumb-wrapper">
          <img src="${s.url}" alt="${s.title}">
        </div>
        <div class="sample-card-title">${s.title}</div>
        <div class="sample-card-desc">${s.description} • ${formatBytes(s.size_bytes)}</div>
      `;
      card.addEventListener('click', () => {
        el.modalSamples.style.display = 'none';
        loadSample(s.filename);
      });
      el.modalSamplesGrid.appendChild(card);
    });
  }

  el.modalSamplesClose.addEventListener('click', () => {
    el.modalSamples.style.display = 'none';
  });

  // Shortcuts Modal
  el.btnShortcuts.addEventListener('click', () => {
    el.modalShortcuts.style.display = 'flex';
  });

  el.modalShortcutsClose.addEventListener('click', () => {
    el.modalShortcuts.style.display = 'none';
  });

  // Modal Backdrop Click
  [el.modalSamples, el.modalCode, el.modalShortcuts].forEach(modal => {
    modal.addEventListener('click', e => {
      if (e.target === modal) modal.style.display = 'none';
    });
  });

  // Theme Toggle
  el.btnThemeToggle.addEventListener('click', () => {
    state.isDarkTheme = !state.isDarkTheme;
    if (state.isDarkTheme) {
      el.body.classList.remove('studio-light');
      el.body.classList.add('studio-dark');
    } else {
      el.body.classList.remove('studio-dark');
      el.body.classList.add('studio-light');
    }
  });

  // Keyboard Shortcuts
  window.addEventListener('keydown', e => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;

    if (e.key === 'Escape') {
      el.modalSamples.style.display = 'none';
      el.modalCode.style.display = 'none';
      el.modalShortcuts.style.display = 'none';
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runConversion();
    } else if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!el.btnDownloadSvg.disabled) el.btnDownloadSvg.click();
    } else if (e.key === '1') {
      setViewMode('split');
    } else if (e.key === '2') {
      setViewMode('side');
    } else if (e.key === '3') {
      setViewMode('vector');
    } else if (e.key === '4') {
      setViewMode('raster');
    } else if (e.key === '5') {
      setViewMode('onion');
    } else if (e.key === '+' || e.key === '=') {
      setZoom(state.zoom * 1.25);
    } else if (e.key === '-' || e.key === '_') {
      setZoom(state.zoom / 1.25);
    } else if (e.key === '0') {
      setZoom(1.0);
    } else if (e.key === '?') {
      el.modalShortcuts.style.display = 'flex';
    }
  });

  console.log('🎨 Logo2SVG Creative Studio Engine fully initialized.');
})();
