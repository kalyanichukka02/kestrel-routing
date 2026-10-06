**To:** Ritu Deshpande, Head of D2C Operations  **Cc:** Farhan Sheikh, Meenal Joshi, Tanmay Kulkarni
**Re:** Replacing the routing bot: what I built, what I'd change in the plan

**The decision.** Don't switch the bot off on a "90% match to its labels" test. Those labels are the bot's own routing, and the bot is wrong about a quarter of the time: only **77%** of requests ended up with the team the bot chose (Billing 65%, Repairs 64%, Filters & Consumables 60%). A tool that copies the bot at 90% would copy those mistakes. I built a replacement that learns from **where each request actually ended up**, and I'd run it for two weeks next to the bot before switching.

**The number.** On the latest three months, which the tool never saw before, it chose the right team **84%** of the time (range 82–85%), against **77%** for the bot. On the 84% of requests where it is confident, it is right **95%** of the time, against 86% for the bot. For the other 16% (about 110 a month), the message is too vague to route, for example "please call me about my purifier". The tool says so and suggests one question to ask, instead of guessing. It will not match the bot's labels at 90% (it matches 77%), which is the point: it disagrees where the bot is wrong.

**The rupees.**
- The bot's misroutes cost about **Rs 15 lakh a year** in transfers (Rs 305 each) and repeat contacts (Rs 260 each).
- Estimated saving from the new tool: **at least Rs 1.9 lakh a year**, and up to about Rs 5.3 lakh, from fewer transfers. Add the **Rs 3.2 lakh licence** you stop paying: about **Rs 5.1 lakh a year at least**.
- Farhan's question: the tool uses **no paid AI service**, so the AI charge is **Rs 0 a month** at 700 requests. It runs on any small office server; I have not priced that.
- These are estimates from past transfers, not a measured result. The two-week trial will give the real figure.

**Meenal was right.** Customers who say "I paid for the installation" were sent to Billing 86% of the time; only a quarter belonged there. Purifier breakdowns sent to Consumables were right only 28% of the time. The new tool gets 87% and 65% of those right.

**For headcount.** Don't plan from the bot's queues. By where the work actually ended, Repairs is 23% of requests (the bot says 29%), Billing 12% (bot 15%), Consumables 10% (bot 14%). Installs, Returns and Warranty are each busier than the bot shows (15%, 14%, 13%). These are shares of requests, not hours of work.

**Next week**
1. Run the tool alongside the bot on live requests for two weeks, and compare both to where each request ends. Switch only if it wins.
2. Agree with Meenal who asks the one question on the vague 16%.
3. Ask Tanmay why the export holds 15 months, not 18, and whether the missing three exist.
4. Hold headcount decisions until you've seen the trial.

*The tool, evidence, and every assumption are in the project files; the weak spots are listed in the README.*
