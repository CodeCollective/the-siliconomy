
import { sceneConfig } from './scene-config.js';

export const createStandardScene = (engine, canvas) => {
  const scene = new BABYLON.Scene(engine);
  scene.clearColor = new BABYLON.Color3(...sceneConfig.scene.clearColor);

  // Camera setup
  const camera = new BABYLON.ArcRotateCamera(
    "camera", 
    sceneConfig.camera.alpha, 
    sceneConfig.camera.beta, 
    sceneConfig.camera.radius, 
    BABYLON.Vector3.Zero(), 
    scene
  );
  camera.attachControl(canvas, true);
  camera.upperBetaLimit = sceneConfig.camera.upperBetaLimit;
  camera.lowerRadiusLimit = sceneConfig.camera.lowerRadiusLimit;
  camera.upperRadiusLimit = sceneConfig.camera.upperRadiusLimit;

  // Create lights dynamically
  sceneConfig.lights.forEach(lightConfig => {
    let light;
    switch(lightConfig.type) {
      case 'hemispheric':
        light = new BABYLON.HemisphericLight(
          lightConfig.name,
          new BABYLON.Vector3(...lightConfig.direction),
          scene
        );
        break;
      case 'directional':
        light = new BABYLON.DirectionalLight(
          lightConfig.name,
          new BABYLON.Vector3(...lightConfig.direction),
          scene
        );
        if (lightConfig.intensity) {
          light.intensity = lightConfig.intensity;
        }
        break;
    }
    if (lightConfig.shadowEnabled) {
      light.shadowEnabled = true;
    }
  });

  // Ground
  const ground = BABYLON.MeshBuilder.CreateGround(
    "ground", 
    { 
      width: sceneConfig.ground.width, 
      height: sceneConfig.ground.height 
    }, 
    scene
  );
  ground.position.y = sceneConfig.ground.positionY;
  ground.receiveShadows = sceneConfig.ground.receiveShadows;

  // Box with interaction
  const box = BABYLON.MeshBuilder.CreateBox(
    "box", 
    { size: sceneConfig.box.size }, 
    scene
  );
  box.position.y = sceneConfig.box.positionY;
  box.material = new BABYLON.StandardMaterial(sceneConfig.materials.box.name, scene);
  box.material.diffuseColor = new BABYLON.Color3(...sceneConfig.box.diffuseColor);

  let grabbedBox = null;
    
  scene.onPointerDown = (evt) => {
    const pick = scene.pick(scene.pointerX, scene.pointerY);
    if (pick?.hit && pick.pickedMesh && pick.pickedMesh.name === "box") {
      grabbedBox = pick.pickedMesh;
      box.material.emissiveColor = new BABYLON.Color3(...sceneConfig.box.emissiveColor);
    }
  };

  scene.onPointerUp = () => {
    if (grabbedBox) {
      grabbedBox.material.emissiveColor = new BABYLON.Color3(0, 0, 0);
      grabbedBox = null;
    }
  };

  scene.onPointerMove = () => {
    if (grabbedBox) {
      const groundPos = scene.pick(scene.pointerX, scene.pointerY, 
        (mesh) => mesh.name === "ground")?.pickedPoint;
      if (groundPos) {
        grabbedBox.position.x = groundPos.x;
        grabbedBox.position.z = groundPos.z;
      }
    }
  };

  return scene;
};
