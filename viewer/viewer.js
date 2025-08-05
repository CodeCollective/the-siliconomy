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

        // Camera
        const camera = new BABYLON.ArcRotateCamera(
            "camera",
            -Math.PI / 2,
            Math.PI / 4,
            10,
            BABYLON.Vector3.Zero(),
            scene
        );
        camera.attachControl(canvas, true);
        camera.wheelPrecision = 0.2; // Increased zoom rate

        // Lighting
        const light1 = new BABYLON.HemisphericLight("light1", new BABYLON.Vector3(0, 1, 0), scene);
        const light2 = new BABYLON.DirectionalLight("light2", new BABYLON.Vector3(0, -1, 1), scene);
        light2.intensity = 0.5;
        const ambientLight = new BABYLON.HemisphericLight("ambient", new BABYLON.Vector3(0, 1, 0), scene);
        ambientLight.intensity = 1;

        // Ground
        const ground = BABYLON.MeshBuilder.CreateGround("ground", { width: 2000, height: 2000, color: "green" }, scene);
        ground.position.y = 0;
        ground.color = "green"

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
                                checkboxes[idx-1].checked = true;
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
                                checkboxes[idx-1].checked = false;
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
                    primitives.forEach(({mesh, index, name}) => {
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

                    // Fit camera to model
                    const bounds = scene.getWorldExtends();
                    const diagonal = bounds.max.subtract(bounds.min).length();
                    camera.radius = diagonal * 1.5;

                    // Save selected model
                    localStorage.setItem('selectedModel', modelUrl);

                    // Restore camera state if pending from reload
                    const pendingCameraState = localStorage.getItem('pendingCameraState');
                    if (pendingCameraState) {
                        try {
                            const state = JSON.parse(pendingCameraState);
                            camera.alpha = state.alpha;
                            camera.beta = state.beta;
                            camera.radius = state.radius;
                            camera.target = new BABYLON.Vector3(
                                state.target.x || 0,
                                state.target.y || 0,
                                state.target.z || 0
                            );
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
                                const cameraState = {
                                    alpha: camera.alpha,
                                    beta: camera.beta,
                                    radius: camera.radius,
                                    target: {
                                        x: camera.target.x,
                                        y: camera.target.y,
                                        z: camera.target.z
                                    }
                                };
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

        // Improved camera state saving (replace the existing save section):
        let lastCameraState = null;
        scene.onBeforeRenderObservable.add(() => {
            const currentState = {
                alpha: camera.alpha,
                beta: camera.beta,
                radius: camera.radius,
                target: {
                    x: camera.target.x,
                    y: camera.target.y,
                    z: camera.target.z
                }
            };

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

        // Load saved camera if exists
        if (savedCamera) {
            try {
                const cameraState = JSON.parse(savedCamera);
                camera.alpha = cameraState.alpha;
                camera.beta = cameraState.beta;
                camera.radius = cameraState.radius;

                // Convert the plain object back to Vector3
                if (cameraState.target) {
                    camera.target = new BABYLON.Vector3(
                        cameraState.target.x || 0,
                        cameraState.target.y || 0,
                        cameraState.target.z || 0
                    );
                }
            } catch (e) {
                console.error('Failed to load camera state:', e);
            }
        }

        // Handle window resize
        window.addEventListener('resize', function() {
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

    } catch (e) {
        showError(`Fatal error: ${e.message}`);
        loading.textContent = "Failed to initialize. See error message.";
    }
});
