# Evaluation Criteria

> Added for the workshop repo (the codelab references this file but does not include it).
> It mirrors the 7 criteria and weights the Evaluator Agent uses, so the Planner can
> self-check before sending a plan for scoring.

| Criterion               | Weight | What a 100 looks like                                              |
|-------------------------|--------|---------------------------------------------------------------------|
| safety_compliance       | 20%    | Hospitals/fire stations reachable, emergency crossings every ~2 mi  |
| logistics_completeness  | 20%    | Water, chip timing, marshals, start/finish capacity all specified   |
| community_impact        | 15%    | Cheer zones, resident notice, business access, equitable route      |
| financial_viability     | 15%    | Balanced budget, 3+ revenue sources, realistic costs                |
| participant_experience  | 15%    | Landmarks, good surface/elevation, post-race medals/food/recovery   |
| intent_alignment        | 10%    | City, theme, scale and budget match the request                     |
| distance_compliance     | 5%     | Exactly 26.2 mi / 42.195 km                                         |

## Pass rule

A plan **passes** only if the weighted `overall_score >= 85` **and** there are no high-severity findings.

Severity by criterion score: `< 40` high, `< 60` medium, `< 80` low.

## Self-check before sending to the Evaluator

- [ ] Route distance stated as 26.2 miles / 42.195 km
- [ ] Emergency vehicle crossings and hospital detours listed
- [ ] Water stations, medical tents, chip timing, marshals listed
- [ ] Budget with costs **and** revenue (registration, sponsors, merchandise…)
- [ ] Cheer zones / community engagement
- [ ] Landmarks and post-race amenities
- [ ] Timeline: setup, race day waves, teardown

## Capacity rules of thumb

- Start corrals: ~1 m² per runner; use waves above 20,000 runners.
- Finish area: medals, water, food and a family reunion zone sized for peak arrivals (~30% of the field within 45 minutes).
- Budget per runner for a mid-size city marathon is often in the USD 100–250 range; registration rarely covers everything, so sponsorship matters.
