// Full-screen triangle. The fragment shader does all the work: it rebuilds a
// world-space ray per pixel from the real camera and bends it around the hole.
varying vec2 vNdc;

void main() {
  vNdc = position.xy;
  gl_Position = vec4(position.xy, 1.0, 1.0);
}
