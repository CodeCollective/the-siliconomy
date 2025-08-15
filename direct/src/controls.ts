/*
 * XR Locomotion + Snap-Turn Controls for three.js (TypeScript)
 * ------------------------------------------------------------
 * Drop-in utility that wires WebXR controller models, logs controller
 * connections, and exposes a per-frame `tick(dt)` you can call from
 * your animation loop. Designed to coexist with your own setAnimationLoop.
 *
 * Usage (in your main.ts):
 *
 *   import { setupXRLocomotionControls } from './controls';
 *   const ctrl = setupXRLocomotionControls({ renderer, camera, scene, options: {
 *     movementSpeed: 1.5,
 *     turnAngle: Math.PI / 6,
 *     deadzone: 0.15,
 *     snapCooldownMs: 200,
 *     addHands: true,
 *     addVRButton: true,
 *   }});
 *
 *   // inside your animate(t):
 *   const dt = (t - lastT) / 1000; lastT = t;
 *   ctrl.tick(dt);
 *
 *   // when tearing down:
 *   ctrl.dispose();
 */

import * as THREE from 'three';
import {
  XRControllerModelFactory
} from '../three.js/examples/jsm/webxr/XRControllerModelFactory.js';
import {
  XRHandModelFactory
} from '../three.js/examples/jsm/webxr/XRHandModelFactory.js';
import { VRButton } from '../three.js/examples/jsm/webxr/VRButton.js';

export type XRControlsOptions = {
  /** meters per second */
  movementSpeed?: number;
  /** radians per snap */
  turnAngle?: number;
  /** 0..1 */
  deadzone?: number;
  /** ms */
  snapCooldownMs?: number;
  /** attach mesh hand models if supported */
  addHands?: boolean;
  /** attach controller 3D models to grips */
  addControllerModels?: boolean;
  /** insert a VR button (with local-floor) */
  addVRButton?: boolean;
  /** optional: custom VRButton init params */
  vrButtonInit?: any;
  /** log connect/disconnect events */
  verbose?: boolean;
};

export type XRControlsDeps = {
  renderer: THREE.WebGLRenderer;
  camera: THREE.PerspectiveCamera; // your app camera
  scene: THREE.Scene;
  options?: XRControlsOptions;
};

export type XRControls = {
  /** Call once per frame with seconds */
  tick: (dt: number) => void;
  /** Enable/disable locomotion without tearing down */
  setEnabled: (enabled: boolean) => void;
  /** Cleanup all event listeners and scene objects */
  dispose: () => void;
  /** Accessors */
  getRig: () => THREE.Object3D | null;
  /** Debug helper to read raw pads */
  getGamepads: () => { left?: Gamepad; right?: Gamepad };
};

/** Internal structure */
type Handedness = XRHandedness; // 'left' | 'right' | 'none'

interface ControllerSlots {
  controller: THREE.Object3D; // bare controller (events)
  grip: THREE.Object3D;       // controller grip (models)
  hand?: THREE.Object3D;      // optional hand
}

/** Utility: safely get the XR rig (parent of XR camera) when in-session. */
function getRig(renderer: THREE.WebGLRenderer, fallback: THREE.Object3D | null = null): THREE.Object3D | null {
  // During an immersive session, renderer.xr.getCamera() returns an XR camera
  // that is a child of a rig group. We move that rig for locomotion.
  const xrCam = renderer.xr.getCamera();
  return (xrCam && xrCam.parent) ? xrCam.parent : fallback;
}

export function setupXRLocomotionControls({ renderer, camera, scene, options }: XRControlsDeps): XRControls {
  const opts: Required<XRControlsOptions> = {
    movementSpeed: 1.5,
    turnAngle: Math.PI / 6,
    deadzone: 0.15,
    snapCooldownMs: 200,
    addHands: true,
    addControllerModels: true,
    addVRButton: true,
    vrButtonInit: { requiredFeatures: ['local-floor'] },
    verbose: true,
    ...(options || {})
  } as Required<XRControlsOptions>;

  renderer.xr.enabled = true;

  // Optional: add VRButton
  if (opts.addVRButton) {
    const btn = VRButton.createButton(renderer, opts.vrButtonInit);
    // ensure only one button is attached
    if (!document.body.contains(btn)) document.body.appendChild(btn);
  }

  const controllerModelFactory = new XRControllerModelFactory();
  const handModelFactory = new XRHandModelFactory();

  // Allocate slots for left/right
  const slots: Partial<Record<Handedness, ControllerSlots>> = {};

  // Pre-fetch controllers & grips by index (0/1). Handedness is known at 'connected'.
  const c0 = renderer.xr.getController(0);
  const c1 = renderer.xr.getController(1);
  const g0 = renderer.xr.getControllerGrip(0);
  const g1 = renderer.xr.getControllerGrip(1);

  // Attach controller 3D models to grips
  if (opts.addControllerModels) {
    g0.add(controllerModelFactory.createControllerModel(g0));
    g1.add(controllerModelFactory.createControllerModel(g1));
  }

  // Add to scene now; handedness mapping comes on 'connected'
  scene.add(c0, c1, g0, g1);

  const onConnected = (ev: any) => {
    const src: XRInputSource = ev.data;
    const handed = (src.handedness || 'none') as Handedness;

    if (opts.verbose) console.log('[XR] connected', handed, src.profiles, !!src.gamepad);

    const slot: ControllerSlots = {
      controller: (handed === 'left' ? c0 : c1),
      grip: (handed === 'left' ? g0 : g1),
    };

    if (opts.addHands && typeof (renderer.xr as any).getHand === 'function') {
      const h = (renderer.xr as any).getHand(handed === 'left' ? 0 : 1) as THREE.Object3D;
      const handModel = handModelFactory.createHandModel(h, 'mesh');
      h.add(handModel);
      scene.add(h);
      slot.hand = h;
    }
    slots[handed] = slot;
  };

  const onDisconnected = (ev: any) => {
    const src: XRInputSource = ev.data;
    const handed = (src.handedness || 'none') as Handedness;
    if (opts.verbose) console.log('[XR] disconnected', handed);
    delete slots[handed];
  };

  c0.addEventListener('connected', onConnected);
  c1.addEventListener('connected', onConnected);
  c0.addEventListener('disconnected', onDisconnected);
  c1.addEventListener('disconnected', onDisconnected);

  // Locomotion state
  let enabled = true;
  let snapBlocked = false;

  function getPads(): { left?: Gamepad; right?: Gamepad } {
    const left = (slots['left']?.controller as any)?.inputSource?.gamepad as Gamepad | undefined;
    const right = (slots['right']?.controller as any)?.inputSource?.gamepad as Gamepad | undefined;
    return { left, right };
  }

  function moveRigXZ(rig: THREE.Object3D, head: THREE.Camera, dx: number, dy: number, dt: number) {
    // forward/right derived from head orientation, projected to XZ
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(head.quaternion);
    forward.y = 0; forward.normalize();

    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(head.quaternion);
    right.y = 0; right.normalize();

    const speed = opts.movementSpeed * dt;
    rig.position.addScaledVector(forward, dy * speed);
    rig.position.addScaledVector(right,   dx * speed);
  }

  function snapTurn(rig: THREE.Object3D, axis: number) {
    if (snapBlocked) return;
    if (Math.abs(axis) < 0.9) return;
    rig.rotation.y += axis > 0 ? opts.turnAngle : -opts.turnAngle;
    snapBlocked = true;
    setTimeout(() => { snapBlocked = false; }, opts.snapCooldownMs);
  }

  function tick(dt: number) {
    if (!enabled) return;
    if (!renderer.xr.isPresenting) return;

    const rig = getRig(renderer);
    if (!rig) return;

    const head = renderer.xr.getCamera(camera);

    const { left, right } = getPads();

    // Left thumbstick: axes[0] = X, axes[1] = Y
    if (left && left.axes && left.axes.length >= 2) {
      const ax = left.axes[0];
      const ay = left.axes[1];
      const dz = opts.deadzone;
      const dx = Math.abs(ax) > dz ? ax : 0;
      const dy = Math.abs(ay) > dz ? ay : 0;
      if (dx || dy) moveRigXZ(rig, head, dx, dy, dt);
    }

    // Right thumbstick X: snap turn
    if (right && right.axes && right.axes.length >= 1) {
      const turnAxis = right.axes[0];
      snapTurn(rig, turnAxis);
    }
  }

  function setEnabled(v: boolean) { enabled = v; }

  function dispose() {
    c0.removeEventListener('connected', onConnected);
    c1.removeEventListener('connected', onConnected);
    c0.removeEventListener('disconnected', onDisconnected);
    c1.removeEventListener('disconnected', onDisconnected);

    // Remove scene attachments (keep grips/controllers managed by XR session)
    if (slots['left']?.hand) scene.remove(slots['left']!.hand!);
    if (slots['right']?.hand) scene.remove(slots['right']!.hand!);

    // best-effort: clear references
    (slots as any)['left'] = undefined;
    (slots as any)['right'] = undefined;
  }

  return {
    tick,
    setEnabled,
    dispose,
    getRig: () => getRig(renderer),
    getGamepads: getPads,
  };
}
