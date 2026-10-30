#!/bin/sh
# Bundle the Textures for the static page: site/textures.js (React included). Needs react, react-dom and esbuild:
# NODE_PATH=<a node_modules with them> sh site/textures/build.sh
set -e
cd "$(dirname "$0")"
npx esbuild mount.tsx --bundle --minify --format=iife --jsx=automatic --target=es2019 \
  --define:process.env.NODE_ENV='"production"' --outfile=../textures.js
