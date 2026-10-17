# Third-party sources — gameplay engines

Both live engines use one consistent **6,291-genre Every Noise snapshot** from the locally imported crawl, checked on 2026-10-14. They do not combine the legacy 5,453-row community CSV with the newer graph.

| Engine material | Original source | Import and use |
| --- | --- | --- |
| Genre names, XY coordinates, RGB colors | [Every Noise main map](https://everynoise.com/engenremap.html), cached `index.html` | All 6,291 entries; original names, coordinates and colors retained. Display label positions are randomized separately. |
| Near links | First light neighborhood on each cached genre page; `nearbyitem*` entries | Self entries excluded. 123,435 directed arcs become 83,881 edges by OR-symmetrization. |
| Opposite links | Dark neighborhood on each cached genre page; `mirroritem*` entries | 125,820 directed arcs become 114,896 edges. The two graph layers retain their 32 shared undirected edges. |
| Round samples | Each genre map's `item1` and `item2`, with source `preview_url` and Spotify track ID | Original order retained. These are not the research artist list or Spotify playlist order. Audio is fetched only for playback through an anonymous local endpoint. |
| Comparison samples | Numbered `itemN` entries on each candidate genre's cached map | Read lazily and checked against the crawl hash. A stable random sample per candidate excludes both clue songs by track ID or preview URL identity. |

The catalog contains 44 unavailable first entries and 56 unavailable second entries. These 100 source entries contain neither a preview URL nor a track ID; their missing values are preserved. The server supports Every Noise's own resolver when an original track ID is available, but that fallback cannot recover an empty source entry. Unavailable audio does not remove a genre from the target pool or replace a sample.

Source fingerprints:

```text
index.html SHA-256:
06742b5d75e2e3b03dbbd8550c36b3bcd22b4cbb77d232cd81755881de90e978
neighborhoods.json SHA-256:
63851ed9c6f6a35ae16400cf9414740934de701c0ce77fc61590ba9c7acdf16d
```

Every imported genre page is also checked against its crawl-record SHA-256. The parsed catalog records the source URLs, crawl-check interval, and sample element positions. See [ENGINE.md](docs/ENGINE.md) for the local import command and directory layout.

Genrerace uses this complete catalog for every metric and neighborhood, as well as names, colors and the first available numbered sample of a clicked genre. Neither audio availability nor route history removes genres from its metric space.

The original map is by Glenn McDonald / Every Noise at Once. Raw pages, graph data, private catalog caches and audio are not committed or redistributed by this change. The repository's MIT license and the legacy community CSV's CC BY-SA declaration do not grant rights to this separate website crawl or its recordings. Third-party material retains its original rights.

## Legacy map sources

The following records concern the separate `/map.html` demo and its former visual fixtures. The gameplay engine does not use the curated `genreguessr-demo.json` groups.

# 第三方数据与许可

| 内容 | 来源/版本 | 许可与处理 |
| --- | --- | --- |
| `web/map-data.json` | [EveryNoise-Watch](https://github.com/AyrtonB/EveryNoise-Watch)，提交26915304e3b99dc70b0c3f85b0e3954289df72f0，5,453行 | 上游[datapackage.json](https://github.com/AyrtonB/EveryNoise-Watch/blob/26915304e3b99dc70b0c3f85b0e3954289df72f0/data/datapackage.json)标注[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)；此转换数据沿用同许可 |
| `web/genreguessr-demo.json` | 120 genres curated from the same `map-data.json` snapshot above | CC BY-SA 4.0; names, XY coordinates and RGB colors copied unchanged. Six groups are visual fixtures, not metric-generated clusters. On-screen positions are randomized independently of the source coordinates. |
| 网站原始邻居抓取包 | 协作者提供，6,291节点快照 | 本地研究资料，未纳入Git；不以本项目MIT或社区CSV许可替代其来源许可 |

地图署名：原始地图由 Glenn McDonald / Every Noise at Once 制作，社区数据由 Ayrton Bourn 整理。当前转换把 `genre,x,y,hex_colour` 改为JSON对象 `name,x,y,color`，坐标和颜色保持不变。前端另外计算XY近邻和距离，未宣称为原站的邻居算法。数据页保留来源和许可链接。

CC BY-SA 4.0适用于该地图转换数据；代码MIT许可不替代数据许可。本清单记录上游声明，不声称重新授予第三方权利。新增或更新第三方材料必须记录相应来源与许可。
