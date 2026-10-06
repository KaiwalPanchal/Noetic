"""Generate minimalist, high-professional vector diagrams for Overmind README.
"""
from pathlib import Path

ASSETS_DIR = Path(r"C:\External Apps\overmind-taste-engine\assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def generate_loop_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 620" width="100%" height="100%">
  <defs>
    <!-- Background styling -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B0F17"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>

    <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#818CF8"/>
    </linearGradient>

    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#161F30"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>

    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#818CF8"/>
      <stop offset="100%" stop-color="#C084FC"/>
    </linearGradient>

    <!-- Drop Shadows -->
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.45"/>
    </filter>

    <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <!-- Markers -->
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748B"/>
    </marker>
    <marker id="arrow-sky" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38BDF8"/>
    </marker>
    <marker id="arrow-indigo" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#818CF8"/>
    </marker>
    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34D399"/>
    </marker>

    <!-- Grid pattern -->
    <pattern id="dotPattern" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="#334155" fill-opacity="0.35"/>
    </pattern>
  </defs>

  <style>
    .mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, sans-serif; }
    .card-title { font-weight: 600; font-size: 14px; fill: #F8FAFC; }
    .card-body { font-size: 12px; fill: #94A3B8; }
    .badge-text { font-size: 11px; font-weight: 600; }
  </style>

  <!-- Container Box -->
  <rect width="1080" height="620" rx="16" fill="url(#bgGrad)" stroke="#1E293B" stroke-width="1.5"/>
  <rect width="1080" height="620" rx="16" fill="url(#dotPattern)" opacity="0.65"/>

  <!-- Top Header -->
  <g transform="translate(48, 38)">
    <rect width="132" height="24" rx="6" fill="#1E1B4B" stroke="#4338CA" stroke-width="1"/>
    <text x="66" y="16" class="mono badge-text" fill="#A5B4FC" text-anchor="middle" letter-spacing="1">OVERMIND LOOP</text>
    <text x="146" y="18" class="sans" font-size="18" font-weight="600" fill="#F8FAFC">From High-Signal Intake to Validated Execution</text>
    <text x="0" y="44" class="sans" font-size="12" fill="#64748B">Continuous ingestion, mental-model extraction, and taste-filtered application across content, code, and decisions.</text>
  </g>

  <!-- ================= ROW 1: THE CORE PIPELINE ================= -->

  <!-- CARD 1: SOURCES -->
  <g transform="translate(48, 115)" filter="url(#shadow)">
    <rect width="190" height="175" rx="12" fill="url(#cardGrad)" stroke="#1E293B" stroke-width="1.5"/>
    <rect x="0" y="0" width="190" height="3" rx="1.5" fill="#38BDF8"/>
    
    <!-- Card Header -->
    <text x="20" y="32" class="sans card-title">Sources</text>
    <text x="20" y="48" class="sans" font-size="11" fill="#64748B">Raw Signal Intake</text>
    
    <!-- Items -->
    <g transform="translate(20, 68)">
      <circle cx="4" cy="7" r="2.5" fill="#38BDF8"/>
      <text x="14" y="11" class="sans card-body">Books &amp; Essays</text>
      
      <circle cx="4" cy="29" r="2.5" fill="#38BDF8"/>
      <text x="14" y="33" class="sans card-body">High-Signal URLs &amp; Sites</text>
      
      <circle cx="4" cy="51" r="2.5" fill="#38BDF8"/>
      <text x="14" y="55" class="sans card-body">Deep-Dive Topic Threads</text>
      
      <circle cx="4" cy="73" r="2.5" fill="#38BDF8"/>
      <text x="14" y="77" class="sans card-body">Technical Papers &amp; Code</text>
    </g>
  </g>

  <!-- CONNECTOR 1: SOURCES -> INGEST -> FRAMEWORKS -->
  <path d="M 238 202 L 312 202" stroke="#38BDF8" stroke-width="1.8" marker-end="url(#arrow-sky)"/>
  <g transform="translate(242, 172)">
    <rect width="66" height="24" rx="12" fill="#0F172A" stroke="#0284C7" stroke-width="1.2"/>
    <text x="33" y="16" class="mono" font-size="11" font-weight="600" fill="#38BDF8" text-anchor="middle">/ingest</text>
  </g>

  <!-- CARD 2: FRAMEWORKS -->
  <g transform="translate(320, 115)" filter="url(#shadow)">
    <rect width="215" height="175" rx="12" fill="url(#cardGrad)" stroke="#3730A3" stroke-width="1.5"/>
    <rect x="0" y="0" width="215" height="3" rx="1.5" fill="#818CF8"/>
    
    <!-- Card Header -->
    <text x="20" y="32" class="sans card-title">Frameworks</text>
    <text x="120" y="32" class="mono" font-size="10" fill="#818CF8">frameworks/</text>
    <text x="20" y="48" class="sans" font-size="11" fill="#64748B">Extracted Mental Models</text>
    
    <!-- Items -->
    <g transform="translate(20, 68)">
      <circle cx="4" cy="7" r="2.5" fill="#818CF8"/>
      <text x="14" y="11" class="sans card-body">Core Principles</text>
      
      <circle cx="4" cy="29" r="2.5" fill="#818CF8"/>
      <text x="14" y="33" class="sans card-body">Executable Mental Moves</text>
      
      <circle cx="4" cy="51" r="2.5" fill="#818CF8"/>
      <text x="14" y="55" class="sans card-body">Anti-Patterns &amp; Traps</text>
      
      <circle cx="4" cy="73" r="2.5" fill="#818CF8"/>
      <text x="14" y="77" class="sans card-body">Genealogy &amp; Attribution</text>
    </g>
  </g>

  <!-- CONNECTOR 2: FRAMEWORKS -> APPLY -> OUTPUTS -->
  <path d="M 535 202 L 585 202" stroke="#818CF8" stroke-width="1.8"/>
  <path d="M 585 202 C 605 202, 605 142, 625 142 L 638 142" stroke="#818CF8" stroke-width="1.8" marker-end="url(#arrow-indigo)"/>
  <path d="M 585 202 L 638 202" stroke="#818CF8" stroke-width="1.8" marker-end="url(#arrow-indigo)"/>
  <path d="M 585 202 C 605 202, 605 262, 625 262 L 638 262" stroke="#818CF8" stroke-width="1.8" marker-end="url(#arrow-indigo)"/>
  
  <g transform="translate(548, 172)">
    <rect width="60" height="24" rx="12" fill="#0F172A" stroke="#6366F1" stroke-width="1.2"/>
    <text x="30" y="16" class="mono" font-size="11" font-weight="600" fill="#A5B4FC" text-anchor="middle">/apply</text>
  </g>

  <!-- THREE OUTPUT CARDS -->
  <!-- OUTPUT 1: CONTENT -->
  <g transform="translate(648, 115)" filter="url(#shadow)">
    <rect width="384" height="52" rx="10" fill="url(#cardGrad)" stroke="#1E293B" stroke-width="1.2"/>
    <text x="16" y="24" class="sans" font-size="13" font-weight="600" fill="#F8FAFC">Content Package</text>
    <text x="16" y="40" class="sans" font-size="11" fill="#64748B">Topic deep-dives &amp; sharp takes</text>
    
    <g transform="translate(195, 14)">
      <rect width="52" height="22" rx="6" fill="#1E293B" stroke="#475569" stroke-width="1"/>
      <text x="26" y="15" class="mono" font-size="10" fill="#94A3B8" text-anchor="middle">/draft</text>
      
      <path d="M 56 11 L 70 11" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow)"/>
      
      <rect x="76" y="0" width="48" height="22" rx="6" fill="#064E3B" stroke="#059669" stroke-width="1"/>
      <text x="100" y="15" class="mono" font-size="10" font-weight="600" fill="#34D399" text-anchor="middle">/ship</text>
      
      <text x="134" y="15" class="sans" font-size="11" font-weight="500" fill="#10B981">You post</text>
    </g>
  </g>

  <!-- OUTPUT 2: CODE BRIEF -->
  <g transform="translate(648, 177)" filter="url(#shadow)">
    <rect width="384" height="52" rx="10" fill="url(#cardGrad)" stroke="#1E293B" stroke-width="1.2"/>
    <text x="16" y="24" class="sans" font-size="13" font-weight="600" fill="#F8FAFC">Code Build Brief</text>
    <text x="16" y="40" class="sans" font-size="11" fill="#64748B">Site replication, layout &amp; mechanics</text>
    
    <g transform="translate(240, 15)">
      <path d="M 0 11 L 16 11" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow)"/>
      <rect x="22" y="0" width="112" height="22" rx="6" fill="#1E1B4B" stroke="#4338CA" stroke-width="1"/>
      <text x="78" y="15" class="sans" font-size="10" font-weight="500" fill="#A5B4FC" text-anchor="middle">Coding Agent (Codex/Claude)</text>
    </g>
  </g>

  <!-- OUTPUT 3: PROJECT DECISION -->
  <g transform="translate(648, 239)" filter="url(#shadow)">
    <rect width="384" height="52" rx="10" fill="url(#cardGrad)" stroke="#1E293B" stroke-width="1.2"/>
    <text x="16" y="24" class="sans" font-size="13" font-weight="600" fill="#F8FAFC">Project Decision</text>
    <text x="16" y="40" class="sans" font-size="11" fill="#64748B">Trade-offs, stances &amp; next actions</text>
    
    <g transform="translate(240, 15)">
      <path d="M 0 11 L 16 11" stroke="#475569" stroke-width="1.2" marker-end="url(#arrow)"/>
      <rect x="22" y="0" width="112" height="22" rx="6" fill="#1E293B" stroke="#475569" stroke-width="1"/>
      <text x="78" y="15" class="sans" font-size="10" font-weight="500" fill="#94A3B8" text-anchor="middle">Project Notes / Wiki</text>
    </g>
  </g>

  <!-- ================= ROW 2: THE STEERING FOUNDATION ================= -->

  <g transform="translate(48, 330)" filter="url(#shadow)">
    <!-- Base Container -->
    <rect width="984" height="248" rx="14" fill="#0C1322" stroke="#1E293B" stroke-width="1.5"/>
    
    <!-- Top badge -->
    <g transform="translate(24, 18)">
      <rect width="170" height="22" rx="6" fill="#1E293B" stroke="#334155" stroke-width="1"/>
      <text x="85" y="15" class="mono badge-text" fill="#94A3B8" text-anchor="middle">TASTE INFRASTRUCTURE</text>
      <text x="182" y="16" class="sans" font-size="13" font-weight="600" fill="#F8FAFC">Steering Engine &amp; Continuous Feedback</text>
    </g>

    <!-- COLUMN 1: TASTE GRAPH & STANCES -->
    <g transform="translate(24, 56)">
      <rect width="310" height="168" rx="10" fill="#111827" stroke="#1F2937" stroke-width="1.2"/>
      <text x="18" y="26" class="sans" font-size="13" font-weight="600" fill="#F1F5F9">Taste Graph &amp; Stances</text>
      <rect x="195" y="12" width="98" height="20" rx="4" fill="#1E293B"/>
      <text x="244" y="26" class="mono" font-size="10" fill="#38BDF8" text-anchor="middle">interests.md</text>
      
      <g transform="translate(18, 48)">
        <text x="0" y="14" class="sans" font-size="11" font-weight="600" fill="#F59E0B">Stances</text>
        <text x="60" y="14" class="sans" font-size="11" fill="#94A3B8">— What you believe &amp; defend</text>
        
        <text x="0" y="38" class="sans" font-size="11" font-weight="600" fill="#F43F5E">Negative Filters</text>
        <text x="96" y="38" class="sans" font-size="11" fill="#94A3B8">— What you explicitly reject</text>
        
        <text x="0" y="62" class="sans" font-size="11" font-weight="600" fill="#10B981">Exemplars</text>
        <text x="70" y="62" class="sans" font-size="11" fill="#94A3B8">— Uncompromising gold standards</text>
        
        <path d="M 0 80 L 274 80" stroke="#1E293B" stroke-width="1"/>
        <text x="0" y="100" class="sans" font-size="11" fill="#64748B">Judgment compounds: every saved stance</text>
        <text x="0" y="115" class="sans" font-size="11" fill="#64748B">improves future agent outputs.</text>
      </g>
    </g>

    <!-- COLUMN 2: ACTIVE TASTE ENGINES (Curate & Research) -->
    <g transform="translate(354, 56)">
      <rect width="280" height="168" rx="10" fill="#111827" stroke="#1F2937" stroke-width="1.2"/>
      <text x="18" y="26" class="sans" font-size="13" font-weight="600" fill="#F1F5F9">Active Discovery</text>
      <text x="18" y="42" class="sans" font-size="11" fill="#64748B">Taste-directed exploration</text>

      <g transform="translate(18, 58)">
        <!-- Curate Box -->
        <rect width="244" height="42" rx="8" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
        <rect x="10" y="10" width="62" height="22" rx="6" fill="#1E293B" stroke="#0284C7" stroke-width="1"/>
        <text x="41" y="25" class="mono" font-size="10" font-weight="600" fill="#38BDF8" text-anchor="middle">/curate</text>
        <text x="82" y="20" class="sans" font-size="11" font-weight="600" fill="#E2E8F0">Vault-Only Idea Mining</text>
        <text x="82" y="32" class="sans" font-size="10" fill="#64748B">Finds non-obvious connections</text>

        <!-- Research Box -->
        <g transform="translate(0, 52)">
          <rect width="244" height="42" rx="8" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
          <rect x="10" y="10" width="76" height="22" rx="6" fill="#1E293B" stroke="#6366F1" stroke-width="1"/>
          <text x="48" y="25" class="mono" font-size="10" font-weight="600" fill="#818CF8" text-anchor="middle">/research</text>
          <text x="96" y="20" class="sans" font-size="11" font-weight="600" fill="#E2E8F0">Taste-Filtered Web</text>
          <text x="96" y="32" class="sans" font-size="10" fill="#64748B">Discards low-signal noise</text>
        </g>
      </g>
    </g>

    <!-- COLUMN 3: BUILD-IN-PUBLIC & FEEDBACK -->
    <g transform="translate(654, 56)">
      <rect width="306" height="168" rx="10" fill="#111827" stroke="#1F2937" stroke-width="1.2"/>
      <text x="18" y="26" class="sans" font-size="13" font-weight="600" fill="#F1F5F9">Build Log &amp; Journey</text>
      <rect x="180" y="12" width="108" height="20" rx="4" fill="#1E293B"/>
      <text x="234" y="26" class="mono" font-size="10" fill="#34D399" text-anchor="middle">Twitter/journey/</text>

      <g transform="translate(18, 54)">
        <rect width="70" height="22" rx="6" fill="#064E3B" stroke="#059669" stroke-width="1"/>
        <text x="35" y="15" class="mono" font-size="10" font-weight="600" fill="#34D399" text-anchor="middle">/journey</text>
        <text x="82" y="16" class="sans" font-size="11" font-weight="600" fill="#E2E8F0">Build-in-public ledger</text>

        <text x="0" y="44" class="sans" font-size="11" fill="#94A3B8">• Records what shipped, broke &amp; decided</text>
        <text x="0" y="64" class="sans" font-size="11" fill="#94A3B8">• Built-in privacy gate prevents leaks</text>
        <text x="0" y="84" class="sans" font-size="11" fill="#94A3B8">• Closes loop: learnings update the taste graph</text>
      </g>
    </g>
  </g>

  <!-- UPWARD STEERING ARROWS -->
  <!-- Steering to Intake & Frameworks -->
  <path d="M 494 330 L 494 298" stroke="#6366F1" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#arrow-indigo)"/>
  <!-- Feedback from Journey back to Taste Graph -->
  <path d="M 807 554 C 807 596, 179 596, 179 554" fill="none" stroke="#34D399" stroke-width="1.6" stroke-dasharray="4,4" marker-end="url(#arrow-emerald)"/>
  <g transform="translate(420, 584)">
    <rect width="180" height="20" rx="4" fill="#0B0F17" stroke="#059669" stroke-width="1"/>
    <text x="90" y="14" class="sans" font-size="10" font-weight="600" fill="#34D399" text-anchor="middle">Learnings Compound into Taste</text>
  </g>
</svg>
'''
    (ASSETS_DIR / "overmind-loop.svg").write_text(svg, encoding="utf-8")
    print("overmind-loop.svg generated")

def generate_architecture_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 640" width="100%" height="100%">
  <defs>
    <linearGradient id="archBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B0F17"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>

    <linearGradient id="cardGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#161F30"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>

    <pattern id="dotPattern2" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="#334155" fill-opacity="0.35"/>
    </pattern>

    <filter id="archShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.5"/>
    </filter>

    <marker id="archArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748B"/>
    </marker>
    <marker id="archArrowIndigo" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#818CF8"/>
    </marker>
  </defs>

  <style>
    .mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, sans-serif; }
    .layer-title { font-size: 15px; font-weight: 700; letter-spacing: 0.5px; fill: #F8FAFC; }
    .card-title { font-weight: 600; font-size: 13px; fill: #F1F5F9; }
    .card-body { font-size: 11.5px; fill: #94A3B8; }
  </style>

  <rect width="1080" height="640" rx="16" fill="url(#archBg)" stroke="#1E293B" stroke-width="1.5"/>
  <rect width="1080" height="640" rx="16" fill="url(#dotPattern2)" opacity="0.65"/>

  <!-- Header -->
  <g transform="translate(48, 38)">
    <rect width="186" height="24" rx="6" fill="#1E1B4B" stroke="#4338CA" stroke-width="1"/>
    <text x="93" y="16" class="mono" font-size="11" font-weight="600" fill="#A5B4FC" text-anchor="middle" letter-spacing="1">MODULAR ARCHITECTURE</text>
    <text x="202" y="18" class="sans" font-size="18" font-weight="600" fill="#F8FAFC">The Four-Layer Engine Framework</text>
    <text x="0" y="44" class="sans" font-size="12" fill="#64748B">A modular Python architecture decoupling orchestration, persistent markdown knowledge, multi-agent tools, and human actions.</text>
  </g>

  <!-- DRIVERS / INTERFACES (TOP ROW) -->
  <g transform="translate(48, 105)">
    <!-- Claude Code Driver -->
    <g filter="url(#archShadow)">
      <rect width="474" height="54" rx="10" fill="#131B2E" stroke="#1E293B" stroke-width="1.2"/>
      <rect x="16" y="14" width="100" height="24" rx="6" fill="#1E293B" stroke="#0284C7" stroke-width="1"/>
      <text x="66" y="30" class="sans" font-size="11" font-weight="600" fill="#38BDF8" text-anchor="middle">Claude Code</text>
      <text x="128" y="27" class="sans" font-size="12" font-weight="600" fill="#F1F5F9">Interactive Vault Commands</text>
      <text x="128" y="42" class="mono" font-size="10.5" fill="#64748B">/ingest · /apply · /curate · /draft · /ship · /journey</text>
    </g>

    <!-- Python Pipeline Driver -->
    <g transform="translate(510, 0)" filter="url(#archShadow)">
      <rect width="474" height="54" rx="10" fill="#131B2E" stroke="#1E293B" stroke-width="1.2"/>
      <rect x="16" y="14" width="112" height="24" rx="6" fill="#1E293B" stroke="#6366F1" stroke-width="1"/>
      <text x="72" y="30" class="mono" font-size="11" font-weight="600" fill="#A5B4FC" text-anchor="middle">pipeline.py</text>
      <text x="140" y="27" class="sans" font-size="12" font-weight="600" fill="#F1F5F9">Multi-Agent Automated CLI</text>
      <text x="140" y="42" class="mono" font-size="10.5" fill="#64748B">python pipeline.py &lt;pipeline&gt; [--agent agy|codex|claude]</text>
    </g>
  </g>

  <!-- CONNECTOR TO ORCHESTRATION -->
  <path d="M 285 160 L 285 186" stroke="#475569" stroke-width="1.5" marker-end="url(#archArrow)"/>
  <path d="M 747 160 L 747 186" stroke="#475569" stroke-width="1.5" marker-end="url(#archArrow)"/>

  <!-- ================= LAYER 1: ORCHESTRATION ================= -->
  <g transform="translate(48, 190)" filter="url(#archShadow)">
    <rect width="984" height="114" rx="12" fill="#111827" stroke="#4338CA" stroke-width="1.5"/>
    <rect x="0" y="0" width="984" height="3" rx="1.5" fill="#818CF8"/>
    
    <g transform="translate(24, 20)">
      <text x="0" y="16" class="sans layer-title">1. ORCHESTRATION LAYER</text>
      <rect x="226" y="3" width="130" height="18" rx="4" fill="#1E1B4B"/>
      <text x="291" y="16" class="mono" font-size="10" fill="#A5B4FC" text-anchor="middle">taste_engine/orchestration/</text>
      <text x="0" y="36" class="sans" font-size="12" fill="#94A3B8">Control flow is deterministic Python. Steps are isolated agent calls, never open-ended runaway loops.</text>
    </g>

    <!-- Grid of Orchestration features -->
    <g transform="translate(24, 68)">
      <rect width="216" height="32" rx="6" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
      <text x="12" y="20" class="mono" font-size="11" fill="#38BDF8">registry.py</text>
      <text x="96" y="20" class="sans" font-size="11" fill="#94A3B8">Pipeline discovery</text>

      <g transform="translate(232, 0)">
        <rect width="216" height="32" rx="6" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
        <text x="12" y="20" class="mono" font-size="11" fill="#A5B4FC">run.py</text>
        <text x="64" y="20" class="sans" font-size="11" fill="#94A3B8">State &amp; pause/resume</text>
      </g>

      <g transform="translate(464, 0)">
        <rect width="236" height="32" rx="6" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
        <text x="12" y="20" class="mono" font-size="11" fill="#34D399">steps.py</text>
        <text x="76" y="20" class="sans" font-size="11" fill="#94A3B8">Route · validate · retry</text>
      </g>

      <g transform="translate(716, 0)">
        <rect width="220" height="32" rx="6" fill="#161F30" stroke="#1E293B" stroke-width="1"/>
        <text x="12" y="20" class="mono" font-size="11" fill="#FBBF24">fallback</text>
        <text x="74" y="20" class="sans" font-size="11" fill="#94A3B8">Cross-CLI failover</text>
      </g>
    </g>
  </g>

  <!-- THREE DOWNWARD CONNECTORS -->
  <path d="M 212 305 L 212 342" stroke="#475569" stroke-width="1.5" marker-end="url(#archArrow)"/>
  <path d="M 540 305 L 540 342" stroke="#475569" stroke-width="1.5" marker-end="url(#archArrow)"/>
  <path d="M 868 305 L 868 342" stroke="#475569" stroke-width="1.5" marker-end="url(#archArrow)"/>

  <!-- ================= THREE SUPPORTING LAYERS (BOTTOM ROW) ================= -->
  
  <!-- LAYER 2: KNOWLEDGE -->
  <g transform="translate(48, 348)" filter="url(#archShadow)">
    <rect width="312" height="200" rx="12" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="312" height="3" rx="1.5" fill="#38BDF8"/>
    
    <text x="18" y="28" class="sans card-title">2. KNOWLEDGE LAYER</text>
    <text x="18" y="44" class="mono" font-size="10" fill="#38BDF8">knowledge/</text>
    <text x="18" y="62" class="sans" font-size="11" fill="#64748B">The vault is the database</text>

    <g transform="translate(18, 78)">
      <circle cx="4" cy="7" r="2.5" fill="#38BDF8"/>
      <text x="14" y="11" class="mono" font-size="11" fill="#F1F5F9">config.py</text>
      <text x="76" y="11" class="sans card-body">— Vault &amp; engine paths</text>

      <circle cx="4" cy="31" r="2.5" fill="#38BDF8"/>
      <text x="14" y="35" class="mono" font-size="11" fill="#F1F5F9">context.py</text>
      <text x="82" y="35" class="sans card-body">— Budgeted context</text>

      <circle cx="4" cy="55" r="2.5" fill="#38BDF8"/>
      <text x="14" y="59" class="mono" font-size="11" fill="#F1F5F9">notes.py</text>
      <text x="72" y="59" class="sans card-body">— Note serialization</text>

      <path d="M 0 74 L 276 74" stroke="#1E293B" stroke-width="1"/>
      <text x="0" y="92" class="sans" font-size="11" font-weight="600" fill="#F43F5E">Strict Privacy Protection</text>
      <text x="0" y="106" class="sans" font-size="10.5" fill="#64748B">Private folders are never indexed or fed</text>
      <text x="0" y="119" class="sans" font-size="10.5" fill="#64748B">to any agent context.</text>
    </g>
  </g>

  <!-- LAYER 3: TOOLS -->
  <g transform="translate(384, 348)" filter="url(#archShadow)">
    <rect width="312" height="200" rx="12" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="312" height="3" rx="1.5" fill="#818CF8"/>
    
    <text x="18" y="28" class="sans card-title">3. TOOLS LAYER</text>
    <text x="18" y="44" class="mono" font-size="10" fill="#818CF8">tools/</text>
    <text x="18" y="62" class="sans" font-size="11" fill="#64748B">Stateless instruments &amp; adapters</text>

    <g transform="translate(18, 78)">
      <circle cx="4" cy="7" r="2.5" fill="#818CF8"/>
      <text x="14" y="11" class="mono" font-size="11" fill="#F1F5F9">agents.py</text>
      <text x="76" y="11" class="sans card-body">— Claude · Codex · Agy</text>

      <circle cx="4" cy="31" r="2.5" fill="#818CF8"/>
      <text x="14" y="35" class="mono" font-size="11" fill="#F1F5F9">prompts.py</text>
      <text x="84" y="35" class="sans card-body">— Versioned .md prompts</text>

      <circle cx="4" cy="55" r="2.5" fill="#818CF8"/>
      <text x="14" y="59" class="mono" font-size="11" fill="#F1F5F9">schema_check</text>
      <text x="100" y="59" class="sans card-body">— Strict JSON validation</text>

      <circle cx="4" cy="79" r="2.5" fill="#818CF8"/>
      <text x="14" y="83" class="mono" font-size="11" fill="#F1F5F9">links.py</text>
      <text x="68" y="83" class="sans card-body">— Real HTTP link verifier</text>

      <circle cx="4" cy="103" r="2.5" fill="#818CF8"/>
      <text x="14" y="107" class="mono" font-size="11" fill="#F1F5F9">tweets.py</text>
      <text x="78" y="107" class="sans card-body">— Character count validator</text>
    </g>
  </g>

  <!-- LAYER 4: ACTIONS -->
  <g transform="translate(720, 348)" filter="url(#archShadow)">
    <rect width="312" height="200" rx="12" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="312" height="3" rx="1.5" fill="#34D399"/>
    
    <text x="18" y="28" class="sans card-title">4. ACTIONS LAYER</text>
    <text x="18" y="44" class="mono" font-size="10" fill="#34D399">actions/</text>
    <text x="18" y="62" class="sans" font-size="11" fill="#64748B">Controlled side effects</text>

    <g transform="translate(18, 78)">
      <circle cx="4" cy="7" r="2.5" fill="#34D399"/>
      <text x="14" y="11" class="mono" font-size="11" fill="#F1F5F9">gate.py</text>
      <text x="66" y="11" class="sans card-body">— Human approval gate</text>

      <circle cx="4" cy="31" r="2.5" fill="#34D399"/>
      <text x="14" y="35" class="mono" font-size="11" fill="#F1F5F9">git.py</text>
      <text x="56" y="35" class="sans card-body">— Sandboxed branches</text>

      <path d="M 0 54 L 276 54" stroke="#1E293B" stroke-width="1"/>
      <text x="0" y="72" class="sans" font-size="11" font-weight="600" fill="#34D399">Zero Auto-Publishing</text>
      <text x="0" y="88" class="sans" font-size="10.5" fill="#64748B">All agent notes land as</text>
      <rect x="122" y="77" width="94" height="16" rx="3" fill="#1E293B"/>
      <text x="169" y="89" class="mono" font-size="9" fill="#F59E0B" text-anchor="middle">pending_review</text>
      <text x="0" y="104" class="sans" font-size="10.5" fill="#64748B">Code is built on clean git branches,</text>
      <text x="0" y="118" class="sans" font-size="10.5" fill="#64748B">never directly committed.</text>
    </g>
  </g>

  <!-- FOOTER PRINCIPLE BADGE -->
  <g transform="translate(48, 574)">
    <rect width="984" height="34" rx="8" fill="#0C1322" stroke="#1E293B" stroke-width="1"/>
    <text x="492" y="21" class="sans" font-size="11" font-weight="500" fill="#64748B" text-anchor="middle">
      <tspan fill="#818CF8" font-weight="600">Dependency Direction:</tspan> Pipelines → Orchestration → Tools / Actions → Knowledge. Lower layers never import higher ones.
    </text>
  </g>
</svg>
'''
    (ASSETS_DIR / "overmind-architecture.svg").write_text(svg, encoding="utf-8")
    print("overmind-architecture.svg generated")

def generate_pipeline_harness_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 340" width="100%" height="100%">
  <defs>
    <linearGradient id="pipeBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B0F17"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>

    <pattern id="dotPattern3" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="#334155" fill-opacity="0.35"/>
    </pattern>

    <filter id="pipeShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000000" flood-opacity="0.45"/>
    </filter>

    <marker id="pipeArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748B"/>
    </marker>
    <marker id="pipeArrowSky" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38BDF8"/>
    </marker>
    <marker id="pipeArrowEmerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34D399"/>
    </marker>
  </defs>

  <style>
    .mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, sans-serif; }
  </style>

  <rect width="1080" height="340" rx="16" fill="url(#pipeBg)" stroke="#1E293B" stroke-width="1.5"/>
  <rect width="1080" height="340" rx="16" fill="url(#dotPattern3)" opacity="0.65"/>

  <!-- Header -->
  <g transform="translate(48, 32)">
    <rect width="168" height="22" rx="6" fill="#1E1B4B" stroke="#4338CA" stroke-width="1"/>
    <text x="84" y="15" class="mono" font-size="10.5" font-weight="600" fill="#A5B4FC" text-anchor="middle" letter-spacing="1">AGENT HARNESS FLOW</text>
    <text x="182" y="16" class="sans" font-size="16" font-weight="600" fill="#F8FAFC">How Each Step Executes: Multi-Agent &amp; Fault-Tolerant</text>
    <text x="0" y="38" class="sans" font-size="11.5" fill="#64748B">Strict contracts, schema enforcement, link resolution, and seamless fallback between Claude, Codex, and Antigravity.</text>
  </g>

  <!-- 5 STAGES HORIZONTAL -->
  <!-- STAGE 1: TRIGGER -->
  <g transform="translate(48, 95)" filter="url(#pipeShadow)">
    <rect width="164" height="190" rx="10" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="164" height="3" rx="1.5" fill="#38BDF8"/>
    <text x="16" y="26" class="sans" font-size="12" font-weight="700" fill="#F8FAFC">1. INITIATION</text>
    <text x="16" y="42" class="mono" font-size="10" fill="#38BDF8">pipeline.py</text>
    
    <g transform="translate(16, 60)">
      <text x="0" y="14" class="sans" font-size="11" fill="#94A3B8">• Pipeline selected</text>
      <text x="0" y="34" class="sans" font-size="11" fill="#94A3B8">• Run ID generated</text>
      <rect x="0" y="44" width="132" height="20" rx="4" fill="#1E293B"/>
      <text x="66" y="58" class="mono" font-size="9" fill="#A5B4FC" text-anchor="middle">.taste-engine/runs/</text>
      <text x="0" y="80" class="sans" font-size="11" fill="#94A3B8">• State persisted</text>
      <text x="0" y="100" class="sans" font-size="11" fill="#94A3B8">• Resumes if broken</text>
    </g>
  </g>

  <path d="M 212 190 L 238 190" stroke="#38BDF8" stroke-width="1.5" marker-end="url(#pipeArrowSky)"/>

  <!-- STAGE 2: CONTEXT -->
  <g transform="translate(244, 95)" filter="url(#pipeShadow)">
    <rect width="170" height="190" rx="10" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="170" height="3" rx="1.5" fill="#818CF8"/>
    <text x="16" y="26" class="sans" font-size="12" font-weight="700" fill="#F8FAFC">2. CONTEXT &amp; SPEC</text>
    <text x="16" y="42" class="mono" font-size="10" fill="#818CF8">knowledge/ + contract</text>
    
    <g transform="translate(16, 60)">
      <text x="0" y="14" class="sans" font-size="11" fill="#94A3B8">• Token budgeting</text>
      <text x="0" y="34" class="sans" font-size="11" fill="#94A3B8">• Privacy filter denies</text>
      <text x="12" y="50" class="sans" font-size="10.5" fill="#F43F5E">private folders</text>
      <text x="0" y="74" class="sans" font-size="11" fill="#94A3B8">• Prompt template</text>
      <text x="0" y="94" class="sans" font-size="11" fill="#94A3B8">• Strict agent contract</text>
    </g>
  </g>

  <path d="M 414 190 L 440 190" stroke="#818CF8" stroke-width="1.5" marker-end="url(#pipeArrow)"/>

  <!-- STAGE 3: AGENT EXECUTION -->
  <g transform="translate(446, 95)" filter="url(#pipeShadow)">
    <rect width="186" height="190" rx="10" fill="#111827" stroke="#4338CA" stroke-width="1.2"/>
    <rect x="0" y="0" width="186" height="3" rx="1.5" fill="#A855F7"/>
    <text x="16" y="26" class="sans" font-size="12" font-weight="700" fill="#F8FAFC">3. AGENT STEP</text>
    <text x="16" y="42" class="mono" font-size="10" fill="#A855F7">tools/agents.py</text>
    
    <g transform="translate(16, 56)">
      <rect width="154" height="24" rx="4" fill="#1E293B"/>
      <text x="8" y="16" class="sans" font-size="10" font-weight="600" fill="#38BDF8">claude</text>
      <text x="54" y="16" class="sans" font-size="10" fill="#94A3B8">| sonnet via CLI</text>

      <g transform="translate(0, 30)">
        <rect width="154" height="24" rx="4" fill="#1E293B"/>
        <text x="8" y="16" class="sans" font-size="10" font-weight="600" fill="#818CF8">codex</text>
        <text x="48" y="16" class="sans" font-size="10" fill="#94A3B8">| exec w/ schema</text>
      </g>

      <g transform="translate(0, 60)">
        <rect width="154" height="24" rx="4" fill="#1E293B"/>
        <text x="8" y="16" class="sans" font-size="10" font-weight="600" fill="#34D399">agy</text>
        <text x="36" y="16" class="sans" font-size="10" fill="#94A3B8">| antigravity CLI</text>
      </g>

      <text x="0" y="106" class="sans" font-size="10.5" fill="#F59E0B">↳ Automatic failover</text>
      <text x="14" y="120" class="sans" font-size="10" fill="#64748B">if down, timeout or quota</text>
    </g>
  </g>

  <path d="M 632 190 L 658 190" stroke="#818CF8" stroke-width="1.5" marker-end="url(#pipeArrow)"/>

  <!-- STAGE 4: VALIDATION -->
  <g transform="translate(664, 95)" filter="url(#pipeShadow)">
    <rect width="170" height="190" rx="10" fill="#111827" stroke="#1E293B" stroke-width="1.2"/>
    <rect x="0" y="0" width="170" height="3" rx="1.5" fill="#F59E0B"/>
    <text x="16" y="26" class="sans" font-size="12" font-weight="700" fill="#F8FAFC">4. VALIDATION</text>
    <text x="16" y="42" class="mono" font-size="10" fill="#F59E0B">tools/schema_check</text>
    
    <g transform="translate(16, 60)">
      <text x="0" y="14" class="sans" font-size="11" fill="#94A3B8">• Strict JSON Schema</text>
      <text x="0" y="34" class="sans" font-size="11" fill="#94A3B8">• Real URL resolution</text>
      <text x="0" y="54" class="sans" font-size="11" fill="#94A3B8">• X character limits</text>
      <path d="M 0 68 L 138 68" stroke="#1E293B" stroke-width="1"/>
      <text x="0" y="86" class="sans" font-size="10.5" font-weight="600" fill="#F59E0B">✗ Invalid output?</text>
      <text x="0" y="102" class="sans" font-size="10" fill="#64748B">Retries 1x with exact error</text>
      <text x="0" y="116" class="sans" font-size="10" fill="#64748B">or triggers CLI fallback.</text>
    </g>
  </g>

  <path d="M 834 190 L 860 190" stroke="#34D399" stroke-width="1.5" marker-end="url(#pipeArrowEmerald)"/>

  <!-- STAGE 5: RESULT & HUMAN GATE -->
  <g transform="translate(866, 95)" filter="url(#pipeShadow)">
    <rect width="166" height="190" rx="10" fill="#111827" stroke="#059669" stroke-width="1.2"/>
    <rect x="0" y="0" width="166" height="3" rx="1.5" fill="#34D399"/>
    <text x="16" y="26" class="sans" font-size="12" font-weight="700" fill="#F8FAFC">5. HUMAN GATE</text>
    <text x="16" y="42" class="mono" font-size="10" fill="#34D399">actions/gate.py</text>
    
    <g transform="translate(16, 60)">
      <text x="0" y="14" class="sans" font-size="11" fill="#94A3B8">• Note written with</text>
      <rect x="0" y="22" width="134" height="20" rx="4" fill="#1E293B"/>
      <text x="67" y="36" class="mono" font-size="9" fill="#F59E0B" text-anchor="middle">status: pending_review</text>
      
      <text x="0" y="60" class="sans" font-size="11" fill="#94A3B8">• Human approval:</text>
      <rect x="0" y="68" width="134" height="20" rx="4" fill="#064E3B"/>
      <text x="67" y="82" class="mono" font-size="9" fill="#34D399" text-anchor="middle">pipeline.py approve</text>
      
      <text x="0" y="106" class="sans" font-size="10.5" fill="#10B981">✓ Zero auto-posts</text>
      <text x="0" y="120" class="sans" font-size="10.5" fill="#10B981">✓ Clean git branches</text>
    </g>
  </g>
</svg>
'''
    (ASSETS_DIR / "overmind-pipeline.svg").write_text(svg, encoding="utf-8")
    print("overmind-pipeline.svg generated")

if __name__ == "__main__":
    generate_loop_svg()
    generate_architecture_svg()
    generate_pipeline_harness_svg()
