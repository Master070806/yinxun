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

Sessions expire after two hours and are lost when the server restarts. Accounts, global leaderboards, a universal score scale, persistent history, and production hosting are not implemented. Multiplayer room scoreboards use the explicit per-question distance rule described in the README.

See [ENGINE.md](ENGINE.md) for exact formulas, sampler guarantees, local setup and validation commands. Automated tests cover the original guessing engine, sample parsing and playback endpoints, race traversal, directed reachability, session bounds, concurrent duplicate moves, and multiplayer rooms. The earlier full-catalog audit passed for all three 6,291×6,291 geometries, including independently checked neighborhoods and multi-hop races. Missing Genreguessr source clues are marked explicitly with playback disabled; they do not trigger a target substitution.

## Genrerace

The front-page Genrerace link opens `/genrerace`. Setup includes all 6,291 start and goal genres, independent randomization dice, the three metric choices and their relevant controls. The playing screen contains one cluster, a Select button, and a minimal route history with the move count. The history lists every visited genre in order, including the start and revisits, and marks the current position. Clicking a genre selects it and plays its first available Every Noise sample; Select confirms the move and opens that genre's actual neighborhood. Listening never increments the round count or adds a history entry. The current genre can be heard without moving. The win screen shows only “You win,” the number of moves and the ordered visited route. A start equal to the goal finishes in zero moves.

The race engine uses the full metric space at every step: nearest-k neighborhoods for XYRGB and signed kernel (5–25 genres including the center; default 12), and complete closed unit balls for graph mode. Parameters stay fixed during the race. There are no example clusters, route-based subsets or forced goal appearances. Race sessions share the metric provider and retain only sparse neighborhoods, avoiding a dense matrix per session.

Reachability respects directed nearest-neighbor membership. An unreachable initial pair is reported without rerolling. Legal moves into a region that cannot reach the goal remain available and are marked. The server validates moves, route and count; revision checks prevent duplicate submissions from moving twice. Playback uses the existing bounded anonymous audio proxy, and a playback failure leaves movement available.

A live browser check completed youth orchestra → american romanticism → korean classical performance → chamber ensemble in exactly three moves. It confirmed audio playback without movement, fresh neighborhoods after Select, stopped audio on movement, and the server-derived route on the win screen.

## Multiplayer

Two additional front-page links open multiplayer Genreguessr and Genrerace. Rooms use invite links, separate player credentials, a host-controlled lobby, and shared server state. Genreguessr retains all arrangement settings and adds 1–20 rounds, with barriers between cluster guesses, eligible genre guesses, and result acknowledgments. Incorrect cluster guesses earn zero; final genre scores depend on the chosen metric and accumulate in the room scoreboard. Genrerace fixes a common start and goal, accepts independent legal moves, and freezes all routes on the first winning move. Final results display every route, including players who left.

Room polling restores the same player on refresh. Leaving or host removal releases a pending barrier. Private answers and source metadata are excluded from room snapshots. The server remains loopback-only by default; `--host 0.0.0.0` explicitly enables access from other devices, and invite links use the browser's current host. Public hosting is not provisioned.

Validation: all 142 automated tests pass, including 42 multiplayer tests. Live browser checks completed a three-player, two-round guessing match with distance scores and cumulative standings, and a two-player race with independent routes, refresh recovery, and a shared finish. Lobby settings edits and invite copying were also verified. Failed later-round generation can be retried with adjusted settings while preserving the pending target, scores, and round count.

## Legacy map

`/map.html` remains the earlier 5,453-point EveryNoise-Watch demo, with its own bundled CSV-derived data and XY experiments. It is separate from the 6,291-genre gameplay engine. Its old curated cluster fixtures remain historical assets and do not determine actual games. The original README is preserved below the new English setup section.

Earlier audio-model experiments remain only in Git history. The current implementation does not require GPU models, an embedding database, or the previously proposed 100-song library. Source provenance and license boundaries are recorded in [DATA_SOURCES.md](../DATA_SOURCES.md).
