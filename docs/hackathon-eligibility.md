# Hackathon requirements and evidence status

This records the requirements in the three participant-brief images supplied locally for the October 24, 2026 UM6P Rabat Hack Day. It is not an organizer eligibility ruling or a claim that the project was submitted or will receive a prize. The private local brief images are not redistributed with the code.

## Requirements in the supplied brief

The common assignment is to build something useful in which open-source or open-weight AI does substantive work, publish a public GitHub repository under a clear open-source license, complete meaningful work during the Hack Day, provide a working demonstration, and submit before **17:00**. The build window is 10:00–17:00; teams have one to four members. Reused work must be credited, licenses respected, and keys/private data excluded from the public repository. The MLH Code of Conduct applies.

The brief also says, “Make something an algorithm can't solve.” The intended AI contribution here is interpreting drawing content and engineering-language evidence; hydraulic equations and graph traversal remain explicitly deterministic.

**Case 01 — Best Open-Source AI Project:** original work with a material role for open-source/open-weight AI; public repository; clear license; model and key dependencies identified; working demo and clear explanation. The brief also mentions the Agent Skill Open Standard for skills and originality or meaningful changes for harnesses. This project is an application, not a claim to have authored a submitted agent skill or harness.

**Case 02 — Best Use of Gemma 4:** genuinely use a Gemma model through the **Gemini API**; name the model in the README; make the integration visible in code or demonstration; explain why Gemma matters. A Gemini API credential is required and must not be committed. One submission may select both challenges. Eligibility is checked before ranking; presentation polish does not replace a missing requirement.

One teammate submits through the event page's Challenges → Add Submission flow, supplying the repository, project name, description, technologies and demo URL, selecting the entered challenges, and completing Submit Project before 17:00. The brief says judges first review the submission, repository, README and evidence; the five highest-ranked eligible teams advance to a five-minute demonstration and three-minute questions.

## What has actually been demonstrated

The configured working model is **`gemma-4-26b-a4b-it` through the Google Gemini API**. The 31B Gemma 4 variant was tried first and produced intermittent provider failures. The 26B choice is explicit configuration, not an automatic fallback to another provider. No Anthropic/Claude fallback is used by the current AI path.

Actual Atlas station-image extraction, topology review, and evidence-grounded engineering investigation have passed live requests and browser checks. Merely setting a model name or possessing a credential would not establish this; the current evidence includes real model responses and verified model identity. See [validation.md](validation.md) for the detailed run record and scope. Verification of Atlas requests does not by itself establish that every larger source-case drawing or question has been verified live.

Gemma performs work requiring interpretation: reading engineering symbols, tags, instrument signals, candidate connectivity and drawing regions; returning uncertainty for review; and explaining operational evidence with competing hypotheses. The model's output is checked by Pydantic and topology validation rather than accepted as engineering fact. Reviewed drawing facts, configured assumptions, computed observations and diagnostic hypotheses remain distinguishable.

Physics and graph operations stay deterministic: EPANET/WNTR calculates hydraulic readings and what-if operating points; graph algorithms trace connections. Gemma does not invent telemetry, calculate substitute hydraulic values, or receive the hidden injected fault identity as its diagnosis answer. The source-derived case's equipment, source facts, assumptions, controls, tank balance and measurements are separated from the original Atlas demonstration.

## Submission-readiness status

| Requirement | Local evidence / outstanding item |
| --- | --- |
| Material open-weight AI contribution | Live Gemma 4 extraction and investigation verified on Atlas. |
| Gemma 4 specifically through Gemini API | Implemented and live-verified with the configured 26B model. |
| Original application and meaningful Hack Day work | Implementation, integration, tests and documentation were developed in this workspace during the event date. Team declarations and organizer acceptance remain separate. |
| Clear code license | MIT license provided for original application code and original Atlas drawing. Third-party engineering documents retain their own rights and attribution. |
| Model, dependencies, startup instructions and explanation | README and pinned backend/frontend dependency files provided; README describes Gemma's role and the deterministic hydraulic engine. |
| Working demonstration and evidence | Local application, tested workflows and presentation artifacts exist. Consult the latest validation record for the precise tested scope; a local build alone is not a public demo URL. |
| Public repository accessible without signing in | **Not completed by this local build.** No public repository publication is claimed. |
| Event submission with required fields/challenges | **Not completed by this local build.** No submission confirmation or timely submission is claimed. |
| Submission before 17:00 | **Not established.** A functioning local application does not satisfy the event filing deadline. |

The demonstrated Gemma integration supports the model-usage part of the brief. Overall eligibility still requires the missing publication/submission steps and organizer review. This document does not claim an award, finalist selection, or an exemption from the deadline.
