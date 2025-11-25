# Screen Readers

Screen readers convert on-screen content into synthesized speech or refreshable braille. The three most-used screen readers are JAWS (Windows, commercial), NVDA (Windows, free), and VoiceOver (macOS and iOS, built-in). TalkBack is Android's built-in screen reader.

## Common keyboard commands

- NVDA: toggle with Insert+N for the menu; read current line with Insert+Up Arrow; list headings with Insert+F7.
- VoiceOver (macOS): toggle with Cmd+F5; the VO modifier defaults to Ctrl+Option; rotor with VO+U.
- JAWS: toggle with Insert+F4 to quit; list headings with Insert+F6.

## ARIA landmarks and headings

Screen reader users navigate primarily by headings (h1-h6) and ARIA landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`, `role="search"`). A clean heading outline is the single highest-impact accessibility fix for most sites.

## Live regions

Use `aria-live="polite"` for non-urgent updates (e.g. form validation summaries) and `aria-live="assertive"` for urgent ones (e.g. session timeouts). Overusing assertive is noisy and disruptive.

## Name, role, value

Every interactive control must expose an accessible name, a role, and its current state or value. Native HTML elements (`<button>`, `<a href>`, `<input>`) get this for free; custom widgets need ARIA.
