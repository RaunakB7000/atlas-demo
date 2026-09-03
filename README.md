Atlas — AI Emergency Operations Copilot
Atlas ingests streams like:

- 911 call transcripts
- caller location
- incident type
- unit availability
- hospital capacity
- traffic / road closures
- weather
- prior nearby incidents
  Then it uses AIR to process, classify, prioritize, and continuously re-plan emergency response.
  The important caveat: for a hackathon, you should use synthetic or public historical 911-style data, not real private live calls unless ASU explicitly gives you authorized access.
  What Atlas would actually do
  Imagine 200 calls arriving across Phoenix.
  Instead of a dispatcher manually interpreting everything one by one, AIR processes them concurrently.
  Example calls:
  “There’s smoke coming from an apartment.”

“My dad collapsed and isn’t responding.”

“Three-car crash on Rural and Broadway.”

“Someone is yelling outside but I don’t see a weapon.”

Atlas turns that unstructured audio/text into structured incidents:
Incident #183
Type: Medical
Severity: Critical
Location: 85281
Signals:

- unconscious person
- possible cardiac arrest
  Recommended response:
- EMS
- nearest ALS ambulance
  Priority: P1
  Then you put them on a live map.
  Where AIR actually matters
  This is where I think the idea gets good.

1. Massive concurrent call processing
   Suppose a major event happens and suddenly you have:
   2,000 incoming calls.
   AIR could process many transcripts/inferences in parallel.
   Pipeline:
   911 Audio Streams
   ↓
   Qwen ASR
   speech → text
   ↓
   AIR LLM workers
   ↓
   Extract:

- emergency type
- severity
- address/location
- injuries
- hazards
- number of people
  ↓
  Structured incidents
  AIR includes a dedicated Qwen ASR model plus large reasoning models, so that fits the platform capabilities directly.
  Now your AIR justification isn't:
  “We call an LLM.”

It's:
“We process hundreds or thousands of emergency reports simultaneously.”

2. Detect duplicate calls
   This is a really interesting feature.
   During a major emergency, many people call 911 about the same event.
   Example:
   Caller 1:
   "There's a huge accident on Mill Ave."

Caller 2:
"Three cars crashed by Mill and University."

Caller 3:
"I just saw a car flip near ASU."
Those may represent one incident, not three.
AIR generates embeddings for the calls and clusters them using:

- geographic proximity
- time proximity
- semantic similarity
  So:
  500 calls

          ↓

AIR embeddings

        ↓

Incident clustering

        ↓

127 unique emergencies
That's a legitimate compute problem.
AIR provides a local embedding model suited for embedding/RAG workflows. Spark Challenge Prep Workshop Deck.pdfPDF
And this gives you a fantastic demo metric:
“Atlas received 1,000 reports but determined they represented 243 unique incidents.”

3. Severity classification
   AIR examines every incident and determines:
   P1 — Immediate threat to life
   P2 — Urgent
   P3 — Moderate
   P4 — Non-emergency
   But I would not let the AI autonomously make final life-or-death dispatch decisions.
   Pitch it as:
   Decision support for human dispatchers
   Atlas recommends:
   ⚠️ Possible cardiac arrest — escalate to P1.

Dispatcher approves.
That is a much more responsible system design and will likely play better with the challenge's emphasis on ethical technology. 4. Resource allocation
Now combine 911 intelligence with your original Atlas idea.
You have:
15 ambulances
8 fire trucks
20 police units
and:
47 active incidents
AIR has to decide which resources are most appropriate.
For example:
Incident A
Cardiac arrest
1.2 miles

Incident B
Minor collision
0.4 miles

Incident C
Building fire
3.1 miles
Atlas considers:

- severity
- travel time
- required equipment
- nearby units
- hospital capacity
- expected future demand
  and recommends assignments.

5. Continuously re-optimize
   This should be the hero feature.
   Emergency situations aren't static.
   At 8:03 PM:
   Ambulance 12 → Incident A

Then at 8:04:
🚨 New cardiac arrest call arrives.

Atlas recomputes.
Maybe Ambulance 12 should go to the new incident and Ambulance 7 covers the previous one.
Or:
Highway closed.

Recompute routes.
Or:
Hospital A reaches capacity.

Redirect incoming ambulances.
That's genuinely agentic.
Observe
↓
Analyze
↓
Plan
↓
Recommend
↓
New information
↓
Re-plan
↺ 6. Predict where calls are likely to happen
This is where it becomes even more computationally intensive.
Feed it historical data:
millions of 911 calls

- time
- location
- weather
- events
- traffic
  AIR / an ML model can identify spatiotemporal patterns.
  For example:
  Friday, 11 PM
  Mill Avenue

Atlas predicts:
Elevated incident probability
Then it could recommend pre-positioning ambulances nearby before emergencies happen.
Instead of:
“Where should we send this ambulance?”

you move toward:
“Where should ambulances be positioned in the next hour?”

That's a much bigger product.
Full Atlas architecture
ATLAS

                 Emergency streams
                        │
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓

911 calls Traffic Weather
│
↓
AIR ASR
│
↓
Transcript Processing
│
↓
┌─────────────────────────────────────────┐
│ AIR AGENT LAYER │
│ │
│ Call Understanding Agent │
│ Severity Agent │
│ Duplicate/Clustering Agent │
│ Resource Allocation Agent │
│ Routing Agent │
│ Prediction Agent │
└───────────────────┬─────────────────────┘
↓
Optimization Engine
↓
LIVE MAP

      🔴 Cardiac arrest
      🔴 Building fire
      🟠 Accident
      🟡 Disturbance

                     +
         Recommended responders

The demo I'd build
Don't actually build all of that tomorrow.
Create a simulator generating maybe:
500 synthetic 911 calls
spread around Tempe/Phoenix.
Then hit:
START EMERGENCY SIMULATION
Calls begin streaming in.
Incoming reports: 327
AIR starts processing.
Transcribed: 327
Unique incidents: 91
Critical: 12
High priority: 29
Medium: 50
The map starts populating.
Then click:
Incident #37
🔴 Possible cardiac arrest

6 calls clustered into this incident.

Confidence: 94%

Recommended response: Ambulance 4

Then trigger:
🚨 NEW INCIDENT
Major collision reported.

Atlas says:
Current resource allocation is no longer optimal.

Recalculating...
Map updates.
That's your wow moment.
And your 20-second pitch
“During emergencies, dispatch centers don't suffer from a lack of information—they suffer from too much information arriving too quickly. Atlas uses ASU AIR to process thousands of emergency reports in parallel, transcribe and understand calls, detect duplicate reports, identify critical incidents, and continuously recommend how limited emergency resources should be allocated as conditions change.”

Then:
“Instead of helping dispatchers handle one call, Atlas helps them understand the entire emergency landscape.”
