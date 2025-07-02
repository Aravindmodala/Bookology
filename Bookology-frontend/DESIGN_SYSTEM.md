# Bookology Design System

## Overview
The Bookology frontend uses a modern black and white design system built with Tailwind CSS and custom CSS variables. This system prioritizes accessibility, responsiveness, and visual hierarchy.

## Color Palette

### Primary Colors
```css
--color-black: #000000      /* Pure black background */
--color-white: #ffffff      /* Pure white text/accents */
```

### Gray Scale
```css
--color-gray-900: #111111   /* Darkest gray - cards, modals */
--color-gray-800: #1a1a1a   /* Dark gray - secondary backgrounds */
--color-gray-700: #2a2a2a   /* Medium dark - borders */
--color-gray-600: #404040   /* Medium - disabled states */
--color-gray-500: #666666   /* Light medium - muted text */
--color-gray-400: #888888   /* Light - placeholder text */
--color-gray-300: #aaaaaa   /* Lighter - secondary text */
--color-gray-200: #cccccc   /* Very light - body text */
--color-gray-100: #f5f5f5   /* Lightest - light mode (future) */
```

## Typography

### Font Stack
```css
font-family: 'Inter', 'Segoe UI', 'Roboto', system-ui, -apple-system, sans-serif;
```

### Type Scale
```css
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */
--text-5xl: 3rem      /* 48px */
```

### Typography Usage
- **h1**: `text-4xl` (36px) - Page titles
- **h2**: `text-3xl` (30px) - Section headings
- **h3**: `text-2xl` (24px) - Subsection headings
- **h4**: `text-xl` (20px) - Card titles
- **h5**: `text-lg` (18px) - Small headings
- **Body**: `text-base` (16px) - Main content
- **Small**: `text-sm` (14px) - Secondary content
- **Caption**: `text-xs` (12px) - Metadata, timestamps

## Spacing System

### Scale
```css
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-5: 1.25rem   /* 20px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-10: 2.5rem   /* 40px */
--space-12: 3rem     /* 48px */
--space-16: 4rem     /* 64px */
--space-20: 5rem     /* 80px */
--space-24: 6rem     /* 96px */
```

### Usage Guidelines
- **Component padding**: `space-6` (24px) for cards, modals
- **Section spacing**: `space-16` to `space-24` (64px-96px)
- **Element gaps**: `space-4` to `space-6` (16px-24px)
- **Button padding**: `space-3` to `space-6` (12px-24px)

## Component Library

### Buttons

#### Primary Button
```css
.btn-primary {
  @apply bg-white text-black border-2 border-white font-medium px-6 py-3 rounded-lg;
  @apply hover:bg-transparent hover:text-white transition-all duration-300;
  @apply focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black;
  @apply active:scale-95;
}
```

#### Secondary Button
```css
.btn-secondary {
  @apply bg-transparent text-white border-2 border-white font-medium px-6 py-3 rounded-lg;
  @apply hover:bg-white hover:text-black transition-all duration-300;
  @apply focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black;
  @apply active:scale-95;
}
```

#### Ghost Button
```css
.btn-ghost {
  @apply bg-transparent text-white border-2 border-gray-600 font-medium px-6 py-3 rounded-lg;
  @apply hover:border-white transition-all duration-300;
  @apply focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 focus:ring-offset-black;
  @apply active:scale-95;
}
```

#### Icon Button
```css
.btn-icon {
  @apply w-10 h-10 flex items-center justify-center bg-transparent border-2 border-gray-600 rounded-lg;
  @apply hover:border-white transition-all duration-300;
  @apply focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 focus:ring-offset-black;
  @apply active:scale-95;
}
```

### Cards
```css
.card {
  @apply bg-gray-900 border border-gray-800 rounded-xl p-6;
  @apply shadow-lg backdrop-blur-sm;
}
```

### Form Elements

#### Input Field
```css
.input-field {
  @apply w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3;
  @apply text-white placeholder-gray-400;
  @apply focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent;
  @apply transition-all duration-300;
}
```

#### Textarea Field
```css
.textarea-field {
  @apply w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3;
  @apply text-white placeholder-gray-400 resize-none;
  @apply focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent;
  @apply transition-all duration-300;
}
```

### Layout Components

#### Container
```css
.container {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8;
}
```

#### Section
```css
.section {
  @apply py-16 sm:py-20 lg:py-24;
}
```

### Modal Components

#### Modal Overlay
```css
.modal-overlay {
  @apply fixed inset-0 bg-black bg-opacity-75 backdrop-blur-sm z-50;
  @apply flex items-center justify-center p-4;
}
```

#### Modal Content
```css
.modal-content {
  @apply bg-gray-900 border border-gray-800 rounded-2xl;
  @apply max-w-4xl w-full max-h-[90vh] overflow-hidden;
  @apply shadow-2xl;
}
```

### Navigation

#### Nav Link
```css
.nav-link {
  @apply text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium;
  @apply transition-all duration-300;
}

.nav-link.active {
  @apply text-white bg-gray-800;
}
```

## Responsive Design

### Breakpoints
- **sm**: 640px - Small tablets
- **md**: 768px - Tablets
- **lg**: 1024px - Small desktops
- **xl**: 1280px - Large desktops
- **2xl**: 1536px - Extra large screens

### Mobile-First Approach
All components are designed mobile-first with progressive enhancement for larger screens.

### Touch Targets
- Minimum touch target size: 44px × 44px
- Button padding ensures adequate touch area
- Proper spacing between interactive elements

## Accessibility

### Color Contrast
- All text meets WCAG 2.1 AA standards
- White text on black background: 21:1 ratio
- Gray text maintains minimum 4.5:1 ratio

### Focus Management
- Visible focus indicators on all interactive elements
- Keyboard navigation support
- Skip links for screen readers

### Screen Reader Support
- Semantic HTML structure
- Proper ARIA labels and roles
- Descriptive alt text for images

## Animation and Transitions

### Transition Timing
```css
--transition-fast: 150ms ease-in-out;
--transition-normal: 300ms ease-in-out;
--transition-slow: 500ms ease-in-out;
```

### Animation Classes
- `.animate-slide-in-bottom`: Modal entrance
- `.animate-slide-in-top`: Dropdown entrance
- `.animate-fade-in`: General fade-in
- `.animate-pulse`: Loading states

### Principles
- Subtle and purposeful animations
- Respect `prefers-reduced-motion`
- Performance-optimized transforms

## Best Practices

### Component Usage
1. Use semantic HTML elements
2. Apply utility classes over custom CSS
3. Maintain consistent spacing
4. Follow the established hierarchy
5. Test on multiple screen sizes

### Performance
1. Minimize custom CSS
2. Use Tailwind's purge feature
3. Optimize images and assets
4. Lazy load heavy components

### Maintenance
1. Document new components
2. Update design tokens in CSS variables
3. Test accessibility with each change
4. Maintain consistent naming conventions

## Usage Examples

### Basic Page Layout
```jsx
<div className="min-h-screen bg-black">
  <Navbar />
  <main className="container section">
    <div className="card">
      <h1 className="text-3xl font-bold text-white mb-4">Page Title</h1>
      <p className="text-gray-200 mb-6">Content goes here</p>
      <button className="btn-primary">Call to Action</button>
    </div>
  </main>
</div>
```

### Form Layout
```jsx
<form className="space-y-6">
  <div>
    <label className="block text-sm font-medium text-gray-300 mb-2">
      Email
    </label>
    <input 
      type="email" 
      className="input-field" 
      placeholder="Enter your email"
    />
  </div>
  <button type="submit" className="btn-primary w-full">
    Submit
  </button>
</form>
```

### Modal Implementation
```jsx
<div className="modal-overlay">
  <div className="modal-content">
    <div className="flex justify-between items-center p-6 border-b border-gray-800">
      <h2 className="text-xl font-bold text-white">Modal Title</h2>
      <button className="btn-icon">✕</button>
    </div>
    <div className="p-6">
      Modal content
    </div>
  </div>
</div>
```

This design system ensures consistent, accessible, and maintainable UI components across the Bookology application.