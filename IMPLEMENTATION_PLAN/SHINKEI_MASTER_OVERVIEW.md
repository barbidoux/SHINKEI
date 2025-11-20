# 📚 **SHINKEI PROJECT - MASTER DOCUMENTATION OVERVIEW**

## **How to Navigate the Complete Implementation Package**
## **Version:** 1.0.0

---

# **WELCOME TO THE SHINKEI IMPLEMENTATION PACKAGE**

This package contains everything Claude Code needs to build the Shinkei (心継) Narrative Engine from scratch to production deployment.

---

# **DOCUMENT STRUCTURE**

## **1. Specification Documents (Provided)**

### **SHINKEI_SPECS.md**
- **Purpose**: Complete feature specifications
- **When to read**: Before starting and when clarifying requirements
- **Key sections**:
  - Project vision and objectives
  - Data model definitions
  - Coherence rules
  - Three narrative modes (Auto, Collab, Manual)
  - WebUI requirements
  - GraphRAG roadmap

### **Shinkei__心継__Project__Software_Architecture_Document.md**
- **Purpose**: Technical architecture decisions
- **When to read**: Before Phase 0 and when making architectural decisions
- **Key sections**:
  - C4 model architecture
  - Technology stack rationale
  - Modular monolith pattern
  - Database schema design
  - Security architecture
  - Observability strategy

---

## **2. Implementation Guides (Created)**

### **📘 SHINKEI_IMPLEMENTATION_PLAN.md** ⭐ PRIMARY GUIDE
**This is your main roadmap.**

**Structure:**
- **Phase 0**: Project Foundation & Setup (3-5 days)
- **Phase 1**: Database Layer & Core Models (5-7 days)
- **Phase 2**: Authentication & Security (5-7 days)
- **Phase 3**: Core CRUD Operations & API (7-10 days)
- **Phase 4**: AI Engine Foundation (7-10 days)
- **Phase 5**: Narrative Generation Pipeline (10-14 days)
- **Phase 6**: Frontend Foundation (10-14 days)
- **Phase 7**: World & Timeline Management UI (7-10 days)
- **Phase 8**: Story Management UI (7-10 days)
- **Phase 9**: Multi-Mode Authoring System (14-21 days)
- **Phase 10**: Cross-Story Intersections (7-10 days)
- **Phase 11**: GraphRAG Preparation (10-14 days)
- **Phase 12**: Production Readiness (14-21 days)

**Each phase contains:**
- Detailed step-by-step instructions
- Complete code examples
- Unit test templates
- Integration test templates
- Completion checklists
- Quality gates

**How to use:**
1. Start at Phase 0, Milestone 0.1
2. Follow each step sequentially
3. Complete all tests before moving to next milestone
4. Check off items in completion checklist
5. Only proceed when all quality gates pass

---

### **📗 SHINKEI_AI_ENGINE_FRONTEND_GUIDE.md** ⭐ SUPPLEMENTARY DETAILS
**Deep dive into complex implementations.**

**When to use:**
- During Phase 4-5 (AI Engine)
- During Phase 6-8 (Frontend)
- When implementing narrative generation
- When building UI components

**Contains:**
- Complete AI engine architecture
- Abstract NarrativeModel interface
- OpenAI implementation example
- Prompt engineering utilities
- Model factory pattern
- Generation service implementation
- Frontend architecture patterns
- State management strategies
- Component design patterns

**How to use:**
1. Reference when main plan says "See supplementary guide"
2. Use as detailed reference for AI and Frontend phases
3. Copy code patterns as needed
4. Adapt to specific requirements

---

### **📙 SHINKEI_QUICK_START_GUIDE.md** ⭐ DAILY REFERENCE
**Your everyday coding companion.**

**When to use:**
- Every development session
- When encountering common issues
- When needing code templates
- When debugging problems

**Contains:**
- Daily startup checklist
- Code templates (copy-paste ready)
- Debugging workflows
- Decision trees
- Performance optimization checklist
- Security checklist
- Commit message convention
- Quick reference commands
- Troubleshooting quick fixes
- Code review checklist

**How to use:**
1. Start each day with startup checklist
2. Use templates when creating new components
3. Follow debugging workflows when stuck
4. Reference during code review

---

# **RECOMMENDED WORKFLOW**

## **Before Starting Development**

1. **Read the specifications** (30-60 minutes)
   - [ ] Read SHINKEI_SPECS.md completely
   - [ ] Read Architecture Document sections 1-4
   - [ ] Understand core concepts: World, Story, StoryBeat, WorldEvent

2. **Review the implementation plan** (1-2 hours)
   - [ ] Read Phase 0 completely
   - [ ] Skim through all phase headers
   - [ ] Understand the overall timeline
   - [ ] Identify any questions or concerns

3. **Set up your environment** (2-3 hours)
   - [ ] Follow Phase 0, Milestone 0.1 exactly
   - [ ] Verify all tools installed
   - [ ] Run hello-world tests
   - [ ] Commit initial setup

---

## **During Each Development Session**

### **Morning Routine** (15 minutes)
```bash
# 1. Start services
docker-compose up -d

# 2. Verify health
curl http://localhost:8000/health

# 3. Run existing tests
cd backend && poetry run pytest
cd ../frontend && npm test

# 4. Review current milestone in implementation plan

# 5. Create feature branch if needed
git checkout -b feature/phase-X-milestone-Y
```

### **Development Loop** (per feature)
1. **Plan** (5-10 minutes)
   - Read milestone instructions
   - Identify what needs to be built
   - Check supplementary guide if needed

2. **Test First** (15-30 minutes)
   - Write unit tests for new feature
   - Tests should fail (red)

3. **Implement** (30-60 minutes)
   - Write minimal code to pass tests
   - Use templates from quick start guide
   - Tests should pass (green)

4. **Refactor** (10-20 minutes)
   - Improve code quality
   - Remove duplication
   - Tests should still pass (green)

5. **Integrate** (15-30 minutes)
   - Write integration tests
   - Test feature in context
   - Manual testing if needed

6. **Document** (5-10 minutes)
   - Add docstrings
   - Update API docs
   - Comment complex logic

7. **Review** (10-15 minutes)
   - Run code review checklist
   - Run security checklist
   - Run linter and formatter

8. **Commit** (5 minutes)
   ```bash
   git add .
   git commit -m "feat(scope): description"
   git push origin feature-branch
   ```

### **End of Day** (10 minutes)
```bash
# 1. Run full test suite
poetry run pytest --cov

# 2. Check code quality
poetry run black .
poetry run ruff check .
poetry run mypy src/

# 3. Update progress
# Mark completed items in implementation plan

# 4. Push work
git push origin feature-branch

# 5. Document blockers/questions
# Add to project notes or GitHub issues
```

---

## **When You're Stuck**

### **Decision Tree: What Document to Check?**

```
Problem type?
│
├─ "I don't understand what to build"
│  └─ Read: SHINKEI_SPECS.md
│
├─ "I don't know HOW to build this"
│  └─ Read: SHINKEI_IMPLEMENTATION_PLAN.md (current phase)
│
├─ "I need detailed implementation for AI/Frontend"
│  └─ Read: SHINKEI_AI_ENGINE_FRONTEND_GUIDE.md
│
├─ "I need a code template"
│  └─ Read: SHINKEI_QUICK_START_GUIDE.md (Part I)
│
├─ "Something is broken"
│  └─ Read: SHINKEI_QUICK_START_GUIDE.md (Part II - Debugging)
│
├─ "Should I do X or Y?"
│  └─ Read: SHINKEI_QUICK_START_GUIDE.md (Part III - Decision Trees)
│
└─ "How do I run/test/deploy?"
   └─ Read: SHINKEI_QUICK_START_GUIDE.md (Part VII - Commands)
```

---

## **When Things Go Wrong**

### **Common Issues and Where to Find Solutions**

| Issue | Document | Section |
|-------|----------|---------|
| Tests failing | Quick Start Guide | Part II: Debugging Workflows |
| Can't connect to database | Quick Start Guide | Part VIII: Troubleshooting |
| Import errors | Quick Start Guide | Part II: Debugging Workflows |
| Docker issues | Quick Start Guide | Part VIII: Troubleshooting |
| API returns 422 | Quick Start Guide | Part II: Debugging Workflows |
| Migration conflicts | Quick Start Guide | Part VIII: Troubleshooting |
| Performance issues | Quick Start Guide | Part IV: Performance Optimization |
| Security concerns | Implementation Plan | Phase 2 + Quick Start Part V |
| Architecture questions | Architecture Document | Relevant section |
| Feature clarification | SHINKEI_SPECS.md | Relevant section |

---

# **PHASE-SPECIFIC READING GUIDES**

## **Phase 0-1: Foundation & Database**

**Primary Reading:**
- Implementation Plan: Phase 0 & 1 (complete)
- Quick Start Guide: Part I (Getting Started)

**Reference:**
- Architecture Document: Section 5 (Database Schema)
- Quick Start Guide: Pattern 1-3 (Models, Schemas, Repositories)

**Don't worry about yet:**
- AI Engine details
- Frontend specifics
- GraphRAG implementation

---

## **Phase 2-3: Authentication & API**

**Primary Reading:**
- Implementation Plan: Phase 2 & 3 (complete)
- Quick Start Guide: Part I & V (Security)

**Reference:**
- Architecture Document: Section 7 (Security)
- Quick Start Guide: Pattern 4 (API Endpoints)

**Don't worry about yet:**
- AI generation logic
- Frontend implementation
- Advanced features

---

## **Phase 4-5: AI Engine**

**Primary Reading:**
- Implementation Plan: Phase 4 & 5 (complete)
- AI Engine Guide: Complete document ⭐

**Reference:**
- SHINKEI_SPECS.md: Section 6 (AI Engine)
- Architecture Document: Section 6 (AI Integration)

**Critical concepts:**
- Abstract interface pattern
- Prompt engineering
- Generation context
- Model factory pattern

---

## **Phase 6-8: Frontend**

**Primary Reading:**
- Implementation Plan: Phase 6-8 (complete)
- AI Engine Guide: Frontend sections

**Reference:**
- Architecture Document: Section 4 (Frontend)
- SHINKEI_SPECS.md: Section 8 (WebUI)

**Key patterns:**
- SvelteKit routing
- State management
- API client
- Component composition

---

## **Phase 9-10: Advanced Features**

**Primary Reading:**
- Implementation Plan: Phase 9-10 (complete)
- SHINKEI_SPECS.md: Section 7 (Narrative Modes)

**Reference:**
- AI Engine Guide: Generation Service
- Architecture Document: Section 8 (Coherence)

**Focus areas:**
- Mode switching logic
- Collaborative UI
- Timeline intersections
- Real-time updates

---

## **Phase 11-12: Production**

**Primary Reading:**
- Implementation Plan: Phase 11-12 (complete)
- Architecture Document: Section 9 (Deployment)

**Reference:**
- Quick Start Guide: Part IV (Performance)
- Quick Start Guide: Part V (Security)

**Production concerns:**
- Performance optimization
- Security hardening
- Monitoring setup
- Deployment automation

---

# **QUALITY STANDARDS**

## **Code Must Pass:**

### **Automated Checks**
```bash
# Formatting
poetry run black --check .

# Linting
poetry run ruff check .

# Type checking
poetry run mypy src/

# Tests
poetry run pytest --cov --cov-fail-under=80

# Security scanning
docker run --rm -v $(pwd):/app aquasec/trivy fs /app
```

### **Manual Review**
- [ ] Code review checklist (Quick Start Part IX)
- [ ] Security checklist (Quick Start Part V)
- [ ] Performance checklist (Quick Start Part IV)

---

# **PROJECT MILESTONES**

## **Major Milestones**

| Milestone | Completion Criteria | Estimated Time |
|-----------|-------------------|----------------|
| Foundation Complete | Phase 0-1 done, all tests pass | 10 days |
| Backend MVP | Phase 0-3 done, API fully functional | 24 days |
| AI Integration | Phase 4-5 done, generation working | 41 days |
| Frontend MVP | Phase 6-8 done, basic UI functional | 68 days |
| Feature Complete | Phase 9-10 done, all modes working | 95 days |
| Production Ready | Phase 11-12 done, deployed | 153 days |

## **Weekly Goals**

### **Week 1**: Foundation
- Project setup complete
- Database schema implemented
- First migration applied

### **Week 2**: Core Models
- All models implemented
- All repositories complete
- Unit tests at 80%+ coverage

### **Week 3-4**: Authentication & API
- Supabase Auth integrated
- All CRUD endpoints working
- Integration tests complete

### **Week 5-6**: AI Engine
- Abstract interface complete
- At least one provider working
- Generation pipeline functional

### **Week 7-8**: Generation Service
- Beat generation working
- Summary generation working
- Coherence validation working

### **Week 9-11**: Frontend Foundation
- SvelteKit app functional
- Auth flow working
- Basic navigation complete

### **Week 12-13**: World & Story UI
- World management complete
- Story creation working
- Timeline visualization basic

### **Week 14-16**: Advanced UI
- Auto mode complete
- Collaborative mode complete
- Manual mode complete

### **Week 17-18**: Polish
- Cross-story features
- GraphRAG foundation
- Bug fixes

### **Week 19-22**: Production
- Performance optimized
- Security hardened
- Monitoring deployed
- Documentation complete

---

# **SUCCESS METRICS**

## **Technical Metrics**

- [ ] Test coverage ≥ 80%
- [ ] All security scans pass
- [ ] API response time < 200ms (p95)
- [ ] Frontend load time < 2s
- [ ] Zero critical bugs
- [ ] All linters pass
- [ ] All type checks pass

## **Functional Metrics**

- [ ] User can create worlds
- [ ] User can create stories
- [ ] AI generates coherent narratives
- [ ] All three modes functional
- [ ] Stories can intersect via WorldEvents
- [ ] Timeline visualization works
- [ ] Data persists correctly
- [ ] Auth flow secure

## **Quality Metrics**

- [ ] Code is well-documented
- [ ] API docs are complete
- [ ] User documentation exists
- [ ] Deployment is automated
- [ ] Monitoring is configured
- [ ] Backup/recovery tested

---

# **COMMUNICATION PROTOCOLS**

## **When to Ask for Help**

**Ask immediately if:**
- Requirements are unclear
- Architecture decision needed
- Security concern identified
- Major blocker encountered
- Timeline at risk

**Try to solve first, then ask:**
- Code not working
- Test failing
- Minor bug
- Unclear error message

## **How to Report Issues**

```markdown
## Issue Description
[Clear description of the problem]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Environment
- OS: [e.g., macOS 12.0]
- Python: [e.g., 3.11.0]
- Node: [e.g., 20.0.0]
- Docker: [e.g., 24.0.0]

## Relevant Logs
```
[paste logs here]
```

## What I've Tried
- [Attempt 1]
- [Attempt 2]

## Relevant Documentation
- [Link to implementation plan section]
- [Link to architecture document]
```

---

# **FINAL CHECKLIST BEFORE STARTING**

- [ ] I've read SHINKEI_SPECS.md
- [ ] I've read the Architecture Document (key sections)
- [ ] I've reviewed the Implementation Plan structure
- [ ] I've skimmed the Quick Start Guide
- [ ] I understand the 12-phase approach
- [ ] I have access to all required tools
- [ ] I've set up my development environment
- [ ] I'm ready to start Phase 0, Milestone 0.1
- [ ] I know where to find help when stuck
- [ ] I understand the quality standards

---

# **CONCLUSION**

You now have everything you need to build Shinkei from scratch. The documents are designed to work together:

1. **Specs & Architecture** = The "What" and "Why"
2. **Implementation Plan** = The "How" (step-by-step)
3. **Supplementary Guides** = The "Details" (deep dives)
4. **Quick Start** = The "Reference" (daily use)

**Start with confidence. The plan is comprehensive, tested, and designed for success.**

**When in doubt:**
1. Check the specs for requirements
2. Check the implementation plan for instructions
3. Check the quick start guide for templates
4. Ask for help if stuck

**Good luck, and enjoy building Shinkei! 🚀**

---

## **Document Versions**

| Document | Version | Last Updated |
|----------|---------|--------------|
| SHINKEI_SPECS.md | 1.0 | [Original] |
| Architecture Document | 1.0.2 | [Original] |
| Implementation Plan | 1.0.0 | Today |
| AI Engine Guide | 1.0.0 | Today |
| Quick Start Guide | 1.0.0 | Today |
| Master Overview | 1.0.0 | Today |

---

## **Quick Access Index**

**Most Frequently Used:**
- Start here: Implementation Plan Phase 0
- Code templates: Quick Start Part I
- Debugging: Quick Start Part II
- Commands: Quick Start Part VII

**Phase-Specific:**
- Database: Implementation Plan Phase 1
- Auth: Implementation Plan Phase 2
- API: Implementation Plan Phase 3
- AI: AI Engine Guide
- Frontend: Implementation Plan Phase 6

**Reference:**
- Architecture decisions: Architecture Document
- Feature requirements: SHINKEI_SPECS.md
- Security: Quick Start Part V
- Performance: Quick Start Part IV

---

**This is your complete Shinkei implementation package. Everything you need is here. Start building! 💪**
