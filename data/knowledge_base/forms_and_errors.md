# Accessible Forms and Error Handling

## Labels

Every input needs a programmatically associated label. The simplest approach is `<label for="id">` paired with `<input id="id">`. Placeholder text is not a label because it disappears on input and often has insufficient contrast.

## Required fields

Mark required fields with both a visual indicator (e.g. an asterisk with a legend "* required") and the `required` attribute. `aria-required="true"` can reinforce this for ARIA-only widgets.

## Error messages

WCAG 3.3.1 Error Identification requires that errors be identified in text. 3.3.3 Error Suggestion (AA) requires suggestions for fixing the error when known. Link the error message to the input via `aria-describedby` so screen readers announce it when the field receives focus.

## Inline validation

Do not validate on every keystroke; users can't finish typing. Validate on blur or on submit. Announce validation summaries in an `aria-live="polite"` region so screen reader users hear them without losing focus.

## Autocomplete

Use the `autocomplete` attribute (`name`, `email`, `street-address`, etc.) per WCAG 1.3.5 Identify Input Purpose. This also helps password managers and users with cognitive disabilities.
