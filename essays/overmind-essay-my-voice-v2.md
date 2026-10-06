# You Are the Filter

*Why taste is the only thing AI can't do for you, and how to build a system around that*

Here's a confession. I have hundreds of saved articles I will never read again.

You do too. The bookmarked threads, the highlighted PDFs, the notes app that's basically a graveyard. And every time we save something, we get a tiny hit of "nice, I've got that now." We don't. We've got a link.

This is the oldest trap in the information age, and it's about to get a lot worse. Because AI just made the trap *frictionless*. You can now summarize a 400-page book in ten seconds, and walk away feeling like you read it.

So let me tell you where I've landed, and why I'm building OverMind the way I am.

**Understanding content is basically a solved problem. Knowing what to do with it is not. And that second part, the choosing, is called taste. It's yours, and it's the only part that matters.**

But there's a catch I didn't see at first, and it changes how the whole system has to work. Let me walk you through it.

## Part 1: Saving is not learning

Back in 1945, a scientist named Vannevar Bush dreamed up a machine called the Memex. Picture a desk that could instantly pull up anything humanity had ever written and let you follow connections between ideas. His fear was that we were producing knowledge faster than anyone could use it.

Well, we built it. It's called your phone. And we're more buried than ever.

The problem has a name: the collector's fallacy. When you save something, your brain quietly files it under "done." The act of collecting feels like the act of learning. It isn't. It's like buying gym equipment and feeling fit.

*If you want to go deeper:* Bush's original essay is [As We May Think](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/), and Christian Tietze's short post on [The Collector's Fallacy](https://zettelkasten.de/posts/collectors-fallacy/) is the best explanation of why saving feels like learning.

## Part 2: Your notes should talk back

So what actually works? A German sociologist named Niklas Luhmann had a famous trick. He kept a box of index cards, one idea per card, and linked every card to others. Over decades it became so interconnected that he described it as a conversation partner. It would surface things he'd forgotten and connect ideas he'd never put side by side.

The magic wasn't the box. It was that he wrote *every card himself*. Putting an idea into your own words, and deciding where it connects, isn't the step before understanding. It is the understanding.

And that's where AI makes things tricky. An agent can read a book and hand you the key points in seconds. Great for finding things. But finding an idea and owning an idea are two different skills, and only one of them is automated.

There's early research backing this up. A study by Microsoft and Carnegie Mellon asked knowledge workers about their AI use. The people who trusted AI most reported doing the least critical thinking. To be fair, it's a self-reported survey and shows correlation, so it's a warning light, not a verdict. But it's a warning light worth noticing.

So OverMind's job isn't to think for you. It's to take away the busywork so you have more energy for the thinking.

*If you want to go deeper:* Luhmann's own [Communicating with Slip Boxes](https://luhmann.surge.sh/communicating-with-slip-boxes), Andy Matuschak's [Evergreen Notes](https://notes.andymatuschak.org/Evergreen_notes), the [Lee et al. study on AI and critical thinking](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/), and Paul Graham's [Writes and Write-Nots](https://paulgraham.com/writes.html), which argues that writing and thinking are basically the same muscle.

## Part 3: Frameworks beat summaries

Here's the difference. A summary tells you what happened. A framework tells you what to do next.

Think of Jeff Bezos's one-way and two-way doors. Some decisions are like walking through a door you can walk back through. Try it, see what happens, undo it if you hate it. Others slam shut behind you. The rule: move fast on the reversible ones, slow down on the irreversible ones. Fast on hats, slow on tattoos. That's not a quote you nod at. That's something you can run on a Tuesday morning when you're deciding whether to rebuild your website.

Or Charlie Munger's idea that you should collect a handful of big mental models from lots of different fields, so that when a problem shows up you have more than one way to look at it. Or Kelly Johnson's rule at Lockheed's Skunk Works, the team that built legendary fighter jets: keep it simple, because if a mechanic can't fix it in the field with basic tools, the design failed.

Notice the pattern. Each one is small enough to use in the moment. That's what makes it a framework.

And it's why OverMind is built from four simple blocks (projects, knowledge, tools, actions) instead of one giant system. There's a great old parable about two watchmakers. Both built watches with a hundred parts. One built each watch in a single go, so every time the phone rang, he lost all his progress and had to start over. The other built small stable sub-assemblies, so an interruption only cost him a little. Guess who finished more watches. Complicated things survive when they're made of simple pieces that work.

Same warning applies, though. If a framework never gets tested against your real life, it's just a summary wearing a nicer jacket. So the system has to make you *use* things, not just store them.

*If you want to go deeper:* [Bezos's 2015 shareholder letter](https://www.sec.gov/Archives/edgar/data/1018724/000119312516530910/d168744dex991.htm) (the doors idea lives here), Munger's talk [A Lesson on Elementary Worldly Wisdom](https://fs.blog/great-talks/a-lesson-on-worldly-wisdom/), Shane Parrish's [Mental Models](https://fs.blog/mental-models/) library, the [Lockheed Martin history of Kelly Johnson](https://www.lockheedmartin.com/en-us/news/features/history/johnson.html), Herbert Simon's *The Architecture of Complexity* (that's the watchmaker parable), and [Gall's Law](https://notes.andymatuschak.org/z4GDrXLY7RaUDcvZLim3mfA): every complex system that works grew out of a simple one that worked.

## Part 4: The loop is the whole game

Now the big one. Everything that gets better gets better the same way: try something, see what happens, keep what worked, go again.

Evolution does it with millions of generations and no designer. Chemist Frances Arnold won a Nobel Prize by giving up on designing enzymes by hand and instead making random variations and ruthlessly picking the best. There's a classic demo of why this works. If you tried to randomly type the sentence "METHINKS IT IS LIKE A WEASEL," you'd be waiting longer than the age of the universe. But if you keep the closest guess each round and mutate from there, you get it in about forty tries. That's the whole secret: random attempts plus something that keeps the good ones.

Machine learning is the same story. A neural network starts out knowing nothing. It guesses, checks how wrong it was, nudges itself slightly, and repeats millions of times. Intelligence, in that sense, is just the leftover residue of a lot of loops.

And it's true for people. There's a famous story from the book *Art & Fear* about a pottery class split in two. One half was graded on the *quality* of a single perfect pot. The other was graded purely on the *weight* of everything they made. At the end, the best pots all came from the quantity group. They'd been making, failing, and adjusting, while the other group sat theorizing. (Fun footnote: the origin of that story is a bit murkier than the clean version suggests. I still love it, but treat it as a useful tool, not gospel.) James Dyson built over 5,000 prototypes before his vacuum worked. Same shape.

The punchline is that the quality of your first attempt barely matters. How many times you loop, and how fast you get feedback, decides almost everything.

*If you want to go deeper:* the [Weasel program on Wikipedia](https://en.wikipedia.org/wiki/Weasel_program), [Karpathy's tweet on how neural networks learn](https://twitter.com/karpathy/status/893576281375219712), the [Art & Fear excerpt](https://kottke.org/09/02/art-and-fear) plus [Austin Kleon on the story's origin](https://austinkleon.com/2020/12/10/quantity-leads-to-quality-the-origin-of-a-parable/), [Dyson's 5,127 prototypes](https://gizmodo.com/praising-failure-james-dyson-talks-vacuums-5-127-proto-5790556), and a good plain-English summary of [deliberate practice](https://jsomers.net/blog/deliberate-practice).

## Part 5: The twist (this is the important bit)

Here's what clicked for me while writing this. Go back through every success story above. In every single one, someone had already solved the *judging* problem.

The weasel program works because the target sentence is fixed in advance. Even Dawkins admits that's a flaw in the analogy, because real evolution has no goal. Machine learning works because someone defined what "wrong" means. Labs that do directed evolution have a saying: you get what you screen for. Whatever test you use to pick winners is what you'll end up with.

So when AI makes generating options nearly free, the bottleneck moves. It's no longer "can we make ten versions?" It's "which one is actually good?"

You are the filter. That's not a motivational line. It's a job description, and it's a hard one.

## Part 6: Where taste comes from

So if you're the filter, how do you get a good one?

Ira Glass nailed this. When you start doing creative work, you've got great taste, which is exactly why your early stuff feels terrible. There's a gap between what you can see is good and what you can make. The only way across is volume. You make a lot of bad things until your hands catch up with your eyes.

Which means taste isn't just something you bring to the loop. It's something the loop *builds*. You sharpen your filter by running the reps it's supposed to judge.

Rick Rubin is the poster child for pure taste. He's said he can't play instruments or work the mixing board, he just knows what he likes. People hear that and think you can skip the making. But Rubin spent decades in studios watching ideas get tried, rejected, and refined in real time. He built his filter by being in the room. Someone who only picks from machine output and never makes anything may never cross Glass's gap, and will slowly start preferring whatever the machine finds easiest to produce.

This is why I trust a 1960 paper from J.C.R. Licklider more than most AI hype. He imagined humans and computers as partners. The machine handles the routine, clerical, combinatorial grunt work. The human sets the goals and decides what counts as good. Notice what he never handed over: the criteria.

*If you want to go deeper:* [Ira Glass on The Gap](https://jamesclear.com/ira-glass-failure), Rick Rubin on [60 Minutes](https://www.cbsnews.com/news/rick-rubin-anderson-cooper-60-minutes-interview-2023-01-15/), Paul Graham's [Taste for Makers](https://paulgraham.com/taste.html), Jack Arenas on [Taste Is the Moat](https://foundercollective.com/blog/taste-is-the-moat/), Dylan Field's conversation on [Latent Space](https://www.latent.space/p/figma), and Licklider's [Man-Computer Symbiosis](https://groups.csail.mit.edu/medg/people/psz/Licklider.html).

## So what does this mean for how we build?

It means the harness has a clear design rule. Let the machine do the fetching, formatting, and permuting. Never let it do the deciding.

That's why I believe what I believe:

- **The machine drafts, you decide.** But only if deciding is a muscle you actually use.
- **Iteration beats first drafts.** As long as every round ends in a judgment that costs you something.
- **Taste is subtraction.** Saying "no" to something polished and plausible is the hardest thing to automate, and the easiest thing to forget how to do.
- **Ship over structure.** Shipped work is the one test you can't fake. The world doesn't care how smooth your process felt.

## Why this matters

Graham thinks we're heading for a split: people who can still form and test ideas, and people who can't. I think he's right. And the scary part isn't that machines will think for us. It's that they'll make thinking *optional*, and optional skills quietly fade.

So the real question for anyone building anything right now isn't "should I use AI?" It's "where do I draw the line between what it handles and what I keep?"

Let it handle the grunt work. Keep the taste.

Tools that do that make you sharper. Tools that take both leave you with a mountain of output and nothing to judge it by.

You are the filter. Stay in the loop.
