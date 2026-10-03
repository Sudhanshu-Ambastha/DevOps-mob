import express from "express";
import helmet from "helmet";
import cookieParser from "cookie-parser";
import routes from "./routes/index.js";
import requestLogger from "./middleware/requestLogger.js";
import { errorHandler, notFound } from "./middleware/errorHandler.js";

const app=express();

app.set("trust proxy", 1);

app.use(helmet());
app.use(express.json({limit:"200kb"}));
app.use(cookieParser());
app.use(requestLogger);

app.use("/api", routes);

app.use(notFound);
app.use(errorHandler);

export default app;
