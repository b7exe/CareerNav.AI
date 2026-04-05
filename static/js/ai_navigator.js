const SKILLS_LIST = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS", "Azure", 
    "GCP", "Docker", "Kubernetes", "SQL", "MongoDB", "PostgreSQL", "Java", 
    "Spring Boot", "Go", "Rust", "AI", "ML", "LLM", "FastAPI", "GraphQL", 
    "Redis", "Kafka", "Terraform", "CI/CD", "Git", "Linux", "Cybersecurity",
    "DevOps", "Data Science", "Deep Learning", "NLP", "Computer Vision",
    "Flutter", "React Native", "Next.js", "Django", "Ruby on Rails", "PHP"
];

// Hash function for string
const cyrb53 = function(str, seed = 0) {
    let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
    for (let i = 0, ch; i < str.length; i++) {
        ch = str.charCodeAt(i);
        h1 = Math.imul(h1 ^ ch, 2654435761);
        h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1>>>16), 2246822507) ^ Math.imul(h2 ^ (h2>>>13), 3266489909);
    h2 = Math.imul(h2 ^ (h2>>>16), 2246822507) ^ Math.imul(h1 ^ (h1>>>13), 3266489909);
    return 4294967296 * (2097151 & h2) + (h1>>>0);
};

let chartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initSkillsGrid();
    initMarketPulse();
    
    document.getElementById('profileForm').addEventListener('submit', handleProfileSubmit);
    document.getElementById('resetProfileBtn').addEventListener('click', resetProfile);

    // If session profile exists (passed down unexpectedly or stored), we load it.
    const urlParams = new URLSearchParams(window.location.search);
    const domain = urlParams.get('domain');
    if (domain) {
        const stage = urlParams.get('stage') || 'entry';
        const target_role = urlParams.get('target_role') || domain;
        
        let years = 0;
        if(stage === 'mid') years = 3;
        else if(stage === 'senior') years = 6;
        
        const generatedProfile = {
            id: "usr-" + Date.now().toString(36),
            name: "Professional",
            current_role: domain,
            experience_years: years,
            location: 'Hyderabad',
            target_role: target_role,
            salary_expectation: "Not specified",
            preferred_work_type: "any",
            current_skills: SKILLS_LIST.filter(s => domain.toLowerCase().includes(s.toLowerCase())), // simple heuristic
            last_analysis: new Date().toISOString()
        };
        
        fillFormWithProfile(generatedProfile);
        runAnalysisFlow(generatedProfile);
        
    } else {
        // Fallback to localStorage if no URL params
        const storedProfileStr = localStorage.getItem('user_profile');
        if (storedProfileStr) {
            try {
                const tempProfile = JSON.parse(storedProfileStr);
                fillFormWithProfile(tempProfile);
                runAnalysisFlow(tempProfile);
            } catch(e) {}
        }
    }
});

function getProfileHash(profileObj) {
    return cyrb53(JSON.stringify(profileObj)).toString();
}

function initSkillsGrid() {
    const grid = document.getElementById('skillsGrid');
    SKILLS_LIST.forEach(skill => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-2';
        div.innerHTML = `
            <input type="checkbox" id="skill_${skill}" value="${skill}" class="skill-checkbox rounded border-slate-700 bg-slate-800 text-brand-accent focus:ring-brand-accent p-2">
            <label for="skill_${skill}" class="text-sm text-slate-300 select-none">${skill}</label>
        `;
        grid.appendChild(div);
    });
}

function fillFormWithProfile(p) {
    document.getElementById('pRole').value = p.current_role || '';
    document.getElementById('pExp').value = p.experience_years || 0;
    document.getElementById('pLocation').value = p.location || 'Hyderabad';
    document.getElementById('pTarget').value = p.target_role || '';
    document.getElementById('pSalary').value = p.salary_expectation ? parseInt(p.salary_expectation.replace(/\D/g,'')) : '';
    document.getElementById('pWorkType').value = p.preferred_work_type || 'any';
    
    if (p.current_skills && Array.isArray(p.current_skills)) {
        const checkboxes = document.querySelectorAll('.skill-checkbox');
        checkboxes.forEach(cb => {
            if (p.current_skills.includes(cb.value)) {
                cb.checked = true;
            }
        });
    }
}

async function handleProfileSubmit(e) {
    e.preventDefault();
    const skills = Array.from(document.querySelectorAll('.skill-checkbox:checked')).map(cb => cb.value);
    
    const userProfile = {
        id: "usr-" + Date.now().toString(36),
        name: "Professional", // Could collect this
        current_role: document.getElementById('pRole').value,
        experience_years: parseInt(document.getElementById('pExp').value),
        location: document.getElementById('pLocation').value,
        target_role: document.getElementById('pTarget').value,
        salary_expectation: document.getElementById('pSalary').value ? `₹${document.getElementById('pSalary').value} LPA` : "Not specified",
        preferred_work_type: document.getElementById('pWorkType').value,
        current_skills: skills,
        last_analysis: new Date().toISOString()
    };

    localStorage.setItem('user_profile', JSON.stringify(userProfile));
    
    // Ping the backend /api/save-profile
    try {
        await fetch('/api/save-profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
    } catch(e) {}

    runAnalysisFlow(userProfile);
}

function resetProfile() {
    document.getElementById('dashboardResults').classList.add('hidden');
    document.getElementById('profileSetup').classList.remove('hidden');
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function retryAnalysis() {
    const stored = localStorage.getItem('user_profile');
    if (stored) {
        runAnalysisFlow(JSON.parse(stored));
    } else {
        resetProfile();
    }
}

async function initMarketPulse() {
    const pulseKey = "market_pulse_cache";
    const now = Date.now();
    let data = null;

    const cachedStr = localStorage.getItem(pulseKey);
    if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        // 6 hours
        if (now - cached.timestamp < 6 * 60 * 60 * 1000) {
            data = cached.data;
            console.log("Using cached market pulse, age: " + Math.round((now - cached.timestamp)/60000) + " minutes");
        }
    }

    if (!data) {
        try {
            const res = await fetch('/api/market-pulse');
            if(res.ok) {
                data = await res.json();
                localStorage.setItem(pulseKey, JSON.stringify({timestamp: now, data: data}));
            }
        } catch(e) {}
    }

    if (data) {
        document.getElementById('marketPulseBanner').classList.remove('hidden');
        if (data.trending && data.trending.length > 0) {
            const repos = data.trending.map(t => t.name).join(", ");
            document.getElementById('pulseText').innerText = `Trending now: ${repos}`;
            document.getElementById('pulseIndicator').className = "w-3 h-3 rounded-full animate-pulse bg-green-500 shadow-[0_0_8px_#22c55e]";
        }
        document.getElementById('pulseTime').innerText = `Refreshed ${new Date().toLocaleTimeString()}`;
    }
}

async function runAnalysisFlow(userProfile) {
    document.getElementById('profileSetup').classList.add('hidden');
    document.getElementById('loadingOverlay').classList.remove('hidden');
    
    // Fake timers for UX
    const loaderText = document.getElementById('loadingText');
    const stages = [
        "Analyzing trending technologies...",
        "Running AI analysis on your profile...",
        "Building your personalized roadmap..."
    ];
    let s = 0;
    const ltimer = setInterval(() => {
        if(s < stages.length) {
            loaderText.innerText = stages[s++];
        } else {
            clearInterval(ltimer);
        }
    }, 2000);

    const profileHash = getProfileHash(userProfile);
    const cacheKey = `analysis_${userProfile.id || 'default'}_${profileHash}`;
    
    let aiResponse = null;
    const cachedStr = localStorage.getItem(cacheKey);
    if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        // 24 hours
        if (Date.now() - cached.timestamp < 24 * 60 * 60 * 1000) {
            aiResponse = cached.data;
            console.log(`Using cached AI analysis, age: ${Math.round((Date.now() - cached.timestamp)/60000)} minutes`);
        }
    }

    if (!aiResponse) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ userProfile }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (res.ok) {
                aiResponse = await res.json();
                if (aiResponse && !aiResponse.error) {
                    localStorage.setItem(cacheKey, JSON.stringify({
                        timestamp: Date.now(),
                        data: aiResponse
                    }));
                }
            } else {
                aiResponse = {error: true};
            }
        } catch(err) {
            clearTimeout(timeoutId);
            if (err.name === 'AbortError') {
                aiResponse = {error: true, message: "Analysis is taking longer than expected. The market data servers may be busy. Please try again in a moment."};
            } else {
                aiResponse = {error: true, message: "Something went wrong. Please try again."};
            }
        }
    }

    clearInterval(ltimer);
    
    if (aiResponse && aiResponse.error) {
        showError(aiResponse.message || "Market analysis temporarily unavailable. Please try again in a moment.");
        return;
    }

    document.getElementById('loadingOverlay').classList.add('hidden');
    renderDashboard(aiResponse);
    
    // PROGRESSIVE LOAD: AI Disruption Radar
    fetchDisruptionRadar(userProfile);
}

function showError(msg) {
    document.getElementById('loaderSpinner').classList.add('hidden');
    document.getElementById('errorIcon').classList.remove('hidden');
    document.getElementById('errorRetryContainer').classList.remove('hidden');
    document.getElementById('loadingText').innerText = "Analysis Failed";
    document.getElementById('loadingSubtext').innerText = msg;
    document.getElementById('loadingSubtext').classList.add('text-brand-error');
}

function renderDashboard(data) {
    if (!data) return;
    
    // Reset any error/loading UI in case of retry success
    document.getElementById('loaderSpinner').classList.remove('hidden');
    document.getElementById('errorIcon').classList.add('hidden');
    document.getElementById('errorRetryContainer').classList.add('hidden');
    document.getElementById('loadingSubtext').classList.remove('text-brand-error');

    document.getElementById('dashboardResults').classList.remove('hidden');

    // Risk Assessment
    if (data.risk_assessment) {
        const risk = data.risk_assessment;
        document.getElementById('riskLabel').innerText = risk.ai_substitution_risk.replace('_', ' ');
        document.getElementById('riskPercent').innerText = `${risk.risk_percentage}%`;
        document.getElementById('riskBar').style.width = `${risk.risk_percentage}%`;
        document.getElementById('riskReasoning').innerText = risk.reasoning;
        
        const rList = document.getElementById('riskActions');
        rList.innerHTML = (risk.future_proof_actions || []).map(a => `<li>• ${a}</li>`).join('');

        // Color coding
        const border = document.getElementById('riskLevelBorder');
        const badge = document.getElementById('riskLabel');
        const bar = document.getElementById('riskBar');

        border.className = "glass-panel p-6 rounded-xl border-l-4";
        badge.className = "text-[10px] uppercase tracking-widest px-2 py-0.5 rounded font-bold";
        bar.className = "h-full transition-all duration-1000";

        if (risk.ai_substitution_risk === 'very_high') {
            border.classList.add('border-red-600');
            badge.classList.add('bg-red-600/20', 'text-red-500');
            bar.classList.add('bg-red-600');
        } else if (risk.ai_substitution_risk === 'high') {
            border.classList.add('border-orange-500');
            badge.classList.add('bg-orange-500/20', 'text-orange-500');
            bar.classList.add('bg-orange-500');
        } else if (risk.ai_substitution_risk === 'medium') {
            border.classList.add('border-yellow-500');
            badge.classList.add('bg-yellow-500/20', 'text-yellow-500');
            bar.classList.add('bg-yellow-500');
        } else {
            border.classList.add('border-green-500');
            badge.classList.add('bg-green-500/20', 'text-green-500');
            bar.classList.add('bg-green-500');
        }
    }

    // Salary Card
    if (data.salary_intelligence) {
        document.getElementById('salMarket').innerText = data.salary_intelligence.current_market_range || '-';
        document.getElementById('salEst').innerText = data.salary_intelligence.your_estimated_range || '-';
        document.getElementById('salNext').innerText = data.salary_intelligence.to_reach_next_level || '-';
        document.getElementById('salTip').innerText = data.salary_intelligence.negotiation_tip || '-';
    }

    // Actions
    if (data.immediate_actions) {
        const box = document.getElementById('actionsList');
        box.innerHTML = '';
        data.immediate_actions.forEach(act => {
            let color = 'border-brand-accent';
            if (act.priority === 'urgent') color = 'border-red-500';
            else if (act.priority === 'high') color = 'border-orange-500';

            box.innerHTML += `
                <div class="border-l-4 ${color} bg-slate-800/50 p-3 rounded-r-lg flex flex-col gap-1">
                    <div class="flex justify-between">
                        <span class="font-semibold text-white text-sm">${act.action}</span>
                        <span class="text-xs text-slate-400 bg-slate-700 px-2 py-0.5 rounded">${act.time_required}</span>
                    </div>
                    <span class="text-xs ${act.priority==='urgent'?'text-red-400':'text-slate-400'}">${act.impact}</span>
                </div>
            `;
        });
    }

    // Chart.js
    if (data.skill_gap_chart && data.skill_gap_chart.length > 0) {
        if (chartInstance) chartInstance.destroy();
        
        const labels = data.skill_gap_chart.map(s => s.skill).slice(0, 8);
        const uLevel = data.skill_gap_chart.map(s => s.user_level).slice(0, 8);
        const mDemand = data.skill_gap_chart.map(s => s.market_demand).slice(0, 8);

        const ctx = document.getElementById('skillGapChart').getContext('2d');
        Chart.defaults.color = '#94a3b8';
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Your Level',
                        data: uLevel,
                        backgroundColor: '#38bdf8', // brand-accent
                        barPercentage: 0.6,
                        categoryPercentage: 0.8
                    },
                    {
                        label: 'Market Demand',
                        data: mDemand,
                        backgroundColor: '#fbbf24', // warning an orange hue
                        barPercentage: 0.6,
                        categoryPercentage: 0.8
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    y: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // Roadmap timeline
    if (data.career_roadmap) {
        document.getElementById('roadmapTarget').innerText = data.career_roadmap.target_role || '';
        const tbox = document.getElementById('roadmapTimeline');
        tbox.innerHTML = '';
        if (data.career_roadmap.milestones) {
            data.career_roadmap.milestones.forEach((m, i) => {
                let colorClass = 'bg-brand-accent shadow-[0_0_10px_#38bdf8]';
                if (m.month > 3 && m.month <= 6) colorClass = 'bg-purple-500 shadow-[0_0_10px_#a855f7]';
                else if (m.month > 6) colorClass = 'bg-green-500 shadow-[0_0_10px_#22c55e]';

                const skillsHTML = (m.skills_to_learn || []).map(s => `<span class="bg-slate-700 text-xs px-2 py-0.5 rounded">${s}</span>`).join('');
                const actsHTML = (m.actions || []).map(a => `<li class="text-sm text-slate-400 list-disc ml-4">${a}</li>`).join('');

                tbox.innerHTML += `
                    <div class="mb-8 relative pl-6">
                        <div class="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full ${colorClass}"></div>
                        <h3 class="font-bold text-white mb-1">Month ${m.month}: ${m.title}</h3>
                        <div class="flex flex-wrap gap-2 mb-2">${skillsHTML}</div>
                        <ul class="mb-2 space-y-1">${actsHTML}</ul>
                        <div class="text-xs text-brand-accent">Outcome: ${m.outcome}</div>
                    </div>
                `;
            });
        }
    }

    // Job Matches
    if (data.job_matches) {
        const jbox = document.getElementById('jobMatchesGrid');
        jbox.innerHTML = '';
        
        let sortedJobs = [...data.job_matches].sort((a,b) => b.match_score - a.match_score);
        sortedJobs.forEach(job => {
            const hasHTML = (job.skills_you_have || []).map(s => `<span class="bg-green-500/20 text-green-400 border border-green-500/30 text-[10px] px-1.5 py-0.5 rounded">${s}</span>`).join('');
            const needsHTML = (job.skills_you_need || []).map(s => `<span class="bg-orange-500/20 text-orange-400 border border-orange-500/30 text-[10px] px-1.5 py-0.5 rounded">${s}</span>`).join('');
            
            // CSS only circle
            const dashConfig = Math.round(job.match_score * 1.25); // roughly map 0-100 to stroke-dasharray (circumference ~ 125)
            
            jbox.innerHTML += `
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div class="flex-grow">
                        <h4 class="font-bold text-white text-lg">${job.title}</h4>
                        <div class="text-sm text-slate-400 mb-2">${job.company} • <span class="text-green-400">${job.salary_range}</span></div>
                        <div class="flex flex-wrap gap-1 mb-1">${hasHTML}</div>
                        <div class="flex flex-wrap gap-1">${needsHTML}</div>
                    </div>
                    
                    <div class="flex flex-row md:flex-col items-center gap-4 w-full md:w-auto mt-2 md:mt-0 justify-between md:justify-center">
                        <!-- CSS Circle -->
                        <div class="relative w-12 h-12 flex items-center justify-center">
                            <svg class="w-full h-full transform -rotate-90">
                                <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="4" fill="transparent" class="text-slate-700" />
                                <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="4" fill="transparent" stroke-dasharray="${dashConfig}, 200" class="${job.match_score > 80 ? 'text-green-500' : 'text-brand-accent'}" />
                            </svg>
                            <span class="absolute text-xs font-bold">${job.match_score}%</span>
                        </div>
                        <a href="${job.apply_url === '#' ? 'javascript:void(0)' : job.apply_url}" target="_blank" class="px-4 py-1 border border-brand-accent text-brand-accent text-sm rounded hover:bg-brand-accent hover:text-slate-900 transition-colors">View Job</a>
                    </div>
                </div>
            `;
        });
    }
}

async function fetchDisruptionRadar(userProfile) {
    const radarContainer = document.getElementById('aiDisruptionRadarContainer');
    radarContainer.classList.remove('hidden'); // Show the layout immediately with loading text
    
    try {
        const res = await fetch('/api/disruption-check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                role: userProfile.target_role || userProfile.current_role,
                skills: userProfile.current_skills
            })
        });

        if (res.ok) {
            const data = await res.json();
            renderDisruptionRadar(data);
        }
    } catch(err) {
        console.error("Disruption Radar Error", err);
    }
}

function renderDisruptionRadar(data) {
    if (!data) return;

    // 1. Score
    const score = Number(data.job_security_score) || 0;
    const scoreText = document.getElementById('radarScoreValue');
    const scoreCircle = document.getElementById('radarScoreCircle');
    const badge = document.getElementById('radarScoreLabelBadge');

    scoreText.innerText = score.toString();
    
    // Circumference for r=88 is 2 * PI * 88 = ~552.92
    const circumference = 553;
    const offset = circumference - (score / 100) * circumference;
    scoreCircle.style.strokeDasharray = `${circumference}, 1000`;
    scoreCircle.style.strokeDashoffset = offset.toString();

    badge.innerText = data.security_label || "AI-Resilient";
    badge.className = "px-6 py-2 rounded-full text-lg font-bold border w-full text-center tracking-wide mt-4";
    
    scoreCircle.classList.remove('text-brand-accent', 'text-green-500', 'text-yellow-500', 'text-orange-500', 'text-red-500');
    if (score >= 80) {
        badge.classList.add('bg-green-500/20', 'text-green-400', 'border-green-500/50');
        scoreCircle.classList.add('text-green-400');
    } else if (score >= 60) {
        badge.classList.add('bg-yellow-500/20', 'text-yellow-400', 'border-yellow-500/50');
        scoreCircle.classList.add('text-yellow-400');
    } else if (score >= 40) {
        badge.classList.add('bg-orange-500/20', 'text-orange-400', 'border-orange-500/50');
        scoreCircle.classList.add('text-orange-400');
    } else {
        badge.classList.add('bg-red-500/20', 'text-red-400', 'border-red-500/50');
        scoreCircle.classList.add('text-red-400');
    }

    // 2. Skill Bars
    const list = document.getElementById('radarSkillsList');
    list.innerHTML = '';
    if (data.skill_analysis && Array.isArray(data.skill_analysis)) {
        data.skill_analysis.forEach(sk => {
            const risk = Number(sk.automation_risk_percent) || 0;
            const safe = 100 - risk;
            const isValuable = sk.direction === 'more_valuable';
            
            list.innerHTML += `
                <div class="mb-3">
                    <div class="flex justify-between text-xs mb-1 font-semibold text-slate-300">
                        <span class="flex items-center gap-1">${sk.skill} ${isValuable ? '<span class="text-brand-accent text-sm" title="Becomes more valuable">★</span>' : ''}</span>
                        <span>${risk}% At Risk</span>
                    </div>
                    <div class="flex h-2 w-full rounded overflow-hidden">
                        <div style="width: ${safe}%" class="bg-green-500" title="Safe"></div>
                        <div style="width: ${risk}%" class="bg-red-500" title="At Risk"></div>
                    </div>
                    <div class="text-[10px] text-slate-400 mt-1 italic">${sk.reason || ''}</div>
                </div>
            `;
        });
    }

    // 3. Highlight Box
    document.getElementById('radarPrioritySkill').innerText = data.top_priority_skill || "Not Specified";
    document.getElementById('radarThreat').innerText = data.biggest_threat || "Unknown";
    document.getElementById('radarOpportunity').innerText = data.biggest_opportunity || "Unknown";

    const plan = document.getElementById('radarPlan');
    plan.innerHTML = '';
    if (data.ninety_day_plan && Array.isArray(data.ninety_day_plan)) {
        data.ninety_day_plan.forEach(step => {
            plan.innerHTML += `<li>${step}</li>`;
        });
    }
}
