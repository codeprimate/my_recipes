# Recipe Authoring: Information Architecture and Presentation Principles

This document defines principles for structuring recipe information to optimize both understanding and execution. It complements the technical formatting requirements in `AGENTS.md` by focusing on *what* information to include and *how* to organize it for maximum clarity and usability.

## Core Philosophy

Recipes serve two distinct but related purposes:
1. **Understanding**: Helping the cook comprehend the overall process, relationships between steps, and why techniques matter
2. **Execution**: Providing precise, actionable instructions at the moment they're needed

The structure should support both modes seamlessly, with information organized for high locality during execution while maintaining context for understanding.

## Key Information for Success

Every recipe step must provide four essential elements:

### 1. Action + Doneness (Co-located)

**Principle**: What to do and how to know it's done must appear together in the same step.

**Structure**:
```
[Action] at [Temperature/Heat Level] for [Time Range] until [Doneness Indicator]
```

**Doneness Indicators Must Include**:
- **Visual cues**: color, appearance, texture (e.g., "edges are medium golden brown, center is light golden and appears dry/matte")
- **Tactile cues**: firmness, consistency (e.g., "surface feels firm when gently pressed")
- **Temperature cues**: when critical (e.g., "reaches 170°F on instant-read thermometer")
- **Behavioral cues**: how it responds to manipulation (e.g., "jiggles slightly when gently shaken, like creamy custard")

**Example (Good)**:
> Bake at \textit{350°F} for \textit{22-28~minutes} until crust is done: edges are medium golden brown, center is light golden and appears dry/matte (not sticky or soft), and surface feels firm when gently pressed. The crust should be fully set throughout.

**Example (Poor)**:
> Bake at \textit{350°F} for \textit{22-28~minutes}.

### 2. Context for Decision-Making

**Principle**: Explain *why* a step matters and *when* to deviate from the stated parameters.

**Include**:
- **Purpose**: Why this step is critical (e.g., "prevents sogginess from the filling")
- **Failure modes**: What happens if done incorrectly (e.g., "undercooked crust will become soggy")
- **Recovery instructions**: What to do if things go wrong, phrased naturally (e.g., "Continue baking in \textit{2~minute} increments until center appears dry and firm" rather than "If center still looks wet, then continue baking")

**Placement**: Critical context belongs in the step; deeper explanation belongs in Preparation Tips.

**Language Note**: Recovery instructions should read as natural continuations of the instruction flow. Use "Continue..." or "Add..." rather than "If X, then do Y" structures to maintain natural readability.

### 3. Critical Sequence Information

**Principle**: Dependencies, timing windows, and temperature transitions must be explicit.

**Include**:
- **Dependencies**: What must happen before/after (e.g., "While crust bakes, prepare curd")
- **Timing windows**: When things must happen together (e.g., "Pour curd onto hot crust immediately after straining")
- **Temperature transitions**: When to change heat settings (e.g., "Remove from oven and reduce temperature to \textit{325°F}")

**Placement**: In the prep line or immediately before the step that requires the condition.

### 4. Troubleshooting (Proximity Principle)

**Principle**: Common issues and recovery instructions should appear where decisions are made, not buried in extended sections.

**Structure**:
- **In-step troubleshooting**: For critical, time-sensitive decisions, phrased naturally (e.g., "Continue baking in \textit{2~minute} increments until center appears dry and firm")
- **Extended section troubleshooting**: For deeper context, substitutions, and advanced techniques

**Language Note**: Present recovery instructions as actionable next steps rather than conditional statements. The cook should understand what to do without parsing "if-then" logic.

## Optimal Presentation Order

### During Execution (High Locality)

Information must be where it's needed, in the order it's needed:

```
Step N: [Action] → [Parameters] → [Doneness Indicator] → [What to Watch For] → [Recovery if Needed]
```

**Example Structure**:
1. **Action**: "Bake at \textit{350°F}"
2. **Time**: "for \textit{22-28~minutes}"
3. **Doneness**: "until edges are medium golden brown, center is light golden and appears dry/matte..."
4. **Verification**: "surface feels firm when gently pressed"
5. **Troubleshooting**: "If center still looks wet or sloshes, continue in \textit{2~minute} increments"

### For Understanding (Context First)

Structure supports comprehension by providing context before details:

1. **Prep Line**: Sets stage with prerequisites (preheat, line pan, bring ingredients to temperature)
2. **Steps**: Action → Parameters → Verification
3. **Extended Sections**: Deeper context, tips, troubleshooting, substitutions

### Information Hierarchy

Organize information by frequency of reference and criticality:

#### Primary (In Directions - Required for Execution)
- **What to do**: The action itself
- **When it's done**: Doneness indicators
- **Critical timing/sequence**: Must-happen-together information
- **Immediate troubleshooting**: Recovery instructions for time-sensitive decisions

#### Secondary (In Hints/Notes - Reference During Execution)
- **Why it matters**: Context for decision-making
- **Common pitfalls**: What can go wrong
- **Substitutions/alternatives**: Options when ingredients unavailable
- **Advanced techniques**: Refinements for experienced cooks

#### Tertiary (In Mise en Place - Planning Phase)
- **Prep sequence**: Logical order of preparation tasks
- **Bowl organization**: How ingredients are grouped
- **Timing windows**: When prep tasks should be completed
- **Equipment setup**: What tools are needed and when

## Presentation Principles

### 1. Natural Language and Flow

**Principle**: Instructions should read naturally, like a skilled cook guiding another cook, not like technical documentation.

**Key Guidelines**:

- **Integrate doneness indicators naturally**: Use descriptive clauses that flow with the sentence structure rather than awkward conditionals
  - **Good**: "Bake at \textit{375°F} for \textit{10~minutes} until moisture is released: caps appear slightly shrunken and darker, visible liquid pools around the caps, and caps feel slightly softened when gently pressed."
  - **Awkward**: "Bake at \textit{375°F} for \textit{10~minutes}. If caps appear shrunken and liquid pools, they are done. If not, continue baking."

- **Use descriptive phrases, not conditional statements**: Describe what should be observed rather than creating "if-then" structures
  - **Good**: "Sausage is done when no pink remains, edges are crisp and browned, and fat has rendered."
  - **Awkward**: "If no pink remains and edges are crisp, then the sausage is done."

- **Place recovery instructions as separate sentences**: Keep them concise and actionable without interrupting the main instruction flow
  - **Good**: "Continue baking in \textit{2~minute} increments until liquid pools appear."
  - **Awkward**: "If liquid does not appear, then you should continue baking in increments of 2 minutes until such time as liquid appears."

- **Integrate verification methods into narrative**: Describe what to observe as part of the natural instruction flow
  - **Good**: "Shallot should appear translucent and garlic should be aromatic without browning."
  - **Awkward**: "Check if shallot is translucent. Also check if garlic is aromatic. Make sure it is not browning."

- **Use parallel structure for multi-modal cues**: When listing visual, tactile, and other cues, maintain consistent phrasing
  - **Good**: "Mushrooms are done when caps feel tender when pierced with a knife, cheese is bubbly and golden brown, and filling is hot throughout."
  - **Awkward**: "Mushrooms are done when caps feel tender. The cheese should be bubbly. Also check that filling is hot."

**Language Patterns to Avoid**:
- Excessive "if-then" conditionals
- Technical jargon that interrupts flow
- Repetitive "check if" or "verify that" phrases
- Awkward conditional recovery instructions
- **Intra-step redundancy**: Restating the same information multiple ways within a single step (e.g., "it appears smooth" followed by "it should look uniform")
- **Over-verbose descriptions**: Saying the same thing in different words (e.g., "dough should hold together when pressed" and "dough should not crumble when squeezed")

**Language Patterns to Use**:
- Descriptive present-tense observations ("appears", "feels", "should be")
- Natural transitions between action and verification
- Concise recovery instructions as separate sentences
- Flowing narrative that guides the cook through the process
- **Single, clear statement**: Each piece of information stated once, clearly and concisely
- **Complementary, not redundant cues**: Multi-modal verification should provide different information (visual + tactile + temperature), not restate the same observation

### 2. Conciseness and Intra-Step Redundancy

**Principle**: Each piece of information should appear once, clearly and concisely. Avoid restating the same concept in different words within a single step.

**Key Guidelines**:

- **State once, clearly**: Don't say the same thing multiple ways
  - **Redundant**: "Beat until smooth and slightly fluffy with no visible sugar granules. The mixture is ready when it appears smooth and slightly fluffy, with no visible sugar granules remaining."
  - **Concise**: "Beat until smooth and slightly fluffy with no visible sugar granules, about \textit{2--3~minutes}."

- **Multi-modal cues should complement, not repeat**: Each verification method should provide distinct information
  - **Good**: "Cookies are done when edges turn pale golden and feel firm, while centers appear slightly underdone but will set upon cooling." (visual + tactile + behavioral)
  - **Redundant**: "Cookies are done when edges turn pale golden. The edges should appear golden. The edges will look golden when done."

- **Integrate doneness into the action, don't restate it separately**
  - **Redundant**: "Mix until dough comes together. Dough is ready when it appears crumbly but holds together when pressed."
  - **Concise**: "Mix until dough appears crumbly but holds together when pressed, about \textit{45~seconds--1~minute}."

- **Avoid redundant qualifiers**: Don't add unnecessary explanatory phrases that repeat what's already stated
  - **Redundant**: "dough should hold together without crumbling when pressed, and should feel slightly tacky but not sticky"
  - **Concise**: "dough should feel slightly tacky but not sticky" (the "holds together" is implied by "cohesive mass")

**When Adding Doneness Indicators**:
- Integrate them directly into the action statement
- Use the most direct, clear phrasing
- If you find yourself restating the same concept, choose the clearest version and remove the rest
- Multi-modal verification should add new information, not restate existing observations

### 3. Locality of Reference

**Principle**: Information needed at step N should be at step N, not scattered across the document.

**Application**:
- Doneness indicators in the same step as the action
- Critical warnings where decisions are made
- Recovery instructions immediately after the verification criteria

**Exception**: Extended sections for deeper context that doesn't affect immediate execution.

### 4. Progressive Disclosure

**Principle**: Essential information in directions; nice-to-know in extended sections.

**Essential (Directions)**:
- What to do
- How to know it's done
- Critical timing/sequence
- Immediate recovery steps

**Nice-to-Know (Extended Sections)**:
- Why techniques work
- Substitutions
- Advanced variations
- Historical/cultural context

### 5. Fail-Safe Design

**Principle**: Include recovery instructions at decision points, especially for unforgiving techniques.

**Unforgiving Techniques Requiring Extra Care**:
- Emulsions (mayonnaises, hollandaise)
- Custards (curds, crème brûlée)
- Bread (proofing, shaping)
- Candy (temperature stages)
- Pastry (laminating, blind baking)

**Structure for Fail-Safe Steps**:
```
[Action] → [Parameters] → [Doneness] → [Warning if Unforgiving] → [Recovery Instructions]
```

### 6. Multi-Modal Verification

**Principle**: Provide multiple ways to verify doneness, not just time.

**Always Include**:
- **Visual**: What it should look like
- **Tactile**: How it should feel
- **Temperature**: When critical (use thermometer)
- **Behavioral**: How it responds to manipulation

**Example (Natural Flow)**:
> Cook until mixture thickens noticeably and reaches \textit{170°F}, about \textit{8-10~minutes}. The curd is done when it reaches \textit{170°F} on an instant-read thermometer, or when it coats the back of a spoon thickly and leaves a clear trail when you draw your finger through it (the trail should not immediately fill in). The mixture should have the consistency of thick pudding and should not look watery or thin.

**Why this works**: The doneness indicators are integrated as descriptive clauses that flow naturally from the action. Multiple verification methods are presented as alternatives ("or when...") rather than as separate conditional checks.

### 7. Contextual Warnings

**Principle**: Flag unforgiving steps where they occur, not just in extended sections.

**Structure**:
- **In-step warning**: Brief, actionable (e.g., "Stir constantly to prevent curdling")
- **Extended section**: Deeper explanation of why and what to watch for

## Step Structure Template

Use this template for each cooking step:

```
\item [Action with ingredients] at [temperature/heat] for [time range] until [doneness indicator]. [Verification method]. [Critical note if applicable]. [Recovery instruction if needed].
```

**Example (Natural Flow)**:
```
\item Bake at \textit{350°F} for \textit{22-28~minutes} until crust is done: edges are medium golden brown, center is light golden and appears dry/matte (not sticky or soft), and surface feels firm when gently pressed. The crust should be fully set throughout. Continue baking in \textit{2~minute} increments until center appears dry and firm. Remove from oven and reduce temperature to \textit{325°F}.
```

**Note**: Recovery instructions read naturally as a continuation of the instruction rather than as a conditional statement. The phrase "Continue baking..." flows from the doneness description without awkward "if-then" structure.

## Special Considerations

### Cooling/Chilling Steps

**Principle**: Specify both time and verification method.

**Structure**:
```
Cool [where] for [time] ([verification method]), then [next step] for [time] ([verification method]).
```

**Example**:
```
Cool completely in the pan on a wire rack for \textit{1~hour} (pan should feel cool to the touch, not warm), then refrigerate for at least \textit{3~hours} or overnight (filling should be firm throughout when ready to cut).
```

### Temperature Transitions

**Principle**: Always state both the action and the new temperature.

**Structure**:
```
[Action that changes temperature]. [New temperature for next step].
```

**Example**:
```
Remove from oven and reduce temperature to \textit{325°F}.
```

### Simultaneous Tasks

**Principle**: Make parallel work explicit.

**Structure**:
```
While [task A], [task B].
```

**Example**:
```
While crust bakes, whisk together \nicefrac{2}{3}~cup \textbf{granulated sugar} and 1~tsp. \textbf{cornstarch} in a medium saucepan.
```

## Extended Sections: Content Guidelines

### Preparation Tips

**Purpose**: Technique guidance, common pitfalls, and troubleshooting.

**Structure**:
- **Technique guidance**: How to perform steps correctly
- **Common pitfalls**: What to avoid and why
- **Troubleshooting**: What to do when things go wrong
- **Visual/texture cues**: How to distinguish normal from problematic

**Example**:
```
\item Don't underbake the crust; it's done when edges are medium golden brown, center is light golden and appears dry/matte (not sticky), and surface feels firm when gently pressed. Fully baked crust is essential for structural integrity and prevents sogginess from the filling
```

### Mise en Place

**Purpose**: Prep sequence and organization to minimize cognitive load during active cooking.

**Include**:
- Bowl assignments with stage annotations
- Timing windows for prep tasks (room temperature butter, cooling reductions)
- Logical prep sequence
- Approximate volumes when helpful

**Example**:
```
\item \textit{Small Bowl~\#1} --- lemon zest from 1 lemon (for crust)
\item Make \textbf{raspberry reduction} first; allow \textit{30~minutes} to cool to room temperature
\item Bring 8~Tbsp. \textbf{butter} to room temperature for crust (\textit{1~hour})
```

## Quality Checklist

Before finalizing a recipe, verify:

- [ ] Every cooking step includes doneness indicators (not just time)
- [ ] Critical timing/sequence information is explicit
- [ ] Unforgiving techniques have in-step warnings
- [ ] Recovery instructions appear at decision points
- [ ] Temperature transitions are clearly stated
- [ ] Cooling/chilling steps specify verification methods
- [ ] Multi-modal verification (visual, tactile, temperature) is provided
- [ ] Troubleshooting appears where decisions are made
- [ ] Extended sections provide deeper context without duplicating critical information
- [ ] Prep line sets context for all subsequent steps
- [ ] Language flows naturally without awkward "if-then" conditionals
- [ ] Doneness indicators are integrated as descriptive clauses, not separate checks
- [ ] Recovery instructions read as natural continuations, not conditional statements
- [ ] Instructions read like a skilled cook guiding another cook, not technical documentation
- [ ] No intra-step redundancy: each piece of information stated once, clearly
- [ ] Multi-modal cues provide complementary information, not restatements
- [ ] Conciseness: no unnecessary repetition of the same concept in different words

## Examples

### Good: Complete Step with Natural Flow

```
\item Cook over medium-low heat, stirring constantly with a silicone spatula or wooden spoon, scraping the bottom and sides of the pan. Cook until mixture thickens noticeably and reaches \textit{170°F}, about \textit{8-10~minutes}. The curd is done when it reaches \textit{170°F} on an instant-read thermometer, or when it coats the back of a spoon thickly and leaves a clear trail when you draw your finger through it (the trail should not immediately fill in). The mixture should have the consistency of thick pudding and should not look watery or thin.
```

**Why it works**:
- Action: "Cook over medium-low heat, stirring constantly"
- Parameters: "until reaches 170°F, about 8-10 minutes"
- Multi-modal doneness: temperature OR visual/tactile test (presented as alternatives, not conditionals)
- Verification: clear trail, thick pudding consistency (integrated naturally)
- Warning: "should not look watery or thin" (descriptive, not conditional)
- Natural flow: Doneness indicators read as descriptive observations, not "if-then" checks

### Good: Natural Recovery Instructions

```
\item Bake at \textit{375°F} for \textit{20-25~minutes} until mushrooms are tender and tops are golden brown. Mushrooms are done when caps feel tender when pierced with a knife, cheese is bubbly and golden brown, and filling is hot throughout. Continue baking in \textit{2~minute} increments until cheese is golden and mushrooms are tender.
```

**Why it works**:
- Recovery instruction flows naturally from the doneness description
- Uses "Continue baking..." rather than "If not done, then continue..."
- Maintains parallel structure with the doneness indicators

### Poor: Awkward Conditional Phrasing

```
\item Bake at \textit{375°F} for \textit{20-25~minutes}. If mushrooms are tender and cheese is golden, then they are done. If mushrooms are not tender or cheese is not golden, then continue baking in 2-minute increments. Check if mushrooms are tender by piercing with a knife. Verify that cheese is golden brown.
```

**Why it fails**:
- Excessive "if-then" conditionals create awkward, technical-sounding prose
- Repetitive "check if" and "verify that" phrases interrupt flow
- Reads like a checklist rather than natural instruction
- Recovery instruction is buried in conditional logic

### Poor: Incomplete Step

```
\item Cook the curd for 8-10 minutes until thick.
```

**Why it fails**:
- No temperature specified
- No doneness indicator beyond "thick"
- No verification method
- No recovery instructions

## Integration with AGENTS.md

This document focuses on *information architecture* (what to include and how to organize it), while `AGENTS.md` covers:

- **Technical formatting**: LaTeX syntax, formatting conventions
- **Recipe validation**: Scientific and culinary validation
- **Content requirements**: What sections to include

Together, they provide complete guidance for recipe authoring:
- `AGENTS.md`: The *what* and *how* of formatting and validation
- `RECIPE-AUTHORING.md`: The *what* and *how* of information presentation

Use both documents when authoring recipes to ensure technical correctness, culinary integrity, and optimal information architecture.
