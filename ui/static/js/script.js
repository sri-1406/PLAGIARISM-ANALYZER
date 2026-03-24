document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const fileInput = document.getElementById('fileInput');
    const resultsDiv = document.getElementById('results');
    const loader = document.getElementById('loader');
    const errorDiv = document.getElementById('errorMsg');

    // UI Elements for results
    const scoreVal = document.getElementById('scoreVal');
    const docList = document.getElementById('docList');
    const highlightedBox = document.getElementById('highlightedBox');
    const themeToggle = document.getElementById('themeToggle');
    const uploadLabel = document.getElementById('uploadLabel');

    // New Multi-Compare Elements
    const singleResults = document.getElementById('singleResults');
    const multiResults = document.getElementById('multiResults');
    const matrixContainer = document.getElementById('matrixContainer');
    const pairwiseList = document.getElementById('pairwiseList');
    const singleModeBtn = document.getElementById('singleMode');
    const multiModeBtn = document.getElementById('multiMode');
    const singleInputSection = document.getElementById('singleInputSection');
    const multiInputSection = document.getElementById('multiInputSection');

    let currentMode = 'single'; // 'single' or 'multi'

    // Theme logic
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Mode Toggle Logic
    singleModeBtn.addEventListener('click', () => {
        currentMode = 'single';
        singleModeBtn.classList.add('active');
        multiModeBtn.classList.remove('active');
        singleInputSection.style.display = 'block';
        multiInputSection.style.display = 'none';
        resultsDiv.style.display = 'none';
        
        // Dynamic label text
        uploadLabel.textContent = 'Upload Document';
    });

    multiModeBtn.addEventListener('click', () => {
        currentMode = 'multi';
        multiModeBtn.classList.add('active');
        singleModeBtn.classList.remove('active');
        singleInputSection.style.display = 'none';
        multiInputSection.style.display = 'block';
        resultsDiv.style.display = 'none';
        
        // Dynamic label text
        uploadLabel.textContent = 'Upload Documents';
        
        // Reset file input for clean state
        fileInput.value = '';
        document.getElementById('fileName').textContent = 'No file selected';
    });

    analyzeBtn.addEventListener('click', async () => {
        if (currentMode === 'single') {
            const text = textInput.value.trim();
            if (!text) {
                showError('Please enter some text to analyze.');
                return;
            }
            performAnalysis(text);
        } else {
            const files = fileInput.files;
            if (files.length < 2) {
                showError('Please select at least two files for cross-comparison.');
                return;
            }
            performMultiAnalysis(files);
        }
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file || currentMode === 'multi') return; 

        const allowedExtensions = ['.txt', '.pdf', '.docx'];
        const fileName = file.name.toLowerCase();
        const isValid = allowedExtensions.some(ext => fileName.endsWith(ext));

        if (!isValid) {
            showError('Unsupported file format. Please use .txt, .pdf, or .docx');
            return;
        }


        const formData = new FormData();
        formData.append('file', file);

        showLoader(true);
        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            // Just fill the text area so user can see it
            textInput.value = data.text;
            
            // Do NOT call displayResults here. 
            // We just want to prepare the text for the user to click "Analyze" manually.
            resultsDiv.style.display = 'none'; 
            
        } catch (err) {
            showError(err.message);
        } finally {
            showLoader(false);
        }
    });

    async function performAnalysis(text) {
        showLoader(true);
        resultsDiv.style.display = 'none';
        singleResults.style.display = 'block';
        multiResults.style.display = 'none';
        errorDiv.style.display = 'none';
        
        // RESET needle and gauge to zero instantly before sweep
        const needleGroup = document.getElementById('needleGroup');
        const gaugeProgress = document.getElementById('gaugeProgress');
        const scoreValElement = document.getElementById('scoreVal');
        
        if (needleGroup) needleGroup.setAttribute('transform', 'rotate(-90 100 100)');
        if (gaugeProgress) gaugeProgress.style.strokeDashoffset = '251.3';
        if (scoreValElement) scoreValElement.textContent = '0.0%';

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

    async function performMultiAnalysis(files) {
        showLoader(true);
        resultsDiv.style.display = 'none';
        singleResults.style.display = 'none';
        multiResults.style.display = 'block';
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

    function displayResults(data, originalText) {
        resultsDiv.style.display = 'block';
        
        const pct = data.overall_percentage || 0;
        
        // Select SVG components
        const scoreValElement = document.getElementById('scoreVal');
        const needleGroup = document.getElementById('needleGroup');
        const gaugeProgress = document.getElementById('gaugeProgress');
        
        // Arc tracking
        const circumference = 251.3;
        const offset = circumference - (pct / 100) * circumference;
        gaugeProgress.style.strokeDashoffset = offset;
        
        // Number counting
        let currentCount = 0;
        const duration = 1500;
        const startTime = Date.now();
        
        const updateCounter = () => {
            const now = Date.now();
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            currentCount = (pct * easedProgress).toFixed(1);
            
            scoreValElement.textContent = `${currentCount}%`;
            
            // Incrementally move needle along with the number
            moveNeedle(parseFloat(currentCount));
            
            if (progress < 1) requestAnimationFrame(updateCounter);
            else {
                scoreValElement.textContent = `${pct.toFixed(1)}%`;
                moveNeedle(pct); // Ensure final position is exact
            }
        };
        requestAnimationFrame(updateCounter);
        
        // Use the new functional needle move function
        moveNeedle(pct);
        
        // Match final colors to the new 3-zone boundaries (0-30%, 30-70%, 70-100%)
        if (pct < 30) scoreValElement.style.color = '#10b981';
        else if (pct < 70) scoreValElement.style.color = '#f59e0b';
        else scoreValElement.style.color = '#ef4444';

        // Update matched documents
        docList.innerHTML = '';
        if (data.top_matches.length === 0) {
            docList.innerHTML = '<li>No significant document matches found.</li>';
        } else {
            data.top_matches.forEach(match => {
                const li = document.createElement('li');
                li.className = 'match-item';
                li.innerHTML = `
                    <span>${match.title}</span>
                    <strong>${(match.score * 100).toFixed(1)}% match</strong>
                `;
                docList.appendChild(li);
            });
        }

        // Highlight sentences
        let highlightedHtml = originalText;
        
        // Sort plagiarized sentences by length (longest first) to avoid partial replacement issues
        const sortedSents = [...data.plagiarized_sentences].sort((a, b) => b.sentence.length - a.sentence.length);
        
        sortedSents.forEach(item => {
            const escapedSent = item.sentence.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(escapedSent, 'g');
            const percentage = (item.match_score * 100).toFixed(1);
            highlightedHtml = highlightedHtml.replace(
                regex, 
                `<span class="plagiarized-sent" title="Source: ${item.source}">${item.sentence} <span class="similarity-pill">${percentage}%</span></span>`
            );
        });

        highlightedBox.innerHTML = highlightedHtml;
        
        // Wrap with expandable if it's too long
        wrapWithExpandable(highlightedBox);

        // Scroll to results
        resultsDiv.scrollIntoView({ behavior: 'smooth' });

        // Update History list
        loadHistory();
    }

    function displayMultiResults(data) {
        resultsDiv.style.display = 'block';
        matrixContainer.innerHTML = '';
        pairwiseList.innerHTML = '';

        // 1. Render Matrix
        const table = document.createElement('table');
        table.className = 'matrix-table';
        
        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>File Name</th>' + data.document_names.map(name => `<th>${name}</th>`).join('');
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        data.document_names.forEach(name1 => {
            const row = document.createElement('tr');
            let rowHtml = `<th>${name1}</th>`;
            data.document_names.forEach(name2 => {
                const score = data.matrix[name1][name2];
                const isHigh = score >= 70 && name1 !== name2;
                rowHtml += `<td class="${isHigh ? 'high-sim' : ''}">${score.toFixed(1)}%</td>`;
            });
            row.innerHTML = rowHtml;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        matrixContainer.appendChild(table);

        // 2. Render Pairwise List
        if (data.pairwise_results.length === 0) {
            pairwiseList.innerHTML = '<p>No significant inter-document matches found.</p>';
        } else {
            data.pairwise_results.forEach(pair => {
                const card = document.createElement('div');
                card.className = `pair-card ${pair.similarity_percentage >= 70 ? 'critical' : ''}`;
                
                const scoreColor = pair.similarity_percentage >= 70 ? '#ef4444' : (pair.similarity_percentage >= 30 ? '#f59e0b' : '#10b981');

                card.innerHTML = `
                    <h4>
                        <span>${pair.doc1} <small>vs</small> ${pair.doc2}</span>
                        <span class="score-pill" style="background: ${scoreColor}22; color: ${scoreColor}">${pair.similarity_percentage.toFixed(1)}%</span>
                    </h4>
                    <p class="pair-details">Found ${pair.matching_sentences_count} matching sentences between these documents.</p>
                `;

                if (pair.matches.length > 0) {
                    const matchBox = document.createElement('div');
                    matchBox.className = 'sentence-matches';
                    pair.matches.slice(0, 5).forEach(m => {
                        const mdiv = document.createElement('div');
                        mdiv.className = 'match-pair';
                        mdiv.innerHTML = `
                            <div class="match-pair">
                                <span class="label">Doc A Sentence:</span>
                                <div>"${m.sentence1}"</div>
                                <span class="label" style="margin-top:8px">Doc B Match (${m.score}%):</span>
                                <div>"${m.sentence2}"</div>
                            </div>
                        `;
                        matchBox.appendChild(mdiv);
                    });
                    if (pair.matches.length > 5) {
                        const moreCount = pair.matches.length - 5;
                        const moreBtn = document.createElement('p');
                        moreBtn.style.cssText = 'font-size:0.8rem; color:var(--text-light); margin-top:10px; cursor:pointer;';
                        moreBtn.textContent = `+ ${moreCount} more matches (Scroll inside card)`;
                        matchBox.appendChild(moreBtn);
                    }
                    card.appendChild(matchBox);
                    
                    // Wrap with expandable for long match cards
                    wrapWithExpandable(matchBox);
                }

                pairwiseList.appendChild(card);
            });
        }

        resultsDiv.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Wrap an element in an expandable container if it exceeds height limit
     */
    function wrapWithExpandable(target) {
        // If target already wrapped, don't do it again
        if (target.parentElement.classList.contains('expandable-container')) return;

        // Check content height after a short delay for accurate measurement
        setTimeout(() => {
            const heightLimit = 280;
            if (target.scrollHeight <= heightLimit) return;

            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'expandable-wrapper';
            
            // Create container
            const container = document.createElement('div');
            container.className = 'expandable-container';
            
            // Move target into container
            target.parentNode.insertBefore(wrapper, target);
            wrapper.appendChild(container);
            container.appendChild(target);

            // Create button
            const btn = document.createElement('button');
            btn.className = 'read-more-btn';
            btn.innerHTML = 'Read More ↓';
            
            btn.onclick = () => {
                const isExpanded = container.classList.toggle('expanded');
                btn.innerHTML = isExpanded ? 'Read Less ↑' : 'Read More ↓';
                
                // If collapsing, scroll to top of section
                if (!isExpanded) {
                    wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            };
            
            wrapper.appendChild(btn);
        }, 100);
    }

    /**
     * Functional needle control
     * @param {number} value - Percentage value (0-100)
     */
    function moveNeedle(value) {
        const needleGroup = document.getElementById('needleGroup');
        if (!needleGroup) return;

        // Map 0-100 to -90deg to +90deg
        const minAngle = -90;
        const maxAngle = 90;
        const clampedValue = Math.max(0, Math.min(100, value));
        const rotation = (clampedValue * (maxAngle - minAngle) / 100) + minAngle;

        // Use SVG attribute for perfect (100, 100) center baseline rotation
        needleGroup.setAttribute('transform', `rotate(${rotation} 100 100)`);
    }

    function showLoader(show) {
        loader.style.display = show ? 'block' : 'none';
        analyzeBtn.disabled = show;
    }

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
    }

    async function loadHistory() {
        const historyList = document.getElementById('historyList');
        if(!historyList) return;

        try {
            const response = await fetch('/api/reports');
            const data = await response.json();
            
            historyList.innerHTML = '';
            if (data.length === 0) {
                historyList.innerHTML = '<p style="color:var(--text-light)">No analysis history yet.</p>';
                return;
            }

            // Only show last 10 in a clean grid
            data.slice(0, 10).forEach(report => {
                const card = document.createElement('div');
                card.className = 'history-card';
                
                let textColor = '#10b981';
                if(report.percentage >= 70) textColor = '#ef4444';
                else if(report.percentage >= 30) textColor = '#f59e0b';
                
                card.innerHTML = `
                    <span class="date">${new Date(report.timestamp).toLocaleDateString()}</span>
                    <p class="preview">${report.preview}</p>
                    <div class="score" style="color: ${textColor}">${report.percentage.toFixed(1)}%</div>
                `;
                historyList.appendChild(card);
            });
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    }

    // Load history on page load
    loadHistory();
});
