// main.ts
import { WebGPURenderer } from 'three/webgpu';
import {
  Scene,
  Color,
  PerspectiveCamera,
  HemisphereLight,
  DirectionalLight,              // ⭐
  PMREMGenerator,                // ⭐
  ACESFilmicToneMapping,         // ⭐
  SRGBColorSpace,                // ⭐
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'; // ⭐
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

function ensureWebGPU() {
  if (typeof navigator === 'undefined' || !(navigator as any).gpu) {
    throw new Error('WebGPU not available. Use a compatible browser/device and run over HTTPS.');
  }
  if (location.protocol !== 'https:') {
    throw new Error('WebGPU requires a secure context. Serve this over HTTPS.');
  }
}

async function initViewer(): Promise<void> {
  ensureWebGPU();

  const canvas = document.getElementById('webgpu-canvas') as HTMLCanvasElement | null;
  if (!canvas) throw new Error('Canvas element #webgpu-canvas not found.');

  // ✅ Use the dedicated WebGPU entry and pass the existing canvas
  const renderer = new WebGPURenderer({
    canvas,
    antialias: false,
    powerPreference: 'high-performance',
  });
  await renderer.init();

  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);

  // ⭐ Color management & tonemapping
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;

  const scene = new Scene();
  scene.background = new Color(0xf2f2f2); // ⭐ lighter bg so the model pops

  // ⭐ Add an environment for PBR
  const pmrem = new PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envTex;

  const camera = new PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 1.6, -5);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // ⭐ Slightly brighter hemi + a directional “key” light
  scene.add(new HemisphereLight(0xffffff, 0x444466, 1.1));
  const dir = new DirectionalLight(0xffffff, 2.2);
  dir.position.set(0, 3, 0);
  scene.add(dir);


  scene.add(new HemisphereLight(0xffffff, 0x333333, 1.0));

  const loader = new GLTFLoader();
loader.load(
  '/laser_cutter.glb',
  (gltf) => {
    const root = gltf.scene;

    // Scale millimeters → meters (1000x smaller)
    root.scale.setScalar(0.001);

    scene.add(root);

    // Frame the camera to fit the model
    controls.target.set(0, 0, 0);
    controls.update();
  },
  undefined,
  (error) => console.error('Error loading GLTF:', error)
);


  window.addEventListener('resize', () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initViewer().catch((err) => {
    console.error('Failed to initialize viewer:', err);
    const el = document.createElement('div');
    el.style.cssText =
      'position:fixed;top:0;left:0;right:0;padding:12px;background:#300;color:#fff;font:14px/1.4 system-ui;z-index:9999';
    el.textContent = String(err?.message ?? err);
    document.body.appendChild(el);
  });
});
