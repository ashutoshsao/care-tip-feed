# Picking the right care tips, every day ⏱ 1 min

- **Problem:** thousands of health videos, 500k+ users, one daily feed each — in a product where a wrong tip can hurt
- **Answer:** an LLM reads the profile only when it changes; the daily feed is plain code — safety filter first, then ranking by severity
- **Result:** 0 unsafe tips vs ~19 for random or embedding-only feeds, at 82% relevance

> Say: "I treated this as a safety problem first and a ranking problem second."
