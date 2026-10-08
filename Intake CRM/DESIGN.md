---
name: Intake
description: A quiet, light operations dashboard for legal intake. Templates and PNC records, nothing more.
colors:
  ink-blue: "oklch(0.43 0.085 255)"
  ink-blue-deep: "oklch(0.37 0.085 255)"
  ink-blue-wash: "oklch(0.95 0.018 255)"
  cool-paper: "oklch(0.982 0.003 250)"
  white: "oklch(1 0 0)"
  sunk-paper: "oklch(0.966 0.005 250)"
  hairline: "oklch(0.915 0.006 250)"
  hairline-strong: "oklch(0.85 0.008 250)"
  ink-text: "oklch(0.24 0.014 255)"
  slate-text: "oklch(0.44 0.014 255)"
  quiet-text: "oklch(0.52 0.012 255)"
  danger: "oklch(0.5 0.16 25)"
  live-green: "oklch(0.58 0.13 155)"
typography:
  display:
    fontFamily: "Manrope Variable, Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "2.375rem"
    fontWeight: 300
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Manrope Variable, Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 600
  body:
    fontFamily: "Manrope Variable, Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Manrope Variable, Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
components:
  button-primary:
    backgroundColor: "{colors.ink-blue}"
    textColor: "{colors.white}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.ink-blue-deep}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink-text}"
    rounded: "{rounded.sm}"
    height: "38px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink-text}"
    rounded: "{rounded.sm}"
    height: "40px"
  badge-api:
    backgroundColor: "{colors.ink-blue-wash}"
    textColor: "{colors.ink-blue}"
    rounded: "4px"
---

# Design System: Intake

## Overview

**Creative North Star: "The Quiet Filing Room"**

A light, calm workspace. It looks finished because of precise details, not decoration. Large text is set thin (Manrope 300); everything you read or act on is set at regular weight or heavier. Most of the screen is cool paper-white and hairlines. The one ink-blue accent appears only where something is selected, actionable, or newly arrived.

The user asked for "minimalist, easy readability, not corny", a light theme, and a thin but readable typeface. Every rule below serves that.

**Key Characteristics:**
- One typeface, two voices: thin display, regular body.
- Restrained colour: neutrals plus a single muted ink-blue.
- Documents shown as paper pages, not as cards.
- Motion only to signal a change of state (150–220 ms, ease-out).

## Colors

Cool, barely tinted neutrals with one muted ink-blue.

### Primary
- **Ink Blue** (`ink-blue`): primary buttons, the selected tab underline, the selected PNC name, focus rings, links and the API badge. Never decorative.

### Neutral
- **Cool Paper** (`cool-paper`): the page background.
- **Sunk Paper** (`sunk-paper`): the PNC list column and the preview side of the dialog, a second layer that is slightly darker than the page.
- **Hairline / Hairline Strong**: dividers, borders around the paper pages, input borders.
- **Ink Text / Slate Text / Quiet Text**: three levels of text, from primary to secondary to metadata. Quiet Text still meets 4.5:1 contrast on the paper background.

### Named Rules
**The One Ink Rule.** Ink Blue marks selection, action, focus and new arrivals. If something isn't one of those, it is neutral.

**The Meaningful Red Rule.** Red appears only for deletion and errors. Green appears only on the live-connection dot.

## Typography

**Display and Body Font:** Manrope Variable, self-hosted. The fallback is Segoe UI Variable.

**Character:** Thin, wide-set headings give the sleek feel. Body text, labels and data stay at 400–600 so they remain readable.

### Hierarchy
- **Display** (300, 2.375rem, 1.15): page and record titles (Document Library, the PNC name). Drops to 1.875rem on small screens.
- **Title** (600, 1.0625rem): the dialog title.
- **Body** (400, 0.9375rem, 1.55): running text. A summary is shown at 1.0625rem and limited to a 68ch line length.
- **Label** (500–600, 0.8125rem): field labels, section headings, metadata. Times and sizes use tabular numbers so they line up.

### Named Rules
**The Thin-Is-For-Large Rule.** Weight 300 is used only at 1.375rem and above. Anything smaller is 400 or heavier.

## Layout

- **Top bar:** a fixed 60px bar holding the wordmark, two underline tabs and a live-connection status.
- **Document Library:** centred, max width 1280px, with an auto-filling grid of 168px-minimum pages (132px on small screens).
- **PNC Records:**
  - A two-column split filling the full height: a list column of 260–320px with its own scroll, and the detail pane.
  - Detail content is limited to 760px wide.
  - Below 760px wide, the columns stack: the list is capped at 38% of the viewport height, with the detail underneath.
- **Gutters:** `clamp(16px, 3vw, 40px)`.

## Elevation & Depth

Mostly flat, built from tonal layers. Shadows are reserved for objects that sit on top of the page.

- **Paper page:** a 1px hairline ring plus a soft, offset ambient shadow. On hover it lifts 3px and the shadow deepens.
- **Dialog:** a deep, soft shadow over a lightly blurred dark backdrop.

## Shapes

- **Corners:** 6px on controls, 10px on placeholders, 14px on the dialog and drop zones.
- **Documents:** pages use a near-square 3px corner, so they read as sheets of paper.
- **Borders:** hairline 1px. Dashed borders mark only empty or drop areas.

## Components

### Buttons
- **Shape:** 6px radius, 38px tall (32px for the small variant).
- **Primary:** Ink Blue background with white text. Darkens on hover.
- **Secondary:** white background with a strong hairline border. On hover it takes the Sunk Paper background.
- **Quiet danger:** red text with no border. On hover it gets a pale red wash. Used for Trash.

### Inputs / Fields
- White background, strong hairline border, 6px radius.
- **Focus:** Ink Blue border plus a 3px ring of Ink Blue at 16% opacity.
- **Error:** red border, with red message text under the field.

### Navigation
- Underline tabs. Inactive tabs use Slate Text. The active tab uses Ink Text, and a 2px Ink-Blue underline scales in beneath it.
- Each tab shows a count in a pill. The active tab's pill is tinted with the Ink Blue wash.

### Document page (signature)
- A first-page PDF thumbnail drawn on a sheet of paper, with the name and size/date below it.
- While loading, it shows a skeleton of placeholder text lines.
- Clicking it opens the details dialog (a native `<dialog>`). Its actions are: rename and press Done, Trash (with an inline confirmation), or Close.

### PNC list item
- Shows the name, a received time, and an `API` badge on PNCs the main app created.
- The selected item becomes a raised white row.
- New arrivals slide in at the top and the Ink Blue wash fades out over 1.6 s.

## Do's and Don'ts

### Do:
- **Do** keep every addition inside the two tabs. This is a mock.
- **Do** use weight 300 only for large display text.
- **Do** theme the browser's own surfaces too: text selection, caret, scrollbars, focus rings.

### Don't:
- **Don't** add filters, search, dashboards or charts.
- **Don't** use Ink Blue decoratively, or add a second accent colour.
- **Don't** use emoji or Unicode characters as icons. Icons are inline SVG with a 1.5px stroke.
