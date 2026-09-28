import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

export default function WhatsAppQrConnect() {
  const [status, setStatus] = useState("idle");
  const [qr, setQr] = useState(null);
  const [error, setError] = useState("");
  const pollRef = useRef(null);

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function startPolling() {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const s = await api.getWhatsAppQrStatus();
        setStatus(s.status);
        if (s.qr) {
          setQr(s.qr);
        } else if (s.status === "connected" || s.status === "disconnected") {
          setQr(null);
        }
        if (s.status === "connected") {
          stopPolling();
        }
      } catch {
        // Keep polling through transient network errors
      }
    }, 1000);
  }

  useEffect(() => {
    api
      .getWhatsAppQrStatus()
      .then((s) => {
        setStatus(s.status);
        if (s.qr) setQr(s.qr);
        if (s.status === "qr_pending" || s.status === "connecting") {
          startPolling();
        }
      })
      .catch(() => {});
    return () => stopPolling();
  }, []);

  async function handleStart() {
    setError("");
    setStatus("connecting");
    try {
      const data = await api.startWhatsAppQr();
      setStatus(data.status);
      if (data.qr) setQr(data.qr);
      if (data.status !== "connected") {
        startPolling();
      }
    } catch (err) {
      setError(err.message);
      setStatus("idle");
    }
  }

  async function handleDisconnect() {
    setError("");
    stopPolling();
    try {
      await api.disconnectWhatsAppQr();
      setStatus("disconnected");
      setQr(null);
    } catch (err) {
      setError(err.message);
    }
  }

  if (status === "connected") {
    return (
      <div className="flex items-center justify-between">
        <p className="text-sm text-wa font-medium">Connected</p>
        <button
          onClick={handleDisconnect}
          className="text-xs text-red-600 hover:underline border border-line px-2 py-1 rounded hover:bg-red-50 transition"
        >
          Disconnect & Scan New QR
        </button>
      </div>
    );
  }

  return (
    <div>
      {qr && (
        <>
          <div className="mb-3 flex justify-center">
            <img
              src={qr}
              alt="Scan this code with WhatsApp to connect"
              className="w-40 h-40 rounded-lg border border-line"
            />
          </div>
          <p className="text-xs text-ink-muted text-center mb-3">
            Open WhatsApp → Linked devices → Link a device, and scan this code.
          </p>
        </>
      )}
      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      <button
        onClick={handleStart}
        disabled={status === "connecting"}
        className="w-full rounded-lg bg-accent text-white text-sm font-medium py-2 hover:opacity-90 transition disabled:opacity-60"
      >
        {status === "connecting" ? "Generating qr code…" : qr ? "Refresh qr code" : "Connect via qr code"}
      </button>
    </div>
  );
}
