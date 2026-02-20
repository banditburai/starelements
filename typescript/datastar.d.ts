/** Ambient types for Datastar (loaded via import map at runtime). */
declare module 'datastar' {
    export function effect(fn: () => void | (() => void)): () => void;
    export function mergePatch(patch: Record<string, unknown>): void;
    export function getPath(path: string): unknown;
    /** Effects are deferred until all nested batches close. */
    export function beginBatch(): void;
    export function endBatch(): void;
}
