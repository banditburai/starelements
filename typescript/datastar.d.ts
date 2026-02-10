/** Ambient types for Datastar (loaded via import map at runtime). */
declare module 'datastar' {
    /** Run a reactive effect. Returns a dispose function to stop it. */
    export function effect(fn: () => void | (() => void)): () => void;

    /** Merge a patch object into the signal store. */
    export function mergePatch(patch: Record<string, unknown>): void;

    /** Read a value from the signal store by dotted path. */
    export function getPath(path: string): unknown;
}
