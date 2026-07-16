# Dockerfile for ARIA's Web App (flask_app/). Build from the PROJECT ROOT,
# not from inside flask_app/, since the image needs both aria_core/ (the
# shared package) and flask_app/ — same reason app.py appends the project
# root to sys.path at runtime (see the comment near the top of app.py).
#
#   docker build -t aria-web .
#   docker run -p 5000:5000 -e GROQ_API_KEY=your_key_here aria-web
#
# CLI/GUI aren't included here on purpose — they're desktop apps that want
# a real display and microphone, which doesn't map cleanly onto a
# container. This image is for the Web App only.

FROM python:3.11-slim

# build-essential: some of chromadb's/sentence-transformers' own
# dependencies may need a C compiler if a prebuilt wheel isn't available
# for this platform. curl: used by the HEALTHCHECK below.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the shared package first — it changes far less often than flask_app/
# during normal development, so keeping it in its own layer means Docker's
# build cache doesn't get invalidated by every flask_app/ edit.
COPY aria_core/ ./aria_core/

# Lean vs full image: pass --build-arg REQUIREMENTS_FILE=requirements-deploy.txt
# to skip chromadb/sentence-transformers/torch entirely (RAG disabled at
# runtime via ENABLE_RAG=false) — the same tradeoff documented in the
# Deployment section of the README, now expressed as a build option instead
# of being tied to one specific hosting provider's dashboard.
ARG REQUIREMENTS_FILE=requirements.txt
COPY flask_app/requirements.txt flask_app/requirements-deploy.txt ./flask_app/

# sentence-transformers pulls in torch, and a plain `pip install` for torch
# often resolves to the CUDA/GPU build by default (multiple GB) even though
# this container never touches a GPU. Installing the CPU-only build first
# (only when building the full/RAG image) heads that off — it's a few
# hundred MB instead. Skipped entirely for the lean build, which doesn't
# need torch at all.
RUN if [ "$REQUIREMENTS_FILE" = "requirements.txt" ]; then \
        pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; \
    fi
RUN pip install --no-cache-dir -r flask_app/${REQUIREMENTS_FILE}

# Pre-download the embedding model at BUILD time, not runtime. Without this,
# the model downloads lazily on the container's first real chat request —
# which can take longer than gunicorn's default 30s worker timeout, killing
# the worker before the download even finishes (repeatedly, since each new
# worker retries the same slow download). Baking the weights into the image
# means the container never needs network access for this at all.
RUN if [ "$REQUIREMENTS_FILE" = "requirements.txt" ]; then \
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; \
    fi

COPY flask_app/ ./flask_app/

WORKDIR /app/flask_app

# Most hosting platforms (Render, Railway, Koyeb, ...) inject their own PORT
# at runtime; 5000 is just the default for local `docker run`/compose use.
ENV PORT=5000
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f "http://localhost:${PORT}/" || exit 1

# Shell form (not exec form / JSON array) is deliberate here: it's the only
# way for ${PORT} to be substituted from the container's actual runtime
# environment variable rather than baked in at build time.
# --timeout 60 (up from gunicorn's default 30s): a defensive margin for the
# first request after a cold start, since loading the (now pre-baked, but
# still non-trivial) embedding model from disk into memory isn't instant.
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --timeout 60