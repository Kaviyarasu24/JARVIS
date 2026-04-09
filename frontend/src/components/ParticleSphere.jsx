import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import '../styles/particles.css'

/* ── Circular particle texture ───────────────────────────────────────────── */
function createParticleTexture() {
  const size = 64
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')

  // Create a highly luminous core with a vibrant blue aura
  const gradient = ctx.createRadialGradient(
    size / 2, size / 2, 0,
    size / 2, size / 2, size / 2
  )
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1)') // Pure white core
  gradient.addColorStop(0.15, 'rgba(180, 220, 255, 0.9)') // Bright inner ring
  gradient.addColorStop(0.4, 'rgba(60, 130, 255, 0.6)') // Vibrant blue mid
  gradient.addColorStop(1, 'rgba(20, 50, 255, 0)') // Fading edge

  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, size, size)

  const texture = new THREE.CanvasTexture(canvas)
  texture.needsUpdate = true
  return texture
}

/* ── Speed/scale params per state ──────────────────────────────────────── */
const STATE_PARAMS = {
  standby:    { wobble: 0.08, scale: 1.0,  brightness: 1.0,  pointSize: 0.06 },
  listening:  { wobble: 0.12, scale: 0.95, brightness: 1.15, pointSize: 0.07 },
  processing: { wobble: 0.25, scale: 1.1,  brightness: 1.2,  pointSize: 0.08 },
  speaking:   { wobble: 0.20, scale: 1.05, brightness: 1.2,  pointSize: 0.09 },
}

/* ── Particles component ─────────────────────────────────────────────────── */
function Particles({ agentState }) {
  const pointsRef = useRef()
  const count = 6000

  // Lerped params
  const params = useRef({ wobble: STATE_PARAMS.standby.wobble, scale: STATE_PARAMS.standby.scale, brightness: STATE_PARAMS.standby.brightness, pointSize: STATE_PARAMS.standby.pointSize })

  const [basePositions, offsets, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3)
    const off = new Float32Array(count)
    const sizeArr = new Float32Array(count)

    for (let i = 0; i < count; i++) {
      // Random distribution on a thick spherical shell
      const u = Math.random()
      const v = Math.random()
      const theta = u * 2.0 * Math.PI
      const phi = Math.acos(2.0 * v - 1.0)
      
      // Radius variation to create the "dense structural" look
      let r = 1.9 + (Math.random() * 0.25 - 0.125)
      if (Math.random() > 0.85) {
        r = Math.cbrt(Math.random()) * 1.8
      }

      pos[i * 3]     = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)

      off[i] = Math.random() * Math.PI * 2
      sizeArr[i] = 0.5 + Math.random() * 0.8
    }
    return [pos, off, sizeArr]
  }, [])

  const positions = useMemo(() => new Float32Array(count * 3), [])
  const texture = useMemo(() => createParticleTexture(), [])

  // For smooth mouse parallax
  const mouseEased = useRef({ x: 0, y: 0 })

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    const target = STATE_PARAMS[agentState] || STATE_PARAMS.standby
    const p = params.current
    const lerp = 0.04

    // Smooth lerp towards target state
    p.wobble      += (target.wobble - p.wobble) * lerp
    p.scale       += (target.scale - p.scale) * lerp
    p.brightness  += (target.brightness - p.brightness) * lerp
    p.pointSize   += (target.pointSize - p.pointSize) * lerp

    // Global rhythmic expansion breathing cycle
    const globalBreath = Math.sin(t * 1.5) * 0.03
    let speakPulse = 0
    if (agentState === 'speaking') {
      speakPulse = Math.sin(t * 4) * 0.04 + Math.sin(t * 8) * 0.02
    }

    const currentScale = p.scale + globalBreath + speakPulse

    // Update particle positions with individual point inflow/outflow
    for (let i = 0; i < count; i++) {
      const bx = basePositions[i * 3]
      const by = basePositions[i * 3 + 1]
      const bz = basePositions[i * 3 + 2]

      // Individual breathing phase: Points drift inward and outward from their base position
      // Using an individual offset creates a cascading, organic "boiling/breathing" look
      const individualBreathSpeed = 0.8 + (offsets[i] % 1) * 0.5
      const individualPhase = offsets[i] * 5.0
      
      // Calculate how far in/out this point floats based on the wobble state
      const pointDisplacement = Math.sin(t * individualBreathSpeed + individualPhase) * (p.wobble * 1.5)
      const factor = currentScale + pointDisplacement

      positions[i * 3]     = bx * factor
      positions[i * 3 + 1] = by * factor
      positions[i * 3 + 2] = bz * factor
    }

    // Apply smooth mouse easing
    mouseEased.current.x += (state.pointer.x - mouseEased.current.x) * 0.05
    mouseEased.current.y += (state.pointer.y - mouseEased.current.y) * 0.05

    if (pointsRef.current) {
      pointsRef.current.geometry.attributes.position.needsUpdate = true
      
      // Removed rotation: The sphere stays still, relying purely on the inflow/outflow animation.
      // Parallax is maintained so it still reacts slightly to the mouse.
      pointsRef.current.rotation.y = mouseEased.current.x * 0.15
      pointsRef.current.rotation.x = -mouseEased.current.y * 0.15
      
      pointsRef.current.material.opacity = p.brightness
      pointsRef.current.material.size = p.pointSize
    }
  })

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-size"
          count={count}
          array={sizes}
          itemSize={1}
        />
      </bufferGeometry>
      <pointsMaterial
        map={texture}
        size={0.06}
        color="#70a0ff"
        transparent
        opacity={1.0}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

/* ── Exported wrapper ────────────────────────────────────────────────────── */
export default function ParticleSphere({ agentState = 'standby' }) {
  return (
    <div className="particle-container image-matched-bg">
      <div className={`particle-glow image-matched ${agentState !== 'standby' ? 'active' : ''}`} />
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 45 }}
        dpr={[1, 2.5]} // High dpr for sharp points
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <Particles agentState={agentState} />
      </Canvas>
    </div>
  )
}
