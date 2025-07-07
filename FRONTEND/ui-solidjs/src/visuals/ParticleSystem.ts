// Advanced WebGL Particle System for Network Visualization
// Provides high-performance particle effects for data flows and animations

export interface ParticleSystemConfig {
  maxParticles: number;
  particleSize: number;
  particleLifetime: number;
  emissionRate: number;
  gravity: { x: number; y: number };
  velocityRange: { min: number; max: number };
  colorRange: { start: [number, number, number, number]; end: [number, number, number, number] };
  blendMode: 'normal' | 'additive' | 'multiply';
  textureUrl?: string;
}

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  color: [number, number, number, number];
  rotation: number;
  rotationSpeed: number;
}

export class WebGLParticleSystem {
  private gl: WebGL2RenderingContext;
  private canvas: HTMLCanvasElement;
  private program: WebGLProgram | null = null;
  private vertexBuffer: WebGLBuffer | null = null;
  private particles: Particle[] = [];
  private config: ParticleSystemConfig;
  private lastTime = 0;
  private emissionAccumulator = 0; // Used for continuous emission rate control
  private isRunning = false;
  
  // Shader sources
  private vertexShaderSource = `#version 300 es
    precision highp float;
    
    in vec2 a_position;
    in vec2 a_particlePosition;
    in float a_size;
    in vec4 a_color;
    in float a_rotation;
    
    uniform vec2 u_resolution;
    uniform mat4 u_viewMatrix;
    
    out vec4 v_color;
    out vec2 v_texCoord;
    
    void main() {
      // Rotate particle
      float cos_r = cos(a_rotation);
      float sin_r = sin(a_rotation);
      vec2 rotated = vec2(
        a_position.x * cos_r - a_position.y * sin_r,
        a_position.x * sin_r + a_position.y * cos_r
      );
      
      // Scale and translate
      vec2 position = a_particlePosition + rotated * a_size;
      
      // Convert to clip space
      vec2 clipSpace = ((position / u_resolution) * 2.0) - 1.0;
      clipSpace.y *= -1.0;
      
      gl_Position = vec4(clipSpace, 0.0, 1.0);
      v_color = a_color;
      v_texCoord = a_position * 0.5 + 0.5;
    }
  `;
  
  private fragmentShaderSource = `#version 300 es
    precision highp float;
    
    in vec4 v_color;
    in vec2 v_texCoord;
    
    uniform sampler2D u_texture;
    uniform bool u_useTexture;
    
    out vec4 fragColor;
    
    void main() {
      vec4 color = v_color;
      
      if (u_useTexture) {
        vec4 texColor = texture(u_texture, v_texCoord);
        color *= texColor;
      } else {
        // Default circular particle
        float dist = length(v_texCoord - 0.5);
        float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
        color.a *= alpha;
      }
      
      fragColor = color;
    }
  `;

  constructor(canvas: HTMLCanvasElement, config: Partial<ParticleSystemConfig> = {}) {
    this.canvas = canvas;
    
    const gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: false,
      antialias: true,
    });
    
    if (!gl) {
      throw new Error('WebGL2 not supported');
    }
    
    this.gl = gl;
    this.config = {
      maxParticles: 1000,
      particleSize: 4.0,
      particleLifetime: 3000,
      emissionRate: 50,
      gravity: { x: 0, y: 50 },
      velocityRange: { min: 20, max: 100 },
      colorRange: {
        start: [1.0, 1.0, 1.0, 1.0],
        end: [0.5, 0.5, 1.0, 0.0]
      },
      blendMode: 'additive',
      ...config
    };
    
    this.initialize();
  }

  private async initialize(): Promise<void> {
    const gl = this.gl;
    
    // Create shader program
    this.program = this.createShaderProgram();
    if (!this.program) {
      throw new Error('Failed to create shader program');
    }
    
    // Create vertex buffer
    this.vertexBuffer = gl.createBuffer();
    
    // Setup WebGL state
    gl.enable(gl.BLEND);
    this.setBlendMode(this.config.blendMode);
    
    // Create default texture if none provided
    if (!this.config.textureUrl) {
      this.createDefaultTexture();
    }
    
    // Initialize particle data
    this.particles = [];
    for (let i = 0; i < this.config.maxParticles; i++) {
      this.particles.push(this.createParticle());
    }
  }

  private createShaderProgram(): WebGLProgram | null {
    const gl = this.gl;
    
    const vertexShader = this.createShader(gl.VERTEX_SHADER, this.vertexShaderSource);
    const fragmentShader = this.createShader(gl.FRAGMENT_SHADER, this.fragmentShaderSource);
    
    if (!vertexShader || !fragmentShader) {
      return null;
    }
    
    const program = gl.createProgram();
    if (!program) return null;
    
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Shader program link error:', gl.getProgramInfoLog(program));
      gl.deleteProgram(program);
      return null;
    }
    
    return program;
  }

  private createShader(type: number, source: string): WebGLShader | null {
    const gl = this.gl;
    const shader = gl.createShader(type);
    if (!shader) return null;
    
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    
    return shader;
  }

  private createDefaultTexture(): void {
    const gl = this.gl;
    const texture = gl.createTexture();
    
    // Create a simple white circle texture
    const size = 32;
    const data = new Uint8Array(size * size * 4);
    const center = size / 2;
    
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const dx = x - center;
        const dy = y - center;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const alpha = Math.max(0, 1 - (distance / center));
        
        const index = (y * size + x) * 4;
        data[index] = 255;     // R
        data[index + 1] = 255; // G
        data[index + 2] = 255; // B
        data[index + 3] = Math.floor(alpha * 255); // A
      }
    }
    
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, size, size, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  }

  private setBlendMode(mode: string): void {
    const gl = this.gl;
    
    switch (mode) {
      case 'additive':
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
        break;
      case 'multiply':
        gl.blendFunc(gl.DST_COLOR, gl.ZERO);
        break;
      case 'normal':
      default:
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        break;
    }
  }

  private createParticle(): Particle {
    return {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      life: 0,
      maxLife: this.config.particleLifetime,
      size: this.config.particleSize,
      color: [...this.config.colorRange.start] as [number, number, number, number],
      rotation: 0,
      rotationSpeed: (Math.random() - 0.5) * 0.02,
    };
  }

  public emit(x: number, y: number, count = 1): void {
    for (let i = 0; i < count; i++) {
      const particle = this.findDeadParticle();
      if (!particle) break;
      
      this.resetParticle(particle, x, y);
    }
  }

  public emitFlow(startX: number, startY: number, endX: number, endY: number, particleCount = 10): void {
    for (let i = 0; i < particleCount; i++) {
      const t = i / (particleCount - 1);
      const x = startX + (endX - startX) * t;
      const y = startY + (endY - startY) * t;
      
      setTimeout(() => {
        this.emit(x, y, 1);
      }, i * 100); // Stagger emission
    }
  }

  private findDeadParticle(): Particle | null {
    return this.particles.find(p => p.life <= 0) || null;
  }

  private resetParticle(particle: Particle, x: number, y: number): void {
    const angle = Math.random() * Math.PI * 2;
    const speed = this.config.velocityRange.min + 
                  Math.random() * (this.config.velocityRange.max - this.config.velocityRange.min);
    
    particle.x = x;
    particle.y = y;
    particle.vx = Math.cos(angle) * speed;
    particle.vy = Math.sin(angle) * speed;
    particle.life = particle.maxLife;
    particle.rotation = Math.random() * Math.PI * 2;
    particle.rotationSpeed = (Math.random() - 0.5) * 0.02;
    particle.color = [...this.config.colorRange.start] as [number, number, number, number];
  }

  public update(deltaTime: number): void {
    const dt = deltaTime / 1000; // Convert to seconds
    
    this.particles.forEach(particle => {
      if (particle.life <= 0) return;
      
      // Update physics
      particle.vx += this.config.gravity.x * dt;
      particle.vy += this.config.gravity.y * dt;
      particle.x += particle.vx * dt;
      particle.y += particle.vy * dt;
      particle.rotation += particle.rotationSpeed;
      
      // Update life
      particle.life -= deltaTime;
      
      // Interpolate color
      const t = 1 - (particle.life / particle.maxLife);
      const startColor = this.config.colorRange.start;
      const endColor = this.config.colorRange.end;
      for (let i = 0; i < 4; i++) {
        const startValue = startColor[i] ?? 1.0;
        const endValue = endColor[i] ?? 0.0;
        particle.color[i] = startValue + (endValue - startValue) * t;
      }
    });
  }

  public render(): void {
    const gl = this.gl;
    if (!this.program) return;
    
    // Resize canvas if needed
    if (this.canvas.width !== this.canvas.clientWidth || 
        this.canvas.height !== this.canvas.clientHeight) {
      this.canvas.width = this.canvas.clientWidth;
      this.canvas.height = this.canvas.clientHeight;
      gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    }
    
    gl.useProgram(this.program);
    
    // Create vertex data for all alive particles
    const aliveParticles = this.particles.filter(p => p.life > 0);
    if (aliveParticles.length === 0) return;
    
    const verticesPerParticle = 6; // Two triangles
    const attributesPerVertex = 9; // x, y, px, py, size, r, g, b, a, rotation
    const vertexData = new Float32Array(aliveParticles.length * verticesPerParticle * attributesPerVertex);
    
    aliveParticles.forEach((particle, index) => {
      const baseIndex = index * verticesPerParticle * attributesPerVertex;
      
      // Quad vertices (two triangles)
      const vertices = [
        -1, -1,  // Triangle 1
         1, -1,
        -1,  1,
        -1,  1,  // Triangle 2
         1, -1,
         1,  1,
      ];
      
      for (let v = 0; v < verticesPerParticle; v++) {
        const vIndex = baseIndex + v * attributesPerVertex;
        
        vertexData[vIndex] = vertices[v * 2] ?? 0;     // x
        vertexData[vIndex + 1] = vertices[v * 2 + 1] ?? 0; // y
        vertexData[vIndex + 2] = particle.x;     // px
        vertexData[vIndex + 3] = particle.y;     // py
        vertexData[vIndex + 4] = particle.size;  // size
        vertexData[vIndex + 5] = particle.color[0]; // r
        vertexData[vIndex + 6] = particle.color[1]; // g
        vertexData[vIndex + 7] = particle.color[2]; // b
        vertexData[vIndex + 8] = particle.color[3]; // a
      }
    });
    
    // Upload vertex data
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.DYNAMIC_DRAW);
    
    // Setup attributes
    const stride = attributesPerVertex * 4; // 4 bytes per float
    const positionLocation = gl.getAttribLocation(this.program, 'a_position');
    const particlePosLocation = gl.getAttribLocation(this.program, 'a_particlePosition');
    const sizeLocation = gl.getAttribLocation(this.program, 'a_size');
    const colorLocation = gl.getAttribLocation(this.program, 'a_color');
    
    gl.enableVertexAttribArray(positionLocation);
    gl.enableVertexAttribArray(particlePosLocation);
    gl.enableVertexAttribArray(sizeLocation);
    gl.enableVertexAttribArray(colorLocation);
    
    gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, stride, 0);
    gl.vertexAttribPointer(particlePosLocation, 2, gl.FLOAT, false, stride, 8);
    gl.vertexAttribPointer(sizeLocation, 1, gl.FLOAT, false, stride, 16);
    gl.vertexAttribPointer(colorLocation, 4, gl.FLOAT, false, stride, 20);
    
    // Set uniforms
    const resolutionLocation = gl.getUniformLocation(this.program, 'u_resolution');
    gl.uniform2f(resolutionLocation, this.canvas.width, this.canvas.height);
    
    // Draw particles
    gl.drawArrays(gl.TRIANGLES, 0, aliveParticles.length * verticesPerParticle);
  }

  public start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.lastTime = performance.now();
    this.renderLoop();
  }

  public stop(): void {
    this.isRunning = false;
  }

  private renderLoop = (): void => {
    if (!this.isRunning) return;
    
    const currentTime = performance.now();
    const deltaTime = currentTime - this.lastTime;
    this.lastTime = currentTime;
    
    this.update(deltaTime);
    this.render();
    
    requestAnimationFrame(this.renderLoop);
  };

  public updateConfig(newConfig: Partial<ParticleSystemConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (newConfig.blendMode) {
      this.setBlendMode(newConfig.blendMode);
    }
  }

  public getAliveParticleCount(): number {
    return this.particles.filter(p => p.life > 0).length;
  }

  public clear(): void {
    this.particles.forEach(particle => {
      particle.life = 0;
    });
  }

  public dispose(): void {
    this.stop();
    
    if (this.gl && this.program) {
      this.gl.deleteProgram(this.program);
    }
    
    if (this.gl && this.vertexBuffer) {
      this.gl.deleteBuffer(this.vertexBuffer);
    }
  }
}
