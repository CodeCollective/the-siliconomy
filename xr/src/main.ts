import * as BABYLON from "@babylonjs/core";
import HavokPhysics from "@babylonjs/havok";
import type { HavokPhysicsWithBindings } from "@babylonjs/havok";
import "@babylonjs/loaders/glTF";
import "@babylonjs/core/Materials/Textures/Loaders";

const canvas = document.createElement("canvas");
canvas.style.width = "100%";
canvas.style.height = "100%";
document.querySelector<HTMLDivElement>("#app")?.appendChild(canvas);

const engine = new BABYLON.Engine(canvas, true);
let havokInstance: HavokPhysicsWithBindings;
let scene: BABYLON.Scene;

async function createScene() {
  // Load Havok WASM
  const wasmBinary = await fetch(
    "./node_modules/@babylonjs/havok/lib/esm/HavokPhysics.wasm"
  );
  const wasmBinaryArrayBuffer = await wasmBinary.arrayBuffer();
  havokInstance = await HavokPhysics({ wasmBinary: wasmBinaryArrayBuffer });
  const havokPlugin = new BABYLON.HavokPlugin(true, havokInstance);

  // Scene setup (units in millimeters)
  const scene = new BABYLON.Scene(engine);
  scene.enablePhysics(new BABYLON.Vector3(0, -9800, 0), havokPlugin);

  // Lighting - Make sure we have good lighting
  const hemiLight = new BABYLON.HemisphericLight(
    "hemi",
    new BABYLON.Vector3(0, 1, 0),
    scene
  );
  hemiLight.intensity = 0.7;
  
  const dirLight = new BABYLON.DirectionalLight(
    "dir",
    new BABYLON.Vector3(0, -1, 1),
    scene
  );
  dirLight.intensity = 0.5;

  // Ground (scaled to mm)
  const ground = BABYLON.MeshBuilder.CreateGround(
    "ground",
    { width: 2000, height: 2000 },
    scene
  );
  ground.position.y = 0;
  const groundMat = new BABYLON.StandardMaterial("groundMat", scene);
  groundMat.diffuseColor = new BABYLON.Color3(0.2, 0.2, 0.3);
  ground.material = groundMat;

  // Add physics to ground
  new BABYLON.PhysicsAggregate(
    ground,
    BABYLON.PhysicsShapeType.BOX,
    { mass: 0, restitution: 0.7 },
    scene
  );

  // Environment - Add fallback if environment texture fails
  try {
    scene.environmentTexture = BABYLON.CubeTexture.CreateFromPrefilteredData(
      "https://assets.babylonjs.com/environments/environmentSpecular.dds",
      scene
    );
  } catch (error) {
    console.warn("Failed to load environment texture:", error);
    // Create a simple skybox as fallback
    const skybox = BABYLON.MeshBuilder.CreateSphere("skybox", {diameter: 4000}, scene);
    const skyboxMaterial = new BABYLON.StandardMaterial("skyboxMaterial", scene);
    skyboxMaterial.backFaceCulling = false;
    skyboxMaterial.emissiveColor = new BABYLON.Color3(0.1, 0.1, 0.15);
    skybox.material = skyboxMaterial;
    skybox.infiniteDistance = true;
  }

  // Camera - Fix initial positioning
  const camera = new BABYLON.ArcRotateCamera(
    "cam",
    -Math.PI / 2,
    Math.PI / 3,
    2000,
    BABYLON.Vector3.Zero(),
    scene
  );
  camera.attachControl(canvas, true);
  camera.lowerRadiusLimit = 100;
  camera.upperRadiusLimit = 5000;
  
  // Set camera to human height initially
  camera.position = new BABYLON.Vector3(0, 1800, 2000);
  camera.setTarget(new BABYLON.Vector3(0, 0, 0));

  // Add some basic test objects if models fail to load
  const testSphere = BABYLON.MeshBuilder.CreateSphere("testSphere", {diameter: 100}, scene);
  testSphere.position = new BABYLON.Vector3(0, 500, 0);
  const sphereMat = new BABYLON.StandardMaterial("sphereMat", scene);
  sphereMat.diffuseColor = new BABYLON.Color3(1, 0, 0);
  testSphere.material = sphereMat;
  
  new BABYLON.PhysicsAggregate(
    testSphere,
    BABYLON.PhysicsShapeType.SPHERE,
    { mass: 1, restitution: 0.7 },
    scene
  );

  // Load models (with better error handling)
  const allMeshes: BABYLON.Mesh[] = [testSphere];
  
  try {
    const res = await fetch("/models.json");
    const modelPaths: string[] = await res.json();

    for (const path of modelPaths) {
      try {
        const result = await BABYLON.SceneLoader.ImportMeshAsync(
          "",
          "",
          path,
          scene
        );
        result.meshes.forEach((mesh, i) => {
          if (mesh instanceof BABYLON.Mesh && mesh.getTotalVertices() > 0) {
            allMeshes.push(mesh);
            if (i === 0) {
              mesh.position.y = 500;
              // Use simpler BOX shape for physics if mesh is complex
              const shapeType =
                mesh.getTotalVertices() > 100
                  ? BABYLON.PhysicsShapeType.BOX
                  : BABYLON.PhysicsShapeType.MESH;
              new BABYLON.PhysicsAggregate(
                mesh,
                shapeType,
                { mass: 1, restitution: 0.7 },
                scene
              );
            }
          }
        });
      } catch (error) {
        console.error(`Failed to load model ${path}:`, error);
      }
    }
  } catch (error) {
    console.warn("Failed to load models.json, using test objects only:", error);
  }

  // Frame camera around all objects
  if (allMeshes.length > 0) {
    const first = allMeshes[0].getBoundingInfo();
    let min = first.boundingBox.minimumWorld.clone();
    let max = first.boundingBox.maximumWorld.clone();
    let radius = first.boundingSphere.radiusWorld;

    for (let i = 1; i < allMeshes.length; i++) {
      const bounds = allMeshes[i].getBoundingInfo();
      min = BABYLON.Vector3.Minimize(min, bounds.boundingBox.minimumWorld);
      max = BABYLON.Vector3.Maximize(max, bounds.boundingBox.maximumWorld);
      radius = Math.max(radius, bounds.boundingSphere.radiusWorld);
    }

    const center = BABYLON.Vector3.Center(min, max);
    camera.setTarget(center);
    camera.radius = Math.max(radius * 2.5, 1000); // Ensure minimum distance
  }

  // WebXR setup with better error handling
  let xr;
  try {
    xr = await BABYLON.WebXRDefaultExperience.CreateAsync(scene, {
      floorMeshes: [ground],
      inputOptions: {
        doNotLoadControllerMeshes: false,
      },
    });
    console.log("WebXR initialized successfully");
  } catch (error) {
    console.error("WebXR initialization failed:", error);
    // Continue without WebXR
  }

  // Configure movement controls after XR session is initialized
  async function configureMovementControls() {
    if (!xr) return false;
    
    try {
      // Check if XR input is available
      if (!xr.baseExperience.input) {
        console.warn("XR input is not available yet");
        return false;
      }

      // Disable teleportation first
      const teleportation = xr.baseExperience.featuresManager.getEnabledFeature(
        BABYLON.WebXRFeatureName.TELEPORTATION
      );
      if (teleportation) {
        xr.baseExperience.featuresManager.disableFeature(
          BABYLON.WebXRFeatureName.TELEPORTATION
        );
      }

      // Enable movement feature
      const movement = (await xr.baseExperience.featuresManager.enableFeature(
        BABYLON.WebXRFeatureName.MOVEMENT,
        "latest",
        {
          xrInput: xr.baseExperience.input,
          locomotion: {
            movementOrientation: "gaze",
            movementSpeed: 1.0, // 1 meter per second
          },
        }
      )) as BABYLON.WebXRControllerMovement;

      if (movement) {
        movement.movementEnabled = true;
        movement.rotationEnabled = false;
        console.log("Movement feature enabled successfully");
        return true;
      } else {
        console.warn("Movement feature could not be enabled");
        return false;
      }
    } catch (error) {
      console.error("Failed to configure movement controls:", error);
      return false;
    }
  }

  // XR event handling
  if (xr) {
    // Wait for XR session to be ready before configuring movement
    xr.baseExperience.onStateChangedObservable.add((state) => {
      console.log("XR State changed:", state);
      if (state === BABYLON.WebXRState.IN_XR) {
        console.log("XR session is active, configuring movement...");
        // Add a small delay to ensure input is fully initialized
        setTimeout(() => {
          configureMovementControls();
        }, 100);
      }
    });

    // Alternative approach: listen for session initialization
    xr.baseExperience.sessionManager.onXRSessionInit.add(() => {
      console.log("XR session initialized");
      setTimeout(() => {
        configureMovementControls();
      }, 200);
    });
  }

  // Add fallback controls for development/desktop
  console.log("Adding fallback WASD controls");
  scene.actionManager = new BABYLON.ActionManager(scene);
  
  const keys: { [key: string]: boolean } = {};
  
  scene.actionManager.registerAction(new BABYLON.ExecuteCodeAction(
    BABYLON.ActionManager.OnKeyDownTrigger,
    (evt) => {
      keys[evt.sourceEvent.key.toLowerCase()] = true;
    }
  ));
  
  scene.actionManager.registerAction(new BABYLON.ExecuteCodeAction(
    BABYLON.ActionManager.OnKeyUpTrigger,
    (evt) => {
      keys[evt.sourceEvent.key.toLowerCase()] = false;
    }
  ));

  // Movement logic for fallback controls
  scene.onBeforeRenderObservable.add(() => {
    const speed = 50; // mm per frame
    const forward = camera.getDirection(BABYLON.Vector3.Forward());
    const right = camera.getDirection(BABYLON.Vector3.Right());
    
    if (keys['w']) camera.position.addInPlace(forward.scale(speed));
    if (keys['s']) camera.position.addInPlace(forward.scale(-speed));
    if (keys['a']) camera.position.addInPlace(right.scale(-speed));
    if (keys['d']) camera.position.addInPlace(right.scale(speed));
  });

  // Add render loop debugging
  let frameCount = 0;
  scene.onBeforeRenderObservable.add(() => {
    frameCount++;
    if (frameCount % 60 === 0) { // Log every 60 frames
      console.log("Scene is rendering, frame:", frameCount);
    }
  });

  return scene;
}

// Start scene with better error handling
createScene().then((_scene) => {
  scene = _scene;
  console.log("Scene created successfully, starting render loop");
  
  engine.runRenderLoop(() => {
    if (scene && scene.activeCamera) {
      scene.render();
    } else {
      console.warn("Scene or camera not available for rendering");
    }
  });
}).catch((error) => {
  console.error("Failed to create scene:", error);
  // Create a minimal fallback scene
  const fallbackScene = new BABYLON.Scene(engine);
  const fallbackCamera = new BABYLON.FreeCamera("fallbackCamera", new BABYLON.Vector3(0, 0, -10), fallbackScene);
  fallbackCamera.attachControl(canvas, true);
  
  const light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0, 1, 0), fallbackScene);
  const sphere = BABYLON.MeshBuilder.CreateSphere("sphere", {diameter: 2}, fallbackScene);
  
  engine.runRenderLoop(() => fallbackScene.render());
});

window.addEventListener("resize", () => engine.resize());