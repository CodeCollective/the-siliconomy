export const sceneConfig = {
  scene: {
    clearColor: [0.05, 0.05, 0.05]
  },
  ground: {
    width: 10,
    height: 10,
    positionY: -1,
    receiveShadows: true
  },
  box: {
    size: 0.5,
    positionY: 0,
    diffuseColor: [0.2, 0.7, 1.0],
    emissiveColor: [0.5, 0.5, 0.5]
  },
  camera: {
    alpha: -Math.PI / 2,
    beta: Math.PI / 2,
    radius: 5,
    upperBetaLimit: Math.PI / 2,
    lowerRadiusLimit: 2,
    upperRadiusLimit: 10
  },
  lights: [
    {
      type: "hemispheric",
      name: "ambientLight",
      direction: [0, 1, 0]
    },
    {
      type: "directional",
      name: "mainLight",
      direction: [0, -1, 1],
      intensity: 1.0
    }
  ],
  materials: {
    box: {
      name: "boxMaterial",
      emissiveColor: [0, 0, 0] // Default, changes when grabbed
    }
  },
  models: [
    {
      name: "laserCutter",
      path: "/assets/output/",
      file: "laser_cutter.glb",
      position: [0, 0, 0],
      scaling: [1, 1, 1],
      rotation: [0, 0, 0]
    }
  ]
};
