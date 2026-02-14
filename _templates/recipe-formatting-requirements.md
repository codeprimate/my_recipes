# LaTeX Recipe Formatting Requirements

*For LLM agent use. Single source of truth for recipe formatting. Referenced from `AGENTS.md`; the Post-Creation Sanity Check verifies compliance with these requirements.*

---

**Reference:** Use the provided templates in `_templates/` for document class, packages, font settings, and page layout. Do not recreate technical specifications from scratch. Reference sample recipes for idiomatic formatting and structure.

## Preamble and Document-Wide Rules

- **Fractions:** Use `\usepackage{nicefrac}` and `\nicefrac{numerator}{denominator}` for all fractions (e.g., \nicefrac{1}{2}, \nicefrac{1}{4}, \nicefrac{1}{3}, \nicefrac{3}{4}). Do not use Unicode fraction characters.
- **Units:** American units only; use periods in abbreviations (Tbsp., tsp., oz., lb.).
- **Page breaks:** Include in preamble to prevent breaks within list items:
  - `\widowpenalty=10000`
  - `\clubpenalty=10000`
  - `\interlinepenalty=500`

## Ingredients Section

- Two-column format with dotted lines (reference template multicols setup).
- List ingredients **in order of use** in the directions.
- Format: Ingredient `\dotfill` Amount.
- Capitalize ingredient names.
- American units with periods; `\nicefrac{numerator}{denominator}` for all fractions.

## Directions Section

- Begin with a **prep line:** tasks separated by em-dashes (---).
- Use `enumerate` environment for steps.
- **In-document formatting:**
  - `\textbf{ingredients}` in directions
  - `\textit{times and temperatures}` and `\textit{bowl references}` (e.g., `\textit{Small Bowl~\#1}`)
  - Non-breaking space (`~`) before units and before ingredients where appropriate
  - Include °F for all temperatures

### Steps and substeps

- **When to use:** Use a **single numbered step with lettered substeps** when one logical step contains several sequential sub-actions that belong together (e.g. mixing a dough: cream fat and sugar, add eggs, add dry ingredients). This keeps the main list from becoming too long or too fine while preserving a clear sequence.
- **How to format:** One top-level `\item` with a short intro phrase, then a nested `\begin{enumerate}...\end{enumerate}` whose items render as (a), (b), (c), (d). No extra packages required.
- **Example:**
```latex
\item Mix the dough in a large bowl:
\begin{enumerate}
    \item Stir \textbf{peanut~butter} and \textbf{sugar} until smooth, about \textit{3--5~minutes}. Scrape bowl as needed.
    \item Add \textbf{eggs} one at a time, mixing well after each until fully incorporated.
    \item Add \textbf{vanilla} and mix until combined.
    \item Add \textbf{baking~soda} and \textbf{salt} and stir until just combined; dough should be smooth and uniform.
\end{enumerate}
```
- **Granularity:** Use substeps for a tight sequence within one step; use separate numbered steps for a change of method, heat, vessel, or major component (e.g. crust → filling → bake).

## Bowl References in Directions

- **Combining when added together:** When **multiple ingredients are added in the same step**, combine them in **one bowl**—do not use a separate bowl for each. Single ingredients may have their own bowl or be set aside without one. Use a bowl when something must be held (reserved liquid, cooked item set aside, component added back later).
- **Bowl size** by actual volume of raw or prepared ingredient(s):
  - **Small Bowl:** typically up to 1~cup (spices, small aromatics, small amounts of prepared ingredients)
  - **Medium Bowl:** typically 2--6~cups (moderate amounts, combined mixtures, smaller quantities of cooked protein)
  - **Large Bowl:** truly large volumes, pounds of ingredients, or substantial quantities requiring significant capacity or mixing
- **Prep line:** When multiple ingredients are added together in one step, combine them in one bowl; single ingredients may have a bowl or "measure and set aside" / "have ready." Format: `combine in \textit{Small Bowl~\#1} (aromatics)`.
- **Cooking steps:** List ingredients first, then bowl reference in parentheses when a bowl is used. Format: `\textbf{onion} and \textbf{garlic} (\textit{Small Bowl~\#1})`.
- **Quantities in bowl references:** Include quantities only for measured ingredients (tsp., Tbsp., cups, etc.); omit for produce, whole cans, and whole items. Examples: `2~tsp. \textbf{cumin} with 1~tsp. \textbf{oregano} (\textit{Small Bowl~\#2})`; `\textbf{kale} and \textbf{cannellini beans} (\textit{Large Bowl~\#1})`.
- **When a bowl is required:** Reserved liquids, cooked ingredients set aside, or components added back later get a bowl. Examples: `reserve \textbf{pasta water} in \textit{Medium Bowl~\#1}`; `transfer cooked \textbf{chicken} to \textit{Large Bowl~\#2} and set aside`.

## Quote Description (Required)

- **Placement:** After `\maketitle` and `\thispagestyle{empty}`, before `\section*{Ingredients}`.
- **Format:** `\begin{quote}\textit{...}\end{quote}` (content italicized).
- **Content:** High-level description of components and how they come together, ending with yield. Concise (2--3 sentences); major components, preparation methods, and yield.
- **Example:** `\begin{quote}\textit{Pressure-cooked chicken thighs are diced and combined with al-dente rice, blanched broccoli, and sautéed vegetables (caramelized corn, onion, garlic, and mushrooms). A spiced roux-based cream sauce binds everything together, and the casserole is baked until bubbly and topped with crispy fried onions for texture. Serves 6--8.}\end{quote}`

## Extended Sections (Second Page)

- Use `\newpage` after the main recipe, then required sections: **Equipment** and **Hints/Notes**.

**Equipment**
- `\section*{Equipment Required}`; list tools in `itemize`. Include sizes for bowls, pans, and dishes; list optional but helpful tools; order by use when possible.
- Content: list all essential equipment, specify container sizes, include measuring tools and common implements, note optional tools, be specific about tool types.

**Hints and Notes**
- `\section*{Hints and Notes}`; use `\subsection*` for: Yield, Mise en Place, Ingredient Tips, Preparation Tips, Make Ahead & Storage, Serving Suggestions. Use `itemize` within subsections.
- **Format in Hints/Notes:** `\textbf{ingredients}` when referenced; `\textit{times and temperatures}`; °F for temperatures; non-breaking space (`~`) before units and ingredients.
- **Content guidelines:**
  - **Yield:** Number of servings, portions, or quantity produced (e.g., "Serves 4--6" or "Makes 12 stuffed mushroom caps").
  - **Mise en Place:** Same bowl-combining rule as in Bowl References—ingredients added in the same step in one bowl; single ingredients may have a bowl or "have ready" / "measure and set aside"; reserved liquids and items set aside get a bowl. Enumerate bowls by size and number (e.g., "Small Bowl #1," "Medium Bowl #2"). Select sizes by actual volume (small: up to ~\nicefrac{1}{2}~cup for annotations, medium: ~\nicefrac{1}{2}--2~cups, large: multiple cups/pounds). Annotate each bowl with cooking stage (e.g., "Medium Bowl #1 — aromatics") and approximate volumes when helpful. For reserved liquids or components set aside, assign a bowl and list in Mise en Place. Note timing for room-temperature ingredients; specify logical prep sequence before applying heat.
  - **Ingredient Tips:** Preferred types, substitutions, quality notes.
  - **Preparation Tips:** Technique guidance, common pitfalls.
  - **Make Ahead & Storage:** Timing windows, storage conditions, reheating.
  - **Serving Suggestions:** Pairings, garnishes, presentation.

## Layout and Optional Elements

- **Layout:** Title with `\maketitle`; empty author/date; first page `\thispagestyle{empty}`; reference templates for margins and fonts.
- **Optional:** For complex recipes, use separate sections (e.g., green chile template).
