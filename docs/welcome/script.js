/* ==========================================================================
   ARGUS — Interactions v3
   1) Nav state / scroll progress / mobile menu
   2) Reveal-on-scroll + active section highlight
   3) Hero live ReAct loop terminal
   4) Architecture ReAct diagram cycling
   5) Recon pipeline interactive stepper
   6) Live Studio session simulation
   7) Animated hero counters
   ========================================================================== */

'use strict';

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* --------------------------------------------------------------------------
 * 1. Navigation
 * ------------------------------------------------------------------------ */
const nav = document.getElementById('siteNav');
const progressBar = document.getElementById('scrollProgress');

function onScroll() {
    const y = window.scrollY;
    nav.classList.toggle('is-scrolled', y > 24);

    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    progressBar.style.width = max > 0 ? `${(y / max) * 100}%` : '0%';
}
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

const burger = document.getElementById('navBurger');
const mobileMenu = document.getElementById('mobileMenu');

burger.addEventListener('click', () => {
    const open = !mobileMenu.classList.contains('is-open');
    burger.classList.toggle('is-open', open);
    mobileMenu.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
});

mobileMenu.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => {
        burger.classList.remove('is-open');
        mobileMenu.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    })
);

/* --------------------------------------------------------------------------
 * 2. Reveal on scroll + active nav link
 * ------------------------------------------------------------------------ */
const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

const sectionLinks = document.querySelectorAll('.nav-links a[data-section]');
const sectionObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        sectionLinks.forEach(link =>
            link.classList.toggle('is-active', link.dataset.section === entry.target.id));
    });
}, { rootMargin: '-35% 0px -55% 0px' });

['architecture', 'recon', 'modules', 'studio', 'team'].forEach(id => {
    const el = document.getElementById(id);
    if (el) sectionObserver.observe(el);
});

/* --------------------------------------------------------------------------
 * 3. Hero live ReAct loop
 * ------------------------------------------------------------------------ */
const agentLoopEl = document.getElementById('agentLoop');

function alLine(cls, html) {
    const p = document.createElement('p');
    p.className = `al-line ${cls}`;
    p.innerHTML = html;
    agentLoopEl.appendChild(p);
    agentLoopEl.scrollTop = agentLoopEl.scrollHeight;
}

if (agentLoopEl && !prefersReducedMotion) {
    const cycles = [
        [
            ['al-cmd', '<span class="p">argus@ops:~$</span> argus brain --target staging.local --mode react-langgraph'],
            ['al-sys', '[brain] loading WhiteRabbitNeo-V3-7B via ollama <span class="al-ok">ok</span>'],
            ['al-sys', '[rag]   faiss index ready &middot; nomic-embed-text'],
            ['al-sys', '[wsl]   kali bridge connected &middot; 12 tools registered'],
            ['al-sep', '&#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183;'],
            ['', '<span class="al-tag-th">&#9670; THOUGHT</span>      <span class="al-dim">&ldquo;map the attack surface before any active contact.&rdquo;</span>'],
            ['', '<span class="al-tag-ac">&#9650; ACTION</span>       ReconService.passive_recon([&quot;subfinder&quot;, &quot;amass&quot;])'],
            ['', '<span class="al-tag-ob">&#9632; OBSERVATION</span>  <span class="al-dim">18 subdomains &middot; 4 alive hosts &rarr; memory.blackboard</span>']
        ],
        [
            ['', '<span class="al-tag-th">&#9670; THOUGHT</span>      <span class="al-dim">&ldquo;validate live hosts and fingerprint the stack.&rdquo;</span>'],
            ['', '<span class="al-tag-ac">&#9650; ACTION</span>       httpx probe + whatweb + wafw00f'],
            ['', '<span class="al-tag-ob">&#9632; OBSERVATION</span>  <span class="al-dim">nginx/1.24 &middot; waf detected &middot; admin gateway exposed :8080</span>'],
            ['al-warn', '! exposed admin gateway flagged for reflective verification'],
            ['al-sep', '&#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183; &#183;'],
            ['', '<span class="al-tag-th">&#9670; THOUGHT</span>      <span class="al-dim">&ldquo;reflect before exploitation &mdash; avoid WAF false positives.&rdquo;</span>'],
            ['', '<span class="al-tag-ac">&#9650; ACTION</span>       ReflectiveAgent.pre_execute_verify(finding#41)'],
            ['al-ok', '<i class="fa-solid fa-check"></i> findings persisted &middot; sqlite blackboard synchronized']
        ]
    ];

    let cycleIdx = 0;

    function playCycle() {
        const lines = cycles[cycleIdx];
        cycleIdx = (cycleIdx + 1) % cycles.length;
        let i = 0;

        function next() {
            if (i >= lines.length) {
                setTimeout(() => {
                    agentLoopEl.innerHTML = '';
                    playCycle();
                }, 2600);
                return;
            }
            alLine(lines[i][0], lines[i][1]);
            i++;
            setTimeout(next, i === 1 ? 900 : 620);
        }
        next();
    }
    playCycle();
} else if (agentLoopEl) {
    alLine('al-cmd', '<span class="p">argus@ops:~$</span> argus brain --target staging.local --mode react-langgraph');
    alLine('al-ok', '<i class="fa-solid fa-check"></i> brain online &middot; rag ready &middot; wsl bridge connected');
    alLine('', '<span class="al-tag-th">&#9670; THOUGHT</span> <span class="al-dim">map the attack surface.</span>');
    alLine('', '<span class="al-tag-ac">&#9650; ACTION</span> passive_recon([&quot;subfinder&quot;, &quot;amass&quot;])');
    alLine('al-ok', '<i class="fa-solid fa-check"></i> 18 subdomains discovered &middot; session synchronized');
}

/* --------------------------------------------------------------------------
 * 4. Architecture ReAct diagram cycling
 * ------------------------------------------------------------------------ */
const loopNodes = document.querySelectorAll('#loopDiagram .loop-node');
if (loopNodes.length && !prefersReducedMotion) {
    let nodeIdx = 0;
    setInterval(() => {
        loopNodes.forEach(n => n.classList.remove('is-active'));
        loopNodes[nodeIdx].classList.add('is-active');
        nodeIdx = (nodeIdx + 1) % loopNodes.length;
    }, 1500);
}

/* --------------------------------------------------------------------------
 * 5. Recon stepper
 * ------------------------------------------------------------------------ */
const phasePanel = document.getElementById('phasePanel');
const stepButtons = document.querySelectorAll('.step-btn');

const PHASES = [
    {
        name: 'Passive OSINT',
        desc: 'Silent asset and subdomain harvesting from public sources — zero packets touch the target while the surface map takes shape.',
        tools: ['Subfinder', 'Findomain', 'Amass', 'Assetfinder'],
        cmd: '$ recon passive --target staging.local\n[+] subfinder ....... 11 found\n[+] findomain ...... 4 new'
    },
    {
        name: 'Active Brute-Force',
        desc: 'DNS and endpoint brute-forcing with curated custom wordlists to force hidden surfaces into view.',
        tools: ['Gobuster', 'FFuf'],
        cmd: '$ recon bruteforce --wordlist deep\n[+] gobuster dns ... 6 vhosts\n[+] ffuf content ... 23 paths'
    },
    {
        name: 'Permutations',
        desc: 'Dynamic permutation synthesis expands the wordlist with naming conventions, then mass-resolves every candidate.',
        tools: ['DNSGen', 'MassDNS'],
        cmd: '$ recon permute --mode smart\n[+] dnsgen ......... 340 candidates\n[+] massdns ........ 7 resolved'
    },
    {
        name: 'Probing & Validation',
        desc: 'Every candidate is probed over HTTP/HTTPS — titles extracted, redirects followed, duplicates collapsed into one clean feed.',
        tools: ['HTTPX', 'anew'],
        cmd: '$ recon probe --ports 80,443,8080\n[+] httpx .......... 4 alive\n[+] anew ........... dedup ok'
    },
    {
        name: 'Deep Tech & Vulns',
        desc: 'Technology fingerprinting, WAF detection and template-driven vulnerability scanning turn a surface map into an attack plan.',
        tools: ['WhatWeb', 'Wafw00f', 'Nmap', 'Nuclei'],
        cmd: '$ recon deep --checks all\n[!] wafw00f ........ waf detected\n[+] nuclei ......... 2 findings'
    }
];

let phaseIdx = 0;
let phaseTimer = null;

function renderPhase(idx) {
    if (!phasePanel) return;
    phaseIdx = idx;
    const ph = PHASES[idx];
    phasePanel.classList.add('is-switching');
    phasePanel.innerHTML =
        '<div class="phase-main">' +
            `<h3><small>PHASE 0${idx + 1} / 05</small>${ph.name}</h3>` +
            `<p>${ph.desc}</p>` +
        '</div>' +
        '<div class="phase-side">' +
            '<div class="chip-row">' +
                ph.tools.map(t => `<span class="chip">${t}</span>`).join('') +
            '</div>' +
            `<pre class="phase-cmd"><span class="p">${ph.cmd.split('\n')[0]}</span>\n${ph.cmd.split('\n').slice(1).join('\n')}</pre>` +
        '</div>';
    setTimeout(() => phasePanel.classList.remove('is-switching'), 360);

    stepButtons.forEach((btn, i) => {
        btn.classList.toggle('is-active', i === idx);
        btn.setAttribute('aria-selected', String(i === idx));
    });
}

function startPhaseAutoplay() {
    stopPhaseAutoplay();
    if (prefersReducedMotion) return;
    phaseTimer = setInterval(() => renderPhase((phaseIdx + 1) % PHASES.length), 4200);
}
function stopPhaseAutoplay() {
    if (phaseTimer) { clearInterval(phaseTimer); phaseTimer = null; }
}

stepButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        stopPhaseAutoplay();
        renderPhase(Number(btn.dataset.phase));
    });
});

renderPhase(0);
startPhaseAutoplay();

/* --------------------------------------------------------------------------
 * 6. Live Studio simulation
 * ------------------------------------------------------------------------ */
const studioLogs = document.getElementById('studioLogs');
const studioBtn = document.getElementById('runStudioBtn');
const studioClock = document.getElementById('studioClock');

const SESSION = [
    { phase: 'initialization' },
    { cls: 'log-info',    t: '[INIT]  ArgusBrain booting via Ollama — model: WhiteRabbitNeo-V3-7B' },
    { cls: 'log-info',    t: '[RAG]   FAISS vector store loaded · embeddings: nomic-embed-text' },
    { cls: 'log-info',    t: '[WSL]   Kali bridge verified (subprocess/ssh) · 12 tools registered' },
    { phase: 'react loop' },
    { cls: 'log-ai',      t: '[THOUGHT] target given: staging.local → start with Phase 1 passive OSINT.' },
    { cls: 'log-info',    t: '[ACTION]  ReconService.execute_passive_recon(["subfinder","findomain","assetfinder"])' },
    { cls: 'log-success', t: '[OBSERV.] 18 live subdomains discovered · anew dedup pipeline passed' },
    { cls: 'log-ai',      t: '[THOUGHT] subdomains collected → run httpx validation, then nmap/nuclei.' },
    { cls: 'log-warning', t: '[DISCOVERY] exposed admin gateway at api.staging.local:8080' },
    { phase: 'reflection & memory' },
    { cls: 'log-ai',      t: '[REFLECT] pre_execute_verify running — filtering WAF traps & false positives' },
    { cls: 'log-success', t: '[MEMORY] findings + entity relations persisted to SQLite blackboard' },
    { cls: 'log-success', t: '[DONE]   recon cycle complete · session state synced to Studio UI' }
];

let studioRunning = false;

function stamp() {
    const d = new Date();
    const p = n => String(n).padStart(2, '0');
    return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function stLine(cls, text) {
    const p = document.createElement('p');
    p.className = `st-line ${cls}`;
    p.innerHTML = `<span class="st-time">${stamp()}</span>${text}`;
    studioLogs.appendChild(p);
    studioLogs.scrollTop = studioLogs.scrollHeight;
}

function runSession() {
    if (studioRunning || !studioLogs) return;
    studioRunning = true;
    studioLogs.innerHTML = '';
    if (studioBtn) {
        studioBtn.disabled = true;
        studioBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Executing…';
    }
    if (studioClock) studioClock.textContent = 'running';

    let i = 0;
    (function next() {
        if (i >= SESSION.length) {
            studioRunning = false;
            if (studioBtn) {
                studioBtn.disabled = false;
                studioBtn.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Re-run session';
            }
            if (studioClock) studioClock.textContent = 'complete ✓';
            return;
        }
        const step = SESSION[i];
        if (step.phase) {
            const tag = document.createElement('span');
            tag.className = 'st-phase';
            tag.textContent = `// ${step.phase}`;
            studioLogs.appendChild(tag);
        } else {
            stLine(step.cls, step.t);
        }
        i++;
        setTimeout(next, step.phase ? 350 : 640);
    })();
}

if (studioBtn) studioBtn.addEventListener('click', runSession);

// Auto-run when the studio section first scrolls into view
if (studioLogs) {
    const studioTrigger = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                studioTrigger.disconnect();
                setTimeout(runSession, prefersReducedMotion ? 0 : 500);
            }
        });
    }, { threshold: 0.35 });
    studioTrigger.observe(studioLogs);
}

/* --------------------------------------------------------------------------
 * 7. Animated hero counters
 * ------------------------------------------------------------------------ */
const counters = document.querySelectorAll('.hero-stats dt[data-count]');

function animateCounter(el) {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    if (prefersReducedMotion || target === 0) {
        el.textContent = target + suffix;
        return;
    }
    const duration = 1400;
    const start = performance.now();

    function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased) + suffix;
        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

if (counters.length) {
    const counterObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    counters.forEach(el => counterObserver.observe(el));
}

/* --------------------------------------------------------------------------
 * 8. Autoplay demo video on scroll
 * ------------------------------------------------------------------------ */
const demoVideo = document.getElementById('demoVideo');
const videoShell = document.getElementById('demoVideoShell');

if (demoVideo && videoShell) {
    const videoObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                demoVideo.play().catch(err => {
                    console.log('Autoplay prevented or waiting for interaction:', err);
                });
            } else {
                demoVideo.pause();
            }
        });
    }, { threshold: 0.25 });

    videoObserver.observe(videoShell);
}

