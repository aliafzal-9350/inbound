const path = require("path");
const fs = require("fs");
const axios = require("axios");
const QRCode = require("qrcode");
const pino = require("pino");

const SESSIONS_DIR = path.join(__dirname, "..", "sessions");
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const INTERNAL_SECRET = process.env.WHATSAPP_QR_INTERNAL_SECRET || "dev-internal-secret";

// Default to real Baileys mode so real WhatsApp Web QR codes are generated for phone scanning
const MOCK_MODE = process.env.WHATSAPP_QR_MOCK === "true";

const sessions = new Map(); // tenantId -> { status, qr, sock? }

function cleanupSocket(sock) {
  if (!sock) return;
  try {
    sock.ev.removeAllListeners();
    if (sock.ws) {
      sock.ws.close();
    }
    sock.end(undefined);
  } catch (e) {
    // Ignore cleanup error
  }
}

async function notifyStatus(tenantId, status) {
  try {
    await axios.post(
      `${BACKEND_URL}/webhooks/whatsapp-qr/status`,
      { tenant_id: tenantId, status },
      { headers: { "X-Internal-Secret": INTERNAL_SECRET } }
    );
  } catch (err) {
    console.error("[whatsapp-qr] failed to notify backend of status:", err.message);
  }
}

async function forwardMessage(tenantId, sender, name, text) {
  try {
    await axios.post(
      `${BACKEND_URL}/webhooks/whatsapp-qr`,
      { tenant_id: tenantId, sender, name, text },
      { headers: { "X-Internal-Secret": INTERNAL_SECRET } }
    );
  } catch (err) {
    console.error("[whatsapp-qr] failed to forward message to backend:", err.message);
  }
}

async function startSessionMock(tenantId) {
  const qr = await QRCode.toDataURL(`ravisn-mock-session:${tenantId}:${Date.now()}`);
  sessions.set(tenantId, { status: "qr_pending", qr });

  setTimeout(async () => {
    const entry = sessions.get(tenantId);
    if (!entry || entry.status === "connected") return;
    entry.status = "connected";
    entry.qr = null;
    await notifyStatus(tenantId, "connected");
  }, 8000);

  return sessions.get(tenantId);
}

async function startSessionReal(tenantId, isReconnect = false) {
  const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    Browsers,
    fetchLatestBaileysVersion,
  } = require("@whiskeysockets/baileys");

  const sessionPath = path.join(SESSIONS_DIR, tenantId);
  fs.mkdirSync(sessionPath, { recursive: true });

  // Clean up any existing socket for this tenant before creating a new one
  const existing = sessions.get(tenantId);
  if (existing?.sock) {
    cleanupSocket(existing.sock);
    existing.sock = null;
  }

  let version;
  try {
    const v = await fetchLatestBaileysVersion();
    version = v.version;
  } catch (e) {
    // fallback to default version
  }

  const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
  const sock = makeWASocket({
    version,
    auth: state,
    logger: pino({ level: "warn" }),
    printQRInTerminal: false,
    browser: Browsers.windows("Desktop"),
    syncFullHistory: false,
    generateHighQualityLinkPreview: true,
    connectTimeoutMs: 60000,
    defaultQueryTimeoutMs: 60000,
    keepAliveIntervalMs: 30000,
  });

  const entry = sessions.get(tenantId) || { status: "connecting", qr: null };
  entry.sock = sock;
  sessions.set(tenantId, entry);

  sock.ev.on("creds.update", saveCreds);

  const qrPromise = new Promise((resolve) => {
    let resolved = false;
    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        resolve(entry);
      }
    }, 12000);

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;
      if (qr) {
        try {
          entry.qr = await QRCode.toDataURL(qr);
          entry.status = "qr_pending";
        } catch (err) {
          console.error("[whatsapp-qr] failed to generate QR data URL:", err.message);
        }
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          resolve(entry);
        }
      }
      if (connection === "open") {
        entry.status = "connected";
        entry.qr = null;
        await notifyStatus(tenantId, "connected");
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          resolve(entry);
        }
      }
      if (connection === "close") {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const isLoggedOut = statusCode === DisconnectReason.loggedOut || statusCode === 401;
        const isRestart = statusCode === DisconnectReason.restartRequired || statusCode === 515;

        // Clean up socket instance
        cleanupSocket(sock);
        if (entry.sock === sock) {
          entry.sock = null;
        }

        if (isLoggedOut) {
          console.log(`[whatsapp-qr] Session logged out (${statusCode}) for tenant ${tenantId}`);
          sessions.delete(tenantId);
          fs.rmSync(sessionPath, { recursive: true, force: true });
          await notifyStatus(tenantId, "disconnected");
        } else if (isRestart) {
          console.log(`[whatsapp-qr] Restart required (515) for tenant ${tenantId}, reconnecting...`);
          setTimeout(() => startSessionReal(tenantId, true), 1500);
        } else {
          console.log(`[whatsapp-qr] Reconnecting session (${statusCode || "unknown"}) for tenant ${tenantId}...`);
          setTimeout(() => startSessionReal(tenantId, true), 2000);
        }
      }
    });
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;
    for (const msg of messages) {
      if (msg.key.fromMe || !msg.message) continue;
      const text = msg.message.conversation || msg.message.extendedTextMessage?.text;
      if (!text) continue;
      const sender = msg.key.remoteJid.replace("@s.whatsapp.net", "");

      // Send typing status to customer's phone
      try {
        await sock.sendPresenceUpdate("composing", msg.key.remoteJid);
      } catch (err) {}

      await forwardMessage(tenantId, sender, msg.pushName || null, text);

      try {
        await sock.sendPresenceUpdate("paused", msg.key.remoteJid);
      } catch (err) {}
    }
  });

  return qrPromise;
}

async function startSession(tenantId) {
  const existing = sessions.get(tenantId);
  if (existing && existing.status === "connected") return existing;
  if (existing && existing.status === "qr_pending" && existing.qr) return existing;
  if (existing?.sock) {
    cleanupSocket(existing.sock);
    existing.sock = null;
  }
  return MOCK_MODE ? startSessionMock(tenantId) : startSessionReal(tenantId);
}

function getStatus(tenantId) {
  const entry = sessions.get(tenantId);
  if (!entry) return { status: "disconnected", qr: null };
  return { status: entry.status, qr: entry.qr };
}

async function sendMessage(tenantId, to, body) {
  const entry = sessions.get(tenantId);
  if (!entry || entry.status !== "connected") {
    throw new Error("Session is not connected");
  }
  if (MOCK_MODE) {
    console.log(`[MOCK] whatsapp qr -> would send to ${to}: ${body}`);
    return;
  }
  const jid = to.includes("@") ? to : `${to}@s.whatsapp.net`;
  if (entry.sock) {
    try {
      await entry.sock.sendPresenceUpdate("composing", jid);
    } catch (e) {}
  }
  await entry.sock.sendMessage(jid, { text: body });
  if (entry.sock) {
    try {
      await entry.sock.sendPresenceUpdate("paused", jid);
    } catch (e) {}
  }
}

async function disconnectSession(tenantId) {
  const entry = sessions.get(tenantId);
  if (entry?.sock) {
    try {
      await entry.sock.logout().catch(() => {});
    } catch (e) {}
    cleanupSocket(entry.sock);
    entry.sock = null;
  }
  sessions.delete(tenantId);
  const sessionPath = path.join(SESSIONS_DIR, tenantId);
  fs.rmSync(sessionPath, { recursive: true, force: true });
  await notifyStatus(tenantId, "disconnected");
}

module.exports = {
  MOCK_MODE,
  startSession,
  getStatus,
  sendMessage,
  disconnectSession,
  forwardMessage,
};
