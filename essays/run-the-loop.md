# Run the Loop

*Thinking in frameworks, taste, and why iteration is the only algorithm that works.*

## Gen 0: The pots

There's this story I keep thinking about. A ceramics teacher splits his class in two. One half gets graded only on quantity, so fifty pounds of pots is an A. The other half gets graded on quality. They have to make just one pot, but it has to be perfect.

At the end of term, guess which side made the best pots. Bayles and Orland tell it in *Art & Fear*: "the works of highest quality were all produced by the group being graded for quantity." That group was "busily churning out piles of work — and learning from their mistakes." The quality group "had sat theorizing about perfection, and in the end had little more to show for their efforts than grandiose theories and a pile of dead clay."

So basically two things made those pots good. They made a lot of them. And after every pot, someone decided what was worth keeping.

Making a lot is cheap now. Deciding what to keep is the skill that's left.

## Gen 1: Frameworks are compressed thinking

There are a few things we've all heard from one place or another. Keep it simple, stupid. Thinking fast and slow. We repeat them like slogans. But each one is years of someone's thinking, folded small enough to carry around.

Shane Parrish at Farnam Street calls mental models "tools for compressing complexity into manageable chunks." Charlie Munger, in his 1994 talk at USC, said it harder: "If the facts don't hang together on a latticework of theory, you don't have them in a usable form." And he thought "80 or 90 important models will carry about 90% of the freight in making you a worldly-wise person."

Take KISS. It's attributed to Kelly Johnson at Lockheed's Skunk Works. The story is that he gave his engineers a handful of tools and said the jet had to be fixable by an average mechanic in the field with only those tools. Four letters, and a whole design philosophy inside them.

Or Bezos's doors, from his 2015 shareholder letter. One-way doors "must be made methodically, carefully, slowly." But "most decisions aren't like that – they are changeable, reversible – they're two-way doors." My own version of this is hats, haircuts and tattoos. If you're not sure about something, it's a hat. Try a few, you'll find what you like. A haircut has consequences for a while, but it grows out. And tattoos are, you know, just tattoos. Honestly most of what I lose sleep over turns out to be a hat.

I think this is the most underrated skill right now, because AI hands everyone answers. A Microsoft Research paper at CHI 2025 found that "higher confidence in GenAI is associated with less critical thinking." Paul Graham, in "Writes and Write-Nots," says where that ends up: "It will be a world of thinks and think-nots." Frameworks are how you stay with the thinks. They give you a way to judge an answer instead of just taking it.

## Gen 2: The bottleneck moved

For most of history, the hard part was getting through the material. That part is almost free now. Paste a forty-page report into a model and you get the argument back in a minute. AI basically solved consuming and understanding content.

What's left is judgement. Rick Rubin told 60 Minutes, "I know what I like and what I don't like. And I'm decisive about what I like and what I don't like." He calls himself a "reducer, instead of a producer." I think that's the job description now. The machine produces. Someone has to reduce.

Ira Glass has this bit called "The Gap": "All of us who do creative work, we get into it because we have good taste. But it's like there is this gap." His fix was volume: "It is only by going through a volume of work that you're going to catch up and close that gap." Now AI does the volume. So the gap flips. It used to be your hands lagging behind your taste. Now it's whether your taste can keep up with the output.

Paul Graham said it back in 2002, in "Taste for Makers": "We need good taste to make good things." Dylan Field of Figma, on Latent Space, named what sets you apart now as "brand, it's point of view, it's taste, it's craft, it's design."

For me, taste is three verbs. Keep, reject, build. The machine can help with everything else.

## Gen 3: Evolution is the only algorithm that works

Every pot was a test, and every test came back with a result. That's the whole trick, and nature runs the exact same code.

In *The Blind Watchmaker*, Richard Dawkins wrote a small program that had to reach "METHINKS IT IS LIKE A WEASEL." Pure single-step chance would take about "a million million million times as long as the universe has so far existed." With cumulative selection, where you keep the best of each round and mutate from there, it got there in 43 generations. One run finished "while I was out to lunch."

Machine learning is the same idea with calculus. Gradient descent guesses, measures the error, nudges, and repeats. Andrej Karpathy tweeted in 2017: "Gradient descent can write code better than you. I'm sorry."

Learning a skill works like this too. Ericsson and his colleagues, in their 1993 paper on deliberate practice, said learners "should receive immediate informative feedback and knowledge of results of their performance." James Dyson built 5,127 prototypes. "There were 5,126 failures. But I learned from each one."

And speed matters as much as count. John Boyd's OODA loop is observe, orient, decide, act. His point was that F-86 pilots could cycle that loop faster than MiG-15 pilots, and the faster loop wins. Gall's Law, from *Systemantics*, says the same thing about building: "A complex system that works is invariably found to have evolved from a simple system that worked. A complex system designed from scratch never works and cannot be patched up to make it work."

One more thing about those pots. The story didn't even start in a ceramics studio. Ted Orland later said it came from photographer Jerry Uelsmann's class, and they changed the medium for the book. So even the parable got iterated. I like it more for that.

My rule: the number of iterations and how fast you get feedback beat how good your first attempt is.

## Gen 4: The harness

None of this is new, by the way. In 1945 Vannevar Bush imagined the memex in "As We May Think," "an enlarged intimate supplement to his memory." It was built on one observation: "The human mind does not work that way. It operates by association." Niklas Luhmann actually built one out of paper. About 90,000 handwritten cards, more than 500 publications. He called his slip box "a kind of secondary memory... an alter ego with who we can constantly communicate."

A memory you can talk to. With agents, it can finally talk back.

So I built OverMind, and I'm putting it out as a framework of its own. It's an open-source harness with four blocks: projects, knowledge, tools and actions. You wire them in whatever order your work needs, because creative work never runs in a straight line.

The first thing it does is organise what I consume. I `/ingest` a book or a paper and I get a framework back, not a summary. A summary just sits there. A framework has moves you can make and rules for when to make them.

Then it holds my chain of thoughts. The stances I hold, the stuff I reject, that half-formed idea from last month. It's all on disk and linked, so the next idea starts from everything before it and not from zero. Bush had it right: "The process of tying two items together is the important thing."

And then the loops, which are the part I actually care about. `/apply` points a framework at something real and goes round: draft, critique, revise, again. Each pass is a generation. The idea keeps getting closer to the best version of itself.

One rule I won't bend: it never posts anything on its own. The machine drafts, I decide.

## Gen 5: The strongest objection

Christian Tietze makes the best case against all this. In "The Collector's Fallacy" he says "'to know about something' isn't the same as 'knowing something'." His next heading is even blunter: "Collectors don't make progress." Andy Matuschak goes further: "People who write extensively about note-writing rarely have a serious context of use." And Munger, in the same talk: "To the man with only a hammer, every problem looks like a nail." Give someone a shiny harness and every free afternoon goes into tuning it.

Fair. I've felt that pull myself. My answer is in the design. A harness built on loops has to produce output, otherwise the loop never closes. A framework you never apply is just collecting with nicer formatting. So the test is simple. Did something ship this week? If not, the harness is a hobby.

## Selection

Back to the pots one last time. The quantity group made fifty pounds of pots and kept looking at which ones worked. Making was cheap. Judging was the work.

That's where we all are now. Machines can throw pots all day. The harness runs the loop. You are the selection pressure.

So don't go build a second brain this week. Pick one framework you already half-know (Bezos's doors are fine) and run one loop on something real. Draft it, judge it, go again.

Collect less. Select harder.

---

## Further reading

- Bayles & Orland, *Art & Fear* (1993). The ceramics class: [excerpt](https://kottke.org/09/02/art-and-fear). Its origin: [Austin Kleon](https://austinkleon.com/2020/12/10/quantity-leads-to-quality-the-origin-of-a-parable/)
- Charlie Munger, [A Lesson on Elementary Worldly Wisdom](https://fs.blog/great-talks/a-lesson-on-worldly-wisdom/) (1994)
- Shane Parrish, [Mental Models](https://fs.blog/mental-models/)
- Jeff Bezos, [2015 shareholder letter](https://www.sec.gov/Archives/edgar/data/1018724/000119312516530910/d168744dex991.htm)
- Kelly Johnson and KISS: [Lockheed Martin](https://www.lockheedmartin.com/en-us/news/features/history/johnson.html)
- Lee et al., [The Impact of Generative AI on Critical Thinking](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/) (CHI 2025)
- Paul Graham, [Writes and Write-Nots](https://paulgraham.com/writes.html) (2024) · [Taste for Makers](https://paulgraham.com/taste.html) (2002)
- Rick Rubin, [60 Minutes interview](https://www.cbsnews.com/news/rick-rubin-anderson-cooper-60-minutes-interview-2023-01-15/) (2023)
- Ira Glass, [The Gap](https://jamesclear.com/ira-glass-failure)
- Jack Arenas, [Taste is the Moat](https://foundercollective.com/blog/taste-is-the-moat/) (2025)
- Dylan Field on [Latent Space](https://www.latent.space/p/figma) (2025)
- Richard Dawkins, *The Blind Watchmaker* (1986). See the [weasel program](https://en.wikipedia.org/wiki/Weasel_program)
- Andrej Karpathy, [tweet](https://twitter.com/karpathy/status/893576281375219712) (2017)
- Ericsson et al., deliberate practice (1993): [summary](https://jsomers.net/blog/deliberate-practice)
- James Dyson, [5,127 prototypes](https://gizmodo.com/praising-failure-james-dyson-talks-vacuums-5-127-proto-5790556)
- John Gall, *Systemantics* (1975). Gall's Law: [note](https://notes.andymatuschak.org/z4GDrXLY7RaUDcvZLim3mfA)
- Vannevar Bush, [As We May Think](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/) (1945)
- J.C.R. Licklider, [Man-Computer Symbiosis](https://groups.csail.mit.edu/medg/people/psz/Licklider.html) (1960)
- Niklas Luhmann, [Communicating with Slip Boxes](https://luhmann.surge.sh/communicating-with-slip-boxes)
- Christian Tietze, [The Collector's Fallacy](https://zettelkasten.de/posts/collectors-fallacy/) (2014)
- Andy Matuschak, [Evergreen notes](https://notes.andymatuschak.org/Evergreen_notes)
