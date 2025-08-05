
// Show loading indicator
document.getElementById('loadingIndicator').style.display = 'block';

// Function to create fallback objects
function createFallbackObjects() {
    console.log('Using fallback objects instead of models');
    document.getElementById('fallback-objects').setAttribute('visible', 'true');
}

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
            const container = document.getElementById('model-container');
            let loadedCount = 0;

            if (!models || models.length === 0) {
                throw new Error('No models found');
            }

            models.forEach((path, index) => {
                const entity = document.createElement('a-entity');
                entity.setAttribute('gltf-model', path);
                entity.setAttribute('position', `${(index - Math.floor(models.length / 2)) * 2} 1 -3`);
                entity.setAttribute('scale', '0.001 0.001 0.001');
                entity.setAttribute('class', 'clickable');
                entity.setAttribute('grabbable', '');
                entity.setAttribute('dynamic-body', 'mass: 1');
                entity.setAttribute('rotation', '0 180 0');
                entity.setAttribute('shadow', 'cast: true');

                // Add error handling for individual models
                entity.addEventListener('model-loaded', () => {
                    loadedCount++;
                    if (loadedCount === models.length) {
                        document.getElementById('loadingIndicator').style.display = 'none';
                    }
                });

                entity.addEventListener('model-error', () => {
                    console.warn(`Failed to load model: ${path}`);
                    // Create a fallback box for this model
                    const fallback = document.createElement('a-box');
                    fallback.setAttribute('position', entity.getAttribute('position'));
                    fallback.setAttribute('class', 'clickable');
                    fallback.setAttribute('grabbable', '');
                    fallback.setAttribute('dynamic-body', 'mass: 1');
                    fallback.setAttribute('color', '#FF6B6B');
                    fallback.setAttribute('width', '1');
                    fallback.setAttribute('height', '1');
                    fallback.setAttribute('depth', '1');
                    container.appendChild(fallback);
                    entity.remove();
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
});

// Handle VR enter/exit events
document.querySelector('a-scene').addEventListener('enter-vr', () => {
    console.log('Entered VR mode');
});

document.querySelector('a-scene').addEventListener('exit-vr', () => {
    console.log('Exited VR mode');
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