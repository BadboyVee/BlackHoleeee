/**
 * Everything written on the site lives here. Change the name, projects and links
 * in this one file and the whole portfolio (and the page title) follows.
 *
 * This file is also read by vite.config.ts at build time, so keep it plain data:
 * no imports and no browser APIs.
 */

export type Project = {
  id: string
  title: string
  kind: string
  year: string
  role: string
  description: string
  stack: string[]
  href: string
  /** Colours and layout for the mock screen shown on the 3D laptop. */
  screen: {
    layout: 'finance' | 'music' | 'commerce' | 'type' | 'system'
    bg: string
    fg: string
    accent: string
    accent2: string
    headline: [string, string]
    url: string
  }
}

export const site = {
  name: 'Kai Morrow',
  firstName: 'Kai',
  lastName: 'Morrow',
  role: 'Creative Frontend Developer',
  title: 'Kai Morrow · Creative Frontend Developer',
  description:
    'Portfolio of Kai Morrow, a creative frontend developer building immersive, high-performance web experiences with React, WebGL and motion.',
  /** Absolute URL of the social preview image, once the site has a domain. */
  ogImage: 'og.jpg',
  email: 'hello@example.com',
  location: 'Lisbon, Portugal',
  timezone: 'Europe/Lisbon',
  availability: 'Available for new projects',
  year: '2026',

  socials: [
    { label: 'GitHub', href: 'https://github.com/' },
    { label: 'LinkedIn', href: 'https://www.linkedin.com/' },
    { label: 'X / Twitter', href: 'https://x.com/' },
    { label: 'Dribbble', href: 'https://dribbble.com/' },
  ],

  nav: [
    { label: 'Work', href: '#work' },
    { label: 'About', href: '#about' },
    { label: 'Toolkit', href: '#toolkit' },
    { label: 'Contact', href: '#contact' },
  ],

  hero: {
    kicker: 'Creative Frontend Developer',
    lead: 'I build web experiences with gravity: interfaces that pull people in through motion, 3D and an obsessive eye for detail.',
    // Sagittarius A*, the black hole at the centre of the Milky Way.
    coordinates: ['Sgr A*', 'RA 17h 45m 40s', 'Dec −29° 00′ 28″'],
  },

  marquee: ['Creative Development', 'WebGL & Three.js', 'Motion Design', 'Interaction', 'Design Systems', 'Performance'],

  about: {
    statement:
      'I’m a frontend developer who treats the browser like a film set. For eight years I’ve turned ambitious ideas into fast, tactile interfaces where motion has meaning, 3D feels effortless and every pixel pulls its weight.',
    body: [
      'I partner with studios, startups and brands that care about craft. Some days that means a design system that keeps forty screens honest. Other days it’s a WebGL scene that has to hold 60 fps on a mid-range phone.',
      'Away from the keyboard I shoot film, chase dark skies and read about things that are very, very far away.',
    ],
    stats: [
      { value: 8, suffix: '+', label: 'Years shipping for the web' },
      { value: 60, suffix: '+', label: 'Projects launched' },
      { value: 99, suffix: '', label: 'Average Lighthouse score' },
      { value: 14, suffix: '', label: 'Industry awards' },
    ],
  },

  projects: [
    {
      id: 'aurora',
      title: 'Aurora Finance',
      kind: 'Real-time wealth dashboard',
      year: '2026',
      role: 'Lead frontend',
      description:
        'A trading dashboard where portfolios move like weather. Live market data streams into fluid WebGL charts at 120 fps, backed by a design system that keeps 400 screens consistent.',
      stack: ['Next.js', 'TypeScript', 'WebGL', 'D3'],
      href: '#contact',
      screen: {
        layout: 'finance',
        bg: '#07111f',
        fg: '#e8f1ff',
        accent: '#3cf0c5',
        accent2: '#7b5cff',
        headline: ['Money,', 'in motion.'],
        url: 'aurora.finance',
      },
    },
    {
      id: 'nebula',
      title: 'Nebula Records',
      kind: 'Audio-reactive label site',
      year: '2025',
      role: 'Creative development',
      description:
        'An independent label’s home as a living galaxy. Every release is a planet, and the music bends the scene in real time through custom shaders driven by the Web Audio API.',
      stack: ['Three.js', 'GLSL', 'Web Audio', 'GSAP'],
      href: '#contact',
      screen: {
        layout: 'music',
        bg: '#0b0612',
        fg: '#f6eaff',
        accent: '#ff4fd8',
        accent2: '#ffb36b',
        headline: ['Sound', 'has gravity'],
        url: 'nebula-records.fm',
      },
    },
    {
      id: 'atlas',
      title: 'Atlas Outdoor',
      kind: '3D product configurator',
      year: '2025',
      role: 'Frontend & 3D',
      description:
        'Customers build their own expedition pack in 3D, choosing materials, colours and straps with live pricing. Conversion rose 38% in the first quarter after launch.',
      stack: ['React Three Fiber', 'Hydrogen', 'Zustand'],
      href: '#contact',
      screen: {
        layout: 'commerce',
        bg: '#ebe4d8',
        fg: '#1b1a17',
        accent: '#d9541e',
        accent2: '#2f4a3a',
        headline: ['Built for', 'the long way'],
        url: 'atlas-outdoor.com',
      },
    },
    {
      id: 'kinetic',
      title: 'Kinetic Type Lab',
      kind: 'Variable-font playground',
      year: '2024',
      role: 'Concept, design & code',
      description:
        'An experimental tool that turns variable fonts into motion. Letters stretch, breathe and react to sound, and the exported loops went on to open a design festival.',
      stack: ['Vite', 'Canvas', 'Variable fonts'],
      href: '#contact',
      screen: {
        layout: 'type',
        bg: '#ff5b1f',
        fg: '#120d0a',
        accent: '#120d0a',
        accent2: '#fff3e8',
        headline: ['TYPE', 'IN MOTION'],
        url: 'kinetic.type',
      },
    },
    {
      id: 'orbit',
      title: 'Orbit UI',
      kind: 'Design system for a SaaS suite',
      year: '2024',
      role: 'Design engineering',
      description:
        '120 accessible components, tokens synced from Figma and visual regression tests that let six product teams ship every week without breaking a pixel.',
      stack: ['React', 'Radix', 'Tailwind', 'Storybook'],
      href: '#contact',
      screen: {
        layout: 'system',
        bg: '#f3f4f7',
        fg: '#14151a',
        accent: '#4f46e5',
        accent2: '#16a34a',
        headline: ['One system,', 'every product'],
        url: 'orbit-ui.dev',
      },
    },
  ] satisfies Project[],

  toolkit: {
    orbs: [
      'React', 'TypeScript', 'Three.js', 'R3F', 'GLSL', 'WebGL', 'WebGPU', 'GSAP', 'Lenis', 'Next.js', 'Vite',
      'Node', 'Tailwind', 'CSS', 'HTML', 'Figma', 'Blender', 'Astro', 'Svelte', 'Git', 'A11y', 'Motion',
    ],
    groups: [
      { title: 'Languages', items: ['TypeScript', 'JavaScript', 'GLSL & WGSL', 'HTML & CSS'] },
      { title: 'Frameworks', items: ['React & Next.js', 'Astro', 'Svelte', 'Node'] },
      { title: 'Creative', items: ['Three.js & R3F', 'WebGL & WebGPU', 'GSAP & Lenis', 'Canvas & SVG'] },
      { title: 'Craft', items: ['Design systems', 'Accessibility', 'Performance', 'Figma & Blender'] },
    ],
  },

  process: [
    {
      title: 'Discover',
      tagline: 'Orbit the problem',
      text: 'Workshops, audits and a lot of questions. We map goals, people and constraints before a single pixel moves.',
      deliverables: ['Research', 'Creative brief', 'Technical plan'],
    },
    {
      title: 'Design',
      tagline: 'Shape the gravity',
      text: 'Moodboards, prototypes and motion studies. Ideas get tested early in the browser, where they will actually live.',
      deliverables: ['Prototypes', 'Motion language', 'Design system'],
    },
    {
      title: 'Develop',
      tagline: 'Bend the light',
      text: 'Production code that is typed, tested and tuned. 3D and animation are built to hold 60 fps on real devices, not only on my laptop.',
      deliverables: ['Frontend build', 'WebGL & shaders', 'CMS integration'],
    },
    {
      title: 'Launch',
      tagline: 'Escape velocity',
      text: 'Performance budgets, accessibility checks and analytics, then a calm launch day. I stay on to measure, learn and improve.',
      deliverables: ['QA & accessibility', 'Launch', 'Iteration'],
    },
  ],

  experience: [
    { years: '2024 — Now', role: 'Senior Creative Developer', company: 'Studio Parallax', place: 'Remote' },
    { years: '2021 — 2024', role: 'Frontend Engineer', company: 'Nebula Labs', place: 'Lisbon' },
    { years: '2019 — 2021', role: 'Interactive Developer', company: 'Pixelcraft Agency', place: 'Berlin' },
    { years: '2017 — 2019', role: 'Freelance Web Developer', company: 'Independent', place: 'Worldwide' },
  ],

  contact: {
    kicker: 'Contact',
    headline: ['Got an idea?', 'Let’s give it', 'gravity.'],
    text: 'Tell me about your project, timeline and ambitions. I usually reply within a day.',
    cta: 'Start a project',
  },
}

export type Site = typeof site
