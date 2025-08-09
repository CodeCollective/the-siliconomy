// Show loading indicator
document.getElementById('loadingIndicator').style.display = 'block';

document.addEventListener('DOMContentLoaded', function () {
    // Your code here will execute when the DOM is ready
    console.log('DOM fully loaded and parsed');
    loadModels();
});

// Function to load models
function loadModels() {
    fetch('/models.json')
        .then(res => {
            if (!res.ok) {
                throw new Error('Models file not found');
            }
            return res.json();
        })
        .then(models => {
            // Ensure all paths are properly formatted
            models = models.map(path => {
                if (!path.startsWith('/') && !path.startsWith('http')) {
                    return `/${path}`;
                }
                return path;
            });
            return models;
        })
        .then(models => {
            const container = document.getElementById('model-container');
            let loadedCount = 0;

            if (!models || models.length === 0) {
                throw new Error('No models found');
            }

            models.forEach((path, index) => {
                const entity = document.createElement('a-entity');
                entity.setAttribute('gltf-model', path);
                entity.setAttribute('position', `0 0 0`);
                entity.setAttribute('scale', '0.001 0.001 0.001');
                entity.setAttribute('class', 'clickable');
                entity.setAttribute('grabbable', '');
                entity.setAttribute('dynamic-body', 'mass: 1');
                entity.setAttribute('rotation', '0 180 0');
                //entity.setAttribute('shadow', 'cast: true');

                // Add error handling for individual models
                entity.addEventListener('model-loaded', () => {
                    loadedCount++;
                    if (loadedCount === models.length) {
                        document.getElementById('loadingIndicator').style.display = 'none';
                    }
                });

                entity.addEventListener('model-error', () => {
                    console.warn(`Failed to load model: ${path}`);
                });

                container.appendChild(entity);
            });

            // Timeout fallback
            setTimeout(() => {
                if (loadedCount === 0) {
                    createFallbackObjects();
                    document.getElementById('loadingIndicator').style.display = 'none';
                }
            }, 5000);
        })
        .catch(error => {
            console.error('Error loading models:', error);
            createFallbackObjects();
            document.getElementById('loadingIndicator').style.display = 'none';
        });
}

// Wait for A-Frame to initialize
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadModels, 100);

    // Add VR session manager to scene
    document.querySelector('a-scene').setAttribute('vr-session-manager', '');
});

// Track active VR session
let activeVRSession = null;

// Handle VR enter/exit events
document.querySelector('a-scene').addEventListener('enter-vr', () => {
    console.log('Entered VR mode');

    // Get the XRSystem
    const scene = document.querySelector('a-scene');
    if (scene.xrSession) {
        activeVRSession = scene.xrSession;

        // Add session end handler
        activeVRSession.addEventListener('end', () => {
            console.log('VR session ended');
            activeVRSession = null;
        });

        // Add controller event listeners
        const controllers = scene.querySelectorAll('[hand-controls], [vive-controls], [oculus-touch-controls], [windows-motion-controls]');
        controllers.forEach(controller => {
            
            // Button events
            controller.addEventListener('buttondown', (e) => {
                console.log(`Button pressed: ${e.detail.id}`);
            });
            controller.addEventListener('buttonup', (e) => {
                console.log(`Button released: ${e.detail.id}`);
            });
            // Thumbstick events
            controller.addEventListener('axismove', (e) => {

                const hand = controller.getAttribute('hand') || controller.getAttribute('hand-controls');
                console.log(`Controller hand: ${hand}`); // 'left' or 'right'

                console.log('AXISMOVE EVENT DETAILS:', {
                    controller: controller.components,
                    event: e.detail,
                    axes: e.detail.axis,
                    changed: e.detail.changed
                });

                // Try different axis indices if needed
                const xAxis = e.detail.axis[0] || e.detail.axis[2] || 0;
                const yAxis = e.detail.axis[1] || e.detail.axis[3] || 0;

                if (xAxis !== 0 || yAxis !== 0) {
                    console.log(`Thumbstick moved: X=${xAxis.toFixed(2)}, Y=${yAxis.toFixed(2)}`);

                    // Get camera entity and its position
                    const cameraEl = document.querySelector('[simple-movement]');
                    if (!cameraEl) {
                        console.error('Could not find camera element with simple-movement component');
                        return;
                    }

                    const currentPos = cameraEl.getAttribute('position');
                    const rotation = cameraEl.getAttribute('rotation'); // {x, y, z}

                    // Convert yaw (rotation around Y-axis) to radians
                    const yaw = THREE.MathUtils.degToRad(rotation.y);

                    // Compute local forward and right vectors
                    const forward = new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw));
                    const right = new THREE.Vector3(-forward.z, 0, forward.x);

                    const moveSpeed = 0.01; // Adjust speed as needed
                    const moveVec = forward.multiplyScalar(yAxis * moveSpeed).add(
                        right.multiplyScalar(xAxis * moveSpeed)
                    );

                    const newPos = {
                        x: currentPos.x - moveVec.x,
                        y: currentPos.y,
                        z: currentPos.z - moveVec.z
                    };

                    const newPosStr = `${newPos.x} ${newPos.y} ${newPos.z}`;
                    cameraEl.setAttribute('position', newPosStr);

                    console.log(
                        'VR Movement - Axis:',
                        `X=${xAxis.toFixed(2)} Y=${yAxis.toFixed(2)}`,
                        'New Position:',
                        newPosStr
                    );
                }
            });

        });
    }
});

document.querySelector('a-scene').addEventListener('exit-vr', () => {
    console.log('Exited VR mode');

    // Clean up WebGL resources
    if (activeVRSession) {
        activeVRSession.end().catch(e => {
            console.warn('Error ending VR session:', e);
        });
        activeVRSession = null;
    }
});

// Prevent multiple VR sessions
AFRAME.registerComponent('vr-session-manager', {
    init: function () {
        this.el.addEventListener('enter-vr', (e) => {
            if (activeVRSession) {
                e.preventDefault();
                return false;
            }
        });
    }
});

// Custom component to handle simple movement
AFRAME.registerComponent('simple-movement', {
    init: function () {
        this.velocity = new THREE.Vector3();
        this.speed = 5;
        this.keys = {};

        // Key event listeners
        window.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
        });
    },

    tick: function (time, deltaTime) {
        const data = this.data;
        const el = this.el;
        const velocity = this.velocity;

        // Log keyboard movement
        if (this.keys['KeyW'] || this.keys['KeyS'] || this.keys['KeyA'] || this.keys['KeyD']) {
            console.log(`Keyboard movement: W=${this.keys['KeyW']}, S=${this.keys['KeyS']}, A=${this.keys['KeyA']}, D=${this.keys['KeyD']}`);
        }

        // Get camera direction
        const camera = el.querySelector('a-camera');
        if (!camera) return;

        const cameraEl = camera.object3D;
        const direction = new THREE.Vector3();
        cameraEl.getWorldDirection(direction);

        // Reset velocity
        velocity.set(0, 0, 0);

        // Movement based on WASD keys
        if (this.keys['KeyW']) {
            velocity.add(direction.multiplyScalar(this.speed * deltaTime / 1000));
        }
        if (this.keys['KeyS']) {
            velocity.add(direction.multiplyScalar(-this.speed * deltaTime / 1000));
        }
        if (this.keys['KeyA']) {
            const left = new THREE.Vector3();
            left.crossVectors(direction, cameraEl.up).normalize();
            velocity.add(left.multiplyScalar(-this.speed * deltaTime / 1000));
        }
        if (this.keys['KeyD']) {
            const right = new THREE.Vector3();
            right.crossVectors(direction, cameraEl.up).normalize();
            velocity.add(right.multiplyScalar(this.speed * deltaTime / 1000));
        }

        // Apply movement
        if (velocity.length() > 0) {
            const currentPosition = el.getAttribute('position');
            el.setAttribute('position', {
                x: currentPosition.x + velocity.x,
                y: currentPosition.y, // Keep Y fixed for ground movement
                z: currentPosition.z + velocity.z
            });
        }
    }
});
