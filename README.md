# Cartography & BGMs

A collection of games about listening and exploring musical genres, brought by **Circles & Basterds**.

The home, about, and solo/multiplayer game pages support **简体中文 / English**.
Use the button in the bottom-left corner to switch instantly without restarting
the game. Chinese is the initial default; your choice is saved in the browser.
Chinese mode shows supported genre aliases on candidate labels, with original names
in their tooltips and available immediately through the English switch. Revealed
answers, routes and race search suggestions use bilingual labels. Chinese or English
search resolves to the original genre ID; ambiguous
Chinese aliases require selecting the bilingual suggestion. Player nicknames remain
unchanged. The legacy map remains a separate Chinese-only experiment.

`web/genre-names.js` contains editable display aliases and conservative composition
rules. This first pass covers 2,440 of the 6,291 names in the supplied crawl. These
are reading aids, not official genre definitions; unrecognized names retain their
original text. Regional and small-scene names still need further editorial work.

**Genreguessr** is a two-round listening game built on [Every Noise at Once](https://everynoise.com/). It uses a consistent local snapshot of **6,291 genres**, with their map coordinates, colors, musical neighborhoods, contrasting neighborhoods, and song samples. Three selectable metrics determine what it means for genres to be close.

**Genrerace** is a route-finding game on the same complete metric space: choose a start and goal, listen to nearby genres, and move through their neighborhoods until you reach the goal. Both games share the catalog and metric engine. The interface uses randomly scattered genre names in their original RGB colors; their positions on the game screen do not represent metric distance.

## Gameplay

1. **Arrange the game.** Choose a metric, its weights and separation parameters, and **3–10 candidate clusters**. For XYRGB and signed kernel, also choose **5–25 genres per cluster**. Graph mode uses complete one-step neighborhoods, whose sizes vary.
2. **Find the cluster.** The engine draws a target uniformly from all 6,291 genres. Listen to the first sample on that genre's Every Noise map, presented anonymously, and select the cluster containing it.
3. **Find the genre.** A correct cluster choice unlocks the second sample from the same genre. Click candidate genre names to select them and hear comparison samples. These exclude both round clues, including songs also listed under other genres. Each candidate keeps the same comparison sample throughout that game. The top play button replays the second clue; **Select** confirms your answer.
4. **Discover the answer.** A wrong guess ends the game. Both correct and incorrect final outcomes reveal the target with a link to its Every Noise page. Start a new game to play again.

Listening to a candidate does not submit an answer. Only one sample plays at a time. The clues are exactly the map's numbered `item1` and `item2` samples, rather than the separate artist-list or playlist order. Missing or unavailable audio does not silently replace a clue or reroll the target.

## Genrerace

1. Choose any start and goal from all **6,291 genres**, or use either dice button for an independent uniform draw.
2. Choose the metric and its parameters. XYRGB and signed kernel use **5–25 nearest genres including the current genre**, defaulting to 12. Graph mode uses the complete closed unit ball.
3. Click a genre to hear its first available numbered sample. **Select** moves there and opens its neighborhood, computed against the entire catalog. The goal stays visible above the cluster; the visited route and move count appear below. Listening alone never counts as a move.
4. Reach the goal to win. The result shows your ordered route and number of moves. Starting at the goal wins in zero moves.

Settings remain fixed throughout a race. Nearest-neighbor membership can be one-way even with a symmetric metric, so the engine checks reachability on the directed movement graph. An unreachable initial goal is reported without changing either genre or the parameters. Every legal neighbor remains available; a move that makes the goal unreachable is allowed and marked. Audio availability never filters the neighborhoods.

## Multiplayer

The front page also links to **Multiplayer Genreguessr** and **Multiplayer Genrerace**. Create a room, enter a name, and copy its invite link to friends. Each room supports 2–16 players. The host can edit settings in the lobby, then starts once everyone has joined; new players cannot join a game already in progress. Refreshing the same tab restores that player's seat. A player can leave, and the host can remove someone whose browser has closed. Removing a player releases their pending selection; leaving as host transfers control to another active player.

**Multiplayer Genreguessr** retains every single-player arrangement control and adds **1–20 rounds**. Everyone hears the same clues and sees the same clusters. Each round has two stages:

1. Everyone confirms a cluster. The second stage starts only after all active players have selected. A wrong cluster earns zero points and waits for the next round.
2. Players who chose correctly hear the second clue and confirm a genre. The answer and scores are revealed together after all eligible players submit. Everyone selects Next round to continue, or Finish after the final round.

Genre points use the selected metric. If $d$ is the target-to-guess distance and $D$ is the largest finite target distance among the correct cluster's genres, the score is $\operatorname{round}(1000\max(0,1-d/D))$. The exact target earns 1,000 points; an infinite distance earns zero. If $D=0$, a zero-distance guess earns 1,000 points. For example, at half the cluster's maximum distance, a guess earns 500 points. This is a room scoring rule normalized to each question, not a universal measure of musical similarity. Scores accumulate over the chosen number of rounds. Generation retries retain the same hidden target. If a later question cannot be generated, the host can adjust the arrangement and retry that target without losing scores or changing the number of rounds; settings otherwise stay fixed during play.

**Multiplayer Genrerace** gives every player the host's chosen starting genre, goal and metric settings. Each player explores independently. The first goal-reaching move accepted by the server ends the race atomically: later moves are rejected, and everyone sees the winner and every player's complete ordered route and move count. Starting at the goal is a shared zero-move win. Players see other routes only after the race ends.

Rooms synchronize with short polling. The server validates every selection, scores answers, and resolves concurrent moves; browser state cannot award points or choose a winner. Answers, private session IDs, and track metadata stay on the server until the appropriate reveal. Invite links contain a room ID, while each player's separate credential stays in their tab's session storage. Audio credentials are omitted from access logs. Rooms and credentials are temporary and are lost when the server restarts.

## Three ways to measure closeness

| Metric | What it compares | Candidate cluster |
| --- | --- | --- |
| **XYRGB** | Map position and original RGB color, with an adjustable balance | The chosen number of nearest genres, including the center |
| **Neighbor graph** | Shortest paths through Every Noise's light neighborhood links | The center and every genre one edge away |
| **Signed kernel** | Near and contrasting relationships across the whole graph | The chosen number of nearest genres, including the center |

These are different models of the source data, rather than a claim that musical similarity has one objective distance.

### XYRGB: weighted map and color distance

Write a genre's coordinates as $p_i=(x_i,y_i)$ and its color as $c_i=(r_i,g_i,b_i)$. The metric is

$$
d(i,j)^2 = \alpha\frac{\lVert p_i-p_j\rVert^2}{s_p^2}
          +(1-\alpha)\frac{\lVert c_i-c_j\rVert^2}{s_c^2},
\qquad 0<\alpha<1.
$$

Here $s_p^2$ and $s_c^2$ are the mean squared distances over all distinct pairs in the position and color blocks. This normalization makes the weight balance meaningful despite their different scales. Both spatial axes share the same scale. The default is **80% position / 20% color**.

This metric is direct and geometric: nearby map positions and similar colors reduce distance. It does not use the neighborhood graph.

### Neighbor graph: shortest-path distance

Each genre is a vertex. An undirected near edge joins two genres if either genre lists the other in its light neighborhood box. The metric $d_G(i,j)$ is the number of edges in a shortest path; genres in disconnected components have distance $\infty$.

A cluster centered at $a$ is the closed unit ball

$$
B_1(a)=\{v:d_G(a,v)\leq1\}.
$$

Two centers are compatible when the **Hausdorff distance between their unit balls** is at least the chosen integer $m$:

$$
H(A,B)=\max\!\left\{
\max_{a\in A}\min_{b\in B}d_G(a,b),\;
\max_{b\in B}\min_{a\in A}d_G(a,b)
\right\}.
$$

This measures neighborhood structure without using XYRGB. Hausdorff separation is not a minimum gap between every pair of genres: separated clusters can still overlap.

### Signed kernel: near and contrasting relationships

Let $A_n,A_o$ be the undirected adjacency matrices for the light **near** and dark **opposite** neighborhood links, and $D_n,D_o$ their degree matrices. Each layer is symmetrized independently; an edge appearing in both is retained in both.

$$
L_s=D_n-A_n+\lambda(D_o+A_o),\qquad
K=(L_s+\eta I)^{-1},\qquad \lambda,\eta>0.
$$

The normalized kernel induces the distance

$$
d_K(i,j)=\sqrt{2-\frac{2K_{ij}}{\sqrt{K_{ii}K_{jj}}}}.
$$

Near edges contribute squared differences to the signed Laplacian energy; opposite edges contribute squared sums. Thus $L_s$ is positive semidefinite and the regularized kernel is positive definite. The resulting distance is Euclidean between normalized kernel features and uses relationships across the graph. Opposite links influence this geometry; they do not impose a fixed distance on each opposite pair.

**Opposition weight $\lambda$** controls the strength of the opposite layer. **Regularization $\eta$** controls the diagonal shift before inversion. Defaults are $\lambda=1$ and $\eta=0.1$. The implementation uses the full kernel, without a low-dimensional approximation.

## How the clusters are generated

The target is drawn first and kept fixed. For either continuous metric, centers must be pairwise at least the chosen distance $\ell$ apart, and each cluster contains its $k$ nearest genres, including the center. For graph mode, the unit-ball Hausdorff distances must be at least $m$.

Target-conditioned rejection sampling produces a uniform valid center set **conditional on that target and successful generation**. Exactly one offered cluster contains the target; other overlaps are allowed. Cluster order and genre order are shuffled. If no valid arrangement is found within the attempt limit, retrying keeps the same target and allows parameter changes. Parameters are never silently relaxed.

See [the engine guide](docs/ENGINE.md) for the exact sampling distribution, formulas, and implementation layers.

## Run locally

Use **Python 3.11+**. NumPy and SciPy provide the geometry calculations. No Spotify account, API credentials, GPU, or database is required.

```sh
git clone --branch genreguessr https://github.com/Master070806/yinxun.git
cd yinxun
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Supply the complete cached Every Noise crawl. It is **not included in Git**. The default location is `../data/everynoise`, relative to this repository:

```text
everynoise/
├── index.html
├── genres.json
├── neighborhoods.json
└── pages/
    └── engenremap-*.html.gz
```

For another location, set `EVERYNOISE_DATA_DIR` to that directory. Then build the private catalog and start the local server:

```sh
.venv/bin/python scripts/build_catalog.py
.venv/bin/python serve.py --port 8780
```

Open [Cartography & BGMs](http://127.0.0.1:8780/), [Genreguessr](http://127.0.0.1:8780/genreguessr), or [Genrerace](http://127.0.0.1:8780/genrerace). The server binds only to `127.0.0.1`. Audio playback needs an internet connection and an available upstream preview.

For friends on the **same network**, opt into a network listener:

```sh
.venv/bin/python serve.py --host 0.0.0.0 --port 8780
```

Open the game using the host computer's LAN address (for example, `http://192.168.1.10:8780`, with your actual address), then create a room and copy the invite. A `localhost` or `127.0.0.1` invite only works on the host computer. Internet play requires a shared reachable server or HTTPS reverse proxy; this repository does not provision public hosting. All players must connect to the same running Python process because room state is held in memory.

The first geometry calculation can take a moment, especially for signed kernel. One full 6,291-by-6,291 float64 matrix uses about **302 MiB**, and kernel construction needs additional working memory. Recent geometries are cached. Game sessions expire after two hours and disappear when the server restarts.

## Engine structure

| Location | Responsibility |
| --- | --- |
| `engine/catalog.py` | Validated source snapshot, shared genre IDs, graph layers, ordered samples |
| `engine/metrics.py` | XYRGB, graph and signed-kernel distances; cluster construction |
| `engine/sampling.py` | Target-conditioned cluster sampling |
| `engine/game.py` | Target selection, round progression, comparison songs and answer validation |
| `engine/race.py` | Full-catalog traversal, directed reachability, fixed parameters, route and move validation |
| `engine/multiplayer.py` | Invite rooms, player authentication, shared stages, scores and atomic race finishes |
| `engine/audio.py` | Bounded anonymous audio proxy and standard ID3 metadata removal |
| `serve.py` | Local API and explicitly allowed website assets |
| `web/` | Minimal English interface and genre-label layouts |
| `tests/` | Small reproducible fixtures for geometry, sampling, sessions, sources and HTTP |

Answers, source track metadata and correct-cluster identifiers stay on the server during play. Browser audio links are anonymous local endpoints. Recognizing the music itself remains the intended clue.

## Validation

Answer submissions can be retried safely with the same choice. If a response is
lost after the server accepts it, the solo guessing page retrieves the committed
result instead of accepting a second answer. Changing an already submitted answer
is still rejected. In-flight requests show a submitting state and have a timeout.

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_project.py
node --check web/genreguessr.js
node --check web/genrerace.js
node --check web/multiplayer.js
node --check web/genre-cluster.js
node --check web/map.js
node --test tests/i18n.test.mjs
```

The tests use small fixtures and do not require the full crawl or online audio. Actual playback and complete-catalog generation are checked separately. GitHub Actions runs the automated checks on pushes and pull requests.

With the complete local crawl, run `.venv/bin/python scripts/check_race_catalog.py` to audit all three metrics on all 6,291 genres, compare neighborhoods with independent calculations, and verify multi-move races using genres beyond the legacy map's IDs.

## Sources, scope and license

Genre data and samples originate from **Glenn McDonald / Every Noise at Once**. Source pages are checked against their crawl hashes. Raw crawl files, private catalog caches and audio recordings are not committed. Third-party data and recordings retain their own rights; the code's [MIT license](LICENSE) does not relicense them. See [source provenance](DATA_SOURCES.md).

The earlier 5,453-point map remains at `/map.html` as a separate legacy demo. Its community CSV and curated visual fixtures do not determine either game. Accounts, leaderboards, persistent history and production hosting are not implemented.

Further reading: [engine details](docs/ENGINE.md), [current status](docs/STATUS.md), and [contributing](CONTRIBUTING.md).
