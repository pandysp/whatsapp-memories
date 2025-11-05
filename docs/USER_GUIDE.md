# User Guide

> How to use WhatsApp Memories to browse, curate, and manage your memorable conversations

## Accessing the App

**Production URL:** https://whatsapp-memories.vercel.app

**Supported Devices:**
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome, Firefox)
- Tablets

**No Login Required:** The app displays pre-processed memories from your WhatsApp exports.

---

## Interface Overview

The app uses a familiar WhatsApp-like interface with two main areas:

### Desktop View

```
┌─────────────────────────────────────────────┐
│  ┌──────────┐  ┌────────────────────────┐  │
│  │          │  │                        │  │
│  │ Exchange │  │   Message              │  │
│  │ List     │  │   View                 │  │
│  │ (Sidebar)│  │   (Chat Area)          │  │
│  │          │  │                        │  │
│  └──────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Left Sidebar (1/3 width):**
- List of all message exchanges
- Shows first message preview
- Timestamp
- Avatar with initials

**Right Area (2/3 width):**
- Full conversation when exchange is selected
- Message bubbles (left/right based on sender)
- Timestamps on each message
- Action buttons (merge, delete)

### Mobile View

On mobile, the interface switches between two full-screen views:

1. **List View** - Shows all exchanges (default)
2. **Chat View** - Shows selected conversation

Tap an exchange to switch to chat view. Use back button to return to list.

---

## Browsing Exchanges

### Viewing the List

**Exchange List Items Show:**
- Person name (or "Unknown Contact" if no name)
- First message preview (truncated)
- Date/time of first message
- Avatar with person's initials

**Sorting:**
- Exchanges are sorted chronologically by first message date
- Newest conversations appear at the top (ascending order)

### Infinite Scroll

As you scroll down the list, more exchanges load automatically:

- Loads 20 exchanges at a time
- Scroll triggers load when you're near the bottom
- No "Load More" button needed
- Total count shown at bottom of list

**Loading States:**
- Spinner appears while fetching more exchanges
- "No more exchanges to load" when you've reached the end

### Selecting an Exchange

**Desktop:**
- Click any exchange in the sidebar
- Chat area updates to show full conversation
- Selected exchange has light gray background

**Mobile:**
- Tap any exchange in the list
- View switches to full-screen chat
- Use browser back button to return to list

---

## Reading Conversations

### Message Display

Each message shows:
- **Sender name** (small text above bubble)
- **Message content** (main text in bubble)
- **Timestamp** (bottom-right of bubble)

**Message Bubble Colors:**
- First person in exchange: Left side, green bubbles
- Second person: Right side, white bubbles
- Color assignment is automatic based on first message

### Message Formatting

- Line breaks are preserved from original WhatsApp messages
- Emojis display natively
- Long messages wrap naturally in bubbles

### Scrolling Through Messages

- Scroll within the chat area to see full conversation
- On mobile, swipe up/down to scroll messages
- Initial view starts at top of conversation

---

## Curating Your Memories

### Why Curate?

The LLM extraction process intentionally over-extracts to avoid missing meaningful moments. You'll want to:

- Remove exchanges that aren't as meaningful on second review
- Merge related conversations that were split across days
- Keep only the truly special moments

**Recommended Workflow:**
1. Browse all exchanges first
2. Delete obvious non-meaningful ones
3. Merge related conversations
4. Do a final pass to refine

---

## Deleting Messages

### Individual Message Delete

**Steps:**
1. Click **"Select messages to delete"** button (top-right)
2. Click on messages you want to remove
3. Selected messages get a blue checkbox
4. Click **"Delete Selected"** button
5. Confirm in popup dialog

**Notes:**
- You can select multiple messages before deleting
- Changes take effect immediately
- No undo feature - be careful!
- If you delete all messages in an exchange, the exchange remains as an empty placeholder

### Deleting Entire Exchanges

Currently, you must:
1. Select all messages individually, or
2. Use the merge feature to consolidate, then delete unwanted merged result

**Tip:** If an exchange has only 1-2 messages, it's faster to delete them individually than merge.

---

## Merging Exchanges

### When to Merge

Merge exchanges that are:
- Same conversation split across different days
- Related moments that should be viewed together
- Chronologically close and contextually connected

**Example Merge Scenarios:**
- "Planning vacation" (Day 1) + "Vacation excitement" (Day 2)
- "Morning chat" (8 AM) + "Evening continuation" (8 PM same day)

### How to Merge

**Steps:**
1. Click **"Merge exchanges"** button (top-right)
2. Interface switches to merge mode
3. **Important:** Only exchanges from the same source file can be merged
4. Click/tap multiple exchanges to select them (blue checkbox appears)
5. Click **"Merge Selected"** button
6. Confirm in popup dialog

**What Happens:**
- All messages from selected exchanges combine into one
- Messages are reordered chronologically (by date/time)
- The exchange with the smallest ID becomes the target
- Other exchanges disappear after merge
- Changes take effect immediately

### Merge Constraints

**Source File Restriction:**
- Only exchanges from the same WhatsApp export file can be merged
- This preserves context and conversation continuity
- Exchanges from different files appear grayed out when others are selected

**Why This Matters:**
- Different source files might be different chats or time periods
- Mixing them could create confusing narratives
- The app enforces this constraint automatically

### After Merging

- The merged exchange appears in the list with updated message count
- Messages are sorted chronologically within the exchange
- First message in the merged result determines list position
- Select the merged exchange to review the combined conversation

---

## Mobile-Specific Tips

### Navigation

**Switching Views:**
- **List → Chat**: Tap any exchange
- **Chat → List**: Use browser back button (←)

**Scrolling:**
- Swipe up/down to scroll through lists and messages
- Momentum scrolling works naturally

### Selection Mode

**Selecting Messages:**
- Tap messages to select (don't long-press)
- Tap again to deselect
- Selection mode stays active until you exit

**Selecting for Merge:**
- Tap exchanges to select in merge mode
- Blue checkboxes indicate selection
- Compatible exchanges highlighted, incompatible grayed out

### Action Buttons

All action buttons are optimized for touch:
- Large tap targets
- Clear visual feedback
- Confirmation dialogs prevent accidents

---

## Best Practices

### Efficient Curation

**First Pass:**
1. Scroll through entire list quickly
2. Get a sense of what's there
3. Note obvious deletes or merges

**Second Pass:**
1. Read exchanges more carefully
2. Delete non-meaningful ones
3. Mark mentally which ones to merge

**Third Pass:**
1. Execute merges for related conversations
2. Delete messages within exchanges that don't fit
3. Final review of remaining curated set

### Organizing Workflow

**By Timeline:**
- Work chronologically (top to bottom)
- Easier to spot related conversations to merge
- Maintains narrative flow

**By Theme:**
- Search mentally for themes (travel, inside jokes, deep talks)
- Merge related themed exchanges
- Create cohesive memory collections

**By Deletion:**
- First pass: Delete obvious non-keepers
- Reduces list size quickly
- Makes merge decisions easier

### Avoiding Mistakes

**Before Deleting:**
- Read the full exchange one more time
- Ask: "Would I want to revisit this in 5 years?"
- Remember: No undo!

**Before Merging:**
- Verify exchanges are actually related
- Check dates - should be close together
- Preview both exchanges before committing

---

## Common Scenarios

### Scenario: Too Many Exchanges

**Problem:** Thousands of exchanges, overwhelming to browse

**Solution:**
1. Use pagination - don't try to view all at once
2. Start from most recent (top) and work backwards
3. Delete aggressively on first pass
4. Merge liberally to consolidate
5. Multiple curation sessions are okay

### Scenario: Split Conversations

**Problem:** One conversation split across 3-5 exchanges

**Solution:**
1. Enable merge mode
2. Select all related exchanges
3. Merge into one
4. Review merged result
5. Delete any filler messages within merged exchange

### Scenario: Accidental Selection

**Problem:** Selected wrong message/exchange

**Solution:**
- **In message select mode:** Tap message again to deselect
- **In merge mode:** Tap exchange again to deselect
- **After merge/delete:** No undo - restore from backup (admin only)

### Scenario: Empty Exchange After Delete

**Problem:** Deleted all messages, exchange still shows

**Solution:**
- This is expected behavior
- Empty exchanges remain as placeholders
- Admin can clean up via database operations
- Doesn't affect functionality

### Scenario: Mobile Keyboard Covers Buttons

**Problem:** Action buttons hidden when keyboard appears

**Solution:**
- Dismiss keyboard (tap outside text input or Done button)
- Rotate to landscape if needed
- Buttons reappear when keyboard closes

---

## Understanding the Data

### What Am I Looking At?

These are **AI-extracted** conversations from your WhatsApp chats:

- Processed through Gemini 2.5 Flash LLM
- Selected based on criteria for "memorable" moments
- Intentionally over-extracted (false positives better than false negatives)
- Your job as curator is to refine the selection

### Message Metadata

Each message includes:
- **Date**: DD.MM.YY format (e.g., 15.03.24)
- **Time**: HH:MM:SS or HH:MM format (e.g., 14:35:22)
- **Person**: Sender name from WhatsApp export
- **Quote**: The actual message text

**Note:** If metadata is missing (null/empty), fields may show as blank.

### Source File Context

Each exchange has a `sourceFile` field:
- Usually: `filename::function_name` format
- Indicates which WhatsApp export it came from
- Relevant for merge compatibility
- Visible in debugging but not shown in main UI

---

## Performance Tips

### Faster Loading

**Initial Load:**
- First 20 exchanges load quickly (<1 second)
- Subsequent pages load as you scroll
- Backend caches data for faster response

**Smooth Scrolling:**
- Infinite scroll triggers before you reach bottom
- Preloads next page while you're reading
- Minimizes wait time

**Mobile Performance:**
- App is optimized for mobile browsers
- Images lazy-load (if any)
- Minimal JavaScript for fast rendering

### Data Refresh

**When Data Updates:**
- Frontend automatically fetches latest data
- No manual refresh needed
- After delete/merge, list updates immediately

**If Data Seems Stale:**
- Refresh browser page (F5 / ⌘R)
- Check network tab for API errors
- Verify backend is healthy

---

## Keyboard Shortcuts

Currently, the app doesn't have keyboard shortcuts, but uses standard browser controls:

- **Scroll**: Arrow keys, Page Up/Down
- **Back**: Browser back button or Backspace
- **Refresh**: F5 or Cmd/Ctrl+R
- **Zoom**: Cmd/Ctrl + Plus/Minus

---

## Privacy & Security

### What Data Is Stored?

- **Production**: Only the exchanges you've curated
- **No tracking**: No analytics or user tracking
- **No login**: No account or personal data collected

### Who Can See My Data?

- **Only you** (or whoever has the deployment URL)
- Deploy on private infrastructure if needed
- Can add authentication layer (requires code changes)

### Data Retention

- Data persists until you explicitly delete it
- Admin can clear entire database
- Backups (if configured) retain historical data

---

## Troubleshooting

For technical issues, see [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Common User Issues:**

**Can't see any exchanges:**
- Verify production URL is correct
- Check that data has been loaded (admin task)
- Try refreshing browser page

**Merge button grayed out:**
- Select at least 2 exchanges first
- Ensure selected exchanges are from same source file
- Incompatible exchanges can't be merged

**Mobile view not working:**
- Try resizing browser window
- Responsive breakpoint is 768px width
- Clear browser cache and reload

**Changes not saving:**
- Check browser console for errors (F12)
- Verify backend health endpoint
- Network issues may prevent saves

---

## Getting Help

**For Questions:**
- Consult this guide first
- Check [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub repository

**For Bug Reports:**
Include:
- What you were trying to do
- What happened instead
- Browser/device information
- Screenshot if helpful

---

## Appendix: UI Element Reference

### Button Locations

**Top-Right Actions (Desktop/Mobile):**
- "Select messages to delete" - Enables message selection mode
- "Delete Selected" - Appears after selecting messages
- "Merge exchanges" - Enables exchange merge mode
- "Merge Selected" - Appears after selecting 2+ compatible exchanges
- "Cancel" - Exits any selection mode

### Visual Indicators

**Selection States:**
- Blue checkbox - Item is selected
- Gray checkbox - Item is not selected
- Grayed out item - Not compatible for current action
- Blue background - Item is highlighted/active

**Loading States:**
- Spinner icon - Data is loading
- "Loading more..." text - Pagination in progress
- Empty state - No data available

### Color Coding

**Message Bubbles:**
- Green (left side) - First person in exchange
- White (right side) - Second person in exchange

**Backgrounds:**
- Light gray (`#f0f2f5`) - Selected exchange in sidebar
- White - Unselected exchanges
- Beige (`#e5ddd5`) - Chat area background (WhatsApp style)

---

**Ready to curate your memories?** Visit https://whatsapp-memories.vercel.app and start browsing!
