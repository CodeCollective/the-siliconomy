// main.ts
import * as THREE from "three";

const {
  WebGLRenderer,
  Scene,
  Color,
  PerspectiveCamera,
  HemisphereLight,
  DirectionalLight,
  PMREMGenerator,
  ACESFilmicToneMapping,
  SRGBColorSpace,
} = THREE;
// @ts-ignore
import { RoomEnvironment } from "../three.js/examples/jsm/environments/RoomEnvironment.js";
// @ts-ignore
import { GLTFLoader } from "../three.js/examples/jsm/loaders/GLTFLoader.js";
// @ts-ignore
import { OrbitControls } from "../three.js/examples/jsm/controls/OrbitControls.js";
import type { GLTF } from "../three.js/examples/jsm/loaders/GLTFLoader.js";

// ⬇️ New: XR locomotion controls
import { setupXRLocomotionControls } from "./controls";

function initViewer(): void {
  const canvas = document.getElementById(
    "webgpu-canvas"
  ) as HTMLCanvasElement | null;
  if (!canvas) throw new Error("Canvas element #webgpu-canvas not found.");

  const renderer = new WebGLRenderer({
    canvas,
    antialias: false,
    powerPreference: "high-performance",
  });

  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);

  // Color management & tonemapping
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;

  const scene = new Scene();
  scene.background = new Color(0xf2f2f2);

  // Environment for PBR
  const pmrem = new PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envTex;

  const camera = new PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );
  camera.position.set(0, 1.6, -5);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // WebXR
  renderer.xr.enabled = true;

  console.log("Init Controls");
  // ⬇️ Wire up locomotion + controller/hand models (replaces ad-hoc code)
  const controlsXR = setupXRLocomotionControls({
    renderer,
    camera,
    scene,
    options: {
      movementSpeed: 1.5,
      turnAngle: Math.PI / 6,
      deadzone: 0.15,
      snapCooldownMs: 200,
      addHands: true,
      addControllerModels: true,
      addVRButton: true, // replaces manual VRButton.createButton(...)
      verbose: true,
    },
  });

  console.log("Init Controls Done");
  // Lights
  scene.add(new HemisphereLight(0xffffff, 0x444466, 1.1));
  const dir = new DirectionalLight(0xffffff, 2.2);
  dir.position.set(0, 3, 0);
  scene.add(dir);
  scene.add(new HemisphereLight(0xffffff, 0x333333, 1.0));

  // Model
  const loader = new GLTFLoader();
  loader.load(
    "/laser_cutter.glb",
    (gltf: GLTF) => {
      const root = gltf.scene;
      root.scale.setScalar(0.001); // mm → m
      scene.add(root);

      controls.target.set(0, 0, 0);
      controls.update();
    },
    undefined,
    (error: Error) => console.error("Error loading GLTF:", error)
  );

  // Resize (only when NOT in XR)
  window.addEventListener("resize", () => {
    if (renderer.xr.isPresenting) return; // let WebXR manage size
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  // Keep camera happy on session start/end
  renderer.xr.addEventListener("sessionstart", () => {
    // No renderer.setSize here — WebXR manages it.
    // If you need to tweak resolution scale:
    // renderer.xr.setFramebufferScaleFactor(1.0);
  });

  renderer.xr.addEventListener("sessionend", () => {
    // Restore canvas size to window when exiting VR
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  // Animation loop
  // Animation loop
  let last = performance.now();
  function animate(t = performance.now()) {
    const dt = (t - last) / 1000;
    last = t;

    // Only let OrbitControls run when NOT in XR so it doesn’t fight the rig
    if (!renderer.xr.isPresenting) {
      controls.update();
    }

    // ✅ Only update XR locomotion AFTER entering VR
    if (renderer.xr.isPresenting) {
      controlsXR.tick(dt);
    }

    renderer.render(scene, camera);
  }

  renderer.setAnimationLoop(animate);
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    initViewer();
  } catch (err) {
    console.error("Failed to initialize viewer:", err);
    const el = document.createElement("div");
    el.style.cssText =
      "position:fixed;top:0;left:0;right:0;padding:12px;background:#300;color:#fff;font:14px/1.4 system-ui;z-index:9999";
    el.textContent = err instanceof Error ? err.message : String(err);
    document.body.appendChild(el);
  }
});
