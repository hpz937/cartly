# Future Ideas & Improvements

This document tracks potential features, enhancements, and improvements for Cartly.

## High Priority

### Recipe Search & Filtering
- [x] Add search bar to filter recipes by name
- [x] Search within recipe descriptions
- [x] Sort recipes by name (A-Z, Z-A)
- [x] Sort recipes by date (newest/oldest first)
- [ ] Search within ingredients (find recipes using "chicken")
- [ ] Filter by prep time, cook time, servings
- [ ] Filter by recipes whose ingredients are already in shopping list

### Recipe Scaling
- [x] Add servings adjuster with +/- buttons
- [x] Automatically scale all ingredient quantities
- [x] Handle fractional conversions (1/2 cup → 1 cup when doubling)
- [x] Preserve original servings in recipe data

### Missing Test Coverage
- [ ] Add tests for recipe import/export functionality
- [ ] Add tests for drag-and-drop reordering persistence
- [ ] Add tests for notes field save/retrieve
- [ ] Add tests for photo upload edge cases
- [ ] Add tests for recipe scaling (when implemented)

### Shopping List Export/Import
- [ ] Add "Export List" button to shopping list view
- [ ] Export format: JSON with items, categories, metadata
- [ ] Import shopping lists from JSON
- [ ] Merge imported items with existing list (duplicate detection)

## Medium Priority

### UX Improvements

#### Recipe Duplication
- [ ] Add "Duplicate Recipe" button in recipe detail view
- [ ] Copy all ingredients, steps, metadata (except photo initially)
- [ ] Append " (Copy)" to duplicated recipe name
- [ ] Option to include photo in duplication

#### Better Default List UX
- [ ] Add visual indicator (star icon filled vs outline)
- [ ] Show "Default" label more prominently
- [ ] Confirm dialog when changing default list
- [ ] Show default list in a special position (top of list)

#### Ingredient Input Helpers
- [ ] Autocomplete for common units (cups, tbsp, tsp, ml, grams, oz)
- [ ] Autocomplete for common ingredients
- [ ] Quick unit converter tooltip
- [ ] Standardize unit formatting across recipes

#### Cooking Mode
- [ ] Add "Start Cooking" button in recipe view
- [ ] Show steps one at a time with large text
- [ ] Add checkboxes to mark steps complete (session only)
- [ ] Timer integration for steps mentioning time
- [ ] Hands-free navigation (voice commands or large next/prev buttons)

#### Bulk Recipe-to-List
- [ ] Allow selecting multiple recipes from recipe list
- [ ] "Add Selected to Shopping List" button
- [ ] Show combined ingredient count before adding
- [ ] Merge duplicate ingredients across recipes

### Data Management

#### Recipe Features
- [ ] Add tags/categories (breakfast, dessert, vegetarian, quick, etc.)
- [ ] Add source URL field to track recipe origin
- [ ] Add difficulty level (easy, medium, hard)
- [ ] Add rating system (1-5 stars)
- [ ] Add "last made" timestamp
- [ ] Add yield field (separate from servings, e.g., "24 cookies")
- [ ] Add cost estimation field

#### Database Backup/Restore
- [ ] "Backup Everything" button - exports entire database
- [ ] Export format includes lists, recipes, settings, metadata
- [ ] "Restore from Backup" with merge or replace options
- [ ] Automatic backup scheduling option
- [ ] Backup history/versioning

#### Shopping List Features
- [ ] Merge multiple shopping lists into one
- [ ] Copy list (not just export/import)
- [ ] Share list via link or QR code
- [ ] List templates (common grocery runs)
- [ ] Add price field to items for budget tracking
- [ ] Store history (track what you bought when)

## Low Priority / Nice-to-Have

### UI/UX Polish
- [x] Theme-matched modals instead of browser prompt/confirm dialogs
- [ ] Toast notifications for success/info messages (currently using modals)
- [ ] Loading spinners for async operations
- [ ] Dark mode toggle (currently always dark)
- [ ] Customizable theme colors
- [ ] Print-friendly recipe view (CSS @media print)
- [ ] Print-friendly shopping list view

### Advanced Recipe Features
- [ ] Nutrition information fields (calories, protein, carbs, fat)
- [ ] Nutrition calculator based on ingredients
- [ ] Prep/cook time validation warnings
- [ ] Recipe versioning/edit history
- [ ] Recipe collections/cookbooks
- [ ] Meal planning calendar
- [ ] Seasonal recipe suggestions
- [ ] Recipe recommendations based on shopping list

### Technical Improvements

#### Frontend Architecture
- [x] Extract CSS and JavaScript from HTML into separate files
- [x] Implement Alpine.js for reactive components
- [x] Implement Tailwind CSS for consistent styling
- [ ] Further split into modules (recipes.js, lists.js, api.js, ui.js)
- [ ] Better state management (Pinia or similar)
- [ ] Reduce duplication in rendering code

#### Performance & Storage
- [ ] Move photos from base64 in database to filesystem
- [ ] Lazy load recipe photos (thumbnails vs full size)
- [ ] Pagination for large recipe lists
- [ ] Virtual scrolling for long shopping lists
- [ ] Cache API responses client-side
- [ ] Service worker for offline support

#### Progressive Web App (PWA)
- [ ] Add manifest.json for "install to home screen"
- [ ] Service worker for offline functionality
- [ ] Cache recipes for offline access
- [ ] Sync changes when back online
- [ ] Push notifications (e.g., recipe reminders)

#### Developer Experience
- [ ] Add `.gitattributes` to fix CRLF/LF warnings
- [ ] API versioning (e.g., /api/v1/recipes)
- [ ] OpenAPI/Swagger documentation
- [ ] Docker health checks
- [ ] Automated testing in CI/CD
- [ ] Code linting and formatting

### Security & Multi-User

#### Basic Security
- [ ] Simple password protection at nginx level
- [ ] Rate limiting on API endpoints
- [ ] Input sanitization improvements
- [ ] File upload size limits (already exists, but validate more strictly)
- [ ] CSRF protection for POST/PUT/DELETE endpoints

#### Multi-User Support (Major Feature)
- [ ] User authentication system
- [ ] User registration and login
- [ ] Personal recipe collections per user
- [ ] Shared recipes (public/private)
- [ ] Shared shopping lists (family accounts)
- [ ] Permission system (view/edit/admin)

## Community & Sharing

### Recipe Sharing
- [ ] Generate shareable recipe links
- [ ] QR codes for recipes
- [ ] Export recipe as PDF
- [ ] Export recipe as formatted text (WhatsApp, email)
- [ ] Recipe image generation (card with photo and name)

### Integration Ideas
- [ ] Import recipes from URLs (recipe scraping)
- [ ] Export to popular recipe apps
- [ ] Grocery delivery integration
- [ ] Kitchen appliance integration (smart ovens, etc.)
- [ ] Voice assistant integration (Alexa, Google Home)

## Known Issues / Tech Debt

- [ ] Base64 photos bloat database size
- [ ] No error logging/monitoring system
- [x] Frontend HTML file is 1700+ lines (needs refactoring)
- [ ] Some error messages too generic for users
- [ ] No request logging for debugging
- [x] Git line ending warnings (need .gitattributes)

---

## Contributing Ideas

Have an idea not listed here? Add it! Feel free to:
1. Add new ideas to the appropriate section
2. Mark items with `[In Progress]` when working on them
3. Move completed items to a "Done" section with date
4. Add priority labels: `[P0]` (critical), `[P1]` (high), `[P2]` (medium), `[P3]` (low)

## Recently Completed

- ✅ Theme-matched modals for all user input dialogs (2026-02-01)
- ✅ Alpine.js + Tailwind CSS frontend rebuild with dark mode (2026-02-01)
- ✅ Recipe search and sorting (name, date) (2026-02-01)
- ✅ Shopping list categories with grouping (2026-02-01)
- ✅ Recipe scaling with servings adjuster (2026-02-01)
- ✅ Recipe import/export in JSON format (2026-02-01)
- ✅ Drag-and-drop reordering for ingredients and steps (2026-02-01)
- ✅ Notes field for recipes (2026-02-01)
- ✅ Default shopping list feature (2026-01)
- ✅ Recipe-to-shopping-list with duplicate detection (2026-01)
- ✅ Photo upload for recipes (2026-01)
