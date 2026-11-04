// No KaTeX in this file: `trust` here belongs to other libraries, and `secure` is a cookie
// flag. Neither is a renderer setting.
import express from "express";

const app = express();

// ok: mermaid-or-katex-unsafe-config
export const tlsOptions = { trust: true, rejectUnauthorized: true };

// ok: mermaid-or-katex-unsafe-config
export const cookieOptions = { httpOnly: true, secure: [] };

app.set("trust proxy", true);
