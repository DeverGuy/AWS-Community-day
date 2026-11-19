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
    window.location.pathname === "/admin/";

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
      socket.on("vote_update", () => {
        loadLeaderboard();
      });
      socket.on("new_submission", () => {
        refreshCompetitionState();
        loadLeaderboard();
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

  function updateAdminPhaseButtons(currentPhase) {
    const phase = currentPhase || (state.compState && state.compState.status) || "lobby";
    document.querySelectorAll(".btn-phase-ctrl").forEach(btn => {
      const bPhase = btn.dataset.phase;
      if (bPhase === phase) {
        btn.classList.remove("pq-btn-outline-pill");
        btn.classList.add("pq-btn-orange-pill", "active-phase");
      } else {
        btn.classList.remove("pq-btn-orange-pill", "active-phase");
        btn.classList.add("pq-btn-outline-pill");
      }
    });
    const adminLiveBadge = document.getElementById("admin-live-phase-badge");
    if (adminLiveBadge) {
      const phaseBadgeMap = {
        lobby: "🟢 LOBBY MODE",
        battle: "⚔️ BATTLE ROUND (LIVE)",
        showcase: "🌟 SHOWCASE & VOTING",
        leaderboard: "🏆 FINAL STANDINGS"
      };
      adminLiveBadge.textContent = phaseBadgeMap[phase] || phase.toUpperCase();
    }
  }

  let lastHandledPhase = null;

  async function ensureParticipantActive() {
    if (state.participant && state.participant.id) return state.participant;
    try {
      const storedName = localStorage.getItem("sbg_builder_name");
      const storedEmail = localStorage.getItem("sbg_builder_email");
      const inputName = identifierNameInput ? identifierNameInput.value.trim() : "";
      const inputEmail = identifierEmailInput ? identifierEmailInput.value.trim() : "";

      const name = inputName || storedName || `Builder-${Math.floor(100 + Math.random() * 900)}`;
      const email = inputEmail || storedEmail || `${name.toLowerCase()}@aws-community.dev`;

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
    const prevPhase = state.compState ? state.compState.status : null;
    state.compState = payload;
    const currentPhase = payload.status || "lobby";

    if (typeof payload.time_remaining === "number") {
      state.timeRemaining = payload.time_remaining;
    }

    // Keep Admin Phase Buttons visual state updated
    updateAdminPhaseButtons(currentPhase);

    // 1. Navigation Status & Pill
    const statusText = document.getElementById("nav-comp-status");
    const liveStatusPill = document.getElementById("live-status-pill");
    const subCountEl = document.getElementById("nav-submissions-count");
    const topLbBtn = document.getElementById("nav-leaderboard-btn");

    if (subCountEl && typeof payload.submission_count === "number") {
      subCountEl.textContent = payload.submission_count;
    }

    if (statusText) {
      if (currentPhase === "battle") {
        statusText.textContent = `Round ${payload.round_number || 1} Live`;
      } else if (currentPhase === "showcase") {
        statusText.textContent = "Showcase & Voting";
      } else if (currentPhase === "leaderboard") {
        statusText.textContent = "Final Standings";
      } else {
        statusText.textContent = "Lobby Open";
      }
    }

    if (liveStatusPill) {
      liveStatusPill.className = `pq-live-event-pill pill-phase-${currentPhase}`;
    }

    // Update Admin Phase Control Strip (Live Status & Player Count)
    const adminLiveBadge = document.getElementById("admin-live-phase-badge");
    const adminPlayersCount = document.getElementById("admin-live-players-count");
    if (adminLiveBadge) {
      const phaseBadgeMap = {
        lobby: "🟢 LOBBY MODE",
        battle: "⚔️ BATTLE ROUND (LIVE)",
        showcase: "🌟 SHOWCASE & VOTING",
        leaderboard: "🏆 FINAL STANDINGS"
      };
      adminLiveBadge.textContent = phaseBadgeMap[currentPhase] || currentPhase.toUpperCase();
    }
    if (adminPlayersCount && payload.participant_count !== undefined) {
      adminPlayersCount.textContent = payload.participant_count;
    }

    // 2. Identifier Screen Live Phase Banner & CTA Button Text
    const phaseBanner = document.getElementById("live-phase-banner");
    const phaseText = document.getElementById("live-phase-text");
    const startBtn = document.getElementById("start-game-btn");

    if (phaseBanner && phaseText) {
      phaseBanner.className = `live-phase-banner phase-${currentPhase}`;
      if (currentPhase === "battle") {
        phaseText.textContent = "🔥 BATTLE ROUND IS LIVE! Complete your prompt before the timer expires!";
        if (startBtn && !state.participant) {
          const span = startBtn.querySelector("span");
          if (span) span.textContent = "🚀 Join Live Battle Now";
        }
      } else if (currentPhase === "showcase") {
        phaseText.textContent = "🌟 Showcase & Voting Phase is LIVE! Review submissions and vote with 👏!";
        if (startBtn && !state.participant) {
          const span = startBtn.querySelector("span");
          if (span) span.textContent = "View Showcase & Vote";
        }
      } else if (currentPhase === "leaderboard") {
        phaseText.textContent = "🏆 Final Standings Announced! Check out the Hall of Future Builders!";
        if (startBtn && !state.participant) {
          const span = startBtn.querySelector("span");
          if (span) span.textContent = "View Final Standings";
        }
      } else {
        phaseText.textContent = "🟢 Competition Lobby: Waiting for the host to start Battle Round.";
        if (startBtn && !state.participant) {
          const span = startBtn.querySelector("span");
          if (span) span.textContent = "Launch Prompt Arena & Reveal Challenge";
        }
      }
    }

    // 3. Leaderboard Button Visibility
    if (topLbBtn) {
      if (currentPhase === "showcase" || currentPhase === "leaderboard" || state.isAdmin || (state.participant && state.hasGenerated)) {
        topLbBtn.classList.remove("hidden");
      } else {
        topLbBtn.classList.add("hidden");
      }
    }

    // 4. Live Global Screen Control & Transitions across All Tabs
    const isFirstRun = lastHandledPhase === null;
    const phaseChanged = lastHandledPhase !== currentPhase;

    if (phaseChanged) {
      lastHandledPhase = currentPhase;

      if (currentPhase === "battle") {
        // --- 1. START BATTLE ROUND: Launch all players into Arena ---
        if (adminModal) adminModal.classList.add("hidden");
        await ensureParticipantActive();
        unlockWorkspaceForNewSession();
        showScreen("game");
        startChallengeTimer(payload.time_remaining || state.timerDuration || 180);
        playAudioTone("success");
        showToast(`⚔️ Round ${payload.round_number || 1} Live! 180 seconds on the clock!`, "success");

      } else if (currentPhase === "showcase") {
        // --- 2. SHOWCASE & VOTING: Move all players to Leaderboard to vote ---
        stopChallengeTimer();
        if (!state.hasGenerated && state.participant) {
          lockWorkspaceAfterFinalize("⏰ Round Ended by Host", "ROUND OVER", "00:00");
        }
        showScreen("leaderboard");
        loadLeaderboard();
        playAudioTone("success");
        showToast("🌟 Showcase & Voting is now LIVE! Cast your applause votes with 👏!", "info");

      } else if (currentPhase === "leaderboard") {
        // --- 3. FINAL STANDINGS: Reveal official final rankings ---
        stopChallengeTimer();
        showScreen("leaderboard");
        loadLeaderboard();
        playAudioTone("success");
        showToast("🏆 Final Standings Announced! Check out the Hall of Future Builders!", "success");

      } else if (currentPhase === "lobby") {
        // --- 4. LOBBY MODE: Return everyone to Lobby ---
        stopChallengeTimer();
        showScreen("identifier");
        if (!isFirstRun) {
          showToast("🟢 Competition returned to Lobby Mode.", "info");
        }
      }
    } else {
      // Sync running timer during active battle if needed
      if (currentPhase === "battle" && !state.hasGenerated && !state.timerInterval) {
        startChallengeTimer(payload.time_remaining || 180);
      }
    }
  }

  // Multi-tab zero-latency broadcast sync
  const phaseBroadcast = (typeof BroadcastChannel !== "undefined") ? new BroadcastChannel("pq_competition_sync") : null;
  if (phaseBroadcast) {
    phaseBroadcast.onmessage = (evt) => {
      if (evt.data && evt.data.type === "phase_update" && evt.data.state) {
        applyLiveCompetitionState(evt.data.state);
      }
    };
  }

  window.addEventListener("storage", (evt) => {
    if (evt.key === "pq_live_phase_sync" && evt.newValue) {
      try {
        const payload = JSON.parse(evt.newValue);
        applyLiveCompetitionState(payload);
      } catch (e) { }
    }
  });

  // Smooth 1-second timer tick for active battle
  setInterval(() => {
    if (state.compState && state.compState.status === "battle" && state.timeRemaining > 0) {
      state.timeRemaining -= 1;
      const homeTimerEl = document.getElementById("home-stat-timer");
      if (homeTimerEl) homeTimerEl.textContent = formatSecondsToHMS(state.timeRemaining);
    }
  }, 1000);

  async function refreshCompetitionState() {
    try {
      const resp = await fetch("/api/state");
      if (resp.ok) {
        const data = await resp.json();
        applyLiveCompetitionState(data);
      }
    } catch (e) { }
  }

  // Fast polling fallback: 1200ms guarantees sub-1.5s synchronization everywhere
  setInterval(() => {
    refreshCompetitionState();
  }, 1200);

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
  const identifierForm = document.getElementById("identifier-form");
  const identifierNameInput = document.getElementById("identifier-name");
  const identifierEmailInput = document.getElementById("identifier-email");
  const identifierError = document.getElementById("identifier-error");
  const startBtn = document.getElementById("start-game-btn");
  const quickDemoFillBtn = document.getElementById("quick-demo-fill-btn");

  if (quickDemoFillBtn) {
    quickDemoFillBtn.addEventListener("click", () => {
      playAudioTone("click");
      const demoNames = ["CloudDreamer", "PromptPro", "AWSExplorer", "NovaArchitect"];
      const picked = demoNames[Math.floor(Math.random() * demoNames.length)];
      if (identifierNameInput) identifierNameInput.value = picked;
      if (identifierEmailInput) identifierEmailInput.value = `${picked.toLowerCase()}@aws-community.dev`;
      hideIdentifierError();
    });
  }

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
    if (e && typeof e.preventDefault === "function") e.preventDefault();
    if (isSubmittingIdentifier) return;

    const name = identifierNameInput ? identifierNameInput.value.trim() : "";
    const email = identifierEmailInput ? identifierEmailInput.value.trim().toLowerCase() : "";
    const currentPhase = state.compState ? state.compState.status : "lobby";

    if (!name && !email && (currentPhase === "showcase" || currentPhase === "leaderboard")) {
      showScreen("leaderboard");
      loadLeaderboard();
      return;
    }

    if (!name) {
      showIdentifierError("Please enter your builder alias or full name.");
      if (identifierNameInput) identifierNameInput.focus();
      return;
    }

    if (!email || !validateEmail(email)) {
      showIdentifierError("Please enter a valid email address (e.g. builder@university.edu).");
      if (identifierEmailInput) identifierEmailInput.focus();
      return;
    }

    hideIdentifierError();
    isSubmittingIdentifier = true;

    if (startBtn) {
      startBtn.disabled = true;
      startBtn.innerHTML = `<span class="awsui-spinner-inline"></span><span>Entering Prompt Quest Arena...</span>`;
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
        unlockWorkspaceForNewSession();
        state.participant = data.participant;
        state.timerDuration = Number(data.timer_duration) || 180;
        const target = data.target_challenge || data.challenge;
        state.currentChallenge = target;

        try {
          localStorage.setItem("sbg_builder_name", name);
          localStorage.setItem("sbg_builder_email", email);
          localStorage.setItem("sbg_participant_id", data.participant.id);
        } catch (storageErr) { }

        updateUserNavProfile(name, email);

        const gName = document.getElementById("game-builder-name");
        const gEmail = document.getElementById("game-builder-email");
        if (gName) gName.textContent = name;
        if (gEmail) gEmail.textContent = `(${email})`;

        renderAssignedChallenge(target);
        refreshCompetitionState();

        showScreen("game");
        startChallengeTimer(state.timerDuration);
        showToast(`Welcome, ${name}! You have ${state.timerDuration}s and 1 final generation attempt.`, "success");
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
        startBtn.innerHTML = `<span>Launch Prompt Arena &amp; Reveal Challenge</span><span class="btn-arrow">→</span>`;
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

    if (catNameEl) catNameEl.textContent = "Visual Scene Challenge";
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
      } else if (words < 10) {
        qualityPill.textContent = "Readiness: Brief";
      } else if (words < 20) {
        qualityPill.textContent = "Readiness: Good";
        qualityPill.classList.add("quality-good");
      } else {
        qualityPill.textContent = "Readiness: Optimal ✓";
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
  const submitBtn = document.getElementById("submit-masterpiece-btn");
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
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>🏆 Score Auto-Saves on Finalize</span>`;
    }
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
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>🏆 Score Auto-Saves on Finalize</span>`;
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
          }).catch(() => {});
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
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>🏆 View Leaderboard</span>`;
    }
    const srcTagBefore = document.getElementById("canvas-source-tag");
    const latTagBefore = document.getElementById("canvas-latency-tag");
    if (srcTagBefore) srcTagBefore.classList.add("hidden");
    if (latTagBefore) latTagBefore.classList.add("hidden");

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

        const sourceTag = document.getElementById("canvas-source-tag");
        if (sourceTag) {
          sourceTag.textContent = `Engine: ${(gen.source || "CLOUDFLARE-AI").toUpperCase()}`;
          sourceTag.classList.remove("hidden");
        }

        const latencyTag = document.getElementById("canvas-latency-tag");
        if (latencyTag) {
          latencyTag.textContent = `${gen.latency || "1.0"}s`;
          latencyTag.classList.remove("hidden");
        }

        renderEvaluationScorecard(gen.evaluation);
        renderHistoryReel();
        updateDashboardProgressRing(gen.evaluation?.total_score, gen.evaluation?.tier_badge);
        refreshCompetitionState();

        lockWorkspaceAfterFinalize("✅ Final Image Generated (1/1 Used)", "FINALIZED", "1 / 1");

        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = state.isSubmitted
            ? `<span>🏆 Score Saved — View Leaderboard</span>`
            : `<span>🏆 Lock In &amp; Save Score</span>`;
        }

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
    if (totalEl) {
      const targetScore = Number(ev.total_score) || 0;
      let curr = 0;
      const step = Math.max(1, Math.ceil(targetScore / 25));
      const interval = setInterval(() => {
        curr += step;
        if (curr >= targetScore) {
          curr = targetScore;
          clearInterval(interval);
        }
        totalEl.textContent = curr;
      }, 25);
    }
    triggerCelebrationConfetti();

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
  // 6. SUBMIT MASTERPIECE / VIEW LEADERBOARD
  // ---------------------------------------------------------------------------
  if (submitBtn) {
    submitBtn.addEventListener("click", async () => {
      if (!state.participant) {
        showToast("Please register on Home first.", "error");
        return;
      }
      if (state.isSubmitted) {
        playAudioTone("click");
        showScreen("leaderboard");
        return;
      }
      if (!state.currentImage) {
        showToast("Finalize and generate your image first.", "error");
        return;
      }

      playAudioTone("success");
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="awsui-spinner-inline"></span><span>Locking In Score...</span>`;

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
          state.isSubmitted = true;
          refreshCompetitionState();
          updateDashboardProgressRing(data.submission.ai_score, data.submission.tier_badge);
          showToast(
            `Score locked in! AI Judge Match: ${data.submission.ai_score}/100 under ${state.participant.name}.`,
            "success"
          );
          showScreen("leaderboard");
        } else {
          showToast(data.error || "Submission failed.", "error");
        }
      } catch (err) {
        showToast("Error submitting masterpiece.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = state.isSubmitted
          ? `<span>🏆 Score Saved — View Leaderboard</span>`
          : `<span>🏆 Lock In &amp; Save Score</span>`;
      }
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
          { rank: 1, name: "CloudDreamer", score: "98.5" },
          { rank: 2, name: "PromptPro", score: "93.2" },
          { rank: 3, name: "AWSExplorer", score: "89.7" }
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
            const cleanTitle = (entry.challenge_title || "Target Reference").replace(/^.*?•\s*/, '').trim();
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
                <div class="podium-cat-text">${cleanTitle}</div>
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
        const cleanTitle = (entry.challenge_title || "Target Reference").replace(/^.*?•\s*/, '').trim();
        const tr = document.createElement("tr");
        const rankClass =
          entry.rank === 1 ? "rank-1" : entry.rank === 2 ? "rank-2" : entry.rank === 3 ? "rank-3" : "";

        tr.innerHTML = `
          <td class="table-rank ${rankClass}">#${entry.rank}</td>
          <td><strong>${entry.player_name}</strong></td>
          <td><span style="font-size:12px; color:var(--aws-blue); font-family:var(--font-mono);">${entry.player_email || "—"}</span></td>
          <td>
            <div style="font-size:13px; font-weight:700;">${cleanTitle}</div>
          </td>
          <td class="table-score">${entry.ai_score}</td>
          <td style="font-weight:800; font-size:14px; font-family:var(--font-mono);">${entry.composite_score}</td>
          <td><span class="badge-tag">${entry.tier_badge}</span></td>
          <td>
            <div style="display:flex; gap:6px; align-items:center;">
              <button type="button" class="btn-vote-applause" title="Upvote creation (+2 pts)">
                👏 ${entry.votes || 0}
              </button>
              ${state.isAdmin ? `<button type="button" class="pq-btn-outline-pill btn-sm inspect-entry-btn">Inspect</button>` : ""}
            </div>
          </td>
        `;

        const voteBtn = tr.querySelector(".btn-vote-applause");
        if (voteBtn) {
          voteBtn.addEventListener("click", async () => {
            playAudioTone("click");
            const voterId = state.participant ? state.participant.id : "guest_voter";
            try {
              const vResp = await fetch("/api/vote", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ submission_id: entry.id, voter_id: voterId })
              });
              const vData = await vResp.json();
              if (vResp.ok && vData.success) {
                loadLeaderboard();
              } else {
                showToast(vData.error || "Unable to vote on this entry.", "error");
              }
            } catch (e) {
              showToast("Error submitting vote.", "error");
            }
          });
        }

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
      const hostCtrlBtn = document.getElementById("nav-host-ctrl-btn");
      if (hostCtrlBtn) hostCtrlBtn.classList.remove("hidden");
    }
  } catch (e) { }

  if (openAdminBtn) {
    openAdminBtn.addEventListener("click", () => {
      adminModal.classList.remove("hidden");
      if (state.isAdmin) {
        loadAdminChallenges();
        updateAdminPhaseButtons();
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
          const hostCtrlBtn = document.getElementById("nav-host-ctrl-btn");
          if (hostCtrlBtn) hostCtrlBtn.classList.remove("hidden");
          if (adminAuthPanel) adminAuthPanel.classList.add("hidden");
          if (adminDashPanel) adminDashPanel.classList.remove("hidden");
          if (adminAuthError) adminAuthError.classList.add("hidden");
          playAudioTone("success");
          loadAdminChallenges();
          loadLeaderboard();
          updateAdminPhaseButtons();
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
        if (btn.dataset.tab === "tab-competition") {
          updateAdminPhaseButtons();
        }
      }
    });
  });

  document.querySelectorAll(".btn-phase-ctrl").forEach(btn => {
    btn.addEventListener("click", async () => {
      const phase = btn.dataset.phase;
      if (!phase) return;

      if (!state.adminToken) {
        showToast("Admin authorization required. Please authenticate in the admin panel first.", "warning");
        if (adminAuthPanel) adminAuthPanel.classList.remove("hidden");
        if (adminDashPanel) adminDashPanel.classList.add("hidden");
        if (adminCodeInput) adminCodeInput.focus();
        return;
      }

      playAudioTone("click");
      updateAdminPhaseButtons(phase);

      try {
        const resp = await fetch("/api/admin/phase", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Code": state.adminToken
          },
          body: JSON.stringify({ phase })
        });
        const data = await resp.json();
        if (data.success) {
          applyLiveCompetitionState(data.state);
          updateAdminPhaseButtons(phase);
          if (phaseBroadcast) {
            phaseBroadcast.postMessage({ type: "phase_update", state: data.state });
          }
          try {
            localStorage.setItem("pq_live_phase_sync", JSON.stringify(data.state));
          } catch (e) { }
          const phaseNames = {
            lobby: "LOBBY MODE",
            battle: "BATTLE ROUND",
            showcase: "SHOWCASE & VOTING",
            leaderboard: "FINAL STANDINGS"
          };
          showToast(`Competition phase live switched to: ${phaseNames[phase] || phase.toUpperCase()}`, "success");
        } else {
          showToast(data.error || "Unable to switch competition phase.", "error");
        }
      } catch (e) {
        console.error("Phase switch error:", e);
        showToast("Error updating competition phase.", "error");
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
    if (!adminChallengesTable) return;
    try {
      const resp = await fetch("/api/challenges");
      const data = await resp.json();

      if (data.stats) {
        const t = document.getElementById("stat-total-challenges");
        const a = document.getElementById("stat-active-challenges");
        if (t) t.textContent = data.stats.total;
        if (a) a.textContent = data.stats.active;
      }

      adminChallengesTable.innerHTML = "";
      (data.challenges || []).forEach(ch => {
        const tr = document.createElement("tr");
        const isActive = ch.is_active;
        const imgCell = ch.static_url
          ? `<img src="${ch.static_url}?v=${Date.now()}" alt="${ch.title}" style="width:52px; height:34px; object-fit:cover; border-radius:4px; border:1px solid rgba(255,255,255,0.2);">`
          : `<div style="width:52px; height:34px; border-radius:4px; background:rgba(255,255,255,0.06); display:flex; align-items:center; justify-content:center; font-size:14px;" title="AI synthesized on demand">🎨</div>`;

        tr.innerHTML = `
          <td>${imgCell}</td>
          <td><span class="status-badge ${isActive ? "active" : "inactive"}">${isActive ? "ACTIVE" : "INACTIVE"}</span></td>
          <td>
            <div style="font-weight:700;">${ch.title}</div>
            <div style="font-size:11.5px; color:var(--pq-text-secondary);">${ch.brief.slice(0, 90)}...</div>
          </td>
          <td>
            <div style="display:flex; gap:6px; align-items:center;">
              <button type="button" class="pq-btn-outline-pill btn-sm upload-ch-img-btn" title="Upload custom reference image">📷 Upload</button>
              <input type="file" class="hidden-ch-file-input hidden" accept="image/png, image/jpeg, image/webp">
              <button type="button" class="pq-btn-outline-pill btn-sm toggle-act-btn">${isActive ? "Deactivate" : "Activate"}</button>
              <button type="button" class="awsui-btn-danger btn-sm delete-ch-btn" style="margin-top:0;">Delete</button>
            </div>
          </td>
        `;

        const fileInput = tr.querySelector(".hidden-ch-file-input");
        const uploadBtn = tr.querySelector(".upload-ch-img-btn");

        if (uploadBtn && fileInput) {
          uploadBtn.addEventListener("click", () => fileInput.click());
          fileInput.addEventListener("change", (evt) => {
            const file = evt.target.files && evt.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async (readEvt) => {
              const b64 = readEvt.target.result;
              try {
                uploadBtn.disabled = true;
                uploadBtn.textContent = "Uploading...";
                const uResp = await fetch(`/api/challenges/${ch.id}/image`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "X-Admin-Code": state.adminToken
                  },
                  body: JSON.stringify({ image_data: b64 })
                });
                const uData = await uResp.json();
                if (uData.success) {
                  playAudioTone("success");
                  showToast(`Custom reference image uploaded for "${ch.title}"!`, "success");
                  loadAdminChallenges();
                } else {
                  showToast(uData.error || "Failed to upload image.", "error");
                }
              } catch (err) {
                showToast("Error uploading image.", "error");
              } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = "📷 Upload";
              }
            };
            reader.readAsDataURL(file);
          });
        }

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

  let newChallengeImageData = null;
  const newChallengeImageInput = document.getElementById("new-challenge-image");
  const newChallengePreviewWrap = document.getElementById("new-challenge-image-preview");
  const newChallengePreviewImg = document.getElementById("new-challenge-preview-img");
  const clearImagePreviewBtn = document.getElementById("clear-image-preview-btn");

  if (newChallengeImageInput) {
    newChallengeImageInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (loadEvt) => {
        newChallengeImageData = loadEvt.target.result;
        if (newChallengePreviewImg) newChallengePreviewImg.src = newChallengeImageData;
        if (newChallengePreviewWrap) newChallengePreviewWrap.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    });
  }

  if (clearImagePreviewBtn) {
    clearImagePreviewBtn.addEventListener("click", () => {
      newChallengeImageData = null;
      if (newChallengeImageInput) newChallengeImageInput.value = "";
      if (newChallengePreviewWrap) newChallengePreviewWrap.classList.add("hidden");
    });
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
            image_data: newChallengeImageData,
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
          newChallengeImageData = null;
          if (newChallengeImageInput) newChallengeImageInput.value = "";
          if (newChallengePreviewWrap) newChallengePreviewWrap.classList.add("hidden");
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

  // Confetti Particle Burst Engine
  function triggerCelebrationConfetti() {
    const canvas = document.getElementById("pq-confetti-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ["#B69AFF", "#D8C8FF", "#8C4FFF", "#22C55E", "#EC7211", "#FFFFFF"];
    const particles = [];
    for (let i = 0; i < 90; i++) {
      particles.push({
        x: canvas.width * 0.5 + (Math.random() - 0.5) * 360,
        y: canvas.height * 0.4 + (Math.random() - 0.5) * 120,
        vx: (Math.random() - 0.5) * 14,
        vy: (Math.random() - 0.8) * 16,
        size: Math.random() * 7 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        vr: (Math.random() - 0.5) * 10,
        alpha: 1
      });
    }

    let frame = 0;
    function renderConfetti() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let alive = false;
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.35;
        p.rotation += p.vr;
        p.alpha -= 0.012;
        if (p.alpha > 0) {
          alive = true;
          ctx.save();
          ctx.globalAlpha = Math.max(0, p.alpha);
          ctx.translate(p.x, p.y);
          ctx.rotate((p.rotation * Math.PI) / 180);
          ctx.fillStyle = p.color;
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 1.5);
          ctx.restore();
        }
      });
      frame++;
      if (alive && frame < 180) {
        requestAnimationFrame(renderConfetti);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    requestAnimationFrame(renderConfetti);
  }

  // Host Controls Topbar Shortcut Button
  const hostCtrlBtn = document.getElementById("nav-host-ctrl-btn");
  if (hostCtrlBtn) {
    hostCtrlBtn.addEventListener("click", () => {
      if (adminModal) {
        adminModal.classList.remove("hidden");
        if (state.isAdmin) {
          loadAdminChallenges();
          updateAdminPhaseButtons();
        }
      }
    });
  }

  // Home Dashboard: View All Top Builders Link
  const homeViewAllBtn = document.getElementById("home-view-all-lb-btn");
  if (homeViewAllBtn) {
    homeViewAllBtn.addEventListener("click", () => {
      showScreen("leaderboard");
      loadLeaderboard();
      triggerCelebrationConfetti();
    });
  }

  // Initialize
  initChallengeStats();
  checkSavedIdentity();
  updateCharCount();
  refreshCompetitionState();
  loadLeaderboard();
});
