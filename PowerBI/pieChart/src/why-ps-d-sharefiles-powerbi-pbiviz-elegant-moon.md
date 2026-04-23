# Plan — Scaffold D3 Pie Chart in `pieChart` visual

## Context

User ran `pbiviz start` on [pieChart](d:/ShareFiles/PowerBI/pieChart) (Power BI visual scaffold, pbiviz 7.0.3) and hit a validator error: empty `author` block in [pbiviz.json](d:/ShareFiles/PowerBI/pieChart/pbiviz.json). Underlying goal is to build a working pie chart and debug it **locally in Power BI Desktop** (user confirmed Desktop "Develop a visual" toggle — the same workflow they remembered from 5 years ago — is the target, not the cloud Fabric path).

Current state (from Explore subagent):
- The scaffold renders a plain-text "Update count: N" counter — no data binding yet ([src/visual.ts:61-68](d:/ShareFiles/PowerBI/pieChart/src/visual.ts)).
- `d3@7.9.0` and `@types/d3@7.4.3` already in [package.json](d:/ShareFiles/PowerBI/pieChart/package.json).
- [capabilities.json](d:/ShareFiles/PowerBI/pieChart/capabilities.json) already defines `category` (Grouping) + `measure` (Measure) data roles, mapped to `categorical.categories` and `categorical.values[0]`. No changes needed.
- [src/settings.ts](d:/ShareFiles/PowerBI/pieChart/src/settings.ts) uses the modern `FormattingSettingsModel` pattern (`DataPointCardSettings` with color / toggle / fontSize). Will reuse color.

## Scope

Three focused changes + Desktop verification. No dependency installs, no capabilities changes, no refactor of settings.

### 0. Create `D:\ShareFiles\.gitignore` — stop committing build artifacts

Repo root `D:\ShareFiles` is a git repo with no `.gitignore`. Current `git status` shows `?? PowerBI/` is untracked and contains `node_modules/` (huge), `dist/`, `.tmp/`, and `webpack.statistics.dev.html` — none of which belong in version control. Adding the ignore *before* `git add` is critical so these never enter the index.

Write `D:\ShareFiles\.gitignore` with:

```gitignore
# Node / npm
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# pbiviz / Power BI visuals build output
dist/
.tmp/
*.pbiviz
webpack.statistics*.html

# Editor / OS
.DS_Store
Thumbs.db
*.swp
*.swo

# Logs and coverage
*.log
coverage/
```

Leave `.vscode/` and `.claude/` **un-ignored** — they appear to be intentional in other tracked subprojects (Bobydo, JobFit, OODClaude, etc.). `package-lock.json` is also **kept** (good practice for reproducible builds).

### 1. Fix [pbiviz.json](d:/ShareFiles/PowerBI/pieChart/pbiviz.json) — unblock `pbiviz start`

Replace:
```json
"author":{"name":"","email":""}
```
with:
```json
"author":{"name":"Shenyi","email":"austinybao2006@gmail.com"}
```

Nothing else in the file needs to change for local dev. `description`, `supportUrl`, `gitHubUrl` only matter for AppSource publishing.

### 2. Replace [src/visual.ts](d:/ShareFiles/PowerBI/pieChart/src/visual.ts) — D3 pie wired to Category + Measure

Keep the existing class shape (`Visual implements IVisual`, constructor, `update`, `getFormattingModel`). Change the rendering:

**Constructor** — replace the `<p>` counter DOM with an `<svg>` root:
```ts
this.svg = d3.select(options.element)
    .append("svg")
    .classed("pieChart", true);
this.container = this.svg.append("g").classed("container", true);
```
Store `this.svg` and `this.container` as private fields (OOP — instance methods operate on them; no module globals).

**update(options)** — new flow:
1. Early-out if `!options.dataViews?.[0]?.categorical?.categories?.[0]` (no data dropped yet).
2. Read `categories[0].values` (labels) and `values[0].values` (numbers) from the dataView.
3. Resize svg to `options.viewport.width / height`; center `this.container` with a translate to `(w/2, h/2)`; pick `radius = min(w,h)/2 - padding`.
4. Build `d3.pie<number>()` layout and `d3.arc()` generator (inner radius 0, outer `radius`).
5. Data-join the arcs: `this.container.selectAll("path.arc").data(pie(values), (d,i) => categories[i])` → enter/update/exit → set `d` from arc generator, `fill` from `d3.schemeTableau10` (or `d3.scaleOrdinal(d3.schemeCategory10)` keyed on category).
6. Data-join text labels centered at `arc.centroid()` showing the category name.
7. Read `this.formattingSettings.dataPointCard.defaultColor.value.value` for a single-color override when the toggle in settings is off (future; for v1 just use the ordinal scale).

**getFormattingModel / formatting** — leave as-is; `FormattingSettingsService.populateFormattingSettingsCard` already reads from the dataView in the current `update`. Keep the `formattingSettings = this.formattingSettingsService.populateFormattingSettingsCard(VisualFormattingSettingsModel, options.dataViews[0])` call.

**Typing** — import `powerbi.extensibility.visual.VisualUpdateOptions` and `powerbi.DataViewCategorical` as already done; add `import * as d3 from "d3";`.

### 3. Update [style/visual.less](d:/ShareFiles/PowerBI/pieChart/style/visual.less)

Remove the yellow `<em>` counter styling. Add:
```less
.pieChart {
    display: block;
    width: 100%;
    height: 100%;
    path.arc { stroke: #fff; stroke-width: 1px; }
    text.label { font-size: 11px; fill: #fff; text-anchor: middle; pointer-events: none; }
}
```

### Out of scope for this pass

- Selection manager + cross-filtering (click-to-filter other visuals)
- Tooltips via `host.tooltipService`
- Hooking the formatting settings color picker into per-slice fill
- Legend
- Data label number formatting (`valueFormatter`)

These are natural follow-ups once the basic pie renders. Do them after verification, not in this PR.

## Critical files

| File | Change |
|---|---|
| `D:\ShareFiles\.gitignore` | **Create** — ignore node_modules, dist, .tmp, *.pbiviz, webpack stats |
| [pbiviz.json](d:/ShareFiles/PowerBI/pieChart/pbiviz.json) | Fill `author.name`, `author.email` |
| [src/visual.ts](d:/ShareFiles/PowerBI/pieChart/src/visual.ts) | Replace counter with D3 pie |
| [style/visual.less](d:/ShareFiles/PowerBI/pieChart/style/visual.less) | Remove counter styles, add `.pieChart` / `.arc` / `.label` |

## Verification (run in this order)

0. **Gitignore is honored** — from `D:\ShareFiles`: `git status --short`. Should **not** list `PowerBI/pieChart/node_modules/`, `PowerBI/pieChart/dist/`, `PowerBI/pieChart/.tmp/`, or `webpack.statistics.dev.html`. Should list `.gitignore` itself as untracked and `PowerBI/` as untracked (with only the source files inside).
1. **Dev server starts** — from [pieChart](d:/ShareFiles/PowerBI/pieChart): `pbiviz start`. Should print `Server listening on port 8080` with no validation error.
2. **Cert trust** — already done earlier this session (imported into Current User → Trusted Root). Re-verify by opening `https://localhost:8080/assets/status` — no browser warning.
3. **Enable Desktop dev mode** — Power BI Desktop → File → Options and settings → Options → Current file → Report settings → check **"Develop a visual"** → OK. (Per-session; redo each Desktop launch.)
4. **Add Developer Visual** — in any Power BI Desktop report, Visualizations pane → the `</>` icon → drop onto canvas. It will connect to `localhost:8080`.
5. **Bind data** — drag a text column (e.g., product category) into **Category Data** and a numeric measure into **Measure Data**.
6. **Expected result** — a pie chart renders with one slice per category, colored from the Tableau10 palette, labels at arc centroids. Resizing the visual should re-lay out the pie (`update` fires on viewport change).
7. **Hot reload check** — edit the outer `radius - padding` value in [src/visual.ts](d:/ShareFiles/PowerBI/pieChart/src/visual.ts); save; watch Desktop reload the visual within ~1s.
8. **Empty-state check** — remove the measure field. Visual should render nothing (not throw). Re-add → slices come back.

If step 6 renders but colors are wrong, inspect via `edge://inspect` (Desktop uses an embedded Edge WebView) and confirm the ordinal scale is receiving `categories[i]` strings, not indices.
