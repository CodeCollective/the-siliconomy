import { sceneConfig } from './scene-config.js';
import { createStandardScene } from './browser.js';
import { createXRScene } from './xr.js';


const canvas = document.getElementById("renderCanvas");
const engine = new BABYLON.Engine(canvas, true);

// Check for WebXR support upfront
const hasWebXR = async () => {
  try {
    return await BABYLON.WebXRSessionManager.IsSessionSupportedAsync('immersive-vr');
  } catch {
    return false;
  }
};

// Main entry point
hasWebXR().then((supported) => {
  if (supported) {
    createXRScene(engine).then((scene) => {
      engine.runRenderLoop(() => scene.render());
    });
  } else {
    const scene = createStandardScene(engine, canvas);
    engine.runRenderLoop(() => scene.render());
  }
});

window.addEventListener("resize", () => {
  engine.resize();
});
