import app from "./app.js";
import db from "./db.js";

const port = process.env.PORT || 3000;
const server = app.listen(port, () => console.log(`Inventory API listening on ${port}`));

for (const signal of ["SIGTERM", "SIGINT"]) {
    process.on(signal, () => {
        server.close(() => {
            db.close();
            process.exit(0);
        });
    });
}