import express from 'express';
import http from 'http';
import { env } from 'process';
import { Server } from 'socket.io'

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = env.PORT || 5000;

app.get("/", (req, res) => {
    res.json({
        message: "dummy message"
    })
})

server.listen(port, () => {
    console.log(`listening on http://localhost:${port}`);
})
