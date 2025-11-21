# Phase 5: Critical Issues Report

**Date**: 2025-11-21
**Severity**: 🔴 **CRITICAL - BLOCKS PRODUCTION DEPLOYMENT**
**Status**: Issues identified, fixes provided below

---

## Executive Summary

Phase 5 implementation has **4 critical bugs** that will cause runtime failures. All issues are concentrated in the `AuthoringService.manual_assist()` method and test infrastructure. The bugs are straightforward to fix and do not affect the architectural design.

**Impact**: Manual authoring mode and all unit tests are currently broken.

---

## 🔴 Critical Bug #1: Field Name Mismatch (2 occurrences)

### Problem
The `StoryBeat` model uses `order_index` but the code references `seq_in_story`.

### Location 1: Line 156 in `authoring_service.py`
```python
# ❌ INCORRECT
logger.info(
    "autonomous_generation_completed",
    story_id=story_id,
    beat_id=beat.id,
    sequence=beat.seq_in_story  # AttributeError: 'StoryBeat' object has no attribute 'seq_in_story'
)
```

**Fix**:
```python
# ✅ CORRECT
logger.info(
    "autonomous_generation_completed",
    story_id=story_id,
    beat_id=beat.id,
    sequence=beat.order_index  # Use correct field name
)
```

### Location 2: Line 357 in `authoring_service.py`
```python
# ❌ INCORRECT
temp_beat = StoryBeat(
    story_id=story_id,
    seq_in_story=999999,  # TypeError: StoryBeat() got an unexpected keyword argument 'seq_in_story'
    content=user_content,
    generated_by=GeneratedBy.USER
)
```

**Fix**:
```python
# ✅ CORRECT
temp_beat = StoryBeat(
    story_id=story_id,
    order_index=999999,  # Use correct field name
    content=user_content,
    generated_by=GeneratedBy.USER
)
```

### Evidence
From `story_beat.py:60-64`:
```python
order_index: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    comment="Ordering within the story"
)
```

### Impact
- ❌ Autonomous mode logging will fail
- ❌ Manual assist will crash when creating temp beat

---

## 🔴 Critical Bug #2: Method Signature Mismatch - check_beat_coherence

### Problem
`manual_assist()` calls `check_beat_coherence()` with wrong parameter name and type.

### Location: Line 337 in `authoring_service.py`
```python
# ❌ INCORRECT CALL
coherence_result = await self.narrative_service.check_beat_coherence(
    story_id=story_id,
    user_id=user_id,
    beat_content=user_content,  # ❌ Parameter doesn't exist
    provider=provider,
    model=model
)
```

### Actual Signature (narrative_service.py:697-704)
```python
async def check_beat_coherence(
    self,
    story_id: str,
    beat_id: str,  # ❌ Expects beat_id, not beat_content
    user_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
```

### Root Cause
The `check_beat_coherence` method expects an existing beat in the database (via `beat_id`), but manual assist needs to validate user-written content that doesn't exist in the DB yet.

### Fix Options

**Option A: Create temporary beat, check, then delete**
```python
# Create temporary beat in DB
temp_beat = StoryBeat(
    story_id=story_id,
    order_index=999999,
    content=user_content,
    generated_by=GeneratedBy.USER
)
self.session.add(temp_beat)
await self.session.flush()  # Get ID without committing

try:
    # Check coherence
    coherence_result = await self.narrative_service.check_beat_coherence(
        story_id=story_id,
        beat_id=temp_beat.id,  # Now we have a beat_id
        user_id=user_id,
        provider=provider,
        model=model
    )
finally:
    # Clean up temporary beat
    await self.session.delete(temp_beat)
    await self.session.rollback()  # Don't persist
```

**Option B: Add overloaded method to NarrativeGenerationService**
```python
# In narrative_service.py - add new method
async def check_content_coherence(
    self,
    story_id: str,
    content: str,  # Accept raw content instead of beat_id
    user_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check arbitrary content for coherence (for manual authoring).

    Similar to check_beat_coherence but doesn't require persisted beat.
    """
    # Implementation similar to check_beat_coherence but works with content
```

**Recommendation**: **Option A** is simpler and reuses existing logic. Option B is cleaner architecturally but requires more changes.

### Impact
- ❌ Manual assist endpoint will crash with TypeError
- ❌ All manual mode users will experience failures

---

## 🔴 Critical Bug #3: Method Signature Mismatch - summarize_beat

### Problem
`manual_assist()` calls `summarize_beat()` with wrong parameter type.

### Location: Line 363 in `authoring_service.py`
```python
# ❌ INCORRECT CALL
suggested_summary = await self.narrative_service.summarize_beat(
    beat=temp_beat,  # ❌ Passes beat object
    provider=provider,
    model=model
)
```

### Actual Signature (narrative_service.py:490)
```python
async def summarize_beat(
    self,
    beat_id: str,  # ❌ Expects beat_id string
    user_id: str,  # ❌ Missing user_id parameter
    provider: Optional[str] = None
) -> str:
```

### Fix Options

**Option A: Use temp beat approach (consistent with Bug #2 fix)**
```python
# Create temporary beat in DB
temp_beat = StoryBeat(
    story_id=story_id,
    order_index=999999,
    content=user_content,
    generated_by=GeneratedBy.USER
)
self.session.add(temp_beat)
await self.session.flush()

try:
    # Summarize using beat_id
    suggested_summary = await self.narrative_service.summarize_beat(
        beat_id=temp_beat.id,  # Pass ID
        user_id=user_id,       # Pass user_id
        provider=provider
    )
finally:
    await self.session.delete(temp_beat)
    await self.session.rollback()
```

**Option B: Add overloaded method**
```python
# In narrative_service.py - add new method
async def summarize_content(
    self,
    content: str,  # Accept raw content
    story_id: str,  # For context
    user_id: str,
    provider: Optional[str] = None
) -> str:
    """Generate summary for arbitrary content (for manual authoring)."""
```

**Recommendation**: **Option A** for consistency with Bug #2 fix.

### Impact
- ❌ Manual assist endpoint will crash with TypeError
- ❌ Summary generation completely broken in manual mode

---

## 🔴 Critical Bug #4: Missing Test Utility Function

### Problem
Test file references `setup_mock_story_query()` function that doesn't exist.

### Locations: Used 11 times
- test_authoring_service.py lines: 102, 117, 137, 183, 199, 224, 248, 279, 320, 344, 369

```python
# ❌ INCORRECT - Function doesn't exist
setup_mock_story_query(mock_session, mock_story)
```

### Error
```
NameError: name 'setup_mock_story_query' is not defined
```

### Fix
Add this function to `test_authoring_service.py` (after the fixture definitions, around line 23):

```python
def setup_mock_story_query(mock_session, story):
    """Helper to setup mock session to return a story from query."""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = story
    mock_session.execute.return_value = mock_result
```

### Impact
- ❌ 11 out of 16 unit tests fail with NameError
- ❌ Test suite reports false failures

---

## 📊 Impact Summary

### Broken Functionality
| Feature | Status | User Impact |
|---------|--------|-------------|
| **Autonomous Mode** | ⚠️ Mostly Works | Logging fails but generation works |
| **Collaborative Mode** | ✅ **Works** | No issues detected |
| **Manual Mode** | ❌ **BROKEN** | Coherence check and summary both fail |
| **Unit Tests** | ❌ **BROKEN** | 11/16 tests fail |

### Severity Assessment
- **Production Blocker**: YES (Manual mode completely broken)
- **Data Loss Risk**: NO (failures happen before DB commits)
- **Security Risk**: NO (failures are in business logic, not auth/validation)

---

## 🛠️ Complete Fix Implementation

### File 1: `/home/barbidou/SHINKEI/backend/src/shinkei/services/authoring_service.py`

**Change 1** (Line 156):
```python
# Before:
sequence=beat.seq_in_story

# After:
sequence=beat.order_index
```

**Change 2** (Lines 329-390 - full method replacement):
```python
async def manual_assist(
    self,
    story_id: str,
    user_id: str,
    user_content: str,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> ManualAssistance:
    """
    Provide assistance for manually authored content.

    Validates coherence with existing story and world context,
    generates a suggested summary, and suggests relevant world events.

    Args:
        story_id: Story UUID
        user_id: User ID for ownership verification
        user_content: User-written beat content to validate/assist
        provider: Optional LLM provider override
        model: Optional model name override

    Returns:
        ManualAssistance with coherence check, summary, and suggestions

    Raises:
        ValueError: If story not found or user doesn't own it
        RuntimeError: If assistance generation fails
    """
    # Verify story exists (mode check with warning only)
    story = await self._get_story(story_id)
    if story.mode != AuthoringMode.MANUAL:
        logger.warning(
            "manual_assist_wrong_mode",
            story_id=story_id,
            current_mode=story.mode.value,
            message="Manual assistance requested for non-manual story. Proceeding anyway."
        )

    logger.info(
        "manual_assist_started",
        story_id=story_id,
        user_id=user_id,
        content_length=len(user_content)
    )

    # Create temporary beat for coherence check and summarization
    temp_beat = StoryBeat(
        story_id=story_id,
        order_index=999999,  # ✅ FIXED: Use order_index instead of seq_in_story
        content=user_content,
        generated_by=GeneratedBy.USER
    )

    # Add to session and flush to get ID (but don't commit)
    self.session.add(temp_beat)
    await self.session.flush()

    coherence_result = {}
    suggested_summary = ""

    try:
        # Coherence check using temporary beat
        try:
            coherence_result = await self.narrative_service.check_beat_coherence(
                story_id=story_id,
                beat_id=temp_beat.id,  # ✅ FIXED: Use beat_id instead of beat_content
                user_id=user_id,
                provider=provider,
                model=model
            )
        except Exception as e:
            logger.error("coherence_check_failed", error=str(e))
            coherence_result = {
                "is_coherent": None,
                "issues": [],
                "suggestions": [],
                "error": str(e)
            }

        # Generate suggested summary
        try:
            suggested_summary = await self.narrative_service.summarize_beat(
                beat_id=temp_beat.id,  # ✅ FIXED: Pass beat_id
                user_id=user_id,        # ✅ FIXED: Pass user_id
                provider=provider
            )
        except Exception as e:
            logger.error("summary_generation_failed", error=str(e))
            suggested_summary = ""

    finally:
        # Clean up temporary beat - rollback to remove from session
        await self.session.rollback()

    # World event suggestions (placeholder - could be enhanced with AI)
    world_event_suggestions = []

    assistance = ManualAssistance(
        coherence_result=coherence_result,
        suggested_summary=suggested_summary,
        world_event_suggestions=world_event_suggestions
    )

    logger.info(
        "manual_assist_completed",
        story_id=story_id,
        is_coherent=coherence_result.get("is_coherent"),
        has_summary=bool(suggested_summary)
    )

    return assistance
```

### File 2: `/home/barbidou/SHINKEI/backend/tests/unit/test_authoring_service.py`

**Add function after line 21** (after mock_session fixture):

```python
def setup_mock_story_query(mock_session, story):
    """Helper to setup mock session to return a story from query."""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = story
    mock_session.execute.return_value = mock_result
```

---

## ✅ Verification Checklist

After applying fixes, verify:

- [ ] `poetry run pytest tests/unit/test_authoring_service.py -v` - All 16 tests pass
- [ ] `curl -X POST http://localhost:8000/api/v1/narrative/stories/{id}/beats/assist` - Manual assist works
- [ ] `docker exec shinkei-backend poetry run python -c "from shinkei.services.authoring_service import AuthoringService; print('Import successful')"` - No import errors
- [ ] Check logs for `autonomous_generation_completed` - Verify sequence field logs correctly
- [ ] Manual E2E test: Write manual beat, request assistance, verify coherence check returns

---

## 🎯 Priority

**IMMEDIATE** - These fixes are required before Phase 5 can be considered production-ready.

**Estimated Fix Time**: 15-20 minutes

**Risk Level**: LOW - Changes are isolated to identified bugs, no architectural changes needed

---

## 📝 Lessons Learned

1. **Type Safety**: TypeScript on frontend prevented similar issues
2. **Test-Driven Development**: Writing tests before implementation would have caught these
3. **Integration Testing**: Need integration tests that actually call the API endpoints
4. **Code Review**: Manual code review missed field name mismatch
5. **Documentation**: NarrativeGenerationService method signatures should be better documented

---

## Next Steps

1. Apply all fixes from this document
2. Run full test suite
3. Perform manual E2E testing of all three authoring modes
4. Add integration tests for authoring endpoints
5. Update Phase 5 summary with fix verification
