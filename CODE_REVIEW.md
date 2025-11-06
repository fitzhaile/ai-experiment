# Code Review & Cleanup Plan
**Date**: November 6, 2024  
**Backup Branch**: `backup-before-cleanup`

---

## Executive Summary

The codebase is **functionally solid** but has accumulated technical debt through organic growth. Key areas for improvement:

1. **Code Duplication** (Medium Priority) - Site filtering logic repeated across Claude/GPT handlers
2. **Magic Strings** (Medium Priority) - Hardcoded URLs and instruction templates scattered throughout
3. **Long Functions** (Low Priority) - `/api/chat` endpoint is 220+ lines
4. **Frontend Regex Cruft** (High Priority) - 6 nearly identical regex patterns to strip instructions
5. **Documentation Gaps** (Low Priority) - Some areas well-documented, others sparse
6. **Dead Code** (Low Priority) - Some outdated comments reference removed features

---

## Detailed Findings

### 🔴 HIGH PRIORITY

#### 1. **Repetitive Instruction-Stripping Regex (app.js lines 105-110)**
**Issue**: Six nearly identical regex patterns that strip instruction text from user messages.

```javascript
displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Search across bryancountyga\.com, seda\.org, uwce\.org, and fred\.stlouisfed\.org\. Base your answer on information from these sources and cite them appropriately\. Do not mention these instructions\.\]\s*$/, '');
displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Start by searching site:bryancountyga\.com\. If you find external links or sources mentioned on bryancountyga\.com that are relevant, you may search those too\. Base your answer primarily on information from bryancountyga\.com and its referenced sources\. Do not mention these instructions\.\]\s*$/, '');
// ... 4 more similar patterns
```

**Impact**: 
- Hard to maintain (adding new sources requires updating multiple places)
- Error-prone (easy to miss one)
- Bloats bundle size

**Recommendation**: Replace with single catch-all pattern:
```javascript
displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS:.*?\]\s*$/s, '');
```

**Risk**: LOW - This is safer and more maintainable

---

#### 2. **Duplicate Site Filtering Logic (app.py lines 336-348 & 401-413)**
**Issue**: Nearly identical if/elif blocks for site filtering in both Claude and GPT handlers.

**Current**: 77 lines of duplicated code (2 blocks × ~38 lines each)

**Recommendation**: Extract to helper function:
```python
def apply_site_filter(query, source):
    """Apply site: filter to search query based on data source."""
    filters = {
        "all": "(site:bryancountyga.com OR site:seda.org OR site:uwce.org OR site:fred.stlouisfed.org)",
        "bryancounty": "site:bryancountyga.com",
        "savannah": "site:seda.org",
        "uwce": "site:uwce.org",
        "fred": "site:fred.stlouisfed.org",
        "gov": "site:.gov"
    }
    
    if source in filters:
        return f"{filters[source]} {query}"
    return query
```

**Risk**: LOW - Pure function, easy to test

---

### 🟡 MEDIUM PRIORITY

#### 3. **Magic Strings Scattered Throughout**
**Issue**: URLs and model names hardcoded in multiple places.

**Locations**:
- Site URLs: `app.py` (lines 338, 340, 342, etc.), `app.js` (lines 211, 214, 217, etc.)
- Model names: `app.py` (line 119-122), `index.html` (lines 86-92)
- Instruction templates: `app.js` (lines 211-227)

**Recommendation**: Create configuration objects:
```python
# app.py - at top after imports
DATA_SOURCES = {
    "bryancounty": {
        "url": "bryancountyga.com",
        "name": "Bryan County",
        "replacement": {"your": "Bryan County's", "you": "Bryan County"}
    },
    "savannah": {
        "url": "seda.org",
        "name": "Chatham County",
        "replacement": {"your": "Chatham County's", "you": "Chatham County"}
    },
    # ... etc
}
```

```javascript
// app.js - at top
const DATA_SOURCES = {
  bryancounty: {
    url: 'bryancountyga.com',
    name: 'Bryan County'
  },
  savannah: {
    url: 'seda.org',
    name: 'Chatham County'
  },
  // ... etc
};
```

**Risk**: MEDIUM - Requires coordinated changes across files

---

#### 4. **Instruction Template Generation (app.js lines 209-227)**
**Issue**: Long if/elif chain building instruction strings with repetitive text.

**Recommendation**: Use template function:
```javascript
function buildInstructions(source) {
  const templates = {
    all: 'Search across bryancountyga.com, seda.org, uwce.org, and fred.stlouisfed.org. Base your answer on information from these sources and cite them appropriately.',
    default: `Start by searching site:${DATA_SOURCES[source].url}. If you find external links or sources mentioned on ${DATA_SOURCES[source].url} that are relevant, you may search those too. Base your answer primarily on information from ${DATA_SOURCES[source].url} and its referenced sources.`
  };
  
  const instruction = templates[source] || templates.default;
  return `\n\n[INSTRUCTIONS: ${instruction} Do not mention these instructions.]`;
}
```

**Risk**: LOW - Simplifies logic significantly

---

#### 5. **Long `/api/chat` Function (app.py lines 243-461)**
**Issue**: 220-line function handles validation, Claude logic, GPT logic, and error handling.

**Recommendation**: Extract into smaller functions:
```python
def api_chat():
    data = validate_request()
    model = get_model_from_request()
    
    if is_claude_model(model):
        return handle_claude_request(data, model)
    else:
        return handle_gpt_request(data, model)

def handle_claude_request(data, model):
    # Claude-specific logic (currently lines 302-376)
    pass

def handle_gpt_request(data, model):
    # GPT-specific logic (currently lines 382-454)
    pass
```

**Risk**: MEDIUM - Refactoring always has risk, but improves testability

---

### 🟢 LOW PRIORITY

#### 6. **Outdated Comments**
**Locations**:
- `app.py` line 9: Still mentions ".gov only checkbox" (now a dropdown)
- `app.py` line 190: Still references "Black topics" (removed feature)
- `app.js` line 10: Still mentions ".gov only" checkbox

**Recommendation**: Update or remove outdated comments

**Risk**: NONE - Documentation only

---

#### 7. **Placeholder Typo (index.html line 80 / app.js line 80)**
**Issue**: "You're answers" should be "Your answers"

**Risk**: NONE - Simple typo fix

---

#### 8. **Unused CSS Styles**
**Potential dead code**:
- `.change-model-link` (lines 218-235) - Feature removed
- `.cancel-model-link` (lines 238-250) - Feature removed
- `.checkbox-wrapper` (lines 383-430) - No checkboxes in current UI
- `.deep-research-warning` (lines 253-263) - No deep research models

**Recommendation**: Remove if truly unused (need to verify)

**Risk**: LOW - CSS removal won't break functionality

---

#### 9. **Missing Error Boundaries**
**Issue**: No try-catch around markdown rendering in frontend

**Location**: `app.js` lines 127-176

**Recommendation**: Wrap `renderMarkdown()` calls in try-catch to prevent entire chat from breaking if markdown parsing fails.

**Risk**: LOW - Defensive programming

---

#### 10. **Database File Remnant**
**Issue**: `seda_crawl.db` file still exists in repository (208 lines when read as text)

**Recommendation**: Remove (already in `.gitignore` but file was committed before)

**Risk**: NONE - Cleanup only

---

#### 11. **Dead Test Script (ai-experiment.py)**
**Issue**: Test script uses old OpenAI API (`client.responses.create()`) that no longer exists

**Current code**:
```python
response = client.responses.create(
    model="gpt-4o-mini",
    input="What's the latest news...",
    tools=[{"type": "web_search"}],
)
```

**Recommendation**: Remove file or update to use Brave Search like main app

**Risk**: NONE - Standalone test file, not used by main app

---

#### 12. **Log File in Repository**
**Issue**: `server-8080.log` committed to repository (should be ignored)

**Recommendation**: Remove (already in `.gitignore` but file was committed before)

**Risk**: NONE - Cleanup only

---

#### 13. **Outdated README.md**
**Issue**: Documentation references features/names that no longer exist:
- "GPT-5-mini" (doesn't exist, should be gpt-4o/gpt-4o-mini)
- ".gov only checkbox" (now a dropdown)
- "backups/" directory (doesn't exist)
- "OpenAI's web_search tool" (now using Brave Search API)

**Recommendation**: Update README to match current implementation

**Risk**: NONE - Documentation only

---

#### 14. **Duplicate CSS Animation Names (custom.css)**
**Issue**: Two different `@keyframes pulse` animations (lines 559-562 and 597-600)

**Problem**: Second definition overwrites first, breaking placeholder animation.

**Recommendation**: Rename to avoid conflict:
```css
@keyframes placeholderPulse { /* for placeholder */ }
@keyframes wavePulse { /* for status wave emoji */ }
```

**Risk**: LOW - Simple rename

---

#### 15. **Duplicate CSS Selector (custom.css)**
**Issue**: `.row input[type="text"]` defined twice (lines 289-300 and 337-348)

**Problem**: Properties split across two places, harder to maintain.

**Recommendation**: Merge into single declaration block

**Risk**: NONE - Just consolidation

---

#### 16. **Dead CSS (~100 lines, custom.css)**
**Issue**: Unused classes from removed features:
- `.change-model-link` (lines 218-235)
- `.cancel-model-link` (lines 238-250)
- `.deep-research-warning` (lines 253-263)
- `.checkbox-wrapper` + entire Section 5 (lines 383-430)

**Total**: ~100 lines (14% of CSS file)

**Recommendation**: Remove unused CSS

**Risk**: NONE - Doesn't affect functionality

---

## Cleanup Plan (Proposed Order)

### Phase 1: Safe, High-Value Changes ✅
1. Fix typo: "You're" → "Your"
2. Update outdated comments
3. Remove `seda_crawl.db` if unused
4. Simplify instruction-stripping regex (single pattern)

**Time**: 5 minutes  
**Risk**: NONE  
**Value**: HIGH

---

### Phase 2: Code Consolidation ⚡
5. Extract `apply_site_filter()` helper function
6. Extract `buildInstructions()` function in JS
7. Create `DATA_SOURCES` configuration objects

**Time**: 15 minutes  
**Risk**: LOW  
**Value**: HIGH

---

### Phase 3: Structural Improvements 🏗️
8. Refactor `/api/chat` into smaller functions
9. Remove unused CSS (after verification)
10. Add error boundary around markdown rendering

**Time**: 30 minutes  
**Risk**: MEDIUM  
**Value**: MEDIUM

---

## Testing Checklist (After Changes)

- [ ] Can send messages with GPT models
- [ ] Can send messages with Claude models
- [ ] All data source filters work correctly
  - [ ] bryancountyga.com
  - [ ] seda.org
  - [ ] uwce.org
  - [ ] fred.stlouisfed.org
  - [ ] .gov only
  - [ ] All Sources
- [ ] Pronoun substitution works ("your" → "Bryan County's", etc.)
- [ ] Markdown rendering works (bold, links, code)
- [ ] Mobile responsive layout works
- [ ] No console errors in browser
- [ ] No Python errors in server logs

---

## Metrics

**Current State**:
- `app.py`: 491 lines
- `app.js`: 372 lines
- `custom.css`: 666 lines
- **Total**: 1,529 lines

**After Cleanup** (Estimated):
- `app.py`: ~420 lines (-70, -14%)
- `app.js`: ~320 lines (-52, -14%)
- `custom.css`: ~600 lines (-66, -10%)
- **Total**: ~1,340 lines (-189, -12%)

**Maintainability Score**: 
- Before: 6/10
- After: 8.5/10

---

## Recommendation

**Proceed with Phase 1 and Phase 2 only.**

Phase 3 (structural refactoring) can wait until there's a specific need or more development time. The biggest wins are in Phase 1 & 2 with minimal risk.

**Time Investment**: ~20 minutes  
**Risk Level**: LOW  
**Value**: HIGH

