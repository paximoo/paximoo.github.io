/**
 * Bookie — Interactive JEE Inorganic Chemistry Practice Web App
 * Pure Vanilla JavaScript
 */

(function () {
  'use strict';

  // --- STATE MANAGEMENT ---
  const state = {
    db: null,
    currentTopicIndex: 0, // 0: Hydrogen, 1: s-Block, 2: p-Block
    currentSectionIndex: 0, // index inside current topic, or -1 for 'all'
    typeFilter: 'all',
    statusFilter: 'all',
    searchQuery: '',
    progress: {}, // { [qUid]: { status: 'correct'|'incorrect'|'unattempted', selectedOpt: null, bookmarked: false, revealed: false } }
    theme: localStorage.getItem('bookie_theme') || 'dark'
  };

  // Unique key generator for questions
  function getQuestionKey(topicIdx, secIdx, qNum) {
    return `t${topicIdx}_s${secIdx}_q${qNum}`;
  }

  // Load progress from localStorage
  function loadProgress() {
    try {
      const saved = localStorage.getItem('bookie_user_progress');
      if (saved) {
        state.progress = JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Could not load progress from localStorage', e);
      state.progress = {};
    }
  }

  // Save progress to localStorage
  function saveProgress() {
    try {
      localStorage.setItem('bookie_user_progress', JSON.stringify(state.progress));
    } catch (e) {
      console.warn('Could not save progress to localStorage', e);
    }
  }

  // --- INITIALIZATION ---
  async function init() {
    loadProgress();
    applyTheme(state.theme);

    // 1. Load Database
    if (window.BOOKIE_DATA) {
      state.db = window.BOOKIE_DATA;
    } else {
      try {
        const response = await fetch('questions.json');
        state.db = await response.json();
      } catch (err) {
        console.error('Failed to fetch questions.json', err);
        document.getElementById('currentSectionTitle').textContent = 'Error loading database. Please run a local web server.';
        return;
      }
    }

    // 2. Setup DOM Elements & Event Listeners
    setupEventListeners();

    // 3. Render Navigation Tree & Initial Section
    renderSidebarTree();
    renderCurrentView();
    updateGlobalStats();
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    // Theme toggle
    const themeBtn = document.getElementById('themeToggle');
    themeBtn.addEventListener('click', () => {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('bookie_theme', state.theme);
      applyTheme(state.theme);
    });

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    let backdrop = document.querySelector('.sidebar-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'sidebar-backdrop';
      document.body.appendChild(backdrop);
    }

    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      backdrop.classList.toggle('active');
    });

    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('active');
    });

    // Type filter
    const typeSelect = document.getElementById('typeFilter');
    typeSelect.addEventListener('change', (e) => {
      state.typeFilter = e.target.value;
      renderCurrentView();
    });

    // Status chips filter
    const statusChips = document.querySelectorAll('.status-chips .chip');
    statusChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        statusChips.forEach((c) => c.classList.remove('active'));
        chip.classList.add('active');
        state.statusFilter = chip.getAttribute('data-status');
        renderCurrentView();
      });
    });

    // Search input
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');

    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.trim().toLowerCase();
      clearSearch.style.display = state.searchQuery ? 'block' : 'none';
      renderCurrentView();
    });

    clearSearch.addEventListener('click', () => {
      searchInput.value = '';
      state.searchQuery = '';
      clearSearch.style.display = 'none';
      renderCurrentView();
    });

    // Reset filters button in empty state
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    resetFiltersBtn.addEventListener('click', () => {
      state.typeFilter = 'all';
      typeSelect.value = 'all';
      state.statusFilter = 'all';
      statusChips.forEach((c) => c.classList.toggle('active', c.getAttribute('data-status') === 'all'));
      state.searchQuery = '';
      searchInput.value = '';
      clearSearch.style.display = 'none';
      renderCurrentView();
    });

    // Toggle all answers button
    const toggleAllBtn = document.getElementById('toggleAllAnswersBtn');
    toggleAllBtn.addEventListener('click', () => {
      const drawers = document.querySelectorAll('.answer-drawer');
      const anyClosed = Array.from(drawers).some((d) => !d.classList.contains('open'));

      drawers.forEach((drawer) => {
        if (anyClosed) {
          drawer.classList.add('open');
        } else {
          drawer.classList.remove('open');
        }
      });

      toggleAllBtn.textContent = anyClosed ? 'Hide All Answers' : 'Show All Answers';
    });

    // Reset progress button
    const resetProgBtn = document.getElementById('resetProgressBtn');
    resetProgBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to reset all your practice progress, bookmarks, and scores?')) {
        state.progress = {};
        saveProgress();
        renderSidebarTree();
        renderCurrentView();
        updateGlobalStats();
      }
    });
  }

  // --- THEME APPLIER ---
  function applyTheme(theme) {
    document.body.classList.remove('theme-dark', 'theme-light');
    document.body.classList.add(`theme-${theme}`);
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  }

  // --- SIDEBAR RENDERING ---
  function renderSidebarTree() {
    const treeNav = document.getElementById('treeNav');
    treeNav.innerHTML = '';

    state.db.topics.forEach((topic, tIdx) => {
      const topicEl = document.createElement('div');
      topicEl.className = 'tree-topic open';

      const totalTopicQs = topic.sections.reduce((acc, s) => acc + s.questions.length, 0);

      // Topic Header
      const headerEl = document.createElement('div');
      headerEl.className = `tree-topic-header ${state.currentTopicIndex === tIdx && state.currentSectionIndex === -1 ? 'active' : ''}`;
      headerEl.innerHTML = `
        <div class="topic-title-group">
          <span class="topic-icon">▶</span>
          <span>${topic.name}</span>
        </div>
        <span class="topic-count">${totalTopicQs} Qs</span>
      `;

      headerEl.addEventListener('click', (e) => {
        // Toggle open/close if clicking arrow, else select all sections in topic
        if (e.target.classList.contains('topic-icon')) {
          topicEl.classList.toggle('open');
        } else {
          state.currentTopicIndex = tIdx;
          state.currentSectionIndex = -1; // view all sections in topic
          highlightActiveNavItem();
          renderCurrentView();
          closeMobileSidebar();
        }
      });

      // Sections container
      const secContainer = document.createElement('div');
      secContainer.className = 'tree-sections';

      topic.sections.forEach((sec, sIdx) => {
        const secItem = document.createElement('div');
        secItem.className = `tree-section-item ${state.currentTopicIndex === tIdx && state.currentSectionIndex === sIdx ? 'active' : ''}`;
        secItem.dataset.topic = tIdx;
        secItem.dataset.section = sIdx;

        // Count completed in section
        let secCorrect = 0;
        sec.questions.forEach((q) => {
          const key = getQuestionKey(tIdx, sIdx, q.q);
          if (state.progress[key]?.status === 'correct') {
            secCorrect++;
          }
        });

        secItem.innerHTML = `
          <span>${sec.name}</span>
          <span class="sec-count">${secCorrect}/${sec.questions.length}</span>
        `;

        secItem.addEventListener('click', () => {
          state.currentTopicIndex = tIdx;
          state.currentSectionIndex = sIdx;
          highlightActiveNavItem();
          renderCurrentView();
          closeMobileSidebar();
        });

        secContainer.appendChild(secItem);
      });

      topicEl.appendChild(headerEl);
      topicEl.appendChild(secContainer);
      treeNav.appendChild(topicEl);
    });

    highlightActiveNavItem();
  }

  function highlightActiveNavItem() {
    document.querySelectorAll('.tree-topic-header').forEach((el, idx) => {
      el.classList.toggle('active', state.currentTopicIndex === idx && state.currentSectionIndex === -1);
    });
    document.querySelectorAll('.tree-section-item').forEach((el) => {
      const tIdx = parseInt(el.dataset.topic, 10);
      const sIdx = parseInt(el.dataset.section, 10);
      el.classList.toggle('active', state.currentTopicIndex === tIdx && state.currentSectionIndex === sIdx);
    });
  }

  function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    if (window.innerWidth < 900) {
      sidebar.classList.remove('open');
      backdrop?.classList.remove('active');
    }
  }

  // --- QUESTION CARD GENERATOR ---
  function createQuestionCard(q, tIdx, sIdx) {
    const qKey = getQuestionKey(tIdx, sIdx, q.q);
    const pState = state.progress[qKey] || {
      status: 'unattempted',
      selectedOpt: null,
      bookmarked: false,
      revealed: false
    };

    const card = document.createElement('div');
    card.className = `q-card ${pState.status}`;
    card.id = `card_${qKey}`;

    // Format type label
    const typeLabelMap = {
      statement_pair: 'Statement I / II',
      assertion_reason: 'Assertion-Reason',
      match_column: 'Match Column',
      single_mcq: 'MCQ',
      integer_type: 'Integer Type',
      fill_blanks: 'Reactions / Blanks',
      bonus: 'NCERT Audit'
    };
    const typeDisplay = typeLabelMap[q.type] || q.type;

    // Header
    const headerEl = document.createElement('div');
    headerEl.className = 'q-header';
    headerEl.innerHTML = `
      <div class="q-header-left">
        <span class="q-num-badge">Q${q.q}</span>
        <span class="q-type-badge type-${q.type}">${typeDisplay}</span>
      </div>
      <div class="q-header-right">
        <span class="status-pill ${pState.status}">${pState.status}</span>
        <button class="star-btn ${pState.bookmarked ? 'active' : ''}" title="Bookmark this question">★</button>
      </div>
    `;

    // Star / Bookmark event
    const starBtn = headerEl.querySelector('.star-btn');
    starBtn.addEventListener('click', () => {
      pState.bookmarked = !pState.bookmarked;
      starBtn.classList.toggle('active', pState.bookmarked);
      state.progress[qKey] = pState;
      saveProgress();
      updateGlobalStats();
    });

    card.appendChild(headerEl);

    // Body Container
    const bodyEl = document.createElement('div');
    bodyEl.className = 'q-body';

    // 1. Text Prompt if present
    if (q.text) {
      const promptEl = document.createElement('div');
      promptEl.className = 'prompt-text';
      promptEl.innerHTML = formatChemistryText(q.text);
      bodyEl.appendChild(promptEl);
    }

    // 2. Statements (for statement_pair and assertion_reason)
    if (q.statements && q.statements.length > 0) {
      const stmtsWrapper = document.createElement('div');
      stmtsWrapper.className = 'statements-wrapper';

      q.statements.forEach((stmt) => {
        const isReason = stmt.label.includes('Reason');
        const stmtBox = document.createElement('div');
        stmtBox.className = `statement-box ${isReason ? 'reason-box' : ''}`;
        stmtBox.innerHTML = `
          <span class="stmt-label">${stmt.label}</span>
          <div class="stmt-text">${formatChemistryText(stmt.text)}</div>
        `;
        stmtsWrapper.appendChild(stmtBox);
      });

      bodyEl.appendChild(stmtsWrapper);
    }

    // 3. Match the Column Grid
    if (q.columns && q.columns.left) {
      const colContainer = document.createElement('div');
      colContainer.className = 'columns-container';

      const leftCol = document.createElement('div');
      leftCol.innerHTML = '<div class="column-header">Column I</div>';
      q.columns.left.forEach((item) => {
        leftCol.innerHTML += `
          <div class="col-item">
            <span class="col-lbl">(${item.label})</span>
            <span>${formatChemistryText(item.text)}</span>
          </div>
        `;
      });

      const rightCol = document.createElement('div');
      rightCol.innerHTML = '<div class="column-header">Column II</div>';
      q.columns.right.forEach((item) => {
        rightCol.innerHTML += `
          <div class="col-item">
            <span class="col-lbl">(${item.label})</span>
            <span>${formatChemistryText(item.text)}</span>
          </div>
        `;
      });

      colContainer.appendChild(leftCol);
      colContainer.appendChild(rightCol);
      bodyEl.appendChild(colContainer);
    }

    // 4. Fill in the blanks equations
    if (q.blanks && q.blanks.length > 0) {
      const blanksList = document.createElement('div');
      blanksList.className = 'blanks-list';
      q.blanks.forEach((b) => {
        const item = document.createElement('div');
        item.className = 'blank-item';
        item.innerHTML = formatChemistryText(b);
        blanksList.appendChild(item);
      });
      bodyEl.appendChild(blanksList);
    }

    // 5. Options Grid (Interactive MCQs)
    let optionBtns = [];
    if (q.options && q.options.length > 0) {
      const optGrid = document.createElement('div');
      optGrid.className = 'options-grid';
      const letters = ['a', 'b', 'c', 'd', 'e'];

      q.options.forEach((optText, optIdx) => {
        const optLetter = letters[optIdx] || String.fromCharCode(97 + optIdx);
        const optBtn = document.createElement('button');
        optBtn.className = 'option-btn';
        optBtn.dataset.opt = optLetter;

        const isSelected = pState.selectedOpt === optLetter;
        if (isSelected) {
          optBtn.classList.add('selected');
        }

        // Highlight correct/incorrect if already revealed
        if (pState.revealed) {
          const normAns = String(q.answer).trim().toLowerCase();
          if (normAns === optLetter) {
            optBtn.classList.add('correct-ans');
          } else if (isSelected) {
            optBtn.classList.add('wrong-choice');
          }
        }

        optBtn.innerHTML = `
          <span class="opt-letter">${optLetter.toUpperCase()}</span>
          <span class="opt-text">${formatChemistryText(optText)}</span>
        `;

        optBtn.addEventListener('click', () => {
          pState.selectedOpt = optLetter;
          pState.revealed = true; // Auto-reveal on choice

          const normAns = String(q.answer).trim().toLowerCase();
          const isCorrect = normAns === optLetter;
          pState.status = isCorrect ? 'correct' : 'incorrect';

          state.progress[qKey] = pState;
          saveProgress();

          // Update UI
          updateCardOptionStyles(card, q, pState);
          openAnswerDrawer(card);
          updateSectionProgress();
          updateGlobalStats();
        });

        optionBtns.push(optBtn);
        optGrid.appendChild(optBtn);
      });

      bodyEl.appendChild(optGrid);
    } else if (q.type === 'integer_type') {
      // Integer input
      const intGroup = document.createElement('div');
      intGroup.className = 'integer-input-group';
      intGroup.innerHTML = `
        <input type="number" class="integer-input" placeholder="Your integer value" value="${pState.selectedOpt || ''}">
        <button class="primary-btn check-int-btn">Submit</button>
      `;

      const input = intGroup.querySelector('.integer-input');
      const submitBtn = intGroup.querySelector('.check-int-btn');

      const handleIntSubmit = () => {
        const userVal = input.value.trim();
        if (!userVal) return;
        pState.selectedOpt = userVal;
        pState.revealed = true;

        const isCorrect = String(q.answer).trim() === userVal;
        pState.status = isCorrect ? 'correct' : 'incorrect';

        state.progress[qKey] = pState;
        saveProgress();

        openAnswerDrawer(card);
        updateSectionProgress();
        updateGlobalStats();
      };

      submitBtn.addEventListener('click', handleIntSubmit);
      input.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') handleIntSubmit();
      });

      bodyEl.appendChild(intGroup);
    }

    card.appendChild(bodyEl);

    // Answer Reveal Accordion Section
    const ansSection = document.createElement('div');
    ansSection.className = 'answer-reveal-section';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'toggle-answer-btn';
    toggleBtn.innerHTML = `<span>${pState.revealed ? 'Hide Answer' : 'Show Answer & NCERT Citation'}</span>`;

    const answerDrawer = document.createElement('div');
    answerDrawer.className = `answer-drawer ${pState.revealed ? 'open' : ''}`;

    // Clean up answer display for header badge
    const displayAnswer = String(q.answer).toUpperCase();

    answerDrawer.innerHTML = `
      <div class="correct-badge-row">
        <span class="ans-badge">Answer: ${displayAnswer}</span>
      </div>
      ${q.explanation ? `<div class="eval-box"><strong>Evaluation:</strong> ${formatChemistryText(q.explanation)}</div>` : ''}
      <div class="ncert-callout">
        <div class="ncert-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <span>Exact NCERT Line Citation</span>
        </div>
        <div class="ncert-quote-text">${formatChemistryText(q.ncert)}</div>
      </div>
      <div class="assessment-buttons">
        <button class="assess-btn mark-correct ${pState.status === 'correct' ? 'active' : ''}">✔ I got it right</button>
        <button class="assess-btn mark-wrong ${pState.status === 'incorrect' ? 'active' : ''}">✖ Mark for review</button>
      </div>
    `;

    // Toggle button handler
    toggleBtn.addEventListener('click', () => {
      pState.revealed = !pState.revealed;
      answerDrawer.classList.toggle('open', pState.revealed);
      toggleBtn.innerHTML = `<span>${pState.revealed ? 'Hide Answer' : 'Show Answer & NCERT Citation'}</span>`;
      state.progress[qKey] = pState;
      saveProgress();

      if (pState.revealed) {
        updateCardOptionStyles(card, q, pState);
      }
    });

    // Manual self-assessment buttons
    const markCorrectBtn = answerDrawer.querySelector('.mark-correct');
    const markWrongBtn = answerDrawer.querySelector('.mark-wrong');

    markCorrectBtn.addEventListener('click', () => {
      pState.status = 'correct';
      markCorrectBtn.classList.add('active');
      markWrongBtn.classList.remove('active');
      state.progress[qKey] = pState;
      saveProgress();
      updateCardHeaderStatus(card, 'correct');
      updateSectionProgress();
      updateGlobalStats();
    });

    markWrongBtn.addEventListener('click', () => {
      pState.status = 'incorrect';
      markWrongBtn.classList.add('active');
      markCorrectBtn.classList.remove('active');
      state.progress[qKey] = pState;
      saveProgress();
      updateCardHeaderStatus(card, 'incorrect');
      updateSectionProgress();
      updateGlobalStats();
    });

    ansSection.appendChild(toggleBtn);
    ansSection.appendChild(answerDrawer);
    card.appendChild(ansSection);

    return card;
  }

  function updateCardOptionStyles(card, q, pState) {
    const normAns = String(q.answer).trim().toLowerCase();
    card.querySelectorAll('.option-btn').forEach((btn) => {
      const optLetter = btn.dataset.opt;
      btn.classList.remove('selected', 'correct-ans', 'wrong-choice');

      if (btn.dataset.opt === pState.selectedOpt) {
        btn.classList.add('selected');
      }

      if (normAns === optLetter) {
        btn.classList.add('correct-ans');
      } else if (btn.dataset.opt === pState.selectedOpt) {
        btn.classList.add('wrong-choice');
      }
    });

    updateCardHeaderStatus(card, pState.status);
  }

  function updateCardHeaderStatus(card, status) {
    const pill = card.querySelector('.status-pill');
    if (pill) {
      pill.className = `status-pill ${status}`;
      pill.textContent = status;
    }
  }

  function openAnswerDrawer(card) {
    const drawer = card.querySelector('.answer-drawer');
    const toggleBtn = card.querySelector('.toggle-answer-btn span');
    if (drawer) {
      drawer.classList.add('open');
    }
    if (toggleBtn) {
      toggleBtn.textContent = 'Hide Answer';
    }
  }

  // Chemistry formatting helper (preserves verbatim, escapes HTML)
  function formatChemistryText(str) {
    if (!str) return '';
    // Escape HTML special chars
    let s = str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Format markdown bold (**bold**) and italics (*italic*)
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Replace linebreaks with <br>
    s = s.replace(/\n/g, '<br>');
    return s;
  }

  // --- VIEW RENDERER ---
  function renderCurrentView() {
    const topic = state.db.topics[state.currentTopicIndex];
    if (!topic) return;

    // 1. Determine questions to display
    let questionsToRender = [];
    let bannerTitle = '';
    let bannerNcert = '';

    if (state.currentSectionIndex === -1) {
      // All sections in topic
      bannerTitle = `${topic.name} — All Sections`;
      bannerNcert = topic.chapter;
      topic.sections.forEach((sec, sIdx) => {
        sec.questions.forEach((q) => {
          questionsToRender.push({ q, sIdx, tIdx: state.currentTopicIndex });
        });
      });
    } else {
      const section = topic.sections[state.currentSectionIndex];
      bannerTitle = section.name;
      bannerNcert = `NCERT Coverage: ${section.ncertRange}`;
      section.questions.forEach((q) => {
        questionsToRender.push({ q, sIdx: state.currentSectionIndex, tIdx: state.currentTopicIndex });
      });
    }

    // 2. Apply Filters: Type, Status, and Search Query
    let filteredQuestions = questionsToRender.filter(({ q, sIdx, tIdx }) => {
      const qKey = getQuestionKey(tIdx, sIdx, q.q);
      const pState = state.progress[qKey] || { status: 'unattempted', bookmarked: false };

      // Type filter
      if (state.typeFilter !== 'all' && q.type !== state.typeFilter) {
        return false;
      }

      // Status filter
      if (state.statusFilter === 'unattempted' && pState.status !== 'unattempted') {
        return false;
      }
      if (state.statusFilter === 'correct' && pState.status !== 'correct') {
        return false;
      }
      if (state.statusFilter === 'incorrect' && pState.status !== 'incorrect') {
        return false;
      }
      if (state.statusFilter === 'bookmarked' && !pState.bookmarked) {
        return false;
      }

      // Search query
      if (state.searchQuery) {
        const query = state.searchQuery;
        const inText = (q.text || '').toLowerCase().includes(query);
        const inExpl = (q.explanation || '').toLowerCase().includes(query);
        const inNcert = (q.ncert || '').toLowerCase().includes(query);
        const inStmts = (q.statements || []).some((s) => s.text.toLowerCase().includes(query));
        const inOpts = (q.options || []).some((o) => o.toLowerCase().includes(query));

        if (!inText && !inExpl && !inNcert && !inStmts && !inOpts) {
          return false;
        }
      }

      return true;
    });

    // 3. Update Banner
    document.getElementById('currentSectionTitle').textContent = bannerTitle;
    document.getElementById('currentNcertRange').textContent = bannerNcert;
    document.getElementById('breadcrumbs').innerHTML = `
      <span class="crumb-topic">${topic.name}</span>
      <span class="crumb-sep">›</span>
      <span class="crumb-sec">${state.currentSectionIndex === -1 ? 'All Questions' : topic.sections[state.currentSectionIndex].name}</span>
    `;

    // 4. Render Cards
    const container = document.getElementById('questionsList');
    const emptyState = document.getElementById('emptyState');
    container.innerHTML = '';

    if (filteredQuestions.length === 0) {
      emptyState.style.display = 'block';
    } else {
      emptyState.style.display = 'none';

      filteredQuestions.forEach(({ q, sIdx, tIdx }) => {
        const card = createQuestionCard(q, tIdx, sIdx);
        container.appendChild(card);
      });
    }

    updateSectionProgress();
  }

  // --- PROGRESS & STATS CALCULATOR ---
  function updateSectionProgress() {
    const topic = state.db.topics[state.currentTopicIndex];
    if (!topic) return;

    let total = 0;
    let completed = 0;

    const countList = state.currentSectionIndex === -1
      ? topic.sections
      : [topic.sections[state.currentSectionIndex]];

    countList.forEach((sec, localIdx) => {
      const sIdx = state.currentSectionIndex === -1 ? localIdx : state.currentSectionIndex;
      sec.questions.forEach((q) => {
        total++;
        const key = getQuestionKey(state.currentTopicIndex, sIdx, q.q);
        if (state.progress[key]?.status === 'correct') {
          completed++;
        }
      });
    });

    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    const fill = document.getElementById('sectionProgressFill');
    const label = document.getElementById('sectionProgressLabel');

    if (fill) fill.style.width = `${percent}%`;
    if (label) label.textContent = `${completed} / ${total} Correct (${percent}%)`;
  }

  function updateGlobalStats() {
    let totalAll = 0;
    let correctAll = 0;

    state.db.topics.forEach((t, tIdx) => {
      t.sections.forEach((s, sIdx) => {
        s.questions.forEach((q) => {
          totalAll++;
          const key = getQuestionKey(tIdx, sIdx, q.q);
          if (state.progress[key]?.status === 'correct') {
            correctAll++;
          }
        });
      });
    });

    const pct = totalAll > 0 ? Math.round((correctAll / totalAll) * 100) : 0;
    const masteryEl = document.getElementById('masteryText');
    if (masteryEl) {
      masteryEl.textContent = `${correctAll} / ${totalAll} (${pct}%)`;
    }
    const totalBadge = document.getElementById('totalQuestionsBadge');
    if (totalBadge) {
      totalBadge.textContent = `${totalAll} Qs`;
    }
  }

  // Boot the app when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

