/**
 * BUILD THE FUTURE - AI Prompt Battle Client Engine
 * Clean, Streamlined Flow: Identifier Page (Name + Email) -> Main Game
 * Inspired by AWS Student Builder Groups
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  const state = {
    participant: null,
    currentChallenge: null,
    currentImage: null,
    currentEvaluation: null,
    generations: [],
    isAdmin: false,
    adminToken: null
  };

  // Safe Socket.IO Connection (optional real-time updates)
  let socket = null;
  try {
    if (typeof io !== "undefined") {
      socket = io();
      socket.on("connect", () => {
        console.log("[Socket.IO] Connected to real-time session");
      });
      socket.on("vote_update", () => {
        if (screens.leaderboard && screens.leaderboard.classList.contains("active")) {
          loadLeaderboard();
        }
      });
      socket.on("new_submission", () => {
        if (screens.leaderboard && screens.leaderboard.classList.contains("active")) {
          loadLeaderboard();
        }
      });
    }
  } catch (err) {
    console.warn("[Socket.IO] Note: Real-time socket not available, standard REST mode active:", err);
  }

  // Subtle Web Audio Feedback (Lazy initialized inside user gestures)
  let audioCtx = null;
  function playAudioTone(type = "click") {
    try {
      if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
        const AudioClass = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioClass();
      }
      if (!audioCtx) return;
      if (audioCtx.state === "suspended") {
        audioCtx.resume();
      }
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      const now = audioCtx.currentTime;

      if (type === "click") {
        osc.frequency.setValueAtTime(520, now);
        osc.frequency.exponentialRampToValueAtTime(780, now + 0.05);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
      } else if (type === "success") {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (e) {
      // Audio autoplay policy or device without audio
    }
  }

  // Toast Notifications
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "toast-error" : type === "success" ? "toast-success" : ""}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // Screen Navigation
  const screens = {
    identifier: document.getElementById("identifier-screen"),
    game: document.getElementById("game-screen"),
    leaderboard: document.getElementById("leaderboard-screen")
  };

  function showScreen(name) {
    Object.values(screens).forEach(s => s && s.classList.remove("active"));
    if (screens[name]) {
      screens[name].classList.add("active");
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (name === "leaderboard") {
      loadLeaderboard();
    }
  }

  // Top Nav Leaderboard toggle
  const navLeaderboardBtn = document.getElementById("nav-leaderboard-btn");
  const backToGameBtn = document.getElementById("back-to-game-btn");

  if (navLeaderboardBtn) {
    navLeaderboardBtn.addEventListener("click", () => {
      playAudioTone("click");
      showScreen("leaderboard");
    });
  }

  if (backToGameBtn) {
    backToGameBtn.addEventListener("click", () => {
      playAudioTone("click");
      if (state.participant) {
        showScreen("game");
      } else {
        showScreen("identifier");
      }
    });
  }

  // Switch User / Logout button
  const changeUserBtn = document.getElementById("change-user-btn");
  if (changeUserBtn) {
    changeUserBtn.addEventListener("click", () => {
      playAudioTone("click");
      try {
        localStorage.removeItem("sbg_builder_name");
        localStorage.removeItem("sbg_builder_email");
        localStorage.removeItem("sbg_participant_id");
      } catch (e) {}

      state.participant = null;
      state.currentChallenge = null;
      state.generations = [];
      
      const userPill = document.getElementById("top-nav-user-pill");
      if (userPill) userPill.classList.add("hidden");
      
      showScreen("identifier");
      showToast("Signed out. Please enter identification to continue.", "info");
    });
  }

  // ---------------------------------------------------------------------------
  // 1. IDENTIFIER PAGE (Name + Email Registration)
  // ---------------------------------------------------------------------------
  const identifierForm = document.getElementById("identifier-form");
  const identifierNameInput = document.getElementById("identifier-name");
  const identifierEmailInput = document.getElementById("identifier-email");
  const identifierError = document.getElementById("identifier-error");
  const startBtn = document.getElementById("start-game-btn");

  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function showIdentifierError(msg) {
    if (identifierError) {
      identifierError.textContent = msg;
      identifierError.classList.remove("hidden");
    }
  }

  function hideIdentifierError() {
    if (identifierError) {
      identifierError.textContent = "";
      identifierError.classList.add("hidden");
    }
  }

  let isSubmittingIdentifier = false;

  async function handleIdentifierSubmit(e) {
    if (e && typeof e.preventDefault === "function") {
      e.preventDefault();
    }
    if (isSubmittingIdentifier) return;

    const name = identifierNameInput ? identifierNameInput.value.trim() : "";
    const email = identifierEmailInput ? identifierEmailInput.value.trim().toLowerCase() : "";

    // Validation
    if (!name) {
      showIdentifierError("Please enter your full name or student builder alias.");
      if (identifierNameInput) identifierNameInput.focus();
      return;
    }

    if (!email || !validateEmail(email)) {
      showIdentifierError("Please enter a valid email address (e.g. builder@university.edu) to store your score.");
      if (identifierEmailInput) identifierEmailInput.focus();
      return;
    }

    hideIdentifierError();
    isSubmittingIdentifier = true;

    if (startBtn) {
      startBtn.disabled = true;
      startBtn.innerHTML = `
        <span class="awsui-spinner-inline"></span>
        <span>Registering &amp; Assigning Challenge...</span>
      `;
    }

    try {
      const resp = await fetch("/api/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email })
      });
      const data = await resp.json();

      if (resp.ok && data.success && data.participant) {
        playAudioTone("success");
        state.participant = data.participant;
        state.currentChallenge = data.challenge;

        // Save to localStorage safely
        try {
          localStorage.setItem("sbg_builder_name", name);
          localStorage.setItem("sbg_builder_email", email);
          localStorage.setItem("sbg_participant_id", data.participant.id);
        } catch (storageErr) {}

        // Update Top Navigation Profile Pill
        updateUserNavProfile(name, email);

        // Update Game Header Strip
        const gName = document.getElementById("game-builder-name");
        const gEmail = document.getElementById("game-builder-email");
        if (gName) gName.textContent = name;
        if (gEmail) gEmail.textContent = `(${email})`;

        // Populate Assigned Challenge
        renderAssignedChallenge(data.challenge);

        // Transition to Main Game Screen
        showScreen("game");
        showToast(`Welcome, ${name}! Assigned challenge: "${data.challenge.title}"`, "success");
      } else {
        showIdentifierError(data.error || "Unable to register session. Please try again.");
      }
    } catch (err) {
      console.error("Join error:", err);
      showIdentifierError("Network connection error. Please ensure the local server is running.");
    } finally {
      isSubmittingIdentifier = false;
      if (startBtn) {
        startBtn.disabled = false;
        startBtn.innerHTML = `
          <span>Enter Main Game &amp; Reveal Challenge</span>
          <span class="btn-arrow">→</span>
        `;
      }
    }
  }

  // Bind Identifier Submit Event Handlers
  if (startBtn) {
    startBtn.addEventListener("click", handleIdentifierSubmit);
  }
  if (identifierForm) {
    identifierForm.addEventListener("submit", handleIdentifierSubmit);
  }
  if (identifierNameInput) {
    identifierNameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleIdentifierSubmit();
      }
    });
  }
  if (identifierEmailInput) {
    identifierEmailInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleIdentifierSubmit();
      }
    });
  }

  function updateUserNavProfile(name, email) {
    const pill = document.getElementById("top-nav-user-pill");
    const nameEl = document.getElementById("top-nav-user-name");
    const emailEl = document.getElementById("top-nav-user-email");
    const avatarEl = document.getElementById("user-avatar-initials");

    if (nameEl) nameEl.textContent = name;
    if (emailEl) emailEl.textContent = email;

    // Generate clean 2-letter initials
    if (avatarEl) {
      const parts = name.trim().split(/\s+/);
      const initials = parts.length >= 2 
        ? (parts[0][0] + parts[1][0]).toUpperCase()
        : name.slice(0, 2).toUpperCase();
      avatarEl.textContent = initials || "SB";
    }

    if (pill) pill.classList.remove("hidden");
  }

  // Pre-fill previously stored builder info without auto-submitting
  function checkSavedIdentity() {
    try {
      const savedName = localStorage.getItem("sbg_builder_name");
      const savedEmail = localStorage.getItem("sbg_builder_email");
      if (savedName && identifierNameInput) {
        identifierNameInput.value = savedName;
      }
      if (savedEmail && identifierEmailInput) {
        identifierEmailInput.value = savedEmail;
      }
    } catch (e) {
      // Storage unavailable
    }
  }

  // ---------------------------------------------------------------------------
  // 2. MAIN GAME: CHALLENGE RENDERING
  // ---------------------------------------------------------------------------
  function renderAssignedChallenge(ch) {
    if (!ch) return;
    state.currentChallenge = ch;

    const catNameEl = document.getElementById("player-cat-name");
    const titleEl = document.getElementById("player-challenge-title");
    const briefEl = document.getElementById("player-challenge-brief");
    const visualEl = document.getElementById("player-visual-goals");
    const kwContainer = document.getElementById("player-keywords-container");

    if (catNameEl) catNameEl.textContent = ch.category;
    if (titleEl) titleEl.textContent = ch.title;
    if (briefEl) briefEl.textContent = ch.brief;
    if (visualEl) visualEl.textContent = ch.visual_goals || "Emphasize futuristic realism and storytelling composition.";

    if (kwContainer) {
      kwContainer.innerHTML = "";
      const keywords = ch.inspiration_keywords || [];
      keywords.forEach(kw => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "keyword-chip";
        chip.textContent = `+ ${kw}`;
        chip.title = "Click to append keyword to your prompt";
        chip.addEventListener("click", () => {
          playAudioTone("click");
          appendModifier(kw);
        });
        kwContainer.appendChild(chip);
      });
    }
  }

  // Re-roll Challenge
  const rerollBtn = document.getElementById("reroll-challenge-btn");
  if (rerollBtn) {
    rerollBtn.addEventListener("click", async () => {
      if (!state.participant) {
        showToast("Please register on the identification page first.", "error");
        return;
      }
      playAudioTone("click");
      rerollBtn.disabled = true;
      rerollBtn.textContent = "🔄 Rolling...";

      try {
        const resp = await fetch("/api/reroll-challenge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ participant_id: state.participant.id })
        });
        const data = await resp.json();
        if (data.success && data.challenge) {
          renderAssignedChallenge(data.challenge);
          showToast(`Assigned New Challenge: "${data.challenge.title}"`, "info");
        } else {
          showToast(data.error || "Could not re-roll challenge.", "error");
        }
      } catch (e) {
        showToast("Network error re-rolling challenge.", "error");
      } finally {
        rerollBtn.disabled = false;
        rerollBtn.textContent = "🔄 Re-roll Challenge";
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 3. PROMPT CONSOLE & MODIFIERS
  // ---------------------------------------------------------------------------
  const promptInput = document.getElementById("prompt-input");
  const charCounter = document.getElementById("char-counter");

  function updateCharCount() {
    if (!promptInput || !charCounter) return;
    const text = promptInput.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    charCounter.textContent = `${text.length} chars / ${words} words`;
  }

  if (promptInput) {
    promptInput.addEventListener("input", updateCharCount);
  }

  function appendModifier(modifier) {
    if (!promptInput) return;
    const current = promptInput.value.trim();
    if (!current) {
      promptInput.value = modifier.startsWith(",") ? modifier.replace(/^,\s*/, "") : modifier;
    } else {
      const cleanMod = modifier.startsWith(",") ? modifier : `, ${modifier}`;
      promptInput.value = current + cleanMod;
    }
    updateCharCount();
    promptInput.focus();
  }

  document.querySelectorAll(".mod-pill-tag").forEach(pill => {
    pill.addEventListener("click", () => {
      playAudioTone("click");
      appendModifier(pill.dataset.insert);
    });
  });

  const clearBtn = document.getElementById("clear-prompt-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (promptInput) {
        promptInput.value = "";
        updateCharCount();
        promptInput.focus();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 4. IMAGE GENERATION & AI EVALUATION
  // ---------------------------------------------------------------------------
  const generateBtn = document.getElementById("generate-image-btn");
  const submitBtn = document.getElementById("submit-masterpiece-btn");
  const overlay = document.getElementById("generating-overlay");
  const activeImg = document.getElementById("active-generated-image");
  const placeholder = document.getElementById("canvas-placeholder");
  const viewFullBtn = document.getElementById("view-full-image-btn");

  async function handleGenerate() {
    const prompt = promptInput ? promptInput.value.trim() : "";
    if (!prompt) {
      showToast("Please formulate a prompt for your assigned challenge.", "error");
      if (promptInput) promptInput.focus();
      return;
    }

    if (!state.currentChallenge) {
      showToast("No challenge assigned. Please identify or re-roll.", "error");
      return;
    }

    playAudioTone("click");
    if (generateBtn) generateBtn.disabled = true;
    if (overlay) overlay.classList.remove("hidden");

    try {
      const resp = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          participant_id: state.participant ? state.participant.id : null,
          challenge_id: state.currentChallenge.id,
          prompt: prompt
        })
      });
      const data = await resp.json();

      if (data.success && data.generation) {
        playAudioTone("success");
        const gen = data.generation;
        state.currentImage = gen.image_data;
        state.currentEvaluation = gen.evaluation;
        state.generations.push(gen);

        // Display image
        if (activeImg) {
          activeImg.src = gen.image_data;
          activeImg.classList.remove("hidden");
        }
        if (placeholder) placeholder.classList.add("hidden");
        if (viewFullBtn) viewFullBtn.disabled = false;

        // Tags
        const sourceTag = document.getElementById("canvas-source-tag");
        if (sourceTag) {
          sourceTag.textContent = `Engine: ${(gen.source || 'AI').toUpperCase()}`;
          sourceTag.classList.remove("hidden");
        }

        const latencyTag = document.getElementById("canvas-latency-tag");
        if (latencyTag) {
          latencyTag.textContent = `${gen.latency || '1.0'}s`;
          latencyTag.classList.remove("hidden");
        }

        // Display AI Evaluation Scorecard
        renderEvaluationScorecard(gen.evaluation);

        // Update history reel
        renderHistoryReel();

        // Enable Submit button
        if (submitBtn) submitBtn.disabled = false;
        showToast("Visual synthesized! AI evaluation ready.", "success");
      } else {
        showToast(data.error || "Generation error. Please retry.", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Network error generating visual.", "error");
    } finally {
      if (generateBtn) generateBtn.disabled = false;
      if (overlay) overlay.classList.add("hidden");
    }
  }

  if (generateBtn) generateBtn.addEventListener("click", handleGenerate);

  // ---------------------------------------------------------------------------
  // 5. RENDER AI EVALUATION SCORECARD
  // ---------------------------------------------------------------------------
  function renderEvaluationScorecard(ev) {
    if (!ev) return;
    const card = document.getElementById("ai-eval-preview-card");
    if (card) card.classList.remove("hidden");

    const chName = document.getElementById("eval-challenge-name");
    if (chName && state.currentChallenge) {
      chName.textContent = `Challenge: ${state.currentChallenge.title} (${state.currentChallenge.category})`;
    }

    const totalEl = document.getElementById("eval-total-score");
    if (totalEl) totalEl.textContent = ev.total_score;

    const tierPill = document.getElementById("eval-tier-pill");
    if (tierPill) tierPill.textContent = ev.tier_badge;

    // 4 Pillars
    const b = ev.breakdown || {};
    const sRel = b.thematic_relevance?.score || 0;
    const sCre = b.creativity_originality?.score || 0;
    const sTec = b.prompt_engineering?.score || 0;
    const sImp = b.future_impact?.score || 0;

    const elRel = document.getElementById("score-rel");
    const barRel = document.getElementById("bar-rel");
    if (elRel) elRel.textContent = `${sRel} / 25`;
    if (barRel) barRel.style.width = `${(sRel / 25) * 100}%`;

    const elCre = document.getElementById("score-cre");
    const barCre = document.getElementById("bar-cre");
    if (elCre) elCre.textContent = `${sCre} / 25`;
    if (barCre) barCre.style.width = `${(sCre / 25) * 100}%`;

    const elTec = document.getElementById("score-tec");
    const barTec = document.getElementById("bar-tec");
    if (elTec) elTec.textContent = `${sTec} / 25`;
    if (barTec) barTec.style.width = `${(sTec / 25) * 100}%`;

    const elImp = document.getElementById("score-imp");
    const barImp = document.getElementById("bar-imp");
    if (elImp) elImp.textContent = `${sImp} / 25`;
    if (barImp) barImp.style.width = `${(sImp / 25) * 100}%`;

    // Commentary & Badges
    const summaryEl = document.getElementById("eval-summary-text");
    if (summaryEl) summaryEl.textContent = ev.summary_comment || "";

    const badgeRow = document.getElementById("eval-badges-row");
    if (badgeRow) {
      badgeRow.innerHTML = "";
      (ev.special_badges || []).forEach(bg => {
        const tag = document.createElement("span");
        tag.className = "badge-tag";
        tag.textContent = bg;
        badgeRow.appendChild(tag);
      });
    }
  }

  // History Reel
  function renderHistoryReel() {
    const reel = document.getElementById("history-reel-container");
    const countBadge = document.getElementById("history-count");
    if (countBadge) countBadge.textContent = state.generations.length;
    if (!reel) return;

    reel.innerHTML = "";
    state.generations.forEach((gen, idx) => {
      const img = document.createElement("img");
      img.src = gen.image_data;
      img.className = `history-thumb ${idx === state.generations.length - 1 ? "selected" : ""}`;
      img.title = `Prompt: ${gen.prompt.slice(0, 50)}... (Score: ${gen.evaluation?.total_score || 'N/A'})`;
      img.addEventListener("click", () => {
        playAudioTone("click");
        document.querySelectorAll(".history-thumb").forEach(t => t.classList.remove("selected"));
        img.classList.add("selected");

        if (activeImg) activeImg.src = gen.image_data;
        if (promptInput) promptInput.value = gen.prompt;
        updateCharCount();
        state.currentImage = gen.image_data;
        state.currentEvaluation = gen.evaluation;
        renderEvaluationScorecard(gen.evaluation);
      });
      reel.appendChild(img);
    });
  }

  // ---------------------------------------------------------------------------
  // 6. SUBMIT MASTERPIECE & STORE SCORE
  // ---------------------------------------------------------------------------
  if (submitBtn) {
    submitBtn.addEventListener("click", async () => {
      if (!state.participant) {
        showToast("Please register on the identification page first.", "error");
        return;
      }
      if (!state.currentImage) {
        showToast("Generate an image first before submitting.", "error");
        return;
      }

      playAudioTone("success");
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <span class="awsui-spinner-inline"></span>
        <span>Submitting...</span>
      `;

      try {
        const resp = await fetch("/api/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            participant_id: state.participant.id,
            prompt: promptInput ? promptInput.value.trim() : "",
            image_data: state.currentImage
          })
        });
        const data = await resp.json();

        if (data.success) {
          showToast(`Masterpiece locked in with AI Score: ${data.submission.ai_score}! Stored under ${state.participant.name} (${state.participant.email}).`, "success");
          showScreen("leaderboard");
        } else {
          showToast(data.error || "Submission failed.", "error");
        }
      } catch (err) {
        showToast("Error submitting masterpiece.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>🏆 Submit &amp; Save Score</span>`;
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 7. LEADERBOARD
  // ---------------------------------------------------------------------------
  const leaderboardBody = document.getElementById("leaderboard-table-body");
  const leaderboardFilter = document.getElementById("leaderboard-cat-filter");

  async function loadLeaderboard() {
    if (!leaderboardBody) return;
    try {
      const url = leaderboardFilter && leaderboardFilter.value ? `/api/leaderboard?category=${encodeURIComponent(leaderboardFilter.value)}` : "/api/leaderboard";
      const resp = await fetch(url);
      const data = await resp.json();
      const list = data.leaderboard || [];

      if (list.length === 0) {
        leaderboardBody.innerHTML = `
          <tr>
            <td colspan="8" class="table-empty">No entries for this category yet. Submit creations from the Prompt Studio!</td>
          </tr>
        `;
        return;
      }

      leaderboardBody.innerHTML = "";
      list.forEach((entry) => {
        const tr = document.createElement("tr");
        const rankClass = entry.rank === 1 ? "rank-1" : entry.rank === 2 ? "rank-2" : entry.rank === 3 ? "rank-3" : "";

        tr.innerHTML = `
          <td class="table-rank ${rankClass}">#${entry.rank}</td>
          <td><strong>${entry.player_name}</strong></td>
          <td><span style="font-size:12px; color:var(--aws-blue); font-family:var(--font-mono);">${entry.player_email || '—'}</span></td>
          <td>
            <div style="font-size:11px; font-weight:700; color:var(--sbg-purple-dark);">${entry.category}</div>
            <div style="font-size:12.5px;">${entry.challenge_title}</div>
          </td>
          <td class="table-score">${entry.ai_score}</td>
          <td style="font-weight:800; font-size:14px;">${entry.composite_score}</td>
          <td><span class="badge-tag">${entry.tier_badge}</span></td>
          <td><button class="awsui-btn-secondary btn-sm inspect-entry-btn">Inspect</button></td>
        `;

        tr.querySelector(".inspect-entry-btn").addEventListener("click", () => {
          openImageModal(entry.image_data, `"${entry.prompt}" — ${entry.player_name} (${entry.player_email || ''}) | Score: ${entry.composite_score} pts`);
        });

        leaderboardBody.appendChild(tr);
      });
    } catch (err) {
      console.error("Leaderboard load error:", err);
    }
  }

  if (leaderboardFilter) {
    leaderboardFilter.addEventListener("change", loadLeaderboard);
  }

  // ---------------------------------------------------------------------------
  // 8. IMAGE ZOOM MODAL
  // ---------------------------------------------------------------------------
  const imageModal = document.getElementById("image-modal");
  const modalImg = document.getElementById("modal-full-image");
  const modalCaption = document.getElementById("modal-image-caption");
  const closeImageModal = document.getElementById("close-image-modal");

  function openImageModal(src, caption) {
    if (!imageModal || !modalImg) return;
    modalImg.src = src;
    if (modalCaption) modalCaption.textContent = caption || "";
    imageModal.classList.remove("hidden");
  }

  if (closeImageModal) {
    closeImageModal.addEventListener("click", () => imageModal.classList.add("hidden"));
  }
  if (imageModal) {
    imageModal.addEventListener("click", (e) => {
      if (e.target === imageModal) imageModal.classList.add("hidden");
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (imageModal && !imageModal.classList.contains("hidden")) imageModal.classList.add("hidden");
      if (adminModal && !adminModal.classList.contains("hidden")) adminModal.classList.add("hidden");
    }
  });

  if (viewFullBtn) {
    viewFullBtn.addEventListener("click", () => {
      if (state.currentImage) {
        openImageModal(state.currentImage, `Prompt: ${promptInput ? promptInput.value : ''}`);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 9. ADMIN MODAL & CONTROLS
  // ---------------------------------------------------------------------------
  const adminModal = document.getElementById("admin-modal");
  const openAdminBtn = document.getElementById("open-admin-btn");
  const closeAdminModal = document.getElementById("close-admin-modal");
  const adminLoginBtn = document.getElementById("admin-login-btn");
  const adminCodeInput = document.getElementById("admin-code-input");
  const adminAuthError = document.getElementById("admin-auth-error");
  const adminAuthPanel = document.getElementById("admin-auth-panel");
  const adminDashPanel = document.getElementById("admin-dashboard-panel");

  if (openAdminBtn) {
    openAdminBtn.addEventListener("click", () => {
      adminModal.classList.remove("hidden");
      if (state.isAdmin) loadAdminChallenges();
    });
  }

  if (closeAdminModal) {
    closeAdminModal.addEventListener("click", () => adminModal.classList.add("hidden"));
  }

  if (adminLoginBtn) {
    adminLoginBtn.addEventListener("click", async () => {
      const code = adminCodeInput ? adminCodeInput.value.trim() : "";
      try {
        const resp = await fetch("/api/admin/auth", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ admin_code: code })
        });
        const data = await resp.json();
        if (data.success) {
          state.isAdmin = true;
          state.adminToken = code;
          if (adminAuthPanel) adminAuthPanel.classList.add("hidden");
          if (adminDashPanel) adminDashPanel.classList.remove("hidden");
          if (adminAuthError) adminAuthError.classList.add("hidden");
          playAudioTone("success");
          loadAdminChallenges();
        } else {
          if (adminAuthError) adminAuthError.classList.remove("hidden");
        }
      } catch (e) {
        if (adminAuthError) adminAuthError.classList.remove("hidden");
      }
    });
  }

  // Admin Tab Navigation
  document.querySelectorAll(".modal-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".modal-tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  const accHead = document.getElementById("toggle-add-challenge-form");
  const accContent = document.getElementById("add-challenge-form-body");
  if (accHead && accContent) {
    accHead.addEventListener("click", () => accContent.classList.toggle("hidden"));
  }

  const adminChallengesTable = document.getElementById("admin-challenges-table-body");
  const adminCatFilter = document.getElementById("admin-cat-filter");

  async function loadAdminChallenges() {
    if (!adminChallengesTable) return;
    try {
      const cat = adminCatFilter ? adminCatFilter.value : "";
      const url = cat ? `/api/challenges?category=${encodeURIComponent(cat)}` : "/api/challenges";
      const resp = await fetch(url);
      const data = await resp.json();

      if (data.stats) {
        const t = document.getElementById("stat-total-challenges");
        const a = document.getElementById("stat-active-challenges");
        const c = document.getElementById("stat-categories-count");
        if (t) t.textContent = data.stats.total;
        if (a) a.textContent = data.stats.active;
        if (c) c.textContent = Object.keys(data.stats.categories || {}).length;
      }

      adminChallengesTable.innerHTML = "";
      (data.challenges || []).forEach(ch => {
        const tr = document.createElement("tr");
        const isActive = ch.is_active;

        tr.innerHTML = `
          <td><span class="status-badge ${isActive ? 'active' : 'inactive'}">${isActive ? 'ACTIVE' : 'INACTIVE'}</span></td>
          <td><strong style="color:var(--sbg-purple-dark);">${ch.category}</strong></td>
          <td>
            <div style="font-weight:700;">${ch.title}</div>
            <div style="font-size:11.5px; color:var(--aws-text-secondary);">${ch.brief.slice(0, 90)}...</div>
          </td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="awsui-btn-secondary btn-sm toggle-act-btn">${isActive ? 'Deactivate' : 'Activate'}</button>
              <button class="awsui-btn-danger btn-sm delete-ch-btn">Delete</button>
            </div>
          </td>
        `;

        tr.querySelector(".toggle-act-btn").addEventListener("click", async () => {
          playAudioTone("click");
          await fetch(`/api/challenges/${ch.id}/toggle`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({ is_active: !isActive })
          });
          loadAdminChallenges();
        });

        tr.querySelector(".delete-ch-btn").addEventListener("click", async () => {
          if (confirm(`Delete challenge "${ch.title}"?`)) {
            playAudioTone("click");
            await fetch(`/api/challenges/${ch.id}`, {
              method: "DELETE",
              headers: { "X-Admin-Code": state.adminToken }
            });
            loadAdminChallenges();
          }
        });

        adminChallengesTable.appendChild(tr);
      });
    } catch (e) {
      console.error(e);
    }
  }

  if (adminCatFilter) {
    adminCatFilter.addEventListener("change", loadAdminChallenges);
  }

  // Add challenge
  const saveChallengeBtn = document.getElementById("save-new-challenge-btn");
  if (saveChallengeBtn) {
    saveChallengeBtn.addEventListener("click", async () => {
      const category = document.getElementById("new-challenge-category")?.value;
      const title = document.getElementById("new-challenge-title")?.value.trim();
      const brief = document.getElementById("new-challenge-brief")?.value.trim();
      const visual = document.getElementById("new-challenge-visual")?.value.trim();
      const keywords = document.getElementById("new-challenge-keywords")?.value.trim();
      const focus = document.getElementById("new-challenge-focus")?.value.trim();

      if (!category || !title || !brief) {
        showToast("Category, title, and brief are required.", "error");
        return;
      }

      try {
        const resp = await fetch("/api/challenges/add", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Code": state.adminToken
          },
          body: JSON.stringify({
            category, title, brief, visual_goals: visual, inspiration_keywords: keywords, evaluation_focus: focus, is_active: true
          })
        });
        const data = await resp.json();
        if (data.success) {
          playAudioTone("success");
          showToast(`Challenge "${title}" added and activated!`, "success");
          document.getElementById("new-challenge-title").value = "";
          document.getElementById("new-challenge-brief").value = "";
          document.getElementById("new-challenge-visual").value = "";
          document.getElementById("new-challenge-keywords").value = "";
          document.getElementById("new-challenge-focus").value = "";
          if (accContent) accContent.classList.add("hidden");
          loadAdminChallenges();
        } else {
          showToast(data.error || "Failed to add challenge.", "error");
        }
      } catch (e) {
        showToast("Error adding challenge.", "error");
      }
    });
  }

  // Reset challenges
  const resetChallengesBtn = document.getElementById("reset-challenges-btn");
  if (resetChallengesBtn) {
    resetChallengesBtn.addEventListener("click", async () => {
      if (confirm("Reset challenge library to standard official challenge set?")) {
        playAudioTone("click");
        await fetch("/api/challenges/reset", {
          method: "POST",
          headers: { "X-Admin-Code": state.adminToken }
        });
        showToast("Challenge catalog reset to official defaults.", "info");
        loadAdminChallenges();
      }
    });
  }

  // Reset competition
  const resetCompBtn = document.getElementById("reset-comp-btn");
  if (resetCompBtn) {
    resetCompBtn.addEventListener("click", async () => {
      if (confirm("DANGER: Reset all participants, generations, and locked-in submissions?")) {
        playAudioTone("click");
        await fetch("/api/admin/reset", {
          method: "POST",
          headers: { "X-Admin-Code": state.adminToken }
        });
        try {
          localStorage.clear();
        } catch (e) {}
        showToast("Competition data reset.", "info");
        window.location.reload();
      }
    });
  }

  // Populate dropdowns
  async function initCategorySelects() {
    try {
      const resp = await fetch("/api/challenges");
      const data = await resp.json();
      const cats = data.categories || [];

      const selects = [
        document.getElementById("leaderboard-cat-filter"),
        document.getElementById("admin-cat-filter"),
        document.getElementById("new-challenge-category")
      ];

      selects.forEach(sel => {
        if (!sel) return;
        const currentVal = sel.value;
        const hasAll = sel.id !== "new-challenge-category";
        sel.innerHTML = hasAll ? '<option value="">All Categories</option>' : '';
        cats.forEach(c => {
          const opt = document.createElement("option");
          opt.value = c;
          opt.textContent = c;
          sel.appendChild(opt);
        });
        if (currentVal) sel.value = currentVal;
      });
    } catch (e) {
      console.error("Init categories error:", e);
    }
  }

  // Initialize
  initCategorySelects();
  checkSavedIdentity();
  updateCharCount();
});
