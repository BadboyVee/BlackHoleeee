// Everything the site says lives in this one file.
// Change a name, a link or a project here and the whole page follows.

export const site = {
  /** Shown in the logo, the hero and the footer. */
  name: 'Vee',
  role: 'Creative Frontend Developer',
  /** One line under the hero headline. */
  intro:
    'I build interfaces with gravity: real-time 3D, scroll-driven motion and obsessive polish, engineered to stay fast.',
  /**
   * Where the "get in touch" buttons point. Leave `email` empty to send
   * people to GitHub instead; fill it in (e.g. 'hello@you.dev') to open mail.
   */
  email: '',
  github: 'https://github.com/BadboyVee',
  source: 'https://github.com/BadboyVee/BlackHoleeee',
  year: new Date().getFullYear(),
}

export const contactHref = site.email ? `mailto:${site.email}` : site.github
export const contactLabel = site.email || 'github.com/BadboyVee'

export const nav = [
  { label: 'About', href: '#about' },
  { label: 'Work', href: '#work' },
  { label: 'Stack', href: '#stack' },
  { label: 'Approach', href: '#approach' },
  { label: 'Contact', href: '#contact' },
]

export const socials = [
  { label: 'GitHub', href: site.github },
  { label: 'Source code', href: site.source },
]

export const marquee = ['React', 'Three.js', 'WebGPU', 'GLSL', 'TypeScript', 'GSAP', 'Lenis', 'React Three Fiber', 'Tailwind CSS', 'Vite']

export const about = {
  statement:
    'I treat the browser like a physics engine. Motion has weight, 3D has a purpose, and every scroll should feel like falling toward something worth reaching.',
  body: [
    'I work where engineering meets art direction: WebGL and WebGPU scenes, hand-written shaders and interfaces that answer the instant you touch them.',
    'Nothing on this page is a video. The black hole behind these words is a few hundred lines of GLSL bending light around a point, per pixel, sixty times a second.',
  ],
  stats: [
    { value: '04', label: 'Browser worlds, live and playable' },
    { value: '00', label: 'Videos on this page. Every pixel is rendered live' },
    { value: '60', label: 'Frames per second, or it is not finished' },
  ],
}

export interface Project {
  title: string
  kind: string
  description: string
  tags: string[]
  href: string
  /** Optional screenshot in public/work/. Without one, a generated poster is shown. */
  image?: string
  /** Accent used behind the image while it loads and in the hover glow. */
  tone: string
}

const live = 'https://badboyvee.github.io/BlackHoleeee'

export const projects: Project[] = [
  {
    title: 'Saltwind Cove',
    kind: 'WebGPU world',
    description:
      'An ocean you can walk, swim, sail and dive in. FFT waves, breakers that curl on a sandbar, a boat with a real Kelvin wake and a humpback whale.',
    tags: ['WebGPU', 'TSL', 'FFT water'],
    href: `${live}/ocean/`,
    image: './work/saltwind-cove.jpg',
    tone: '#1f6f8b',
  },
  {
    title: 'Skyline Tram',
    kind: 'Browser game',
    description:
      'Drive a retro aerial tram between two islands above a sea of clouds, and keep your passengers comfortable enough to tip.',
    tags: ['Three.js', 'Game design', 'Single file'],
    href: `${live}/skyline-tram/`,
    tone: '#d9783a',
  },
  {
    title: 'Seven Wonders',
    kind: 'Interactive atlas',
    description:
      'The seven ancient wonders on one island. Scrub through four thousand years and watch them rise, stand together and fall.',
    tags: ['Three.js', 'Procedural', 'Synth audio'],
    href: `${live}/seven-wonders/`,
    tone: '#c9a35a',
  },
  {
    title: 'M5 CS',
    kind: 'Procedural model',
    description:
      'A car modelled entirely in code. Lofted bodywork, twenty-spoke wheels and studio lighting, with no imported meshes or textures.',
    tags: ['Three.js', 'Procedural modelling', 'Lighting'],
    href: `${live}/bmw-m5-cs/`,
    tone: '#5b7f6a',
  },
]

/** One row per ring of the orrery, in the same order (see three/Orrery.tsx). */
export const stack = [
  { title: 'Real-time 3D', tools: 'Three.js · React Three Fiber · WebGPU' },
  { title: 'Shaders', tools: 'GLSL · TSL · Ray marching · Post-processing' },
  { title: 'Interface engineering', tools: 'React · TypeScript · Next.js' },
  { title: 'Motion', tools: 'GSAP · ScrollTrigger · Lenis' },
  { title: 'Styling systems', tools: 'Tailwind CSS · Design tokens · Fluid type' },
  { title: 'Performance', tools: 'Adaptive resolution · Code splitting · Frame budgets' },
]

export const approach = [
  {
    title: 'Feel first',
    text: 'I prototype the motion before the layout. If it does not feel right in the hand, no amount of polish will save it later.',
  },
  {
    title: 'Build it real',
    text: 'No faked previews. Real shaders, real data and real devices from the first day, so there are no surprises on the last one.',
  },
  {
    title: 'Budget every frame',
    text: 'Sixteen milliseconds is the whole budget. I measure, adapt resolution on the fly and cut whatever does not earn its cost.',
  },
  {
    title: 'Leave no one out',
    text: 'Keyboards, reduced motion, slow phones. A stunning site that locks people out is not finished.',
  },
]
