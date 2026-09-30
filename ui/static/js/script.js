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

    // Mode Toggle
    const singleModeBtn = document.getElementById('singleMode');
    const multiModeBtn = document.getElementById('multiMode');
    const singleInputSection = document.getElementById('singleInputSection');
    const multiInputSection = document.getElementById('multiInputSection');
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
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const activeTheme = document.documentElement.getAttribute('data-theme');
        const nextTheme = activeTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('theme', nextTheme);
    });

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

    if (clearTextBtn) {
        clearTextBtn.addEventListener('click', () => {
            textInput.value = '';
            const extractionBadge = document.getElementById('extractionBadge');
            if (extractionBadge) extractionBadge.style.display = 'none';
            clearAllFiles();
            updateWordAndCharCount();
            textInput.focus();
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
            const resp = await fetch('/api/upload', {
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
                    statusHintText.textContent = `Extracted text from "${file.name}". Ready to analyze.`;
                }
            }
        } catch (e) {
            showError(`Extraction failed: ${e.message}`);
        }
    }

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleIncomingFiles(files, currentMode === 'multi');
    });

    // Mode Toggle Logic
    singleModeBtn.addEventListener('click', () => {
        currentMode = 'single';
        singleModeBtn.classList.add('active');
        singleModeBtn.setAttribute('aria-selected', 'true');
        multiModeBtn.classList.remove('active');
        multiModeBtn.setAttribute('aria-selected', 'false');

        singleInputSection.style.display = 'block';
        multiInputSection.style.display = 'none';
        resultsDiv.style.display = 'none';
        if (singleResults) singleResults.style.display = 'none';
        if (multiResults) multiResults.style.display = 'none';
        clearAllFiles();
        updateStatusHint();
    });

    multiModeBtn.addEventListener('click', () => {
        currentMode = 'multi';
        multiModeBtn.classList.add('active');
        multiModeBtn.setAttribute('aria-selected', 'true');
        singleModeBtn.classList.remove('active');
        singleModeBtn.setAttribute('aria-selected', 'false');

        singleInputSection.style.display = 'none';
        multiInputSection.style.display = 'block';
        resultsDiv.style.display = 'none';
        if (singleResults) singleResults.style.display = 'none';
        if (multiResults) multiResults.style.display = 'none';
        clearAllFiles();
        updateStatusHint();
    });

    // Analyze Click Action
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
                    const resp = await fetch('/api/upload', { method: 'POST', body: formData });
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

        // Stat Quad Population
        if (statSimilarity) statSimilarity.textContent = `${pct.toFixed(1)}%`;
        if (barSimilarity) barSimilarity.style.width = `${pct}%`;

        if (statOriginality) statOriginality.textContent = `${originality.toFixed(1)}%`;
        if (barOriginality) barOriginality.style.width = `${originality}%`;

        const totalSent = data.total_sentences || 0;
        const flaggedSent = Array.isArray(data.plagiarized_sentences) ? data.plagiarized_sentences.length : (data.plagiarized_sentences || 0);

        if (statSentences) statSentences.textContent = `${totalSent}`;
        if (statFlaggedSentences) statFlaggedSentences.textContent = `${flaggedSent} flagged match${flaggedSent === 1 ? '' : 'es'}`;

        if (data.top_matches && data.top_matches.length > 0) {
            const top = data.top_matches[0];
            const topPct = (top.score * 100).toFixed(1);
            if (statTopSource) statTopSource.textContent = top.title || "Matched Corpus File";
            if (statTopSourceScore) statTopSourceScore.textContent = `${topPct}% Maximum Overlap`;
        } else {
            if (statTopSource) statTopSource.textContent = "No Matches Found";
            if (statTopSourceScore) statTopSourceScore.textContent = "100% Unique Corpus";
        }

        // Smooth Scroll to Results
        resultsDiv.scrollIntoView({ behavior: 'smooth' });

        // Refresh History
        loadHistory();
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
                const previewMatch = (report.preview || '').toLowerCase().includes(q);
                const idMatch = String(report.id).includes(q);
                if (!previewMatch && !idMatch) return false;
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

            card.innerHTML = `
                <div class="history-card-top">
                    <div class="history-doc-info">
                        <div class="history-doc-badge">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        </div>
                        <div>
                            <span class="history-doc-title">Audit #${report.id}</span>
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

        // Show extraction badge with Audit #
        const extractionBadge = document.getElementById('extractionBadge');
        const extractionFileName = document.getElementById('extractionFileName');
        if (extractionBadge && extractionFileName) {
            extractionBadge.style.display = 'inline-flex';
            extractionFileName.textContent = `Loaded from Audit #${report.id}`;
        }

        if (statusHintText) {
            statusHintText.textContent = `Loaded content from Audit #${report.id} (${(report.percentage || 0).toFixed(1)}% score). Ready to re-analyze.`;
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

    // Initialize
    updateWordAndCharCount();
    updateStatusHint();
    loadHistory();
});
