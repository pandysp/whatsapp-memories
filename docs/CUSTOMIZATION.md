# Customization Guide

This guide shows you how to use WhatsApp Memory Curator with your own chat history and customize it for your needs.

## Using Your Own WhatsApp Export

### Step 1: Export Your Chat

On WhatsApp:
1. Open the chat you want to export
2. Tap the three dots (⋮) → **More** → **Export chat**
3. Choose **"Without Media"** (faster, smaller file)
4. Save the `.txt` file

The export format looks like:
```
[15.01.25, 08:15:23] Person Name: Message text here
[15.01.25, 08:16:45] Other Person: Reply text
```

### Step 2: Place Your Export File

```bash
# Copy your export to the data_in folder
cp ~/Downloads/WhatsApp-Chat-Export.txt backend/data_in/my_chat.txt

# Or use any path you prefer
cp ~/Downloads/export.txt ~/my-whatsapp-export.txt
```

**Important:** Your chat file should NOT be committed to git. The `.gitignore` is configured to ignore `backend/data_in/*.txt` except `demo_chat.txt`.

### Step 3: Process Your Data

```bash
# Using file in data_in folder
make start ARGS="--file_in=backend/data_in/my_chat.txt --log_level=INFO"

# Or using absolute path
make start ARGS="--file_in=/path/to/your/export.txt --log_level=INFO"
```

**Expected output:**
```
Starting cute message extraction script...
Created 1,800 daily chunks.
Running 1,800 extraction LLM tasks...
Processing completed in 18.3 minutes
Extracted 423 exchanges from 1,800 daily chunks
```

### Step 4: Browse Results

```bash
# Start the backend
make run-backend

# In another terminal, start frontend
cd frontend && npm run dev

# Visit http://localhost:3000
```

## Customizing the Prompt

The extraction quality depends heavily on the prompt in `backend/utils/prompts.py`.

### Understanding the Prompt Structure

```python
def create_extract_cute_messages_prompt(chat_chunk: str) -> str:
    return f"""
    [1] Task description & context
    [2] Instructions
    [3] Few-shot examples (GOOD)
    [4] Few-shot examples (BAD)
    [5] Input data: {chat_chunk}
    """
```

### What You Can Customize

**1. Task Context:**
```python
# Current (generic):
"Your task is to analyze WhatsApp messages between two people."

# Personalized:
"Your task is to analyze WhatsApp messages between John and Sarah."
```

**2. Extraction Criteria:**
```python
# Current:
"Focus on exchanges that are memorable, affectionate, heartwarming..."

# Add your own:
"Focus on exchanges about travel, food adventures, or shared hobbies..."
```

**3. Few-Shot Examples** (most impactful!):

The model learns your definition of "memorable" from examples. Replace the generic Emma/James examples with your own.

## Adding Your Own Few-Shot Examples

Few-shot examples are **the secret sauce**. They teach the LLM what "memorable" means for your specific relationship.

### Finding Good Examples

1. **Manually review** your export file
2. **Identify 3-4 exchanges** that represent what you want:
   - Playful banter / inside jokes
   - Vulnerable / emotional moments
   - Shared memories / meaningful conversations
3. **Identify 3-4 exchanges** to exclude:
   - Pure logistics ("What time?" "7pm")
   - Brief confirmations ("Ok" "Cool")
   - Mundane planning

### Example Structure

```python
**GOOD Example 1: Playful Inside Joke**
```
[15.01.25, 20:15:23] You: I just realized something
[15.01.25, 20:15:45] Partner: What's up?
[15.01.25, 20:16:12] You: You always order the same thing
[15.01.25, 20:16:30] Partner: It's a good choice!
[15.01.25, 20:17:48] You: I'm calling you "Predictable Partner" now
```

**BAD Example 1: Pure Logistics**
```
[16.01.25, 11:30:48] You: Did you see the email?
[16.01.25, 11:31:20] Partner: Yeah
[16.01.25, 11:31:55] You: Want to work on it together?
```

### Where to Add Examples

Open `backend/utils/prompts.py` and find the few-shot examples section (starting around line 16). Replace the Emma/James examples with your own.

**Important:** Keep the same structure:
- Date format: `[DD.MM.YY, HH:MM:SS]`
- Person names: Consistent throughout
- Balance: 3-4 GOOD + 3-4 BAD examples

## Tuning Extraction Quality

### Too Many Extractions (Over-Inclusive)

**Symptoms:** Getting mundane conversations, logistics, brief exchanges.

**Solutions:**
1. Add more BAD examples showing what to exclude
2. Make GOOD examples more extreme (only the BEST stuff)
3. Adjust instructions to be more selective

**But consider:** Over-extraction is often better! Use the UI's delete button to curate. False positives are easy to fix, false negatives are lost forever.

### Too Few Extractions (Under-Inclusive)

**Symptoms:** Missing exchanges you expected to see.

**Solutions:**
1. Check your few-shot examples—are they representative?
2. Make BAD examples less extreme
3. Adjust instructions to be more permissive
4. Verify your export file format matches expected pattern

### Borderline Cases

The model will make judgment calls on borderline exchanges. For example:
- Work collaboration that shows support
- Light humor that's not deeply meaningful
- Planning that includes affection

**This is normal.** Different people have different definitions of "memorable." Use the UI to delete what doesn't resonate with you.

## Understanding the Tradeoffs

### Over-Extraction vs. Under-Extraction

**Over-Extraction (extracting too much):**
- ✅ Captures borderline meaningful moments
- ✅ Easy to fix with delete button
- ❌ Requires manual curation
- ❌ Slightly higher costs

**Under-Extraction (extracting too little):**
- ✅ Only the best stuff
- ❌ Might miss meaningful exchanges
- ❌ No way to recover missed moments
- ❌ Harder to debug

**Recommendation:** Bias toward over-extraction. The delete button exists for a reason.

## Advanced Customization

### Changing the Model

Default: `gemini-2.5-flash-preview-05-20`

To use a different model, edit `backend/process_whatsapp_messages.py`:

```python
# Line ~80
model_name="gemini-2.5-flash-preview-05-20"  # Change this

# Options:
# - "gemini-2.0-flash-exp" (newer, might be better)
# - "gemini-2.5-pro-preview-03-25" (more expensive, higher quality)
```

### Adjusting Temperature

Default: `temperature=0.0` (deterministic)

To make extraction more creative/random:
```python
# Line ~82
temperature=0.0  # Change to 0.3 or 0.5
```

**Not recommended** for this use case. You want consistent, reproducible results.

### Batch Size for Rate Limiting

Default: 5 concurrent requests

To speed up (if your API limits allow):
```python
# backend/utils/llm_utils.py, line 43
sema = asyncio.Semaphore(5)  # Change to 10 or 20
```

**Warning:** Higher concurrency = faster but might hit rate limits.

## Using the UI to Curate

After extraction, the UI provides curation features:

### Deleting Messages

1. Click on a message to select it
2. Select multiple messages if needed
3. Click the trash icon in the header
4. Confirm deletion

**Use case:** Remove individual messages that aren't meaningful, keeping the rest of the exchange.

### Deleting Exchanges

1. Click the three dots (⋮) in the chat header
2. Select "Delete Chat"
3. Confirm

**Use case:** Remove entire exchanges that aren't meaningful.

### Merging Exchanges

1. Click the three dots (⋮) in the sidebar header
2. Select "Start Merge Mode"
3. Click on 2+ exchanges to select them
4. Click "Merge (N)" button
5. Confirm

**Use case:** The LLM split what should be one conversation into multiple exchanges.

**Note:** You can only merge exchanges from the same source file (same WhatsApp export).

## Iterating and Improving

**Workflow:**

1. **Process** your data with default settings
2. **Review** results in UI
3. **Identify patterns** in what was wrongly included/excluded
4. **Update** few-shot examples or instructions
5. **Clear cache** and re-process
6. **Repeat** until satisfied

**Clearing cache:**
```bash
make clear-cache
# Or manually: rm backend_cache.db
```

**Re-processing:**
```bash
make start ARGS="--file_in=backend/data_in/my_chat.txt --log_level=INFO"
```

## FAQ

**Q: How long should my few-shot examples be?**
A: 3-10 messages per example. Long enough to show context, short enough to be clear.

**Q: Can I use examples from a different relationship?**
A: The model learns the PATTERN, not the specific content. Generic examples (like the Emma/James ones) work reasonably well, but examples from your actual relationship will be more accurate.

**Q: How many few-shot examples do I need?**
A: 3-4 GOOD + 3-4 BAD is the sweet spot. More doesn't necessarily help.

**Q: What if the extraction quality is terrible?**
A: Check these in order:
1. Is your export file format correct? (should match `[DD.MM.YY, HH:MM:SS] Name: Message`)
2. Do your few-shot examples accurately represent what you want?
3. Are your instructions clear?
4. Try with a different model (Gemini Pro instead of Flash)

**Q: Can I process multiple chat exports?**
A: Yes! Process each export separately. The UI will show all exchanges with a `sourceFile` indicator. You can merge exchanges from different exports if needed.

**Q: How do I know if extraction quality is good?**
A: Spot-check random exchanges. If ~85% are meaningful to you, that's excellent. Use the delete button for the rest.

## Getting Help

If you're stuck:
1. Check the [ARCHITECTURE.md](ARCHITECTURE.md) for system details
2. Check the [PRIVACY.md](PRIVACY.md) for data handling
3. Open an issue on GitHub with:
   - Your prompt modifications (without personal content)
   - Sample extraction results
   - What you expected vs. what you got
