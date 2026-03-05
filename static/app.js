document.addEventListener('DOMContentLoaded', () => {

    // Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const racecourseSelect = document.getElementById('racecourse-select');
    const loadingState = document.getElementById('loading-state');
    const resultsArea = document.getElementById('results-area');

    const tableBody = document.getElementById('table-body');
    const predictionBody = document.getElementById('prediction-body');
    const picksList = document.getElementById('picks-list');

    // Generate 20 rows for Odds Input
    const oddsTableBody = document.getElementById('odds-table-body');
    if (oddsTableBody) {
        for (let i = 1; i <= 20; i++) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-center font-mono">${i}</td>
                <td>
                    <input type="text" class="odds-input kaime-input" placeholder="例: 1-2-3" id="kaime-${i}" data-row="${i}">
                </td>
                <td>
                    <input type="number" step="0.1" class="odds-input value-input" placeholder="00.0" id="odds-${i}" data-row="${i}">
                </td>
                <td class="text-center font-mono" id="prob-${i}">-</td>
                <td class="text-center font-mono" id="ev-${i}">-</td>
                <td class="text-center" id="judge-${i}">-</td>
            `;
            oddsTableBody.appendChild(tr);
        }
    }

    // UI Interactions
    uploadBtn.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('click', (e) => {
        if (e.target !== uploadBtn) fileInput.click();
    });

    ['dragover', 'dragenter'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) handleFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFiles(e.target.files);
    });

    // Handle the generic file upload process (supports multiple)
    async function handleFiles(filesList) {
        // Validate all files are images
        const files = Array.from(filesList);
        for (let file of files) {
            if (!file.type.startsWith('image/')) {
                alert('画像ファイルのみを選択してください。');
                return;
            }
        }

        // Validate racecourse selection
        const selectedRacecourse = racecourseSelect.value;
        if (!selectedRacecourse) {
            alert('レース場を選択してください。');
            return;
        }

        // Show loading state
        loadingState.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            // Prepare FormData (appending multiple files under the "files" key)
            const formData = new FormData();
            formData.append('racecourse', selectedRacecourse);
            files.forEach(file => {
                formData.append('files', file); // 'files' matches FastAPI's list[UploadFile] param
            });

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            loadingState.classList.add('hidden');
            if (result.status === 'success') {
                renderResults(result.data);
            } else {
                alert('解析に失敗しました。サーバーのログを確認してください。');
                console.error(result);
            }

        } catch (error) {
            console.error('Error:', error);
            loadingState.classList.add('hidden');
            alert('サーバーとの通信に失敗しました。バックエンドが起動しているか確認してください。');
        }
    }

    // Render Data into the UI
    function renderResults(data) {
        // Meta data
        document.getElementById('res-race-num').textContent = data.race_info?.race_number || "-";
        document.getElementById('res-distance').textContent = "Expected Value Engine V2"; // changed label for context
        document.getElementById('res-condition').textContent = data.race_info?.condition || "-";

        // Render Table and Picks List
        tableBody.innerHTML = '';
        if (predictionBody) predictionBody.innerHTML = '';
        picksList.innerHTML = '';

        const horses = data.horses || [];

        // Render Top Picks (based on "kaime" values like ◎, 〇, ▲, △)
        const topHorses = [...horses].filter(h => ["◎", "〇", "▲", "△", "S", "A"].includes(h.kaime) || ["◎", "〇", "▲", "△", "S", "A"].includes(h.judgment));

        if (topHorses.length === 0 && horses.length > 0) {
            // If no exact match, fallback
            topHorses.push(...horses.slice(0, 3));
        }

        topHorses.forEach(horse => {
            // Rank styling
            const isTop = ["◎", "S"].includes(horse.kaime) || ["◎", "S"].includes(horse.judgment);
            const rankClass = isTop ? 's-rank' : 'a-rank';
            const displayRank = horse.kaime && horse.kaime !== '-' ? horse.kaime : (horse.judgment && horse.judgment !== '-' ? horse.judgment : 'PICK');

            const li = document.createElement('li');
            li.className = `pick-item ${rankClass}`;
            li.innerHTML = `
                <div class="pick-num">${horse.number}</div>
                <div class="pick-details">
                    <div class="pick-name">${horse.name}</div>
                    <div class="pick-score">判定: ${horse.judgment || '-'} | 買い目: ${horse.kaime || '-'}</div>
                </div>
                <div class="pick-rank" style="background: ${rankClass === 's-rank' ? 'var(--secondary)' : 'var(--warning)'}">${displayRank}</div>
            `;
            picksList.appendChild(li);
        });

        // Render Table for the 8 new metrics
        horses.forEach(horse => {
            const tr = document.createElement('tr');

            const evalClass = ['S', 'A', '◎', '〇'].includes(horse.judgment) || ['S', 'A', '◎', '〇'].includes(horse.kaime) ? 'eval-s' : 'eval-b';

            tr.innerHTML = `
                <td>${horse.number}</td>
                <td style="font-weight: 500;">${horse.name}</td>
                <td class="text-center font-mono" style="background-color: ${horse.hosei_lap_bg}; color: ${horse.hosei_lap_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.hosei_lap}</td>
                <td class="text-center font-mono" style="background-color: ${horse.hosei_turn_bg}; color: ${horse.hosei_turn_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.hosei_turn}</td>
                <td class="text-center font-mono" style="background-color: ${horse.hosei_straight_bg}; color: ${horse.hosei_straight_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.hosei_straight}</td>
                <td class="text-center font-mono" style="background-color: ${horse.hosei_exhibition_bg}; color: ${horse.hosei_exhibition_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.hosei_exhibition}</td>
                <td class="text-center font-mono" style="font-weight:bold; color:var(--primary);">${horse.kiryoku_total}</td>
                <td class="text-center font-mono">${horse.avg_diff}</td>
                <td class="text-center"><span class="eval-badge ${evalClass}">${horse.judgment}</span></td>
                <td class="text-center"><span class="eval-badge ${evalClass}" style="background:var(--secondary);color:#fff;">${horse.kaime}</span></td>
            `;
            tableBody.appendChild(tr);

            // Build the secondary prediction table row
            if (predictionBody) {
                const ptr = document.createElement('tr');
                ptr.innerHTML = `
                    <td>${horse.number}</td>
                    <td style="font-weight: 500;">${horse.name}</td>
                    <td class="text-center font-mono" style="background-color: ${horse.pred_win_1_bg}; color: ${horse.pred_win_1_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.pred_win_1}</td>
                    <td class="text-center font-mono" style="background-color: ${horse.pred_win_2_bg}; color: ${horse.pred_win_2_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.pred_win_2}</td>
                    <td class="text-center font-mono" style="background-color: ${horse.pred_win_3_bg}; color: ${horse.pred_win_3_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.pred_win_3}</td>
                    <td class="text-center font-mono" style="background-color: ${horse.pred_rentai_3_bg}; color: ${horse.pred_rentai_3_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.pred_rentai_3}</td>
                    <td class="text-center font-mono" style="font-weight:bold; background-color: ${horse.total_power_bg}; color: ${horse.total_power_bg !== 'transparent' ? '#000' : 'var(--primary)'}">${horse.total_power}</td>
                    <td class="text-center font-mono" style="background-color: ${horse.final_eval_bg}; color: ${horse.final_eval_bg !== 'transparent' ? '#000' : 'inherit'}">${horse.final_eval}</td>
                `;
                predictionBody.appendChild(ptr);
            }
        });

        // Show section
        resultsArea.classList.remove('hidden');

        // Initialize EV calculation listeners
        initEVCalculations(horses);
    }

    // --- Expected Value Calculation Logic ---
    function initEVCalculations(horses) {
        // Parse probabilities from horses data (I13:L18 strings)
        // Format of probability strings are usually "12.3%" -> 12.3
        const probabilities = {};

        horses.forEach(h => {
            const num = parseInt(h.number);

            const parseProb = (str) => {
                if (!str || str === '-') return 0;
                const cleaned = str.replace(/[^0-9.]/g, '');
                const val = parseFloat(cleaned);
                return isNaN(val) ? 0 : val / 100.0; // Convert to decimal (e.g., 0.123)
            };

            probabilities[num] = {
                win1: parseProb(h.pred_win_1),
                win2: parseProb(h.pred_win_2),
                win3: parseProb(h.pred_win_3)
            };
        });

        // Define expected value trigger function
        const updateRowEV = (rowId) => {
            const kaimeStr = document.getElementById(`kaime-${rowId}`).value.trim();
            const oddsVal = parseFloat(document.getElementById(`odds-${rowId}`).value) || 0;

            const probEl = document.getElementById(`prob-${rowId}`);
            const evEl = document.getElementById(`ev-${rowId}`);
            const judgeEl = document.getElementById(`judge-${rowId}`);

            // Validate Trifecta input (e.g., "1-2-3")
            const parts = kaimeStr.split(/[-ー=＝,]/).map(p => parseInt(p.trim()));

            if (parts.length === 3 && parts.every(n => n >= 1 && n <= 6)) {
                // Calculate estimated trifecta probability:
                // Simplified algorithm: (1st place prob) * (2nd place given 1st) * (3rd place given 1st and 2nd)
                // We use the crude margin rates (win1, win2, win3) as independent marginal probabilities for demonstration

                const p1 = probabilities[parts[0]].win1;

                // Adjust 2nd place probability (assuming 1st place horse takes up probability mass)
                let p2Raw = probabilities[parts[1]].win2;
                let sumP2Others = 0;
                for (let i = 1; i <= 6; i++) {
                    if (i !== parts[0]) sumP2Others += probabilities[i].win2;
                }
                const p2 = sumP2Others > 0 ? p2Raw / sumP2Others : 0;

                // Adjust 3rd place probability
                let p3Raw = probabilities[parts[2]].win3;
                let sumP3Others = 0;
                for (let i = 1; i <= 6; i++) {
                    if (i !== parts[0] && i !== parts[1]) sumP3Others += probabilities[i].win3;
                }
                const p3 = sumP3Others > 0 ? p3Raw / sumP3Others : 0;

                const totalProb = p1 * p2 * p3;

                // Calculate EV = Prob * Odds * 100
                const expectedValue = totalProb * oddsVal * 100;

                // Format UI
                probEl.textContent = (totalProb * 100).toFixed(2) + "%";

                if (oddsVal > 0) {
                    evEl.textContent = expectedValue.toFixed(1) + "%";

                    // Highlight based on expected value threshold (over 100% is mathematically profitable)
                    if (expectedValue > 120) {
                        evEl.style.color = "var(--secondary)"; // Gold
                        evEl.style.fontWeight = "bold";
                        judgeEl.innerHTML = `<span class="eval-badge eval-s" style="background:var(--secondary);color:#fff;">S</span>`;
                    } else if (expectedValue >= 100) {
                        evEl.style.color = "var(--primary)"; // Neon Green
                        evEl.style.fontWeight = "bold";
                        judgeEl.innerHTML = `<span class="eval-badge eval-b">A</span>`;
                    } else if (expectedValue >= 80) {
                        evEl.style.color = "var(--text-main)";
                        evEl.style.fontWeight = "normal";
                        judgeEl.innerHTML = `<span class="eval-badge eval-c" style="background:transparent; border: 1px solid var(--border-color); color:var(--text-muted)">B</span>`;
                    } else {
                        evEl.style.color = "var(--danger)";
                        evEl.style.fontWeight = "normal";
                        judgeEl.innerHTML = `<span class="eval-badge eval-c" style="background:transparent; border: 1px solid var(--border-color); color:var(--text-muted)">C</span>`;
                    }
                } else {
                    evEl.textContent = "-";
                    evEl.style.color = "inherit";
                    judgeEl.innerHTML = "-";
                }
            } else {
                probEl.textContent = "-";
                evEl.textContent = "-";
                evEl.style.color = "inherit";
                judgeEl.innerHTML = "-";
            }
        };

        // Attach listeners to all inputs
        for (let i = 1; i <= 20; i++) {
            const rowKaime = document.getElementById(`kaime-${i}`);
            const rowOdds = document.getElementById(`odds-${i}`);

            if (rowKaime && rowOdds) {
                // Remove existing listeners by replacing clone
                const newKaime = rowKaime.cloneNode(true);
                const newOdds = rowOdds.cloneNode(true);
                rowKaime.parentNode.replaceChild(newKaime, rowKaime);
                rowOdds.parentNode.replaceChild(newOdds, rowOdds);

                newKaime.addEventListener('input', () => updateRowEV(i));
                newOdds.addEventListener('input', () => updateRowEV(i));
            }
        }
    }

    // Chart.js instance tracking to destroy before redrawing
    let radarChartInstance = null;

    function drawRadarChart(horses) {
        // If no horses, do nothing
        if (!horses || horses.length === 0) return;

        const ctx = document.getElementById('radarChart').getContext('2d');

        if (radarChartInstance) {
            radarChartInstance.destroy();
        }

        // We'll plot the first 4 horses' I-L data on a radar chart
        // Since lower is better (faster time), we might need to invert or just let the chart display it
        // A standard radar chart puts lower values closer to center, which conceptually "looks" smaller.
        // For 'faster is better', we'll just plot the raw numbers and let the user interpret.

        const labels = ['Metric I', 'Metric J', 'Metric K', 'Metric L'];

        const datasets = [];
        const colors = [
            'rgba(99, 102, 241, 0.8)',   // Indigo
            'rgba(236, 72, 153, 0.8)',   // Pink
            'rgba(16, 185, 129, 0.8)',   // Green
            'rgba(245, 158, 11, 0.8)'    // Amber
        ];

        // Take up to 4 horses to not clutter the chart
        const chartHorses = horses.slice(0, 4);

        chartHorses.forEach((horse, index) => {
            // Convert strings to floats for charting
            const dataFloats = horse.times.map(t => {
                const parsed = parseFloat(t);
                return isNaN(parsed) ? 0 : parsed;
            });

            // Only add if there's actual data
            if (dataFloats.some(d => d > 0)) {
                datasets.push({
                    label: horse.name || `枠${horse.number}`,
                    data: dataFloats,
                    backgroundColor: colors[index].replace('0.8', '0.2'),
                    borderColor: colors[index],
                    pointBackgroundColor: colors[index],
                    pointBorderColor: '#fff',
                    borderWidth: 2
                });
            }
        });

        // If no valid float data was parsed from the strings, fallback
        if (datasets.length === 0) {
            datasets.push({
                label: 'データ無し',
                data: [0, 0, 0, 0],
                borderColor: 'rgba(255,255,255,0.2)'
            });
        }

        radarChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: { family: "'Inter', sans-serif", size: 12 }
                        },
                        // Invert the scale so smaller values are on the OUTSIDE (visually "bigger/better" area)
                        reverse: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: 'rgba(255,255,255,0.7)' }
                    }
                }
            }
        });
    }

});
