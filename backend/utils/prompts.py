def create_extract_cute_messages_prompt(chat_chunk: str) -> str:
    """Generates a prompt to extract cute messages from a WhatsApp chat chunk."""
    return f"""Your task is to act as a helpful assistant analyzing a day of WhatsApp messages between two people.
Your goal is to identify message exchanges that are particularly memorable, affectionate, heartwarming, express deep connection, shared joy, or inside jokes.

**Instructions:**
- Please carefully read the following chat messages from a single day.
- Identify any message exchange that are particularly cute, affectionate, heartwarming, express love, deep connection, shared joy, or inside jokes.
- Careful: A chat message can also be a message block. It's when a row doesn't start with date and time.
- Do not include an exchange just because it contains smileys. Focus on exchanges that would make someone genuinely smile or feel emotional when reading them again.
- Once you identify an exchange please remove messages or parts of messages that contain purely logistical information, planning, etc.
- Please include before and after the exchange but only if it helps for context.
- For each identified message, extract the date (DD.MM.YY), time (HH:MM:SS), the sender's name (person), and the message content (quote).
- It is possible that you are reviewing a day without any memorable messages. In this case, return a JSON object with an empty list for `cute_exchanges`.

**GOOD Example 1: Playful Inside Joke Development**
```
[15.01.25, 20:15:23] Emma: I just realized something
[15.01.25, 20:15:45] James: What's up?
[15.01.25, 20:16:12] Emma: You always order the same thing at that cafe
[15.01.25, 20:16:30] James: The oat milk latte?
[15.01.25, 20:16:55] Emma: Yes! Every single time 😂
[15.01.25, 20:17:20] James: It's a good latte!
[15.01.25, 20:17:48] Emma: I'm going to start calling you "Oat Milk James"
[15.01.25, 20:18:15] James: That's actually kind of growing on me
[15.01.25, 20:18:42] Emma: Better than "Boring James"
[15.01.25, 20:19:10] James: Hey! I'm consistent, not boring
[15.01.25, 20:19:35] Emma: Consistently ordering oat milk lattes 😊
[15.01.25, 20:20:05] James: You love it though
[15.01.25, 20:20:30] Emma: I really do ❤️
```

**GOOD Example 2: Vulnerable Moment and Support**
```
[16.01.25, 22:30:15] James: You still up?
[16.01.25, 22:31:05] Emma: Yeah, watching something. Everything okay?
[16.01.25, 22:32:20] James: Just been thinking about what you said earlier today
[16.01.25, 22:33:10] Emma: About the job thing?
[16.01.25, 22:34:25] James: Yeah. I wanted to say thank you for believing in me
[16.01.25, 22:35:15] Emma: Of course I believe in you
[16.01.25, 22:36:40] James: Sometimes I don't believe in myself as much as you do
[16.01.25, 22:37:25] Emma: That's what I'm here for. To remind you how capable you are
[16.01.25, 22:38:45] James: I don't know what I'd do without you
[16.01.25, 22:39:30] Emma: Good thing you don't have to find out 😊
[16.01.25, 22:40:15] James: Lucky me ❤️
```

**GOOD Example 3: Shared Memory and Connection**
```
[17.01.25, 14:20:10] Emma: Look what I found!
[17.01.25, 14:20:12] Emma: <attached: 1 image>
[17.01.25, 14:21:30] James: OMG is that from the hiking trip last summer?
[17.01.25, 14:22:05] Emma: Yes! I was cleaning out my desk and there it was
[17.01.25, 14:22:50] James: We looked so happy
[17.01.25, 14:23:25] Emma: We WERE happy. We still are 😊
[17.01.25, 14:24:10] James: True ❤️
[17.01.25, 14:24:45] Emma: We should plan another trip soon
[17.01.25, 14:25:20] James: I'd love that. Where should we go?
[17.01.25, 14:26:05] Emma: Somewhere with mountains again? You loved the hiking
[17.01.25, 14:27:15] James: Perfect. Let's look at options this weekend
[17.01.25, 14:27:50] Emma: Deal! I'm excited already
```

**GOOD Example 4: Sweet Spontaneous Appreciation**
```
[18.01.25, 08:15:44] James: Random thought
[18.01.25, 08:16:15] Emma: Tell me
[18.01.25, 08:17:20] James: I was walking to work and just felt really grateful
[18.01.25, 08:18:05] Emma: For what?
[18.01.25, 08:19:15] James: For you. For us. For how easy everything feels when we're together
[18.01.25, 08:20:22] Emma: You're going to make me cry at my desk!
[18.01.25, 08:21:10] James: Good tears I hope? 😊
[18.01.25, 08:21:45] Emma: The best tears. I feel the same way about you
[18.01.25, 08:22:30] James: ❤️
```

**BAD Example 1: Too Brief, No Depth**
```
[15.01.25, 15:14:50] James: You excited for tonight?
[15.01.25, 15:15:10] Emma: Yeah!
[15.01.25, 15:15:25] James: Me too 😊
```

**BAD Example 2: Purely Logistical**
```
[16.01.25, 14:12:02] Emma: What time should I pick you up?
[16.01.25, 14:12:35] James: 7pm works
[16.01.25, 14:13:10] Emma: Okay, should I bring anything?
[16.01.25, 14:13:45] James: Just yourself
[16.01.25, 14:14:20] Emma: See you then!
```

**BAD Example 3: Mundane Daily Logistics**
```
[17.01.25, 18:30:15] James: Leaving work now
[17.01.25, 18:30:50] Emma: Okay, I'm starting dinner
[17.01.25, 18:31:35] James: What are we having?
[17.01.25, 18:32:20] Emma: Pasta
[17.01.25, 18:33:05] James: Sounds good
[17.01.25, 18:33:40] Emma: Should be ready when you get home
[17.01.25, 18:34:15] James: Perfect 👍
```

**BAD Example 4: Incomplete Without Context**
```
[18.01.25, 23:45:20] Emma: That was fun
[18.01.25, 23:46:10] James: Yeah, we should do it again
```

Remember: Focus on the sentiment and emotional depth. Only include messages that genuinely capture meaningful moments - vulnerability, joy, playfulness, connection, or inside jokes that define the relationship. Ensure the output is valid JSON matching the specified structure.

**Input Chat Messages for the Day:**
```
{chat_chunk}
```"""


def create_filter_cute_messages_prompt(exchanges: list[list[dict]]) -> str:
    """
    Generates a prompt to filter the top quality cute messages from the first pass.

    Args:
        exchanges: A list of exchanges, where each exchange is a list of MessageDetail dictionaries

    Returns:
        A prompt string instructing the LLM to filter the exchanges based on quality criteria
    """
    return f"""Your task is to act as a helpful assistant reviewing and filtering a set of memorable messages extracted from a chat history.

**Context:**
We are curating the most meaningful and heartfelt messages from a long chat history. We have already done an initial extraction, but now we need to filter down to only the BEST messages.

**Instructions:**
- Review the provided list of message exchanges that were identified in the first pass.
- Apply strict quality filters to select only the MOST meaningful, memorable, and emotionally resonant exchanges.
- Use the following criteria to select the very best exchanges:
  1. Uniqueness of sentiment (avoid repetitive expressions of the same feeling)
  2. Depth of emotion (messages showing profound connection or vulnerability)
  3. Presence of personal details specific to their relationship
  4. Memorable phrasing or language (poetic, creative, or particularly authentic)
  5. Messages that capture particularly significant moments or milestones
- Be VERY selective - aim to keep approximately the top 5-10% of exchanges from those provided.
- The output should match the expected JSON format with a list of cute_exchanges.

Remember: Quality over quantity. Each selected exchange should truly stand out and have special significance. Your goal is to curate a collection that represents the most meaningful moments, not simply a long list of nice messages.

**Input Chat Messages:**
```
{exchanges}
```"""
