"""add_story_pilot_models

Revision ID: b2c5d8e1f3a4
Revises: a19d05a2b925
Create Date: 2025-11-25 10:00:00.000000

Story Pilot AI Chat Assistant feature:
- Agent personas for customizable AI personalities
- World coherence settings for per-world rules
- GraphRAG models for semantic search and entity graph
- Conversation extensions for agent modes and tool tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c5d8e1f3a4'
down_revision: Union[str, None] = 'a19d05a2b925'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================
    # 1. AGENT PERSONAS TABLE
    # ========================
    op.create_table(
        'agent_personas',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('system_prompt', sa.Text, nullable=False),
        sa.Column('traits', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('generation_defaults', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('is_builtin', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_agent_personas_world_id', 'agent_personas', ['world_id'])
    op.create_index('ix_agent_personas_is_active', 'agent_personas', ['is_active'])
    op.create_unique_constraint('uq_agent_personas_world_name', 'agent_personas', ['world_id', 'name'])

    # ================================
    # 2. WORLD COHERENCE SETTINGS TABLE
    # ================================
    op.create_table(
        'world_coherence_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, unique=True),
        # Physics/Logic coherence
        sa.Column('time_consistency', sa.String(20), nullable=False, server_default='strict'),
        sa.Column('spatial_consistency', sa.String(20), nullable=False, server_default='euclidean'),
        sa.Column('causality', sa.String(20), nullable=False, server_default='strict'),
        # Narrative coherence
        sa.Column('character_knowledge', sa.String(20), nullable=False, server_default='strict'),
        sa.Column('death_permanence', sa.String(20), nullable=False, server_default='permanent'),
        # Custom rules
        sa.Column('custom_rules', sa.ARRAY(sa.Text), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_world_coherence_settings_world_id', 'world_coherence_settings', ['world_id'])

    # ========================
    # 3. GRAPH RAG NODES TABLE
    # ========================
    op.create_table(
        'world_graph_nodes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        # Entity reference (polymorphic)
        sa.Column('entity_type', sa.String(50), nullable=False),  # character, location, event, story, beat
        sa.Column('entity_id', sa.String(36), nullable=False),
        # Semantic data
        sa.Column('content_hash', sa.String(64), nullable=False),  # For change detection
        sa.Column('embedding', sa.JSON, nullable=True),  # Vector embedding as JSON array
        sa.Column('semantic_summary', sa.Text, nullable=True),
        # Graph metrics
        sa.Column('importance_score', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_world_graph_nodes_world_id', 'world_graph_nodes', ['world_id'])
    op.create_index('ix_world_graph_nodes_entity_type', 'world_graph_nodes', ['entity_type'])
    op.create_index('ix_world_graph_nodes_entity_id', 'world_graph_nodes', ['entity_id'])
    op.create_index('ix_world_graph_nodes_importance', 'world_graph_nodes', ['importance_score'])
    op.create_index('ix_world_graph_nodes_world_entity', 'world_graph_nodes', ['world_id', 'entity_type', 'entity_id'])
    op.create_unique_constraint('uq_graph_node', 'world_graph_nodes', ['world_id', 'entity_type', 'entity_id'])

    # ========================
    # 4. GRAPH RAG EDGES TABLE
    # ========================
    op.create_table(
        'world_graph_edges',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_node_id', sa.String(36), sa.ForeignKey('world_graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', sa.String(36), sa.ForeignKey('world_graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),  # mentions, knows, located_at, etc.
        sa.Column('strength', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_world_graph_edges_world_id', 'world_graph_edges', ['world_id'])
    op.create_index('ix_world_graph_edges_source', 'world_graph_edges', ['source_node_id'])
    op.create_index('ix_world_graph_edges_target', 'world_graph_edges', ['target_node_id'])
    op.create_index('ix_world_graph_edges_relationship_type', 'world_graph_edges', ['relationship_type'])
    op.create_index('ix_graph_edges_source_target', 'world_graph_edges', ['source_node_id', 'target_node_id'])

    # ==============================
    # 5. GRAPH RAG SYNC STATUS TABLE
    # ==============================
    op.create_table(
        'world_graph_sync_status',
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('last_full_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_incremental_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('node_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('edge_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('sync_in_progress', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_error', sa.Text, nullable=True),
    )

    # ===================================
    # 6. EXTEND CONVERSATIONS TABLE
    # ===================================
    op.add_column('conversations', sa.Column('mode', sa.String(20), nullable=False, server_default='ask'))
    op.add_column('conversations', sa.Column('persona_id', sa.String(36), nullable=True))
    op.add_column('conversations', sa.Column('provider_override', sa.String(50), nullable=True))
    op.add_column('conversations', sa.Column('model_override', sa.String(100), nullable=True))

    # Add foreign key for persona_id (after agent_personas table exists)
    op.create_foreign_key(
        'fk_conversations_persona_id',
        'conversations',
        'agent_personas',
        ['persona_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_conversations_mode', 'conversations', ['mode'])
    op.create_index('ix_conversations_persona_id', 'conversations', ['persona_id'])

    # =========================================
    # 7. EXTEND CONVERSATION_MESSAGES TABLE
    # =========================================
    op.add_column('conversation_messages', sa.Column('tool_calls', sa.JSON, nullable=True))
    op.add_column('conversation_messages', sa.Column('tool_results', sa.JSON, nullable=True))
    op.add_column('conversation_messages', sa.Column('pending_approval', sa.Boolean, nullable=False, server_default='false'))

    op.create_index('ix_conversation_messages_pending_approval', 'conversation_messages', ['pending_approval'])


def downgrade() -> None:
    # =========================================
    # REVERSE: CONVERSATION_MESSAGES COLUMNS
    # =========================================
    op.drop_index('ix_conversation_messages_pending_approval', table_name='conversation_messages')
    op.drop_column('conversation_messages', 'pending_approval')
    op.drop_column('conversation_messages', 'tool_results')
    op.drop_column('conversation_messages', 'tool_calls')

    # ===================================
    # REVERSE: CONVERSATIONS COLUMNS
    # ===================================
    op.drop_index('ix_conversations_persona_id', table_name='conversations')
    op.drop_index('ix_conversations_mode', table_name='conversations')
    op.drop_constraint('fk_conversations_persona_id', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'model_override')
    op.drop_column('conversations', 'provider_override')
    op.drop_column('conversations', 'persona_id')
    op.drop_column('conversations', 'mode')

    # ==============================
    # REVERSE: GRAPH SYNC STATUS
    # ==============================
    op.drop_table('world_graph_sync_status')

    # ========================
    # REVERSE: GRAPH EDGES
    # ========================
    op.drop_table('world_graph_edges')

    # ========================
    # REVERSE: GRAPH NODES
    # ========================
    op.drop_table('world_graph_nodes')

    # ================================
    # REVERSE: WORLD COHERENCE SETTINGS
    # ================================
    op.drop_table('world_coherence_settings')

    # ========================
    # REVERSE: AGENT PERSONAS
    # ========================
    op.drop_table('agent_personas')
