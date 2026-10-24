import express from "express";
import db from "./db.js";
import { validateItem } from "./validate.js";

const app = express();
app.use(express.json());

const parseId = (raw) => (/^[1-9]\d*$/.test(raw) ? Number(raw) : null);

app.get("/health", (req, res) => {
    try {
        db.prepare("SELECT 1").get();
        res.json({ status: "ok", db: "up", uptime: process.uptime() });
    } catch {
        res.status(503).json({ status: "error", db: "down" });
    }
});

app.get("/items", (req, res) => {
    const limit = req.query.limit === undefined ? 10 : Number(req.query.limit);
    const offset = req.query.offset === undefined ? 0 : Number(req.query.offset);

    if (!Number.isInteger(limit) || limit < 1 || limit > 100)
        return res.status(400).json({ errors: ["limit must be an integer between 1 and 100"] });
    if (!Number.isInteger(offset) || offset < 0)
        return res.status(400).json({ errors: ["offset must be an integer >= 0"] });

    const data = db.prepare("SELECT * FROM items ORDER BY id LIMIT ? OFFSET ?").all(limit, offset);
    const { total } = db.prepare("SELECT COUNT(*) AS total FROM items").get();
    res.json({ data, total, limit, offset });
});

// Get one
app.get("/items/:id", (req, res) => {
    const id = parseId(req.params.id);
    if (id === null) return res.status(400).json({ errors: ["id must be a positive integer"] });

    const item = db.prepare("SELECT * FROM items WHERE id = ?").get(id);
    if (!item) return res.status(404).json({ errors: ["item not found"] });
    res.json(item);
});

// Create
app.post("/items", (req, res) => {
    const errors = validateItem(req.body);
    if (errors.length) return res.status(400).json({ errors });

    const { name, sku, quantity, price } = req.body;
    try {
        const info = db
            .prepare("INSERT INTO items (name, sku, quantity, price) VALUES (?, ?, ?, ?)")
            .run(name.trim(), sku, quantity, price);
        const item = db.prepare("SELECT * FROM items WHERE id = ?").get(info.lastInsertRowid);
        res.status(201).location(`/items/${item.id}`).json(item);
    } catch (e) {
        if (e.code === "SQLITE_CONSTRAINT_UNIQUE")
            return res.status(409).json({ errors: ["sku already exists"] });
        throw e;
    }
});

app.put("/items/:id", (req, res) => {
    const id = parseId(req.params.id);
    if (id === null) return res.status(400).json({ errors: ["id must be a positive integer"] });

    const errors = validateItem(req.body);
    if (errors.length) return res.status(400).json({ errors });

    const { name, sku, quantity, price } = req.body;
    try {
        const info = db
            .prepare("UPDATE items SET name = ?, sku = ?, quantity = ?, price = ? WHERE id = ?")
            .run(name.trim(), sku, quantity, price, id);
        if (info.changes === 0) return res.status(404).json({ errors: ["item not found"] });
        res.json(db.prepare("SELECT * FROM items WHERE id = ?").get(id));
    } catch (e) {
        if (e.code === "SQLITE_CONSTRAINT_UNIQUE")
            return res.status(409).json({ errors: ["sku already exists"] });
        throw e;
    }
});

app.delete("/items/:id", (req, res) => {
    const id = parseId(req.params.id);
    if (id === null) return res.status(400).json({ errors: ["id must be a positive integer"] });

    const info = db.prepare("DELETE FROM items WHERE id = ?").run(id);
    if (info.changes === 0) return res.status(404).json({ errors: ["item not found"] });
    res.status(204).end();
});

app.use((req, res) => res.status(404).json({ errors: ["route not found"] }));

app.use((err, req, res, next) => {
    if (err.type === "entity.parse.failed")
        return res.status(400).json({ errors: ["malformed JSON"] });
    console.error(err);
    res.status(500).json({ errors: ["internal server error"] });
});

export default app;