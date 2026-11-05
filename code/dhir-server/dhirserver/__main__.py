"""Start the server:  conda run -n genai python -m dhirserver --model-dir <folder> --port 1235"""

import argparse

from .model import default_model_dir


def main():
    ap = argparse.ArgumentParser(description="Serve Dhir 2B through an OpenAI-style local API")
    ap.add_argument("--model-dir", default=default_model_dir(), help="folder with the Hugging Face files (or DHIR_MODEL_DIR)")
    ap.add_argument("--port", type=int, default=1235)
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp32", "int8"])
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument(
        "--upstream",
        default="http://localhost:1234/v1",
        help="LM Studio URL for embeddings and other models; use 'none' to serve Dhir alone",
    )
    args = ap.parse_args()
    upstream = None if args.upstream.lower() == "none" else args.upstream
    if not args.model_dir:
        raise SystemExit("Pass --model-dir or set DHIR_MODEL_DIR")

    import uvicorn

    from .app import create_app
    from .model import DhirModel, MODEL_ID

    model = DhirModel(args.model_dir, dtype=args.dtype, threads=args.threads)
    print("loaded in %.1f s (%s). Serving %s on http://127.0.0.1:%d/v1 (upstream: %s)"
          % (model.load_s, args.dtype, MODEL_ID, args.port, upstream))
    uvicorn.run(create_app(model, MODEL_ID, upstream), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
