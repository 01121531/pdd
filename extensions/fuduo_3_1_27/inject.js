"use strict";
(() => {
  // src/inject.ts
  var REQ_EVENT = "__pdd_proxy_request__";
  var RES_EVENT = "__pdd_proxy_response__";
  var READY_EVENT = "__pdd_proxy_ready__";
  var INSTANCE_KEY = "__pdd_proxy_instance__";
  var instanceId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  var nonce = crypto.getRandomValues(new Uint8Array(16)).reduce((s, b) => s + b.toString(16).padStart(2, "0"), "");
  window[INSTANCE_KEY] = instanceId;
  var nativeFetch = window.fetch.bind(window);
  var ALLOWED_HOSTS = /* @__PURE__ */ new Set([
    "mms.pinduoduo.com",
    "yingxiao.pinduoduo.com",
    "mobile.pinduoduo.com",
    "live.pinduoduo.com",
    "mms.yangkeduo.com",
    "yingxiao.yangkeduo.com"
  ]);
  function isAllowedUrl(url) {
    try {
      const { hostname, protocol } = new URL(url, location.origin);
      if (!["https:", "http:"].includes(protocol)) return false;
      return ALLOWED_HOSTS.has(hostname);
    } catch {
      return false;
    }
  }
  var pddApi = null;
  var _cachedWpArrays = null;
  var _wpCacheTime = 0;
  var WP_CACHE_TTL = 3e3;
  function getAllWebpackArrays() {
    const now = Date.now();
    if (_cachedWpArrays && now - _wpCacheTime < WP_CACHE_TTL) return _cachedWpArrays;
    const win = window;
    const out = [];
    const seen = /* @__PURE__ */ new Set();
    if (Array.isArray(win.webpackJsonp)) {
      seen.add(win.webpackJsonp);
      out.push(win.webpackJsonp);
    }
    for (const key of Object.keys(win)) {
      if (key.startsWith("webpackChunk") && Array.isArray(win[key])) {
        const arr = win[key];
        if (!seen.has(arr)) {
          seen.add(arr);
          out.push(arr);
        }
      }
    }
    _cachedWpArrays = out;
    _wpCacheTime = now;
    return out;
  }
  var hookedWebpackArrays = /* @__PURE__ */ new WeakSet();
  var _hookDebouncePending = false;
  function hookWebpackChunkPush() {
    for (const wp of getAllWebpackArrays()) {
      if (hookedWebpackArrays.has(wp)) continue;
      hookedWebpackArrays.add(wp);
      const origPush = wp.push.bind(wp);
      wp.push = (...items) => {
        const ret = origPush(...items);
        if (isCurrentInstance() && !pddApi && !_capturing && !_hookDebouncePending) {
          _hookDebouncePending = true;
          setTimeout(() => {
            _hookDebouncePending = false;
            if (isCurrentInstance() && !pddApi) tryCapture();
          }, 50);
        }
        return ret;
      };
    }
  }
  var _capturing = false;
  function captureRequire() {
    const arrays = getAllWebpackArrays();
    if (!arrays.length) return null;
    for (const wp of arrays) {
      let captured = null;
      const id = "__pdd_assist_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8) + "__";
      try {
        wp.push([
          [id],
          { [id](_m, _e, req) {
            captured = req;
          } },
          [[id]]
        ]);
      } catch {
        continue;
      }
      if (captured) return captured;
    }
    return null;
  }
  var REQUIRED_METHODS = ["get", "post", "fetch"];
  function isApiModule(mod) {
    return REQUIRED_METHODS.every((m) => typeof mod[m] === "function");
  }
  function findApiModule(req) {
    const KNOWN_IDS = ["+sIe", "sIe", "+SIe"];
    for (const id of KNOWN_IDS) {
      try {
        const mod = req(id);
        if (mod && isApiModule(mod)) return mod;
      } catch {
      }
    }
    if (!req.c) return null;
    for (const cached of Object.values(req.c)) {
      try {
        if (cached?.exports && isApiModule(cached.exports)) return cached.exports;
      } catch {
      }
    }
    return null;
  }
  function tryCapture() {
    if (_capturing) return false;
    _capturing = true;
    try {
      hookWebpackChunkPush();
      if (pddApi) return true;
      const req = captureRequire();
      if (!req) return false;
      const api = findApiModule(req);
      if (!api) return false;
      pddApi = api;
      console.log(
        "%c[PDD-Inject] API module captured:",
        "color:#4caf50;font-weight:bold",
        Object.keys(pddApi).filter((k) => typeof pddApi[k] === "function")
      );
      window.dispatchEvent(new CustomEvent(READY_EVENT, { detail: { nonce } }));
      return true;
    } finally {
      _capturing = false;
    }
  }
  var MAX_RETRIES = 40;
  var retries = 0;
  var LATE_SCAN_MS = 6e4;
  var LATE_SCAN_INTERVAL_MS = 3e3;
  var lateScanTimer = null;
  var pollTimer = null;
  function isCurrentInstance() {
    return window[INSTANCE_KEY] === instanceId;
  }
  function stopAllTimers() {
    if (lateScanTimer !== null) {
      clearInterval(lateScanTimer);
      lateScanTimer = null;
    }
    if (pollTimer !== null) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  }
  function startLateScan() {
    if (lateScanTimer !== null || pddApi) return;
    const started = Date.now();
    lateScanTimer = setInterval(() => {
      if (!isCurrentInstance() || pddApi || Date.now() - started > LATE_SCAN_MS) {
        stopAllTimers();
        return;
      }
      _cachedWpArrays = null;
      hookWebpackChunkPush();
      if (tryCapture()) stopAllTimers();
    }, LATE_SCAN_INTERVAL_MS);
  }
  function pollCapture() {
    hookWebpackChunkPush();
    if (!isCurrentInstance()) return;
    if (pddApi) {
      stopAllTimers();
      return;
    }
    if (retries >= MAX_RETRIES) {
      if (!pddApi) {
        console.warn(
          "[PDD-Inject] failed to capture API module after",
          MAX_RETRIES,
          "retries; still listening for late webpack chunks (1 min)"
        );
        startLateScan();
      }
      return;
    }
    retries++;
    if (!tryCapture()) {
      pollTimer = setTimeout(pollCapture, retries < 10 ? 500 : 1500);
    } else {
      stopAllTimers();
    }
  }
  if (document.readyState === "complete") {
    pollCapture();
  } else {
    window.addEventListener("load", () => setTimeout(pollCapture, 300));
  }
  function sendResponse(id, ok, body, error) {
    window.dispatchEvent(
      new CustomEvent(RES_EVENT, {
        detail: { id, ok, status: ok ? 200 : 0, body, error }
      })
    );
  }
  window.dispatchEvent(new CustomEvent(READY_EVENT + ":loaded", { detail: { nonce } }));
  window.addEventListener(REQ_EVENT, async (e) => {
    if (window[INSTANCE_KEY] !== instanceId) return;
    const detail = e.detail;
    const { id, url, options } = detail;
    if (detail.nonce !== nonce) {
      sendResponse(id, false, null, "invalid nonce");
      return;
    }
    if (!isAllowedUrl(url)) {
      sendResponse(id, false, null, `blocked: URL host not in whitelist`);
      return;
    }
    if (options?.raw) {
      try {
        const resp = await nativeFetch(url, {
          method: options.method || "POST",
          headers: options.headers || { "Content-Type": "application/json" },
          credentials: "include",
          body: options.body ?? void 0
        });
        const body = await resp.json().catch(() => null);
        sendResponse(id, resp.ok, body);
      } catch (err) {
        const msg = err instanceof Error ? err.message : typeof err === "string" ? err : (() => {
          try {
            return JSON.stringify(err);
          } catch {
            return "\u8BF7\u6C42\u5F02\u5E38";
          }
        })();
        sendResponse(id, false, null, msg);
      }
      return;
    }
    if (!pddApi && !tryCapture()) {
      sendResponse(id, false, null, "PDD API not ready");
      return;
    }
    try {
      const method = (options?.method || "GET").toUpperCase();
      let result;
      if (method === "POST") {
        const body = options?.body ? JSON.parse(options.body) : {};
        result = await pddApi.post(url, body);
      } else if (method === "DELETE") {
        result = await pddApi.del(url);
      } else if (method === "PUT") {
        const body = options?.body ? JSON.parse(options.body) : {};
        result = await pddApi.put(url, body);
      } else {
        result = await pddApi.get(url);
      }
      sendResponse(id, true, result);
    } catch (err) {
      const errObj = err;
      if (errObj?.data && typeof errObj.data === "object") {
        sendResponse(id, true, errObj.data);
      } else if (typeof errObj === "object" && errObj !== null && ("error_code" in errObj || "errorCode" in errObj || errObj.success === false)) {
        sendResponse(id, true, errObj);
      } else {
        const msg = errObj?.message ?? errObj?.error_msg ?? errObj?.errorMsg;
        sendResponse(id, false, null, typeof msg === "string" ? msg : (() => {
          try {
            return JSON.stringify(err);
          } catch {
            return "\u8BF7\u6C42\u5F02\u5E38";
          }
        })());
      }
    }
  });
  console.log(
    `%c[PDD-Inject] v1.1 installed (${instanceId})`,
    "color:#2196f3;font-weight:bold"
  );
})();
