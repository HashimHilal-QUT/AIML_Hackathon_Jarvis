# Design System Specification: Editorial Vitality

## 1. Overview & Creative North Star
### The Creative North Star: "The Culinary Socialite"
This design system rejects the "utilitarian cafeteria" aesthetic in favor of a high-energy, editorial experience. It is designed to feel like a premium food magazine brought to life—vibrant, tactile, and deeply social. We move beyond the standard "app-on-a-grid" by utilizing **Dynamic Asymmetry** and **Tonal Depth**. Elements should feel like they are floating in a curated space, with overlapping imagery and bold typography that breaks the container to create a sense of movement and "craveability."

## 2. Color Theory & Visual Soul
The palette balances a professional, institutional foundation (QUT Blue) with "Zest" accents that trigger appetite and energy.

*   **Primary Engine (`#2d5c98`):** Use for brand authority and navigation. It provides the "anchor" for the student experience.
*   **Secondary Zest (`#9b3f00`):** The "Flame" accent. Use this for high-conversion actions and food highlights. It is warm, appetizing, and high-energy.
*   **Tertiary Fresh (`#176a21`):** The "Garden" accent. Use this for health-focused indicators, plant-based options, and "open" status indicators.

### The "No-Line" Rule
**Explicit Instruction:** Traditional 1px solid borders are strictly prohibited for sectioning. Boundaries must be defined through background color shifts.
*   *Example:* A `surface-container-low` card sitting on a `surface` background provides all the definition needed. If you feel the urge to draw a line, use white space instead.

### The "Glass & Gradient" Rule
To escape the "flat" look of utility apps, use **Glassmorphism** for floating headers and navigation bars. Use semi-transparent versions of `surface-container` with a `backdrop-blur` of 12px–20px. 
*   **Signature Textures:** For Hero sections, apply a subtle linear gradient from `primary` to `primary-container` at a 135-degree angle. This adds "soul" and depth to the digital canvas.

## 3. Typography: Friendly Authority
We utilize a two-family system to balance "High-Energy" with "High-Readability."

*   **Display & Headlines (Plus Jakarta Sans):** A modern, geometric sans-serif with a friendly soul. 
    *   *Usage:* Use `display-lg` for daily specials and `headline-md` for social feed headers. Embrace the generous x-height to make the app feel approachable.
*   **Body & Labels (Be Vietnam Pro):** Chosen for its exceptional legibility at small scales.
    *   *Usage:* All transactional data, ingredient lists, and timestamps must use `body-md` or `label-md`.

**The Scale Logic:** Use high-contrast sizing. A `display-sm` headline next to a `body-md` description creates an editorial hierarchy that feels intentional and premium.

## 4. Elevation & Depth: Tonal Layering
Forget shadows as a default; we build depth through "Stacking."

*   **The Layering Principle:** 
    *   Level 0: `surface` (The Base)
    *   Level 1: `surface-container-low` (Content Sections)
    *   Level 2: `surface-container-highest` (Interactive Cards/Action Modals)
*   **Ambient Shadows:** If an element must float (like a floating action button), use an extra-diffused shadow: `box-shadow: 0 12px 32px rgba(31, 45, 81, 0.06);`. The shadow color must be a tint of `on-surface`, never pure black.
*   **The Ghost Border:** If accessibility requires a stroke (e.g., in high-contrast mode), use `outline-variant` at **15% opacity**. It should be felt, not seen.

## 5. Components & Interface Elements

### Buttons: The "Soft-Tactile" Feel
*   **Primary:** `primary` background with `on-primary` text. Use `xl` (3rem) roundedness for a pill shape.
*   **Secondary:** `secondary-container` background with `on-secondary-container` text. This is for "Add to Cart" or "Join Table" actions.
*   **Interaction:** On hover/press, shift background color to `primary-dim` or `secondary-dim`.

### Cards & Lists: The No-Divider Standard
*   **Cards:** Use `DEFAULT` (1rem) roundedness. Cards must never have borders. Use a `surface-container-low` fill. 
*   **Lists:** Forbid divider lines. Separate list items using 12px of vertical spacing. For item grouping, use a subtle background shift to `surface-container-lowest`.

### Input Fields: The "Clean-Entry"
*   **Styling:** Fill with `surface-container-highest`. No border. Use `sm` (0.5rem) roundedness.
*   **Focus State:** Transition the background to `surface-container-lowest` and apply a 2px `surface-tint` "Ghost Border" at 20% opacity.

### Social "Buddy" Chips
*   **Selection Chips:** Use `tertiary-container` for "Active" states (e.g., "Dining with Friends") to signal a positive, social status.
*   **Action Chips:** Pill-shaped, using `surface-container-high` to remain neutral but clickable.

## 6. Do's and Don'ts

### Do:
*   **Do** overlap high-quality food photography over container edges to break the "box" feel.
*   **Do** use `secondary` (Orange) for price points and hunger-inducing CTAs.
*   **Do** use generous whitespace (32px+) between major content sections.
*   **Do** utilize `xl` roundedness on buttons to maintain an approachable, friendly vibe.

### Don't:
*   **Don't** use 1px dividers to separate menu items. Use white space or tonal shifts.
*   **Don't** use pure black `#000000` for text; always use `on-surface` (`#1f2d51`) for a softer, premium contrast.
*   **Don't** use "Drop Shadows" on cards unless they are part of a temporary overlay/modal.
*   **Don't** cram content. If the screen feels full, increase the `surface` padding.