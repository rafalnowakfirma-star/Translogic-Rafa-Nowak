/* Przeglądarka brył 3D (three.js r128). Dane: window.OGROD = {models, stained}. */
(function () {
  "use strict";
  var D = window.OGROD;
  if (!D) return;

  function hasWebGL() {
    try {
      var c = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch (e) { return false; }
  }

  var texCache = {};
  function stainedTex(kind) {
    if (texCache[kind]) return texCache[kind];
    var cells = D.stained[kind];
    var W = 512, H = kind === "rect" ? 256 : 512;
    var cv = document.createElement("canvas");
    cv.width = W; cv.height = H;
    var g = cv.getContext("2d");
    g.fillStyle = "#151515"; g.fillRect(0, 0, W, H);
    g.lineJoin = "round"; g.lineWidth = 3; g.strokeStyle = "#151515";
    cells.forEach(function (c) {
      g.beginPath();
      c[0].forEach(function (p, i) { var x = p[0] * W, y = p[1] * W; if (i) g.lineTo(x, y); else g.moveTo(x, y); });
      g.closePath(); g.fillStyle = c[1]; g.fill(); g.stroke();
    });
    var t = new THREE.CanvasTexture(cv);
    texCache[kind] = t;
    return t;
  }

  var MATDEF = {
    wall: [0xEDE9E2, 0.92, 0], plaster: [0xF4F1EB, 0.95, 0], char: [0x2B2724, 0.95, 0],
    roof: [0x4F555C, 0.6, 0.3], roofcopper: [0x6E8C7B, 0.55, 0.35], copper: [0xB06E3C, 0.4, 0.7],
    dark: [0x2B3238, 0.3, 0.2], door: [0x6B4A2F, 0.7, 0], deck: [0xA88160, 0.85, 0],
    gravel: [0xDDD9CF, 1, 0], water: [0x4F87A8, 0.15, 0.15], moss: [0x6E8F4C, 1, 0],
    grass: [0x93A97A, 1, 0], stone: [0x8E8B86, 0.9, 0]
  };
  var matCache = {};
  function mat(name) {
    if (matCache[name]) return matCache[name];
    var m;
    if (name === "glass") {
      m = new THREE.MeshStandardMaterial({ color: 0x9EC3D6, transparent: true, opacity: 0.48, roughness: 0.05, metalness: 0.35, side: THREE.DoubleSide });
    } else {
      var d = MATDEF[name] || MATDEF.wall;
      m = new THREE.MeshStandardMaterial({ color: d[0], roughness: d[1], metalness: d[2], side: THREE.DoubleSide, flatShading: name === "stone" });
    }
    matCache[name] = m;
    return m;
  }
  function std(color, rough, flat) {
    return new THREE.MeshStandardMaterial({ color: color, roughness: rough === undefined ? 0.9 : rough, flatShading: !!flat });
  }

  function polyGeom(pts) {
    var P = pts.map(function (p) { return new THREE.Vector3(p[0], p[2], p[1]); });
    var n = P.length, nx = 0, ny = 0, nz = 0;
    for (var i = 0; i < n; i++) {
      var a = P[i], b = P[(i + 1) % n];
      nx += (a.y - b.y) * (a.z + b.z); ny += (a.z - b.z) * (a.x + b.x); nz += (a.x - b.x) * (a.y + b.y);
    }
    var ax = Math.abs(nx), ay = Math.abs(ny), az = Math.abs(nz);
    var proj = (ax >= ay && ax >= az) ? function (v) { return new THREE.Vector2(v.y, v.z); }
      : (ay >= az) ? function (v) { return new THREE.Vector2(v.x, v.z); }
      : function (v) { return new THREE.Vector2(v.x, v.y); };
    var tris = THREE.ShapeUtils.triangulateShape(P.map(proj), []);
    var pos = [];
    tris.forEach(function (t) { t.forEach(function (k) { pos.push(P[k].x, P[k].y, P[k].z); }); });
    var g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    return g;
  }

  function shapeOf(pts) {
    var s = new THREE.Shape();
    pts.forEach(function (p, i) { if (i) s.lineTo(p[0], p[1]); else s.moveTo(p[0], p[1]); });
    s.closePath();
    return s;
  }

  function mesh(geo, m, cast) {
    var o = new THREE.Mesh(geo, m);
    o.castShadow = cast !== false; o.receiveShadow = true;
    return o;
  }

  function build(it, grp) {
    var o, g, k;
    switch (it.t) {
      case "prism":
        var s = shapeOf(it.pts);
        (it.holes || []).forEach(function (h) { s.holes.push(shapeOf(h)); });
        g = new THREE.ExtrudeGeometry(s, { depth: it.z1 - it.z0, bevelEnabled: false });
        g.rotateX(Math.PI / 2); g.translate(0, it.z1, 0);
        grp.add(mesh(g, mat(it.m)));
        break;
      case "poly":
        grp.add(mesh(polyGeom(it.pts), mat(it.m)));
        break;
      case "flat":
        o = mesh(polyGeom(it.pts.map(function (p) { return [p[0], p[1], it.z]; })), mat(it.m), false);
        grp.add(o);
        break;
      case "ellipse":
        g = new THREE.CircleGeometry(1, 48); g.rotateX(-Math.PI / 2); g.scale(it.rx, 1, it.ry);
        o = mesh(g, mat(it.m), false); o.position.set(it.x, it.z, it.y); grp.add(o);
        break;
      case "panel":
        var dx = it.b[0] - it.a[0], dy = it.b[1] - it.a[1], L = Math.hypot(dx, dy);
        o = mesh(new THREE.BoxGeometry(L, it.z1 - it.z0, it.d), mat(it.m), it.m !== "glass");
        o.position.set((it.a[0] + it.b[0]) / 2, (it.z0 + it.z1) / 2, (it.a[1] + it.b[1]) / 2);
        o.rotation.y = Math.atan2(-dy, dx);
        grp.add(o);
        break;
      case "tree":
        tree(it, grp);
        break;
      case "stone":
        g = new THREE.DodecahedronGeometry(it.r, 0); g.scale(1, it.h / it.r, 0.85);
        o = mesh(g, mat("stone")); o.position.set(it.x, -0.18 + it.h * 0.45, it.y); o.rotation.y = it.x * 3.1;
        grp.add(o);
        break;
      case "chain":
        var cm = mat("copper");
        for (var z = it.z0, j = 0; z < it.z1; z += 0.17, j++) {
          o = mesh(new THREE.TorusGeometry(0.05, 0.014, 6, 10), cm);
          o.position.set(it.x, z, it.y); o.rotation.y = j % 2 ? Math.PI / 2 : 0;
          grp.add(o);
        }
        break;
      case "person":
        var pm = std(0x2A2E33, 0.8);
        o = mesh(new THREE.CylinderGeometry(0.17, 0.2, 0.75, 10), pm); o.position.set(it.x, it.z + 1.15, it.y); grp.add(o);
        o = mesh(new THREE.CylinderGeometry(0.14, 0.12, 0.8, 10), pm); o.position.set(it.x, it.z + 0.4, it.y); grp.add(o);
        o = mesh(new THREE.SphereGeometry(0.12, 12, 10), pm); o.position.set(it.x, it.z + 1.65, it.y); grp.add(o);
        break;
      case "toro":
        var sm = mat("stone");
        [[0.45, 0.12, 0.45, 0.06], [0.16, 0.5, 0.16, 0.37], [0.36, 0.28, 0.36, 0.76]].forEach(function (b) {
          o = mesh(new THREE.BoxGeometry(b[0], b[1], b[2]), sm); o.position.set(it.x, b[3] - 0.2, it.y); grp.add(o);
        });
        g = new THREE.ConeGeometry(0.38, 0.24, 4); o = mesh(g, sm); o.rotation.y = Math.PI / 4;
        o.position.set(it.x, 0.8, it.y); grp.add(o);
        break;
      case "bamboo":
        var bm = std(0x7C9A4A, 0.7);
        for (k = 0; k < it.n; k++) {
          var a = k * 2.399, r = it.r * Math.sqrt((k + 0.5) / it.n), h = 2.6 + (k * 37 % 10) / 8;
          o = mesh(new THREE.CylinderGeometry(0.025, 0.03, h, 6), bm);
          o.position.set(it.x + r * Math.cos(a), h / 2 - 0.2, it.y + r * Math.sin(a)); grp.add(o);
          o = mesh(new THREE.IcosahedronGeometry(0.28, 0), std(0x8DB05A, 1, true));
          o.scale.set(1, 0.6, 1); o.position.set(it.x + r * Math.cos(a), h - 0.3, it.y + r * Math.sin(a)); grp.add(o);
        }
        break;
      case "stained":
        var P = it.pts.map(function (p) { return [p[0], p[2], p[1]]; });
        g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.Float32BufferAttribute([].concat(P[0], P[1], P[2], P[0], P[2], P[3]), 3));
        g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], 2));
        g.computeVertexNormals();
        o = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: stainedTex(it.design), side: THREE.DoubleSide }));
        grp.add(o);
        break;
      case "lantern":
        var sideLen = 2 * it.a * Math.tan(Math.PI / 8), hgt = it.z1 - it.z0;
        var lm = new THREE.MeshBasicMaterial({ map: stainedTex("rect"), side: THREE.DoubleSide });
        for (k = 0; k < 8; k++) {
          var th = k * Math.PI / 4;
          o = new THREE.Mesh(new THREE.PlaneGeometry(sideLen, hgt), lm);
          o.position.set(it.cx + it.a * Math.cos(th), (it.z0 + it.z1) / 2, it.cy + it.a * Math.sin(th));
          o.rotation.y = Math.atan2(Math.cos(th), Math.sin(th));
          grp.add(o);
        }
        g = new THREE.ConeGeometry(it.a / Math.cos(Math.PI / 8), it.z2 - it.z1, 8, 1, true);
        o = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: stainedTex("rose"), side: THREE.DoubleSide }));
        o.rotation.y = Math.PI / 8; o.position.set(it.cx, (it.z1 + it.z2) / 2, it.cy); grp.add(o);
        o = mesh(new THREE.CylinderGeometry(it.a / Math.cos(Math.PI / 8) + 0.05, it.a / Math.cos(Math.PI / 8) + 0.05, 0.12, 8), mat("copper"));
        o.rotation.y = Math.PI / 8; o.position.set(it.cx, it.z1, it.cy); grp.add(o);
        o = mesh(new THREE.SphereGeometry(0.14, 12, 10), mat("copper")); o.position.set(it.cx, it.z2 + 0.08, it.cy); grp.add(o);
        break;
      case "moonwall":
        var mdx = it.b[0] - it.a[0], mdy = it.b[1] - it.a[1], mL = Math.hypot(mdx, mdy);
        var ms = shapeOf([[0, it.z0], [mL, it.z0], [mL, it.z1], [0, it.z1]]);
        var hole = new THREE.Path(); hole.absarc(it.hu, it.hz, it.hr, 0, Math.PI * 2, true);
        ms.holes.push(hole);
        g = new THREE.ExtrudeGeometry(ms, { depth: it.th, bevelEnabled: false, curveSegments: 40 });
        g.translate(0, 0, -it.th / 2);
        o = mesh(g, mat(it.m)); o.rotation.y = Math.atan2(-mdy, mdx); o.position.set(it.a[0], 0, it.a[1]); grp.add(o);
        break;
    }
  }

  function tree(it, grp) {
    var trunkM = std(it.kind === "birch" ? 0xECE9E2 : 0x5B4330, 0.9);
    var o = mesh(new THREE.CylinderGeometry(0.1, 0.16, it.h * 0.55, 7), trunkM);
    o.position.set(it.x, it.h * 0.275 - 0.2, it.y); grp.add(o);
    if (it.kind === "pine") {
      o = mesh(new THREE.ConeGeometry(it.r, it.h * 0.8, 9), std(0x2F5A3A, 1, true));
      o.position.set(it.x, it.h * 0.55, it.y); grp.add(o);
    } else if (it.kind === "maple") {
      [[0, 0, 0, 0xC2452D], [0.45, -0.15, 0.3, 0xD9662F], [-0.4, -0.2, -0.25, 0xB23A2A], [0.1, 0.25, -0.4, 0xE07A36]].forEach(function (c) {
        var m = mesh(new THREE.IcosahedronGeometry(it.r * 0.62, 1), std(c[3], 1, true));
        m.scale.set(1, 0.7, 1);
        m.position.set(it.x + c[0] * it.r, it.h - it.r * 0.5 + c[1] * it.r, it.y + c[2] * it.r); grp.add(m);
      });
    } else {
      o = mesh(new THREE.IcosahedronGeometry(it.r, 1), std(it.kind === "birch" ? 0x9DBF6A : 0x5E8C4A, 1, true));
      o.scale.set(1, 1.15, 1); o.position.set(it.x, it.h - it.r, it.y); grp.add(o);
    }
  }

  function Viewer(root, model) {
    var canvas = root.querySelector("canvas");
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    var scene = new THREE.Scene();
    var cam = new THREE.PerspectiveCamera(32, 1.6, 0.5, 500);
    var cx = model.center[0], cy = model.center[1], R = model.radius;
    scene.add(new THREE.HemisphereLight(0xE4ECF4, 0x5F6E4C, 0.62));
    var sun = new THREE.DirectionalLight(0xFFF1DC, 0.8);
    sun.position.set(cx - 22, 30, cy + 16);
    sun.target.position.set(cx, 0, cy);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    var sc = sun.shadow.camera; sc.left = -R * 1.8; sc.right = R * 1.8; sc.top = R * 1.8; sc.bottom = -R * 1.8; sc.near = 1; sc.far = 120;
    sun.shadow.bias = -0.0008;
    scene.add(sun); scene.add(sun.target);
    var sky = "#DCE7EF";
    try { sky = getComputedStyle(root).getPropertyValue("--sky1").trim() || sky; } catch (e) {}
    scene.fog = new THREE.Fog(new THREE.Color(sky), R * 3.2, R * 7.5);
    var ground = new THREE.Mesh(new THREE.CircleGeometry(R * 9, 64), mat("grass"));
    ground.rotation.x = -Math.PI / 2; ground.position.set(cx, -0.32, cy); ground.receiveShadow = true;
    scene.add(ground);
    var grp = new THREE.Group();
    model.items.forEach(function (it) { build(it, grp); });
    scene.add(grp);

    var st = { az: -0.62, el: 0.6, dist: R * 2.45 };
    var home = { az: st.az, el: st.el, dist: st.dist };
    var dirty = true;
    function place() {
      var ce = Math.cos(st.el);
      cam.position.set(cx + st.dist * ce * Math.sin(st.az), 1.5 + st.dist * Math.sin(st.el), cy + st.dist * ce * Math.cos(st.az));
      cam.lookAt(cx, 1.6, cy);
    }
    function size() {
      var w = canvas.clientWidth, h = canvas.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      cam.aspect = w / h; cam.updateProjectionMatrix();
      dirty = true;
    }
    function loop() {
      if (dirty) { place(); renderer.render(scene, cam); dirty = false; }
      requestAnimationFrame(loop);
    }
    var drag = null;
    canvas.addEventListener("pointerdown", function (e) { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", function (e) {
      if (!drag) return;
      st.az -= (e.clientX - drag.x) * 0.008;
      st.el = Math.min(1.45, Math.max(0.06, st.el + (e.clientY - drag.y) * 0.006));
      drag = { x: e.clientX, y: e.clientY }; dirty = true;
    });
    function end() { drag = null; }
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);
    root.querySelectorAll("[data-act]").forEach(function (b) {
      b.addEventListener("click", function () {
        var a = b.getAttribute("data-act");
        if (a === "in") st.dist = Math.max(R * 0.9, st.dist * 0.82);
        if (a === "out") st.dist = Math.min(R * 5, st.dist / 0.82);
        if (a === "left") st.az += Math.PI / 4;
        if (a === "right") st.az -= Math.PI / 4;
        if (a === "top") { st.el = 1.3; }
        if (a === "eye") { st.el = 0.12; st.dist = R * 1.9; }
        if (a === "home") { st.az = home.az; st.el = home.el; st.dist = home.dist; }
        dirty = true;
      });
    });
    if (window.ResizeObserver) new ResizeObserver(size).observe(canvas); else window.addEventListener("resize", size);
    size(); loop();
  }

  function start() {
    var roots = document.querySelectorAll(".viewer");
    if (!window.THREE || !hasWebGL()) {
      roots.forEach(function (r) { r.classList.add("no3d"); });
      return;
    }
    roots.forEach(function (r) {
      try { Viewer(r, D.models[r.getAttribute("data-model")]); }
      catch (e) { r.classList.add("no3d"); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
