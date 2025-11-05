# Privacy & Data Handling

This guide explains how your data is handled and best practices for protecting your privacy.

## Where Your Data Goes

### What Stays Local

✅ **Your WhatsApp export file** - Never leaves your machine
✅ **Extracted exchanges** - Stored in SQLite database locally
✅ **Cache data** - Stored in SQLite database locally
✅ **All UI interactions** - Frontend and backend run on your machine

### What Leaves Your Machine

⚠️ **API calls to Gemini** - Your messages are sent to Google's servers for processing

**Specifically:**
- Daily chunks of messages (grouped by day)
- Sent via HTTPS to Gemini API
- Processed by Google's LLM
- Responses cached locally
- Google may log requests per their privacy policy

**What Google sees:**
- The message content (date, time, person, text)
- Your API key
- Metadata (timestamps, request IDs)

**What Google does NOT see:**
- Who you are (unless your API key is linked to your account)
- Your name, email, or personal info (unless in messages)
- The broader context beyond each daily chunk

## Privacy Best Practices

### 1. Protect Your API Key

Your `.env` file contains your Gemini API key:

```bash
GEMINI_API_KEY=your_key_here
```

**DO:**
- ✅ Keep `.env` file local (already in `.gitignore`)
- ✅ Use environment variables in production
- ✅ Regenerate keys if accidentally exposed

**DON'T:**
- ❌ Commit `.env` to git
- ❌ Share your API key publicly
- ❌ Use the same key for multiple projects (optional but recommended)

### 2. Don't Commit Personal Data

The `.gitignore` is configured to protect:

```gitignore
# Chat exports (your personal conversations)
backend/data_in/*.txt
!backend/data_in/demo_chat.txt  # Exception: demo is safe

# Database (contains extracted exchanges)
*.db
*.sqlite3

# Personal few-shot examples
backend/utils/ORIGINAL_FEW_SHOT_EXAMPLES.md
```

**Before committing, always verify:**
```bash
git status

# Should NOT see:
# - .env
# - backend_cache.db
# - backend/data_in/_chat.txt (or your export file)
# - backend/utils/ORIGINAL_FEW_SHOT_EXAMPLES.md
```

### 3. Sanitizing Data for Demos

If you want to demo the project publicly (e.g., for a talk), create sanitized data:

**Option A: Use the provided demo data**
```bash
make start ARGS="--file_in=backend/data_in/demo_chat.txt"
```

**Option B: Create your own demo data**

1. Create a fictional chat with made-up names:
```
[15.01.25, 08:15:23] Alice: Good morning!
[15.01.25, 08:16:45] Bob: Hey! How are you?
```

2. Replace real names with fictional ones:
```bash
# Use sed or your editor to find/replace
sed 's/YourName/Alice/g' real_chat.txt > demo_chat.txt
sed -i 's/PartnerName/Bob/g' demo_chat.txt
```

3. Remove sensitive content (addresses, phone numbers, etc.)

### 4. Understanding LLM Provider Access

**Gemini's data usage:**
- Check [Google's Privacy Policy](https://policies.google.com/privacy)
- Gemini API requests are logged by Google
- They may use data to improve services (check current terms)
- Enterprise accounts have different data handling

**If privacy is critical:**
- Use a local LLM (Ollama, llama.cpp)
- Modify `backend/utils/llm_utils.py` to use local endpoint
- Trade-off: Slower, lower quality, but fully private

## Data Retention

### Local Storage

**What's stored:**
- `backend_cache.db` - SQLite database with:
  - Raw LLM responses (JSON)
  - Extracted exchanges
  - Individual messages
  - Cache keys and metadata

**How long:**
- Forever, until you delete it manually

**How to delete:**
```bash
make clear-cache
# Or manually:
rm backend_cache.db
```

### LLM Provider (Google/Gemini)

**What they store:**
- API request logs
- Usage metrics
- Potentially message content (for service improvement)

**How long:**
- Per their privacy policy (varies)
- May be 30 days, 90 days, or longer

**How to delete:**
- Contact Google support
- Check their data deletion requests process
- Deleting your Google account may remove data

## Compliance Considerations

### GDPR (EU)

If you're processing someone else's WhatsApp messages:
- ✅ Get their consent first
- ✅ Inform them data is sent to Google
- ✅ Allow them to request deletion
- ✅ Don't share extracted data publicly without consent

### Personal Use

If processing your own messages:
- ✅ You can freely process your own data
- ⚠️ Partner's messages are their data too - consider getting consent
- ⚠️ Don't publicly share without consent from all participants

## Security Best Practices

### 1. Keep Dependencies Updated

```bash
# Backend
uv sync --upgrade

# Frontend
cd frontend && npm update
```

### 2. Review Permissions

The app doesn't need:
- ❌ Internet access (except for LLM API calls)
- ❌ Camera/microphone
- ❌ Location services
- ❌ Contact list access

If you see requests for these, something is wrong.

### 3. Run on Trusted Networks

When processing personal data:
- ✅ Use your home/private network
- ⚠️ Be cautious on public WiFi (API calls are HTTPS but still visible metadata)
- ✅ Consider using a VPN for extra privacy

### 4. Secure Your Machine

- ✅ Use disk encryption (FileVault on Mac, BitLocker on Windows)
- ✅ Use a strong password/lock screen
- ✅ Keep OS and security updates current

## Incident Response

**If you accidentally commit sensitive data:**

1. **Don't panic** - It can be fixed

2. **If repo is private:**
```bash
# Remove from latest commit
git reset HEAD~1
git add .
git commit -m "Fix: removed sensitive data"
git push --force
```

3. **If repo is public and pushed:**
```bash
# Remove from git history
pip install git-filter-repo
git filter-repo --path backend/data_in/_chat.txt --invert-paths
git push origin --force --all
```

4. **Rotate any exposed keys:**
- Generate new Gemini API key
- Update `.env`
- Delete old key from Google Cloud Console

5. **Consider the impact:**
- Who has access to the repo?
- Was it forked/cloned?
- Is data sensitive enough to warrant further action?

**If API key is exposed:**
1. Immediately revoke it in [Google AI Studio](https://aistudio.google.com/apikey)
2. Generate a new key
3. Update your `.env` file
4. No lasting damage if caught quickly

## Privacy FAQs

**Q: Can I use this for someone else's chat history?**
A: Technically yes, but ethically and legally you should get their consent first.

**Q: What if my messages contain sensitive info (SSN, passwords, etc.)?**
A: DON'T process them! Or manually redact those sections from the export first.

**Q: Can Google/Gemini see who I'm chatting with?**
A: They see the names in the messages ("Person Name: Message"). Consider using pseudonyms in your few-shot examples.

**Q: Is this HIPAA/FERPA/etc. compliant?**
A: No. Don't use this for regulated data (medical, educational records, etc.) unless you have an enterprise agreement with Google covering compliance.

**Q: Can I process work chats?**
A: Check your company's data policy first. Work messages may be company property and subject to retention policies.

**Q: What if I want complete privacy?**
A: Use a local LLM instead of Gemini:
- Install [Ollama](https://ollama.ai/)
- Run a model like `llama3`
- Modify `backend/utils/llm_utils.py` to point to local endpoint
- Trade-off: Slower and lower quality

**Q: How do I verify no data is leaking?**
A: Monitor network traffic with Wireshark or Little Snitch. You should only see HTTPS requests to:
- `generativelanguage.googleapis.com` (Gemini API)
- `localhost:3000` (frontend)
- `localhost:8000` (backend API)

## Responsible Use

### DO:
- ✅ Process your own data
- ✅ Get consent from chat participants
- ✅ Secure your export files and database
- ✅ Use for personal memory curation

### DON'T:
- ❌ Process others' data without consent
- ❌ Share extracted conversations publicly without permission
- ❌ Use for surveillance or monitoring
- ❌ Process regulated/confidential data

## Getting Help

If you have privacy concerns:
- Open an issue on GitHub (without revealing sensitive details)
- Review Google's [Generative AI Terms](https://ai.google.dev/terms)
- Consult a privacy professional for specific compliance questions

---

**Remember:** This tool processes your personal conversations. Use it responsibly and protect your privacy!
