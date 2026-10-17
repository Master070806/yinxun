# Game engines

Genreguessr draws one target uniformly from all **6,291 genres** in the cached Every Noise snapshot. Round one asks for its cluster; only a correct choice unlocks the second sample and exact-genre round. A wrong cluster or final answer ends the game. Targets, cluster centers, correct-choice identifiers, and track metadata stay on the server until an answer is revealed.

Genrerace traverses neighborhoods on the same full catalog and metric provider. Every new center uses the selected geometry on all 6,291 genres; there is no sampled subspace, route-dependent pruning, or injected goal.

## Local setup

Use Python **3.11 or later**. The engine needs NumPy and SciPy; it does not need a GPU, database, Spotify login, or API credentials.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_catalog.py
.venv/bin/python serve.py --port 8780
```

Open [Genreguessr](http://127.0.0.1:8780/genreguessr). The server binds to `127.0.0.1` and is intended for local use.

The complete source crawl is imported locally, not distributed with the repository. Its default location is `../data/everynoise`, relative to the repository. To use another location, set `EVERYNOISE_DATA_DIR` to a directory containing:

```text
index.html
genres.json
neighborhoods.json
pages/engenremap-*.html.gz
```

The builder checks that the map, genre index, and neighborhood records describe the same universe, and verifies every genre-page SHA-256 against the crawl record. Its parsed cache is `.cache/genreguessr/catalog.json`, ignored by Git and outside the public asset routes. Raw pages remain in the source directory. Cache invalidation includes source contents and page file metadata.

## Layers

| Layer | Module | Responsibility |
| --- | --- | --- |
| Source catalog | `engine/catalog.py` | Stable genre IDs, names, XYRGB, two graph layers, and ordered source samples |
| Geometry | `engine/metrics.py` | Parameterized distance matrices, nearest-k clusters, graph balls, reverse cluster membership |
| Sampling | `engine/sampling.py` | Uniform valid center sets conditional on the fixed target, with a bounded attempt budget |
| Game sessions | `engine/game.py` | Uniform target draw, parameter validation, one-way rounds, answer validation, expiry and retry |
| Race sessions | `engine/race.py` | Fixed geometry, directed reachability, legal moves, revision checks, ordered routes and expiry |
| Anonymous audio | `engine/audio.py` | Resolve original preview URLs, proxy bounded audio responses, remove usual ID3 title/artist tags |
| Delivery and presentation | `serve.py`, `web/genreguessr.js`, `web/genre-cluster.js` | Local HTTP interface, minimal round UI, randomized label placement |

Display positions are independent random placements. They never enter a distance calculation. Genre labels retain their original map RGB colors. In Genreguessr, cluster members and box order are shuffled, and centers are not marked. Genrerace marks its current genre with a dotted border.

## Geometry

Let `p_i=(x_i,y_i)` and `c_i=(r_i,g_i,b_i)` be values from the same 6,291-genre main map. Let `s_p²` and `s_c²` be the mean squared distances over all distinct pairs in their respective blocks. Both spatial axes share one scale.

**XYRGB:**

```text
d(i,j)² = α ||p_i-p_j||² / s_p² + (1-α) ||c_i-c_j||² / s_c²,  0 < α < 1.
```

**Neighbor graph:** each raw near link is independently OR-symmetrized: an undirected edge exists if either direction was recorded. Distance is unweighted shortest-path length. Cross-component distance remains infinity; isolated genres are retained. There are 83,881 undirected edges on all 6,291 nodes.

**Signed kernel:** independently OR-symmetrize the opposite links as well, giving adjacency matrices `A_n,A_o` and their separate degree diagonals `D_n,D_o`. Keep an edge in both layers when it occurs in both; do not cancel it before forming the degrees.

```text
L_s = D_n - A_n + λ(D_o + A_o)
K   = (L_s + ηI)^(-1),                         λ,η > 0
d(i,j) = sqrt(2 - 2 K_ij / sqrt(K_ii K_jj)).
```

The signed energy is a sum of squared differences on near edges and squared sums on opposite edges, so `L_s` is positive semidefinite and `K` is positive definite. This gives a finite Euclidean distance between normalized kernel features. The engine computes the dense kernel using Cholesky factorization in float64; it does not substitute shortest paths or a low-dimensional embedding. One 6,291-by-6,291 float64 matrix occupies about 302 MiB. Parameter changes can require a new matrix computation; a bounded process-local cache reuses recent geometries.

The arrangement offers **3–10 clusters** in every mode, with 4 as the default. For XYRGB and signed kernel, `C(a)` contains the **k nearest genres including its center**, where the player chooses an integer `cluster_size = k` from **5 to 25**, defaulting to 20. Ties are resolved by stable genre ID. Changing k updates the clusters and their reverse membership without changing the distance matrix. Center compatibility is `d(a,b) ≥ ℓ`. For graph mode, `C(a)=B_1(a)` is the complete closed unit ball, and compatibility is `H(C(a),C(b)) ≥ m`, with Hausdorff distance computed in the graph metric. Graph clusters vary in size and do not use the cluster-size control. Hausdorff separation does not generally forbid overlap; the required gameplay condition is that exactly one offered cluster contains the target.

## Target-conditioned sampler

First draw the target `t` using a uniform integer in `[0,6291)`, before inspecting audio or sampling feasibility. No genre is filtered for low degree, missing audio, or difficult parameter settings.

For fixed parameters, let `A_t={a:t∈C(a)}` and `k=n-1`. For each possible correct center `a∈A_t`, let `B_a` contain all compatible centers outside `A_t`, and set `w_a=binomial(|B_a|,k)`.

1. Choose `a` with probability `w_a / Σw_a`, using exact integer weights.
2. Draw a uniform `k`-element subset of `B_a`.
3. Check compatibility between all distractor centers. Reject the entire proposal if any pair fails.
4. Accept, shuffle centers and members, and check that exactly one cluster contains `t`.

Every valid set has one correct center and proposal probability `1/Σw_a`. Consequently the accepted center set is uniform among valid sets **conditional on this target and successful generation**. A zero weight sum proves infeasibility. Exhausting 5,000 attempts only means the search failed within its budget. Neither case silently relaxes parameters or rerolls the target. Retrying a failed start keeps the target and permits a revised arrangement. The distribution of successfully generated games alone can differ from the initial uniform target distribution when some targets fail more often.

## Music and state

The first and second samples are exactly `item1` and `item2` on the target's cached genre map, in that order. They are **not** the separate research artist-list order or Spotify playlist order. The snapshot has 44 unavailable first entries and 56 unavailable second entries; these entries contain neither a preview URL nor a track ID. The audio layer supports Every Noise's own `spotproxy.cgi?track=…` resolver when an original track ID exists without a cached URL, but cannot recover these 100 empty source entries. A public availability flag disables playback and explicitly marks an empty source entry, keeping the same game and target. Temporary upstream failures on otherwise present samples permit playback retries. No later sample replaces either entry.

The client receives an opaque local audio link. It does not receive the target's track ID, artist/title, original URL, or correct cluster marker. The audio proxy restricts upstream hosts, bounds response size and cache capacity, and removes standard ID3 metadata. Playback still depends on the external preview being available. This conceals answer metadata in ordinary play; recognizable music itself remains the intended clue.

In the final round, clicking a genre selects it and plays a comparison sample from that genre's map. The server excludes both target clues by track ID and preview URL identity, including duplicates listed under other genres. It randomly chooses one eligible sample per candidate and keeps that choice for the game. Full sample lists are read lazily from the cached genre pages. Only members of the unlocked final cluster can be previewed. Listening does not submit an answer: the Select button still confirms it. The top play button replays the second clue, and switching between clues and candidate previews stops the previous audio. An unavailable comparison sample leaves the selection intact.

Sessions live in memory, expire after two hours, and disappear when the server restarts. The second sample and final-answer endpoint require a correct round-one answer. Invalid selections do not consume a round. A completed game reveals the target with a link to its canonical Every Noise genre page; final guesses also return their distance in the chosen metric. The link is included only when the answer is revealed, for either a correct or incorrect guess. There is no invented score conversion, account system, or leaderboard.

## Genrerace traversal

Let `V` be the full catalog. Fix the chosen metric and parameters for a race. For XYRGB and signed kernel, `C(v)` is the nearest-k cluster over all `V`, including `v`, with `5 ≤ k ≤ 25` and default `k=12`. Graph mode uses the complete closed unit ball `C(v)=B₁(v)`. No cluster-separation parameter is needed for a walk.

The legal movement relation is `v → w` exactly when `w ∈ C(v)` and `w ≠ v`. Although the underlying distances are symmetric, nearest-k membership need not be. Reachability therefore uses reverse breadth-first search on this directed relation. A start outside the goal's reverse-reachable set returns `422 unreachable_goal`; it does not reroll a genre or alter the settings. Legal moves into a region from which the goal cannot be reached remain available and return `goal_reachable: false`. Graph mode has the usual connected-component reachability.

The server owns the start, goal, immutable settings, cluster rows, route and count. Each accepted move appends one genre, recenters the cluster and increments both `moves` and `revision`. Self-moves and nonmembers are rejected. A request with an old revision returns `409 stale_move` with the current public state, so a retried request cannot count twice. Reaching the goal wins; equal start and goal wins with zero moves.

Race sessions hold sparse immutable neighborhood rows, never a dense matrix. Recent full metric matrices are shared through the existing bounded provider cache. Sessions expire after two hours, with at most 128 races retained; expired and then completed sessions are reclaimed before refusing new ones. Restarting the server clears sessions.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/races` | Start with `start_id`, `goal_id` and `settings` |
| `GET /api/races/<id>` | Read public state; `HEAD` is also supported |
| `POST /api/races/<id>/move` | Move with `genre_id` and the current `revision` |
| `GET /api/genres` | All 6,291 names, IDs and RGB colors |
| `GET /api/genres/<id>/audio` | First available numbered sample through the anonymous audio proxy |

The minimal browser interface renders the returned current cluster, with the goal above it and the visited route and move count below. Clicking a genre selects it and plays audio; only Select submits a move. An unavailable sample leaves movement possible. The gameplay history and win screen use the server's route and count, preserving revisits.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_project.py
.venv/bin/python scripts/build_catalog.py
.venv/bin/python scripts/check_race_catalog.py
node --check web/genreguessr.js
node --check web/genrerace.js
node --check web/genre-cluster.js
```

The unit tests cover metric formulas, overlapping signed edges, graph/Hausdorff edge cases, nearest-neighbor ties, equal sampler proposal mass, unique target membership, full-catalog target selection, state gates, privacy boundaries, and target-preserving retries. Project checks exercise local assets and access boundaries. Catalog validation needs the local source crawl; unit fixtures do not. Actual audio playback requires a separate online check.

Race tests cover full-universe traversal, directed reachability, legal traps, invalid moves, fixed goals and settings, concurrent duplicate submissions, zero-move wins, expiry and session bounds. The optional full-crawl audit checks all three 6,291×6,291 matrices, independently verifies sampled nearest-neighbor rows and every graph unit ball, then walks real multi-hop routes through the race service.
