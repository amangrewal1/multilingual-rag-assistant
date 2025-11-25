# Keyboard Navigation

Many users navigate the web without a mouse: screen reader users, people with motor impairments, power users, and anyone using a device where a pointing device has failed. Keyboard support is required by WCAG 2.1.1.

## Tab order

Focus moves via Tab (forward) and Shift+Tab (backward) through interactive elements in DOM order unless overridden by `tabindex`. `tabindex="0"` adds an element to the tab order at its DOM position. `tabindex="-1"` removes it from the tab order but allows programmatic focus. Positive `tabindex` values are considered an anti-pattern because they break predictable order.

## Focus indicators

Under WCAG 2.4.7, the focused element must be visually distinguishable. Never use `outline: none` without providing an equivalent custom focus style. WCAG 2.4.11 Focus Not Obscured (Minimum, AA) additionally requires that sticky headers or cookie banners do not fully hide the focused element.

## Skip links

A "Skip to main content" link as the first focusable element lets keyboard users bypass repetitive navigation (WCAG 2.4.1 Bypass Blocks). Keep the link visible on focus even if hidden by default.

## Modal dialogs

Modal dialogs must trap focus while open, restore focus to the trigger on close, and allow Escape to dismiss. Use the native `<dialog>` element or the WAI-ARIA Authoring Practices `dialog` pattern.
