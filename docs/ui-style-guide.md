# UI Style Guide: AI Handyman Secretary Assistant

## Color Palette
- Primary: #2563eb (blue-600)
- Secondary: #fbbf24 (amber-400)
- Surface: #f8fafc (gray-50)
- Accent: #22c55e (green-500)
- Error: #ef4444 (red-500)

## Typography
- Headings: Inter, 700, 1.5em/2em
- Body: Inter, 400, 1em/1.5em
- Labels: Inter, 500, 0.9em

## Spacing
- 8pt grid system
- Responsive breakpoints: 640px, 1024px, 1280px

## Components
- **Sidebar Navigation**: Collapsible on mobile, icons + text
- **Header Bar**: User profile, language switcher, notifications
- **Dashboard Cards**: Schedule, Tasks, Billing, Communications
- **Buttons**: Primary (filled), Secondary (outlined), Destructive
- **Modals & Drawers**: For task/appointment details
- **Tables**: For billing history, task list

## Accessibility
- Sufficient color contrast (AA+)
- Keyboard navigable
- ARIA roles for all interactive elements

---

## Layout Principles
- Modular card-based layout for dashboard summary
- Responsive grid: 1 column (mobile), 2 columns (tablet), 3-4 columns (desktop)
- Sticky navigation/header for easy access
- Consistent iconography (Material Icons)

## Example Dashboard Sections

1. **Schedule Overview**
    - Upcoming appointments (list or calendar view)
    - Quick add scheduling button

2. **Tasks**
    - Active and completed tasks in cards or table
    - Status badges, assignment details

3. **Billing**
    - Recent invoices, payment status
    - Link to view detailed billing history

4. **Communications**
    - Recent messages/notifications
    - Quick access to send a message or join a call

---

## Responsive Guidelines
- Navigation collapses to hamburger menu below 1024px
- Dashboard cards stack vertically on mobile
- Touch targets >= 48px
- Font size scales with viewport width
