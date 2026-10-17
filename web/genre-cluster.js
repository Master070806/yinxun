/** A random, flat arrangement of genre names. Positions carry no metric meaning. */
export class GenreCluster {
  constructor(container, genres, { selectable = false, onSelect = () => {}, large = false } = {}) {
    this.container = container;
    this.selectable = selectable;
    this.onSelect = onSelect;
    this.large = large;
    this.selection = null;
    this.frame = null;
    this.disposed = false;
    this.originalMinHeight = container.style.minHeight;
    this.hadViewportClass = container.classList.contains('cluster-viewport');
    this.hadLargeClass = container.classList.contains('gc-large');
    container.classList.add('cluster-viewport');
    container.classList.toggle('gc-large', large);

    this.stage = document.createElement('div');
    this.stage.className = 'gc-stage';
    this.items = genres.map((genre) => {
      const label = document.createElement(selectable ? 'button' : 'span');
      label.className = 'gc-label';
      label.textContent = genre.name;
      label.style.color = genre.color || '#555249';
      if (selectable) {
        label.type = 'button';
        label.setAttribute('aria-pressed', 'false');
        label.addEventListener('click', () => {
          this.select(genre.name);
          this.onSelect(genre.name, genre);
        });
      }
      this.stage.append(label);
      return { genre, label, x: Math.random(), y: Math.random(), width: 0, height: 0 };
    });
    container.append(this.stage);

    this.observer = new ResizeObserver(() => this.schedule());
    this.observer.observe(container);
    this.schedule();
    if (document.fonts?.ready) document.fonts.ready.then(() => this.schedule());
  }

  schedule() {
    if (this.disposed || this.frame !== null) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      this.render();
    });
  }

  render() {
    const width = this.container.clientWidth;
    if (!width) return;

    // Recalculate from the CSS height so a narrow layout can shrink again after
    // becoming wider. Random anchors stay fixed throughout this instance.
    this.container.style.minHeight = this.originalMinHeight;
    const height = this.container.clientHeight;
    if (!height) return;
    const pad = 10;
    const fontSize = this.large ? 18 : (width > 350 ? 14 : 12.5);
    const points = this.items.map((item) => {
      item.label.style.fontSize = `${fontSize}px`;
      item.label.style.maxWidth = `${Math.max(1, width - pad * 2)}px`;
      item.width = item.label.offsetWidth;
      item.height = item.label.offsetHeight;
      const anchorX = pad + item.width / 2 + item.x * Math.max(0, width - pad * 2 - item.width);
      const anchorY = pad + item.height / 2 + item.y * Math.max(0, height - pad * 2 - item.height);
      return { x: anchorX, y: anchorY, anchorX, anchorY, item };
    });

    this.packLabels(points, width, height, pad);
    for (const point of points) {
      point.item.label.style.transform = `translate(-50%, -50%) translate(${point.x.toFixed(2)}px, ${point.y.toFixed(2)}px)`;
    }
    this.stage.style.visibility = 'visible';
  }

  packLabels(points, width, height, pad) {
    const gap = this.large ? 10 : 5;
    const placed = [];
    const bySize = [...points].sort((a, b) => b.item.width * b.item.height - a.item.width * a.item.height);
    for (const point of bySize) {
      const halfWidth = point.item.width / 2, halfHeight = point.item.height / 2;
      if (point.item.height > height - pad * 2) {
        this.packRows(points, width, height, gap, pad);
        return;
      }
      const clampX = (x) => Math.max(pad + halfWidth, Math.min(width - pad - halfWidth, x));
      const clampY = (y) => Math.max(pad + halfHeight, Math.min(height - pad - halfHeight, y));
      const candidatesX = [clampX(point.x), pad + halfWidth, width - pad - halfWidth];
      const candidatesY = [clampY(point.y), pad + halfHeight, height - pad - halfHeight];
      for (const other of placed) {
        candidatesX.push(clampX(other.left - gap - halfWidth), clampX(other.right + gap + halfWidth));
        candidatesY.push(clampY(other.top - gap - halfHeight), clampY(other.bottom + gap + halfHeight));
      }
      let best = null;
      let bestCost = Infinity;
      for (const x of candidatesX) {
        const costX = (x - point.anchorX) ** 2;
        if (costX >= bestCost) continue;
        for (const y of candidatesY) {
          const cost = costX + (y - point.anchorY) ** 2;
          if (cost >= bestCost) continue;
          const rect = { left: x - halfWidth, right: x + halfWidth, top: y - halfHeight, bottom: y + halfHeight };
          const collision = placed.some((other) =>
            rect.left < other.right + gap - 0.01 && rect.right > other.left - gap + 0.01 &&
            rect.top < other.bottom + gap - 0.01 && rect.bottom > other.top - gap + 0.01);
          if (!collision) {
            best = { x, y, ...rect };
            bestCost = cost;
          }
        }
      }
      if (!best) {
        this.packRows(points, width, height, gap, pad);
        return;
      }
      point.x = best.x;
      point.y = best.y;
      placed.push(best);
    }
  }

  packRows(points, width, height, gap, pad) {
    // Preserve a random order when a narrow box needs a shelf fallback. Let the
    // box grow naturally instead of clipping names or adding an inner scroller.
    const rows = [];
    for (const point of [...points].sort((a, b) => a.anchorY - b.anchorY)) {
      let row = rows[rows.length - 1];
      if (!row || row.width + gap + point.item.width > width - pad * 2) {
        row = { points: [], width: 0, height: 0 };
        rows.push(row);
      }
      row.width += point.item.width + (row.points.length ? gap : 0);
      row.height = Math.max(row.height, point.item.height);
      row.points.push(point);
    }
    const requiredHeight = rows.reduce((sum, row) => sum + row.height, 0) + gap * Math.max(0, rows.length - 1) + pad * 2;
    if (requiredHeight > height) {
      height = Math.ceil(requiredHeight);
      this.container.style.minHeight = `${height}px`;
    }
    let previousBottom = pad - gap;
    for (const row of rows) {
      row.y = Math.max(previousBottom + gap + row.height / 2,
        row.points.reduce((sum, point) => sum + point.anchorY, 0) / row.points.length);
      previousBottom = row.y + row.height / 2;
    }
    let nextTop = height - pad + gap;
    for (const row of [...rows].reverse()) {
      row.y = Math.min(row.y, nextTop - gap - row.height / 2);
      nextTop = row.y - row.height / 2;
      const ordered = row.points.sort((a, b) => a.anchorX - b.anchorX);
      let previousRight = pad - gap;
      for (const point of ordered) {
        point.x = Math.max(previousRight + gap + point.item.width / 2, point.anchorX);
        point.y = row.y;
        previousRight = point.x + point.item.width / 2;
      }
      let nextLeft = width - pad + gap;
      for (const point of [...ordered].reverse()) {
        point.x = Math.min(point.x, nextLeft - gap - point.item.width / 2);
        nextLeft = point.x - point.item.width / 2;
      }
    }
  }

  select(name) {
    this.selection = name;
    for (const item of this.items) {
      const selected = item.genre.name === name;
      item.label.classList.toggle('gc-selected', selected);
      if (this.selectable) item.label.setAttribute('aria-pressed', String(selected));
    }
  }

  destroy() {
    this.disposed = true;
    if (this.frame !== null) cancelAnimationFrame(this.frame);
    this.observer.disconnect();
    this.stage.remove();
    this.container.style.minHeight = this.originalMinHeight;
    this.container.classList.toggle('cluster-viewport', this.hadViewportClass);
    this.container.classList.toggle('gc-large', this.hadLargeClass);
  }
}
