# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Node (v26) with built-in `node:http` and `node:sqlite`; plain HTML/CSS/JS front end, no framework, no build step. Dependencies (official npm registry, installed with `--ignore-scripts`): `pdfjs-dist` for PDF thumbnails, `@fontsource-variable/manrope` for the typeface. Runs on localhost only.

## Users

- Intake staff at a law practice, who manage the practice's document templates and look over incoming PNC (Potential New Client) profiles.
- A separate "main app" that calls this product's API to create PNC profiles and to fetch document templates.

## Product Purpose

A barebones mock of a legal-intake CRM. It has two jobs:
- Host the practice's PDF templates, each tagged with a kind the main app looks it up by.
- Make it visible that the main app is working, as PNC profiles arrive and fill in.

It should look polished, but it only needs to function minimally.

## Capabilities and Constraints

- **Document Library:**
  - Upload PDF templates by dragging and dropping, or load the main app's templates with `npm run seed`.
  - View them as a grid of cards with first-page thumbnails.
  - Open a document's details to rename it or trash it.
  - PDF only. No filtering or search.
- **PNC Records:**
  - A list of PNCs with a detail view.
  - PNCs can be added by hand in the UI.
  - PNCs posted by the main app appear live.
  - The detail view shows the call's intake record: disposition, summary, flags, one card per record section, missing information, and a Documents section that stays *Not sent yet* until e-signature is built.
- **API, protected by an API key:**
  - `POST` a PNC profile, or `PUT` one by the main app's call ID (create or update, with the full intake record).
  - List documents (with their kind) and `GET` them.
- **Terminology:** PNC means Potential New Client.

## Product Principles

- It's a mock: no features beyond those listed above.
- It looks polished but stays simple. Easy reading comes first.
- The API is the important surface. The UI exists to make its work visible.
