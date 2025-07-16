
import { sceneConfig } from './scene-config.js';

export const createXRScene = async (engine) => {
  const scene = new BABYLON.Scene(engine);
  scene.clearColor = new BABYLON.Color3(...sceneConfig.scene.clearColor);

  // Create ground
  const ground = BABYLON.MeshBuilder.CreateGround(
    "ground", 
    { 
      width: sceneConfig.ground.width, 
      height: sceneConfig.ground.height 
    }, 
    scene
  );
  ground.position.y = sceneConfig.ground.positionY;

  // Create box
  const box = BABYLON.MeshBuilder.CreateBox(
    "box", 
    { size: sceneConfig.box.size }, 
    scene
  );
  box.position.y = sceneConfig.box.positionY;
  box.material = new BABYLON.StandardMaterial(sceneConfig.materials.box.name, scene);
  box.material.diffuseColor = new BABYLON.Color3(...sceneConfig.box.diffuseColor);

  // Enable WebXR
  const xr = await scene.createDefaultXRExperienceAsync({
    floorMeshes: [ground],
  });

  // Enable pointer selection
  const pointerSelection = xr.baseExperience.featuresManager.enableFeature(
    BABYLON.WebXRFeatureName.POINTER_SELECTION,
    'latest',
    {
      xrInput: xr.input,
      enablePointerSelectionOnAllControllers: true,
      disablePointerUpOnTouchOut: true,
    }
  );

  // Handle grabbing
  pointerSelection.onButtonDownObservable.add((event) => {
    const pick = scene.pickWithRay(event.ray);
    if (pick?.hit && pick.pickedMesh && pick.pickedMesh.name === "box") {
      pick.pickedMesh.setParent(event.inputSource.grip);
    }
  });

  pointerSelection.onButtonUpObservable.add((event) => {
    const grip = event.inputSource.grip;
    if (grip && grip.children.length > 0) {
      const mesh = grip.children[0];
      if (mesh.name === "box") {
        mesh.setParent(null);
      }
    }
  });

  return scene;
};
