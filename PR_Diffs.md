### PR-ready diffs

- fix(logging): avoid container write failures by making file handlers best-effort

```startLine:endLine:app/core/logger_config.py
16:31:app/core/logger_config.py
 def setup_logger(
     name: str = "bookology",
     level: Optional[str] = None,
     format_string: Optional[str] = None
 ) -> logging.Logger:
     """
-    Set up and configure a logger instance with both console and file output.
+    Set up and configure a logger instance with both console and (best-effort) file output.
+    Falls back to console-only when file handlers cannot be created (e.g., read-only FS).
     """
```

- fix(security): tighten CSP connect-src in production and keep permissive DEBUG profile

```startLine:endLine:app/main.py
37:46:app/main.py
-        # Basic CSP (relaxed in DEBUG)
-        if settings.DEBUG:
+        # CSP (configurable)
+        if settings.DEBUG:
             csp = (
                 "default-src 'self'; "
                 "img-src 'self' data: blob: *; "
                 "media-src 'self' data: blob: *; "
                 "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                 "style-src 'self' 'unsafe-inline'; "
                 "connect-src 'self' *; "
                 "font-src 'self' data:; "
                 "frame-ancestors 'none'"
             )
         else:
-            csp = "default-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; font-src 'self' data:; frame-ancestors 'none'"
+            allowed_connect = ["'self'"] + [o for o in settings.ALLOWED_ORIGINS]
+            csp = (
+                "default-src 'self'; "
+                "img-src 'self' data: blob:; "
+                "media-src 'self' data: blob:; "
+                "script-src 'self'; "
+                "style-src 'self' 'unsafe-inline'; "
+                f"connect-src {' '.join(allowed_connect)}; "
+                "font-src 'self' data:; "
+                "frame-ancestors 'none'"
+            )
```

- perf(api): add ETag/304 to chapters endpoint to cut repeated payloads

```startLine:endLine:app/api/stories.py
103:151:app/api/stories.py
-@router.get("/story/{story_id}/chapters")
-async def get_story_chapters(
-    story_id: int, response: Response, user = Depends(get_authenticated_user_optional)
-):
+@router.get("/story/{story_id}/chapters")
+async def get_story_chapters(
+    story_id: int, response: Response, request: Request, user = Depends(get_authenticated_user_optional)
+):
@@
-        chapters = []
-        for chapter in chapters_response.data or []:
-            chapters.append(
-                {
-                    "id": chapter["id"],
-                    "chapter_number": chapter["chapter_number"],
-                    "title": chapter.get("title", f"Chapter {chapter['chapter_number']}")
-                    or f"Chapter {chapter['chapter_number']}",
-                    "content": chapter["content"],
-                    "summary": chapter.get("summary", ""),
-                    "created_at": chapter["created_at"],
-                    "word_count": len(chapter["content"].split()) if chapter["content"] else 0,
-                }
-            )
+        chapters = []
+        total_words = 0
+        latest_updated_at = ""
+        for chapter in chapters_response.data or []:
+            content = chapter["content"] or ""
+            word_count = len(content.split()) if content else 0
+            total_words += word_count
+            updated_at = chapter.get("updated_at") or chapter.get("created_at") or ""
+            if updated_at and updated_at > latest_updated_at:
+                latest_updated_at = updated_at
+            chapters.append(
+                {
+                    "id": chapter["id"],
+                    "chapter_number": chapter["chapter_number"],
+                    "title": chapter.get("title", f"Chapter {chapter['chapter_number']}")
+                    or f"Chapter {chapter['chapter_number']}",
+                    "content": content,
+                    "summary": chapter.get("summary", ""),
+                    "created_at": chapter["created_at"],
+                    "word_count": word_count,
+                }
+            )
+
+        from hashlib import sha256
+        etag_payload = f"{len(chapters)}:{total_words}:{latest_updated_at}".encode("utf-8")
+        etag_value = sha256(etag_payload).hexdigest()[:32]
+        response.headers["ETag"] = etag_value
+
+        if request.headers.get("If-None-Match") == etag_value:
+            response.status_code = status.HTTP_304_NOT_MODIFIED
+            return
```

- perf(web): tune React Query caching and retries

```startLine:endLine:Bookology-frontend/src/main.jsx
7:16:Bookology-frontend/src/main.jsx
-const queryClient = new QueryClient()
+const queryClient = new QueryClient({
+  defaultOptions: {
+    queries: {
+      retry: 2,
+      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 5000),
+      staleTime: 60 * 1000,
+      gcTime: 10 * 60 * 1000,
+      refetchOnWindowFocus: false,
+    },
+    mutations: {
+      retry: 1,
+      retryDelay: 1000,
+    }
+  }
+})
```

- perf/seo(web): image hints and SEO meta

```startLine:endLine:Bookology-frontend/src/components/StoryDashboard.jsx
311:321:Bookology-frontend/src/components/StoryDashboard.jsx
+              width="1200" height="675"
+              loading="eager"
+              decoding="async"
+              fetchpriority="high"
```

```startLine:endLine:Bookology-frontend/src/components/EnhancedStoryCard.jsx
74:86:Bookology-frontend/src/components/EnhancedStoryCard.jsx
+            loading="lazy"
+            decoding="async"
+            fetchpriority="low"
```

```startLine:endLine:Bookology-frontend/src/components/explore/HeroCarousel.tsx
26:37:Bookology-frontend/src/components/explore/HeroCarousel.tsx
+                decoding="async"
+                fetchpriority="high"
```

```startLine:endLine:Bookology-frontend/index.html
4:12:Bookology-frontend/index.html
+    <meta name="description" content="Bookology: Generate, edit, and share AI‑crafted stories with cinematic covers." />
+    <meta name="theme-color" content="#000000" />
+    <meta name="robots" content="index,follow" />
```
