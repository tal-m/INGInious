# Grunt script for generating minified JS

This must be executed after every change to the static JS files.

Run `sudo ./docker-minify.sh` to build a docker container with npm/grunt installed, and execute the minify task using docker-compose (outputs will be written directly to the `../../frontend/static/js/` directory).

After minifiy, rebuild the inginious frontend container image.
