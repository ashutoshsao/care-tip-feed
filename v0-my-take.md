
2026-10-11 19:51

status:

tags: #research #dishaai

# v0-my-take


writing these not sure if they are correct

#### problem
dishaai has a care-tip feed that shows the users one thing about an issue the user is facing in  short form vertical videos of about 40 sec, this feed refreshes everyday for every user, we have to design a system so that every user get's the right feed for them, as disha i is a ai healthcare companion.
1. this feed is for passive education of the user for their current health related problems
2. a good feed would help reema understand more about her health and how can see improve it
3. tip engagement quietly reinforces disha what it tells them on caht and call.

#### assumptions
1. thousands of videos
2. 10k active users not sure
3. each video with a title, a hook, a description, and whatever tags or metadata you choose to require (taxonomy is not part of this problem)
4. engagement per user per tip is logged viewed,liked, disliked
#### tip metadata
1. health condition it focuses on
2. metadata about fit for age, sociocultural , lifestyle, goals, food preference
#### the 5 questions
1. ##### filtering
	1. unrelated tips shouldn't be shown to user for eg. tip about period cramps shouldn't be shown to a male user who's goal is to build muscle.
	2. i think there can be 3 types
		1. relevent
		2. good to know, general tips
		3. not relevent tips
2. ##### ranking
	1. today's feed should cater the current Patient Executive Profile (PEP) as it changes with every time disha interacts with the user
	2. related to her current profile and goals
	3. seen once can be repeated once the relevent once and good to know once are exausted for the day or no repeated can also be done.
	4. her liking, skipping doesn't tell much i guess and it depends on mood if they want to watch they would, if they dont want to they would skip, some people like ever short form video some don't like at all
	5. her most active, painful health condition should be catered at priority
	6. on verity vs depth, we sort by priority the most painful, active issue get's more tips.
3. ##### daily refresh
	1. yes today's feed should know
	2. but instead of simply recalculating everything we can just update the tips are are not relevent now for her
4. ##### scale and cost
	1. we can optimize by not running for everyone but only if there is a diff in PEP of the user
	2. llms can be used for not structured decision path's
	3. embeddings for when we want to find similar tip's maybe using tags, metadata, title, decription
	4. plain rules ?? no idea
5. ##### evolution
	1. i would write evals on if disha is helping users or not, with better feed users should be really getting improvements, to atleast passive education taht is relevent to them
	2. no idea here

#### reema's feed by hand
reema's feed = [
{
title: period pain managmenet
description: about how to maange period pain
reason: post painful health issue currently
},
{
title: how to improve hormonal changes for periods
description: gives tips for periods
reason: same
},
{
title: sleep cycle tip
description: tells about why good sleep cycle is imp
reason: good sleep helps improve hormons which imrpves overall health.
},
]

i won't include
{
title: how to gain weight
reason: not reelvent to her goal
}

more not coming to mind
# References

