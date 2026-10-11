/** The admin's two springs: one for things that arrive, one for moving between states. */
export const springArrive = { type: "spring", stiffness: 400, damping: 30 } as const;
export const springMove = { type: "spring", stiffness: 200, damping: 24 } as const;
