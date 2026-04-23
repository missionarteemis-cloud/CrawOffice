import { execSync } from "child_process";
import { createRequire } from "module";

/**
 * provider-watchdog — Hook before_agent_start
 *
 * Prima di ogni risposta dell'agente:
 * 1. Testa il provider primario con una chiamata leggera
 * 2. Se non risponde, switcha su openrouter/auto e avvisa Diego
 * 3. Se il provider primario torna disponibile, lo ripristina silenziosamente
 */

const PRIMARY   = "openai-codex/gpt-5.4";
const FALLBACK  = "openrouter/auto";
const TEST_URL  = "https://api.openai.com/v1/models"; // endpoint leggero per health check

// Stato condiviso in memoria (resetta ad ogni restart del gateway)
let currentProvider = PRIMARY;
let lastCheck = 0;
const CHECK_INTERVAL_MS = 60_000; // controlla max 1 volta al minuto

async function isOpenAIReachable() {
  try {
    const res = await fetch(TEST_URL, {
      method: "HEAD",
      signal: AbortSignal.timeout(4000), // timeout 4 secondi
    });
    // 401 = raggiungibile ma non autenticato — va bene, significa che il server risponde
    return res.status < 500;
  } catch {
    return false;
  }
}

function switchProvider(target, messages) {
  try {
    execSync(`openclaw config set agents.defaults.model.primary "${target}"`, {
      stdio: "ignore",
      timeout: 5000,
    });
    execSync("openclaw gateway restart", {
      stdio: "ignore",
      timeout: 10000,
    });
    currentProvider = target;
    if (target === FALLBACK) {
      messages.push(`⚡ OpenAI non risponde — switchato su OpenRouter. Riprova ora.`);
    }
  } catch (err) {
    messages.push(`⚠️ Watchdog: switch provider fallito (${err.message}). Usa \`openclaw config set agents.defaults.model.primary "${target}"\` manualmente.`);
  }
}

const handler = async (event) => {
  // Solo su eventi di messaggio in arrivo
  if (event.type !== "message" && event.type !== "agent") return;

  const now = Date.now();
  if (now - lastCheck < CHECK_INTERVAL_MS) return; // throttle
  lastCheck = now;

  const messages = event.messages ?? [];

  const openaiOk = await isOpenAIReachable();

  if (!openaiOk && currentProvider === PRIMARY) {
    // OpenAI giù → switcha su fallback
    switchProvider(FALLBACK, messages);
  } else if (openaiOk && currentProvider === FALLBACK) {
    // OpenAI tornato → ripristina primario silenziosamente
    switchProvider(PRIMARY, []);
  }
};

export default handler;
