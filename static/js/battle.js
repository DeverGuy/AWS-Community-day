/**
 * PROMPT QUEST — AWS Gaming & AI Prompt Engineering Challenge Client Engine
 * Matches the "Prompt Quest AWS Gaming Dashboard" Reference Design
 * Preserves 100% of Backend APIs, Evaluation, Image Synthesis & Leaderboard Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  const state = {
    participant: null,
    currentChallenge: null,
    currentReferenceUri: null,
    currentImage: null,
    currentEvaluation: null,
    generations: [],
    isComparing: false,
    hasGenerated: false,
    isGenerating: false,
    isSubmitted: false,
    timerDuration: 180,
    timerRemaining: 180,
    timerDeadline: null,
    timerInterval: null,
    isAdmin: false,
    adminToken: null,
    compState: null,
    timeRemaining: 180
  };

  // ---------------------------------------------------------------------------
  // 0. OPENING AWS LOGO ANIMATION (Precision Single-Element FLIP Transition)
  // ---------------------------------------------------------------------------
  const introStage = document.getElementById("aws-intro-stage");
  const flyingLogo = document.getElementById("aws-flying-logo");
  const navLogoSlot = document.getElementById("navbar-logo-slot");
  const replayIntroBtn = document.getElementById("replay-intro-btn");

  let introTimers = [];
  function clearIntroTimers() {
    introTimers.forEach(t => clearTimeout(t));
    introTimers = [];
  }

  function finishIntroImmediately() {
    clearIntroTimers();
    document.body.classList.remove("intro-active");
    document.body.classList.add("intro-complete");
    if (introStage) {
      introStage.classList.add("stage-hidden");
      introStage.classList.remove("is-Revealed", "is-Docking");
    }
  }

  function runOpeningLogoAnimation(forcePlay = false) {
    if (!introStage || !flyingLogo || !navLogoSlot) {
      finishIntroImmediately();
      return;
    }

    const prefersReducedMotion =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion && !forcePlay) {
      finishIntroImmediately();
      return;
    }

    clearIntroTimers();

    document.body.classList.remove("intro-complete");
    document.body.classList.add("intro-active");
    introStage.classList.remove("stage-hidden", "is-Revealed", "is-Docking");

    // Base dimensions of the flying AWS logo (matches 286:176 aspect ratio)
    const baseW = Math.min(190, Math.max(140, window.innerWidth * 0.19));
    const baseH = baseW * (176 / 286);
    flyingLogo.style.width = `${baseW}px`;
    flyingLogo.style.height = `${baseH}px`;

    const startX = (window.innerWidth - baseW) / 2;
    const startY = (window.innerHeight - baseH) / 2 - 24;

    flyingLogo.style.transition = "none";
    flyingLogo.style.opacity = "0";
    flyingLogo.style.transform = `translate3d(${startX}px, ${startY}px, 0) scale(0.9)`;

    void flyingLogo.offsetWidth;

    flyingLogo.style.transition =
      "transform 0.55s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.45s ease";
    flyingLogo.style.opacity = "1";
    flyingLogo.style.transform = `translate3d(${startX}px, ${startY}px, 0) scale(1)`;
    introStage.classList.add("is-Revealed");

    // Glide from center to exact top-left sidebar slot bounding box
    const tDock = setTimeout(() => {
      const targetRect = navLogoSlot.getBoundingClientRect();
      const targetX = targetRect.width > 0 ? targetRect.left : 28;
      const targetY = targetRect.height > 0 ? targetRect.top : 24;
      const scaleX = (targetRect.width || 78) / baseW;
      const scaleY = (targetRect.height || 48) / baseH;

      introStage.classList.add("is-Docking");
      flyingLogo.style.transition =
        "transform 0.8s cubic-bezier(0.65, 0, 0.15, 1), filter 0.8s ease";
      flyingLogo.style.filter = "drop-shadow(0 2px 8px rgba(182, 154, 255, 0.2))";
      flyingLogo.style.transform = `translate3d(${targetX}px, ${targetY}px, 0) scale(${scaleX}, ${scaleY})`;
    }, 800);

    // Seamless 0ms handoff
    const tComplete = setTimeout(() => {
      finishIntroImmediately();
    }, 1620);

    introTimers.push(tDock, tComplete);
  }

  const isAdminRoute =
    document.body.dataset.adminRoute === "true" ||
    window.location.pathname === "/admin" ||
    window.location.pathname === "/admin/" ||
    window.location.pathname.endsWith("/admin") ||
    window.location.search.includes("admin=true");

  // Instant page view: 0ms delay on reloads
  finishIntroImmediately();

  if (replayIntroBtn) {
    replayIntroBtn.addEventListener("click", () => {
      playAudioTone("click");
      runOpeningLogoAnimation(true);
    });
  }

  // ---------------------------------------------------------------------------
  // SCREENS & MOBILE SIDEBAR NAVIGATION
  // ---------------------------------------------------------------------------
  const screens = {
    identifier: document.getElementById("identifier-screen"),
    game: document.getElementById("game-screen"),
    results: document.getElementById("results-screen"),
    leaderboard: document.getElementById("leaderboard-screen"),
    achievements: document.getElementById("achievements-screen"),
    profile: document.getElementById("profile-screen")
  };

  const sidebarEl = document.getElementById("pq-sidebar");
  const mobileToggleBtn = document.getElementById("mobile-sidebar-toggle");
  if (mobileToggleBtn && sidebarEl) {
    mobileToggleBtn.addEventListener("click", () => {
      sidebarEl.classList.toggle("mobile-open");
    });
  }

  function showScreen(name) {
    Object.values(screens).forEach(s => s && s.classList.remove("active"));
    if (screens[name]) {
      screens[name].classList.add("active");
    }

    // Show Leaderboard button ONLY after the participant's round is finished (or for admins)
    const topLbBtn = document.getElementById("nav-leaderboard-btn");
    if (topLbBtn) {
      if (state.isAdmin || (state.participant && state.hasGenerated && (name === "results" || name === "leaderboard"))) {
        topLbBtn.classList.remove("hidden");
      } else {
        topLbBtn.classList.add("hidden");
      }
    }

    document.querySelectorAll(".nav-route-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.screen === name);
    });

    if (sidebarEl) sidebarEl.classList.remove("mobile-open");
    window.scrollTo({ top: 0, behavior: "smooth" });

    if (name === "leaderboard" || name === "identifier") {
      loadLeaderboard();
    }
    if (name === "profile") {
      syncProfileScreen();
    }
  }

  // ---------------------------------------------------------------------------
  // SOCKET.IO & LIVE DASHBOARD METRICS
  // ---------------------------------------------------------------------------
  let socket = null;
  try {
    if (typeof io !== "undefined") {
      socket = io();
      socket.on("connect", () => {
        console.log("[Socket.IO] Connected to real-time session");
      });
      socket.on("state_update", (payload) => {
        applyLiveCompetitionState(payload);
      });
      socket.on("phase_changed", (data) => {
        applyLiveCompetitionState((data && data.state) ? data.state : data);
      });
      socket.on("competition_reset", () => {
        handleCompetitionReset();
      });
      socket.on("new_submission", () => {
        refreshCompetitionState();
        loadLeaderboard();
      });
      socket.on("teams_updated", () => {
        loadPublicTeams();
        if (state.isAdmin) {
          loadAdminTeams();
        }
      });
    }
  } catch (err) {
    console.warn("[Socket.IO] Standard REST mode active:", err);
  }

  function handleCompetitionReset() {
    stopChallengeTimer();
    state.participant = null;
    state.hasGenerated = false;
    state.currentChallenge = null;
    state.timerRemaining = 180;
    lastHandledPhase = "lobby";

    try {
      localStorage.removeItem("sbg_participant_id");
      localStorage.removeItem("sbg_builder_name");
      localStorage.removeItem("sbg_builder_email");
    } catch (e) { }

    unlockWorkspaceForNewSession();
    if (promptInput) promptInput.value = "";
    if (identifierNameInput) identifierNameInput.value = "";
    if (identifierEmailInput) identifierEmailInput.value = "";

    const userPill = document.getElementById("top-nav-user-pill");
    if (userPill) userPill.classList.add("hidden");

    showScreen("identifier");
    loadLeaderboard();
    showToast("Competition data has been reset by the host.", "info");
  }

  function formatSecondsToHMS(seconds) {
    const s = Math.max(0, Math.floor(Number(seconds) || 0));
    const hrs = String(Math.floor(s / 3600)).padStart(2, "0");
    const mins = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
    const secs = String(s % 60).padStart(2, "0");
    return `${hrs}:${mins}:${secs}`;
  }

  function updateAdminPhaseButtons() { }

  let lastHandledPhase = null;

  async function ensureParticipantActive() {
    if (state.participant && state.participant.id) return state.participant;
    try {
      const storedName = localStorage.getItem("sbg_builder_name");
      const storedEmail = localStorage.getItem("sbg_builder_email");
      const inputName = identifierNameInput ? identifierNameInput.value.trim() : "";
      const inputEmail = identifierEmailInput ? identifierEmailInput.value.trim() : "";

      const name = inputName || storedName || `Driver-${Math.floor(100 + Math.random() * 900)}`;
      const email = inputEmail || storedEmail || `${name.toLowerCase()}@f1-grandprix.com`;

      const resp = await fetch("/api/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email })
      });
      const data = await resp.json();
      if (resp.ok && data.success && data.participant) {
        state.participant = data.participant;
        state.timerDuration = Number(data.timer_duration) || 180;
        const target = data.target_challenge || data.challenge;
        state.currentChallenge = target;
        updateUserNavProfile(name, email);
        const gName = document.getElementById("game-builder-name");
        const gEmail = document.getElementById("game-builder-email");
        if (gName) gName.textContent = name;
        if (gEmail) gEmail.textContent = `(${email})`;
        renderAssignedChallenge(target);
        return data.participant;
      }
    } catch (e) {
      console.warn("Auto-join error:", e);
    }
    return null;
  }

  async function applyLiveCompetitionState(payload) {
    if (!payload) return;
    state.compState = payload;

    if (typeof payload.time_remaining === "number") {
      state.timeRemaining = payload.time_remaining;
    }

    // 1. Navigation Status & Pill
    const statusText = document.getElementById("nav-comp-status");
    const subCountEl = document.getElementById("nav-submissions-count");
    const topLbBtn = document.getElementById("nav-leaderboard-btn");

    if (subCountEl && typeof payload.submission_count === "number") {
      subCountEl.textContent = payload.submission_count;
    }

    if (statusText) {
      statusText.textContent = "Arena Live";
    }

    // Leaderboard button visibility: accessible for admin or once user generated or completed
    if (topLbBtn) {
      if (state.isAdmin || (state.participant && state.hasGenerated)) {
        topLbBtn.classList.remove("hidden");
      }
    }
  }

  async function refreshCompetitionState() {
    try {
      const resp = await fetch("/api/state");
      if (resp.ok) {
        const data = await resp.json();
        applyLiveCompetitionState(data);
      }
    } catch (e) { }
  }

  // Resilient fallback: poll if Socket.IO is disconnected, at a 5s interval
  setInterval(() => {
    if (!socket || !socket.connected) {
      refreshCompetitionState();
      const currentScr = document.querySelector(".screen-view:not(.hidden)");
      if (currentScr && currentScr.id === "screen-leaderboard") {
        loadLeaderboard();
      }
    }
  }, 5000);

  // Update Home Progress Circular Ring & Profile Screen
  function updateDashboardProgressRing(scoreValue, tierTitle) {
    const pctEl = document.getElementById("home-progress-pct");
    const circleEl = document.getElementById("home-progress-circle");
    const levelEl = document.getElementById("home-progress-level");
    const badgeEl = document.getElementById("home-progress-badge-text");

    const numericScore = Math.min(100, Math.max(0, Math.round(Number(scoreValue) || 0)));
    const circumference = 289; // 2 * pi * 46
    const offset = circumference - (numericScore / 100) * circumference;

    if (pctEl) pctEl.textContent = `${numericScore}%`;
    if (circleEl) circleEl.style.strokeDashoffset = String(offset);

    if (levelEl) {
      const lvl = numericScore >= 88 ? 5 : numericScore >= 75 ? 4 : numericScore >= 60 ? 3 : numericScore > 0 ? 2 : 1;
      levelEl.textContent = `Level ${lvl}`;
    }
    if (badgeEl && tierTitle) {
      badgeEl.textContent = tierTitle.replace(/^[^\w]+/, "").trim();
    }
  }

  function syncProfileScreen() {
    const nameEl = document.getElementById("profile-display-name");
    const emailEl = document.getElementById("profile-display-email");
    const avatarEl = document.getElementById("profile-avatar-lg");
    const genEl = document.getElementById("profile-gen-count");
    const bestEl = document.getElementById("profile-best-score");
    const questEl = document.getElementById("profile-quest-name");

    if (state.participant) {
      if (nameEl) nameEl.textContent = state.participant.name;
      if (emailEl) emailEl.textContent = state.participant.email;
      if (avatarEl) avatarEl.textContent = (state.participant.name || "A").slice(0, 2).toUpperCase();
    }
    if (genEl) genEl.textContent = state.generations.length;
    if (bestEl) {
      const best = state.generations.reduce((m, g) => Math.max(m, g.evaluation?.total_score || 0), 0);
      bestEl.textContent = best.toFixed(1);
    }
    if (questEl) {
      questEl.textContent = state.currentChallenge ? state.currentChallenge.title : "Unassigned";
    }
  }

  // Subtle Web Audio Feedback
  let audioCtx = null;
  function playAudioTone(type = "click") {
    try {
      if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
        const AudioClass = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioClass();
      }
      if (!audioCtx) return;
      if (audioCtx.state === "suspended") audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      const now = audioCtx.currentTime;

      if (type === "click") {
        osc.frequency.setValueAtTime(520, now);
        osc.frequency.exponentialRampToValueAtTime(780, now + 0.05);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
      } else if (type === "success") {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
        gain.gain.setValueAtTime(0.07, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (e) { }
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

  // ---------------------------------------------------------------------------
  // NAVIGATION TRIGGERS
  // ---------------------------------------------------------------------------
  const navHomeBtn = document.getElementById("nav-home-btn");
  const navStudioBtn = document.getElementById("nav-studio-btn");
  const navLeaderboardBtn = document.getElementById("nav-leaderboard-btn");
  const navAchievementsBtn = document.getElementById("nav-achievements-btn");
  const navProfileBtn = document.getElementById("nav-profile-btn");
  const brandHomeTrigger = document.getElementById("brand-home-trigger");
  const heroEnterArenaBtn = document.getElementById("hero-enter-arena-btn");
  const aboutLearnMoreBtn = document.getElementById("about-learn-more-btn");
  const homeViewAllLbBtn = document.getElementById("home-view-all-lb-btn");
  const backToGameBtn = document.getElementById("back-to-game-btn");
  const studioToLeaderboardBtn = document.getElementById("studio-to-leaderboard-btn");
  const refreshLeaderboardBtn = document.getElementById("refresh-leaderboard-btn");
  const achToArenaBtn = document.getElementById("ach-to-arena-btn");
  const profileToArenaBtn = document.getElementById("profile-to-arena-btn");
  const defaultAvatarTrigger = document.getElementById("default-avatar-trigger");

  function navigateToArenaOrRegister() {
    playAudioTone("click");
    if (state.participant) {
      showScreen("game");
    } else {
      showScreen("identifier");
      const regDock = document.getElementById("registration-card-dock");
      const nameInput = document.getElementById("identifier-name");
      if (regDock) regDock.scrollIntoView({ behavior: "smooth", block: "center" });
      if (nameInput) setTimeout(() => nameInput.focus(), 250);
    }
  }

  if (navHomeBtn) navHomeBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("identifier"); });
  if (brandHomeTrigger) brandHomeTrigger.addEventListener("click", () => { playAudioTone("click"); showScreen("identifier"); });
  if (navStudioBtn) navStudioBtn.addEventListener("click", navigateToArenaOrRegister);
  if (heroEnterArenaBtn) heroEnterArenaBtn.addEventListener("click", navigateToArenaOrRegister);
  if (aboutLearnMoreBtn) aboutLearnMoreBtn.addEventListener("click", navigateToArenaOrRegister);
  if (achToArenaBtn) achToArenaBtn.addEventListener("click", navigateToArenaOrRegister);
  if (profileToArenaBtn) profileToArenaBtn.addEventListener("click", navigateToArenaOrRegister);
  if (defaultAvatarTrigger) defaultAvatarTrigger.addEventListener("click", navigateToArenaOrRegister);

  if (navLeaderboardBtn) navLeaderboardBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("leaderboard"); });
  if (homeViewAllLbBtn) homeViewAllLbBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("leaderboard"); });
  if (studioToLeaderboardBtn) studioToLeaderboardBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("leaderboard"); });
  if (navAchievementsBtn) navAchievementsBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("achievements"); });
  if (navProfileBtn) navProfileBtn.addEventListener("click", () => { playAudioTone("click"); showScreen("profile"); });

  if (backToGameBtn) {
    backToGameBtn.addEventListener("click", () => {
      playAudioTone("click");
      if (state.participant && state.hasGenerated && state.currentImage) {
        showScreen("results");
      } else if (state.participant) {
        showScreen("game");
      } else {
        showScreen("identifier");
      }
    });
  }

  if (refreshLeaderboardBtn) {
    refreshLeaderboardBtn.addEventListener("click", () => {
      playAudioTone("click");
      loadLeaderboard();
      showToast("Leaderboard standings refreshed.", "info");
    });
  }

  // Switch User / Next Contestant handler (clears saved identity and redirects cleanly to start)
  function handleNextContestantRedirect() {
    playAudioTone("click");
    stopChallengeTimer();
    try {
      localStorage.removeItem("sbg_builder_name");
      localStorage.removeItem("sbg_builder_email");
      localStorage.removeItem("sbg_participant_id");
    } catch (e) { }
    window.location.assign("/");
  }

  function handleSignOutAndReset() {
    playAudioTone("click");
    try {
      localStorage.removeItem("sbg_builder_name");
      localStorage.removeItem("sbg_builder_email");
      localStorage.removeItem("sbg_participant_id");
    } catch (e) { }

    stopChallengeTimer();
    state.participant = null;
    state.currentChallenge = null;
    state.currentReferenceUri = null;
    state.generations = [];
    unlockWorkspaceForNewSession();

    const nameEl = document.getElementById("identifier-name");
    const emailEl = document.getElementById("identifier-email");
    if (nameEl) nameEl.value = "";
    if (emailEl) emailEl.value = "";

    const userPill = document.getElementById("top-nav-user-pill");
    if (userPill) userPill.classList.add("hidden");
    if (defaultAvatarTrigger) defaultAvatarTrigger.classList.remove("hidden");

    showScreen("identifier");
    showToast("Ready for next contestant. Enter name & email to begin.", "info");
  }

  const changeUserBtn = document.getElementById("change-user-btn");
  if (changeUserBtn) changeUserBtn.addEventListener("click", handleSignOutAndReset);

  const nextContestantBtn = document.getElementById("next-contestant-btn");
  if (nextContestantBtn) nextContestantBtn.addEventListener("click", handleNextContestantRedirect);

  // ---------------------------------------------------------------------------
  // 1. IDENTIFIER REGISTRATION (Name + Email)
  // ---------------------------------------------------------------------------
  // 1. IDENTIFIER REGISTRATION (Team Name + Password Authentication)
  // ---------------------------------------------------------------------------
  const identifierForm = document.getElementById("identifier-form");
  const identifierNameInput = document.getElementById("identifier-name");
  const identifierPasswordInput = document.getElementById("identifier-password");
  const togglePasswordBtn = document.getElementById("toggle-team-password-btn");
  const identifierError = document.getElementById("identifier-error");
  const startBtn = document.getElementById("start-game-btn");

  if (togglePasswordBtn && identifierPasswordInput) {
    togglePasswordBtn.addEventListener("click", () => {
      const isPw = identifierPasswordInput.type === "password";
      identifierPasswordInput.type = isPw ? "text" : "password";
      togglePasswordBtn.textContent = isPw ? "🙈" : "👁️";
    });
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
    if (e && typeof e.preventDefault === "function") e.preventDefault();
    if (isSubmittingIdentifier) return;

    const name = identifierNameInput ? identifierNameInput.value.trim() : "";
    const password = identifierPasswordInput ? identifierPasswordInput.value.trim() : "";

    if (!name) {
      showIdentifierError("Please enter your registered team name.");
      if (identifierNameInput) identifierNameInput.focus();
      return;
    }

    if (!password) {
      showIdentifierError("Please enter your team password.");
      if (identifierPasswordInput) identifierPasswordInput.focus();
      return;
    }

    hideIdentifierError();
    isSubmittingIdentifier = true;

    if (startBtn) {
      startBtn.disabled = true;
      startBtn.innerHTML = `<span class="awsui-spinner-inline"></span><span>Authenticating & Entering Paddock...</span>`;
    }

    try {
      const resp = await fetch("/api/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, password })
      });
      const data = await resp.json();

      if (resp.ok && data.success && data.participant) {
        playAudioTone("success");
        unlockWorkspaceForNewSession();
        state.participant = data.participant;
        state.timerDuration = Number(data.timer_duration) || 180;
        const target = data.target_challenge || data.challenge;
        state.currentChallenge = target;

        const pEmail = data.participant.email || `${name.toLowerCase()}@f1-team.com`;
        try {
          localStorage.setItem("sbg_team_name", name);
          localStorage.setItem("sbg_builder_name", name);
          localStorage.setItem("sbg_team_password", password);
          localStorage.setItem("sbg_builder_email", pEmail);
          localStorage.setItem("sbg_participant_id", data.participant.id);
        } catch (storageErr) { }

        updateUserNavProfile(name, pEmail);

        const gName = document.getElementById("game-builder-name");
        const gEmail = document.getElementById("game-builder-email");
        if (gName) gName.textContent = name;
        if (gEmail) gEmail.textContent = `(${pEmail})`;

        renderAssignedChallenge(target);
        refreshCompetitionState();

        const watermarkEl = document.getElementById("arena-watermark");
        if (watermarkEl) {
          watermarkEl.textContent = `🏎️ F1 PROMPT GRAND PRIX • TEAM: ${name.toUpperCase()} • SESSION PROTECTED • 1 ATTEMPT PER TEAM`;
        }

        showScreen("game");
        startChallengeTimer(state.timerDuration);
        showToast(`Welcome, ${name}! Your team password is verified.`, "success");
      } else {
        playAudioTone("error");
        showIdentifierError(data.error || "Unable to register session. Please verify team name and password.");
        if (data.already_completed) {
          const topLbBtn = document.getElementById("nav-leaderboard-btn");
          if (topLbBtn) topLbBtn.classList.remove("hidden");
        }
      }
    } catch (err) {
      console.error("Join error:", err);
      showIdentifierError("Network connection error. Please ensure the server is reachable.");
    } finally {
      isSubmittingIdentifier = false;
      if (startBtn) {
        startBtn.disabled = false;
        startBtn.innerHTML = `<span>Enter Paddock &amp; Start Qualifying</span><span class="btn-arrow">🏎️</span>`;
      }
    }
  }

  if (startBtn) startBtn.addEventListener("click", handleIdentifierSubmit);
  if (identifierForm) identifierForm.addEventListener("submit", handleIdentifierSubmit);
  if (identifierNameInput) {
    identifierNameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); handleIdentifierSubmit(); }
    });
  }
  if (identifierEmailInput) {
    identifierEmailInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); handleIdentifierSubmit(); }
    });
  }

  function updateUserNavProfile(name, email) {
    const pill = document.getElementById("top-nav-user-pill");
    const nameEl = document.getElementById("top-nav-user-name");
    const emailEl = document.getElementById("top-nav-user-email");
    const avatarEl = document.getElementById("user-avatar-initials");

    if (nameEl) nameEl.textContent = name;
    if (emailEl) emailEl.textContent = email;

    if (avatarEl) {
      const parts = name.trim().split(/\s+/);
      const initials = parts.length >= 2
        ? (parts[0][0] + parts[1][0]).toUpperCase()
        : name.slice(0, 2).toUpperCase();
      avatarEl.textContent = initials || "A";
    }

    if (pill) pill.classList.remove("hidden");
    if (defaultAvatarTrigger) defaultAvatarTrigger.classList.add("hidden");
  }

  function checkSavedIdentity() {
    try {
      const savedName = localStorage.getItem("sbg_builder_name");
      const savedEmail = localStorage.getItem("sbg_builder_email");
      if (savedName && identifierNameInput) identifierNameInput.value = savedName;
      if (savedEmail && identifierEmailInput) identifierEmailInput.value = savedEmail;
    } catch (e) { }
  }

  // ---------------------------------------------------------------------------
  // 2. TARGET REFERENCE SCENE GENERATOR & CHALLENGE RENDERING
  // ---------------------------------------------------------------------------
  function buildChallengeReferenceDataURI(ch) {
    const title = (ch && ch.title) || "Target Reference Scene";
    const safeTitle = title.replace(/[<>&"']/g, "");

    const pal = { sky1: "#08080B", sky2: "#211832", accent: "#B69AFF", sec: "#D8C8FF" };

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
      <defs>
        <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="${pal.sky1}"/>
          <stop offset="100%" stop-color="${pal.sky2}"/>
        </linearGradient>
        <radialGradient id="orbGlow" cx="72%" cy="32%" r="42%">
          <stop offset="0%" stop-color="${pal.accent}" stop-opacity="0.5"/>
          <stop offset="55%" stop-color="#35244F" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="${pal.sky1}" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="800" height="450" fill="url(#bgGrad)"/>
      <rect width="800" height="450" fill="url(#orbGlow)"/>
      <line x1="0" y1="320" x2="800" y2="320" stroke="${pal.accent}" stroke-opacity="0.45" stroke-width="1.5"/>
      <line x1="0" y1="360" x2="800" y2="360" stroke="${pal.sec}" stroke-opacity="0.22" stroke-width="1"/>
      <line x1="400" y1="320" x2="120" y2="450" stroke="${pal.accent}" stroke-opacity="0.2" stroke-width="1"/>
      <line x1="400" y1="320" x2="680" y2="450" stroke="${pal.accent}" stroke-opacity="0.2" stroke-width="1"/>
      <circle cx="575" cy="145" r="54" fill="#35244F" fill-opacity="0.55" stroke="${pal.accent}" stroke-width="1.5"/>
      <circle cx="575" cy="145" r="30" fill="${pal.accent}" fill-opacity="0.45"/>
      <path d="M90 320 L90 175 L155 140 L155 320 Z" fill="#211832" stroke="${pal.sec}" stroke-width="1.8"/>
      <path d="M185 320 L185 110 L270 78 L270 320 Z" fill="#35244F" stroke="${pal.accent}" stroke-width="2"/>
      <path d="M300 320 C300 185, 510 185, 510 320 Z" fill="#211832" fill-opacity="0.92" stroke="${pal.sec}" stroke-width="2"/>
      <path d="M550 320 L550 160 L640 125 L640 320 Z" fill="#35244F" stroke="${pal.sec}" stroke-width="1.8"/>
      <path d="M155 210 Q170 198 185 210" fill="none" stroke="${pal.accent}" stroke-width="2.5"/>
      <path d="M270 165 Q410 105 550 185" fill="none" stroke="${pal.sec}" stroke-dasharray="6 4" stroke-width="1.8"/>
      <rect x="24" y="22" width="350" height="54" rx="8" fill="#211832" fill-opacity="0.94" stroke="${pal.accent}" stroke-width="1.2"/>
      <text x="40" y="43" fill="${pal.accent}" font-family="monospace" font-size="11" font-weight="bold">TARGET REFERENCE SCENE</text>
      <text x="40" y="62" fill="#FFFFFF" font-family="sans-serif" font-size="13.5" font-weight="bold">${safeTitle.slice(0, 38)}</text>
    </svg>`;

    return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
  }

  function renderAssignedChallenge(ch) {
    if (!ch) return;
    state.currentChallenge = ch;

    const catNameEl = document.getElementById("player-cat-name");
    const titleEl = document.getElementById("player-challenge-title");
    const kwContainer = document.getElementById("player-keywords-container");
    const refImg = document.getElementById("challenge-reference-img");
    const compareRefImg = document.getElementById("compare-ref-img");

    if (catNameEl) catNameEl.textContent = ch.category || "Visual Challenge";
    if (titleEl) titleEl.textContent = ch.title || "Target Reference Scene";

    // Display the real unique Target Reference Photo (fallback to SVG only if unavailable)
    const refUri = ch.image_data || buildChallengeReferenceDataURI(ch);
    state.currentReferenceUri = refUri;
    if (refImg) refImg.src = refUri;
    if (compareRefImg) compareRefImg.src = refUri;

    if (kwContainer) {
      kwContainer.innerHTML = "";
      (ch.inspiration_keywords || []).forEach(kw => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "keyword-chip";
        chip.textContent = `+ ${kw}`;
        chip.disabled = state.hasGenerated || state.isGenerating;
        chip.addEventListener("click", () => {
          if (state.hasGenerated || state.isGenerating) return;
          playAudioTone("click");
          appendModifier(kw);
        });
        kwContainer.appendChild(chip);
      });
    }
  }

  const inspectRefBtn = document.getElementById("inspect-reference-btn");
  if (inspectRefBtn) {
    inspectRefBtn.addEventListener("click", () => {
      if (state.currentReferenceUri && state.currentChallenge) {
        playAudioTone("click");
        openImageModal(
          state.currentReferenceUri,
          `Target Reference: ${state.currentChallenge.title}`
        );
      }
    });
  }

  // Re-roll Challenge (only allowed before finalizing single-shot generation)
  const rerollBtn = document.getElementById("reroll-challenge-btn");
  if (rerollBtn) {
    rerollBtn.addEventListener("click", async () => {
      if (!state.participant) {
        showToast("Please register on the Home screen first.", "error");
        return;
      }
      if (state.hasGenerated || state.isGenerating) {
        showToast("Your challenge is locked after finalizing your generation.", "error");
        return;
      }
      playAudioTone("click");
      rerollBtn.disabled = true;
      rerollBtn.textContent = "🔄 Rolling...";

      try {
        const resp = await fetch("/api/target-challenge/new", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ participant_id: state.participant.id })
        });
        const data = await resp.json();
        const newTarget = data.target_challenge || data.challenge;
        if (data.success && newTarget) {
          renderAssignedChallenge(newTarget);
          resetUserGuessState();
          startChallengeTimer(Number(data.timer_duration) || state.timerDuration || 180);
          showToast(`New Quest Assigned: "${newTarget.title}" (180s timer reset)`, "info");
        } else {
          showToast(data.error || "Could not re-roll challenge.", "error");
        }
      } catch (e) {
        showToast("Network error re-rolling challenge.", "error");
      } finally {
        if (!state.hasGenerated) {
          rerollBtn.disabled = false;
        }
        rerollBtn.textContent = "🔄 Re-roll Quest";
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 3. PROMPT CONSOLE & ANTI-CHEAT ENFORCEMENT
  // ---------------------------------------------------------------------------
  const promptInput = document.getElementById("prompt-input");
  const charCounter = document.getElementById("char-counter");
  const qualityPill = document.getElementById("prompt-quality-indicator");
  const promptError = document.getElementById("prompt-error-msg");

  function showPromptError(msg) {
    if (promptError) {
      promptError.textContent = msg;
      promptError.classList.remove("hidden");
    }
  }

  function hidePromptError() {
    if (promptError) {
      promptError.textContent = "";
      promptError.classList.add("hidden");
    }
  }

  function updateCharCount() {
    if (!promptInput || !charCounter) return;
    const text = promptInput.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    charCounter.textContent = `${text.length} chars / ${words} words`;

    if (qualityPill) {
      qualityPill.classList.remove("quality-good", "quality-strong");
      if (words === 0) {
        qualityPill.textContent = "Readiness: Waiting";
      } else if (words < 6) {
        qualityPill.textContent = "Readiness: Brief";
      } else if (words < 12) {
        qualityPill.textContent = "Readiness: Good ✓";
        qualityPill.classList.add("quality-good");
      } else {
        qualityPill.textContent = "Readiness: Ready to Generate 🚀";
        qualityPill.classList.add("quality-strong");
      }
    }
  }

  // Client-side Anti-Cheat Patterns (Rule 5: No meta-prompts like "generate an image like the one on screen")
  const CHEAT_PATTERNS = [
    /generate (an?|the)? image like/i,
    /like (the )?(image|picture|photo|graphic) on (the )?screen/i,
    /like (the )?(one|target|reference) on (the )?screen/i,
    /same as (the )?(image|picture|target|one|reference|above)/i,
    /same (image|picture|photo|render) as/i,
    /copy (of )?(the )?(image|picture|target|screen)/i,
    /recreate (the )?(image|picture|target|one on screen)/i,
    /make it look like (the )?(image|picture|target|screen)/i,
    /identical to (the )?(image|picture|target|reference|screen)/i,
    /duplicate (the )?(image|picture|screen)/i,
    /image on screen/i,
    /picture on screen/i,
    /photo on screen/i,
    /the one on screen/i,
    /the screen image/i,
    /the target image/i,
    /the reference image/i,
    /show me the same/i,
    /give me the same/i,
    /generate this image/i,
    /clone the image/i,
    /reproduce the image/i,
    /mimic the image/i,
    /replicate the image/i,
    /copy this/i,
    /like above/i,
    /as above/i,
    /like on screen/i,
    /as seen on screen/i,
    /what is on screen/i,
    /what is shown/i,
    /shown on screen/i,
    /displayed on screen/i,
    /the visual on screen/i
  ];

  function validateClientAntiCheat(text) {
    const trimmed = text.trim();
    if (trimmed.length < 12) {
      return {
        isValid: false,
        msg: "Prompt is too short! Please write a descriptive prompt (at least 12 characters) detailing the scene."
      };
    }
    for (const pat of CHEAT_PATTERNS) {
      if (pat.test(trimmed)) {
        return {
          isValid: false,
          msg: "🚫 Cheat phrase detected! You cannot ask the AI to copy 'the image on screen'. Observe the reference scene and describe what you see."
        };
      }
    }
    return { isValid: true, msg: "" };
  }

  // Temporarily allow paste for testing (flip to true to re-enable Rule 1 anti-paste for live event)
  const BLOCK_PASTE = false;

  if (promptInput) {
    promptInput.addEventListener("input", () => {
      updateCharCount();
      hidePromptError();
    });

    if (BLOCK_PASTE) {
      promptInput.addEventListener("paste", (e) => {
        e.preventDefault();
        playAudioTone("error");
        showToast("🚫 Copy-pasting prompts is disabled for fair competition! Type your description manually.", "error");
        showPromptError("Copy-pasting is strictly disabled for fair play! Please type your prompt manually.");
      });
      promptInput.addEventListener("drop", (e) => {
        e.preventDefault();
        playAudioTone("error");
        showToast("🚫 Drag and drop is disabled! Please type your prompt manually.", "error");
      });
      promptInput.addEventListener("keydown", (e) => {
        if (((e.ctrlKey || e.metaKey) && (e.key === "v" || e.key === "V")) || (e.shiftKey && e.key === "Insert")) {
          e.preventDefault();
          playAudioTone("error");
          showToast("🚫 Keyboard paste is disabled! Please type your prompt manually.", "error");
          showPromptError("Keyboard paste shortcut is disabled. Please type your prompt manually.");
        }
      });
      promptInput.addEventListener("contextmenu", (e) => {
        e.preventDefault();
      });
    }
  }

  function appendModifier(modifier) {
    if (!promptInput || state.hasGenerated || state.isGenerating) return;
    const current = promptInput.value.trim();
    if (!current) {
      promptInput.value = modifier.startsWith(",") ? modifier.replace(/^,\s*/, "") : modifier;
    } else {
      const cleanMod = modifier.startsWith(",") ? modifier : `, ${modifier}`;
      promptInput.value = current + cleanMod;
    }
    updateCharCount();
    hidePromptError();
    promptInput.focus();
  }

  document.querySelectorAll(".mod-pill-tag").forEach(pill => {
    pill.addEventListener("click", () => {
      if (state.hasGenerated || state.isGenerating) return;
      playAudioTone("click");
      appendModifier(pill.dataset.insert);
    });
  });

  const clearBtn = document.getElementById("clear-prompt-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (state.hasGenerated || state.isGenerating) return;
      if (promptInput) {
        promptInput.value = "";
        updateCharCount();
        hidePromptError();
        promptInput.focus();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 4. 180-SECOND SINGLE-SHOT TIMER & FINALIZE / AUTO-GENERATE ENGINE
  // ---------------------------------------------------------------------------
  const generateBtn = document.getElementById("generate-image-btn");
  const overlay = document.getElementById("results-loading-overlay") || document.getElementById("generating-overlay");
  const activeImg = document.getElementById("active-generated-image");
  const resultTargetImg = document.getElementById("result-target-image");
  const resultTargetTitle = document.getElementById("result-target-title");
  const resultSubmittedPrompt = document.getElementById("result-submitted-prompt");
  const resultZoomTargetBtn = document.getElementById("result-zoom-target-btn");
  const placeholder = document.getElementById("canvas-placeholder");
  const viewFullBtn = document.getElementById("view-full-image-btn");
  const toggleCompareBtn = document.getElementById("toggle-compare-btn");
  const comparisonSplitView = document.getElementById("comparison-split-view");
  const compareGenImg = document.getElementById("compare-gen-img");
  const timerPill = document.getElementById("countdown-timer-pill");
  const timerLabelEl = document.getElementById("countdown-timer-label");
  const timerDisplayEl = document.getElementById("countdown-timer-display");

  if (resultZoomTargetBtn) {
    resultZoomTargetBtn.addEventListener("click", () => {
      if (state.currentReferenceUri && state.currentChallenge) {
        playAudioTone("click");
        openImageModal(
          state.currentReferenceUri,
          `Target Reference: ${state.currentChallenge.title}`
        );
      }
    });
  }

  function setComparisonMode(enabled) {
    state.isComparing = enabled;
    if (!comparisonSplitView || !activeImg) return;
    if (enabled && state.currentImage) {
      comparisonSplitView.classList.remove("hidden");
      activeImg.classList.add("hidden");
      if (toggleCompareBtn) toggleCompareBtn.textContent = "▣ Single View";
    } else {
      comparisonSplitView.classList.add("hidden");
      if (state.currentImage) activeImg.classList.remove("hidden");
      if (toggleCompareBtn) toggleCompareBtn.textContent = "⇄ Compare Reference";
    }
  }

  if (toggleCompareBtn) {
    toggleCompareBtn.addEventListener("click", () => {
      playAudioTone("click");
      setComparisonMode(!state.isComparing);
    });
  }

  function resetUserGuessState() {
    state.currentImage = null;
    state.currentEvaluation = null;
    setComparisonMode(false);
    if (activeImg) {
      activeImg.classList.add("hidden");
      activeImg.src = "";
    }
    if (compareGenImg) compareGenImg.src = "";
    if (placeholder) placeholder.classList.remove("hidden");
    if (viewFullBtn) viewFullBtn.disabled = true;
    if (toggleCompareBtn) toggleCompareBtn.classList.add("hidden");
    const evalCard = document.getElementById("ai-eval-preview-card");
    if (evalCard) evalCard.classList.add("hidden");
  }

  function formatClock(totalSec) {
    const clamped = Math.max(0, Math.ceil(totalSec));
    const mins = Math.floor(clamped / 60);
    const secs = clamped % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function setTimerBadge(labelText, displayText, modeClass = "") {
    if (timerLabelEl) timerLabelEl.textContent = labelText;
    if (timerDisplayEl) timerDisplayEl.textContent = displayText;
    if (timerPill) {
      timerPill.classList.remove("timer-warning", "timer-danger", "timer-locked");
      if (modeClass) timerPill.classList.add(modeClass);
    }
  }

  function stopChallengeTimer() {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  }

  function startChallengeTimer(durationSeconds = 180) {
    stopChallengeTimer();
    if (state.hasGenerated) return;

    state.timerRemaining = Math.max(1, Number(durationSeconds) || 180);
    state.timerDeadline = Date.now() + state.timerRemaining * 1000;

    const tick = () => {
      if (state.hasGenerated || state.isGenerating) {
        stopChallengeTimer();
        return;
      }
      const remainingMs = state.timerDeadline - Date.now();
      const remainingSec = Math.max(0, Math.ceil(remainingMs / 1000));
      state.timerRemaining = remainingSec;

      if (remainingSec <= 0) {
        stopChallengeTimer();
        setTimerBadge("TIME UP", "00:00", "timer-danger");
        handleGenerate({ autoTriggered: true });
        return;
      }

      let cls = "";
      if (remainingSec <= 10) {
        cls = "timer-danger";
        if (remainingSec === 10 || remainingSec <= 5) {
          playAudioTone("click");
        }
      } else if (remainingSec <= 30) {
        cls = "timer-warning";
      }
      setTimerBadge("AUTO-GENERATE IN", formatClock(remainingSec), cls);
    };

    tick();
    state.timerInterval = setInterval(tick, 500);
  }

  function setPromptControlsDisabled(disabled) {
    if (promptInput) promptInput.disabled = disabled;
    if (clearBtn) clearBtn.disabled = disabled;
    if (rerollBtn) rerollBtn.disabled = disabled;
    document.querySelectorAll(".mod-pill-tag, .keyword-chip").forEach(btn => {
      btn.disabled = disabled;
    });
  }

  function lockWorkspaceAfterFinalize(btnText = "✅ Final Image Generated (1/1 Used)", timerLabel = "FINALIZED", timerDigits = "LOCKED") {
    stopChallengeTimer();
    state.hasGenerated = true;
    state.isGenerating = false;
    setPromptControlsDisabled(true);
    if (rerollBtn) rerollBtn.classList.add("hidden");
    if (generateBtn) {
      generateBtn.disabled = true;
      generateBtn.innerHTML = `<span>${btnText}</span>`;
    }
    setTimerBadge(timerLabel, timerDigits, "timer-locked");
  }

  function unlockWorkspaceForNewSession() {
    stopChallengeTimer();
    state.hasGenerated = false;
    state.isGenerating = false;
    state.isSubmitted = false;
    state.generations = [];
    state.timerRemaining = state.timerDuration || 180;
    resetUserGuessState();
    if (promptInput) {
      promptInput.value = "";
      updateCharCount();
    }
    hidePromptError();
    setPromptControlsDisabled(false);
    if (rerollBtn) {
      rerollBtn.classList.remove("hidden");
      rerollBtn.disabled = false;
    }
    if (generateBtn) {
      generateBtn.disabled = false;
      generateBtn.innerHTML = `<span>🚀 Finalize &amp; Generate Image</span>`;
    }
    const countBadge = document.getElementById("history-count");
    if (countBadge) countBadge.textContent = "0 / 1";
    const reel = document.getElementById("history-reel-container");
    if (reel) {
      reel.innerHTML = `<p class="history-empty" id="single-shot-status-text">1 chance remaining — prompt auto-generates when the 180s timer reaches 00:00.</p>`;
    }
    setTimerBadge("AUTO-GENERATE IN", formatClock(state.timerDuration || 180), "");
  }

  async function handleGenerate(options = {}) {
    const autoTriggered = Boolean(options && options.autoTriggered);

    if (state.hasGenerated || state.isGenerating) {
      return;
    }

    const prompt = promptInput ? promptInput.value.trim() : "";

    if (!prompt) {
      if (autoTriggered) {
        lockWorkspaceAfterFinalize("⏱️ Time Expired (No Prompt)", "TIME EXPIRED", "00:00");
        playAudioTone("error");
        const msg = "⏱️ 180 seconds elapsed with no prompt entered. Your single attempt has expired.";
        showPromptError(msg);
        showToast(msg, "error");
        const reel = document.getElementById("history-reel-container");
        if (reel) reel.innerHTML = `<p class="history-empty">Attempt expired at 00:00 with an empty prompt.</p>`;
        if (state.participant) {
          fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              participant_id: state.participant.id,
              challenge_id: state.currentChallenge ? state.currentChallenge.id : null,
              prompt: "",
              auto_triggered: true
            })
          }).catch(() => { });
        }
        return;
      }
      showToast("Please type a descriptive prompt before finalizing.", "error");
      showPromptError("Prompt cannot be empty. Describe the target image before finalizing.");
      if (promptInput) promptInput.focus();
      return;
    }

    // Client-side anti-cheat check (allow editing if clicked manually before deadline)
    const antiCheat = validateClientAntiCheat(prompt);
    if (!antiCheat.isValid && !autoTriggered) {
      playAudioTone("error");
      showToast(antiCheat.msg, "error");
      showPromptError(antiCheat.msg);
      if (promptInput) promptInput.focus();
      return;
    }

    hidePromptError();

    if (!state.currentChallenge) {
      showToast("No quest assigned. Please register on Home first.", "error");
      return;
    }

    // Stop timer & lock inputs while finalizing
    stopChallengeTimer();
    state.isGenerating = true;
    setPromptControlsDisabled(true);
    setTimerBadge(
      autoTriggered ? "TIME UP — GENERATING" : "FINALIZING",
      autoTriggered ? "00:00" : formatClock(state.timerRemaining),
      "timer-warning"
    );

    if (autoTriggered) {
      showToast("⏱️ 180s timer finished! Auto-generating your final image now...", "info");
    } else {
      playAudioTone("click");
    }

    if (generateBtn) {
      generateBtn.disabled = true;
      generateBtn.innerHTML = `
        <span class="awsui-spinner-inline"></span>
        <span>${autoTriggered ? "Time Up — Auto-Generating & Judging..." : "Finalizing, Generating & Judging..."}</span>
      `;
    }
    // Prepare Screen 3 (Photo Comparison & Results) and shift there immediately
    if (resultTargetImg && state.currentReferenceUri) {
      resultTargetImg.src = state.currentReferenceUri;
    }
    if (resultTargetTitle && state.currentChallenge) {
      resultTargetTitle.textContent = state.currentChallenge.title || "Target Scene";
    }
    if (resultSubmittedPrompt) {
      resultSubmittedPrompt.textContent = `"${prompt}"`;
    }
    if (activeImg) {
      activeImg.classList.add("hidden");
      activeImg.src = "";
    }
    const evalCardBefore = document.getElementById("ai-eval-preview-card");
    if (evalCardBefore) evalCardBefore.classList.add("hidden");
    const nextFooterBefore = document.getElementById("results-next-footer");
    if (nextFooterBefore) nextFooterBefore.classList.add("hidden");
    if (viewFullBtn) viewFullBtn.disabled = true;

    if (overlay) overlay.classList.remove("hidden");
    showScreen("results");

    let finalizedSuccessfully = false;
    let permanentlyLocked = false;

    try {
      const resp = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          participant_id: state.participant ? state.participant.id : null,
          challenge_id: state.currentChallenge.id,
          prompt: prompt,
          auto_triggered: autoTriggered
        })
      });
      const data = await resp.json();

      if (!resp.ok && data.is_cheating) {
        playAudioTone("error");
        showPromptError(data.error || "Cheat phrase detected.");
        showToast(data.error || "Cheat phrase detected.", "error");
        if (data.locked || autoTriggered) {
          permanentlyLocked = true;
          lockWorkspaceAfterFinalize("🚫 Attempt Disqualified", "DISQUALIFIED", "00:00");
        }
        showScreen("game");
        return;
      }

      if (!resp.ok && data.already_generated) {
        permanentlyLocked = true;
        playAudioTone("error");
        showPromptError(data.error || "You have already used your single generation attempt.");
        showToast(data.error || "Only 1 generation attempt is allowed.", "error");
        lockWorkspaceAfterFinalize("✅ Final Image Already Generated", "FINALIZED", "LOCKED");
        showScreen("game");
        return;
      }

      if (data.success && data.generation) {
        const gen = data.generation;
        finalizedSuccessfully = true;
        permanentlyLocked = true;

        playAudioTone("success");
        state.currentImage = gen.image_data;
        state.currentEvaluation = gen.evaluation;
        state.generations = [gen];
        state.isSubmitted = Boolean(data.submission);

        if (activeImg) {
          activeImg.src = gen.image_data;
          activeImg.classList.remove("hidden");
        }
        if (compareGenImg) compareGenImg.src = gen.image_data;
        if (placeholder) placeholder.classList.add("hidden");
        if (viewFullBtn) viewFullBtn.disabled = false;
        if (toggleCompareBtn) toggleCompareBtn.classList.remove("hidden");

        renderEvaluationScorecard(gen.evaluation);
        renderHistoryReel();
        updateDashboardProgressRing(gen.evaluation?.total_score, gen.evaluation?.tier_badge);
        refreshCompetitionState();

        lockWorkspaceAfterFinalize("✅ Final Image Generated (1/1 Used)", "FINALIZED", "1 / 1");

        const nextFooterDone = document.getElementById("results-next-footer");
        if (nextFooterDone) nextFooterDone.classList.remove("hidden");

        showScreen("results");
        const prefix = autoTriggered ? "⏱️ Auto-generated at 00:00! " : "Final image generated & score saved! ";
        showToast(`${prefix}AI Judge Match Score: ${gen.evaluation?.total_score || 0}/100`, "success");
      } else {
        playAudioTone("error");
        const errMsg = data.error || "Image generation failed. Please check CF_WORKER_URL and CF_WORKER_API_KEY in .env.";
        showPromptError(errMsg);
        showToast(errMsg, "error");
        showScreen("game");
      }
    } catch (err) {
      console.error(err);
      showToast("Network error generating visual. You can retry finalizing.", "error");
      showScreen("game");
    } finally {
      state.isGenerating = false;
      if (overlay) overlay.classList.add("hidden");
      if (!finalizedSuccessfully && !permanentlyLocked) {
        setPromptControlsDisabled(false);
        if (generateBtn) {
          generateBtn.disabled = false;
          generateBtn.innerHTML = `<span>🚀 Finalize &amp; Generate Image</span>`;
        }
        if (!autoTriggered && state.timerRemaining > 0) {
          startChallengeTimer(state.timerRemaining);
        } else {
          setTimerBadge("RETRY FINALIZE", "00:00", "timer-warning");
        }
      }
    }
  }

  if (generateBtn) generateBtn.addEventListener("click", () => handleGenerate({ autoTriggered: false }));

  // ---------------------------------------------------------------------------
  // 5. RENDER UNBIASED DUAL-IMAGE AI EVALUATION SCORECARD
  // ---------------------------------------------------------------------------
  function renderEvaluationScorecard(ev) {
    if (!ev) return;
    const card = document.getElementById("ai-eval-preview-card");
    if (card) card.classList.remove("hidden");

    const chName = document.getElementById("eval-challenge-name");
    if (chName && state.currentChallenge) {
      chName.textContent = `Visual Comparison: "${state.currentChallenge.title}"`;
    }

    const totalEl = document.getElementById("eval-total-score");
    if (totalEl) totalEl.textContent = ev.total_score;

    const tierPill = document.getElementById("eval-tier-pill");
    if (tierPill) {
      tierPill.textContent = ev.tier_badge || "🎯 MATCH EVALUATED";
      if (ev.tier_color) tierPill.style.backgroundColor = ev.tier_color;
    }

    const b = ev.breakdown || {};
    const sRel = b.visual_similarity?.score ?? b.thematic_relevance?.score ?? 0;
    const sCre = b.subject_match?.score ?? b.creativity_originality?.score ?? 0;
    const sTec = b.style_match?.score ?? b.prompt_engineering?.score ?? 0;
    const sImp = b.prompt_precision?.score ?? b.future_impact?.score ?? 0;

    const elRel = document.getElementById("score-rel");
    const barRel = document.getElementById("bar-rel");
    const commRel = document.getElementById("comm-rel");
    if (elRel) elRel.textContent = `${sRel} / 25`;
    if (barRel) barRel.style.width = `${(sRel / 25) * 100}%`;
    if (commRel) commRel.textContent = b.visual_similarity?.comment || "";

    const elCre = document.getElementById("score-cre");
    const barCre = document.getElementById("bar-cre");
    const commCre = document.getElementById("comm-cre");
    if (elCre) elCre.textContent = `${sCre} / 25`;
    if (barCre) barCre.style.width = `${(sCre / 25) * 100}%`;
    if (commCre) commCre.textContent = b.subject_match?.comment || "";

    const elTec = document.getElementById("score-tec");
    const barTec = document.getElementById("bar-tec");
    const commTec = document.getElementById("comm-tec");
    if (elTec) elTec.textContent = `${sTec} / 25`;
    if (barTec) barTec.style.width = `${(sTec / 25) * 100}%`;
    if (commTec) commTec.textContent = b.style_match?.comment || "";

    const elImp = document.getElementById("score-imp");
    const barImp = document.getElementById("bar-imp");
    const commImp = document.getElementById("comm-imp");
    if (elImp) elImp.textContent = `${sImp} / 25`;
    if (barImp) barImp.style.width = `${(sImp / 25) * 100}%`;
    if (commImp) commImp.textContent = b.prompt_precision?.comment || "";

    const targetObsEl = document.getElementById("target-obs-text");
    if (targetObsEl) {
      targetObsEl.textContent = Array.isArray(ev.target_observations)
        ? ev.target_observations.map(x => `• ${x}`).join("\n")
        : (ev.target_observations || "Analyzed target reference scene elements.");
    }

    const userObsEl = document.getElementById("user-obs-text");
    if (userObsEl) {
      userObsEl.textContent = Array.isArray(ev.user_observations)
        ? ev.user_observations.map(x => `• ${x}`).join("\n")
        : (ev.user_observations || "Analyzed replica visual features.");
    }

    const summaryEl = document.getElementById("eval-summary-text");
    if (summaryEl) summaryEl.textContent = ev.unbiased_critique || ev.summary_comment || "";

    const featuresRow = document.getElementById("eval-features-row");
    if (featuresRow) {
      featuresRow.innerHTML = "";
      (ev.matched_features || []).forEach(f => {
        const pill = document.createElement("span");
        pill.className = "feature-pill-matched";
        pill.textContent = `✓ ${f}`;
        featuresRow.appendChild(pill);
      });
      (ev.discrepancies || ev.divergent_features || []).forEach(f => {
        const pill = document.createElement("span");
        pill.className = "feature-pill-divergent";
        pill.textContent = `⚠️ ${f}`;
        featuresRow.appendChild(pill);
      });
    }

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

  function renderHistoryReel() {
    const reel = document.getElementById("history-reel-container");
    const countBadge = document.getElementById("history-count");
    if (countBadge) countBadge.textContent = `${state.generations.length} / 1`;
    if (!reel) return;

    reel.innerHTML = "";
    state.generations.forEach((gen) => {
      const img = document.createElement("img");
      img.src = gen.image_data;
      img.className = "history-thumb selected";
      img.title = `Final Generation — Score: ${gen.evaluation?.total_score ?? "N/A"}/100`;
      reel.appendChild(img);

      const summaryNote = document.createElement("span");
      summaryNote.className = "history-empty";
      summaryNote.style.marginLeft = "10px";
      summaryNote.textContent = `Finalized (${gen.auto_triggered ? "Auto-generated at 00:00" : "Manual Finalize"}) — Score: ${gen.evaluation?.total_score ?? 0}/100`;
      reel.appendChild(summaryNote);
    });
  }

  // ---------------------------------------------------------------------------
  // 7. LEADERBOARD & HOME "TOP PLAYERS" WIDGET
  // ---------------------------------------------------------------------------
  const leaderboardBody = document.getElementById("leaderboard-table-body");
  const leaderboardFilter = document.getElementById("leaderboard-cat-filter");
  const podiumSection = document.getElementById("leaderboard-podium-section");
  const homeTopPlayersList = document.getElementById("home-top-players-list");

  function renderHomeTopPlayersWidget(list) {
    if (!homeTopPlayersList) return;

    const displayItems =
      list && list.length > 0
        ? list.slice(0, 3).map((e, i) => ({
          rank: i + 1,
          name: e.player_name,
          score: `${e.composite_score} pts`
        }))
        : [
          { rank: 1, name: "ScuderiaFerrari", score: "98.5" },
          { rank: 2, name: "RedBullRacing", score: "93.2" },
          { rank: 3, name: "MercedesAMGF1", score: "89.7" }
        ];

    homeTopPlayersList.innerHTML = "";
    displayItems.forEach(item => {
      const row = document.createElement("div");
      row.className = "pq-mini-lb-row";
      const initials = item.name.slice(0, 1).toUpperCase();
      row.innerHTML = `
        <div class="pq-mini-lb-left">
          <span class="pq-medal-badge pq-medal-${item.rank}">${item.rank}</span>
          <span class="pq-mini-rank-num">${item.rank}</span>
          <span class="pq-mini-avatar">${initials}</span>
          <span class="pq-mini-name">${item.name}</span>
        </div>
        <span class="pq-mini-score">${item.score}</span>
      `;
      homeTopPlayersList.appendChild(row);
    });
  }

  async function loadLeaderboard() {
    try {
      const resp = await fetch("/api/leaderboard");
      const data = await resp.json();
      const list = data.leaderboard || [];

      renderHomeTopPlayersWidget(list);
      const subCountEl = document.getElementById("nav-submissions-count");
      if (subCountEl) subCountEl.textContent = list.length;

      if (!leaderboardBody) return;

      if (list.length === 0) {
        if (podiumSection) {
          podiumSection.innerHTML = "";
          podiumSection.classList.add("hidden");
        }
        leaderboardBody.innerHTML = `
          <tr>
            <td colspan="8" class="table-empty">No submissions locked in yet. Enter the Arena to claim Rank #1!</td>
          </tr>
        `;
        return;
      }

      if (podiumSection) {
        podiumSection.innerHTML = "";
        if (state.isAdmin) {
          podiumSection.classList.remove("hidden");
          list.slice(0, 3).forEach(entry => {
            const card = document.createElement("div");
            card.className = `podium-card podium-rank-${entry.rank}`;
            card.innerHTML = `
              <div class="podium-img-wrap" title="Click to inspect full resolution">
                <img src="${entry.image_data}" alt="${entry.player_name}" loading="lazy">
                <span class="podium-rank-badge">#${entry.rank} ${entry.rank === 1 ? "🏆" : entry.rank === 2 ? "🥈" : "🥉"}</span>
              </div>
              <div class="podium-body">
                <div class="podium-builder-row">
                  <span class="podium-builder-name">${entry.player_name}</span>
                  <span class="podium-score-val">${entry.composite_score} pts</span>
                </div>
                <div class="podium-cat-text">${entry.challenge_title}</div>
                <p class="podium-prompt-snip">"${entry.prompt}"</p>
              </div>
            `;
            card.querySelector(".podium-img-wrap").addEventListener("click", () => {
              openImageModal(
                entry.image_data,
                `"${entry.prompt}" — ${entry.player_name} (${entry.player_email || ""}) | Score: ${entry.composite_score} pts`
              );
            });
            podiumSection.appendChild(card);
          });
        } else {
          podiumSection.classList.add("hidden");
        }
      }

      leaderboardBody.innerHTML = "";
      list.forEach(entry => {
        const tr = document.createElement("tr");
        const rankClass =
          entry.rank === 1 ? "rank-1" : entry.rank === 2 ? "rank-2" : entry.rank === 3 ? "rank-3" : "";

        tr.innerHTML = `
          <td class="table-rank ${rankClass}">#${entry.rank}</td>
          <td><strong>${entry.player_name}</strong></td>
          <td><span style="font-size:12px; color:var(--aws-blue); font-family:var(--font-mono);">${entry.player_email || "—"}</span></td>
          <td>
            <div style="font-size:13px; font-weight:700;">${entry.challenge_title}</div>
          </td>
          <td class="table-score" style="font-weight:800; font-size:14px; font-family:var(--font-mono);">${entry.ai_score} <span style="font-size:11px; color:var(--pq-text-secondary); font-weight:400;">/ 100</span></td>
          <td><span class="badge-tag">${entry.tier_badge}</span></td>
          <td>
            <button type="button" class="pq-btn-outline-pill btn-sm inspect-entry-btn">Inspect ↗</button>
          </td>
        `;

        const inspectBtn = tr.querySelector(".inspect-entry-btn");
        if (inspectBtn) {
          inspectBtn.addEventListener("click", () => {
            if (entry.target_image) {
              openDualImageModal(
                entry.target_image,
                entry.image_data,
                `"${entry.prompt}" — ${entry.player_name} (${entry.player_email || ""}) | Match Score: ${entry.ai_score}/100 pts${entry.unbiased_critique ? " | Judge: " + entry.unbiased_critique : ""}`
              );
            } else {
              openImageModal(
                entry.image_data,
                `"${entry.prompt}" — ${entry.player_name} (${entry.player_email || ""}) | Score: ${entry.composite_score} pts`
              );
            }
          });
        }

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
  // 8. IMAGE ZOOM & DUAL-COMPARISON MODAL
  // ---------------------------------------------------------------------------
  const imageModal = document.getElementById("image-modal");
  const modalSingleView = document.getElementById("modal-single-view");
  const modalImg = document.getElementById("modal-full-image");
  const modalDualView = document.getElementById("modal-dual-view");
  const modalDualTarget = document.getElementById("modal-dual-target");
  const modalDualUser = document.getElementById("modal-dual-user");
  const modalCaption = document.getElementById("modal-image-caption");
  const closeImageModal = document.getElementById("close-image-modal");

  function openImageModal(src, caption) {
    if (!imageModal || !modalImg) return;
    if (modalSingleView) modalSingleView.classList.remove("hidden");
    if (modalDualView) modalDualView.classList.add("hidden");
    modalImg.src = src;
    if (modalCaption) modalCaption.textContent = caption || "";
    imageModal.classList.remove("hidden");
  }

  function openDualImageModal(targetSrc, userSrc, caption) {
    if (!imageModal || !modalDualView) return;
    if (modalSingleView) modalSingleView.classList.add("hidden");
    if (modalDualView) modalDualView.classList.remove("hidden");
    if (modalDualTarget) modalDualTarget.src = targetSrc || "";
    if (modalDualUser) modalDualUser.src = userSrc || "";
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
        openImageModal(state.currentImage, `Prompt: ${promptInput ? promptInput.value : ""}`);
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

  // Restore persistent admin session if available
  try {
    const savedAdminToken = sessionStorage.getItem("sbg_admin_token");
    if (savedAdminToken) {
      state.adminToken = savedAdminToken;
      state.isAdmin = true;
      if (adminAuthPanel) adminAuthPanel.classList.add("hidden");
      if (adminDashPanel) adminDashPanel.classList.remove("hidden");
      if (adminAuthError) adminAuthError.classList.add("hidden");
    }
  } catch (e) { }

  if (openAdminBtn) {
    if (isAdminRoute) {
      openAdminBtn.classList.remove("hidden");
    } else {
      openAdminBtn.classList.add("hidden");
    }
    openAdminBtn.addEventListener("click", () => {
      adminModal.classList.remove("hidden");
      if (state.isAdmin) {
        loadAdminChallenges();
        loadAdminTeams();
      }
    });
  }

  if (adminCodeInput && adminLoginBtn) {
    adminCodeInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        adminLoginBtn.click();
      }
    });
  }

  // Automatically open Admin Command Center login when visiting /admin directly
  if (isAdminRoute && adminModal) {
    adminModal.classList.remove("hidden");
    if (adminCodeInput) {
      setTimeout(() => adminCodeInput.focus(), 80);
    }
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
          try {
            sessionStorage.setItem("sbg_admin_token", code);
          } catch (e) { }
          if (adminAuthPanel) adminAuthPanel.classList.add("hidden");
          if (adminDashPanel) adminDashPanel.classList.remove("hidden");
          if (adminAuthError) adminAuthError.classList.add("hidden");
          playAudioTone("success");
          loadAdminChallenges();
          loadAdminTeams();
          loadLeaderboard();
        } else {
          if (adminAuthError) adminAuthError.classList.remove("hidden");
        }
      } catch (e) {
        if (adminAuthError) adminAuthError.classList.remove("hidden");
      }
    });
  }

  document.querySelectorAll(".modal-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".modal-tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) {
        target.classList.add("active");
      }
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
    const imagesGrid = document.getElementById("admin-images-grid");
    try {
      const resp = await fetch("/api/challenges");
      const data = await resp.json();
      const challenges = data.challenges || [];
      cachedChallengesForTeams = challenges;

      if (data.stats) {
        const t = document.getElementById("stat-total-challenges");
        const a = document.getElementById("stat-active-challenges");
        if (t) t.textContent = data.stats.total;
        if (a) a.textContent = data.stats.active;
      }

      // 1. Populate Table (if present)
      if (adminChallengesTable) {
        adminChallengesTable.innerHTML = "";
        challenges.forEach(ch => {
          const tr = document.createElement("tr");
          const isActive = ch.is_active;

          tr.innerHTML = `
            <td><span class="status-badge ${isActive ? "active" : "inactive"}">${isActive ? "ACTIVE" : "INACTIVE"}</span></td>
            <td>
              <div style="font-weight:700;">${ch.title}</div>
              <div style="font-size:11.5px; color:var(--pq-text-secondary);">${(ch.brief || "").slice(0, 110)}...</div>
            </td>
            <td>
              <div style="display:flex; gap:6px; align-items:center;">
                <button type="button" class="pq-btn-outline-pill btn-sm toggle-act-btn">${isActive ? "Deactivate" : "Activate"}</button>
                <button type="button" class="awsui-btn-danger btn-sm delete-ch-btn" style="margin-top:0;">Delete</button>
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
              loadAdminTeams();
            }
          });

          adminChallengesTable.appendChild(tr);
        });
      }

      // 2. Populate Visual Cards Grid (#admin-images-grid)
      if (imagesGrid) {
        imagesGrid.innerHTML = "";
        if (challenges.length === 0) {
          imagesGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:32px; color:var(--pq-text-secondary);">No target images available. Upload one above or click 'Restore Defaults'.</div>`;
          return;
        }

        challenges.forEach(ch => {
          const card = document.createElement("div");
          card.className = "pq-dash-card admin-image-card";
          card.style.cssText = "padding:12px; display:flex; flex-direction:column; gap:8px; border:1px solid rgba(225,6,0,0.3); background:rgba(22,22,31,0.9); border-radius:10px; transition:transform 0.15s ease;";

          const assignedCount = cachedAdminTeamsList.filter(t => t.assigned_challenge_id === ch.id).length;
          const imgUrl = ch.static_url || ch.image_data || "/static/images/f1-logo.svg";

          card.innerHTML = `
            <div style="position:relative; width:100%; height:135px; border-radius:6px; overflow:hidden; background:#000;">
              <img src="${imgUrl}" alt="${ch.title}" style="width:100%; height:100%; object-fit:cover;">
              <span class="status-badge ${ch.is_active ? 'active' : 'inactive'}" style="position:absolute; top:6px; right:6px; font-size:10px; padding:2px 8px;">
                ${ch.is_active ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <div>
              <div style="display:flex; justify-content:space-between; align-items:baseline; gap:6px;">
                <h5 style="margin:0; font-size:13.5px; color:#FFFFFF; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${ch.title}</h5>
                <span style="font-size:11px; color:#FFD200; font-family:var(--font-mono); font-weight:700; flex-shrink:0;">
                  ${assignedCount} team${assignedCount === 1 ? '' : 's'}
                </span>
              </div>
              <p style="margin:4px 0 0; font-size:11.5px; color:var(--pq-text-secondary); line-height:1.3; height:30px; overflow:hidden; text-overflow:ellipsis;">
                ${ch.brief || "Reference target image"}
              </p>
            </div>
            <div style="display:flex; gap:6px; margin-top:auto; padding-top:4px;">
              <button type="button" class="pq-btn-orange-pill btn-sm assign-card-to-sel-btn" data-ch-id="${ch.id}" style="flex:1; font-size:11px; padding:5px 8px;" title="Assign this image to currently selected teams">
                <span>🎯 Assign to Selected</span>
              </button>
              <button type="button" class="pq-btn-outline-pill btn-sm toggle-card-act-btn" data-ch-id="${ch.id}" style="font-size:11px; padding:5px 8px;">
                ${ch.is_active ? "Disable" : "Enable"}
              </button>
              <button type="button" class="awsui-btn-danger btn-sm del-card-btn" data-ch-id="${ch.id}" style="font-size:11px; padding:5px 8px; margin:0;" title="Delete challenge">
                🗑️
              </button>
            </div>
          `;

          // Assign to currently selected teams button
          const assignSelBtn = card.querySelector(".assign-card-to-sel-btn");
          assignSelBtn.addEventListener("click", async () => {
            if (selectedTeamIds.size === 0) {
              showToast("Please select one or more teams first using the checkboxes in the Teams tab.", "warning");
              const teamsTabBtn = document.querySelector('.modal-tab-btn[data-tab="tab-teams"]');
              if (teamsTabBtn) teamsTabBtn.click();
              return;
            }
            playAudioTone("click");
            try {
              const aResp = await fetch("/api/teams/assign", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-Admin-Code": state.adminToken
                },
                body: JSON.stringify({
                  team_ids: Array.from(selectedTeamIds),
                  challenge_id: ch.id
                })
              });
              const aData = await aResp.json();
              if (aData.success) {
                playAudioTone("success");
                showToast(`Assigned "${ch.title}" to ${aData.count} selected teams!`, "success");
                loadAdminTeams();
                loadAdminChallenges();
              } else {
                showToast(aData.error || "Assignment failed.", "error");
              }
            } catch (err) {
              showToast("Network error assigning challenge.", "error");
            }
          });

          // Toggle card active
          const toggleCardBtn = card.querySelector(".toggle-card-act-btn");
          toggleCardBtn.addEventListener("click", async () => {
            playAudioTone("click");
            await fetch(`/api/challenges/${ch.id}/toggle`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Admin-Code": state.adminToken
              },
              body: JSON.stringify({ is_active: !ch.is_active })
            });
            loadAdminChallenges();
          });

          // Delete card
          const delCardBtn = card.querySelector(".del-card-btn");
          delCardBtn.addEventListener("click", async () => {
            if (confirm(`Delete target image challenge "${ch.title}"?`)) {
              playAudioTone("click");
              await fetch(`/api/challenges/${ch.id}`, {
                method: "DELETE",
                headers: { "X-Admin-Code": state.adminToken }
              });
              loadAdminChallenges();
              loadAdminTeams();
            }
          });

          imagesGrid.appendChild(card);
        });
      }

      // Update batch image select dropdown in Tab 1
      updateBatchBarUI();
    } catch (e) {
      console.error(e);
    }
  }

  if (adminCatFilter) {
    adminCatFilter.addEventListener("change", loadAdminChallenges);
  }

  const saveChallengeBtn = document.getElementById("save-new-challenge-btn");
  if (saveChallengeBtn) {
    saveChallengeBtn.addEventListener("click", async () => {
      const title = document.getElementById("new-challenge-title")?.value.trim();
      const brief = document.getElementById("new-challenge-brief")?.value.trim();
      const visual = document.getElementById("new-challenge-visual")?.value.trim();
      const keywords = document.getElementById("new-challenge-keywords")?.value.trim();
      const focus = document.getElementById("new-challenge-focus")?.value.trim();

      if (!title || !brief) {
        showToast("Challenge Title and Brief are required.", "error");
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
            title,
            brief,
            visual_goals: visual,
            inspiration_keywords: keywords,
            evaluation_focus: focus,
            is_active: true
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

  const resetCompBtn = document.getElementById("reset-comp-btn");
  if (resetCompBtn) {
    resetCompBtn.addEventListener("click", async () => {
      if (!state.adminToken) {
        showToast("Admin authorization required. Please authenticate first.", "warning");
        return;
      }
      if (confirm("DANGER: Reset all participants, generations, and locked-in submissions?")) {
        playAudioTone("click");
        try {
          const resp = await fetch("/api/admin/reset", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            }
          });
          const data = await resp.json();
          if (data.success) {
            handleCompetitionReset();
            showToast("Competition data reset complete.", "info");
          } else {
            showToast(data.error || "Reset failed.", "error");
          }
        } catch (e) {
          showToast("Network error resetting competition.", "error");
        }
      }
    });
  }

  // ===========================================================================
  // TEAM MANAGEMENT & IMAGE ASSIGNMENT ENGINE
  // ===========================================================================
  let cachedChallengesForTeams = [];

  async function loadPublicTeams() {
    try {
      const resp = await fetch("/api/teams");
      const data = await resp.json();
      if (!data.success) return;
      state.whitelistEnabled = data.whitelist_enabled;
    } catch (e) {
      console.error("[Teams] Error loading public teams:", e);
    }
  }

  const selectedTeamIds = new Set();
  let cachedAdminTeamsList = [];

  function updateBatchBarUI() {
    const batchBar = document.getElementById("batch-action-bar");
    const badge = document.getElementById("selected-teams-badge");
    const selectAllCb = document.getElementById("select-all-teams-cb");
    const batchSelect = document.getElementById("batch-image-select");

    const count = selectedTeamIds.size;
    if (badge) badge.textContent = count;

    if (batchBar) {
      if (count > 0) {
        batchBar.classList.remove("hidden");
      } else {
        batchBar.classList.add("hidden");
      }
    }

    if (selectAllCb) {
      selectAllCb.checked = count > 0 && count === cachedAdminTeamsList.length;
      selectAllCb.indeterminate = count > 0 && count < cachedAdminTeamsList.length;
    }

    if (batchSelect && cachedChallengesForTeams.length > 0) {
      const curVal = batchSelect.value;
      let opts = `<option value="">-- Choose Target Image to Assign --</option>`;
      cachedChallengesForTeams.forEach(ch => {
        opts += `<option value="${ch.id}">${ch.title}</option>`;
      });
      batchSelect.innerHTML = opts;
      if (curVal) batchSelect.value = curVal;
    }
  }

  async function loadAdminTeams() {
    const tableBody = document.getElementById("admin-teams-table-body");
    const countBadge = document.getElementById("teams-count-badge");
    const statusText = document.getElementById("whitelist-status-text");
    const toggleBtn = document.getElementById("toggle-whitelist-btn");
    const selectAllCb = document.getElementById("select-all-teams-cb");
    if (!tableBody) return;

    try {
      // 1. Fetch active challenges for assignment dropdown
      const chResp = await fetch("/api/challenges");
      const chData = await chResp.json();
      cachedChallengesForTeams = chData.challenges || [];

      // 2. Fetch teams with admin token to reveal passwords
      const resp = await fetch("/api/teams", {
        headers: { "X-Admin-Code": state.adminToken }
      });
      const data = await resp.json();
      if (!data.success) return;

      const teams = data.teams || [];
      cachedAdminTeamsList = teams;
      const isWhitelist = data.whitelist_enabled;
      state.whitelistEnabled = isWhitelist;

      if (countBadge) countBadge.textContent = teams.length;
      if (statusText) {
        statusText.textContent = isWhitelist
          ? "Whitelist ACTIVE (Only pre-registered teams can enter)"
          : "Whitelist DISABLED (Any team can enter)";
        statusText.style.color = isWhitelist ? "#00D2BE" : "#FFA500";
      }
      if (toggleBtn) {
        toggleBtn.textContent = isWhitelist ? "Disable Whitelist" : "Enable Whitelist";
      }

      tableBody.innerHTML = "";
      if (teams.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">No teams registered yet. Upload a team CSV above.</td></tr>`;
        selectedTeamIds.clear();
        updateBatchBarUI();
        return;
      }

      teams.forEach(team => {
        const tr = document.createElement("tr");
        const isChecked = selectedTeamIds.has(team.id);

        let assignedCh = cachedChallengesForTeams.find(c => c.id === team.assigned_challenge_id);
        let challengeOptions = `<option value="">-- Random on Entry --</option>`;
        cachedChallengesForTeams.forEach(ch => {
          const isSelected = team.assigned_challenge_id === ch.id;
          challengeOptions += `<option value="${ch.id}" ${isSelected ? "selected" : ""}>${ch.title}</option>`;
        });

        const thumbUrl = assignedCh ? (assignedCh.static_url || assignedCh.image_data || "/static/images/f1-logo.svg") : "/static/images/f1-logo.svg";

        tr.innerHTML = `
          <td style="text-align:center;">
            <input type="checkbox" class="team-select-cb" data-team-id="${team.id}" ${isChecked ? "checked" : ""} style="cursor:pointer; width:16px; height:16px; accent-color:#E10600;">
          </td>
          <td>
            <div style="font-weight:700; color:#FFFFFF; font-size:13.5px;">${team.name}</div>
            <div style="font-size:11px; color:var(--pq-text-secondary);">${team.email || ""}</div>
          </td>
          <td>
            <code style="font-size:12px; color:#FFD200; background:rgba(255,210,0,0.12); padding:3px 8px; border-radius:4px; font-family:var(--font-mono); font-weight:700;">${team.password || "—"}</code>
          </td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <img src="${thumbUrl}" class="team-thumb-preview" alt="Preview" style="width:36px; height:36px; border-radius:6px; object-fit:cover; border:1px solid rgba(225,6,0,0.4); background:#16161F; flex-shrink:0;">
              <select class="awsui-text-input team-challenge-select" data-team-id="${team.id}" style="padding:4px 8px; font-size:12px; cursor:pointer; flex:1;">
                ${challengeOptions}
              </select>
            </div>
          </td>
          <td>
            <span class="status-badge ${team.has_completed ? "inactive" : "active"}">
              ${team.has_completed ? `Completed (${team.score ? team.score.toFixed(1) : 0} pts)` : "Ready"}
            </span>
          </td>
          <td>
            <button type="button" class="awsui-btn-danger btn-sm delete-team-btn" data-team-id="${team.id}" style="margin:0; padding:4px 10px; font-size:11px;">Delete</button>
          </td>
        `;

        // Checkbox toggle
        const cb = tr.querySelector(".team-select-cb");
        cb.addEventListener("change", () => {
          if (cb.checked) {
            selectedTeamIds.add(team.id);
          } else {
            selectedTeamIds.delete(team.id);
          }
          updateBatchBarUI();
        });

        // Challenge assignment select
        const selectEl = tr.querySelector(".team-challenge-select");
        const thumbEl = tr.querySelector(".team-thumb-preview");
        selectEl.addEventListener("change", async () => {
          const chosenId = selectEl.value;
          playAudioTone("click");
          const newlyAssigned = cachedChallengesForTeams.find(c => c.id === chosenId);
          if (thumbEl) {
            thumbEl.src = newlyAssigned ? (newlyAssigned.static_url || newlyAssigned.image_data || "/static/images/f1-logo.svg") : "/static/images/f1-logo.svg";
          }
          try {
            const aResp = await fetch("/api/teams/assign", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Admin-Code": state.adminToken
              },
              body: JSON.stringify({ team_id: team.id, challenge_id: chosenId || null })
            });
            const aData = await aResp.json();
            if (aData.success) {
              const chTitle = selectEl.options[selectEl.selectedIndex].text;
              showToast(`Assigned "${chTitle}" to ${team.name}!`, "success");
              team.assigned_challenge_id = chosenId || null;
            } else {
              showToast(aData.error || "Assignment failed.", "error");
            }
          } catch (err) {
            showToast("Network error assigning challenge.", "error");
          }
        });

        // Delete button
        const delBtn = tr.querySelector(".delete-team-btn");
        delBtn.addEventListener("click", async () => {
          if (confirm(`Remove team "${team.name}" from whitelist?`)) {
            playAudioTone("click");
            await fetch("/api/teams/delete", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Admin-Code": state.adminToken
              },
              body: JSON.stringify({ team_id: team.id })
            });
            selectedTeamIds.delete(team.id);
            loadAdminTeams();
            loadPublicTeams();
          }
        });

        tableBody.appendChild(tr);
      });

      updateBatchBarUI();

      // Select all checkbox handler
      if (selectAllCb) {
        selectAllCb.onclick = () => {
          const shouldCheck = selectAllCb.checked;
          const allRowCbs = tableBody.querySelectorAll(".team-select-cb");
          allRowCbs.forEach(rCb => {
            rCb.checked = shouldCheck;
            const tid = rCb.getAttribute("data-team-id");
            if (shouldCheck) selectedTeamIds.add(tid);
            else selectedTeamIds.delete(tid);
          });
          updateBatchBarUI();
        };
      }
    } catch (e) {
      console.error("[Teams] Error loading admin teams:", e);
    }
  }

  // Set up Batch Action Bar Buttons
  function setupBatchActionHandlers() {
    const batchAssignBtn = document.getElementById("batch-assign-btn");
    const batchAutoDistBtn = document.getElementById("batch-auto-distribute-btn");
    const batchClearBtn = document.getElementById("batch-clear-assign-btn");
    const batchDeleteBtn = document.getElementById("batch-delete-btn");
    const batchDeselectBtn = document.getElementById("batch-deselect-all-btn");
    const batchImageSelect = document.getElementById("batch-image-select");

    if (batchAssignBtn) {
      batchAssignBtn.addEventListener("click", async () => {
        if (selectedTeamIds.size === 0) {
          showToast("Please select at least one team using the checkboxes.", "warning");
          return;
        }
        const chosenId = batchImageSelect ? batchImageSelect.value : "";
        if (!chosenId) {
          showToast("Please pick a target image from the dropdown to assign.", "warning");
          return;
        }

        playAudioTone("click");
        batchAssignBtn.disabled = true;
        try {
          const resp = await fetch("/api/teams/assign", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({
              team_ids: Array.from(selectedTeamIds),
              challenge_id: chosenId
            })
          });
          const data = await resp.json();
          if (data.success) {
            playAudioTone("success");
            const chTitle = batchImageSelect.options[batchImageSelect.selectedIndex].text;
            showToast(`Assigned "${chTitle}" to ${data.count} selected teams!`, "success");
            loadAdminTeams();
            loadAdminChallenges();
          } else {
            showToast(data.error || "Batch assignment failed.", "error");
          }
        } catch (e) {
          showToast("Network error in batch assignment.", "error");
        } finally {
          batchAssignBtn.disabled = false;
        }
      });
    }

    if (batchAutoDistBtn) {
      batchAutoDistBtn.addEventListener("click", async () => {
        if (selectedTeamIds.size === 0) {
          showToast("Please select at least one team.", "warning");
          return;
        }
        playAudioTone("click");
        batchAutoDistBtn.disabled = true;
        try {
          const resp = await fetch("/api/teams/auto-assign", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({
              team_ids: Array.from(selectedTeamIds)
            })
          });
          const data = await resp.json();
          if (data.success) {
            playAudioTone("success");
            showToast(`Evenly distributed target images across ${data.count} selected teams!`, "success");
            loadAdminTeams();
            loadAdminChallenges();
          } else {
            showToast(data.error || "Failed to auto-distribute.", "error");
          }
        } catch (e) {
          showToast("Network error distributing images.", "error");
        } finally {
          batchAutoDistBtn.disabled = false;
        }
      });
    }

    if (batchClearBtn) {
      batchClearBtn.addEventListener("click", async () => {
        if (selectedTeamIds.size === 0) return;
        playAudioTone("click");
        try {
          const resp = await fetch("/api/teams/assign", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({
              team_ids: Array.from(selectedTeamIds),
              challenge_id: null
            })
          });
          const data = await resp.json();
          if (data.success) {
            showToast(`Reset target image assignment for ${data.count} teams to random on entry.`, "info");
            loadAdminTeams();
            loadAdminChallenges();
          }
        } catch (e) {
          showToast("Network error clearing assignments.", "error");
        }
      });
    }

    if (batchDeleteBtn) {
      batchDeleteBtn.addEventListener("click", async () => {
        if (selectedTeamIds.size === 0) return;
        if (!confirm(`Are you sure you want to permanently delete ${selectedTeamIds.size} selected teams?`)) return;
        playAudioTone("click");
        try {
          const resp = await fetch("/api/teams/delete", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({
              team_ids: Array.from(selectedTeamIds)
            })
          });
          const data = await resp.json();
          if (data.success) {
            showToast(`Deleted ${data.deleted_count} teams.`, "info");
            selectedTeamIds.clear();
            loadAdminTeams();
            loadPublicTeams();
          }
        } catch (e) {
          showToast("Network error deleting teams.", "error");
        }
      });
    }

    if (batchDeselectBtn) {
      batchDeselectBtn.addEventListener("click", () => {
        selectedTeamIds.clear();
        const selectAllCb = document.getElementById("select-all-teams-cb");
        if (selectAllCb) selectAllCb.checked = false;
        const allRowCbs = document.querySelectorAll(".team-select-cb");
        allRowCbs.forEach(cb => cb.checked = false);
        updateBatchBarUI();
      });
    }
  }

  setupBatchActionHandlers();

  // Import Teams button
  const importTeamsBtn = document.getElementById("import-teams-btn");
  if (importTeamsBtn) {
    importTeamsBtn.addEventListener("click", async () => {
      const fileInput = document.getElementById("team-file-input");
      const textInput = document.getElementById("teams-text-input");

      const file = fileInput && fileInput.files ? fileInput.files[0] : null;
      const text = textInput ? textInput.value.trim() : "";

      if (!file && !text) {
        showToast("Please select a file or paste team names.", "warning");
        return;
      }

      playAudioTone("click");
      importTeamsBtn.disabled = true;

      try {
        let resp;
        if (file) {
          const formData = new FormData();
          formData.append("file", file);
          resp = await fetch("/api/teams/upload", {
            method: "POST",
            headers: { "X-Admin-Code": state.adminToken },
            body: formData
          });
        } else {
          resp = await fetch("/api/teams/upload", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Code": state.adminToken
            },
            body: JSON.stringify({ text })
          });
        }

        const data = await resp.json();
        if (data.success) {
          playAudioTone("success");
          showToast(`Successfully registered and whitelisted ${data.count} teams!`, "success");
          if (fileInput) fileInput.value = "";
          if (textInput) textInput.value = "";
          loadAdminTeams();
          loadPublicTeams();
        } else {
          showToast(data.error || "Failed to import teams.", "error");
        }
      } catch (err) {
        showToast("Network error uploading teams.", "error");
      } finally {
        importTeamsBtn.disabled = false;
      }
    });
  }

  // Auto-distribute challenges across teams
  const autoAssignBtn = document.getElementById("auto-assign-teams-btn");
  if (autoAssignBtn) {
    autoAssignBtn.addEventListener("click", async () => {
      if (!confirm("Evenly distribute all active target challenge images across all registered teams?")) return;
      playAudioTone("click");
      try {
        const resp = await fetch("/api/teams/auto-assign", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Code": state.adminToken
          }
        });
        const data = await resp.json();
        if (data.success) {
          playAudioTone("success");
          showToast(`Distributed challenge images across ${data.count} teams!`, "success");
          loadAdminTeams();
        } else {
          showToast(data.error || "Failed to auto-distribute.", "error");
        }
      } catch (e) {
        showToast("Network error distributing challenges.", "error");
      }
    });
  }

  // Toggle whitelist access
  const toggleWhitelistBtn = document.getElementById("toggle-whitelist-btn");
  if (toggleWhitelistBtn) {
    toggleWhitelistBtn.addEventListener("click", async () => {
      playAudioTone("click");
      try {
        const resp = await fetch("/api/teams/toggle-whitelist", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Code": state.adminToken
          },
          body: JSON.stringify({ enabled: !state.whitelistEnabled })
        });
        const data = await resp.json();
        if (data.success) {
          state.whitelistEnabled = data.whitelist_enabled;
          showToast(`Team Whitelist Access is now ${state.whitelistEnabled ? "ACTIVE" : "OFF"}.`, "info");
          loadAdminTeams();
          loadPublicTeams();
        }
      } catch (e) {
        showToast("Error updating whitelist state.", "error");
      }
    });
  }

  // Clear all teams
  const clearTeamsBtn = document.getElementById("clear-teams-btn");
  if (clearTeamsBtn) {
    clearTeamsBtn.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to remove ALL registered teams?")) return;
      playAudioTone("click");
      try {
        const resp = await fetch("/api/teams/clear", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Code": state.adminToken
          }
        });
        const data = await resp.json();
        if (data.success) {
          showToast("All teams cleared.", "info");
          loadAdminTeams();
          loadPublicTeams();
        }
      } catch (e) {
        showToast("Error clearing teams.", "error");
      }
    });
  }

  // Accordion for teams upload
  const uploadTeamsHead = document.getElementById("toggle-upload-teams-form");
  const uploadTeamsBody = document.getElementById("upload-teams-form-body");
  if (uploadTeamsHead && uploadTeamsBody) {
    uploadTeamsHead.addEventListener("click", () => uploadTeamsBody.classList.toggle("hidden"));
  }

  // Upload Custom Target Image Form
  const customImgFileInput = document.getElementById("custom-image-file");
  const customImgPreviewBox = document.getElementById("custom-img-preview-box");
  const customImgPreviewEl = document.getElementById("custom-img-preview-el");

  if (customImgFileInput && customImgPreviewBox && customImgPreviewEl) {
    customImgFileInput.addEventListener("change", () => {
      const file = customImgFileInput.files ? customImgFileInput.files[0] : null;
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          customImgPreviewEl.src = e.target.result;
          customImgPreviewBox.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
      } else {
        customImgPreviewBox.classList.add("hidden");
      }
    });
  }

  const uploadTargetImgForm = document.getElementById("upload-target-image-form");
  if (uploadTargetImgForm) {
    uploadTargetImgForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = customImgFileInput && customImgFileInput.files ? customImgFileInput.files[0] : null;
      const title = document.getElementById("custom-image-title")?.value.trim();
      const brief = document.getElementById("custom-image-brief")?.value.trim();
      const visual = document.getElementById("custom-image-visual")?.value.trim();
      const keywords = document.getElementById("custom-image-keywords")?.value.trim();

      if (!file) {
        showToast("Please choose an image file from your computer.", "warning");
        return;
      }
      if (!title || !brief) {
        showToast("Title and Description are required.", "warning");
        return;
      }

      playAudioTone("click");
      const submitBtn = document.getElementById("upload-custom-image-submit-btn");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("title", title);
        formData.append("brief", brief);
        formData.append("visual_goals", visual);
        formData.append("inspiration_keywords", keywords);
        formData.append("is_active", "true");

        const resp = await fetch("/api/challenges/add", {
          method: "POST",
          headers: { "X-Admin-Code": state.adminToken },
          body: formData
        });
        const data = await resp.json();
        if (data.success) {
          playAudioTone("success");
          showToast(`Target image challenge "${title}" created and ready to assign!`, "success");
          uploadTargetImgForm.reset();
          if (customImgPreviewBox) customImgPreviewBox.classList.add("hidden");
          loadAdminChallenges();
          loadAdminTeams();
        } else {
          showToast(data.error || "Failed to upload image challenge.", "error");
        }
      } catch (err) {
        showToast("Network error uploading target image.", "error");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  const resetDefaultChBtn = document.getElementById("reset-default-challenges-btn");
  if (resetDefaultChBtn) {
    resetDefaultChBtn.addEventListener("click", async () => {
      if (!confirm("Reset image catalog back to default curated Formula 1 challenges?")) return;
      playAudioTone("click");
      await fetch("/api/challenges/reset", {
        method: "POST",
        headers: { "X-Admin-Code": state.adminToken }
      });
      loadAdminChallenges();
      loadAdminTeams();
    });
  }

  // Fetch initial challenge stats
  async function initChallengeStats() {
    try {
      const resp = await fetch("/api/challenges");
      const data = await resp.json();

      if (data.stats) {
        const homePlayersEl = document.getElementById("home-stat-players");
        if (homePlayersEl && (!state.compState || !state.compState.participant_count)) {
          homePlayersEl.textContent = `${data.stats.active || 16}+`;
        }
      }
    } catch (e) {
      console.error("Init stats error:", e);
    }
  }

  // ---------------------------------------------------------------------------
  // ANTI-CHEAT CONTROLS: DISABLE COPY-PASTE (SCREENSHOTS PERMITTED)
  // ---------------------------------------------------------------------------
  function setupSecurityAndIntegrityControls() {
    // 1. Disable Pasting into prompt input (strictly enforce manual typing)
    if (promptInput) {
      promptInput.addEventListener("paste", (e) => {
        e.preventDefault();
        showToast("🚫 Pasting is disabled! You must craft and type your prompt manually.", "error");
        playAudioTone("click");
        return false;
      });

      promptInput.addEventListener("copy", (e) => {
        e.preventDefault();
        showToast("🚫 Copying is disabled in the Prompt Arena.", "warning");
        return false;
      });

      promptInput.addEventListener("cut", (e) => {
        e.preventDefault();
        return false;
      });

      promptInput.addEventListener("drop", (e) => {
        e.preventDefault();
        showToast("🚫 Drag & drop is disabled in the Prompt Arena.", "warning");
        return false;
      });
    }

    // 2. Global Copy & Paste Block for players
    document.addEventListener("copy", (e) => {
      if (state.isAdmin) return;
      e.preventDefault();
      showToast("🚫 Copying challenge text is disabled.", "warning");
      return false;
    });

    document.addEventListener("cut", (e) => {
      if (state.isAdmin) return;
      e.preventDefault();
      return false;
    });

    document.addEventListener("paste", (e) => {
      if (state.isAdmin) return;
      const target = e.target;
      if (target && (target.id === "prompt-input" || target.closest("#game-screen") || target.closest(".pq-prompt-workspace"))) {
        e.preventDefault();
        showToast("🚫 Pasting is disabled in the Prompt Arena. Type your prompt manually!", "error");
        return false;
      }
    });

    // 3. Disable Right-Click Context Menu
    document.addEventListener("contextmenu", (e) => {
      if (state.isAdmin) return;
      e.preventDefault();
      showToast("🚫 Right-click context menu is disabled in the Arena.", "info");
      return false;
    });

    // 4. Keyboard Shortcuts: Allow Screenshots & Snipping Tool freely
    window.addEventListener("keydown", (e) => {
      if (state.isAdmin) return;

      // Ctrl+S / Cmd+S (Save webpage file)
      if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S") && !e.shiftKey) {
        e.preventDefault();
        showToast("🚫 Saving webpage is disabled.", "warning");
        return false;
      }

      // DevTools: F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C, Ctrl+U
      if (e.key === "F12" ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "I" || e.key === "i" || e.key === "J" || e.key === "j" || e.key === "C" || e.key === "c")) ||
        ((e.ctrlKey || e.metaKey) && (e.key === "u" || e.key === "U"))) {
        e.preventDefault();
        showToast("🚫 Developer inspection tools are disabled.", "warning");
        return false;
      }
    });
  }

  // Initialize
  setupSecurityAndIntegrityControls();
  initChallengeStats();
  checkSavedIdentity();
  updateCharCount();
  refreshCompetitionState();
  loadLeaderboard();
  loadPublicTeams();
});
