# Octavia Liquid Glass Design System - Style Guide

This guide provides detailed specifications to recreate the "Octavia" Liquid Glass design aesthetic. It combines deep, rich dark backgrounds with vibrant neon accents, heavy glassmorphism, and dynamic glow effects.

## 1. Core Design Philosophy
- **Theme**: Cyber-futuristic, premium, deep space.
- **Key Elements**:
    - **Liquid Glass**: High-blur, semi-transparent surfaces with subtle borders.
    - **Neon Glows**: Powerful purple, cyan, and pink ambient lights.
    - **Depth**: Layered z-indexes with shadows and backdrop blurs.
    - **Motion**: Subtle pulses, spins, and hover lifts.

---

## 2. Color Palette

### Primary Colors (Purple Power)
| Name | Hex | Variable | Usage |
|------|-----|----------|-------|
| **Purple Base** | `#9333EA` | `--primary-purple` | Main brand color, buttons, borders |
| **Purple Bright** | `#A855F7` | `--primary-purple-bright` | Hovers, active states, glows |
| **Purple Dark** | `#7E22CE` | `--primary-purple-dark` | Gradients, deep shadows |

### Accent Colors
| Name | Hex | Variable | Usage |
|------|-----|----------|-------|
| **Cyan** | `#06B6D4` | `--accent-cyan` | Secondary actions, info states, cool glows |
| **Pink** | `#EC4899` | `--accent-pink` | Highlights, "hot" actions, warm glows |

### Backgrounds (The Void)
| Name | Hex | Variable | Usage |
|------|-----|----------|-------|
| **Dark** | `#0A0118` | `--bg-dark` | Main page background |
| **Darker** | `#050008` | `--bg-darker` | Deep contrast areas |
| **Glass Base** | `#0D0221` | `--bg-glass` | Base color for glass panels (with opacity) |
| **Surface** | `#120829` | `--bg-surface` | Opaque card surfaces |

---

## 3. Typography

**Font Family**:
- **Display**: `Inter Tight`, sans-serif (Weights: 700, 900)
- **Body**: `Inter`, sans-serif (Weights: 400, 500)

**Text Styles**:
- **Headings**: White (`#FFFFFF`), often with `text-glow-purple` class.
- **Subtext**: Slate 400 (`#94A3B8`) or Slate 500 (`#64748B`).
- **Gradients**: Use `.text-gradient-purple` for special emphasis.

```css
.text-gradient-purple {
  background: linear-gradient(135deg, var(--primary-purple), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

## 4. Glassmorphism System

The core of the design. Always use `backdrop-filter: blur()` combined with semi-transparent backgrounds and borders.

### Glass Variables
```css
:root {
  --glass-low: rgba(13, 2, 33, 0.3);
  --glass-medium: rgba(13, 2, 33, 0.5);
  --glass-high: rgba(13, 2, 33, 0.7);
  --border-glass: rgba(147, 51, 234, 0.15);
  --border-glass-hover: rgba(147, 51, 234, 0.4);
}
```

### Standard Glass Panel (`.glass-panel`)
- **Background**: `var(--glass-medium)`
- **Blur**: `24px`
- **Border**: `1px solid var(--border-glass)`
- **Radius**: `1rem` (16px)
- **Shadow**: `0 8px 32px rgba(0, 0, 0, 0.5)`

### Glass Shine Effect
Add a diagonal shine overlay to glass cards for a premium feel.
```css
.glass-shine::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
  opacity: 0.5;
}
```

---

## 5. Glow Effects & Shadows

Glows are used to create atmosphere and focus.

### CSS Variables
```css
:root {
  --shadow-glow: 0 0 60px rgba(147, 51, 234, 0.6), 0 0 100px rgba(147, 51, 234, 0.3);
  --shadow-glow-strong: 0 0 80px rgba(147, 51, 234, 0.8), 0 0 120px rgba(147, 51, 234, 0.4);
}
```

### Ambient Orbs
Place these `div`s behind content with `position: fixed` or `absolute`.
- **Purple**: `radial-gradient(circle, var(--primary-purple) 0%, var(--primary-purple-bright) 50%, transparent 100%)`
- **Cyan**: `radial-gradient(circle, var(--accent-cyan) 0%, #22D3EE 50%, transparent 100%)`
- **Pink**: `radial-gradient(circle, var(--accent-pink) 0%, #F472B6 50%, transparent 100%)`

**Animation**: `pulse-glow` (4s infinite)

---

## 6. Components

### Buttons

#### 1. Border Beam Button (Primary CTA)
A button with a spinning gradient border.
- **Structure**: Wrapper (`.btn-border-beam`) + Inner (`.btn-border-beam-inner`).
- **Effect**: Conic gradient spinning behind the inner content.
- **Inner**: Dark surface (`#120829`), white text.

#### 2. Glass Secondary
- **Background**: `rgba(255, 255, 255, 0.05)`
- **Border**: `1px solid rgba(255, 255, 255, 0.1)`
- **Hover**: Lightens background and border.

### Inputs (`.glass-input`)
- **Background**: `var(--glass-medium)`
- **Border**: `1px solid var(--border-glass)`
- **Focus**: Border becomes `--primary-purple`, adds ring shadow.
- **Placeholder**: `rgba(255, 255, 255, 0.4)`

### Cards (`.glass-panel-glow`)
- **Base**: Standard glass panel properties.
- **Hover**:
    - Background darkens slightly (`rgba(13, 2, 33, 0.6)`).
    - Border becomes brighter (`--border-glass-hover`).
    - Shadow increases.
    - `transform: translateY(-2px)`.

---

## 7. Layout & Spacing

- **Grid System**: Use CSS Grid or Flexbox.
- **Spacing**: Generous padding (e.g., `p-8` for main content).
- **Sidebar**: Fixed width (`w-64`), glass background (`bg-[#0D0221]/50`), backdrop blur (`backdrop-blur-xl`), border right (`border-white/10`).

---

## 8. Implementation Checklist

1.  **Reset**: Use Tailwind CSS reset or standard normalize.
2.  **Fonts**: Import Inter and Inter Tight from Google Fonts.
3.  **Variables**: Copy the `:root` variables from the Color Palette section into your CSS.
4.  **Background**: Apply `.premium-bg` to the `body`.
    ```css
    .premium-bg {
      background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(147, 51, 234, 0.15), transparent),
                  radial-gradient(ellipse 60% 50% at 50% 120%, rgba(147, 51, 234, 0.1), transparent),
                  var(--bg-dark);
    }
    ```
5.  **Global Styles**: Set `color: white` and `font-family: 'Inter', sans-serif`.
6.  **Utilities**: Add the `.glass-panel`, `.glow-*`, and button classes.

---

## 9. Example HTML Structure

```html
<body class="premium-bg font-body text-white min-h-screen">
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-64 glass-panel-low border-r border-white/10 flex flex-col p-4">
      <!-- Nav Items -->
    </aside>

    <!-- Main Content -->
    <main class="flex-1 relative overflow-y-auto custom-scrollbar p-8">
      <!-- Background Glows -->
      <div class="glow-purple fixed top-0 right-0 w-[600px] h-[600px]"></div>

      <!-- Content -->
      <div class="relative z-10 max-w-6xl mx-auto">
        <h1 class="text-4xl font-display font-bold text-glow-purple mb-8">Dashboard</h1>
        
        <!-- Grid -->
        <div class="grid grid-cols-3 gap-6">
          <div class="glass-panel-glow p-6 rounded-2xl">
            <h2 class="text-xl font-bold mb-2">Card Title</h2>
            <p class="text-slate-400">Card content goes here.</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</body>
```
