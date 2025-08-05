document.addEventListener('DOMContentLoaded', async function () {
    const canvas = document.getElementById("renderCanvas");
    const loading = document.getElementById("loading");
    const errorDisplay = document.getElementById("error");

    function showError(message) {
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
        console.error(message);
    }

    try {
        // Initialize engine
        const engine = new BABYLON.Engine(canvas, true);

        // Create basic scene
        loading.textContent = "Creating scene...";
        const scene = new BABYLON.Scene(engine);
        scene.clearColor = new BABYLON.Color3(0.1, 0.1, 0.1);

        // Skybox
        // Create skybox
        /*
        const skybox = BABYLON.MeshBuilder.CreateBox("skyBox", { size: 100000 }, scene);

        // Create skybox material
        const skyboxMaterial = new BABYLON.StandardMaterial("skyBoxMaterial", scene);
        skyboxMaterial.backFaceCulling = false; // render inside of cube
        skyboxMaterial.disableLighting = true;  // prevent scene lighting from affecting it

        // Load cubemap
        skyboxMaterial.reflectionTexture = new BABYLON.CubeTexture("/assets/skybox/skybox", scene);
        skyboxMaterial.reflectionTexture.coordinatesMode = BABYLON.Texture.SKYBOX_MODE;

        // Apply material
        skybox.material = skyboxMaterial;

        // Optional: prevent skybox from casting shadows
        skybox.isPickable = false;
        skybox.infiniteDistance = true;*/

        const camera = new BABYLON.FreeCamera("camera", new BABYLON.Vector3(0, 2000, -3000), scene);
        camera.setTarget(BABYLON.Vector3.Zero());
        camera.attachControl(canvas, true);

        camera.maxZ = 100000; // or however far you want to render

        // WASD Navigation Setup
        const keys = {};
        scene.actionManager = new BABYLON.ActionManager(scene);

        // Register key events
        scene.actionManager.registerAction(
            new BABYLON.ExecuteCodeAction(
                BABYLON.ActionManager.OnKeyDownTrigger,
                function (evt) {
                    const key = evt.sourceEvent.key.toLowerCase();
                    if (!keys[key]) {
                        console.log(`Key pressed: ${key}`);
                    }
                    keys[key] = true;
                }
            )
        );
        scene.actionManager.registerAction(
            new BABYLON.ExecuteCodeAction(
                BABYLON.ActionManager.OnKeyUpTrigger,
                function (evt) {
                    keys[evt.sourceEvent.key.toLowerCase()] = false;
                }
            )
        );

        // Movement parameters
        const moveSpeed = 200; // Adjust this value to change movement speed
        const moveVector = new BABYLON.Vector3();
        const tmpVector = new BABYLON.Vector3();

        // Add to scene's before render
        scene.registerBeforeRender(function () {
            // Reset movement vector
            moveVector.set(0, 0, 0);

            // Get camera forward and right vectors
            const forward = camera.getForwardRay().direction.normalize();
            const right = camera.getDirection(BABYLON.Axis.X).normalize();
            const up = camera.upVector;

            // Handle movement keys
            if (keys['w'] || keys['arrowup']) {
                moveVector.addInPlace(forward);
            }
            if (keys['s'] || keys['arrowdown']) {
                moveVector.addInPlace(forward.scale(-1));
            }
            if (keys['a'] || keys['arrowleft']) {
                moveVector.addInPlace(right.scale(-1));
            }
            if (keys['d'] || keys['arrowright']) {
                moveVector.addInPlace(right);
            }
            // Vertical movement
            if (keys['q']) { // q for up
                moveVector.addInPlace(up);
            }
            if (keys['e']) { // e for down
                moveVector.addInPlace(up.scale(-1));
            }

            // Normalize and scale by speed if there's any movement
            if (moveVector.lengthSquared() > 0) {
                const currentSpeed = keys['shift'] ? moveSpeed * 10 : moveSpeed;
                moveVector.normalize().scaleInPlace(currentSpeed * engine.getDeltaTime() / 1000);

                // Apply movement to both camera position and target
                camera.position.addInPlace(moveVector);
                camera.target.addInPlace(moveVector);
            }
        });
        camera.wheelPrecision = 0.2; // Increased zoom rate

        envTex = new BABYLON.CubeTexture("/assets/skybox/skybox", scene);
        scene.environmentTexture = envTex; // Applies to all PBR materials

        // Lighting
        const light2 = new BABYLON.DirectionalLight("light2", new BABYLON.Vector3(0, -1, 1), scene);
        light2.intensity = 1.5;
        const ambientLight = new BABYLON.HemisphericLight("ambient", new BABYLON.Vector3(0, 1, 0), scene);
        ambientLight.intensity = 1;

        // Try to load models.json
        loading.textContent = "Loading model list...";
        let models = [];

        try {
            const response = await fetch('/models.json');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            models = await response.json();

            if (!Array.isArray(models)) {
                throw new Error("models.json should contain an array of paths");
            }
        } catch (e) {
            showError(`Couldn't load models.json, using fallback models. Error: ${e.message}`);
        }

        // Create model selection buttons
        loading.textContent = "Creating model menu...";
        const modelList = document.getElementById('modelList');
        const primitiveList = document.getElementById('primitiveList');
        const toggleMenu = document.getElementById('toggleMenu');
        let currentModel = null;
        function centerCameraOnMeshes(meshes) {
            if (!meshes || meshes.length === 0) return;

            const boundingInfo = BABYLON.Mesh.MergeMeshes(
                meshes.filter(m => m !== currentModel && m.getTotalVertices() > 0),
                true, true, undefined, false, true
            )?.getBoundingInfo();

            if (!boundingInfo) return;

            const center = boundingInfo.boundingBox.centerWorld;
            const extendSize = boundingInfo.boundingBox.extendSizeWorld;
            const diagonal = extendSize.length();

            // Move camera to be behind and above the object
            camera.setTarget(center);
            camera.position = center.add(new BABYLON.Vector3(0, diagonal * 1.5, -diagonal * 2));
        }

        let currentPrimitives = [];

        // Load saved model if exists
        const savedModel = localStorage.getItem('selectedModel');
        const savedCamera = localStorage.getItem('cameraState');

        // Toggle menu visibility
        toggleMenu.addEventListener('click', () => {
            document.querySelector('.menu-container').classList.toggle('visible');
        });

        // Create buttons for each model
        let modelButtons = [];
        models.forEach((modelUrl, index) => {
            const btn = document.createElement('button');
            btn.className = 'model-btn';

            // Extract model name from URL
            const url = new URL(modelUrl, window.location.href);
            const fileName = url.pathname.split('/').pop();
            btn.textContent = fileName.replace('.glb', '').replace(/_/g, ' ');
            btn.dataset.url = modelUrl;

            modelButtons.push(btn);

            btn.addEventListener('click', async () => {
                loading.textContent = `Loading ${fileName}...`;
                loading.style.display = 'block';

                try {
                    // Remove previous model if exists
                    if (currentModel) {
                        currentModel.dispose();
                    }

                    // Load new model
                    const pathParts = url.pathname.split('/');
                    const path = pathParts.slice(0, -1).join('/') + '/';

                    const meshes = await BABYLON.SceneLoader.ImportMeshAsync(
                        null,
                        path,
                        fileName,
                        scene
                    ).then(result => result.meshes);

                    currentModel = meshes[0];
                    currentModel.name = `model_${index}`;
                    currentModel.position = BABYLON.Vector3.Zero();

                    // Clear previous primitives
                    primitiveList.innerHTML = '';
                    currentPrimitives = [];

                    // Add show/hide all buttons
                    const controlsDiv = document.createElement('div');
                    controlsDiv.className = 'primitive-controls';

                    const checkboxes = [];

                    const showAllBtn = document.createElement('button');
                    showAllBtn.textContent = 'Show All';
                    showAllBtn.className = 'primitive-control-btn';
                    showAllBtn.addEventListener('click', () => {
                        meshes.forEach((m, idx) => {
                            if (idx > 0) {
                                m.isVisible = true;
                                checkboxes[idx - 1].checked = true;
                            }
                        });
                    });

                    const hideAllBtn = document.createElement('button');
                    hideAllBtn.textContent = 'Hide All';
                    hideAllBtn.className = 'primitive-control-btn';
                    hideAllBtn.addEventListener('click', () => {
                        meshes.forEach((m, idx) => {
                            if (idx > 0) {
                                m.isVisible = false;
                                checkboxes[idx - 1].checked = false;
                            }
                        });
                    });

                    controlsDiv.appendChild(showAllBtn);
                    controlsDiv.appendChild(hideAllBtn);
                    primitiveList.appendChild(controlsDiv);

                    // Collect and sort primitives
                    const primitives = [];
                    meshes.forEach((mesh, i) => {
                        if (i === 0) return; // Skip root mesh
                        primitives.push({
                            mesh,
                            index: i,
                            name: mesh.name || `Primitive ${i}`
                        });
                    });

                    // Sort alphabetically by name
                    primitives.sort((a, b) => a.name.localeCompare(b.name));

                    // Restore primitive visibility by name
                    const pendingPrimitiveStates = localStorage.getItem('pendingPrimitiveStates');
                    let primitiveStates = {};
                    if (pendingPrimitiveStates) {
                        try {
                            primitiveStates = JSON.parse(pendingPrimitiveStates);
                            localStorage.removeItem('pendingPrimitiveStates');
                        } catch (e) {
                            console.error('Failed to parse pending primitive states:', e);
                        }
                    }

                    // Add sorted primitives to list
                    primitives.forEach(({ mesh, index, name }) => {
                        const primitiveItem = document.createElement('div');
                        primitiveItem.className = 'primitive-item';

                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        // Match by name, default to true if not found
                        const isVisible = name in primitiveStates ? primitiveStates[name] : true;
                        checkbox.checked = isVisible;
                        mesh.isVisible = isVisible;
                        checkbox.className = 'primitive-checkbox';
                        checkboxes.push(checkbox);

                        const label = document.createElement('span');
                        label.textContent = name;
                        label.className = 'primitive-label';

                        checkbox.addEventListener('change', () => {
                            mesh.isVisible = checkbox.checked;
                            mesh.renderOutline = checkbox.checked;
                        });

                        label.addEventListener('click', () => {
                            // Highlight selected primitive
                            meshes.forEach(m => m.renderOutline = false);
                            mesh.renderOutline = true;
                            mesh.outlineWidth = 0.1;
                            mesh.outlineColor = new BABYLON.Color3(1, 0.5, 0);
                        });

                        primitiveItem.appendChild(checkbox);
                        primitiveItem.appendChild(label);
                        primitiveList.appendChild(primitiveItem);
                        currentPrimitives.push(mesh);
                    });

                    // Save selected model
                    localStorage.setItem('selectedModel', modelUrl);

                    // Restore camera state if pending from reload
                    const pendingCameraState = localStorage.getItem('pendingCameraState');
                    if (pendingCameraState) {
                        try {
                            loadCameraState(JSON.parse(pendingCameraState));
                            localStorage.removeItem('pendingCameraState');
                        } catch (e) {
                            console.error('Failed to restore pending camera state:', e);
                        }
                    }

                    // Set up file change detection
                    let lastModified = null;
                    const checkForChanges = async () => {
                        try {
                            const response = await fetch(modelUrl, { method: 'HEAD' });
                            const currentModified = response.headers.get('last-modified');

                            if (lastModified && currentModified !== lastModified) {
                                console.log('Model file changed, reloading...');
                                // Save current camera state and primitive visibility before reloading
                                const cameraState = saveCameraState();
                                const primitiveStates = {};
                                meshes.forEach((m, idx) => {
                                    if (idx > 0) {
                                        primitiveStates[m.name || `Primitive ${idx}`] = m.isVisible;
                                    }
                                });
                                localStorage.setItem('pendingCameraState', JSON.stringify(cameraState));
                                localStorage.setItem('pendingPrimitiveStates', JSON.stringify(primitiveStates));
                                btn.click(); // Trigger reload
                            }
                            lastModified = currentModified;
                        } catch (e) {
                            console.error('Error checking file changes:', e);
                        }
                    };

                    // Check every 1 seconds
                    const changeCheckInterval = setInterval(checkForChanges, 1000);
                    checkForChanges(); // Initial check

                    // Clean up interval when loading new model
                    btn.addEventListener('click', () => {
                        clearInterval(changeCheckInterval);
                    }, { once: true });

                    loading.style.display = 'none';

                    // Auto-click first model button if no saved model
                    if (!savedModel && index === 0) {
                        btn.click();
                    }
                } catch (e) {
                    showError(`Failed to load ${fileName}: ${e.message}`);
                    loading.style.display = 'none';
                }
            });

            modelList.appendChild(btn);
        });

        loading.style.display = 'none';

        // Load saved model if exists
        if (savedModel) {
            const savedBtn = modelButtons.find(btn => btn.dataset.url === savedModel);
            if (savedBtn) {
                savedBtn.click();
            }
        } else if (modelButtons.length > 0) {
            // Default to first model if no saved model
            modelButtons[0].click();
        }

        // Camera state auto-saving
        let lastCameraState = null;
        scene.onBeforeRenderObservable.add(() => {
            const currentState = saveCameraState();

            // Only save if state actually changed
            if (!lastCameraState ||
                lastCameraState.alpha !== currentState.alpha ||
                lastCameraState.beta !== currentState.beta ||
                lastCameraState.radius !== currentState.radius ||
                lastCameraState.target.x !== currentState.target.x ||
                lastCameraState.target.y !== currentState.target.y ||
                lastCameraState.target.z !== currentState.target.z) {

                localStorage.setItem('cameraState', JSON.stringify(currentState));
                lastCameraState = currentState;
            }
        });

        // Camera state management functions
        function saveCameraState() {
            return {
                alpha: camera.alpha,
                beta: camera.beta,
                radius: camera.radius,
                position: {
                    x: camera.position.x,
                    y: camera.position.y,
                    z: camera.position.z
                },
                target: {
                    x: camera.target.x,
                    y: camera.target.y,
                    z: camera.target.z
                }
            };
        }

        function loadCameraState(state) {
            camera.alpha = state.alpha;
            camera.beta = state.beta;
            camera.radius = state.radius;
            if (state.position) {
                camera.position = new BABYLON.Vector3(
                    state.position.x || 0,
                    state.position.y || 0,
                    state.position.z || 0
                );
            }
            if (state.target) {
                camera.target = new BABYLON.Vector3(
                    state.target.x || 0,
                    state.target.y || 0,
                    state.target.z || 0
                );
            }
        }

        // Load saved camera if exists
        if (savedCamera) {
            try {
                loadCameraState(JSON.parse(savedCamera));
            } catch (e) {
                console.error('Failed to load camera state:', e);
            }
        }

        // Handle window resize
        window.addEventListener('resize', function () {
            if (currentModel) {
                const bounds = scene.getWorldExtends();
                const diagonal = bounds.max.subtract(bounds.min).length();
                camera.radius = diagonal * 1.5;
                engine.resize();
            }
        });

        // Run render loop
        engine.runRenderLoop(function () {
            scene.render();
        });

        document.getElementById('centerButton').addEventListener('click', () => {
            if (currentModel && currentPrimitives.length > 0) {
                centerCameraOnMeshes([currentModel, ...currentPrimitives]);
            }
        });


    } catch (e) {
        showError(`Fatal error: ${e.message}`);
        loading.textContent = "Failed to initialize. See error message.";
    }
});
