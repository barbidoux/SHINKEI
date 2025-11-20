

# **Shinkei (心継) Project: Software Architecture Document**

Version: 1.0.2  
Status: Baseline (Updated)  
Document Control: This document is the canonical source of truth for the architectural design of the Shinkei platform. All development must adhere to the models and standards defined herein.

---

## **1.0 Architectural Overview**

This document defines the high-level architecture of the Shinkei system. The architecture is documented using the **C4 Model** 1, which provides a set of hierarchical diagrams to communicate the system's design at different levels of abstraction.3 This approach ensures clarity for all stakeholders, from high-level context for business owners to component-level detail for developers.3

### **1.1 Level 1: System Context Diagram (C4)**

The System Context diagram is the highest-level view, illustrating the Shinkei system as a "black box" and its interactions with external users and systems.4

* **System:** The Shinkei Narrative Engine is the central software system being built.  
* **Actors:**  
  * Author (User): The primary user of the system, who creates, co-authors, and reads interconnected narratives via the WebUI.  
* **External Systems:**  
  * Supabase Auth: The external identity provider. It is part of the Supabase platform and is responsible for handling all user authentication (sign-up, sign-in, profile management).  
  * External LLM API: One or more third-party Large Language Model providers (e.g., OpenAI, Anthropic, or a self-hosted model) that provide the generative AI capabilities for the "Autonomous" and "Collaborative" authoring modes.6

The specification's requirement for "Simple but secure user management" 6 is perfectly satisfied by this architecture. By defining Supabase Auth as the external system, a foundational architectural decision is made: Shinkei *will not* store user passwords or manage authentication logic. It will delegate this responsibility to the managed Supabase platform. This decision fully satisfies the non-functional requirement (NFR) by simplifying the core application's domain while achieving a high standard of security.

### **1.2 Level 2: Container Diagram (C4)**

The Container diagram zooms into the Shinkei System boundary, revealing the high-level, independently deployable "containers" (applications and data stores) that constitute the system.3

* **Containers:**  
  1. Shinkei WebUI (SvelteKit Application): A Single-Page Application (SPA) delivered to the Author's browser. This container is responsible for rendering the "clean, intuitive, aesthetically refined WebUI" 6 and is built with SvelteKit.7  
  2. Shinkei API (FastAPI Modular Monolith): The core backend application. It is a single, deployable Python application built with FastAPI 9 that serves all API requests, manages business logic, and orchestrates AI interactions.  
  3. Supabase (PostgreSQL Platform): The persistence and authentication layer. This container represents the managed Supabase platform, which provides the core PostgreSQL database.  
  4. Observability Collector (OpenTelemetry): A lightweight, standalone agent 10 that receives, processes, and exports all telemetry (logs, metrics, traces) from the Shinkei API and WebUI to an observability platform.

The NFRs for a "Local-friendly" 6 and "Extensible" system 6 are now resolved through the Supabase ecosystem. The architecture remains constant, but its physical deployment model is flexible:

* **Local Development:** The WebUI and Shinkei API run as local processes. The Supabase container is implemented using the **Supabase CLI**, which runs the entire Supabase stack (Postgres, Auth, etc.) locally in Docker. This provides a high-fidelity, "Local-friendly" 6 development environment that perfectly mirrors production.  
* **SaaS Deployment:** The WebUI is served from a CDN. The Shinkei API is deployed as a scalable service. The Supabase container is the managed, cloud-hosted Supabase platform, which provides a scalable PostgreSQL database designed to handle high concurrency and large data volumes.

### **1.3 Architectural Pattern: The Modular Monolith**

The Shinkei API container is designed as a **Modular Monolith**.11 This pattern is deliberately chosen over a traditional monolith or a microservices architecture to satisfy the NFRs.6

* **Justification:**  
  * **Why not Microservices?** A microservices-first approach 12 introduces significant "development sprawl" 13, complex inter-service communication, and high infrastructure overhead.11 Critically, it is incompatible with the "Local-friendly" NFR 6, as deploying and managing a dozen services locally is operationally infeasible for a non-technical user.  
  * **Why not Supabase's Auto-Generated API?** Supabase provides an excellent auto-generated PostgREST API. However, this is unsuitable for the Shinkei project's complex, stateful business logic (e.g., "Autonomous Mode" generation 6, "Coherence" checks 6, GraphRAG orchestration 6). A dedicated backend is required for this. The FastAPI monolith provides the necessary "business logic" layer that sits *between* the user and the database.  
  * **The Modular Monolith:** This pattern provides the "best of both worlds".14 It retains the development speed 13 and simple debugging 11 of a monolith. Simultaneously, it enforces strong, logical boundaries between "business modules" 11, which aligns perfectly with Domain-Driven Design (DDD).  
* **Core Principles:**  
  1. **Domain-Driven Boundaries:** Modules are structured around business capabilities (e.g., Worlds, Stories, Generation), not technical layers (e.g., controllers, models, views).11  
  2. **Internal API Facades:** Modules communicate "inside the monolith" 11, but *not* by directly accessing each other's database tables or internal logic. Each module *must* expose a well-defined internal API (e.g., a services.py file or "facade") for other modules to consume. Cross-boundary database joins are forbidden.  
  3. **Future-Proof Extensibility:** This modularity 11 is the "preparation for future phases".6 If the Generation (AI) module becomes a performance bottleneck, its well-defined boundary 11 allows it to be "extracted as a microservice" 6 with minimal refactoring of the core system.  
* **Table 1.3.1: Backend Module (Component) Boundaries:** This table defines the public contract for each internal module of the Shinkei API. To enforce the Modular Monolith pattern 11 and prevent code-level coupling, this table serves as the "constitution" for developers, ensuring modules remain independent.11

| Module | Business Capability | Public API / Facade (Example Functions) |
| :---- | :---- | :---- |
| Core | Shared services (DB, Config, Logging) | get\_db\_session(), get\_settings() |
| AuthN\_AuthZ | "Simple but secure user management" | get\_current\_active\_user(token), validate\_supabase\_jwt(token) |
| Worlds | "Create world definitions", "Global timeline" | get\_world(world\_id, user\_id), create\_world\_event(world\_id, event\_data) |
| Stories | "Create multiple stories", "Create... StoryBeats" | get\_story(story\_id, user\_id), create\_story\_beat(story\_id, beat\_data) |
| Coherence | "Ensure coherence in Manual Mode", "Identify entities" | validate\_beat\_coherence(beat\_id), extract\_entities\_from\_beat(beat\_id) |
| Generation | "Autonomous Mode", "Collaborative Mode" | generate\_next\_beat\_autonomous(story\_id), propose\_collaborative\_beats(story\_id, intent) |
| GraphRAG | "Prepare for GraphRAG", "Inter-story inference" | query\_graph(world\_id, query\_text) |

### **1.4 Level 3: Component Diagram (Shinkei API)**

This C4 diagram zooms into the Shinkei API container, visualizing the internal modules (components) defined in Table 1.3.1.4

* **Driving Component:** The Core component provides shared dependencies (like the DB session) to all other components.  
* **User-Facing Components:** AuthN\_AuthZ, Worlds, and Stories handle direct, user-initiated API requests (CRUD operations).  
* **Internal/AI Components:**  
  * Generation (AI): Consumes services from Worlds (to get the bible) and Stories (to get context) to produce new StoryBeats.  
  * Coherence: Consumes services from Stories (to get StoryBeat content) and GraphRAG (to query entities) to perform validation.  
  * GraphRAG: An internal component (initially) that manages the entities and entity\_links tables.

A common failure mode for modular architectures is that the code's structure does not reflect the architectural intent, leading to "architectural drift" and the eventual return of the "big ball of mud".17 To prevent this, the C4 Component diagram will *directly* map to the backend's physical source code directory structure.

This architecture *mandates* a domain-based "module-functionality" structure 15 and *forbids* the file-type structure (e.g., src/controllers/, src/models/) seen in many tutorials.16 This ensures the physical code aligns with the logical architecture, making modularity the path of least resistance.

**Required Project Structure:**

src/  
├── core/         \# Core Module  
├── auth/         \# AuthN\_AuthZ Module  
├── worlds/       \# Worlds Module  
├── stories/      \# Stories Module  
├── coherence/    \# Coherence Module  
├── generation/   \# Generation Module  
└── main.py       \# Assembles the FastAPI app from module routers

## **2.0 The Shinkei Data Model**

This section defines the "whole data model" \[User Query\] required by the Shinkei project. It satisfies the 6 constraints for an SQL database that is "GraphRAG-ready" from day one. The model is presented first as a Logical Data Model (LDM) 20 and then as a precise Physical Data Model (PDM).21

### **2.1 Logical Data Model (LDM)**

The LDM defines the core business entities and their relationships, independent of any specific SQL implementation.20

* Entities 6:  
  * User: An author who owns Worlds.  
  * World: A self-contained universe. It *owns* many Stories and many WorldEvents. It has a World Bible (tone, laws).  
  * WorldEvent: An *objective* event on the World's global timeline. This is a canonical anchor point in time (e.g., "The Battle of Red Mountain").  
  * Story: A subjective narrative (a chronology) that exists within a World. It *owns* many StoryBeats.  
  * StoryBeat: The smallest sequential fragment of a Story.  
* **The Core Logical Relationship (Coherence & Intersection):**  
  * The NFRs 6 require "coherence," a "global timeline," and "intersections."  
  * **Logic:** A Story (subjective) "intersects" 6 the World's "global timeline" (objective) by linking its StoryBeats to WorldEvents.  
  * **Example:** Story A (a soldier's perspective) and Story B (a general's perspective) can both have StoryBeats that *link* to the *same* WorldEvent ("The Battle of Red Mountain"). This is the "intersection." The system can then infer that these two beats are happening *at the same time* and *in the same context*. This is the "inter-story inference" 6 and the foundation of coherence.

### **2.2 Physical Data Model (SQL)**

This is the precise, physical implementation of the LDM for the Supabase (PostgreSQL) database, satisfying the 6 constraint. The design ensures all NFRs for "Stable IDs and timestamps" are met.6

* **Core Entity Tables:**  
  SQL  
  CREATE TABLE users (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      email VARCHAR(255) UNIQUE NOT NULL,  
      \-- The "real-world" audit timestamp (when this user signed up)  
      created\_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')  
  );

  CREATE TABLE worlds (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      owner\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  
      name VARCHAR(255) NOT NULL,  
      description\_bible TEXT,  
      tone\_and\_laws TEXT,  
      \-- The "real-world" audit timestamp (when this world was created)  
      created\_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')  
  );

  CREATE TABLE world\_events (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      world\_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,  
      title VARCHAR(255) NOT NULL,  
      description TEXT,  
      \-- The objective, canonical timestamp for this event IN THE FICTIONAL WORLD.  
      \-- This is the "in-world" time, not the real-world creation time.  
      timestamp\_utc TIMESTAMPTZ NOT NULL,  
      \-- The "real-world" audit timestamp (when this record was created)  
      created\_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')  
  );

  CREATE TABLE stories (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      world\_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,  
      title VARCHAR(255) NOT NULL,  
      summary TEXT,  
      \-- The "real-world" audit timestamp (when this story was created)  
      created\_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')  
  );

  CREATE TABLE story\_beats (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      story\_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,  
      \-- The core narrative content  
      content TEXT,  
      summary TEXT,  
      \-- Sequential order within the Story (e.g., Beat 1, Beat 2, Beat 3\)  
      \-- This defines the internal chronology of a single story.  
      sequence\_order INT NOT NULL,

      \-- Authoring mode (Auto, Collab, Manual) from   
      authoring\_mode VARCHAR(20) NOT NULL CHECK (authoring\_mode IN ('autonomous', 'collaborative', 'manual')),  
      \-- Generation source (ai, mixed, human) from   
      generated\_by VARCHAR(20) NOT NULL CHECK (generated\_by IN ('ai', 'mixed', 'human')),

      \-- The "Intersection" link to the objective timeline  
      linked\_world\_event\_id UUID REFERENCES world\_events(id) ON DELETE SET NULL,

      \-- The "real-world" audit timestamp (when this beat was created)  
      created\_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),

      \-- Ensure sequence is unique within a story  
      UNIQUE(story\_id, sequence\_order)  
  );

  CREATE TABLE ai\_logs (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      beat\_id UUID REFERENCES story\_beats(id) ON DELETE SET NULL,  
      \-- Satisfies "Logged AI interactions" NFR from   
      request\_prompt\_hash VARCHAR(64), \-- Hashed to save space  
      response\_content\_hash VARCHAR(64),  
      raw\_request\_payload TEXT, \-- For full debugging  
      raw\_response\_payload TEXT,  
      timestamp\_utc TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')  
  );

* **Table 2.2.1: Physical Data Model Dictionary:** This table provides the canonical definition and justification for critical columns, as mandated by the "highest level of precision" requirement \[User Query\] and linking the schema to the NFRs.23

| Table | Column | Data Type (Postgres) | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| worlds | description\_bible | TEXT | NOT NULL | Stores the "world bible, tone, and laws." |
| story\_beats | authoring\_mode | VARCHAR(20) | NOT NULL, CHECK | Stores the active mode ('autonomous', 'collaborative', 'manual') per 6. |
| story\_beats | generated\_by | VARCHAR(20) | NOT NULL, CHECK | Stores the hybrid "mixed" state for "Collaborative Mode" per 6. |
| story\_beats | linked\_world\_event\_id | UUID | FK \-\> world\_events.id | **Critical:** This is the physical "intersection" 6 linking the subjective StoryBeat to the objective Global Timeline. |
| **world\_events** | **timestamp\_utc** | **TIMESTAMPTZ** | **NOT NULL** | **This is the "In-World" Fictional Timestamp.** This defines the *fictional* date (past, present, or future) of the event, which drives the global timeline. |
| **story\_beats** | **sequence\_order** | **INT** | **NOT NULL, UNIQUE(story\_id)** | **This is the "Story-Internal" Chronology.** It defines the order of beats *within* a single story (e.g., Beat 1, Beat 2...). |
| **(All tables)** | **created\_at** | **TIMESTAMPTZ** | **DEFAULT (now())** | **This is the "Real-World" (IRL) Audit Timestamp.** It records when the row was created in the database, independent of the fictional timeline. |
| ai\_logs | id | UUID | PK | Fulfills the "Logged AI interactions" NFR.6 |

### **2.3 GraphRAG-Ready Schema (Adjacency Lists)**

This design is the most critical component of the data model, satisfying the "GraphRAG-ready" NFR 6 *within* the "SQL database" constraint.6

These two NFRs are in direct conflict: GraphRAG (Retrieval-Augmented Generation) 24 is designed to query structured knowledge graphs (nodes and edges) 27, which are typically stored in graph databases like Neo4j.28 A standard SQL database is relational, not graph-based.29

The only viable solution is to model a graph *inside* the SQL database. The standard pattern for this is an **Adjacency List**.30 Therefore, the "preparation for future GraphRAG" 6 is the *creation of these graph tables from day one*.

* **Graph Schema (Adjacency List Model):**  
  SQL  
  \-- The "Nodes" of the graph  
  CREATE TABLE entities (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      world\_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,  
      \-- e.g., 'CHARACTER', 'LOCATION', 'CONCEPT', 'ITEM'  
      entity\_type VARCHAR(50) NOT NULL,  
      name VARCHAR(255) NOT NULL,  
      \-- JSONB for flexible properties  
      properties JSONB,  
      UNIQUE(world\_id, entity\_type, name)  
  );

  \-- The "Edges" of the graph  
  CREATE TABLE entity\_links (  
      id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
      world\_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,  
      \-- The source node (e.g., 'Marko')  
      source\_entity\_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,  
      \-- The target node (e.g., 'Dragon')  
      target\_entity\_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,  
      \-- The relationship (e.g., 'HATES', 'VISITED', 'OWNS')  
      relationship\_type VARCHAR(50) NOT NULL,  
      \-- JSONB for edge properties (e.g., '{"timestamp": "..."}')  
      properties JSONB  
  );

  \-- Join table connecting narrative back to the graph  
  CREATE TABLE beat\_entity\_mentions (  
      beat\_id UUID NOT NULL REFERENCES story\_beats(id) ON DELETE CASCADE,  
      entity\_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,  
      PRIMARY KEY(beat\_id, entity\_id)  
  );

* **Process:** When the AI (in any mode) "identifies entities" 6, the Coherence module will populate these tables.  
  1. StoryBeat content: "Marko visited The Red Keep."  
  2. Coherence module creates/finds entities (Node 'Marko', Node 'The Red Keep').  
  3. Coherence module creates an entity\_link (Edge: 'Marko' \--\> 'The Red Keep').  
  4. Coherence module creates beat\_entity\_mentions to link the beat to both entities.  
* This schema provides the structured data 27 necessary for future GraphRAG 24 queries. This implementation is further strengthened by Supabase's native support for the pgvector extension, which should be enabled to support future vector-based RAG operations.

### **2.4 Global Timeline Implementation**

This implements the "coherent global timeline" NFR.6 The specification calls for a global timeline of WorldEvents 6, but StoryBeats are also events in time, linked to those WorldEvents. A user will want to see all these events in a single, chronological view.

A single timeline table 33 would be a poor design, as it would incorrectly mix objective canonical data (WorldEvents) with subjective narrative data (StoryBeats).

The correct implementation, inspired by the "displayable\_events" concept 33, is a read-only VIEW. This VIEW *unifies* (using UNION ALL) all time-based entities into a single, queryable timeline.

* **Global Timeline Schema (VIEW):**  
  SQL  
  CREATE VIEW vw\_global\_timeline AS  
  \-- 1\. All objective WorldEvents  
  SELECT   
      w.world\_id,  
      w.id AS event\_id,  
      'WORLD\_EVENT' AS event\_type,  
      w.title,  
      w.description,  
      w.timestamp\_utc,  
      NULL AS story\_id,  
      NULL AS beat\_id  
  FROM world\_events w

  UNION ALL

  \-- 2\. All subjective StoryBeats, linked to time via their WorldEvent  
  SELECT   
      s.world\_id,  
      b.linked\_world\_event\_id AS event\_id,  
      'STORY\_BEAT' AS event\_type,  
      s.title AS title,  
      b.summary AS description,  
      we.timestamp\_utc, \-- Derives its time from the WorldEvent  
      s.id AS story\_id,  
      b.id AS beat\_id  
  FROM story\_beats b  
  JOIN stories s ON b.story\_id \= s.id  
  JOIN world\_events we ON b.linked\_world\_event\_id \= we.id  
  WHERE b.linked\_world\_event\_id IS NOT NULL;

This VIEW explicitly uses the timestamp\_utc from the world\_events table as its sorting key. This ensures the timeline is always sorted by the *fictional, in-world time*, regardless of the *real-world* created\_at time when the stories or beats were written. A query such as SELECT \* FROM vw\_global\_timeline WHERE world\_id \=? ORDER BY timestamp\_utc now provides the complete, interleaved global timeline 6 for any given world.

### **2.5 Schema Extensibility Strategy**

This delivers the "Expandable schema without breaking changes" NFR.6

* **Strategy:** The system will adopt the formal **"Expand and Contract"** (or "parallel change") model 34 for all database migrations. This ensures zero-downtime deployments. All schema changes must be "constructive" (e.g., adding a new, nullable column) 36 first. Destructive changes (e.g., dropping a- column) 36 are only allowed in a later, separate migration *after* the application code no longer depends on the old schema.  
* **Process (Example: Renaming worlds.name to worlds.title):**  
  1. **Migration 1 (Expand):** ALTER TABLE worlds ADD COLUMN title VARCHAR(255) NULL;.36  
  2. **Application v2 Deployment:** Code is updated to write to *both* name and title. It is updated to read from title, falling back to name if title is NULL.  
  3. **Data Backfill (Script):** UPDATE worlds SET title \= name WHERE title IS NULL;  
  4. **Application v3 Deployment:** Code is updated to *only* read/write to title.  
  5. **Migration 2 (Contract):** ALTER TABLE worlds DROP COLUMN name;.34  
* **Tooling:** **Alembic** 15 will be the required database migration tool, as it is the standard for the SQLAlchemy/SQLModel ecosystem against the Supabase database.

## **3.0 End-to-End Technology Stack**

This section defines "all necessary techno stacks for the development" \[User Query\], with each choice justified against the functional and non-functional requirements.6

* **Table 3.1: Technology Stack Summary:** This table provides the "executive summary" of the entire stack, mapping NFRs directly to the chosen technologies.

| Category | Requirement | Chosen Technology | Justification |
| :---- | :---- | :---- | :---- |
| **Backend API** | "Modular backend API", "AI-driven" | **FastAPI (Python)** | High-performance async 9, superior AI/ML ecosystem 37, domain-based modularity.15 |
| **WebUI** | "Minimalistic, elegant, modern WebUI" | **SvelteKit** | Unmatched performance 38, small bundles 40, developer simplicity 41 aligns with "elegant" NFR. |
| **UI Library** | "Aesthetically refined", "Readability" | **Bits UI \+ Tailwind CSS** | "Headless" 42 / "copy-paste" 43 approach provides maximum customizability for a "minimalistic" 44 design. |
| **Database** | "SQL database", "Local-friendly" | **Supabase (PostgreSQL)** | Managed Postgres platform with integrated Auth and a local dev stack via Supabase CLI. |
| **DB Abstraction** | SQL DB support, Validation | **SQLModel** | Perfect FastAPI match 46; combines Pydantic (validation) and SQLAlchemy (ORM) 47 to abstract the DB connection, supporting both local Supabase and cloud Supabase instances. |
| **Authentication** | "Simple but secure user management" | **Supabase Auth \+ JWT** | Uses Supabase's built-in Auth, with FastAPI performing high-performance local JWT validation. |
| **Observability** | "Logged AI interactions", "Extensible" | **OpenTelemetry \+ SigNoz** | OTel is the vendor-neutral standard.48 SigNoz 10 provides a *unified* 10 platform, avoiding the fragmented Prometheus/Jaeger stack.10 |
| **Documentation** | (Implied) Maintainable Architecture | **Structurizr Lite \+ ADRs** | "Diagrams as Code" 49 for C4 models 50; ADRs 51 log decisions. |

### **3.1 Frontend (WebUI): SvelteKit**

* **Framework:** **SvelteKit**.7  
* Justification: The NFR 6 is for an "aesthetically refined," "minimalistic," and "elegant" UI with high "readability." Svelte 52 is a compiler that shifts work from the browser (runtime) to the build step.40 This produces minimal JavaScript bundles 39, resulting in outstanding raw performance 38 that is ideal for a "smooth navigation" 6 experience. Svelte's "less boilerplate" philosophy 39 aligns with the "elegant" NFR.  
  SvelteKit 7 is chosen over plain Svelte 54 because it is the official, full-featured application framework 7 that integrates perfectly with Supabase's server-side auth helpers. It provides file-system-based routing, server-side rendering (SSR), and a complete development server.8  
* **UI Components:** To achieve the "minimalistic" and "elegant" NFR 6, a heavy, opinionated library like Material UI or Bootstrap 56 will *not* be used. A "headless" or "copy-paste" approach 43 is mandated:  
  * **Core:** **Bits UI** 42 or **Shadcn-Svelte** (a port of 43). These provide accessible, unstyled component primitives 42 that serve as the functional foundation.  
  * **Styling:** **Tailwind CSS**.43 This utility-first framework allows for building the "clean, intuitive... modern" 6 design from scratch, adhering to minimalist principles.44  
* **State Management:** Svelte's native stores 59 will be used.  
  * writable and derived stores 60 will be used for managing global UI state (e.g., the currently selected World). This approach is simpler, cleaner, and more idiomatic to Svelte than importing complex third-party libraries.61  
  * The Supabase client (@supabase/supabase-js) will manage all authentication state.  
* Light/Dark Mode 6: A writable Svelte store 41 will manage the theme ('light', 'dark', 'system'). The 'system' default will use the window.matchMedia("(prefers-color-scheme: dark)") API 63 to detect and react to OS-level preferences.

### **3.2 Backend (API): FastAPI (Python)**

* **Framework:** **FastAPI** (Python).9  
* **Justification:** This is a critical architectural decision. The project's core purpose 6 is an "AI... narrative engine." This requires deep, native integration with the AI/ML ecosystem.  
  * **FastAPI (Python) vs. NestJS (Node.js):** While NestJS is a robust, modular framework well-suited for enterprise apps 64, the Python ecosystem for AI, LLMs, and future GraphRAG 24 is non-negotiable. FastAPI 9 offers superior performance (on par with Node.js 66), a modern async-first architecture 9, automatic data validation, and native integration with the Python AI stack.67  
* **Database Abstraction:** **SQLModel**.46  
* **Justification:** SQLModel, built by the same author as FastAPI 46, is the *perfect* match. It combines:  
  1. **Pydantic:** For data validation and settings management.15  
  2. **SQLAlchemy:** As the underlying ORM 46 that abstracts the database connection. This allows the application to seamlessly connect to both the local Supabase Docker instance and the cloud-hosted Supabase platform just by changing a connection string.  
  * This allows the data model to be defined *once* (as a single Python class) and serve as the ORM table definition *and* the API request/response validation schema, dramatically reducing code duplication.

### **3.3 Database (Persistence): Supabase (PostgreSQL)**

* **Strategy:** The architecture is standardized on the Supabase platform. This satisfies the SQL constraint 6 by using PostgreSQL, while also providing integrated Auth, Storage, and APIs. The "Local-friendly" NFR 6 is met by using the **Supabase CLI** for local development, which runs the full Supabase stack (Postgres, Auth, etc.) in Docker on the developer's machine.  
* **Implementation:** The application will use a single environment variable, DATABASE\_URL, to configure the SQLModel engine.  
  * **Local (Supabase CLI):** DATABASE\_URL="postgresql://postgres:@localhost:5432/postgres"  
  * **Prod (Supabase Cloud):** DATABASE\_URL="postgresql://postgres:@db.abcdef.supabase.co:5432/postgres"  
* Graph Traversal 6: For all GraphRAG-related queries (on the tables in Section 2.3), the system will use **Recursive Common Table Expressions (CTEs)** (WITH RECURSIVE).70 This is a powerful, standard-SQL feature 70 that allows traversal of graph/hierarchical data 71 (our adjacency lists) *without* requiring a dedicated graph database 29, thereby satisfying all 6 constraints.

## **4.0 Security Architecture and Controls**

This section details "all security aspects" \[User Query\] of the Shinkei system. The design philosophy is "simple but secure" 6, achieved by externalizing authentication to Supabase and implementing explicit, code-level authorization controls in our FastAPI backend based on the **OWASP API Security Top 10**.74

### **4.1 Authentication ("Simple but secure user management")**

* **Protocol:** **Supabase Auth (JWT-based)**.  
* **Justification:** By adopting Supabase as the database platform, we also gain access to Supabase Auth. This is the new, definitive Identity Provider (IdP) for the system. The Shinkei WebUI (SvelteKit) will use the Supabase client library (@supabase/supabase-js) to handle all user sign-up, sign-in, and profile management. This satisfies the "simple but secure" NFR.6  
* **FastAPI Integration (High-Performance Validation):**  
  * The Shinkei API (FastAPI) will *not* use the Supabase client library for auth. Instead, to maintain high performance and statelessness, it will act as a protected resource server by **locally validating** the JWTs issued by Supabase Auth.  
  * The AuthN\_AuthZ module will retrieve the Supabase JWT\_SECRET from environment variables. When a request arrives with an Authorization: Bearer \<token\>, the module will use a Python JWT library (like pyjwt) to decode and validate the token's signature, expiry, and claims *locally*.  
  * This critical design choice avoids the common but slow pattern of making a round-trip API call to the Supabase auth.get\_user() endpoint for every single request, which would introduce significant latency.  
* **Token Strategy: Stateless JWT Validation**  
  * The API will be **stateless**.77 The Shinkei WebUI (SvelteKit) will use the official @supabase/supabase-js client library.  
  * **The Flow:**  
    1. **Login:** The user logs in via the SvelteKit UI, and @supabase/supabase-js handles the entire flow with Supabase Auth, securely storing the session and refresh tokens.  
    2. **API Requests:** For every request to the Shinkei API (FastAPI), the SvelteKit frontend will retrieve the *current access token* from the Supabase client (supabase.auth.getSession()) and send it in the Authorization: Bearer \<token\> header.  
    3. **FastAPI Validation:** The FastAPI backend receives this token. The AuthN\_AuthZ module's dependency (get\_current\_active\_user) will *locally validate* this JWT using the shared SETTINGS.supabase\_jwt\_secret. This check is instant and requires no network call.  
    4. **Token Expiry/Refresh:** The @supabase/supabase-js library on the client-side *automatically* handles refreshing the access token in the background. The FastAPI backend is never involved in the refresh process; it only ever sees valid, short-lived access tokens.  
    5. **Logout:** The SvelteKit client calls supabase.auth.signOut(), which invalidates the local session.  
* **Implementation (FastAPI Code Snippet):**  
  * **Protected Endpoint:** current\_user: User \= Depends(get\_current\_active\_user).78

### **4.2 Authorization (OWASP API Security)**

The system will systematically mitigate the OWASP API Security Top 10 risks.75 Security principles from other ecosystems 79 inform the overall posture, but the implementation will be FastAPI-specific.81

* **Table 4.2.1: OWASP API Security Mitigation Matrix:** This matrix provides the auditable, high-precision plan for securing the API, mapping critical threats 75 to specific, code-level solutions.

| Risk (OWASP API 2023\) | Vulnerability Example | Mitigation Strategy | Implementation (FastAPI) |
| :---- | :---- | :---- | :---- |
| **API1:2023 \- Broken Object Level Authorization (BOLA)** | GET /worlds/{world\_id} \- User A requests a world\_id belonging to User B. | **Explicit Ownership Check via Dependency Injection**.82 | world: World \= Depends(get\_world\_for\_user) |
| **API2:2023 \- Broken Authentication** | Compromised JWT token, weak passwords. | **Externalized Supabase Auth \+ Stateless Local JWT Validation**. | Supabase Auth IdP \+ jwt.decode(token, secret). |
| **API3:2023 \- Broken Object Property Level Authorization (BOPLA)** | PUT /user/me \- User sends {"username": "new", "is\_admin": true} (Mass Assignment).83 | **Strict Input/Output Schemas**. | Use separate Pydantic/SQLModel schemas for Input (UserUpdate) and Output (UserPublic).84 *Always* use response\_model. |
| **API4:2023 \- Unrestricted Resource Consumption** | User spams AI generation endpoint POST /stories/gen, incurring massive LLM costs.75 | **Per-User, Per-Endpoint Rate Limiting**. | fastapi-limiter 81 configured with Depends(RateLimiter(times=5, minutes=1)). |
| **API5:2023 \- Broken Function Level Authorization** | Regular user accesses GET /admin/users. | **Role-Based Access Control (RBAC) via Dependencies**. | Depends(get\_user\_with\_role("admin")) dependency on admin routers. |

* **Deep Dive: Mitigating API1: BOLA (Broken Object Level Authorization)** 85  
  * **Threat:** This is the \#1 API risk.76 An authenticated user simply changes the ID in a URL (/worlds/{id}) to access or modify another user's data.82  
  * **Our Solution (Code-Level):** An endpoint *must never* trust a user-supplied ID directly. FastAPI's Dependency Injection system will be used to enforce ownership.  
  * **Forbidden Pattern:**  
    Python  
    @app.get("/worlds/{world\_id}")  
    def get\_world(world\_id: UUID):  
        return db.get(World, world\_id) \# VULNERABLE TO BOLA

  * **Required Secure Pattern** 82:  
    Python  
    \# 1\. Create a reusable dependency  
    async def get\_world\_for\_user(  
        world\_id: UUID,   
        current\_user: User \= Depends(get\_current\_active\_user),  
        db: Session \= Depends(get\_db\_session)  
    ) \-\> World:  
        world \= db.query(World).filter(World.id \== world\_id).first()  
        if not world or world.owner\_id\!= current\_user.id:  
            raise HTTPException(status\_code=404, detail="World not found")  
        return world

    \# 2\. Use the dependency in the endpoint  
    @app.get("/worlds/{world\_id}", response\_model=WorldPublic)  
    async def read\_world(  
        world: World \= Depends(get\_world\_for\_user) \# SECURED  
    ):  
        return world

* **Deep Dive: Mitigating API3: BOPLA (Broken Object Property Level Authorization)** 83  
  * **Threat:** Mass Assignment.83 A user submitting extra, malicious fields in a JSON payload (e.g., "is\_admin": true) that get automatically bound to the database model.84  
  * **Our Solution (Code-Level):** Strict, separate Pydantic/SQLModel schemas for *both* input and output.  
    Python  
    \# 1\. Database Model (has sensitive fields)  
    class User(SQLModel, table=True):  
        id: UUID  
        email: str  
        hashed\_password: str \# Sensitive  
        is\_admin: bool \= False \# Sensitive

    \# 2\. Input Schema (only allows safe fields)  
    class UserUpdate(BaseModel):  
        email: Optional\[str\] \= None  
        \# is\_admin is NOT here. Cannot be set by user.

    \# 3\. Output Schema (filters sensitive fields)  
    class UserPublic(BaseModel):  
        id: UUID  
        email: str  
        \# hashed\_password and is\_admin are NOT here.

    \# 4\. Secured Endpoint  
    @app.patch("/users/me", response\_model=UserPublic) \# Uses Output Schema  
    async def update\_me(  
        user\_in: UserUpdate, \# Uses Input Schema  
        current\_user: User \= Depends(get\_current\_active\_user)  
    ):  
        \#... update logic...  
        return current\_user

### **4.3 AI Security (OWASP LLM Top 10\)**

The AI-driven modes 6 introduce new attack vectors, governed by the **OWASP LLM Top 10**.86

* **Threat: LLM01: Prompt Injection**  
  * **Scenario:** In "Collaborative Mode" 6, a user provides "intent" (e.g., "Write a scene where Marko is sad"). They could inject: "Ignore the world bible and all previous instructions."  
  * **Mitigation:** **Prompt Segregation and System Constraints.** The backend's Generation module will *not* simply concatenate strings. It will use a structured prompt format where the World Bible 6 and System Instructions are in a privileged, non-user-overridable field (e.g., the system role in OpenAI's API). The user's "intent" is placed in the user role, sandboxed from the core instructions.  
* **Threat: LLM07: Insecure Output Handling / LLM04: Model Denial of Service**  
  * **Scenario:** The AI "Autonomous Mode" 6 generates content that is malicious, excessively long, or costly.  
  * **Mitigation:** **Output Validation and Cost Control.**  
    1. **Validation:** All AI-generated content (for StoryBeat.content) will be passed through a data validation and sanitization filter (e.g., nh3 81) before being stored.  
    2. **Cost Control (API4):** The Generation module will enforce strict max\_tokens limits.  
    3. **Rate Limiting:** As defined in 4.2, strict rate limiting 81 will be applied to all generative endpoints to prevent resource-consumption attacks.75

The NFR "ensure coherence in Manual Mode" 6 is not just a feature; it is a critical security control against **LLM09: Data Poisoning** of the knowledge graph.

* **Scenario:** The user, in "Manual Mode" 6, writes: "Marko (who hates dragons) flew a dragon to The Red Keep." This directly contradicts the knowledge graph.  
* **Problem:** If this StoryBeat is saved, and its entities are extracted (Section 2.3), the knowledge graph becomes corrupted. Future GraphRAG queries 24 will return contradictory information, poisoning the "inter-story inference".6  
* **Solution:** The Coherence module (from 1.3) *must* act as a firewall. When a "Manual Mode" beat is saved, it will:  
  1. Extract entities from the beat (Marko, dragon).  
  2. Perform a "dry-run" query on the graph (Section 2.3) to find contradictions (e.g., query for Marko \--\> dragon).  
  3. If a contradiction is found, the API will return a 200 OK but with a warning payload. The WebUI will then prompt the user: "This beat contradicts the fact 'Marko hates dragons.' Save anyway?" This fulfills the NFR without being dictatorial, while protecting the integrity of the graph.

## **5.0 Observability and Logging**

This section defines the strategy for system monitoring, debugging, and fulfilling the "Logged AI interactions" NFR.6 The system will implement the "three pillars of observability": Metrics, Logs, and Traces.87

### **5.1 Standard: OpenTelemetry (OTel)**

* **Decision:** The system will adopt **OpenTelemetry (OTel)** 48 as the *single, unified standard* for all instrumentation.  
* **Justification:** OTel is the Cloud Native Computing Foundation (CNCF) standard 48 and provides a single, vendor-neutral 48 set of SDKs for metrics, logs, and traces.87 This approach avoids the "fragmented stack" 10 of using Prometheus (metrics), Jaeger (traces), and ELK (logs).88 A fragmented stack requires maintaining multiple systems and makes correlating data (e.g., "what logs correspond to this trace?") extremely difficult.10

### **5.2 Backend Instrumentation (FastAPI)**

* **Automatic Instrumentation:** The opentelemetry-instrumentation-fastapi package 89 will be used. By running the application with opentelemetry-instrument 91 or calling FastAPIInstrumentor.instrument\_app(app) 89 at startup, the system will *automatically* get:  
  * **Traces:** A trace for every API request, showing its full lifecycle.  
  * **Metrics:** Standard request/error/duration (RED) metrics.  
  * **Logs:** Automatic exception logging, correlated with traces.  
* **Manual Instrumentation (AI Logging):**  
  * The NFR "Logged AI interactions" 6 cannot be met with a simple print() or file log. That data is "dumb" and lacks the context of the user request that triggered it.  
  * The correct implementation is a *custom OTel span*.89 This will wrap all calls to the external LLM API, recording the performance and content of the AI call *within the context of the parent request trace*.  
  * **Implementation (Code):**  
    Python  
    from opentelemetry import trace

    \# Get a tracer for this module  
    tracer \= trace.get\_tracer(\_\_name\_\_)

    async def call\_llm\_with\_tracing(prompt: str, world\_id: UUID):  
        \# Start a new custom span as a child of the main request trace  
        with tracer.start\_as\_current\_span("ai.generation") as span:  
            \# Log attributes for this specific interaction   
            span.set\_attribute("world.id", str(world\_id))  
            span.set\_attribute("ai.prompt.length", len(prompt))

            try:  
                \# This is the actual call to the LLM API  
                response\_text \= await external\_llm.generate(prompt)

                span.set\_attribute("ai.response.length", len(response\_text))  
                span.set\_attribute("otel.status\_code", "OK")  
                return response\_text  
            except Exception as e:  
                span.record\_exception(e)  
                span.set\_attribute("otel.status\_code", "ERROR")  
                raise e

  * This implementation 92 ties the AI log *directly* to the parent trace, allowing operators to pinpoint if a slow API response was due to internal code or a slow external LLM.92

### **5.3 Observability Platform: SigNoz**

* **Decision:** **SigNoz** 10 will be the unified observability backend (for both local-first and production).  
* **Justification:** SigNoz is an open-source, OTel-native 10 platform that is *designed* to receive OTel data. Unlike the fragmented stack 10, SigNoz provides a *single application and UI* for metrics, traces, and logs.10 This provides a "single pane of glass" and, most importantly, allows for seamless data *correlation*. An operator can click from a spike in a metric chart (e.g., "p99 latency high") to the *exact traces* causing it, and then to the *exact error logs* (including the custom AI span data) for that trace ID.10 This is the modern, superior workflow.

## **6.0 Documentation and Evolution**

This section defines the "living" documentation strategy, ensuring the architecture remains current and all decisions are recorded.

### **6.1 Architecture Documentation: Diagrams as Code**

* **Problem:** Architecture diagrams (like the C4 diagrams in this document) created in a drawing tool become static, outdated, and useless as they immediately fall out of sync with the code.3  
* **Solution:** The project will adopt the **"Diagrams as Code"** 49 philosophy.  
* **Tooling:** **Structurizr Lite**.50  
* **Justification:** Structurizr 4 is a toolset built *specifically* for the C4 model. The **Structurizr DSL** 49 allows the *model* (the components and their relationships) to be defined in a single workspace.dsl text file. This file will be version-controlled in Git alongside the source code.  
* **Benefits** 49:  
  1. **Single Source of Truth:** From this one DSL file, Structurizr Lite 50 can *generate* the System Context, Container, and Component diagrams.  
  2. **Model-Based:** This is superior to PlantUML/Mermaid 49, which are just text-to-image tools. Structurizr understands the *model*, so a change in one place (e.g., renaming a component) propagates to all diagrams.  
  3. **Local-First:** Structurizr Lite runs as a local web server 50, aligning with our "Local-friendly" 6 ethos.

### **6.2 Evolution: Architectural Decision Records (ADRs)**

* **Problem:** The *why* behind an architectural decision is often lost to time, leading to future teams questioning or reversing critical, well-considered choices.  
* **Solution:** The team will maintain **Architectural Decision Records (ADRs)**.51  
* **Implementation:** The team will use the ADR support built into Structurizr Lite.50 A new, immutable, markdown-based ADR file will be created for every significant architectural decision.  
* **Initial ADRs:**  
  * ADR-001: Choice of Modular Monolith Pattern 11  
  * ADR-002: Choice of FastAPI (Python) over NestJS (TS) 37  
  * ADR-003: Choice of SvelteKit for Frontend 38  
  * ADR-004: Choice of Supabase as the PostgreSQL and Auth Platform  
  * ADR-005: Stateless FastAPI Backend with Local Supabase JWT Validation  
  * ADR-006: OTel-Native (SigNoz) Observability Stack 10  
  * ADR-007: GraphRAG-in-SQL (Adjacency List) Schema 31

This practice, combined with the "Diagrams as Code" approach, ensures the Shinkei architecture remains a living, extensible, and well-understood blueprint, fulfilling all NFRs from the 6 specification.

#### **Sources des citations**

1. Diagrams | C4 model, consulté le novembre 14, 2025, [https://c4model.com/diagrams](https://c4model.com/diagrams)  
2. C4 model: Home, consulté le novembre 14, 2025, [https://c4model.com/](https://c4model.com/)  
3. Introduction | C4 model, consulté le novembre 14, 2025, [https://c4model.com/introduction](https://c4model.com/introduction)  
4. Understanding the C4 Model for Software Architecture Documentation | by Sheldon Cohen, consulté le novembre 14, 2025, [https://sheldonrcohen.medium.com/understanding-the-c4-model-for-software-architecture-documentation-e59c4edd0d56](https://sheldonrcohen.medium.com/understanding-the-c4-model-for-software-architecture-documentation-e59c4edd0d56)  
5. What is C4 Model? Complete Guide for Software Architecture \- Miro, consulté le novembre 14, 2025, [https://miro.com/diagramming/c4-model-for-software-architecture/](https://miro.com/diagramming/c4-model-for-software-architecture/)  
6. SHINKEI\_SPECS.md  
7. What is the difference between Svelte and Sveltekit (as a total beginner in frontent) \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1e8fptj/what\_is\_the\_difference\_between\_svelte\_and/](https://www.reddit.com/r/sveltejs/comments/1e8fptj/what_is_the_difference_between_svelte_and/)  
8. I'm building a SPA, should I use Svelte or SvelteKit? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1i612lz/im\_building\_a\_spa\_should\_i\_use\_svelte\_or\_sveltekit/](https://www.reddit.com/r/sveltejs/comments/1i612lz/im_building_a_spa_should_i_use_svelte_or_sveltekit/)  
9. Essential API Tools & Frameworks for Success in 2025 | Zuplo Learning Center, consulté le novembre 14, 2025, [https://zuplo.com/learning-center/emerging-tools-frameworks](https://zuplo.com/learning-center/emerging-tools-frameworks)  
10. Best Microservices Monitoring Tools in 2025: Open-Source vs. SaaS ..., consulté le novembre 14, 2025, [https://signoz.io/comparisons/microservices-monitoring-tools/](https://signoz.io/comparisons/microservices-monitoring-tools/)  
11. What is better? Modular Monolith vs Microservices | by Miłosz ..., consulté le novembre 14, 2025, [https://medium.com/codex/what-is-better-modular-monolith-vs-microservices-994e1ec70994](https://medium.com/codex/what-is-better-modular-monolith-vs-microservices-994e1ec70994)  
12. Monolithic vs Microservices \- Difference Between Software Development Architectures, consulté le novembre 14, 2025, [https://aws.amazon.com/compare/the-difference-between-monolithic-and-microservices-architecture/](https://aws.amazon.com/compare/the-difference-between-monolithic-and-microservices-architecture/)  
13. Microservices vs. monolithic architecture \- Atlassian, consulté le novembre 14, 2025, [https://www.atlassian.com/microservices/microservices-architecture/microservices-vs-monolith](https://www.atlassian.com/microservices/microservices-architecture/microservices-vs-monolith)  
14. Monolith vs. Microservices: What's Your Take? : r/softwarearchitecture \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/softwarearchitecture/comments/1eflqzl/monolith\_vs\_microservices\_whats\_your\_take/](https://www.reddit.com/r/softwarearchitecture/comments/1eflqzl/monolith_vs_microservices_whats_your_take/)  
15. FastAPI Best Practices and Conventions we used at our startup \- GitHub, consulté le novembre 14, 2025, [https://github.com/zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)  
16. How to Structure Your FastAPI Projects \- Medium, consulté le novembre 14, 2025, [https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f](https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f)  
17. evolutionary-architecture/evolutionary-architecture-by-example: Navigate the complex landscape of .NET software architecture with our step-by-step, story-like guide. Unpack the interplay between modular monoliths, microservices, domain-driven design, and various architectural patterns. Go beyond the one-size-fits \- GitHub, consulté le novembre 14, 2025, [https://github.com/evolutionary-architecture/evolutionary-architecture-by-example](https://github.com/evolutionary-architecture/evolutionary-architecture-by-example)  
18. Bigger Applications \- Multiple Files \- FastAPI, consulté le novembre 14, 2025, [https://fastapi.tiangolo.com/tutorial/bigger-applications/](https://fastapi.tiangolo.com/tutorial/bigger-applications/)  
19. How to build a scalable project file structure for a beginner. : r/FastAPI \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/FastAPI/comments/11nu9sw/how\_to\_build\_a\_scalable\_project\_file\_structure/](https://www.reddit.com/r/FastAPI/comments/11nu9sw/how_to_build_a_scalable_project_file_structure/)  
20. What Is a Logical Data Model? \- GoodData, consulté le novembre 14, 2025, [https://www.gooddata.com/blog/how-build-logical-data-models-scale-analytical-applications/](https://www.gooddata.com/blog/how-build-logical-data-models-scale-analytical-applications/)  
21. Logical vs Physical Data Model \- Difference in Data Modeling \- Amazon AWS, consulté le novembre 14, 2025, [https://aws.amazon.com/compare/the-difference-between-logical-and-physical-data-model/](https://aws.amazon.com/compare/the-difference-between-logical-and-physical-data-model/)  
22. Why Start with a Logical Data Model | by Vedran Bilopavlović \- Medium, consulté le novembre 14, 2025, [https://medium.com/@vbilopav/why-start-with-a-logical-data-model-b1fb786ebbf1](https://medium.com/@vbilopav/why-start-with-a-logical-data-model-b1fb786ebbf1)  
23. How to Design a Database Schema | Miro, consulté le novembre 14, 2025, [https://miro.com/diagramming/how-to-design-database-schema/](https://miro.com/diagramming/how-to-design-database-schema/)  
24. consulté le novembre 14, 2025, [https://arxiv.org/abs/2502.11371\#:\~:text=Retrieval%2DAugmented%20Generation%20(RAG),used%20to%20retrieve%20relevant%20information.](https://arxiv.org/abs/2502.11371#:~:text=Retrieval%2DAugmented%20Generation%20\(RAG\),used%20to%20retrieve%20relevant%20information.)  
25. \[2502.11371\] RAG vs. GraphRAG: A Systematic Evaluation and Key Insights \- arXiv, consulté le novembre 14, 2025, [https://arxiv.org/abs/2502.11371](https://arxiv.org/abs/2502.11371)  
26. \[2501.00309\] Retrieval-Augmented Generation with Graphs (GraphRAG) \- arXiv, consulté le novembre 14, 2025, [https://arxiv.org/abs/2501.00309](https://arxiv.org/abs/2501.00309)  
27. Graph RAG vs SQL RAG \- Towards Data Science, consulté le novembre 14, 2025, [https://towardsdatascience.com/graph-rag-vs-sql-rag/](https://towardsdatascience.com/graph-rag-vs-sql-rag/)  
28. How to use graphrag with other database and structured data? \#1679 \- GitHub, consulté le novembre 14, 2025, [https://github.com/microsoft/graphrag/discussions/1679](https://github.com/microsoft/graphrag/discussions/1679)  
29. PostgreSQL CTE statement for graph database \- Stack Overflow, consulté le novembre 14, 2025, [https://stackoverflow.com/questions/33193046/postgresql-cte-statement-for-graph-database](https://stackoverflow.com/questions/33193046/postgresql-cte-statement-for-graph-database)  
30. SQLGraph: An Efficient Relational-Based Property Graph Store \- Google Research, consulté le novembre 14, 2025, [https://research.google.com/pubs/archive/43287.pdf](https://research.google.com/pubs/archive/43287.pdf)  
31. Best practices for managing many-to-many relationships in DynamoDB tables, consulté le novembre 14, 2025, [https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-adjacency-graphs.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-adjacency-graphs.html)  
32. Graph Data Processing with SQL Server 2017 and Azure SQL Database \- Microsoft, consulté le novembre 14, 2025, [https://www.microsoft.com/en-us/sql-server/blog/2017/04/20/graph-data-processing-with-sql-server-2017/](https://www.microsoft.com/en-us/sql-server/blog/2017/04/20/graph-data-processing-with-sql-server-2017/)  
33. sql \- Timeline database schema? \- Stack Overflow, consulté le novembre 14, 2025, [https://stackoverflow.com/questions/25125401/timeline-database-schema](https://stackoverflow.com/questions/25125401/timeline-database-schema)  
34. Safely making database schema changes \- PlanetScale, consulté le novembre 14, 2025, [https://planetscale.com/blog/safely-making-database-schema-changes](https://planetscale.com/blog/safely-making-database-schema-changes)  
35. Database Schema Design: Principles Every Developer Must Know \- Medium, consulté le novembre 14, 2025, [https://medium.com/@artemkhrenov/database-schema-design-principles-every-developer-must-know-fee567414f6d](https://medium.com/@artemkhrenov/database-schema-design-principles-every-developer-must-know-fee567414f6d)  
36. How to Make Database Changes Without Breaking Everything \- Brent Ozar Unlimited®, consulté le novembre 14, 2025, [https://www.brentozar.com/archive/2023/06/how-to-make-database-changes-without-breaking-everything/](https://www.brentozar.com/archive/2023/06/how-to-make-database-changes-without-breaking-everything/)  
37. Battle of the Backends: FastAPI vs. Node.js \- HostAdvice, consulté le novembre 14, 2025, [https://hostadvice.com/blog/web-hosting/node-js/fastapi-vs-nodejs/](https://hostadvice.com/blog/web-hosting/node-js/fastapi-vs-nodejs/)  
38. Comparing front-end frameworks for startups in 2025: Svelte vs React vs Vue \- Merge Rocks, consulté le novembre 14, 2025, [https://merge.rocks/blog/comparing-front-end-frameworks-for-startups-in-2025-svelte-vs-react-vs-vue](https://merge.rocks/blog/comparing-front-end-frameworks-for-startups-in-2025-svelte-vs-react-vs-vue)  
39. React vs Vue vs Svelte: Choosing the Right Framework for 2025 \- Medium, consulté le novembre 14, 2025, [https://medium.com/@ignatovich.dm/react-vs-vue-vs-svelte-choosing-the-right-framework-for-2025-4f4bb9da35b4](https://medium.com/@ignatovich.dm/react-vs-vue-vs-svelte-choosing-the-right-framework-for-2025-4f4bb9da35b4)  
40. Why Learn Svelte in 2025? The Value Proposition & Svelte vs React & Vue, consulté le novembre 14, 2025, [https://dev.to/a1guy/why-learn-svelte-in-2025-the-value-proposition-svelte-vs-react-vue-1bhc](https://dev.to/a1guy/why-learn-svelte-in-2025-the-value-proposition-svelte-vs-react-vue-1bhc)  
41. Introducing Svelte, and Comparing Svelte with React and Vue \- Josh Collinsworth blog, consulté le novembre 14, 2025, [https://joshcollinsworth.com/blog/introducing-svelte-comparing-with-react-vue](https://joshcollinsworth.com/blog/introducing-svelte-comparing-with-react-vue)  
42. Best 15 Svelte UI Components & Libraries for Enterprise-Grade Apps \- DEV Community, consulté le novembre 14, 2025, [https://dev.to/olga\_tash/best-15-svelte-ui-components-libraries-for-enterprise-grade-apps-23gc](https://dev.to/olga_tash/best-15-svelte-ui-components-libraries-for-enterprise-grade-apps-23gc)  
43. 7 Hottest Animated UI Component Libraries of 2025 \- Copy and Paste \- DesignerUp, consulté le novembre 14, 2025, [https://designerup.co/blog/copy-and-paste-ui-component-libraries/](https://designerup.co/blog/copy-and-paste-ui-component-libraries/)  
44. 2025 Inspiration UI Design: Top 10 Trends \- Bookmarkify, consulté le novembre 14, 2025, [https://www.bookmarkify.io/blog/inspiration-ui-design](https://www.bookmarkify.io/blog/inspiration-ui-design)  
45. 10 UI/UX Design Trends That Will Dominate 2025 & Beyond \- BootstrapDash, consulté le novembre 14, 2025, [https://www.bootstrapdash.com/blog/ui-ux-design-trends](https://www.bootstrapdash.com/blog/ui-ux-design-trends)  
46. SQL (Relational) Databases \- FastAPI, consulté le novembre 14, 2025, [https://fastapi.tiangolo.com/tutorial/sql-databases/](https://fastapi.tiangolo.com/tutorial/sql-databases/)  
47. How to build a FastAPI app with PostgreSQL \- YouTube, consulté le novembre 14, 2025, [https://www.youtube.com/watch?v=398DuQbQJq0](https://www.youtube.com/watch?v=398DuQbQJq0)  
48. OpenTelemetry in 2025: The Backbone of Full-Stack Observability for Container Environments | by ServerWala InfraNet FZ-LLC | Medium, consulté le novembre 14, 2025, [https://medium.com/@serverwalainfra/opentelemetry-in-2025-the-backbone-of-full-stack-observability-for-container-environments-619d44135a5a](https://medium.com/@serverwalainfra/opentelemetry-in-2025-the-backbone-of-full-stack-observability-for-container-environments-619d44135a5a)  
49. Structurizr DSL, consulté le novembre 14, 2025, [https://docs.structurizr.com/dsl](https://docs.structurizr.com/dsl)  
50. Getting started with Structurizr Lite \- DEV Community, consulté le novembre 14, 2025, [https://dev.to/simonbrown/getting-started-with-structurizr-lite-27d0](https://dev.to/simonbrown/getting-started-with-structurizr-lite-27d0)  
51. bflorat/architecture-document-template \- GitHub, consulté le novembre 14, 2025, [https://github.com/bflorat/architecture-document-template](https://github.com/bflorat/architecture-document-template)  
52. Why Choose Svelte Over Vue or React? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1jy4m01/why\_choose\_svelte\_over\_vue\_or\_react/](https://www.reddit.com/r/sveltejs/comments/1jy4m01/why_choose_svelte_over_vue_or_react/)  
53. React vs. Vue vs. Svelte: The Real 2025 Guide to Picking Your First JavaScript Framework, consulté le novembre 14, 2025, [https://clinkitsolutions.com/react-vs-vue-vs-svelte-the-real-2025-guide-to-picking-your-first-javascript-framework/](https://clinkitsolutions.com/react-vs-vue-vs-svelte-the-real-2025-guide-to-picking-your-first-javascript-framework/)  
54. Getting started with Svelte \- Learn web development | MDN, consulté le novembre 14, 2025, [https://developer.mozilla.org/en-US/docs/Learn\_web\_development/Core/Frameworks\_libraries/Svelte\_getting\_started](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Frameworks_libraries/Svelte_getting_started)  
55. When should I use SvelteKit and when should I use plain Vite? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/110kzpw/when\_should\_i\_use\_sveltekit\_and\_when\_should\_i\_use/](https://www.reddit.com/r/sveltejs/comments/110kzpw/when_should_i_use_sveltekit_and_when_should_i_use/)  
56. Top 10 Svelte UI Libraries in 2025 \- WeAreDevelopers, consulté le novembre 14, 2025, [https://www.wearedevelopers.com/en/magazine/250/top-svelte-ui-libraries](https://www.wearedevelopers.com/en/magazine/250/top-svelte-ui-libraries)  
57. What's your go to modern UI component library? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1j38oqu/whats\_your\_go\_to\_modern\_ui\_component\_library/](https://www.reddit.com/r/sveltejs/comments/1j38oqu/whats_your_go_to_modern_ui_component_library/)  
58. Best UI/UX Design Trends to Follow in 2025 | by Rahim Ladhani \- Medium, consulté le novembre 14, 2025, [https://nevinainfotech25.medium.com/best-ui-ux-design-trends-to-follow-in-2025-c31d3e62779c](https://nevinainfotech25.medium.com/best-ui-ux-design-trends-to-follow-in-2025-c31d3e62779c)  
59. “State Management: How Svelte Makes It Effortless” | by Pratyush Pavan | Medium, consulté le novembre 14, 2025, [https://medium.com/@pratyushpavanchoudhary/state-management-simplified-sveltes-approach-10a18854337a](https://medium.com/@pratyushpavanchoudhary/state-management-simplified-sveltes-approach-10a18854337a)  
60. Recommendation and opinions on management of complex state in Svelte. \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/rtxcsq/recommendation\_and\_opinions\_on\_management\_of/](https://www.reddit.com/r/sveltejs/comments/rtxcsq/recommendation_and_opinions_on_management_of/)  
61. How do you handle state management in Svelte, and what libraries or approaches do you prefer? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1gqhyoz/how\_do\_you\_handle\_state\_management\_in\_svelte\_and/](https://www.reddit.com/r/sveltejs/comments/1gqhyoz/how_do_you_handle_state_management_in_svelte_and/)  
62. How to implement light/dark theme the Svelte way? : r/sveltejs \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/sveltejs/comments/1nfttkz/how\_to\_implement\_lightdark\_theme\_the\_svelte\_way/](https://www.reddit.com/r/sveltejs/comments/1nfttkz/how_to_implement_lightdark_theme_the_svelte_way/)  
63. How to detect light or dark mode at the OS level with JavaScript \- Rob Kendal, consulté le novembre 14, 2025, [https://robkendal.co.uk/blog/2024-11-21-detecting-os-level-dark-mode/](https://robkendal.co.uk/blog/2024-11-21-detecting-os-level-dark-mode/)  
64. Best Backend Frameworks for 2025 and Beyond | by Temka B \- Medium, consulté le novembre 14, 2025, [https://medium.com/@thxdeadshotxht/best-backend-frameworks-for-2025-and-beyond-9c175af01409](https://medium.com/@thxdeadshotxht/best-backend-frameworks-for-2025-and-beyond-9c175af01409)  
65. NestJS vs. FastAPI: which one's better to specialize in for backend? : r/PinoyProgrammer, consulté le novembre 14, 2025, [https://www.reddit.com/r/PinoyProgrammer/comments/1nurt7z/nestjs\_vs\_fastapi\_alin\_mas\_okay\_ispecialize\_for/?tl=en](https://www.reddit.com/r/PinoyProgrammer/comments/1nurt7z/nestjs_vs_fastapi_alin_mas_okay_ispecialize_for/?tl=en)  
66. Real world scenario FastAPI vs Node.js k8s cluster benchmarks \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/FastAPI/comments/1hyfuob/real\_world\_scenario\_fastapi\_vs\_nodejs\_k8s\_cluster/](https://www.reddit.com/r/FastAPI/comments/1hyfuob/real_world_scenario_fastapi_vs_nodejs_k8s_cluster/)  
67. Ultimate Guide to Choosing the Best Backend Framework for AI Integration in 2024, consulté le novembre 14, 2025, [https://slashdev.io/se/-ultimate-guide-to-choosing-the-best-backend-framework-for-ai-integration-in-2024](https://slashdev.io/se/-ultimate-guide-to-choosing-the-best-backend-framework-for-ai-integration-in-2024)  
68. LocalAI, consulté le novembre 14, 2025, [https://localai.io/](https://localai.io/)  
69. Fastapi to read from an existing database table in postgreSQL \- Stack Overflow, consulté le novembre 14, 2025, [https://stackoverflow.com/questions/71235905/fastapi-to-read-from-an-existing-database-table-in-postgresql](https://stackoverflow.com/questions/71235905/fastapi-to-read-from-an-existing-database-table-in-postgresql)  
70. Documentation: 18: 7.8. WITH Queries (Common Table ... \- PostgreSQL, consulté le novembre 14, 2025, [https://www.postgresql.org/docs/current/queries-with.html](https://www.postgresql.org/docs/current/queries-with.html)  
71. PostgreSQL as a Graph Database: Recursive Queries for Hierarchical Data | by Rizqi Mulki, consulté le novembre 14, 2025, [https://rizqimulki.com/postgresql-as-a-graph-database-recursive-queries-for-hierarchical-data-706dda4e788e](https://rizqimulki.com/postgresql-as-a-graph-database-recursive-queries-for-hierarchical-data-706dda4e788e)  
72. Question: What is the performance of a Postgres recursive query with a large depth on millions of rows? Should I use a graph database instead? \- Reddit, consulté le novembre 14, 2025, [https://www.reddit.com/r/Database/comments/siyakr/question\_what\_is\_the\_performance\_of\_a\_postgres/](https://www.reddit.com/r/Database/comments/siyakr/question_what_is_the_performance_of_a_postgres/)  
73. PostgreSQL Graph Database: Everything You Need To Know \- PuppyGraph, consulté le novembre 14, 2025, [https://www.puppygraph.com/blog/postgresql-graph-database](https://www.puppygraph.com/blog/postgresql-graph-database)  
74. OWASP Top Ten, consulté le novembre 14, 2025, [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)  
75. OWASP Top 10 API Security Risks – 2023, consulté le novembre 14, 2025, [https://owasp.org/API-Security/editions/2023/en/0x11-t10/](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)  
76. OWASP API Security Project, consulté le novembre 14, 2025, [https://owasp.org/www-project-api-security/](https://owasp.org/www-project-api-security/)  
77. Session vs JWT vs OAuth2: The Complete Authentication Strategy | HackerNoon, consulté le novembre 14, 2025, [https://hackernoon.com/session-vs-jwt-vs-oauth2-the-complete-authentication-strategy](https://hackernoon.com/session-vs-jwt-vs-oauth2-the-complete-authentication-strategy)  
78. How do I validate a JWT that's sent as an HttpOnly cookie in FastAPI? \- Stack Overflow, consulté le novembre 14, 2025, [https://stackoverflow.com/questions/74634957/how-do-i-validate-a-jwt-thats-sent-as-an-httponly-cookie-in-fastapi](https://stackoverflow.com/questions/74634957/how-do-i-validate-a-jwt-thats-sent-as-an-httponly-cookie-in-fastapi)  
79. Nodejs Security \- OWASP Cheat Sheet Series, consulté le novembre 14, 2025, [https://cheatsheetseries.owasp.org/cheatsheets/Nodejs\_Security\_Cheat\_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html)  
80. Best Security implementation Practices In NestJS. A Comprehensive Guide, consulté le novembre 14, 2025, [https://dev.to/drbenzene/best-security-implementation-practices-in-nestjs-a-comprehensive-guide-2p88](https://dev.to/drbenzene/best-security-implementation-practices-in-nestjs-a-comprehensive-guide-2p88)  
81. How to secure APIs built with FastAPI: A complete guide \- Escape.tech, consulté le novembre 14, 2025, [https://escape.tech/blog/how-to-secure-fastapi-api/](https://escape.tech/blog/how-to-secure-fastapi-api/)  
82. Web API Security Champion: Broken Object Level Authorization (OWASP TOP 10), consulté le novembre 14, 2025, [https://devsec-blog.com/2024/04/web-api-security-champion-broken-object-level-authorization-owasp-top-10/](https://devsec-blog.com/2024/04/web-api-security-champion-broken-object-level-authorization-owasp-top-10/)  
83. Web API Security Champion Part III: Broken Object Property Level Authorization | CodeX, consulté le novembre 14, 2025, [https://medium.com/codex/web-api-security-champion-part-iii-broken-object-property-level-authorization-owasp-top-10-f6246273aef7](https://medium.com/codex/web-api-security-champion-part-iii-broken-object-property-level-authorization-owasp-top-10-f6246273aef7)  
84. API3:2023 Broken Object Property Level Authorization \- OWASP API Security Top 10, consulté le novembre 14, 2025, [https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)  
85. What is Broken Object Level Authorization (BOLA) \- Imperva, consulté le novembre 14, 2025, [https://www.imperva.com/learn/application-security/broken-object-level-authorization-bola/](https://www.imperva.com/learn/application-security/broken-object-level-authorization-bola/)  
86. OWASP Top 10 for Large Language Model Applications, consulté le novembre 14, 2025, [https://owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)  
87. What is Observability? Metrics, Logs & Traces Overview \- Spacelift, consulté le novembre 14, 2025, [https://spacelift.io/blog/observability-metrics-logs-traces](https://spacelift.io/blog/observability-metrics-logs-traces)  
88. Top 8 Observability Tools for 2025: Go from Data to Action \- Groundcover, consulté le novembre 14, 2025, [https://www.groundcover.com/blog/observability-tools](https://www.groundcover.com/blog/observability-tools)  
89. A Complete Guide to Integrating OpenTelemetry with FastAPI \- Last9, consulté le novembre 14, 2025, [https://last9.io/blog/integrating-opentelemetry-with-fastapi/](https://last9.io/blog/integrating-opentelemetry-with-fastapi/)  
90. OpenTelemetry FastAPI Instrumentation, consulté le novembre 14, 2025, [https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)  
91. Implementing OpenTelemetry in FastAPI \- A Practical Guide | SigNoz, consulté le novembre 14, 2025, [https://signoz.io/blog/opentelemetry-fastapi/](https://signoz.io/blog/opentelemetry-fastapi/)  
92. OpenTelemetry FastAPI Tutorial: Get GREAT App Performance NOW\! \- YouTube, consulté le novembre 14, 2025, [https://www.youtube.com/watch?v=m28TTogdcbk](https://www.youtube.com/watch?v=m28TTogdcbk)  
93. Structurizr Lite, consulté le novembre 14, 2025, [https://docs.structurizr.com/lite](https://docs.structurizr.com/lite)  
94. Structurizr Lite \- GitHub, consulté le novembre 14, 2025, [https://github.com/structurizr/lite](https://github.com/structurizr/lite)  
95. Diagrams as Code : Creating C4 model diagrams with Structurizr DSL \+ Spring Boot locally, consulté le novembre 14, 2025, [https://www.reddit.com/r/java/comments/1nzr46r/diagrams\_as\_code\_creating\_c4\_model\_diagrams\_with/](https://www.reddit.com/r/java/comments/1nzr46r/diagrams_as_code_creating_c4_model_diagrams_with/)  
96. donnemartin/system-design-primer: Learn how to design large-scale systems. Prep for the system design interview. Includes Anki flashcards. \- GitHub, consulté le novembre 14, 2025, [https://github.com/donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)