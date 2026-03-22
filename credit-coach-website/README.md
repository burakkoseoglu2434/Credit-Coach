# Credit Coach Website

Bu klasor, Credit Coach icin ayrilmis website uygulama alanidir.

Bu website'in rolu:

- product marketing site
- demo surface
- proof / evidence library
- investor-facing narrative

Teknik yon ve klasor sorumluluklari icin bkz:

- [TECH_ARCHITECTURE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/TECH_ARCHITECTURE.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)

Operasyonel not:

- website buyer-facing demo ve proof yuzeylerini sunar
- ciddi pilot handoff icin minimum runtime ve persistence baseline'i `PILOT_READINESS.md` icinde tanimlidir
- engine-side controlled pilot package icin bkz `credit-coach/docs/PILOT_EXECUTION_GUIDE.md`
- website pilot story, engine-owned `pilot package`, `pilot_guardrails`, `portfolio_validation_summary` ve `product_confidence_snapshot` artefact'lerini tuketmelidir
- auth, CRM ve admin tooling bu baseline'in disindadir
