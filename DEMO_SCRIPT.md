# Demo script — 90 seconds

**0:00–0:10 — Hook**
"Bihar ke PHC network me 100s of ASHA/ANM workers hain, aur unka attendance aaj bhi register ya WhatsApp pe track hota hai. Ye hai Swasthya Sathi AI — ek agent jo ye kaam khud sambhalta hai."

**0:10–0:25 — Dashboard**
Show the dashboard: stat cards, attendance bar chart color-coded green/amber/red, worker roster with status badges. "Yaha supervisor ko turant pata chal jaata hai kaun follow-up chahta hai."

**0:25–0:60 — The agent (main feature)**
Type in the chat: *"Sunita Devi ko aaj half-day mark karo aur uska is month ka summary dikhao"*
- Point out the response chains two tool calls automatically (show the ✓ audit chips).
- Then type: *"Is month kaun sabse kam attendance wala hai?"* → agent calls `find_low_attendance_workers` and flags Sunita Devi.
- Mention: "Ye keyword-matching chatbot nahi hai — Gemini ko real Python functions diye gaye hain, aur model khud decide karta hai kaunsa tool kab call karna hai."

**0:60–0:75 — Multilingual**
Type a pure English query: *"Who hasn't marked attendance today?"* → show it answering in English this time, proving language-adaptive behaviour.

**0:75–0:90 — Close**
"Attendance management jo ab ek natural conversation hai — built with Gemini, FastAPI aur React. Swasthya Sathi AI, submitted for Google AI Agent Builder Series 2026."
