--
-- PostgreSQL database dump
--

\restrict rgBJfmN50iJifW1eEauV1BeGbr8SfnleiEGWJrfHnLyhSsd93APFNGWwAh3b1zC

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: shinkei_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO shinkei_user;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: shinkei_user
--

COMMENT ON SCHEMA public IS '';


--
-- Name: authoringmode; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.authoringmode AS ENUM (
    'AUTONOMOUS',
    'COLLABORATIVE',
    'MANUAL'
);


ALTER TYPE public.authoringmode OWNER TO shinkei_user;

--
-- Name: beattype; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.beattype AS ENUM (
    'SCENE',
    'SUMMARY',
    'NOTE'
);


ALTER TYPE public.beattype OWNER TO shinkei_user;

--
-- Name: chronologymode; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.chronologymode AS ENUM (
    'LINEAR',
    'FRAGMENTED',
    'TIMELESS'
);


ALTER TYPE public.chronologymode OWNER TO shinkei_user;

--
-- Name: conversationtype; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.conversationtype AS ENUM (
    'WORLD_CHAT',
    'BEAT_DISCUSSION',
    'STORY_PLANNING'
);


ALTER TYPE public.conversationtype OWNER TO shinkei_user;

--
-- Name: generatedby; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.generatedby AS ENUM (
    'AI',
    'USER',
    'COLLABORATIVE'
);


ALTER TYPE public.generatedby OWNER TO shinkei_user;

--
-- Name: povtype; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.povtype AS ENUM (
    'FIRST',
    'THIRD',
    'OMNISCIENT'
);


ALTER TYPE public.povtype OWNER TO shinkei_user;

--
-- Name: storystatus; Type: TYPE; Schema: public; Owner: shinkei_user
--

CREATE TYPE public.storystatus AS ENUM (
    'DRAFT',
    'ACTIVE',
    'COMPLETED',
    'ARCHIVED'
);


ALTER TYPE public.storystatus OWNER TO shinkei_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO shinkei_user;

--
-- Name: beat_modifications; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.beat_modifications (
    id character varying(36) NOT NULL,
    beat_id character varying(36) NOT NULL,
    original_content text NOT NULL,
    modified_content text NOT NULL,
    original_summary text,
    modified_summary text,
    original_time_label character varying(100),
    modified_time_label character varying(100),
    original_world_event_id character varying(36),
    modified_world_event_id character varying(36),
    modification_instructions text NOT NULL,
    reasoning text,
    unified_diff text,
    applied boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.beat_modifications OWNER TO shinkei_user;

--
-- Name: COLUMN beat_modifications.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.id IS 'Modification UUID';


--
-- Name: COLUMN beat_modifications.beat_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.beat_id IS 'Beat being modified';


--
-- Name: COLUMN beat_modifications.original_content; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.original_content IS 'Original beat content';


--
-- Name: COLUMN beat_modifications.modified_content; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.modified_content IS 'Modified beat content';


--
-- Name: COLUMN beat_modifications.original_summary; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.original_summary IS 'Original beat summary';


--
-- Name: COLUMN beat_modifications.modified_summary; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.modified_summary IS 'Modified beat summary';


--
-- Name: COLUMN beat_modifications.original_time_label; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.original_time_label IS 'Original time label';


--
-- Name: COLUMN beat_modifications.modified_time_label; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.modified_time_label IS 'Modified time label';


--
-- Name: COLUMN beat_modifications.original_world_event_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.original_world_event_id IS 'Original world event link';


--
-- Name: COLUMN beat_modifications.modified_world_event_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.modified_world_event_id IS 'Modified world event link';


--
-- Name: COLUMN beat_modifications.modification_instructions; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.modification_instructions IS 'User instructions for modification';


--
-- Name: COLUMN beat_modifications.reasoning; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.reasoning IS 'AI reasoning for changes';


--
-- Name: COLUMN beat_modifications.unified_diff; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.unified_diff IS 'Unified diff of changes';


--
-- Name: COLUMN beat_modifications.applied; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.applied IS 'Whether modification was applied';


--
-- Name: COLUMN beat_modifications.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.beat_modifications.created_at IS 'Timestamp of modification';


--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.conversation_messages (
    id character varying(36) NOT NULL,
    conversation_id character varying(36) NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    reasoning text,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.conversation_messages OWNER TO shinkei_user;

--
-- Name: COLUMN conversation_messages.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.id IS 'Message UUID';


--
-- Name: COLUMN conversation_messages.conversation_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.conversation_id IS 'Conversation ID this message belongs to';


--
-- Name: COLUMN conversation_messages.role; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.role IS 'Message role: user, assistant, or system';


--
-- Name: COLUMN conversation_messages.content; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.content IS 'Message text content';


--
-- Name: COLUMN conversation_messages.reasoning; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.reasoning IS 'AI reasoning/thoughts (for assistant messages)';


--
-- Name: COLUMN conversation_messages.metadata; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.metadata IS 'Additional metadata (model used, tokens, etc.)';


--
-- Name: COLUMN conversation_messages.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversation_messages.created_at IS 'Timestamp of creation';


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.conversations (
    id character varying(36) NOT NULL,
    world_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    type public.conversationtype NOT NULL,
    title character varying(255),
    context_summary text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.conversations OWNER TO shinkei_user;

--
-- Name: COLUMN conversations.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.id IS 'Conversation UUID';


--
-- Name: COLUMN conversations.world_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.world_id IS 'World ID this conversation belongs to';


--
-- Name: COLUMN conversations.user_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.user_id IS 'User ID who owns this conversation';


--
-- Name: COLUMN conversations.type; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.type IS 'Type of conversation';


--
-- Name: COLUMN conversations.title; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.title IS 'Optional conversation title';


--
-- Name: COLUMN conversations.context_summary; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.context_summary IS 'Rolling summary for context window management';


--
-- Name: COLUMN conversations.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN conversations.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.conversations.updated_at IS 'Timestamp of last update';


--
-- Name: stories; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.stories (
    id character varying(36) NOT NULL,
    world_id character varying(36) NOT NULL,
    title character varying(255) NOT NULL,
    synopsis text,
    theme character varying(255),
    status public.storystatus NOT NULL,
    mode public.authoringmode NOT NULL,
    pov_type public.povtype NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.stories OWNER TO shinkei_user;

--
-- Name: COLUMN stories.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.id IS 'Story UUID';


--
-- Name: COLUMN stories.world_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.world_id IS 'World ID this story belongs to';


--
-- Name: COLUMN stories.title; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.title IS 'Story title';


--
-- Name: COLUMN stories.synopsis; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.synopsis IS 'Brief summary';


--
-- Name: COLUMN stories.theme; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.theme IS 'Central theme';


--
-- Name: COLUMN stories.status; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.status IS 'Current status';


--
-- Name: COLUMN stories.mode; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.mode IS 'Authoring mode (autonomous/collaborative/manual)';


--
-- Name: COLUMN stories.pov_type; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.pov_type IS 'Point of view type for narrative';


--
-- Name: COLUMN stories.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN stories.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.stories.updated_at IS 'Timestamp of last update';


--
-- Name: story_beats; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.story_beats (
    id character varying(36) NOT NULL,
    story_id character varying(36) NOT NULL,
    order_index integer NOT NULL,
    content text NOT NULL,
    type public.beattype NOT NULL,
    world_event_id character varying(36),
    generated_by public.generatedby NOT NULL,
    summary text,
    local_time_label character varying(255),
    generation_reasoning text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.story_beats OWNER TO shinkei_user;

--
-- Name: COLUMN story_beats.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.id IS 'StoryBeat UUID';


--
-- Name: COLUMN story_beats.story_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.story_id IS 'Story ID this beat belongs to';


--
-- Name: COLUMN story_beats.order_index; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.order_index IS 'Ordering within the story';


--
-- Name: COLUMN story_beats.content; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.content IS 'The actual text content';


--
-- Name: COLUMN story_beats.type; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.type IS 'Beat type';


--
-- Name: COLUMN story_beats.world_event_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.world_event_id IS 'Optional link to a canonical world event';


--
-- Name: COLUMN story_beats.generated_by; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.generated_by IS 'Source of beat generation (ai/user/collaborative)';


--
-- Name: COLUMN story_beats.summary; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.summary IS 'Short summary for UI display (auto-generated for AI beats)';


--
-- Name: COLUMN story_beats.local_time_label; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.local_time_label IS 'In-world narrative timestamp (e.g., ''Day 3'', ''Log 0017'')';


--
-- Name: COLUMN story_beats.generation_reasoning; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.generation_reasoning IS 'AI reasoning/thoughts behind beat generation';


--
-- Name: COLUMN story_beats.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN story_beats.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.story_beats.updated_at IS 'Timestamp of last update';


--
-- Name: users; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.users (
    id character varying(36) NOT NULL,
    email character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    settings json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO shinkei_user;

--
-- Name: COLUMN users.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.id IS 'UUID from Supabase Auth';


--
-- Name: COLUMN users.email; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.email IS 'User email address';


--
-- Name: COLUMN users.name; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.name IS 'Display name';


--
-- Name: COLUMN users.settings; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.settings IS 'User preferences (language, theme, default_model, etc.)';


--
-- Name: COLUMN users.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN users.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.users.updated_at IS 'Timestamp of last update';


--
-- Name: world_events; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.world_events (
    id character varying(36) NOT NULL,
    world_id character varying(36) NOT NULL,
    t double precision NOT NULL,
    label_time character varying(255) NOT NULL,
    location_id character varying(36),
    type character varying(100) NOT NULL,
    summary text NOT NULL,
    tags character varying[] NOT NULL,
    caused_by_ids character varying[] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.world_events OWNER TO shinkei_user;

--
-- Name: COLUMN world_events.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.id IS 'WorldEvent UUID';


--
-- Name: COLUMN world_events.world_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.world_id IS 'World ID this event belongs to';


--
-- Name: COLUMN world_events.t; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.t IS 'Objective timestamp in world time';


--
-- Name: COLUMN world_events.label_time; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.label_time IS 'Human-readable time label';


--
-- Name: COLUMN world_events.location_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.location_id IS 'Location reference (for future GraphRAG)';


--
-- Name: COLUMN world_events.type; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.type IS 'Event type (incident, glitch, meeting, etc.)';


--
-- Name: COLUMN world_events.summary; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.summary IS 'Brief description of the event';


--
-- Name: COLUMN world_events.tags; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.tags IS 'Tags for categorization';


--
-- Name: COLUMN world_events.caused_by_ids; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.caused_by_ids IS 'IDs of events that caused this event (dependency graph)';


--
-- Name: COLUMN world_events.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN world_events.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.world_events.updated_at IS 'Timestamp of last update';


--
-- Name: worlds; Type: TABLE; Schema: public; Owner: shinkei_user
--

CREATE TABLE public.worlds (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    tone character varying(500),
    backdrop text,
    laws json NOT NULL,
    chronology_mode public.chronologymode NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.worlds OWNER TO shinkei_user;

--
-- Name: COLUMN worlds.id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.id IS 'World UUID';


--
-- Name: COLUMN worlds.user_id; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.user_id IS 'Owner user ID';


--
-- Name: COLUMN worlds.name; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.name IS 'World name';


--
-- Name: COLUMN worlds.description; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.description IS 'General pitch/summary';


--
-- Name: COLUMN worlds.tone; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.tone IS 'Narrative tone';


--
-- Name: COLUMN worlds.backdrop; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.backdrop IS 'World bible, overarching lore';


--
-- Name: COLUMN worlds.laws; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.laws IS 'World rules (physics, metaphysics, social, forbidden)';


--
-- Name: COLUMN worlds.chronology_mode; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.chronology_mode IS 'How time flows in this world';


--
-- Name: COLUMN worlds.created_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.created_at IS 'Timestamp of creation';


--
-- Name: COLUMN worlds.updated_at; Type: COMMENT; Schema: public; Owner: shinkei_user
--

COMMENT ON COLUMN public.worlds.updated_at IS 'Timestamp of last update';


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.alembic_version (version_num) FROM stdin;
f94378c3be57
\.


--
-- Data for Name: beat_modifications; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.beat_modifications (id, beat_id, original_content, modified_content, original_summary, modified_summary, original_time_label, modified_time_label, original_world_event_id, modified_world_event_id, modification_instructions, reasoning, unified_diff, applied, created_at) FROM stdin;
\.


--
-- Data for Name: conversation_messages; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.conversation_messages (id, conversation_id, role, content, reasoning, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.conversations (id, world_id, user_id, type, title, context_summary, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: stories; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.stories (id, world_id, title, synopsis, theme, status, mode, pov_type, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: story_beats; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.story_beats (id, story_id, order_index, content, type, world_event_id, generated_by, summary, local_time_label, generation_reasoning, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.users (id, email, name, settings, created_at, updated_at) FROM stdin;
417ab547-94d7-4eec-9443-1e6492a870c5	matthias.vaytet@gmail.com	matthias.vaytet	{"language": "en", "ui_theme": "system", "llm_provider": "openai", "llm_model": "gpt-4o", "llm_base_url": null}	2025-11-21 09:01:24.246266+00	2025-11-21 09:01:24.246266+00
\.


--
-- Data for Name: world_events; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.world_events (id, world_id, t, label_time, location_id, type, summary, tags, caused_by_ids, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: worlds; Type: TABLE DATA; Schema: public; Owner: shinkei_user
--

COPY public.worlds (id, user_id, name, description, tone, backdrop, laws, chronology_mode, created_at, updated_at) FROM stdin;
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: beat_modifications beat_modifications_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.beat_modifications
    ADD CONSTRAINT beat_modifications_pkey PRIMARY KEY (id);


--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: stories stories_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.stories
    ADD CONSTRAINT stories_pkey PRIMARY KEY (id);


--
-- Name: story_beats story_beats_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.story_beats
    ADD CONSTRAINT story_beats_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: world_events world_events_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.world_events
    ADD CONSTRAINT world_events_pkey PRIMARY KEY (id);


--
-- Name: worlds worlds_pkey; Type: CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.worlds
    ADD CONSTRAINT worlds_pkey PRIMARY KEY (id);


--
-- Name: ix_beat_modifications_applied; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_beat_modifications_applied ON public.beat_modifications USING btree (applied);


--
-- Name: ix_beat_modifications_beat_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_beat_modifications_beat_id ON public.beat_modifications USING btree (beat_id);


--
-- Name: ix_beat_modifications_created_at; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_beat_modifications_created_at ON public.beat_modifications USING btree (created_at);


--
-- Name: ix_conversation_messages_conversation_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversation_messages_conversation_id ON public.conversation_messages USING btree (conversation_id);


--
-- Name: ix_conversation_messages_created_at; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversation_messages_created_at ON public.conversation_messages USING btree (created_at);


--
-- Name: ix_conversations_type; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversations_type ON public.conversations USING btree (type);


--
-- Name: ix_conversations_user_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversations_user_id ON public.conversations USING btree (user_id);


--
-- Name: ix_conversations_world_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversations_world_id ON public.conversations USING btree (world_id);


--
-- Name: ix_conversations_world_user; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_conversations_world_user ON public.conversations USING btree (world_id, user_id);


--
-- Name: ix_stories_world_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_stories_world_id ON public.stories USING btree (world_id);


--
-- Name: ix_story_beats_story_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_story_beats_story_id ON public.story_beats USING btree (story_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_world_events_type; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_world_events_type ON public.world_events USING btree (type);


--
-- Name: ix_world_events_world_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_world_events_world_id ON public.world_events USING btree (world_id);


--
-- Name: ix_world_events_world_t; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_world_events_world_t ON public.world_events USING btree (world_id, t);


--
-- Name: ix_worlds_user_id; Type: INDEX; Schema: public; Owner: shinkei_user
--

CREATE INDEX ix_worlds_user_id ON public.worlds USING btree (user_id);


--
-- Name: beat_modifications beat_modifications_beat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.beat_modifications
    ADD CONSTRAINT beat_modifications_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.story_beats(id) ON DELETE CASCADE;


--
-- Name: conversation_messages conversation_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_world_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_world_id_fkey FOREIGN KEY (world_id) REFERENCES public.worlds(id) ON DELETE CASCADE;


--
-- Name: stories stories_world_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.stories
    ADD CONSTRAINT stories_world_id_fkey FOREIGN KEY (world_id) REFERENCES public.worlds(id) ON DELETE CASCADE;


--
-- Name: story_beats story_beats_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.story_beats
    ADD CONSTRAINT story_beats_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.stories(id) ON DELETE CASCADE;


--
-- Name: story_beats story_beats_world_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.story_beats
    ADD CONSTRAINT story_beats_world_event_id_fkey FOREIGN KEY (world_event_id) REFERENCES public.world_events(id) ON DELETE SET NULL;


--
-- Name: world_events world_events_world_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.world_events
    ADD CONSTRAINT world_events_world_id_fkey FOREIGN KEY (world_id) REFERENCES public.worlds(id) ON DELETE CASCADE;


--
-- Name: worlds worlds_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shinkei_user
--

ALTER TABLE ONLY public.worlds
    ADD CONSTRAINT worlds_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: shinkei_user
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict rgBJfmN50iJifW1eEauV1BeGbr8SfnleiEGWJrfHnLyhSsd93APFNGWwAh3b1zC

