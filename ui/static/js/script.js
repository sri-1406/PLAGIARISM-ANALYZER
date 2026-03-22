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

    // Theme logic
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    analyzeBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) {
            showError('Please enter some text to analyze.');
            return;
        }

        performAnalysis(text);
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

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

            textInput.value = data.text;
            displayResults(data.results, data.text);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoader(false);
        }
    });

    async function performAnalysis(text) {
        showLoader(true);
        resultsDiv.style.display = 'none';
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
            highlightedHtml = highlightedHtml.replace(
                regex, 
                `<span class="plagiarized-sent" title="High Match: ${item.source} (${(item.match_score * 100).toFixed(1)}%)">${item.sentence}</span>`
            );
        });

        highlightedBox.innerHTML = highlightedHtml;
        
        // Scroll to results
        resultsDiv.scrollIntoView({ behavior: 'smooth' });

        // Update History list
        loadHistory();
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
