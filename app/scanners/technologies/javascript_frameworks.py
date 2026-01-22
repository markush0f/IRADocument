"""Framework metadata for JavaScript/TypeScript scanning."""

FRAMEWORK_DEPENDENCIES = {
    "react": {"react"},
    "next": {"next"},
    "astro": {"astro"},
    "vue": {"vue"},
    "nuxt": {"nuxt"},
    "angular": {"@angular/core"},
    "svelte": {"svelte"},
    "sveltekit": {"@sveltejs/kit"},
    "express": {"express"},
    "nestjs": {"@nestjs/core"},
    "koa": {"koa"},
    "fastify": {"fastify"},
    "hapi": {"@hapi/hapi"},
    "vite": {"vite"},
}

FRAMEWORK_CONFIGS = {
    "next": {"next.config.js", "next.config.mjs", "next.config.ts"},
    "astro": {"astro.config.js", "astro.config.mjs", "astro.config.ts"},
    "nuxt": {"nuxt.config.js", "nuxt.config.mjs", "nuxt.config.ts"},
    "angular": {"angular.json"},
    "svelte": {"svelte.config.js", "svelte.config.mjs", "svelte.config.ts"},
    "sveltekit": {"svelte.config.js", "svelte.config.mjs", "svelte.config.ts"},
    "vite": {"vite.config.js", "vite.config.mjs", "vite.config.ts"},
}
