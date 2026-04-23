# pieChart — Power BI Custom Visual

A minimal D3-based pie chart custom visual for Power BI, scaffolded with `pbiviz` and bound to the standard `Category` / `Measure` data slots.

## Stack

| Layer | Choice | Version |
|---|---|---|
| Build tool | `powerbi-visuals-tools` (pbiviz) | 7.0.3 |
| Visuals API | `powerbi-visuals-api` | ~5.3.0 |
| Rendering | `d3` | 7.9.0 |
| Formatting | `powerbi-visuals-utils-formattingmodel` (modern `FormattingSettingsModel`) | 6.0.4 |
| Language | TypeScript (target `es2022`) | — |

## Data contract

Defined in `capabilities.json`:

- `category` (Grouping) → `dataView.categorical.categories[0].values` — slice labels
- `measure` (Measure) → `dataView.categorical.values[0].values` — slice sizes

## Rendering — `src/visual.ts`

Class-based (`Visual implements IVisual`) with instance-method OOP:

- **Constructor** builds an `<svg class="pieChart">` with a centered `<g class="container">` root and an ordinal color scale (`d3.schemeTableau10`) — all held as `readonly` private fields, no module globals.
- **`update(options)`**
  1. Repopulates the formatting settings model from the incoming dataView.
  2. Resizes the SVG to `options.viewport.{width,height}`, translates container to center, computes `radius = min(w,h)/2 - 10`.
  3. `_extractSlices(dataView)` → `Slice[]` (defensive: returns `[]` on missing/empty data).
  4. `d3.pie().value(s => s.value).sort(null)` lays out arcs.
  5. `_renderArcs(arcData, radius)` + `_renderLabels(arcData, radius)` do keyed data-joins (enter/update/exit) so category changes animate correctly.
- **`getFormattingModel()`** delegates to `FormattingSettingsService.buildFormattingModel`.

Private helpers (`_extractSlices`, `_renderArcs`, `_renderLabels`) keep responsibilities separated — easy to unit-test later by injecting a mock `DataView`.

## Setup

```powershell
# 1. Install pbiviz globally (one-time)
npm i -g powerbi-visuals-tools@latest

# 2. Generate + trust the dev HTTPS cert (one-time per machine)
pbiviz install-cert
# Import the generated .pfx (at C:\Users\<you>\pbiviz-certs\...) into
# Current User → Trusted Root Certification Authorities, using the
# passphrase pbiviz printed.

# 3. Install project deps (one-time per clone)
cd D:\ShareFiles\PowerBI\pieChart
npm install

# 4. Start the dev server
pbiviz start
# Serves https://localhost:8080/assets/visual.js with hot reload
```

## Debug — two options

### Power BI Desktop (local, preferred for fast iteration)

1. Open any report in Power BI Desktop.
2. **File → Options and settings → Options → Current file → Report settings** → check **"Develop a visual"** → OK.
   *(Per-session, per-file — must re-enable each time.)*
3. In the **Visualizations** pane, click the `</>` Developer Visual tile → drop it on the canvas.
4. Bind data: drag a text column into **Category Data**, a numeric measure into **Measure Data**.
5. Save [src/visual.ts](src/visual.ts) → Desktop hot-reloads the visual.

### Power BI Service / Fabric (cloud)

1. Enable the persistent developer toggle at https://app.powerbi.com/user/user-settings/developer-settings.
2. Open any report in **fabric-developer** experience — a Developer Visual tile appears in the Visualizations pane.
3. Same data-binding flow. Useful for testing against workspace-backed datasets.

## Package for distribution

```powershell
pbiviz package
# → dist/pieChart.pbiviz — drop into any Power BI report via
#   Visualizations → ... → Import from file
```

## Project conventions

- Private helpers prefixed with `_` (e.g. `_extractSlices`).
- No `@static` methods; all behavior is instance-based to allow DI / mocking.
- Dependencies injected via constructor (`FormattingSettingsService` field) rather than module-level singletons.
- Build artifacts (`node_modules/`, `dist/`, `.tmp/`, `*.pbiviz`, `webpack.statistics*.html`) excluded via the repo-root `.gitignore` at `D:\ShareFiles\.gitignore`.

## Known caveats

- **Personal Microsoft accounts (Gmail / @outlook.com) cannot sign into Power BI.** A work/school tenant is required to sign in on Desktop. For dev-only work, sign up for the free **Microsoft 365 Developer Program** (https://developer.microsoft.com/microsoft-365/dev-program) to get a sandboxed tenant with a Power BI license.
- The IDE may report `Cannot find module './../style/visual.less'` on the side-effect import in [src/visual.ts](src/visual.ts). This is a TS-server-only complaint; pbiviz's webpack loader handles `.less` at build time. Safe to ignore, or add `declare module "*.less";` in a `*.d.ts` to silence it.
- `pbiviz start` validates `pbiviz.json` — empty `author.name` / `author.email` will block startup with a metadata error.

## Status & next steps

**Done:**
- Scaffold generated with `pbiviz new pieChart`
- `pbiviz.json` metadata filled in
- Dev HTTPS cert generated and trusted
- `src/visual.ts` rewritten: counter → D3 pie with keyed data joins, category-colored slices, centroid labels
- `style/visual.less` updated with pie-specific styles
- Repo-root `.gitignore` added

**Next (not done yet — pending Power BI Desktop dev-mode enablement):**
- End-to-end render test in Desktop (awaiting sign-in path resolution)
- Wire the formatting settings color picker into per-slice fill
- Add `host.tooltipService` tooltips showing category + value
- Add `host.createSelectionManager()` for click-to-cross-filter
- Add a legend
- Format measure values via `valueFormatter` (currency, percent, etc.)
