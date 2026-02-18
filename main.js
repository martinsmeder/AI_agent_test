import * as THREE from "./node_modules/three/build/three.module.js";

const app = document.getElementById("app");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87b7ff);

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(10, 8, 10);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
app.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const sunLight = new THREE.DirectionalLight(0xffffff, 1.1);
sunLight.position.set(5, 12, 8);
scene.add(sunLight);

const platformGeometry = new THREE.BoxGeometry(20, 1, 20);
const platformMaterial = new THREE.MeshLambertMaterial({ color: 0x2ea043 });
const platform = new THREE.Mesh(platformGeometry, platformMaterial);
platform.position.y = -0.5;
scene.add(platform);

const grid = new THREE.GridHelper(20, 20, 0x1f6f2d, 0x2a8f3e);
grid.position.y = 0.01;
scene.add(grid);

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

window.addEventListener("resize", onWindowResize);

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

animate();
