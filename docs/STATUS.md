# Current status

Updated 2026-10-17.

## Genreguessr

The English front page links to `/genreguessr`. Arrangement starts a one-way game: choose a cluster, then—only after a correct choice—identify the exact genre. Gameplay keeps the minimal cluster boxes, selection button and anonymous audio control. Genre names are scattered in two dimensions with their original RGB colors; there is no 3D model, dragging, recentering, or stage navigation. Display placement does not represent metric distance.

The actual engine replaces the curated visual fixtures:

- A uniform draw selects one of all 6,291 genres before media availability or cluster feasibility is checked. No genre is filtered or silently replaced.
- The selected XYRGB, neighbor-graph, or signed-kernel metric and its parameters determine real clusters. Players choose 3–10 clusters. Continuous metrics use a chosen 5–25 nearest genres including the center (default 20); graph mode uses complete closed unit balls.
- Target-conditioned rejection sampling produces a uniform valid center set on success. Exactly one offered cluster contains the target. Failed generation retains the target for retry and does not silently relax the settings.
- Round one plays the genre map's first sample; the correct cluster unlocks its second sample. Track metadata stays server-side behind an opaque local audio endpoint.
- In the final round, clicking a genre plays a separate comparison sample and selects that genre. Both clue songs are excluded, including cross-genre duplicates. Select still confirms the answer; the top play control still replays the second clue.
- Server-owned sessions enforce one-way progression and validate selections. A wrong choice ends the game; completed games reveal the target with a link to its Every Noise genre page. Final guesses also return the selected metric distance, without a fabricated score scale.

The parsed catalog is validated against the complete local crawl. It contains 83,881 undirected near edges and 114,896 undirected opposite edges, with both layers preserved on their 32 overlaps. The main map, graph endpoints and sample metadata share the same genre IDs. Raw source files and private caches remain outside public web routes.

## Operational limits

The source crawl must be supplied locally; it is not distributed with the repository. Python 3.11+, NumPy and SciPy are required for gameplay. Signed-kernel construction uses a dense float64 matrix; one full distance matrix uses about 302 MiB. Geometry is cached within the running server.

The snapshot has 44 unavailable first entries and 56 unavailable second entries, each missing both its preview URL and track ID. The server supports Every Noise's resolver when a track ID exists, but cannot resolve these empty entries. Other upstream previews can also become unavailable. It never substitutes a later song or rerolls a target because playback fails.

Graph distance is infinite between disconnected components, and isolated genres remain eligible. Graph cluster sizes vary. Some parameter settings admit no valid cluster set; bounded sampling can also exhaust its attempt limit without proving impossibility.

Sessions expire after two hours and are lost when the server restarts. Accounts, leaderboards, a universal score scale, persistent history, Genrerace gameplay, and production hosting are not implemented.

See [ENGINE.md](ENGINE.md) for exact formulas, sampler guarantees, local setup and validation commands. Unit coverage includes metric identities, graph/Hausdorff edge cases, sampler probability, target coverage, progression, hidden-answer metadata and retained-target retries. The suite passes 67 tests, including lazy source parsing, duplicate-song exclusion and final-round comparison access. Live browser checks confirmed clue and candidate playback, switching between songs, generated clusters and the round transitions. Missing source samples are marked explicitly with playback disabled; they do not trigger a target substitution.

## Legacy map

`/map.html` remains the earlier 5,453-point EveryNoise-Watch demo, with its own bundled CSV-derived data and XY experiments. It is separate from the 6,291-genre gameplay engine. Its old curated cluster fixtures remain historical assets and do not determine actual games. The original README is preserved below the new English setup section.

Earlier audio-model experiments remain only in Git history. The current implementation does not require GPU models, an embedding database, or the previously proposed 100-song library. Source provenance and license boundaries are recorded in [DATA_SOURCES.md](../DATA_SOURCES.md).
