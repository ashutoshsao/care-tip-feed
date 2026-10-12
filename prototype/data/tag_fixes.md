# Tag fixes after generation

Generator: google/gemini-3.1-pro-preview. Errors found on review — evidence for D3 (tags need clinical review).

**22 fixes across 110 tips.** universally_safe narrowed to 13 tips: pure education or trivially safe habits only (no diet change, supplements, fasting, condition-specific content, or expired content) — D18.

- `why_period_bloating`: universally_safe → false
- `myth_28_day_cycle`: universally_safe → false
- `stress_delays_period`: universally_safe → false
- `myth_skipping_periods_harmful`: universally_safe → false
- `shift_fixed_sleep_block`: universally_safe → false
- `shift_catchup_sleep_myth`: universally_safe → false
- `shift_morning_sunglasses`: universally_safe → false
- `shift_caffeine_cutoff`: universally_safe → false
- `shift_night_meals`: universally_safe → false
- `shift_off_day_transition`: universally_safe → false
- `shift_work_sleep_tips`: requires_confirmed_diagnosis `shift_work_sleep` → null (general shift-sleep advice doesn't assume a diagnosis)
- `photo_log_meals`: universally_safe → false
- `thyroid_panel_prep`: universally_safe → false
- `iron_panel_prep`: universally_safe → false
- `vit_d_test_prep`: universally_safe → false
- `vit_d_sunlight_exposure`: universally_safe → false
- `iron_deficiency_fatigue_link`: universally_safe → false
- `myth_hypothyroidism_weight`: universally_safe → false
- `understanding_tsh_levels`: universally_safe → false
- `burning_feet_relief`: universally_safe → false
- `hair_fall_basics`: universally_safe → false
- `mouth_ulcer_relief`: universally_safe → false

## Round 2 — gaps found by the 3-provider judge panel

Note: round 1 removed the shift-work lock from `shift_work_sleep_tips`; the judges showed shift tips do assume night shifts, so all shift-specific tips now carry it — round 1's fix was wrong.

- `pcos_low_gi_plate`: requires_confirmed_diagnosis → pcos (PCOS-specific advice)
- `pcos_post_meal_walk`: requires_confirmed_diagnosis → pcos (PCOS-specific advice)
- `shift_fixed_sleep_block`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_blackout_curtains`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_catchup_sleep_myth`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_morning_sunglasses`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_caffeine_cutoff`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_night_meals`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_room_temperature`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_off_day_transition`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `shift_work_sleep_tips`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `night_shift_eating`: requires shift_work_sleep (assumes night shifts); universally_safe → false
- `thyroid_panel_prep`: prep_for_test → thyroid_panel (shown only while that test is pending)
- `iron_panel_prep`: prep_for_test → iron_panel (shown only while that test is pending)
- `vit_d_test_prep`: prep_for_test → vitamin_d (shown only while that test is pending)
- `how_to_prepare_gtt`: prep_for_test → glucose_tolerance (shown only while that test is pending)
