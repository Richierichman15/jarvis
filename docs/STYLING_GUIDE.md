# Styling Guide

## Color Scheme
- Primary: `#3B82F6` (Blue-500)
- Background: `#111827` (Gray-900)
- Card Background: `#1F2937` (Gray-800)
- Text: 
  - Primary: `#F9FAFB` (Gray-50)
  - Secondary: `#9CA3AF` (Gray-400)

## Typography
- Font Family: Inter (from Google Fonts)
- Headings: 
  - h1: 2.5rem (40px) font-bold
  - h2: 1.875rem (30px) font-semibold
  - h3: 1.5rem (24px) font-medium

## Components

### Buttons
```css
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200;
}

.btn-secondary {
  @apply bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200;
}
```

### Cards
```css
.card {
  @apply bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-200;
}
```

### Forms
```css
.input-field {
  @apply bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500;
}
```

## Animations
- Hover effects on interactive elements
- Smooth transitions for state changes
- Loading spinners for async operations
