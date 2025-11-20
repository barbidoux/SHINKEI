# 📘 **SHINKEI — SPECIFICATION DOCUMENT (FULL VERSION)**

### *A platform for generating, co-authoring, and manually writing interconnected inner worlds.*

---

# 1. **Project Vision**

Shinkei (心継) is a narrative engine where each user can:

* Create one or several **inner worlds**,
* Build multiple **stories** inside each world,
* Let the AI autonomously generate the storyline (Auto Mode),
* Collaborate with the AI (Collaborative Mode),
* Write manually while the system ensures coherence (Manual Mode),
* Enjoy a coherent **global timeline** per world,
* Allow **multiple stories to intersect** through shared events,
* Explore or read these worlds through a **beautiful, elegant WebUI**.

The system must be:

* **Modular**,
* **Extensible**,
* **Local-friendly**,
* **Structured for future GraphRAG and artistic expansions**,
* Designed to scale without breaking the core model.

---

# 2. **Primary Objectives (V1)**

1. Enable users to create:

   * World definitions (bible, tone, laws),
   * A global timeline of the world (through WorldEvents),
   * Multiple stories,
   * Sequential narrative fragments (StoryBeats).

2. Provide three authoring modes:

   * **Autonomous**: AI writes everything,
   * **Collaborative**: AI proposes, user influences and edits,
   * **Manual**: user writes, AI manages coherence only.

3. Deliver a clean, intuitive, aesthetically refined **WebUI**.

4. Prepare for:

   * **GraphRAG** for enhanced memory and inter-story inference,
   * Future global graph visualizations,
   * Potential community / social features.

---

# 3. **High-Level Conceptual Model**

The architecture relies on four conceptual layers:

1. **User**
2. **World**
3. **World Timeline** (via `WorldEvent`)
4. **Stories** (story-specific progression via `Story` + `StoryBeat`)

Cross-story coherence and intersections rely on shared `WorldEvent` nodes.

---

# 4. **Data Model (Detailed)**

## 4.1. `User`

Represents the owner/creator of worlds.

```
User {
  id,
  name,
  settings: {
    language,
    default_model,
    ui_theme,
    ...
  }
}
```

---

## 4.2. `World`

A self-contained narrative universe.

```
World {
  id,
  user_id,
  name,
  description,     // general pitch
  tone,            // ex: "calm, introspective, cold"
  backdrop,        // world bible, overarching lore
  laws: {
    physics,
    metaphysics,
    social,
    forbidden
  },
  chronology_mode, // "linear" | "fragmented" | "timeless"
  created_at,
  updated_at
}
```

---

## 4.3. `WorldEvent` (Global Timeline Backbone)

A canonical event in the world’s objective timeline.

```
WorldEvent {
  id,
  world_id,
  t,               // objective timestamp (int or float)
  label_time,      // narrative representation, ex: "Log 0017"
  location_id,     // optional
  type,            // "incident", "glitch", "meeting", etc.
  summary,
  tags: [ ... ],
  created_at,
  updated_at
}
```

Key rule:
If two StoryBeats reference the same `WorldEvent`, their stories **intersect coherently**.

---

## 4.4. `Story` (Subjective narrative within a world)

```
Story {
  id,
  world_id,
  title,
  synopsis_start,  
  status: "ongoing" | "paused" | "finished" | "branched",
  pov_type: "omniscient" | "character" | "module",
  pov_character_id,      // optional
  world_time_anchor,     // optional global position
  timeline_mode: "journal" | "chapters",
  mode: "auto" | "collab" | "manual",
  created_at,
  updated_at
}
```

---

## 4.5. `StoryBeat` (Narrative fragment / log entry)

```
StoryBeat {
  id,
  story_id,
  seq_in_story,       // absolute order in the story
  world_event_id,     // can be null for dream/flashback
  local_time_label,   // ex: "Entry 003", "Log 0017"
  type: "scene" | "log" | "monologue" | "memory" | "dream",
  text,
  summary,
  generated_by: "ai" | "user" | "mixed",
  created_at
}
```

A StoryBeat is EITHER:

* anchored to `WorldEvent` (normal progression), OR
* detached from time (dreams, visions, memories).

---

## 4.6. Optional Entities (for future GraphRAG)

```
Character
Location
Concept
```

And linking tables:

```
BeatCharacter
BeatLocation
BeatConcept
```

These can be introduced later **without altering the core schema**.

---

# 5. **Coherence Rules**

1. **One world = one global timeline** built from `WorldEvent.t`.
2. **Stories are subjective** chronologies traversing that timeline.
3. **Intersections** happen when:

   * multiple stories reference the same `WorldEvent`.
4. **Three temporal layers**:

   * `t`: objective world time
   * `local_time_label`: in-world narrative timestamp
   * `seq_in_story`: reading order
5. **Every generation must respect**:

   * world laws
   * tone
   * backdrop

---

# 6. **AI Engine Architecture**

## 6.1. Abstract Interface

```
interface NarrativeModel {
  generate_next_beat(context) -> GeneratedBeat
  summarize(text) -> string
}
```

Supports:

* Local models (DeepSeek R1, GPT-OSS 20B, etc.)
* API-based models (OpenAI, etc.)
* Hot-swapping backend engines without rewriting logic

---

## 6.2. `GenerationContext`

Contains:

* World data (tone, laws, backdrop)
* Story metadata (POV, synopsis, mode)
* Recent StoryBeats
* Target WorldEvent (existing or to be created)
* User instructions (collab mode)
* Generation constraints (length, pacing, tension, etc.)

---

## 6.3. Generation Pipeline

1. Fetch world, story, last StoryBeats.
2. Determine target `WorldEvent`:

   * reuse existing, OR
   * create a new one (`t = max + 1`).
3. Build `GenerationContext`.
4. Call `generate_next_beat`.
5. Summarize output.
6. Create `StoryBeat`.
7. Persist to DB.

---

# 7. **Narrative Modes (Core Feature)**

## 7.1. **Autonomous Mode (AI-Driven)**

* AI generates all StoryBeats.
* User only reads or clicks “Continue”.
* Optional automatic generation (daily, on open, etc.).
* No validation required.

---

## 7.2. **Collaborative Mode (Human + AI Co-authoring)**

* User influences:

  * tone,
  * intent,
  * POV,
  * target WorldEvent,
  * structural instructions (“make this darker / slower / surreal”).
* AI provides **multiple candidate scenes**.
* User edits + approves.
* Hybrid creation: `generated_by="mixed"`.

---

## 7.3. **Manual Mode (Human-Written)**

* User writes the entire StoryBeat.
* AI:

  * generates summary,
  * ensures coherence with world laws,
  * identifies characters/locations/concepts,
  * suggests the best WorldEvent.
* No AI content generation.

---

## 7.4. **Mode Switching**

Users can switch at any time:

* Auto → Collab → Manual → back
* Without breaking the story’s structure
* Without invalidating the timeline or events

Shinkei must gracefully adapt prompts and pipelines accordingly.

---

# 8. **WebUI Requirements**

## 8.1. General Design Principles

* Minimalistic, elegant, modern.
* Light/Dark mode.
* Emphasis on **readability** and smooth navigation.

---

## 8.2. Main Views

### **Dashboard / World List**

* List of all user worlds.
* Create world button.

### **World View**

* World summary (tone, laws, backdrop).
* Global timeline (WorldEvent list).
* Story list.
* Actions:

  * Add Story,
  * Add WorldEvent.

### **Story View**

* Title, POV, synopsis.
* **Mode selector** (Auto / Collab / Manual).
* StoryBeat journal view.
* Add / Generate next beat.
* In Collab mode:

  * multiple AI suggestions,
  * intention controls,
  * editing pane.
* In Manual mode:

  * rich text editor,
  * suggestions panel.

### **WorldEvent View**

* label_time, summary, type, tags.
* StoryBeats referencing this event.
* Create new StoryBeat linked to this event.

---

# 9. **GraphRAG (Future Phase)**

Nodes:

* WorldEvent
* StoryBeat
* Character
* Concept
* Location

Edges:

* next_in_story
* belongs_to_story
* occurs_in_world_event
* mentions_character
* expresses_concept
* etc.

Usage:

* Enhance generation with richer memory.
* Search similar narrative patterns.
* Offer interactive graph visualizations.
* Enable future inter-world shared structures.

Shinkei’s data model is **already GraphRAG-ready** from day one.

---

# 10. **Roadmap**

### **Phase 0 — Foundations**

* Repo setup
* Basic backend (FastAPI, Node, etc.)
* DB with migrations
* UI skeleton

### **Phase 1 — Core CRUD**

* Worlds
* WorldEvents
* Stories
* StoryBeats
* Basic UI

### **Phase 2 — AI Engine**

* NarrativeModel implementation
* Generation pipeline
* UI “Generate Next Beat”

### **Phase 3 — Narrative Modes**

* Auto mode
* Manual mode
* Collaborative mode

### **Phase 4 — World Timeline + Crossovers**

* Full timeline UI
* Multi-story intersections via shared WorldEvents

### **Phase 5 — GraphRAG & Advanced Features**

* Vector store integration
* Node indexing
* Semantic retrieval
* Graph visualizations

---

# 11. **Non-Functional Requirements**

* SQL database (SQLite or Postgres)
* Modular backend API
* Logged AI interactions
* Stable IDs and timestamps
* Expandable schema without breaking changes
* Local-friendly performance
* Simple but secure user management

---

# 🟦 **Final Summary**

Shinkei’s specification provides:

* a **robust, clean, extensible core**,
* three **authoring paradigms** (auto, collab, manual),
* a consistent **world timeline with cross-story intersections**,
* future compatibility with **GraphRAG**,
* a polished **WebUI**,
* a well-structured roadmap for incremental complexity.

This document is the blueprint for building Shinkei without technical debt — and with maximum creative power.
