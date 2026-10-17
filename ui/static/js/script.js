document.addEventListener('DOMContentLoaded', () => {
    console.log("%c --- PLAGIARISM ANALYZER PRO v13.0 LOADED --- ", "background: #4f46e5; color: white; font-weight: bold; font-size: 14px; padding: 4px;");

    // Elements
    const textInput = document.getElementById('textInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const fileInput = document.getElementById('fileInput');
    const resultsDiv = document.getElementById('results');
    const loader = document.getElementById('loader');
    const loaderStepText = document.getElementById('loaderStepText');
    const errorDiv = document.getElementById('errorMsg');
    const statusHintText = document.getElementById('statusHintText');

    // Tabs & Views
    const tabUploadBtn = document.getElementById('tabUploadBtn');
    const tabPasteBtn = document.getElementById('tabPasteBtn');
    const singleDropzoneView = document.getElementById('singleDropzoneView');
    const singlePasteView = document.getElementById('singlePasteView');
    const singleDropZone = document.getElementById('singleDropZone');
    const multiDropZone = document.getElementById('multiDropZone');

    // Mode Toggle & Navigation Elements
    const homeModeBtn = document.getElementById('homeMode');
    const brandHomeBtn = document.getElementById('brandHomeBtn');
    const homeSection = document.getElementById('homeSection');
    const featuresSection = document.getElementById('featuresSection');
    const heroSection = document.getElementById('heroSection');
    const featuresBackHomeBtn = document.getElementById('featuresBackHomeBtn');
    const workspaceBackFeaturesBtn = document.getElementById('workspaceBackFeaturesBtn');
    const workspaceBackHomeBtn = document.getElementById('workspaceBackHomeBtn');
    const singleModeBtn = document.getElementById('singleMode');
    const multiModeBtn = document.getElementById('multiMode');
    const versionModeBtn = document.getElementById('versionMode');
    const workspaceCard = document.getElementById('workspaceCard');
    const singleInputSection = document.getElementById('singleInputSection');
    const multiInputSection = document.getElementById('multiInputSection');
    const versionControlSection = document.getElementById('versionControlSection');
    const singleResults = document.getElementById('singleResults');
    const multiResults = document.getElementById('multiResults');
    const themeToggle = document.getElementById('themeToggle');

    // File Chips & Counter
    const fileListContainer = document.getElementById('fileListContainer');
    const wordCounter = document.getElementById('wordCounter');
    const charCounter = document.getElementById('charCounter');
    const clearTextBtn = document.getElementById('clearTextBtn');
    const pasteClipboardBtn = document.getElementById('pasteClipboardBtn');

    // Single Result Metric Elements
    const scoreVal = document.getElementById('scoreVal');
    const gaugeProgress = document.getElementById('gaugeProgress');
    const needleGroup = document.getElementById('needleGroup');
    const riskBadge = document.getElementById('riskBadge');
    const riskText = document.getElementById('riskText');
    const statSimilarity = document.getElementById('statSimilarity');
    const barSimilarity = document.getElementById('barSimilarity');
    const statOriginality = document.getElementById('statOriginality');
    const barOriginality = document.getElementById('barOriginality');
    const statSentences = document.getElementById('statSentences');
    const statFlaggedSentences = document.getElementById('statFlaggedSentences');
    const statTopSource = document.getElementById('statTopSource');
    const statTopSourceScore = document.getElementById('statTopSourceScore');

    // Multi Results Elements
    const matrixContainer = document.getElementById('matrixContainer');
    const pairwiseList = document.getElementById('pairwiseList');
    const multiStatDocs = document.getElementById('multiStatDocs');
    const multiStatDocsSub = document.getElementById('multiStatDocsSub');
    const multiStatPairs = document.getElementById('multiStatPairs');
    const multiStatPeak = document.getElementById('multiStatPeak');
    const multiStatPeakPair = document.getElementById('multiStatPeakPair');
    const multiStatAvg = document.getElementById('multiStatAvg');
    const statCardMultiAi = document.getElementById('statCardMultiAi');
    const multiStatAiProb = document.getElementById('multiStatAiProb');
    const multiBarAiProb = document.getElementById('multiBarAiProb');
    const multiStatAiSub = document.getElementById('multiStatAiSub');
    const multiAiSection = document.getElementById('multiAiSection');
    const multiAiFlaggedBadge = document.getElementById('multiAiFlaggedBadge');
    const multiHumanBadge = document.getElementById('multiHumanBadge');
    const multiAiTableBody = document.getElementById('multiAiTableBody');

    if (statCardMultiAi && multiAiSection) {
        statCardMultiAi.addEventListener('click', () => {
            multiAiSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Downloads
    const downloadSingleBtn = document.getElementById('downloadSingleBtn');
    const downloadMultiBtn = document.getElementById('downloadMultiBtn');

    // History
    const historyList = document.getElementById('historyList');
    const historyCountBadge = document.getElementById('historyCountBadge');

    // State
    let currentMode = 'single'; // 'single' or 'multi'
    let currentSingleTab = 'upload'; // 'upload' or 'paste'
    let selectedFilesStore = [];
    let lastSingleResults = null;
    let lastSingleText = '';
    let lastMultiResults = null;
    let lastReportId = null;
    let loaderInterval = null;

    // Theme Management
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-theme');
            const nextTheme = activeTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', nextTheme);
            localStorage.setItem('theme', nextTheme);
        });
    }

    // Helper: File Type Formatting
    function getFileIcon(filename) {
        const lower = filename.toLowerCase();
        if (lower.endsWith('.pdf')) return '📕';
        if (lower.endsWith('.docx') || lower.endsWith('.doc')) return '📘';
        if (lower.endsWith('.txt')) return '📄';
        return '📑';
    }

    function formatFileSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    // Render Staged Files Container
    function renderFileList() {
        if (!fileListContainer) return;

        if (selectedFilesStore.length === 0) {
            fileListContainer.classList.remove('has-files');
            fileListContainer.innerHTML = '<span class="no-files-placeholder">No documents selected</span>';
            updateStatusHint();
            return;
        }

        fileListContainer.classList.add('has-files');
        const labelText = currentMode === 'single' ? 'Staged Document:' : `Staged Documents (${selectedFilesStore.length}):`;

        let html = `
            <div class="selected-files-header">
                <span class="files-count-label">${labelText}</span>
                <button type="button" class="clear-files-btn" id="clearAllFilesBtn">Clear All</button>
            </div>
            <div class="selected-files-chips">
        `;

        selectedFilesStore.forEach((file, index) => {
            const icon = getFileIcon(file.name);
            const sizeStr = formatFileSize(file.size);
            html += `
                <div class="file-chip">
                    <span class="chip-icon">${icon}</span>
                    <span class="chip-name" title="${file.name}">${file.name}</span>
                    <span class="chip-size">${sizeStr}</span>
                    <button type="button" class="chip-remove" data-index="${index}" title="Remove file">×</button>
                </div>
            `;
        });

        html += `</div>`;
        fileListContainer.innerHTML = html;

        fileListContainer.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-index'), 10);
                removeFileAt(idx);
            });
        });

        const clearBtn = document.getElementById('clearAllFilesBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                clearAllFiles();
            });
        }

        updateStatusHint();
    }

    function removeFileAt(index) {
        selectedFilesStore.splice(index, 1);
        syncFileInput();
        renderFileList();
    }

    function clearAllFiles() {
        selectedFilesStore = [];
        fileInput.value = '';
        renderFileList();
    }

    function syncFileInput() {
        try {
            const dt = new DataTransfer();
            selectedFilesStore.forEach(f => dt.items.add(f));
            fileInput.files = dt.files;
        } catch (e) {
            console.log("DataTransfer sync fallback", e);
        }
    }

    function updateStatusHint() {
        if (!statusHintText) return;
        if (currentMode === 'single') {
            const words = textInput.value.trim().split(/\s+/).filter(Boolean).length;
            if (selectedFilesStore.length > 0) {
                statusHintText.textContent = `Document "${selectedFilesStore[0].name}" loaded (${words} words). Click 'Analyze Plagiarism' to start.`;
            } else if (words > 0) {
                statusHintText.textContent = `${words} words loaded. Click 'Analyze Plagiarism' to start.`;
            } else {
                statusHintText.textContent = "Type or paste text above, or upload a document below (.pdf, .docx, .txt).";
            }
        } else {
            const count = selectedFilesStore.length;
            if (count >= 2) {
                statusHintText.textContent = `${count} documents staged. Ready for N×N cross-comparison.`;
            } else {
                statusHintText.textContent = `Stage at least 2 documents to compare (${count}/2 selected).`;
            }
        }
    }

    // Word & Character Counter
    function updateWordAndCharCount() {
        const text = textInput.value;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const chars = text.length;

        if (wordCounter) wordCounter.textContent = `${words} words`;
        if (charCounter) charCounter.textContent = `${chars} characters`;
        updateStatusHint();
    }

    if (textInput) {
        textInput.addEventListener('input', () => {
            updateWordAndCharCount();
        });
    }

    function resetSingleWorkspace() {
        if (textInput) textInput.value = '';
        const extractionBadge = document.getElementById('extractionBadge');
        if (extractionBadge) extractionBadge.style.display = 'none';
        const extractionFileName = document.getElementById('extractionFileName');
        if (extractionFileName) extractionFileName.textContent = '';
        clearAllFiles();
        updateWordAndCharCount();
        if (singleResults) singleResults.style.display = 'none';
        if (resultsDiv && currentMode === 'single') resultsDiv.style.display = 'none';
        if (loader) loader.style.display = 'none';
        if (errorDiv) errorDiv.style.display = 'none';
        updateStatusHint();
    }

    function resetMultiWorkspace() {
        clearAllFiles();
        if (multiResults) multiResults.style.display = 'none';
        if (resultsDiv && currentMode === 'multi') resultsDiv.style.display = 'none';
        const matrixContainer = document.getElementById('matrixContainer');
        if (matrixContainer) matrixContainer.innerHTML = '';
        const pairwiseList = document.getElementById('pairwiseList');
        if (pairwiseList) pairwiseList.innerHTML = '';
        const multiAiSection = document.getElementById('multiAiSection');
        if (multiAiSection) multiAiSection.style.display = 'none';
        if (loader) loader.style.display = 'none';
        if (errorDiv) errorDiv.style.display = 'none';
        updateStatusHint();
    }

    if (clearTextBtn) {
        clearTextBtn.addEventListener('click', () => {
            resetSingleWorkspace();
            if (textInput) textInput.focus();
        });
    }

    if (pasteClipboardBtn) {
        pasteClipboardBtn.addEventListener('click', async () => {
            try {
                const clipText = await navigator.clipboard.readText();
                if (clipText) {
                    textInput.value = clipText;
                    updateWordAndCharCount();
                }
            } catch (err) {
                showError("Could not access clipboard. Please paste manually into the editor.");
            }
        });
    }

    // Dropzone Click Triggers
    if (singleDropZone) {
        singleDropZone.addEventListener('click', () => {
            fileInput.value = '';
            fileInput.multiple = false;
            fileInput.click();
        });
    }

    if (multiDropZone) {
        multiDropZone.addEventListener('click', () => {
            fileInput.value = '';
            fileInput.multiple = true;
            fileInput.click();
        });
    }

    // Setup Drag and Drop Listeners
    function setupDropzone(zone, isMulti) {
        if (!zone) return;
        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dragover');
            });
        });

        zone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            handleIncomingFiles(files, isMulti);
        });
    }

    setupDropzone(singleDropZone, false);
    setupDropzone(textInput, false);
    setupDropzone(multiDropZone, true);

    // Incoming File Validation and Handler
    const allowedExtensions = ['.txt', '.pdf', '.docx'];

    function handleIncomingFiles(files, isMulti) {
        if (!files || files.length === 0) return;

        if (!isMulti) {
            const file = files[0];
            const name = file.name.toLowerCase();
            const isValid = allowedExtensions.some(ext => name.endsWith(ext));

            if (!isValid) {
                showError('Unsupported file format. Please upload .txt, .pdf, or .docx documents.');
                return;
            }

            selectedFilesStore = [file];
            syncFileInput();
            renderFileList();
            errorDiv.style.display = 'none';

            // Extract text from the uploaded file and show it right in textInput
            extractSingleFileText(file);
        } else {
            const validFiles = files.filter(f => {
                const name = f.name.toLowerCase();
                return allowedExtensions.some(ext => name.endsWith(ext));
            });

            if (validFiles.length < files.length) {
                showError('Some files were ignored. Only .pdf, .docx, and .txt files are accepted.');
            } else {
                errorDiv.style.display = 'none';
            }

            validFiles.forEach(f => {
                if (!selectedFilesStore.some(existing => existing.name === f.name && existing.size === f.size)) {
                    selectedFilesStore.push(f);
                }
            });

            syncFileInput();
            renderFileList();
        }
    }

    async function extractSingleFileText(file) {
        if (statusHintText) statusHintText.textContent = `Extracting text from "${file.name}"...`;
        const formData = new FormData();
        formData.append('file', file);

        try {
            const resp = await fetch('/api/extract-text', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error);

            if (data.text) {
                textInput.value = data.text;
                updateWordAndCharCount();

                // Show extraction badge
                const extractionBadge = document.getElementById('extractionBadge');
                const extractionFileName = document.getElementById('extractionFileName');
                if (extractionBadge && extractionFileName) {
                    extractionBadge.style.display = 'inline-flex';
                    extractionFileName.textContent = file.name;
                }

                if (statusHintText) {
                    statusHintText.textContent = `Extracted text from "${file.name}" (${data.word_count || 0} words). Ready to analyze.`;
                }
            }
        } catch (e) {
            showError(`Extraction failed: ${e.message}`);
        }
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            handleIncomingFiles(files, currentMode === 'multi');
        });
    }

    // Mode Toggle Logic
    // Mode Toggle Logic
    function activateMode(mode) {
        currentMode = mode;
        if (homeModeBtn) {
            homeModeBtn.classList.toggle('active', mode === 'home');
            homeModeBtn.setAttribute('aria-selected', mode === 'home' ? 'true' : 'false');
        }
        if (singleModeBtn) {
            singleModeBtn.classList.toggle('active', mode === 'single');
            singleModeBtn.setAttribute('aria-selected', mode === 'single' ? 'true' : 'false');
        }
        if (multiModeBtn) {
            multiModeBtn.classList.toggle('active', mode === 'multi');
            multiModeBtn.setAttribute('aria-selected', mode === 'multi' ? 'true' : 'false');
        }
        if (versionModeBtn) {
            versionModeBtn.classList.toggle('active', mode === 'version');
            versionModeBtn.setAttribute('aria-selected', mode === 'version' ? 'true' : 'false');
        }

        const workspaceModePillText = document.getElementById('workspaceModePillText');

        if (errorDiv) errorDiv.style.display = 'none';

        if (mode === 'home' || mode === 'features') {
            document.body.classList.add('single-page-mode');
            document.documentElement.classList.add('single-page-mode');
        } else {
            document.body.classList.remove('single-page-mode');
            document.documentElement.classList.remove('single-page-mode');
        }

        if (mode === 'home') {
            resetSingleWorkspace();
            resetMultiWorkspace();

            const vcGrpDetail = document.getElementById('vcGroupDetailContainer');
            const vcCompContainer = document.getElementById('vcComparisonContainer');
            const vcGrpsContainer = document.getElementById('vcGroupsContainer');
            if (vcGrpDetail) vcGrpDetail.style.display = 'none';
            if (vcCompContainer) vcCompContainer.style.display = 'none';
            if (vcGrpsContainer) vcGrpsContainer.style.display = 'block';

            if (homeSection) homeSection.style.display = 'flex';
            if (featuresSection) featuresSection.style.display = 'none';
            if (heroSection) heroSection.style.display = 'none';
            if (workspaceCard) workspaceCard.style.display = 'none';
            if (versionControlSection) versionControlSection.style.display = 'none';
            if (resultsDiv) resultsDiv.style.display = 'none';
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (mode === 'features') {
            resetSingleWorkspace();
            resetMultiWorkspace();

            const vcGrpDetail = document.getElementById('vcGroupDetailContainer');
            const vcCompContainer = document.getElementById('vcComparisonContainer');
            const vcGrpsContainer = document.getElementById('vcGroupsContainer');
            if (vcGrpDetail) vcGrpDetail.style.display = 'none';
            if (vcCompContainer) vcCompContainer.style.display = 'none';
            if (vcGrpsContainer) vcGrpsContainer.style.display = 'block';

            if (homeSection) homeSection.style.display = 'none';
            if (featuresSection) featuresSection.style.display = 'flex';
            if (heroSection) heroSection.style.display = 'none';
            if (workspaceCard) workspaceCard.style.display = 'none';
            if (versionControlSection) versionControlSection.style.display = 'none';
            if (resultsDiv) resultsDiv.style.display = 'none';
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (homeSection) homeSection.style.display = 'none';
        if (featuresSection) featuresSection.style.display = 'none';
        if (heroSection) heroSection.style.display = 'block';

        // Dynamically update mode hero banner headings
        const heroHeadline = document.getElementById('heroHeadline');
        const heroSubline = document.getElementById('heroSubline');

        const modeHeadings = {
            single: {
                title: 'Single Document Plagiarism Analysis',
                sub: 'Upload or paste your text to analyze plagiarism and originality with instant similarity scoring, sentence matching, and downloadable audit reports.'
            },
            multi: {
                title: 'Multi-Document Comparison',
                sub: 'Compare multiple documents simultaneously to identify similarity matrices, cross-file sentence alignments, and cluster overlaps.'
            },
            version: {
                title: 'Version Control & Document Evolution Analysis',
                sub: 'Track document revisions over time, preserve permanent version snapshots, and compare historical evolutions.'
            }
        };

        const currentHeading = modeHeadings[mode] || modeHeadings.single;
        if (heroHeadline) heroHeadline.textContent = currentHeading.title;
        if (heroSubline) heroSubline.textContent = currentHeading.sub;

        if (mode === 'version') {
            const vcGrpDetail = document.getElementById('vcGroupDetailContainer');
            const vcCompContainer = document.getElementById('vcComparisonContainer');
            const vcGrpsContainer = document.getElementById('vcGroupsContainer');
            if (vcGrpDetail) vcGrpDetail.style.display = 'none';
            if (vcCompContainer) vcCompContainer.style.display = 'none';
            if (vcGrpsContainer) vcGrpsContainer.style.display = 'block';

            if (workspaceCard) workspaceCard.style.display = 'none';
            if (resultsDiv) resultsDiv.style.display = 'none';
            if (versionControlSection) versionControlSection.style.display = 'flex';
            checkVcAuthStatus();
        } else {
            if (workspaceCard) workspaceCard.style.display = 'block';
            if (versionControlSection) versionControlSection.style.display = 'none';
            if (singleInputSection) singleInputSection.style.display = mode === 'single' ? 'block' : 'none';
            if (multiInputSection) multiInputSection.style.display = mode === 'multi' ? 'block' : 'none';

            if (mode === 'single') {
                resetSingleWorkspace();
            } else if (mode === 'multi') {
                resetMultiWorkspace();
            }
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Smooth Animated Page Transitions
    let isTransitioning = false;

    function transitionHomeToFeatures() {
        if (isTransitioning) return;
        if (!homeSection || !featuresSection) {
            activateMode('features');
            return;
        }

        isTransitioning = true;
        homeSection.classList.remove('anim-fade-slide-up-enter', 'anim-fade-slide-down-enter');
        homeSection.classList.add('anim-fade-slide-up-exit');

        setTimeout(() => {
            homeSection.style.display = 'none';
            homeSection.classList.remove('anim-fade-slide-up-exit');

            featuresSection.style.display = 'flex';
            featuresSection.classList.remove('anim-fade-slide-down-exit', 'anim-fade-slide-up-exit');
            featuresSection.classList.add('anim-fade-slide-up-enter');
            window.scrollTo({ top: 0, behavior: 'instant' });
            currentMode = 'features';
            document.body.classList.add('single-page-mode');
            document.documentElement.classList.add('single-page-mode');

            setTimeout(() => {
                featuresSection.classList.remove('anim-fade-slide-up-enter');
                isTransitioning = false;
            }, 550);
        }, 340);
    }

    function transitionFeaturesToHome() {
        if (isTransitioning) return;
        if (!homeSection || !featuresSection) {
            activateMode('home');
            return;
        }

        isTransitioning = true;
        featuresSection.classList.remove('anim-fade-slide-up-enter', 'anim-fade-slide-down-enter');
        featuresSection.classList.add('anim-fade-slide-down-exit');

        setTimeout(() => {
            featuresSection.style.display = 'none';
            featuresSection.classList.remove('anim-fade-slide-down-exit');

            homeSection.style.display = 'flex';
            homeSection.classList.remove('anim-fade-slide-up-exit', 'anim-fade-slide-down-exit');
            homeSection.classList.add('anim-fade-slide-down-enter');
            window.scrollTo({ top: 0, behavior: 'instant' });
            currentMode = 'home';
            document.body.classList.add('single-page-mode');
            document.documentElement.classList.add('single-page-mode');

            setTimeout(() => {
                homeSection.classList.remove('anim-fade-slide-down-enter');
                isTransitioning = false;
            }, 550);
        }, 300);
    }

    // Workspace & Features Navigation Buttons
    if (workspaceBackHomeBtn) {
        workspaceBackHomeBtn.addEventListener('click', () => activateMode('home'));
    }

    if (workspaceBackFeaturesBtn) {
        workspaceBackFeaturesBtn.addEventListener('click', () => activateMode('features'));
    }

    if (featuresBackHomeBtn) {
        featuresBackHomeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            transitionFeaturesToHome();
        });
    }

    const navBackHomeBtn = document.getElementById('navBackHomeBtn');
    if (navBackHomeBtn) {
        navBackHomeBtn.addEventListener('click', () => activateMode('home'));
    }

    if (brandHomeBtn) {
        brandHomeBtn.addEventListener('click', () => activateMode('home'));
        brandHomeBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activateMode('home');
            }
        });
    }

    // Three Primary Feature Cards & Action Buttons
    const btnHomeSingle = document.getElementById('btnHomeSingle');
    const btnHomeMulti = document.getElementById('btnHomeMulti');
    const btnHomeVersion = document.getElementById('btnHomeVersion');
    const cardHomeSingle = document.getElementById('cardHomeSingle');
    const cardHomeMulti = document.getElementById('cardHomeMulti');
    const cardHomeVersion = document.getElementById('cardHomeVersion');

    if (btnHomeSingle) {
        btnHomeSingle.addEventListener('click', (e) => {
            e.stopPropagation();
            activateMode('single');
        });
    }
    if (btnHomeMulti) {
        btnHomeMulti.addEventListener('click', (e) => {
            e.stopPropagation();
            activateMode('multi');
        });
    }
    if (btnHomeVersion) {
        btnHomeVersion.addEventListener('click', (e) => {
            e.stopPropagation();
            activateMode('version');
        });
    }

    if (cardHomeSingle) cardHomeSingle.addEventListener('click', () => activateMode('single'));
    if (cardHomeMulti) cardHomeMulti.addEventListener('click', () => activateMode('multi'));
    if (cardHomeVersion) cardHomeVersion.addEventListener('click', () => activateMode('version'));

    // Hero Section Buttons
    const heroGetStartedBtn = document.getElementById('heroGetStartedBtn');
    const heroLearnMoreBtn = document.getElementById('heroLearnMoreBtn');
    const btnPreviewLaunch = document.getElementById('btnPreviewLaunch');

    if (heroGetStartedBtn) heroGetStartedBtn.addEventListener('click', () => activateMode('single'));
    if (heroLearnMoreBtn) {
        heroLearnMoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            transitionHomeToFeatures();
        });
    }
    if (btnPreviewLaunch) btnPreviewLaunch.addEventListener('click', () => activateMode('single'));

    // Call To Action Section Buttons
    const ctaGetStartedBtn = document.getElementById('ctaGetStartedBtn');
    const ctaMultiBtn = document.getElementById('ctaMultiBtn');

    if (ctaGetStartedBtn) ctaGetStartedBtn.addEventListener('click', () => activateMode('single'));
    if (ctaMultiBtn) ctaMultiBtn.addEventListener('click', () => activateMode('multi'));

    // Footer Quick Links
    const footerSingleLink = document.getElementById('footerSingleLink');
    const footerMultiLink = document.getElementById('footerMultiLink');
    const footerVersionLink = document.getElementById('footerVersionLink');

    if (footerSingleLink) footerSingleLink.addEventListener('click', () => activateMode('single'));
    if (footerMultiLink) footerMultiLink.addEventListener('click', () => activateMode('multi'));
    if (footerVersionLink) footerVersionLink.addEventListener('click', () => activateMode('version'));

    // Auth Modal Handlers
    const authModal = document.getElementById('authModal');
    const btnNavLogin = document.getElementById('btnNavLogin');
    const btnNavSignUp = document.getElementById('btnNavSignUp');
    const mobBtnLogin = document.getElementById('mobBtnLogin');
    const mobBtnSignUp = document.getElementById('mobBtnSignUp');
    const btnCloseAuthModal = document.getElementById('btnCloseAuthModal');
    const tabAuthLogin = document.getElementById('tabAuthLogin');
    const tabAuthSignup = document.getElementById('tabAuthSignup');
    const fieldAuthName = document.getElementById('fieldAuthName');
    const authModalHeading = document.getElementById('authModalHeading');
    const authModalSub = document.getElementById('authModalSub');
    const btnSubmitAuthText = document.getElementById('btnSubmitAuthText');
    const authOptionsRow = document.getElementById('authOptionsRow');
    const btnGuestAccess = document.getElementById('btnGuestAccess');
    const formAuth = document.getElementById('formAuth');
    const authNotice = document.getElementById('authNotice');

    function openAuthModal(isSignUp = false) {
        if (!authModal) return;
        authModal.style.display = 'flex';
        if (authNotice) authNotice.style.display = 'none';
        setAuthTab(isSignUp);
        if (mobileNavDrawer) mobileNavDrawer.style.display = 'none';
    }

    function closeAuthModal() {
        if (authModal) authModal.style.display = 'none';
    }

    function setAuthTab(isSignUp) {
        if (!tabAuthSignup || !tabAuthLogin) return;
        if (isSignUp) {
            tabAuthSignup.classList.add('active');
            tabAuthLogin.classList.remove('active');
            if (fieldAuthName) fieldAuthName.style.display = 'flex';
            if (authModalHeading) authModalHeading.textContent = 'Create Free Account';
            if (authModalSub) authModalSub.textContent = 'Join thousands of researchers and institutions.';
            if (btnSubmitAuthText) btnSubmitAuthText.textContent = 'Create Account';
            if (authOptionsRow) authOptionsRow.style.display = 'none';
        } else {
            tabAuthLogin.classList.add('active');
            tabAuthSignup.classList.remove('active');
            if (fieldAuthName) fieldAuthName.style.display = 'none';
            if (authModalHeading) authModalHeading.textContent = 'Welcome Back';
            if (authModalSub) authModalSub.textContent = 'Access your document analysis history and saved reports.';
            if (btnSubmitAuthText) btnSubmitAuthText.textContent = 'Sign In';
            if (authOptionsRow) authOptionsRow.style.display = 'flex';
        }
    }

    if (btnNavLogin) btnNavLogin.addEventListener('click', () => openAuthModal(false));
    if (btnNavSignUp) btnNavSignUp.addEventListener('click', () => openAuthModal(true));
    if (mobBtnLogin) mobBtnLogin.addEventListener('click', () => openAuthModal(false));
    if (mobBtnSignUp) mobBtnSignUp.addEventListener('click', () => openAuthModal(true));
    if (btnCloseAuthModal) btnCloseAuthModal.addEventListener('click', closeAuthModal);
    if (tabAuthLogin) tabAuthLogin.addEventListener('click', () => setAuthTab(false));
    if (tabAuthSignup) tabAuthSignup.addEventListener('click', () => setAuthTab(true));

    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) closeAuthModal();
        });
    }

    if (btnGuestAccess) {
        btnGuestAccess.addEventListener('click', () => {
            if (authNotice) {
                authNotice.className = 'auth-notice';
                authNotice.style.display = 'block';
                authNotice.textContent = 'Signed in as Guest Researcher. Enjoy full analysis!';
                setTimeout(() => {
                    closeAuthModal();
                    activateMode('single');
                }, 900);
            }
        });
    }

    if (formAuth) {
        formAuth.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('authEmail');
            const email = emailInput ? emailInput.value : 'User';
            if (authNotice) {
                authNotice.className = 'auth-notice';
                authNotice.style.display = 'block';
                authNotice.textContent = `Welcome back! Signed in as ${email}`;
                setTimeout(() => {
                    closeAuthModal();
                }, 1000);
            }
        });
    }

    // Contact Form Submission
    const homeContactForm = document.getElementById('homeContactForm');
    const contactFormStatus = document.getElementById('contactFormStatus');
    if (homeContactForm) {
        homeContactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('contactName');
            const name = nameInput ? nameInput.value : 'User';
            if (contactFormStatus) {
                contactFormStatus.className = 'contact-form-status success';
                contactFormStatus.style.display = 'flex';
                contactFormStatus.innerHTML = `✓ Thank you, ${name}! Your inquiry has been sent to our academic support team.`;
                homeContactForm.reset();
                setTimeout(() => {
                    contactFormStatus.style.display = 'none';
                }, 6000);
            }
        });
    }


    // Analyze Click Action
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            errorDiv.style.display = 'none';

            if (currentMode === 'single') {
                // Determine text to analyze
                let textToAnalyze = textInput.value.trim();

                if (!textToAnalyze && selectedFilesStore.length > 0) {
                    // If textInput is empty but a file is staged, extract it now
                    showLoader(true);
                    const formData = new FormData();
                    formData.append('file', selectedFilesStore[0]);
                    try {
                        const resp = await fetch('/api/extract-text', { method: 'POST', body: formData });
                        const uploadData = await resp.json();
                        if (uploadData.error) throw new Error(uploadData.error);
                        textToAnalyze = uploadData.text;
                        textInput.value = textToAnalyze;
                        updateWordAndCharCount();
                    } catch (err) {
                        showLoader(false);
                        showError(err.message);
                        return;
                    }
                }

                if (!textToAnalyze) {
                    showError('Please upload a document (.pdf, .docx, .txt) or enter text to analyze.');
                    return;
                }

                lastSingleText = textToAnalyze;
                performAnalysis(textToAnalyze);
            } else {
                if (selectedFilesStore.length < 2) {
                    showError('Please stage at least 2 documents for cross-comparison.');
                    return;
                }
                performMultiAnalysis(selectedFilesStore);
            }
        });
    }

    // =========================================================================
    // ISOLATED AI-GENERATED CONTENT DETECTION HANDLER
    // =========================================================================
    const checkAiBtn = document.getElementById('checkAiBtn');
    const checkAiBtnText = document.getElementById('checkAiBtnText');

    if (checkAiBtn) {
        checkAiBtn.addEventListener('click', async () => {
            let textToCheck = textInput.value.trim();

            if (!textToCheck && selectedFilesStore.length > 0) {
                showLoader(true);
                const formData = new FormData();
                formData.append('file', selectedFilesStore[0]);
                try {
                    const resp = await fetch('/api/extract-text', { method: 'POST', body: formData });
                    const uploadData = await resp.json();
                    if (uploadData.error) throw new Error(uploadData.error);
                    textToCheck = uploadData.text;
                    textInput.value = textToCheck;
                    updateWordAndCharCount();
                } catch (err) {
                    showLoader(false);
                    showError(err.message);
                    return;
                } finally {
                    showLoader(false);
                }
            }

            if (!textToCheck) {
                showError('Please upload a document (.pdf, .docx, .txt) or enter text to scan for AI content.');
                return;
            }

            // Reveal single results view container to display AI findings
            resultsDiv.style.display = 'block';
            if (singleResults) singleResults.style.display = 'block';
            if (multiResults) multiResults.style.display = 'none';

            runAiContentDetection(textToCheck, true);
        });
    }

    async function runAiContentDetection(text, scrollToAi = false, precomputedData = null) {
        const aiCard = document.getElementById('aiDetectionCard');
        if (!aiCard) return;

        aiCard.style.display = 'block';

        const aiPill = document.getElementById('aiClassificationPill');
        const aiPillText = document.getElementById('aiClassificationText');
        const aiProbVal = document.getElementById('aiProbabilityVal');
        const aiHumanProbVal = document.getElementById('aiHumanProbabilityVal');
        const aiConfVal = document.getElementById('aiConfidenceVal');
        const aiChunksVal = document.getElementById('aiChunksVal');
        const aiBarHuman = document.getElementById('aiBarFillHuman');
        const aiBarAi = document.getElementById('aiBarFillAi');
        const aiBarHumanLabel = document.getElementById('aiBarHumanLabel');
        const aiBarAiLabel = document.getElementById('aiBarAiLabel');
        const aiDetail = document.getElementById('aiAssessmentDetail');
        const aiDisclaimer = document.getElementById('aiDisclaimerText');

        // Loading state
        if (checkAiBtn) checkAiBtn.disabled = true;
        if (checkAiBtnText) checkAiBtnText.textContent = 'Scanning AI...';
        if (aiPill) {
            aiPill.className = 'ai-pill ai-pill-inconclusive';
            if (aiPillText) aiPillText.textContent = 'Evaluating...';
        }
        if (aiDetail) {
            aiDetail.textContent = 'Analyzing neural token distributions and perplexity heuristics...';
        }

        const statAiProb = document.getElementById('statAiProbability');
        const barAiProb = document.getElementById('barAiProbability');
        const statAiClass = document.getElementById('statAiClassification');
        const aiIconWrap = document.getElementById('aiStatIconWrapper');
        if (statAiProb) statAiProb.textContent = 'Scanning...';
        if (statAiClass) statAiClass.textContent = 'Analyzing neural patterns...';
        if (barAiProb) {
            barAiProb.style.width = '35%';
            barAiProb.style.background = 'linear-gradient(90deg, #7c3aed 0%, #a855f7 100%)';
        }

        if (scrollToAi) {
            aiCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        try {
            let data = precomputedData;
            if (!data) {
                const resp = await fetch('/api/ai/detect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });

                data = await resp.json();

                if (!resp.ok || !data.valid) {
                    throw new Error(data.error || 'Failed to analyze text for AI generation.');
                }
            }

            const aiProb = parseFloat(data.ai_probability || 0);
            const humanProb = parseFloat(data.human_probability || 0);

            if (aiProbVal) aiProbVal.textContent = `${aiProb.toFixed(1)}%`;
            if (aiHumanProbVal) aiHumanProbVal.textContent = `${humanProb.toFixed(1)}%`;
            if (aiConfVal) aiConfVal.textContent = data.confidence || 'Moderate';

            const chunksCount = data.chunks_analyzed || 1;
            if (aiChunksVal) aiChunksVal.textContent = `${chunksCount} Segment${chunksCount !== 1 ? 's' : ''}`;

            if (aiBarHuman) aiBarHuman.style.width = `${humanProb}%`;
            if (aiBarAi) aiBarAi.style.width = `${aiProb}%`;
            if (aiBarHumanLabel) aiBarHumanLabel.textContent = `${humanProb.toFixed(1)}%`;
            if (aiBarAiLabel) aiBarAiLabel.textContent = `${aiProb.toFixed(1)}%`;

            // Classification Pill Styling
            if (aiPill && aiPillText) {
                aiPill.className = 'ai-pill';
                aiPillText.textContent = data.classification || 'Inconclusive';

                if (data.classification === 'Likely AI-generated') {
                    aiPill.classList.add('ai-pill-ai');
                    if (aiProbVal) aiProbVal.style.color = 'var(--danger)';
                } else if (data.classification === 'Likely human-written') {
                    aiPill.classList.add('ai-pill-human');
                    if (aiProbVal) aiProbVal.style.color = 'var(--text-main)';
                } else if (data.classification.includes('Mixed')) {
                    aiPill.classList.add('ai-pill-mixed');
                    if (aiProbVal) aiProbVal.style.color = 'var(--warning)';
                } else {
                    aiPill.classList.add('ai-pill-inconclusive');
                    if (aiProbVal) aiProbVal.style.color = 'var(--text-muted)';
                }
            }

            // Sync with Card 1 in Executive Overview (Idea 4)
            if (statAiProb) statAiProb.textContent = `${aiProb.toFixed(1)}%`;
            if (barAiProb) {
                barAiProb.style.width = `${Math.min(100, Math.max(3, aiProb))}%`;
                if (aiProb >= 50) {
                    barAiProb.style.background = 'var(--danger)';
                } else if (aiProb >= 25) {
                    barAiProb.style.background = 'var(--warning)';
                } else {
                    barAiProb.style.background = 'var(--success)';
                }
            }
            if (statAiClass) {
                statAiClass.textContent = data.classification || (aiProb < 25 ? 'Likely human-written' : 'AI patterns detected');
            }
            if (aiIconWrap) {
                aiIconWrap.className = 'stat-icon-wrapper';
                if (aiProb >= 50) aiIconWrap.classList.add('icon-danger');
                else if (aiProb >= 25) aiIconWrap.classList.add('icon-warning');
                else aiIconWrap.classList.add('icon-ai');
            }

            if (aiDetail) {
                aiDetail.textContent = data.assessment_detail || 'Analysis completed.';
            }

            if (aiDisclaimer && data.disclaimer) {
                aiDisclaimer.innerHTML = `<strong>Notice:</strong> ${escapeHtml(data.disclaimer)}`;
            }

        } catch (err) {
            console.error('AI Detection Error:', err);
            if (aiPill) {
                aiPill.className = 'ai-pill ai-pill-inconclusive';
                if (aiPillText) aiPillText.textContent = 'Notice';
            }
            if (aiDetail) {
                aiDetail.textContent = `AI Content Scan: ${err.message}`;
            }
            if (statAiProb) statAiProb.textContent = 'Inconclusive';
            if (statAiClass) statAiClass.textContent = 'Short / unverified text';
            if (barAiProb) barAiProb.style.width = '0%';
        } finally {
            if (checkAiBtn) checkAiBtn.disabled = false;
            if (checkAiBtnText) checkAiBtnText.textContent = 'Check AI Content';
        }
    }

    // Single Analysis Runner
    async function performAnalysis(text) {
        showLoader(true);
        resultsDiv.style.display = 'none';
        singleResults.style.display = 'block';
        multiResults.style.display = 'none';
        errorDiv.style.display = 'none';

        // Reset Gauge Elements
        if (needleGroup) needleGroup.setAttribute('transform', 'rotate(-90 100 100)');
        if (gaugeProgress) gaugeProgress.style.strokeDashoffset = '251.3';
        if (scoreVal) scoreVal.textContent = '0.0%';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            displayResults(data, text);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoader(false);
        }
    }

    // Multi Analysis Runner
    async function performMultiAnalysis(files) {
        showLoader(true);
        resultsDiv.style.display = 'none';
        if (singleResults) singleResults.style.display = 'none';
        if (multiResults) multiResults.style.display = 'none';
        errorDiv.style.display = 'none';

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const response = await fetch('/api/multi-check', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            displayMultiResults(data);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoader(false);
        }
    }

    // Display Single Results (Executive View)
    function displayResults(data, originalText) {
        lastSingleResults = data;
        lastReportId = data.report_id;
        resultsDiv.style.display = 'block';
        if (singleResults) singleResults.style.display = 'block';
        if (multiResults) multiResults.style.display = 'none';

        const pct = parseFloat(data.overall_percentage || data.similarity_score || 0);
        const originality = Math.max(0, 100 - pct);

        // Arc tracking
        const circumference = 251.3;

        // Reset elements
        moveNeedle(0);
        if (gaugeProgress) gaugeProgress.style.strokeDashoffset = circumference;

        // Number animation
        let currentCount = 0;
        const duration = 1400;
        const startTime = Date.now();

        const updateCounter = () => {
            const now = Date.now();
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            currentCount = (pct * easedProgress).toFixed(1);

            if (scoreVal) scoreVal.textContent = `${currentCount}%`;
            moveNeedle(parseFloat(currentCount));

            if (gaugeProgress) {
                const currentOffset = circumference - (parseFloat(currentCount) / 100) * circumference;
                gaugeProgress.style.strokeDashoffset = currentOffset;
            }

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                if (scoreVal) scoreVal.textContent = `${pct.toFixed(1)}%`;
                moveNeedle(pct);
                if (gaugeProgress) {
                    const finalOffset = circumference - (pct / 100) * circumference;
                    gaugeProgress.style.strokeDashoffset = finalOffset;
                }
            }
        };
        requestAnimationFrame(updateCounter);

        // Risk Pill & Colors
        if (riskBadge && riskText) {
            riskBadge.className = 'risk-pill';
            if (pct < 40) {
                riskBadge.classList.add('risk-low');
                riskText.textContent = 'Safe & Authentic';
                if (scoreVal) scoreVal.style.color = 'var(--success)';
            } else if (pct < 70) {
                riskBadge.classList.add('risk-mid');
                riskText.textContent = 'Moderate Similarity';
                if (scoreVal) scoreVal.style.color = 'var(--warning)';
            } else {
                riskBadge.classList.add('risk-high');
                riskText.textContent = 'High Plagiarism Risk';
                if (scoreVal) scoreVal.style.color = 'var(--danger)';
            }
        }

        // Stat Quad Population (Idea 1, 3, and 4)
        // 1. Idea 4: AI Generation Likelihood (Initial state while AI runs async)
        const statAiProb = document.getElementById('statAiProbability');
        const barAiProb = document.getElementById('barAiProbability');
        const statAiClass = document.getElementById('statAiClassification');
        const aiIconWrap = document.getElementById('aiStatIconWrapper');
        if (statAiProb) statAiProb.textContent = 'Scanning...';
        if (barAiProb) {
            barAiProb.style.width = '30%';
            barAiProb.style.background = 'linear-gradient(90deg, #7c3aed 0%, #a855f7 100%)';
        }
        if (statAiClass) statAiClass.textContent = 'Analyzing neural patterns...';
        if (aiIconWrap) aiIconWrap.className = 'stat-icon-wrapper icon-ai';

        const statCardAi = document.getElementById('statCardAi');
        if (statCardAi && !statCardAi.hasAttribute('data-bound')) {
            statCardAi.setAttribute('data-bound', 'true');
            statCardAi.addEventListener('click', () => {
                const aiCard = document.getElementById('aiDetectionCard');
                if (aiCard) {
                    aiCard.style.display = 'block';
                    aiCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        }

        // 2. Document Originality
        if (statOriginality) statOriginality.textContent = `${originality.toFixed(1)}%`;
        if (barOriginality) barOriginality.style.width = `${originality}%`;
        const origSub = document.getElementById('statOriginalitySubtext');
        if (origSub) {
            origSub.textContent = pct < 40 ? 'High originality score' : (pct < 70 ? 'Moderate originality' : 'Elevated overlap detected');
        }

        // 3. Idea 1: Flagged Sentences Breakdown
        const totalSent = data.total_sentences || 0;
        const flaggedSent = Array.isArray(data.plagiarized_sentences) ? data.plagiarized_sentences.length : (data.plagiarized_sentences || 0);
        const cleanSent = Math.max(0, totalSent - flaggedSent);
        const flaggedPct = totalSent > 0 ? ((flaggedSent / totalSent) * 100) : 0;

        if (statSentences) statSentences.textContent = `${flaggedSent} / ${totalSent}`;
        const barFlagged = document.getElementById('barFlaggedSentences');
        if (barFlagged) {
            barFlagged.style.width = `${Math.min(100, Math.max(3, flaggedPct))}%`;
            if (flaggedPct < 25) barFlagged.style.backgroundColor = 'var(--success)';
            else if (flaggedPct < 55) barFlagged.style.backgroundColor = 'var(--warning)';
            else barFlagged.style.backgroundColor = 'var(--danger)';
        }
        if (statFlaggedSentences) {
            statFlaggedSentences.textContent = `${cleanSent} clean sentences (${flaggedPct.toFixed(1)}% flagged)`;
        }

        // 4. Idea 3: Match Intensity & Top Source
        const avgSim = data.average_similarity || 0;
        let intensityLabel = 'Zero Matches';
        let pillClass = 'pill-clean';
        let iconClass = 'icon-success';

        if (avgSim >= 75) {
            intensityLabel = 'Direct Match';
            pillClass = 'pill-high';
            iconClass = 'icon-danger';
        } else if (avgSim >= 45) {
            intensityLabel = 'Moderate Match';
            pillClass = 'pill-moderate';
            iconClass = 'icon-warning';
        } else if (avgSim > 0) {
            intensityLabel = 'Mild Paraphrasing';
            pillClass = 'pill-low';
            iconClass = 'icon-primary';
        }

        const intensityPillElem = document.getElementById('statIntensityPill');
        if (intensityPillElem) {
            intensityPillElem.textContent = intensityLabel;
            intensityPillElem.className = `match-pill ${pillClass}`;
        }

        const intensityIconElem = document.getElementById('matchIntensityIconWrapper');
        if (intensityIconElem) {
            intensityIconElem.className = `stat-icon-wrapper ${iconClass}`;
        }

        const topValElem = document.getElementById('statTopSourceVal');
        const topBarElem = document.getElementById('barTopSource');

        if (data.top_matches && data.top_matches.length > 0) {
            const top = data.top_matches[0];
            const topPct = (top.score * 100).toFixed(1);
            const topScoreNum = parseFloat(topPct) || 0;

            if (topValElem) {
                topValElem.textContent = `${topPct}%`;
            } else if (statTopSource) {
                statTopSource.textContent = `${topPct}%`;
            }

            if (topBarElem) {
                topBarElem.style.width = `${Math.min(100, Math.max(3, topScoreNum))}%`;
                if (topScoreNum < 25) topBarElem.style.backgroundColor = 'var(--success)';
                else if (topScoreNum < 55) topBarElem.style.backgroundColor = 'var(--warning)';
                else topBarElem.style.backgroundColor = 'var(--danger)';
            }

            if (statTopSourceScore) {
                statTopSourceScore.textContent = `Top Match: ${top.title || 'Matched Document'}`;
                statTopSourceScore.title = `Top match: ${top.title || ''} (${topPct}% overlap)`;
            }
        } else {
            if (topValElem) {
                topValElem.textContent = '0.0%';
            } else if (statTopSource) {
                statTopSource.textContent = '0.0%';
            }

            if (topBarElem) {
                topBarElem.style.width = '0%';
                topBarElem.style.backgroundColor = 'var(--success)';
            }

            if (statTopSourceScore) {
                statTopSourceScore.textContent = '100% Unique Document';
                statTopSourceScore.title = 'No significant text matches detected across corpus';
            }
        }

        // Smooth Scroll to Results
        resultsDiv.scrollIntoView({ behavior: 'smooth' });

        // Refresh History
        loadHistory();

        // Asynchronously check AI content without blocking plagiarism results
        if (typeof runAiContentDetection === 'function') {
            const preAi = data.ai_analysis || (data.results && data.results.ai_analysis);
            runAiContentDetection(originalText, false, preAi);
        }
    }

    // Display Multi-Compare Results
    function displayMultiResults(data) {
        lastMultiResults = data;
        resultsDiv.style.display = 'block';
        if (singleResults) singleResults.style.display = 'none';
        if (multiResults) multiResults.style.display = 'block';
        matrixContainer.innerHTML = '';
        pairwiseList.innerHTML = '';

        const docNames = data.document_names || [];
        const pairwise = data.pairwise_results || [];

        // 1. Executive Summary Metrics Calculation
        const totalDocs = docNames.length;
        const totalPairs = pairwise.length;
        let peakScore = 0;
        let peakDocNames = "No overlap detected";

        if (pairwise.length > 0) {
            const topPair = pairwise[0]; // sorted descending by backend
            peakScore = topPair.similarity_percentage || 0;
            peakDocNames = `${topPair.doc1} ↔ ${topPair.doc2}`;
        }

        let avgScore = 0;
        if (pairwise.length > 0) {
            const totalSum = pairwise.reduce((acc, p) => acc + (p.similarity_percentage || 0), 0);
            avgScore = totalSum / pairwise.length;
        }

        if (multiStatDocs) multiStatDocs.textContent = `${totalDocs}`;
        if (multiStatDocsSub) multiStatDocsSub.textContent = `${totalDocs} Documents In Corpus`;
        if (multiStatPairs) multiStatPairs.textContent = `${totalPairs}`;
        if (multiStatPeak) {
            multiStatPeak.textContent = `${peakScore.toFixed(1)}%`;
            multiStatPeak.style.color = peakScore >= 70 ? 'var(--danger)' : (peakScore >= 40 ? 'var(--warning)' : 'var(--success)');
        }
        if (multiStatPeakPair) {
            multiStatPeakPair.textContent = peakDocNames;
            multiStatPeakPair.title = peakDocNames;
        }
        if (multiStatAvg) {
            multiStatAvg.textContent = `${avgScore.toFixed(1)}%`;
            multiStatAvg.style.color = avgScore >= 70 ? 'var(--danger)' : (avgScore >= 40 ? 'var(--warning)' : 'var(--success)');
        }

        // Multi-Document AI Content & Authorship Audit
        const aiAnalysis = data.ai_analysis;
        if (aiAnalysis) {
            const avgAi = typeof aiAnalysis.average_ai_probability === 'number' ? aiAnalysis.average_ai_probability : 0;
            if (multiStatAiProb) {
                multiStatAiProb.textContent = `${avgAi.toFixed(1)}%`;
                multiStatAiProb.style.color = avgAi >= 70 ? 'var(--danger)' : (avgAi >= 40 ? 'var(--warning)' : 'var(--success)');
            }
            if (multiBarAiProb) {
                multiBarAiProb.style.width = `${Math.min(100, Math.max(0, avgAi))}%`;
            }
            if (multiStatAiSub) {
                const flagged = aiAnalysis.ai_flagged_count || 0;
                const human = aiAnalysis.human_count || 0;
                multiStatAiSub.textContent = `${flagged} Flagged AI • ${human} Human`;
            }
            if (multiAiFlaggedBadge) {
                multiAiFlaggedBadge.textContent = `${aiAnalysis.ai_flagged_count || 0} AI Flagged`;
            }
            if (multiHumanBadge) {
                multiHumanBadge.textContent = `${aiAnalysis.human_count || 0} Human Written`;
            }

            if (multiAiTableBody && Array.isArray(aiAnalysis.documents)) {
                multiAiTableBody.innerHTML = '';
                // Sort documents from low to high by AI Likelihood
                const sortedAiDocs = [...aiAnalysis.documents].sort((a, b) => (parseFloat(a.ai_probability) || 0) - (parseFloat(b.ai_probability) || 0));
                sortedAiDocs.forEach(doc => {
                    const row = document.createElement('tr');
                    const isAi = doc.classification === 'Likely AI-generated';
                    const isHuman = doc.classification === 'Likely human-written';
                    const pillClass = isAi ? 'ai-pill-ai' : (isHuman ? 'ai-pill-human' : 'ai-pill-inconclusive');
                    const pillIcon = isAi ? '🤖' : (isHuman ? '✍️' : '⚖️');
                    const scoreColor = isAi ? 'var(--danger)' : (isHuman ? 'var(--success)' : 'var(--warning)');
                    
                    row.innerHTML = `
                        <td class="ai-doc-name-cell">
                            <span class="ai-file-icon">📄</span>
                            <span class="ai-file-name" title="${escapeHtml(doc.name)}">${escapeHtml(doc.name)}</span>
                        </td>
                        <td>${doc.word_count ? doc.word_count.toLocaleString() : '0'}</td>
                        <td>
                            <div class="ai-score-cell">
                                <span class="ai-score-num" style="color: ${scoreColor}">${(doc.ai_probability || 0).toFixed(1)}%</span>
                                <div class="ai-score-track">
                                    <div class="ai-score-fill" style="width: ${Math.min(100, Math.max(0, doc.ai_probability || 0))}%; background: ${scoreColor}"></div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <span class="ai-pill ${pillClass}">${pillIcon} ${escapeHtml(doc.classification || 'Inconclusive')}</span>
                        </td>
                        <td>
                            <span class="ai-conf-badge">${escapeHtml(doc.confidence || 'Moderate')}</span>
                        </td>
                    `;
                    multiAiTableBody.appendChild(row);
                });
            }
        }

        // 2. Render Matrix Table
        const table = document.createElement('table');
        table.className = 'matrix-table';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Corpus Document</th>' + docNames.map(name => `<th>${escapeHtml(name)}</th>`).join('');
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        docNames.forEach(name1 => {
            const row = document.createElement('tr');
            let rowHtml = `<th>${escapeHtml(name1)}</th>`;
            docNames.forEach(name2 => {
                const score = (data.matrix && data.matrix[name1] && data.matrix[name1][name2] !== undefined)
                    ? data.matrix[name1][name2]
                    : (name1 === name2 ? 100 : 0);

                if (name1 === name2) {
                    rowHtml += `<td class="self-sim" title="Identical baseline (Self)">100% <span style="font-size:0.75rem; opacity:0.8;">(Self)</span></td>`;
                } else if (score >= 70) {
                    rowHtml += `<td class="high-sim" title="High Similarity">${score.toFixed(1)}%</td>`;
                } else if (score >= 40) {
                    rowHtml += `<td class="mid-sim" title="Moderate Similarity">${score.toFixed(1)}%</td>`;
                } else {
                    rowHtml += `<td class="low-sim" title="Low Similarity / Unique">${score.toFixed(1)}%</td>`;
                }
            });
            row.innerHTML = rowHtml;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        matrixContainer.appendChild(table);

        // 3. Render Pairwise Alignments
        if (pairwise.length === 0) {
            pairwiseList.innerHTML = '<p class="pair-details" style="padding:1.5rem; text-align:center;">No cross-document combinations available.</p>';
        } else {
            pairwise.forEach((pair, pairIdx) => {
                const card = document.createElement('div');
                const isCrit = pair.similarity_percentage >= 70;
                const isMid = pair.similarity_percentage >= 40 && pair.similarity_percentage < 70;
                card.className = `pair-card ${isCrit ? 'critical' : ''}`;

                const scoreColor = isCrit ? 'var(--danger)' : (isMid ? 'var(--warning)' : 'var(--success)');
                const scoreBg = isCrit ? 'var(--danger-light)' : (isMid ? 'var(--warning-light)' : 'var(--success-light)');
                const matchCount = pair.matching_sentences_count || (pair.matches ? pair.matches.length : 0);
                const hasMatches = pair.matches && pair.matches.length > 0;
                const drawerId = `pairDrawer_${pairIdx}`;

                let matchesHtml = '';
                if (hasMatches) {
                    matchesHtml = `
                        <div class="pair-matches-drawer" id="${drawerId}" style="display: none;">
                            <div class="match-snippet-label">Aligned Sentence Matches (${pair.matches.length}):</div>
                            ${pair.matches.map((m, mIdx) => {
                        const mScore = m.similarity_percentage || m.score || 0;
                        const mCrit = mScore >= 70;
                        const mBadgeBg = mCrit ? 'var(--danger-light)' : 'var(--warning-light)';
                        const mBadgeColor = mCrit ? 'var(--danger)' : 'var(--warning)';
                        return `
                                    <div class="match-snippet-box">
                                        <div class="match-snippet-header">
                                            <span style="color:var(--text-muted);">Match #${mIdx + 1}</span>
                                            <span class="match-snippet-level" style="background:${mBadgeBg}; color:${mBadgeColor}">
                                                ${mScore.toFixed(1)}% • ${escapeHtml(m.plagiarism_level || 'Overlap')}
                                            </span>
                                        </div>
                                        <div style="margin-bottom:0.4rem;">
                                            <span class="match-snippet-label">${escapeHtml(pair.doc1)}:</span>
                                            <p class="match-snippet-text">"${escapeHtml(m.sentence1)}"</p>
                                        </div>
                                        <div>
                                            <span class="match-snippet-label">${escapeHtml(pair.doc2)}:</span>
                                            <p class="match-snippet-text" style="color:var(--text-muted);">"${escapeHtml(m.sentence2)}"</p>
                                        </div>
                                    </div>
                                `;
                    }).join('')}
                        </div>
                    `;
                }

                card.innerHTML = `
                    <div class="pair-card-header">
                        <div class="pair-doc-names">
                            <span class="pair-doc-pill">
                                <span>📄</span>
                                <span title="${escapeHtml(pair.doc1)}">${escapeHtml(pair.doc1)}</span>
                            </span>
                            <span class="pair-vs-badge">VS</span>
                            <span class="pair-doc-pill">
                                <span>📄</span>
                                <span title="${escapeHtml(pair.doc2)}">${escapeHtml(pair.doc2)}</span>
                            </span>
                        </div>
                        <span class="pair-score-badge" style="background:${scoreBg}; color:${scoreColor}">
                            ${pair.similarity_percentage.toFixed(1)}% Similarity
                        </span>
                    </div>
                    <div class="pair-summary-bar">
                        <span>Detected <strong>${matchCount}</strong> overlapping sentence segment${matchCount === 1 ? '' : 's'}.</span>
                        ${hasMatches ? `
                            <button type="button" class="btn-toggle-matches" data-drawer="${drawerId}">
                                <span>View Matches (${pair.matches.length})</span>
                                <span class="arrow-icon">▼</span>
                            </button>
                        ` : ''}
                    </div>
                    ${matchesHtml}
                `;

                // Bind drawer toggle
                const toggleBtn = card.querySelector('.btn-toggle-matches');
                if (toggleBtn) {
                    toggleBtn.addEventListener('click', () => {
                        const targetDrawer = card.querySelector(`#${drawerId}`);
                        const arrow = toggleBtn.querySelector('.arrow-icon');
                        if (targetDrawer) {
                            const isHidden = targetDrawer.style.display === 'none';
                            targetDrawer.style.display = isHidden ? 'flex' : 'none';
                            if (arrow) arrow.textContent = isHidden ? '▲' : '▼';
                        }
                    });
                }

                pairwiseList.appendChild(card);
            });
        }

        // Smooth Scroll to Results
        resultsDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Needle Controller
    function moveNeedle(value) {
        if (!needleGroup) return;
        const minAngle = -90;
        const maxAngle = 90;
        const clampedValue = Math.max(0, Math.min(100, value));
        const rotation = (clampedValue * (maxAngle - minAngle) / 100) + minAngle;
        needleGroup.setAttribute('transform', `rotate(${rotation} 100 100)`);
    }

    // Loader with Progressive Step Ticker
    const steps = [
        "Parsing document structure & encoding text...",
        "Executing sentence segmentation & N-gram tokenization...",
        "Building TF-IDF vector representations...",
        "Calculating Cosine & Jaccard similarity matrices...",
        "Compiling executive metrics & PDF report..."
    ];

    function showLoader(show) {
        loader.style.display = show ? 'block' : 'none';
        analyzeBtn.disabled = show;

        if (show) {
            let stepIdx = 0;
            if (loaderStepText) loaderStepText.textContent = steps[0];
            loaderInterval = setInterval(() => {
                stepIdx = (stepIdx + 1) % steps.length;
                if (loaderStepText) loaderStepText.textContent = steps[stepIdx];
            }, 550);
        } else {
            if (loaderInterval) {
                clearInterval(loaderInterval);
                loaderInterval = null;
            }
        }
    }

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Download PDF Handlers
    function triggerDownloadSingle() {
        if (!lastReportId) {
            showError("No report ID found. Please re-run analysis.");
            return;
        }
        window.location.assign(`/api/download/${lastReportId}`);
    }

    if (downloadSingleBtn) downloadSingleBtn.addEventListener('click', triggerDownloadSingle);

    if (downloadMultiBtn) {
        downloadMultiBtn.addEventListener('click', async () => {
            if (!lastMultiResults) return;
            try {
                const response = await fetch('/api/download-report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: 'multi', ...lastMultiResults })
                });

                if (!response.ok) throw new Error('Multi-document report generation failed.');

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = 'Multi_Comparison_Report.pdf';
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                    window.URL.revokeObjectURL(downloadUrl);
                    document.body.removeChild(a);
                }, 2000);
            } catch (err) {
                showError('Multi-report download failed: ' + err.message);
            }
        });
    }

    // ==========================================================================
    // ENHANCED AUDIT HISTORY CONTROLLER (Search, Filter, Pagination, Load)
    // ==========================================================================
    let allAudits = [];
    let filteredAudits = [];
    let currentHistoryPage = 1;
    const AUDITS_PER_PAGE = 9;
    let activeFilter = 'all';
    let searchQuery = '';

    const historySearchInput = document.getElementById('historySearchInput');
    const historyClearSearch = document.getElementById('historyClearSearch');
    const filterButtons = document.querySelectorAll('.history-filter-btn');
    const historyPagination = document.getElementById('historyPagination');
    const historyPrevBtn = document.getElementById('historyPrevBtn');
    const historyNextBtn = document.getElementById('historyNextBtn');
    const historyPageIndicator = document.getElementById('historyPageIndicator');

    function formatRelativeTime(dateString) {
        if (!dateString) return 'Recent';
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffSec = Math.floor((now - date) / 1000);

            if (isNaN(diffSec)) return dateString;
            if (diffSec < 60) return 'Just now';
            if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
            if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
            if (diffSec < 172800) return 'Yesterday';
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        } catch (e) {
            return dateString;
        }
    }

    async function loadHistory() {
        if (!historyList) return;

        try {
            const response = await fetch('/api/reports');
            allAudits = await response.json();

            if (historyCountBadge) {
                historyCountBadge.textContent = `${allAudits.length} Audits`;
            }

            applyHistoryFilters();
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    }

    function applyHistoryFilters() {
        filteredAudits = allAudits.filter(report => {
            const pct = parseFloat(report.percentage || 0);

            // 1. Risk Filter
            if (activeFilter === 'clean' && pct >= 40) return false;
            if (activeFilter === 'moderate' && (pct < 40 || pct >= 70)) return false;
            if (activeFilter === 'critical' && pct < 70) return false;

            // 2. Search Query Filter
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                const fileNameMatch = (report.filename || '').toLowerCase().includes(q);
                const previewMatch = (report.preview || '').toLowerCase().includes(q);
                const idMatch = String(report.id).includes(q);
                if (!previewMatch && !idMatch && !fileNameMatch) return false;
            }

            return true;
        });

        currentHistoryPage = 1;
        renderHistoryPage();
    }

    function renderHistoryPage() {
        if (!historyList) return;

        historyList.innerHTML = '';

        if (filteredAudits.length === 0) {
            historyList.innerHTML = `
                <div class="history-empty-state">
                    <div class="history-empty-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    </div>
                    <div class="history-empty-title">No matching document audits</div>
                    <p class="history-empty-sub">${searchQuery ? `No results found for "${searchQuery}".` : 'No audits match the selected filter category.'}</p>
                    <button type="button" class="btn-reset-filters" id="resetHistoryFiltersBtn">Reset Filters</button>
                </div>
            `;

            const resetBtn = document.getElementById('resetHistoryFiltersBtn');
            if (resetBtn) {
                resetBtn.addEventListener('click', () => {
                    activeFilter = 'all';
                    searchQuery = '';
                    if (historySearchInput) historySearchInput.value = '';
                    if (historyClearSearch) historyClearSearch.style.display = 'none';
                    filterButtons.forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'all'));
                    applyHistoryFilters();
                });
            }

            if (historyPagination) historyPagination.style.display = 'none';
            return;
        }

        // Pagination math
        const totalPages = Math.ceil(filteredAudits.length / AUDITS_PER_PAGE);
        const startIdx = (currentHistoryPage - 1) * AUDITS_PER_PAGE;
        const pageItems = filteredAudits.slice(startIdx, startIdx + AUDITS_PER_PAGE);

        pageItems.forEach(report => {
            const pct = parseFloat(report.percentage || 0);

            let cardClass = 'card-safe';
            let tagClass = 'tag-safe';
            let barClass = 'bar-safe';
            let riskLabel = 'Clean';
            let scoreColor = 'var(--success)';

            if (pct >= 70) {
                cardClass = 'card-high';
                tagClass = 'tag-high';
                barClass = 'bar-high';
                riskLabel = 'High Risk';
                scoreColor = 'var(--danger)';
            } else if (pct >= 40) {
                cardClass = 'card-mid';
                tagClass = 'tag-mid';
                barClass = 'bar-mid';
                riskLabel = 'Moderate';
                scoreColor = 'var(--warning)';
            }

            const relativeTime = formatRelativeTime(report.timestamp);
            const totalSent = report.total_sentences || 0;
            const flaggedSent = report.flagged_sentences || 0;

            const card = document.createElement('div');
            card.className = `history-card ${cardClass}`;

            const docDisplayName = report.filename || `Audit #${report.id}`;

            card.innerHTML = `
                <div class="history-card-top">
                    <div class="history-doc-info">
                        <div class="history-doc-badge">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        </div>
                        <div style="min-width: 0; overflow: hidden;">
                            <span class="history-doc-title" title="${escapeHtml(docDisplayName)}">${escapeHtml(docDisplayName)}</span>
                            <span class="history-doc-date">${relativeTime}</span>
                        </div>
                    </div>
                    <div class="history-risk-tag ${tagClass}">
                        <span class="risk-dot"></span>
                        <span>${riskLabel}</span>
                    </div>
                </div>

                <div class="history-card-body">
                    <p class="history-preview">"${report.preview || 'Analyzed text document'}"</p>
                    
                    <div class="history-meta-row">
                        <span class="meta-item">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>
                            ${totalSent} sent.
                        </span>
                        <span class="meta-item ${flaggedSent > 0 ? 'flagged' : ''}">
                            ${flaggedSent} flagged
                        </span>
                    </div>

                    <div class="history-mini-bar">
                        <div class="mini-bar-fill ${barClass}" style="width: ${Math.min(100, Math.max(3, pct))}%"></div>
                    </div>
                </div>

                <div class="history-card-footer">
                    <div class="history-score-wrap">
                        <span class="history-score-val" style="color: ${scoreColor}">${pct.toFixed(1)}%</span>
                        <span class="history-score-label">Similarity</span>
                    </div>
                    <div class="history-actions">
                        <button type="button" class="btn-history-inspect" data-id="${report.id}" title="Load text into editor">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                            <span>Load</span>
                        </button>
                        <a href="/api/download/${report.id}" class="btn-history-pdf" title="Download certified PDF report">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                            <span>PDF</span>
                        </a>
                    </div>
                </div>
            `;

            // Bind Load button action
            const loadBtn = card.querySelector('.btn-history-inspect');
            if (loadBtn) {
                loadBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    loadAuditIntoEditor(report);
                });
            }

            historyList.appendChild(card);
        });

        // Update Pagination Controls
        if (historyPagination) {
            if (totalPages > 1) {
                historyPagination.style.display = 'flex';
                if (historyPageIndicator) {
                    historyPageIndicator.textContent = `Page ${currentHistoryPage} of ${totalPages} (${filteredAudits.length} audits)`;
                }
                if (historyPrevBtn) historyPrevBtn.disabled = currentHistoryPage <= 1;
                if (historyNextBtn) historyNextBtn.disabled = currentHistoryPage >= totalPages;
            } else {
                historyPagination.style.display = 'none';
            }
        }
    }

    function loadAuditIntoEditor(report) {
        if (!textInput) return;

        // Switch to single mode if not already
        if (currentMode !== 'single') {
            singleModeBtn.click();
        }

        // Fill text into editor
        textInput.value = report.full_text || report.preview;
        updateWordAndCharCount();

        // Show extraction badge with filename
        const docDisplayName = report.filename || `Audit #${report.id}`;
        const extractionBadge = document.getElementById('extractionBadge');
        const extractionFileName = document.getElementById('extractionFileName');
        if (extractionBadge && extractionFileName) {
            extractionBadge.style.display = 'inline-flex';
            extractionFileName.textContent = `Loaded from ${docDisplayName}`;
        }

        if (statusHintText) {
            statusHintText.textContent = `Loaded content from ${docDisplayName} (${(report.percentage || 0).toFixed(1)}% score). Ready to re-analyze.`;
        }

        // Smooth scroll up to the workspace editor
        const singleInput = document.getElementById('singleInputSection');
        if (singleInput) {
            singleInput.scrollIntoView({ behavior: 'smooth', block: 'start' });
            textInput.focus();
        }
    }

    // Bind Search Input
    if (historySearchInput) {
        historySearchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.trim();
            if (historyClearSearch) {
                historyClearSearch.style.display = searchQuery ? 'block' : 'none';
            }
            applyHistoryFilters();
        });
    }

    if (historyClearSearch) {
        historyClearSearch.addEventListener('click', () => {
            searchQuery = '';
            if (historySearchInput) {
                historySearchInput.value = '';
                historySearchInput.focus();
            }
            historyClearSearch.style.display = 'none';
            applyHistoryFilters();
        });
    }

    // Bind Filter Buttons
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.getAttribute('data-filter') || 'all';
            applyHistoryFilters();
        });
    });

    // Bind Pagination Buttons
    if (historyPrevBtn) {
        historyPrevBtn.addEventListener('click', () => {
            if (currentHistoryPage > 1) {
                currentHistoryPage--;
                renderHistoryPage();
                document.querySelector('.history-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    if (historyNextBtn) {
        historyNextBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredAudits.length / AUDITS_PER_PAGE);
            if (currentHistoryPage < totalPages) {
                currentHistoryPage++;
                renderHistoryPage();
                document.querySelector('.history-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    // =========================================================================
    // VERSION CONTROL & DOCUMENT EVOLUTION AUDIT MODULE
    // =========================================================================
    let vcCurrentUser = null;
    let vcGroupsCache = [];
    let vcCurrentGroup = null;
    let vcCurrentComparison = null;

    // Elements
    const navAuthWidget = document.getElementById('navAuthWidget');
    const btnNavAuth = document.getElementById('btnNavAuth');
    const navAuthLabel = document.getElementById('navAuthLabel');
    const btnNavLogout = document.getElementById('btnNavLogout');

    const vcAuthGate = document.getElementById('vcAuthGate');
    const tabVcLogin = document.getElementById('tabVcLogin');
    const tabVcRegister = document.getElementById('tabVcRegister');
    const vcLoginForm = document.getElementById('vcLoginForm');
    const vcLoginEmail = document.getElementById('vcLoginEmail');
    const vcLoginPassword = document.getElementById('vcLoginPassword');
    const vcLoginError = document.getElementById('vcLoginError');
    const btnVcSubmitLogin = document.getElementById('btnVcSubmitLogin');

    const vcRegisterForm = document.getElementById('vcRegisterForm');
    const vcRegName = document.getElementById('vcRegName');
    const vcRegEmail = document.getElementById('vcRegEmail');
    const vcRegPassword = document.getElementById('vcRegPassword');
    const vcRegError = document.getElementById('vcRegError');
    const btnVcSubmitRegister = document.getElementById('btnVcSubmitRegister');

    const vcDashboard = document.getElementById('vcDashboard');
    const vcUserName = document.getElementById('vcUserName');
    const vcUserEmail = document.getElementById('vcUserEmail');
    const vcUserAvatar = document.getElementById('vcUserAvatar');
    const btnVcLogout = document.getElementById('btnVcLogout');

    const vcStatGroups = document.getElementById('vcStatGroups');
    const vcStatVersions = document.getElementById('vcStatVersions');
    const vcStatComparisons = document.getElementById('vcStatComparisons');

    const vcGroupsContainer = document.getElementById('vcGroupsContainer');
    const vcGroupSearch = document.getElementById('vcGroupSearch');
    const vcGroupsList = document.getElementById('vcGroupsList');
    const btnOpenNewGroupModal = document.getElementById('btnOpenNewGroupModal');

    const vcGroupDetailContainer = document.getElementById('vcGroupDetailContainer');
    const btnBackToGroups = document.getElementById('btnBackToGroups');
    const btnUploadNextVersion = document.getElementById('btnUploadNextVersion');
    const vcDetailGroupTitle = document.getElementById('vcDetailGroupTitle');
    const vcDetailGroupMeta = document.getElementById('vcDetailGroupMeta');
    const vcVersionsList = document.getElementById('vcVersionsList');
    const vcSelectV1 = document.getElementById('vcSelectV1');
    const vcSelectV2 = document.getElementById('vcSelectV2');
    const btnRunArbitraryCompare = document.getElementById('btnRunArbitraryCompare');
    const vcGroupComparisonsList = document.getElementById('vcGroupComparisonsList');

    const vcComparisonContainer = document.getElementById('vcComparisonContainer');
    const btnBackToGroupDetail = document.getElementById('btnBackToGroupDetail');
    const btnDownloadVcReport = document.getElementById('btnDownloadVcReport');
    const vcCompDocTitle = document.getElementById('vcCompDocTitle');
    const vcCompVersionsSubtitle = document.getElementById('vcCompVersionsSubtitle');
    const vcKpiSimVal = document.getElementById('vcKpiSimVal');
    const vcKpiSimBar = document.getElementById('vcKpiSimBar');
    const vcKpiMatchVal = document.getElementById('vcKpiMatchVal');
    const vcKpiMatchBar = document.getElementById('vcKpiMatchBar');

    // Modal Version AI Elements
    const modalVersionAi = document.getElementById('modalVersionAi');
    const btnCloseVersionAiModal = document.getElementById('btnCloseVersionAiModal');
    const btnCloseVersionAiModalBtn = document.getElementById('btnCloseVersionAiModalBtn');
    const verAiModalTitle = document.getElementById('verAiModalTitle');
    const verAiModalSubtitle = document.getElementById('verAiModalSubtitle');
    const verAiVal = document.getElementById('verAiVal');
    const verHumanVal = document.getElementById('verHumanVal');
    const verAiBarFill = document.getElementById('verAiBarFill');
    const verAiHumanLegend = document.getElementById('verAiHumanLegend');
    const verAiAiLegend = document.getElementById('verAiAiLegend');
    const verAiClassPill = document.getElementById('verAiClassPill');
    const verAiConfPill = document.getElementById('verAiConfPill');
    const verAiWordsPill = document.getElementById('verAiWordsPill');
    const verAiAssessmentText = document.getElementById('verAiAssessmentText');
    const btnDownloadVersionAiReport = document.getElementById('btnDownloadVersionAiReport');

    const vcStatUnchanged = document.getElementById('vcStatUnchanged');
    const vcStatUnchangedPct = document.getElementById('vcStatUnchangedPct');
    const vcStatModified = document.getElementById('vcStatModified');
    const vcStatModifiedPct = document.getElementById('vcStatModifiedPct');
    const vcStatAdded = document.getElementById('vcStatAdded');
    const vcStatAddedPct = document.getElementById('vcStatAddedPct');
    const vcStatRemoved = document.getElementById('vcStatRemoved');
    const vcStatRemovedPct = document.getElementById('vcStatRemovedPct');

    // Modals
    const modalNewGroup = document.getElementById('modalNewGroup');
    const btnCloseNewGroupModal = document.getElementById('btnCloseNewGroupModal');
    const btnCancelNewGroup = document.getElementById('btnCancelNewGroup');
    const formNewGroup = document.getElementById('formNewGroup');
    const newGroupTitle = document.getElementById('newGroupTitle');
    const dropzoneNewGroup = document.getElementById('dropzoneNewGroup');
    const fileNewGroup = document.getElementById('fileNewGroup');
    const labelNewGroupFile = document.getElementById('labelNewGroupFile');
    const errorNewGroup = document.getElementById('errorNewGroup');

    const modalUploadVersion = document.getElementById('modalUploadVersion');
    const btnCloseUploadModal = document.getElementById('btnCloseUploadModal');
    const btnCancelUploadModal = document.getElementById('btnCancelUploadModal');
    const formUploadVersion = document.getElementById('formUploadVersion');
    const uploadVersionGroupId = document.getElementById('uploadVersionGroupId');
    const infoUploadModalGroup = document.getElementById('infoUploadModalGroup');
    const dropzoneUploadVersion = document.getElementById('dropzoneUploadVersion');
    const fileUploadVersion = document.getElementById('fileUploadVersion');
    const labelUploadVersionFile = document.getElementById('labelUploadVersionFile');
    const selectCompareWithVer = document.getElementById('selectCompareWithVer');
    const errorUploadVersion = document.getElementById('errorUploadVersion');

    // Check Auth Status
    async function checkVcAuthStatus() {
        try {
            const resp = await fetch('/api/auth/status');
            const data = await resp.json();
            if (data.authenticated && data.user) {
                vcCurrentUser = data.user;
                if (navAuthLabel) navAuthLabel.textContent = data.user.name || data.user.email;
                if (btnNavLogout) btnNavLogout.style.display = 'inline-flex';
                if (vcUserName) vcUserName.textContent = data.user.name || 'User';
                if (vcUserEmail) vcUserEmail.textContent = data.user.email;
                if (vcUserAvatar) vcUserAvatar.textContent = (data.user.name || data.user.email || 'U')[0].toUpperCase();

                if (currentMode === 'version') {
                    if (vcAuthGate) vcAuthGate.style.display = 'none';
                    if (vcDashboard) vcDashboard.style.display = 'block';
                    if (vcGroupDetailContainer) vcGroupDetailContainer.style.display = 'none';
                    if (vcComparisonContainer) vcComparisonContainer.style.display = 'none';
                    if (vcGroupsContainer) vcGroupsContainer.style.display = 'block';
                    vcCurrentGroup = null;
                    vcCurrentComparison = null;
                    loadVcGroups();
                }
            } else {
                vcCurrentUser = null;
                if (navAuthLabel) navAuthLabel.textContent = 'Sign In';
                if (btnNavLogout) btnNavLogout.style.display = 'none';

                if (currentMode === 'version') {
                    if (vcAuthGate) vcAuthGate.style.display = 'block';
                    if (vcDashboard) vcDashboard.style.display = 'none';
                }
            }
        } catch (err) {
            console.error('VC auth check failed:', err);
        }
    }

    // Auth Switchers
    if (tabVcLogin) {
        tabVcLogin.addEventListener('click', () => {
            tabVcLogin.classList.add('active');
            if (tabVcRegister) tabVcRegister.classList.remove('active');
            if (vcLoginForm) vcLoginForm.style.display = 'flex';
            if (vcRegisterForm) vcRegisterForm.style.display = 'none';
            if (vcLoginError) vcLoginError.style.display = 'none';
        });
    }

    if (tabVcRegister) {
        tabVcRegister.addEventListener('click', () => {
            tabVcRegister.classList.add('active');
            if (tabVcLogin) tabVcLogin.classList.remove('active');
            if (vcRegisterForm) vcRegisterForm.style.display = 'flex';
            if (vcLoginForm) vcLoginForm.style.display = 'none';
            if (vcRegError) vcRegError.style.display = 'none';
        });
    }

    // Submit Login
    if (vcLoginForm) {
        vcLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (vcLoginError) vcLoginError.style.display = 'none';
            const email = vcLoginEmail.value.trim();
            const password = vcLoginPassword.value;
            if (!email || !password) return;

            try {
                if (btnVcSubmitLogin) btnVcSubmitLogin.disabled = true;
                const resp = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await resp.json();
                if (resp.ok && data.user) {
                    vcLoginForm.reset();
                    await checkVcAuthStatus();
                } else {
                    if (vcLoginError) {
                        vcLoginError.textContent = data.error || 'Authentication failed.';
                        vcLoginError.style.display = 'block';
                    }
                }
            } catch (err) {
                if (vcLoginError) {
                    vcLoginError.textContent = 'Server connection error: ' + err.message;
                    vcLoginError.style.display = 'block';
                }
            } finally {
                if (btnVcSubmitLogin) btnVcSubmitLogin.disabled = false;
            }
        });
    }

    // Submit Register
    if (vcRegisterForm) {
        vcRegisterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (vcRegError) vcRegError.style.display = 'none';
            const name = vcRegName.value.trim();
            const email = vcRegEmail.value.trim();
            const password = vcRegPassword.value;
            if (!name || !email || !password) return;

            try {
                if (btnVcSubmitRegister) btnVcSubmitRegister.disabled = true;
                const resp = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });
                const data = await resp.json();
                if (resp.ok && data.user) {
                    vcRegisterForm.reset();
                    await checkVcAuthStatus();
                } else {
                    if (vcRegError) {
                        vcRegError.textContent = data.error || 'Registration failed.';
                        vcRegError.style.display = 'block';
                    }
                }
            } catch (err) {
                if (vcRegError) {
                    vcRegError.textContent = 'Server connection error: ' + err.message;
                    vcRegError.style.display = 'block';
                }
            } finally {
                if (btnVcSubmitRegister) btnVcSubmitRegister.disabled = false;
            }
        });
    }

    // Logout
    async function handleVcLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch (e) {
            console.error('Logout error:', e);
        }
        vcCurrentUser = null;
        await checkVcAuthStatus();
    }

    if (btnVcLogout) btnVcLogout.addEventListener('click', handleVcLogout);
    if (btnNavLogout) btnNavLogout.addEventListener('click', handleVcLogout);

    if (btnNavAuth) {
        btnNavAuth.addEventListener('click', () => {
            activateMode('version');
        });
    }

    // Load Document Groups
    async function loadVcGroups() {
        if (!vcCurrentUser) return;
        try {
            const resp = await fetch('/api/vc/groups');
            const data = await resp.json();
            if (!resp.ok) {
                if (resp.status === 401) checkVcAuthStatus();
                return;
            }

            vcGroupsCache = data.groups || [];
            if (vcStatGroups) vcStatGroups.textContent = data.total_groups || vcGroupsCache.length;
            if (vcStatVersions) vcStatVersions.textContent = data.total_versions || 0;
            if (vcStatComparisons) vcStatComparisons.textContent = data.total_comparisons || 0;

            renderVcGroups(vcGroupsCache);
        } catch (err) {
            console.error('Failed to load VC groups:', err);
        }
    }

    function renderVcGroups(groups) {
        if (!vcGroupsList) return;
        if (!groups || groups.length === 0) {
            vcGroupsList.innerHTML = `
                <div class="history-empty-state">
                    <div class="history-empty-icon">📁</div>
                    <div class="history-empty-title">No Document Repositories Yet</div>
                    <p class="history-empty-sub">Create your first repository with an initial version to track changes and evolution over time.</p>
                    <button type="button" class="btn-hero-action btn-empty-hero" id="btnEmptyCreateGroup">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        <span>Create First Repository</span>
                    </button>
                </div>
            `;
            const emptyBtn = document.getElementById('btnEmptyCreateGroup');
            if (emptyBtn) emptyBtn.addEventListener('click', openNewGroupModal);
            return;
        }

        let html = '';
        groups.forEach(g => {
            const vCount = g.version_count || 1;
            const vText = `${vCount} Version${vCount === 1 ? '' : 's'}`;
            html += `
                <div class="vc-group-card" data-id="${g.id}">
                    <div>
                        <div class="vc-group-card-header">
                            <h4 class="vc-group-card-title">${escapeHtml(g.name)}</h4>
                            <span class="vc-group-card-badge">${vText}</span>
                        </div>
                        <div class="vc-group-card-meta">
                            <div><strong>Latest File:</strong> ${escapeHtml(g.latest_filename || '—')}</div>
                            <div><strong>Updated:</strong> ${g.updated_at || g.created_at}</div>
                        </div>
                    </div>
                    <div class="vc-group-card-actions">
                        <button type="button" class="btn-card-action btn-open-group" data-id="${g.id}">
                            <span>Open Repository &rarr;</span>
                        </button>
                        <button type="button" class="btn-card-del btn-del-group" data-id="${g.id}" title="Delete repository">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>
                    </div>
                </div>
            `;
        });
        vcGroupsList.innerHTML = html;

        // Wire group cards
        vcGroupsList.querySelectorAll('.btn-open-group').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const gid = e.currentTarget.getAttribute('data-id');
                openGroupDetail(gid);
            });
        });

        vcGroupsList.querySelectorAll('.vc-group-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('button')) return;
                const gid = card.getAttribute('data-id');
                openGroupDetail(gid);
            });
        });

        vcGroupsList.querySelectorAll('.btn-del-group').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const gid = e.currentTarget.getAttribute('data-id');
                if (!confirm('Are you sure you want to permanently delete this document repository and ALL its version snapshots?')) return;

                try {
                    const resp = await fetch(`/api/vc/groups/${gid}`, { method: 'DELETE' });
                    if (resp.ok) {
                        loadVcGroups();
                    } else {
                        const d = await resp.json();
                        alert(d.error || 'Failed to delete repository.');
                    }
                } catch (err) {
                    alert('Delete failed: ' + err.message);
                }
            });
        });
    }

    // Filter Groups
    if (vcGroupSearch) {
        vcGroupSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if (!query) {
                renderVcGroups(vcGroupsCache);
                return;
            }
            const filtered = vcGroupsCache.filter(g =>
                (g.name && g.name.toLowerCase().includes(query)) ||
                (g.latest_filename && g.latest_filename.toLowerCase().includes(query))
            );
            renderVcGroups(filtered);
        });
    }

    // Modal: New Group
    function openNewGroupModal() {
        if (formNewGroup) formNewGroup.reset();
        if (labelNewGroupFile) labelNewGroupFile.textContent = 'Click to browse or drop .pdf, .docx, .txt';
        if (errorNewGroup) errorNewGroup.style.display = 'none';
        if (modalNewGroup) modalNewGroup.style.display = 'flex';
    }

    function closeNewGroupModal() {
        if (modalNewGroup) modalNewGroup.style.display = 'none';
    }

    if (btnOpenNewGroupModal) btnOpenNewGroupModal.addEventListener('click', openNewGroupModal);
    if (btnCloseNewGroupModal) btnCloseNewGroupModal.addEventListener('click', closeNewGroupModal);
    if (btnCancelNewGroup) btnCancelNewGroup.addEventListener('click', closeNewGroupModal);

    if (dropzoneNewGroup && fileNewGroup) {
        dropzoneNewGroup.addEventListener('click', () => fileNewGroup.click());
        fileNewGroup.addEventListener('change', () => {
            if (fileNewGroup.files.length > 0) {
                labelNewGroupFile.textContent = fileNewGroup.files[0].name;
            }
        });
        dropzoneNewGroup.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzoneNewGroup.classList.add('dragover');
        });
        dropzoneNewGroup.addEventListener('dragleave', () => dropzoneNewGroup.classList.remove('dragover'));
        dropzoneNewGroup.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzoneNewGroup.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileNewGroup.files = e.dataTransfer.files;
                labelNewGroupFile.textContent = e.dataTransfer.files[0].name;
            }
        });
    }

    if (formNewGroup) {
        formNewGroup.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (errorNewGroup) errorNewGroup.style.display = 'none';
            const title = newGroupTitle.value.trim();
            const file = fileNewGroup.files[0];
            if (!title || !file) {
                if (errorNewGroup) {
                    errorNewGroup.textContent = 'Please provide a repository name and an initial document file.';
                    errorNewGroup.style.display = 'block';
                }
                return;
            }

            const submitBtn = document.getElementById('btnSubmitNewGroup');
            try {
                if (submitBtn) submitBtn.disabled = true;
                const fd = new FormData();
                fd.append('name', title);
                fd.append('file', file);

                const resp = await fetch('/api/vc/groups', {
                    method: 'POST',
                    body: fd
                });
                const data = await resp.json();
                if (resp.ok && data.group_id) {
                    closeNewGroupModal();
                    await loadVcGroups();
                    openGroupDetail(data.group_id);
                } else {
                    if (errorNewGroup) {
                        errorNewGroup.textContent = data.error || 'Failed to create repository.';
                        errorNewGroup.style.display = 'block';
                    }
                }
            } catch (err) {
                if (errorNewGroup) {
                    errorNewGroup.textContent = 'Upload failed: ' + err.message;
                    errorNewGroup.style.display = 'block';
                }
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // Open Group Detail
    async function openGroupDetail(groupId) {
        try {
            const resp = await fetch(`/api/vc/groups/${groupId}`);
            const data = await resp.json();
            if (!resp.ok) {
                alert(data.error || 'Failed to load group details.');
                return;
            }

            vcCurrentGroup = data.group;
            if (vcGroupsContainer) vcGroupsContainer.style.display = 'none';
            if (vcComparisonContainer) vcComparisonContainer.style.display = 'none';
            if (vcGroupDetailContainer) vcGroupDetailContainer.style.display = 'block';

            if (vcDetailGroupTitle) vcDetailGroupTitle.textContent = data.group.name;
            if (vcDetailGroupMeta) {
                vcDetailGroupMeta.textContent = `Created: ${data.group.created_at} • ${data.versions.length} Version Snapshots`;
            }

            // Render Timeline
            renderVersionsTimeline(data.versions);

            // Populate selectors for arbitrary comparison
            populateCompareSelectors(data.versions);

            // Render comparison history
            renderGroupComparisons(data.comparisons);
        } catch (err) {
            console.error('Error opening group detail:', err);
        }
    }

    function renderVersionsTimeline(versions) {
        if (!vcVersionsList) return;
        if (!versions || versions.length === 0) {
            vcVersionsList.innerHTML = '<p class="vc-empty-hint">No versions found.</p>';
            return;
        }

        let html = '';
        versions.forEach(v => {
            const sizeStr = v.file_size ? `${(v.file_size / 1024).toFixed(1)} KB` : '';
            const wordsStr = v.word_count ? `${v.word_count} words` : '';
            const sentencesStr = v.sentence_count ? `${v.sentence_count} sentences` : '';
            const metaParts = [sizeStr, wordsStr, sentencesStr, v.created_at].filter(Boolean).join(' • ');

            let aiBadgeHtml = '';
            if (v.ai_probability !== null && v.ai_probability !== undefined) {
                const aiProb = typeof v.ai_probability === 'number' ? v.ai_probability : parseFloat(v.ai_probability || 0);
                const isAi = aiProb >= 50;
                const aiClass = isAi ? 'ai-pill-ai' : 'ai-pill-human';
                const aiIcon = isAi ? '🤖' : '✍️';
                const label = v.ai_classification || (isAi ? 'Likely AI' : 'Likely Human');
                aiBadgeHtml = `<span class="vc-version-ai-pill ${aiClass}" title="RoBERTa AI Probability: ${aiProb.toFixed(1)}%">${aiIcon} ${aiProb.toFixed(1)}% AI • ${escapeHtml(label)}</span>`;
            }

            html += `
                <div class="vc-version-card">
                    <div class="vc-version-left">
                        <div class="vc-version-badge">V${v.version_number}</div>
                        <div>
                            <div class="vc-version-num">Version ${v.version_number} ${aiBadgeHtml}</div>
                            <div class="vc-version-filename">${escapeHtml(v.filename)}</div>
                            <div class="vc-version-meta">${metaParts}</div>
                        </div>
                    </div>
                    <div class="vc-version-actions">
                        <button type="button" class="btn-version-ai btn-show-version-ai" data-id="${v.id}" title="View AI Content Analysis for Version ${v.version_number}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8.01" y2="16"/><line x1="16" y1="16" x2="16.01" y2="16"/></svg>
                            <span>AI Analysis</span>
                        </button>
                        <a href="/api/vc/versions/${v.id}/download" class="btn-version-dl" title="Download original file">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                            <span>Download</span>
                        </a>
                        ${versions.length > 1 ? `
                            <button type="button" class="btn-version-del btn-del-version" data-id="${v.id}" title="Delete this version">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        vcVersionsList.innerHTML = html;

        // Wire AI analysis buttons
        vcVersionsList.querySelectorAll('.btn-show-version-ai').forEach(btn => {
            btn.addEventListener('click', () => {
                const vid = btn.getAttribute('data-id');
                const targetVer = versions.find(item => String(item.id) === String(vid));
                if (targetVer) {
                    showVersionAiModal(targetVer);
                }
            });
        });

        // Wire delete version buttons
        vcVersionsList.querySelectorAll('.btn-del-version').forEach(btn => {
            btn.addEventListener('click', async () => {
                const vid = btn.getAttribute('data-id');
                if (!confirm('Are you sure you want to delete this version snapshot?')) return;
                try {
                    const resp = await fetch(`/api/vc/versions/${vid}`, { method: 'DELETE' });
                    if (resp.ok) {
                        openGroupDetail(vcCurrentGroup.id);
                    } else {
                        const d = await resp.json();
                        alert(d.error || 'Failed to delete version.');
                    }
                } catch (err) {
                    alert('Error: ' + err.message);
                }
            });
        });
    }

    function showVersionAiModal(ver) {
        if (!modalVersionAi) return;
        const ai = ver.ai_analysis || {};
        const aiProb = typeof ver.ai_probability === 'number' ? ver.ai_probability : (ai.ai_probability || 0);
        const humanProb = typeof ai.human_probability === 'number' ? ai.human_probability : Math.max(0, 100 - aiProb);
        const classification = ai.classification || ver.ai_classification || (aiProb >= 50 ? 'Likely AI-generated' : 'Likely human-written');
        const confidence = ai.confidence || 'Moderate';
        const wordCount = ai.word_count || ver.word_count || 'Analyzed';
        const assessment = ai.assessment_detail || (
            aiProb >= 70 ? 'The sequence patterns, token distributions, and structural style strongly match patterns identified by the neural classifier as machine-generated text.' :
            (aiProb <= 30 ? 'The sequence patterns, structural style, and syntactic variance strongly align with patterns identified by the neural classifier as organic human writing.' :
            'The document exhibits mixed stylistic signals, showing traits common to both human writing and AI-assisted generation.')
        );

        if (verAiModalTitle) verAiModalTitle.textContent = `Version ${ver.version_number} AI Content Analysis`;
        if (verAiModalSubtitle) verAiModalSubtitle.textContent = `${ver.filename} • Analyzed via RoBERTa (HC3 benchmark)`;
        if (verAiVal) verAiVal.textContent = `${aiProb.toFixed(1)}%`;
        if (verHumanVal) verHumanVal.textContent = `${humanProb.toFixed(1)}%`;
        if (verAiBarFill) verAiBarFill.style.width = `${Math.min(100, Math.max(0, aiProb))}%`;
        if (verAiHumanLegend) verAiHumanLegend.textContent = `Organic Human: ${humanProb.toFixed(1)}%`;
        if (verAiAiLegend) verAiAiLegend.textContent = `Synthetic AI: ${aiProb.toFixed(1)}%`;

        if (verAiClassPill) {
            const isAi = aiProb >= 50;
            verAiClassPill.textContent = (isAi ? '🤖 ' : '✍️ ') + classification;
            verAiClassPill.className = `ai-pill ${isAi ? 'ai-pill-ai' : 'ai-pill-human'}`;
        }
        if (verAiConfPill) verAiConfPill.textContent = `${confidence} Confidence`;
        if (verAiWordsPill) verAiWordsPill.textContent = `${typeof wordCount === 'number' ? wordCount.toLocaleString() : wordCount} Words`;
        if (verAiAssessmentText) verAiAssessmentText.textContent = assessment;
        if (btnDownloadVersionAiReport) btnDownloadVersionAiReport.href = `/api/vc/versions/${ver.id}/ai-report`;

        modalVersionAi.style.display = 'flex';
    }

    if (btnCloseVersionAiModal && modalVersionAi) {
        btnCloseVersionAiModal.addEventListener('click', () => {
            modalVersionAi.style.display = 'none';
        });
    }
    if (btnCloseVersionAiModalBtn && modalVersionAi) {
        btnCloseVersionAiModalBtn.addEventListener('click', () => {
            modalVersionAi.style.display = 'none';
        });
    }
    if (modalVersionAi) {
        modalVersionAi.addEventListener('click', (e) => {
            if (e.target === modalVersionAi) {
                modalVersionAi.style.display = 'none';
            }
        });
    }

    function populateCompareSelectors(versions) {
        if (!vcSelectV1 || !vcSelectV2) return;
        vcSelectV1.innerHTML = '';
        vcSelectV2.innerHTML = '';

        if (!versions || versions.length < 2) {
            vcSelectV1.innerHTML = '<option value="">Need at least 2 versions</option>';
            vcSelectV2.innerHTML = '<option value="">Need at least 2 versions</option>';
            if (btnRunArbitraryCompare) btnRunArbitraryCompare.disabled = true;
            return;
        }

        if (btnRunArbitraryCompare) btnRunArbitraryCompare.disabled = false;

        versions.forEach((v) => {
            const opt1 = document.createElement('option');
            opt1.value = v.id;
            opt1.textContent = `V${v.version_number}: ${v.filename}`;
            vcSelectV1.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = v.id;
            opt2.textContent = `V${v.version_number}: ${v.filename}`;
            vcSelectV2.appendChild(opt2);
        });

        // Set default: V1 = first version, V2 = latest version
        vcSelectV1.selectedIndex = 0;
        vcSelectV2.selectedIndex = versions.length - 1;
    }

    function renderGroupComparisons(comparisons) {
        if (!vcGroupComparisonsList) return;
        if (!comparisons || comparisons.length === 0) {
            vcGroupComparisonsList.innerHTML = '<p class="vc-empty-hint" style="padding: 1.25rem; color: var(--text-muted); font-size: 0.88rem;">No version comparisons generated yet. Use the comparison toolbar above or upload next version with auto-comparison.</p>';
            return;
        }

        let html = `
            <table class="vc-table">
                <thead>
                    <tr>
                        <th>Baseline</th>
                        <th>Revision</th>
                        <th>Version Sim.</th>
                        <th>Content Match</th>
                        <th>Comparison Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        comparisons.forEach(c => {
            const v1Num = c.v1_num !== undefined ? c.v1_num : (c.prev_version_number !== undefined ? c.prev_version_number : 1);
            const v1Name = c.v1_name || c.prev_filename || 'Baseline';
            const v2Num = c.v2_num !== undefined ? c.v2_num : (c.new_version_number !== undefined ? c.new_version_number : 2);
            const v2Name = c.v2_name || c.new_filename || 'Revision';
            const simPct = (c.version_similarity || 0).toFixed(1) + '%';
            const matchPct = (c.matching_percentage || 0).toFixed(1) + '%';
            html += `
                <tr>
                    <td><strong>V${v1Num}</strong> (${escapeHtml(v1Name)})</td>
                    <td><strong>V${v2Num}</strong> (${escapeHtml(v2Name)})</td>
                    <td><span class="badge-status badge-status-modified">${simPct}</span></td>
                    <td><span class="badge-status badge-status-unchanged">${matchPct}</span></td>
                    <td>${c.created_at}</td>
                    <td>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <button type="button" class="btn-card-action btn-inspect-comp" data-id="${c.id}">
                                Inspect Diff
                            </button>
                            <a href="/api/vc/comparisons/${c.id}/report" class="btn-version-dl" title="Download Official PDF Audit Report">
                                <span>PDF</span>
                            </a>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        vcGroupComparisonsList.innerHTML = html;

        vcGroupComparisonsList.querySelectorAll('.btn-inspect-comp').forEach(btn => {
            btn.addEventListener('click', () => {
                const cid = btn.getAttribute('data-id');
                loadComparisonById(cid);
            });
        });
    }

    // Modal: Upload Next Version
    function openUploadVersionModal() {
        if (!vcCurrentGroup) return;
        if (formUploadVersion) formUploadVersion.reset();
        if (uploadVersionGroupId) uploadVersionGroupId.value = vcCurrentGroup.id;
        if (infoUploadModalGroup) infoUploadModalGroup.textContent = `Repository: ${vcCurrentGroup.name}`;
        if (labelUploadVersionFile) labelUploadVersionFile.textContent = 'Click to browse or drop .pdf, .docx, .txt';
        if (errorUploadVersion) errorUploadVersion.style.display = 'none';

        // Populate compare dropdown
        if (selectCompareWithVer) {
            selectCompareWithVer.innerHTML = '<option value="">Do not compare now</option>';
            if (vcCurrentGroup && vcVersionsList) {
                // Fetch current versions from cache or server
                fetch(`/api/vc/groups/${vcCurrentGroup.id}`)
                    .then(r => r.json())
                    .then(d => {
                        if (d.versions) {
                            d.versions.forEach(v => {
                                const opt = document.createElement('option');
                                opt.value = v.id;
                                opt.textContent = `Compare with V${v.version_number}: ${v.filename}`;
                                selectCompareWithVer.appendChild(opt);
                            });
                            // Select latest
                            if (d.versions.length > 0) {
                                selectCompareWithVer.selectedIndex = d.versions.length;
                            }
                        }
                    });
            }
        }

        if (modalUploadVersion) modalUploadVersion.style.display = 'flex';
    }

    function closeUploadVersionModal() {
        if (modalUploadVersion) modalUploadVersion.style.display = 'none';
    }

    if (btnUploadNextVersion) btnUploadNextVersion.addEventListener('click', openUploadVersionModal);
    if (btnCloseUploadModal) btnCloseUploadModal.addEventListener('click', closeUploadVersionModal);
    if (btnCancelUploadModal) btnCancelUploadModal.addEventListener('click', closeUploadVersionModal);

    if (dropzoneUploadVersion && fileUploadVersion) {
        dropzoneUploadVersion.addEventListener('click', () => fileUploadVersion.click());
        fileUploadVersion.addEventListener('change', () => {
            if (fileUploadVersion.files.length > 0) {
                labelUploadVersionFile.textContent = fileUploadVersion.files[0].name;
            }
        });
        dropzoneUploadVersion.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzoneUploadVersion.classList.add('dragover');
        });
        dropzoneUploadVersion.addEventListener('dragleave', () => dropzoneUploadVersion.classList.remove('dragover'));
        dropzoneUploadVersion.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzoneUploadVersion.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileUploadVersion.files = e.dataTransfer.files;
                labelUploadVersionFile.textContent = e.dataTransfer.files[0].name;
            }
        });
    }

    if (formUploadVersion) {
        formUploadVersion.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (errorUploadVersion) errorUploadVersion.style.display = 'none';
            const file = fileUploadVersion.files[0];
            if (!file) {
                if (errorUploadVersion) {
                    errorUploadVersion.textContent = 'Please choose a document file to upload.';
                    errorUploadVersion.style.display = 'block';
                }
                return;
            }

            const submitBtn = document.getElementById('btnSubmitUploadVersion');
            try {
                if (submitBtn) submitBtn.disabled = true;
                const fd = new FormData();
                fd.append('file', file);
                if (selectCompareWithVer && selectCompareWithVer.value) {
                    fd.append('compare_with_version_id', selectCompareWithVer.value);
                }

                const resp = await fetch(`/api/vc/groups/${vcCurrentGroup.id}/versions`, {
                    method: 'POST',
                    body: fd
                });
                const data = await resp.json();
                if (resp.ok) {
                    closeUploadVersionModal();
                    if (data.comparison) {
                        renderComparisonResult(data.comparison);
                    } else {
                        openGroupDetail(vcCurrentGroup.id);
                    }
                } else {
                    if (errorUploadVersion) {
                        errorUploadVersion.textContent = data.error || 'Upload failed.';
                        errorUploadVersion.style.display = 'block';
                    }
                }
            } catch (err) {
                if (errorUploadVersion) {
                    errorUploadVersion.textContent = 'Error: ' + err.message;
                    errorUploadVersion.style.display = 'block';
                }
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // Run Arbitrary Compare
    if (btnRunArbitraryCompare) {
        btnRunArbitraryCompare.addEventListener('click', async () => {
            const v1 = vcSelectV1.value;
            const v2 = vcSelectV2.value;
            if (!v1 || !v2) {
                alert('Please select two versions to compare.');
                return;
            }
            if (v1 === v2) {
                alert('Please select two different versions to compare.');
                return;
            }

            try {
                btnRunArbitraryCompare.disabled = true;
                const resp = await fetch('/api/vc/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ v1_id: parseInt(v1, 10), v2_id: parseInt(v2, 10) })
                });

                let data = null;
                const ct = resp.headers.get('content-type') || '';
                if (ct.includes('application/json')) {
                    data = await resp.json();
                }

                if (resp.ok && data && data.comparison) {
                    renderComparisonResult(data.comparison);
                } else {
                    alert((data && data.error) || `Comparison failed (HTTP ${resp.status}).`);
                }
            } catch (err) {
                alert('Error running comparison: ' + err.message);
            } finally {
                btnRunArbitraryCompare.disabled = false;
            }
        });
    }

    // Load Comparison by ID
    async function loadComparisonById(comparisonId) {
        try {
            const resp = await fetch(`/api/vc/comparisons/${comparisonId}`);
            let data = null;
            const ct = resp.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                data = await resp.json();
            }

            if (resp.ok && data && data.comparison) {
                renderComparisonResult(data.comparison);
            } else {
                alert((data && data.error) || `Failed to load comparison (HTTP ${resp.status}).`);
            }
        } catch (err) {
            alert('Error loading comparison: ' + err.message);
        }
    }

    // Render Comparison Result View
    function renderComparisonResult(compData) {
        vcCurrentComparison = compData;
        if (vcGroupDetailContainer) vcGroupDetailContainer.style.display = 'none';
        if (vcGroupsContainer) vcGroupsContainer.style.display = 'none';
        if (vcComparisonContainer) vcComparisonContainer.style.display = 'block';

        const prevV = compData.prev_version || compData.v1_info || {};
        const newV = compData.new_version || compData.v2_info || {};

        if (vcCompDocTitle) {
            vcCompDocTitle.textContent = (vcCurrentGroup ? vcCurrentGroup.name : (compData.group_name || 'Document Evolution Audit'));
        }
        if (vcCompVersionsSubtitle) {
            vcCompVersionsSubtitle.textContent = `Baseline V${prevV.version_number || 1} (${prevV.filename || 'Version 1'}) ↔ Revision V${newV.version_number || 2} (${newV.filename || 'Version 2'}) • Evaluated ${compData.created_at || 'Just now'}`;
        }

        // Dual KPIs
        const simVal = (compData.version_similarity || 0).toFixed(1);
        const matchVal = (compData.matching_percentage || 0).toFixed(1);
        if (vcKpiSimVal) vcKpiSimVal.textContent = simVal + '%';
        if (vcKpiSimBar) vcKpiSimBar.style.width = Math.min(100, Math.max(0, simVal)) + '%';
        if (vcKpiMatchVal) vcKpiMatchVal.textContent = matchVal + '%';
        if (vcKpiMatchBar) vcKpiMatchBar.style.width = Math.min(100, Math.max(0, matchVal)) + '%';


        // Quad Stats
        const st = compData.statistics || {};
        if (vcStatUnchanged) vcStatUnchanged.textContent = st.unchanged || 0;
        if (vcStatUnchangedPct) vcStatUnchangedPct.textContent = `${(st.unchanged_pct || 0).toFixed(1)}% of revision`;
        if (vcStatModified) vcStatModified.textContent = st.modified || 0;
        if (vcStatModifiedPct) vcStatModifiedPct.textContent = `${(st.modified_pct || 0).toFixed(1)}% of revision`;
        if (vcStatAdded) vcStatAdded.textContent = st.added || 0;
        if (vcStatAddedPct) vcStatAddedPct.textContent = `${(st.added_pct || 0).toFixed(1)}% of revision`;
        if (vcStatRemoved) vcStatRemoved.textContent = st.removed || 0;
        if (vcStatRemovedPct) vcStatRemovedPct.textContent = `${(st.removed_pct || 0).toFixed(1)}% of baseline`;

        vcComparisonContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Back Buttons
    if (btnBackToGroups) {
        btnBackToGroups.addEventListener('click', () => {
            if (vcGroupDetailContainer) vcGroupDetailContainer.style.display = 'none';
            if (vcComparisonContainer) vcComparisonContainer.style.display = 'none';
            if (vcGroupsContainer) vcGroupsContainer.style.display = 'block';
            loadVcGroups();
        });
    }

    if (btnBackToGroupDetail) {
        btnBackToGroupDetail.addEventListener('click', () => {
            if (vcComparisonContainer) vcComparisonContainer.style.display = 'none';
            if (vcCurrentGroup) {
                openGroupDetail(vcCurrentGroup.id);
            } else {
                if (vcGroupsContainer) vcGroupsContainer.style.display = 'block';
                loadVcGroups();
            }
        });
    }

    // Download PDF Report
    if (btnDownloadVcReport) {
        btnDownloadVcReport.addEventListener('click', () => {
            if (vcCurrentComparison && vcCurrentComparison.id) {
                window.open(`/api/vc/comparisons/${vcCurrentComparison.id}/report`, '_blank');
            }
        });
    }

    // Initialize
    updateWordAndCharCount();
    updateStatusHint();
    loadHistory();
    checkVcAuthStatus();
    activateMode('home');
});

