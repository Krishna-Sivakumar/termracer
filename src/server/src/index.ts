import express from 'express';
import http from 'http';
import { env } from 'process';
import { Server } from 'socket.io';
import { event } from './events';

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = env.PORT || 5000;

app.get("/", (req, res) => {
    res.json({
        message: "dummy message"
    })
})

io.on(event.connection, async socket => {
    console.log(`connection established: ${socket.sid}`);

    socket.on(event.message, async function(message: string) {
        console.log(message);
        await socket.send("socket is now disconnecting...");
        await io.in(socket.id).disconnectSockets();
    })
})

server.listen(port, () => {
    console.log(`listening on http://localhost:${port}`);
})
