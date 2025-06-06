/** @type {import('next').NextConfig} */
import fs from "fs";
import webpack from "./webpack.config.mjs";

const nextConfig = JSON.parse(fs.readFileSync("./next.config.json", "utf-8"));
nextConfig.webpack = webpack;
nextConfig.env = {
  INPUT_FILES: process.env.INPUT_FILES,
};
export default nextConfig;
