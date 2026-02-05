# Privacy Assessment Document Editing Proposal

## Vision

Transform privacy assessments from traditional forms to collaborative, document-like interfaces similar to Confluence or Notion, where content is editable text with commenting, highlighting, and team collaboration features.

## Core Concepts

### 1. Editable Text Blocks (Not Form Fields)

- Replace `Input.TextArea` with editable text blocks
- Text appears as normal content until user clicks to edit
- Clicking text activates edit mode (text becomes input)
- Save/Cancel buttons appear when editing
- Visual indicator (pencil icon, border) shows editable sections

### 2. Text Highlighting & Comments

- Users can select/highlight any text in the document
- Selection triggers a floating toolbar with actions:
  - **Comment** - Add a comment thread on the selection
  - **Request input from team** - Send selection to Slack with context
  - **View evidence** - Open evidence tray for related content
  - **Copy** - Copy selected text
- Comments appear as inline annotations (similar to Google Docs)
- Comment threads show: author, timestamp, replies, resolve status

### 3. Edit Mode

- Click on any section text to enter edit mode
- Text transforms into a textarea/input
- Edit mode shows:
  - Save button (checkmark icon)
  - Cancel button (X icon)
  - Character count (optional)
  - Formatting toolbar (optional, for future)
- Visual feedback: border highlight, background change
- Auto-save draft option (optional)

### 4. Document Structure

- Maintain current collapse/expand structure
- Each section is a document block
- Sections can be:
  - **View mode**: Read-only text with edit button
  - **Edit mode**: Active editing with save/cancel
  - **Comment mode**: Showing comment threads

### 5. Collaboration Features

- **Inline comments**: Click comment icon to view/add comments
- **Team requests**: Highlight text → "Request input" → Opens Slack integration
- **Version history**: Track who edited what and when (future)
- **Suggestions mode**: Suggest edits without directly modifying (future)

## Component Architecture

### EditableTextBlock Component

```tsx
<EditableTextBlock
  value={text}
  onSave={(newValue) => updateSection(newValue)}
  placeholder="Click to edit..."
  readOnly={!canEdit}
  showEditButton={true}
  onComment={(selection) => openCommentThread(selection)}
  onRequestInput={(selection) => requestTeamInput(selection)}
/>
```

### CommentThread Component

```tsx
<CommentThread
  selection={selectedText}
  comments={comments}
  onAddComment={(comment) => addComment(comment)}
  onResolve={() => resolveThread()}
/>
```

### SelectionToolbar Component

```tsx
<SelectionToolbar
  selection={selectedText}
  position={mousePosition}
  onComment={() => openCommentThread()}
  onRequestInput={() => requestTeamInput()}
  onViewEvidence={() => openEvidenceTray()}
/>
```

## Implementation Plan

### Phase 1: Basic Editable Text

1. Replace `Input.TextArea` with editable text blocks
2. Add click-to-edit functionality
3. Add save/cancel buttons
4. Maintain current form state management

### Phase 2: Text Selection & Toolbar

1. Implement text selection detection
2. Create floating toolbar on selection
3. Add basic actions (comment, request input, view evidence)

### Phase 3: Comment System

1. Add comment data model
2. Implement comment threads
3. Add comment UI (inline annotations)
4. Connect to backend (when available)

### Phase 4: Enhanced Collaboration

1. Team input requests with context
2. Comment notifications
3. Edit history/versioning

## UI/UX Considerations

### Visual Design

- **Edit mode**: Subtle border, light background tint, edit icon
- **Comments**: Small icon/indicator, expand to show thread
- **Selection**: Highlight with semi-transparent overlay
- **Toolbar**: Floating, positioned near selection, modern design

### Interactions

- **Click text**: Enter edit mode
- **Select text**: Show toolbar
- **Hover**: Show subtle edit indicator
- **Keyboard**: ESC to cancel, Cmd/Ctrl+S to save

### Responsive

- Toolbar adapts to screen edges
- Comments stack on mobile
- Edit mode full-width on mobile

## Data Model Changes

### Current

```typescript
formValues: {
  projectOverview: string;
  dpiaNeed: string;
  // ...
}
```

### Proposed

```typescript
sections: {
  [sectionKey]: {
    content: string;
    editedBy: string;
    editedAt: string;
    comments: Comment[];
    status: 'draft' | 'published' | 'review';
  }
}

comments: {
  [commentId]: {
    id: string;
    sectionKey: string;
    selection: { start: number; end: number; text: string };
    author: string;
    content: string;
    timestamp: string;
    replies: Comment[];
    resolved: boolean;
  }
}
```

## Migration Strategy

1. Keep existing form structure initially
2. Add editable text components alongside
3. Gradually replace form fields
4. Maintain backward compatibility with form data
