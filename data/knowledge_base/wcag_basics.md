# WCAG 2.2 Basics

The Web Content Accessibility Guidelines (WCAG) 2.2 are organized around four principles: Perceivable, Operable, Understandable, and Robust (POUR). Each principle contains guidelines with testable success criteria graded A, AA, or AAA.

Level AA is the most common legal benchmark (referenced by the ADA, EAA, and Section 508). Level AAA is aspirational and often impractical for entire sites.

WCAG 2.2 added nine new success criteria, including 2.4.11 Focus Not Obscured (Minimum), 2.5.7 Dragging Movements, and 2.5.8 Target Size (Minimum, 24x24 CSS pixels).

## Contrast

Success criterion 1.4.3 Contrast (Minimum) requires a 4.5:1 contrast ratio for normal text and 3:1 for large text (18pt or 14pt bold). Non-text UI components and graphical objects need 3:1 under 1.4.11 Non-text Contrast.

## Keyboard

Success criterion 2.1.1 Keyboard requires that all functionality be operable through a keyboard interface. 2.1.2 No Keyboard Trap forbids focus being stuck in a component. 2.4.7 Focus Visible requires a visible focus indicator.

## Alt text

1.1.1 Non-text Content requires a text alternative for non-text content. Decorative images should use an empty alt attribute (`alt=""`) so screen readers skip them.
