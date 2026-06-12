(() => {
  // --- navigator.webdriver ---
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
  });

  // --- navigator.plugins ---
  if (navigator.plugins.length === 0) {
    const makePlugin = (name, filename, description) => {
      const p = Object.create(Plugin.prototype);
      Object.defineProperties(p, {
        name: { value: name, enumerable: true },
        filename: { value: filename, enumerable: true },
        description: { value: description, enumerable: true },
        length: { value: 1, enumerable: true },
      });
      return p;
    };
    const plugins = [
      makePlugin('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format'),
      makePlugin('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', ''),
      makePlugin('Native Client', 'internal-nacl-plugin', ''),
    ];
    const pluginArray = Object.create(PluginArray.prototype);
    plugins.forEach((p, i) => Object.defineProperty(pluginArray, i, { value: p, enumerable: true }));
    Object.defineProperty(pluginArray, 'length', { value: plugins.length, enumerable: true });
    pluginArray.item = (i) => plugins[i] || null;
    pluginArray.namedItem = (name) => plugins.find((p) => p.name === name) || null;
    pluginArray.refresh = () => {};
    Object.defineProperty(navigator, 'plugins', { get: () => pluginArray });
  }

  // --- navigator.permissions.query ---
  const origQuery = navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query = (params) => {
    if (params.name === 'notifications') {
      return Promise.resolve({ state: Notification.permission });
    }
    return origQuery(params);
  };

  // --- WebGL renderer ---
  const VENDOR = 'Google Inc. (Intel)';
  const RENDERER = 'ANGLE (Intel, Mesa Intel(R) UHD Graphics 630 (CFL GT2), OpenGL 4.6)';

  const origGetParam = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function (param) {
    if (param === 37445) return VENDOR;
    if (param === 37446) return RENDERER;
    return origGetParam.call(this, param);
  };

  if (typeof WebGL2RenderingContext !== 'undefined') {
    const origGetParam2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function (param) {
      if (param === 37445) return VENDOR;
      if (param === 37446) return RENDERER;
      return origGetParam2.call(this, param);
    };
  }

  // --- chrome.app / chrome.csi / chrome.loadTimes ---
  if (!window.chrome) window.chrome = {};
  if (!window.chrome.app) {
    window.chrome.app = {
      isInstalled: false,
      InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
      RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
    };
  }
  if (!window.chrome.csi) window.chrome.csi = function () { return {}; };
  if (!window.chrome.loadTimes) window.chrome.loadTimes = function () { return {}; };

  // --- Mask Function.prototype.toString ---
  const origToString = Function.prototype.toString;
  const overrides = new WeakMap();
  const markNative = (fn, name) => overrides.set(fn, `function ${name}() { [native code] }`);

  Function.prototype.toString = function () {
    return overrides.has(this) ? overrides.get(this) : origToString.call(this);
  };

  markNative(Function.prototype.toString, 'toString');
  markNative(navigator.permissions.query, 'query');
  markNative(WebGLRenderingContext.prototype.getParameter, 'getParameter');
  if (typeof WebGL2RenderingContext !== 'undefined') {
    markNative(WebGL2RenderingContext.prototype.getParameter, 'getParameter');
  }
  markNative(window.chrome.csi, 'csi');
  markNative(window.chrome.loadTimes, 'loadTimes');
})();
