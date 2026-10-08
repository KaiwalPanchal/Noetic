{{preamble}}

# Your job: deconstruct reference websites into a UI build spec ("steal like an artist")

Framework to apply:
{{framework}}

Reference URLs:
{{references}}

What the owner wants to build: {{goal}}

Instructions:
1. Fetch each reference. Identify the notable elements: hero, navigation, grid, cards, typography system, transitions, scroll behavior, cursor effects, micro-interactions.
2. For each element, give:
   - `implementation`: the likely technique (e.g. CSS grid 12-col, GSAP ScrollTrigger pin+scrub, Framer Motion layout animations, WebGL shader, View Transitions API)
   - `why_it_works`: the taste judgment, not a description
   - `steal`: the MECHANISM to reuse
   - `transform`: how to make the expression the owner's own (type, color, timing, copy)
3. Steal from many: prefer combining elements across references.
4. `do_not_copy`: brand assets, logos, copy text, images, licensed fonts, proprietary code.
5. `acceptance`: testable criteria, always including reduced-motion support and 375px mobile width with no horizontal scroll.
6. Element ids are E1, E2, …  The slug is kebab-case.
7. If a reference can't be fetched, say so in `seen_at` and work from what you can verify. Don't invent details.
