# Refresh demo (prototype step 10)

```
## 7 simulated days on profile v1 (top 5 each day)
day 0: pinn:Chest Pain? Get Checked Now | prio:Why Do We Get Period Cramps? | prio:Ease Cramps With a Warm Comp | pres:Set a Strict Daytime Sleep B | rota:How stress delays your perio
day 1: pinn:Chest Pain? Get Checked Now | prio:Soothing Ginger Turmeric Dri | prio:The Science Behind Period Pa | pres:How to Build a Sleep Routine | rota:Set a Caffeine Cutoff Time
   ↳ dislikes 'Soothing Ginger Turmeric Drink'
day 2: pinn:Chest Pain? Get Checked Now | prio:Gentle Movement for Period P | prio:Relieve bloating with ginger | pres:Finding Your Pelvic Floor Mu | rota:Preparing for an Iron Blood 
day 3: pinn:Chest Pain? Get Checked Now | prio:Eat Magnesium for Better Per | prio:Myth: Painkillers Ruin Your  | pres:How To Do Kegel Exercises | rota:4 Steps to Calm Down Quickly
day 4: pinn:Chest Pain? Get Checked Now | prio:Normal Cramps vs Dysmenorrhe | prio:Myth: Severe Period Pain is  | pres:Wear Sunglasses on Your Comm | rota:Relieve Back Pain With Cat-C
day 5: pinn:Chest Pain? Get Checked Now | prio:Drink Water to Stop Cramps | prio:Ease Cramps With a Warm Comp | pres:Mastering the Anchor Sleep S | rota:Elevate Legs for Swelling Re
day 6: pinn:Chest Pain? Get Checked Now | prio:Ease Cramps With a Warm Comp | prio:Relieve bloating with ginger | pres:Soothe Back Pain with Heat | rota:Why Screens Keep You Awake
disliked video shown again after day 1: False

## Profile update v1 → v2 (diff of structured profiles, D11)
red flags: {'suspected_cardiac': 'active'} → {'suspected_cardiac': 'cleared'}
tests:     {'thyroid_panel': 'scheduled', 'iron_panel': 'scheduled', 'vitamin_d': 'scheduled'} → {'vitamin_d': 'results_received', 'iron_panel': 'results_received', 'thyroid_panel': 'results_received'}
newly confirmed: ['iron_deficiency', 'vitamin_d_deficiency'];  restrictions: ['no_high_exertion']
old-vs-new code checks (D7): no flags

left the feed:   Chest Pain? Get Checked Now; Trick Your Brain With Blackout Curtains; Why Do Your Legs Swell?
joined the feed: Diet for Iron-Deficiency Anaemia; Why Low Iron Causes Fatigue; Getting Vitamin D From Sunlight
  Chest Pain? Get Checked Now              v1: eligible                                   v2: eligible
  Diet for Iron-Deficiency Anaemia         v1: diagnosis lock: iron_deficiency not confirmed v2: eligible
  Preparing for an Iron Blood Test         v1: eligible                                   v2: test prep for iron_panel, not pending
  Burn Fat Fast With HIIT                  v1: contraindicated: ['suspected_cardiac']     v2: clinician restriction: avoid strenuous exercise

## Fast path: Arjun reports new chest pain at 2 PM (feed already built this morning)
removed from today's feed immediately: Knee-Friendly Chair Squats; The Perfect Gym Warmup
pinned: Chest Pain? Get Checked Now
```
