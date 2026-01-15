# Evidence Tray & Source Links - Visual Styling Proposal

## Design Philosophy
Move from "cold enterprise" to "warm modern" - inspired by Notion, Linear, and other modern productivity tools. Maintain professionalism while feeling more approachable and human.

---

## 1. Source Links [1] Styling

### Current Issues
- Plain link buttons feel too technical/clinical
- Dotted underline is too subtle
- No visual weight or presence
- Feels like a footnote, not an interactive element

### Proposed Changes

#### Option A: Pill Badge Style (Recommended)
```
[1] → Small pill-shaped badge with:
- Soft background: #F0F4FF (light blue tint)
- Border: 1px solid #D6E4FF (slightly darker blue)
- Text: #4A6CF7 (minos color, but softer)
- Border radius: 12px (fully rounded)
- Padding: 2px 8px
- Font size: 11px
- Font weight: 500
- Hover: Slight scale (1.05), darker background (#E0E9FF)
- Active: Scale (0.95)
- Transition: all 0.2s ease
```

#### Option B: Icon + Number
```
[1] → Small circular badge with:
- Background: #F5F7FA (warm gray)
- Border: 1px solid #E5E9F0
- Icon: Small document/evidence icon (6px)
- Number: 11px, medium weight
- Hover: Background shifts to #EBEEF5, border to #D1D9E6
```

#### Option C: Underline with Background
```
[1] → Inline with:
- Background: rgba(74, 108, 247, 0.08) (very light minos)
- Border radius: 3px
- Padding: 1px 4px
- Text: #4A6CF7
- Hover: Background to rgba(74, 108, 247, 0.12)
```

**Recommendation: Option A (Pill Badge)** - Most modern, clear, and interactive feeling.

---

## 2. Evidence Tray Styling

### Current Issues
- Too much white space feels sterile
- Hard borders feel harsh
- Cards feel disconnected
- Typography hierarchy unclear
- Colors too muted/cold

### Proposed Changes

#### A. Background & Container
```css
- Drawer background: #FAFBFC (warm off-white, not pure white)
- Card backgrounds: #FFFFFF (pure white for contrast)
- Subtle gradient or texture (optional): Very light warm tint
```

#### B. Card Styling
```css
Question Cards:
- Background: #FFFFFF
- Border: 1px solid #E8EBED (softer, warmer gray)
- Border radius: 12px (more rounded)
- Box shadow: 0 1px 3px rgba(0, 0, 0, 0.04) (softer shadow)
- Padding: 20px (more breathing room)
- Hover: Border color shifts to #D1D9E6, shadow increases slightly
- Transition: all 0.2s ease

Evidence Type Cards (System/Human/Analysis):
- Background: #F8F9FA (very light warm gray)
- Border: 1px solid #E8EBED
- Border radius: 8px
- Padding: 16px
- Margin: 8px 0
```

#### C. Typography
```css
Question Headers:
- Font size: 15px (slightly larger)
- Font weight: 600 (not bold, but semibold)
- Color: #1A1F36 (warmer dark, not pure black)
- Line height: 1.4

Section Headers (System/Human/Analysis):
- Font size: 13px
- Font weight: 500
- Color: #4A5568 (warmer gray)
- Letter spacing: -0.01em (slightly tighter)

Body Text:
- Font size: 13px (not 12px)
- Line height: 1.6 (more breathing room)
- Color: #4A5568 (warmer than pure gray)
```

#### D. Colors & Accents
```css
Primary Accent (minos):
- Use softer variant: #5B7FFF (slightly lighter, more vibrant)
- For hover states: #4A6CF7

Success/Verified:
- Softer green: #10B981 (not harsh)
- Background tint: #ECFDF5

Warning/Pending:
- Softer amber: #F59E0B
- Background tint: #FFFBEB

Tags/Badges:
- Background: rgba(74, 108, 247, 0.1)
- Border: rgba(74, 108, 247, 0.2)
- Text: #4A6CF7
- Border radius: 6px
```

#### E. Interactive Elements
```css
Collapse Headers:
- Hover background: #F8F9FA (subtle)
- Active background: #F1F3F5
- Padding: 12px 16px (more comfortable)
- Border radius: 8px on hover

Buttons (View evidence, Export):
- Background: #F8F9FA
- Border: 1px solid #E8EBED
- Border radius: 8px
- Hover: Background #F1F3F5, border #D1D9E6
- Active: Scale 0.98
```

#### F. Evidence Items
```css
System/Human/Analysis Items:
- Background: #FFFFFF (white cards on gray background)
- Border: 1px solid #E8EBED
- Border radius: 8px
- Padding: 16px
- Margin: 8px 0
- Hover: Border color #D1D9E6, subtle shadow
- Transition: all 0.15s ease

Source Links in Items:
- Color: #5B7FFF
- Hover: Underline appears
- Font weight: 500
```

#### G. Spacing & Layout
```css
- Increase padding throughout: 20px → 24px
- More generous gaps: 16px → 20px between sections
- Card margins: 12px → 16px
- Inner padding: 12px → 16px
- Section spacing: 24px → 32px
```

#### H. Icons & Visual Elements
```css
- Use softer icon colors: #6B7280 (not pure gray)
- Icon size: 14px (slightly larger for better visibility)
- Add subtle icon backgrounds on hover
- Use Ant Design X icons where appropriate
```

---

## 3. Specific Component Updates

### Source Links [1] Component
```tsx
// Pill badge style
<Button
  type="text"
  style={{
    padding: "2px 8px",
    height: "auto",
    minHeight: "auto",
    fontSize: 11,
    fontWeight: 500,
    color: "#4A6CF7",
    backgroundColor: "#F0F4FF",
    border: "1px solid #D6E4FF",
    borderRadius: 12,
    lineHeight: 1.2,
    transition: "all 0.2s ease",
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.backgroundColor = "#E0E9FF";
    e.currentTarget.style.transform = "scale(1.05)";
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.backgroundColor = "#F0F4FF";
    e.currentTarget.style.transform = "scale(1)";
  }}
>
  [1]
</Button>
```

### Evidence Tray Cards
```tsx
// Warmer, softer card styling
<Card
  style={{
    border: "1px solid #E8EBED",
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
    transition: "all 0.2s ease",
  }}
  bodyStyle={{
    padding: 20,
  }}
  hoverable
  onMouseEnter={(e) => {
    e.currentTarget.style.borderColor = "#D1D9E6";
    e.currentTarget.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.06)";
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.borderColor = "#E8EBED";
    e.currentTarget.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.04)";
  }}
>
```

### Drawer Background
```tsx
// Warmer background
<Drawer
  styles={{
    body: {
      backgroundColor: "#FAFBFC", // Warm off-white
      padding: 0,
    },
  }}
/>
```

---

## 4. Typography Scale
```
- H1 (Question): 15px, 600 weight, #1A1F36
- H2 (Section): 13px, 500 weight, #4A5568
- Body: 13px, 400 weight, #4A5568
- Small/Secondary: 12px, 400 weight, #6B7280
- Caption: 11px, 400 weight, #9CA3AF
```

---

## 5. Color Palette Updates
```
Primary (minos): #5B7FFF → #4A6CF7 (hover)
Background: #FAFBFC (warm off-white)
Card: #FFFFFF
Border: #E8EBED (soft gray)
Text Primary: #1A1F36 (warm dark)
Text Secondary: #4A5568 (warm gray)
Text Tertiary: #6B7280 (medium gray)
Success: #10B981
Warning: #F59E0B
Error: #EF4444
```

---

## 6. Animation & Transitions
```
- All transitions: 0.2s ease (smooth, not jarring)
- Hover scale: 1.05 (subtle, not dramatic)
- Active scale: 0.98 (tactile feedback)
- Smooth scroll: behavior: "smooth"
- Focus highlight: 0.3s fade in/out
```

---

## 7. Specific Improvements

### Source Links
- ✅ Pill badge style (Option A)
- ✅ Hover scale effect
- ✅ Softer colors
- ✅ Better visual weight

### Evidence Tray
- ✅ Warmer background (#FAFBFC)
- ✅ Softer borders (#E8EBED)
- ✅ More rounded corners (12px)
- ✅ Better shadows (softer, more subtle)
- ✅ Improved spacing (more breathing room)
- ✅ Warmer text colors
- ✅ Better hover states
- ✅ Smoother transitions

### Cards
- ✅ White cards on warm background
- ✅ Softer borders
- ✅ Hover effects
- ✅ Better padding

---

## Implementation Priority

1. **High Priority:**
   - Source link pill badges
   - Warmer background colors
   - Softer borders
   - Better spacing

2. **Medium Priority:**
   - Typography updates
   - Hover states
   - Shadow improvements

3. **Low Priority:**
   - Subtle animations
   - Icon updates
   - Advanced hover effects

---

## Visual Examples

### Source Link Before/After
**Before:** Plain link with dotted underline `[1]`
**After:** Pill badge `[1]` with soft blue background, rounded, hover effect

### Evidence Tray Before/After
**Before:** White background, hard borders, clinical feel
**After:** Warm off-white background, soft borders, rounded corners, modern feel

### Cards Before/After
**Before:** Sharp corners, minimal shadow, disconnected
**After:** Rounded corners, soft shadow, cohesive, hover effects

---

## Notes
- Maintain accessibility (contrast ratios)
- Keep Ant Design X components
- Ensure responsive design still works
- Test hover states on touch devices
- Consider dark mode compatibility (future)
