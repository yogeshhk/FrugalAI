"""Command line. Run from code/voice-form: python -m voiceform <command> --help

download        one-time model download (the only step that needs internet)
sheet           write eval/RECORDING.md, the lines to record
import FOLDER   convert your recordings to eval/audio/
smoke-audio     machine-voice audio for every line (plumbing check only)
transcribe      one audio file to text
fill            one utterance (text or audio) to a filled form, printed
eval-asr        speech-to-text accuracy and speed over the recordings (or the smoke audio)
eval-extract    field accuracy of one route and model, on the script text or on saved transcripts
report          results/RESULTS.md from all runs
"""

import argparse
import json
import sys


def _llm(model):
    from .llm import LLM

    llm = LLM(model)
    if not llm.available():
        sys.exit(f"LM Studio is not serving {model!r} at {llm.url}; start it and load the model first")
    return llm


def main(argv=None) -> None:
    from . import config

    # Windows consoles default to cp1252, which cannot print Devanagari; never crash on output.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(prog="voiceform", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download")
    d.add_argument("--only", nargs="*", help="names from config.ASR_MODELS, or 'tts'")
    d.add_argument("--no-tts", action="store_true")

    sub.add_parser("sheet")
    im = sub.add_parser("import")
    im.add_argument("folder")

    sm = sub.add_parser("smoke-audio")
    sm.add_argument("--lang", nargs="*", default=["mr", "hi"])

    t = sub.add_parser("transcribe")
    t.add_argument("audio")
    t.add_argument("--lang", required=True, choices=["mr", "hi"])
    t.add_argument("--asr", default=None, help="backend name; default: the first one for the language")

    f = sub.add_parser("fill")
    f.add_argument("--form", required=True)
    f.add_argument("--lang", required=True, choices=["mr", "hi", "en"])
    g = f.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--audio")
    f.add_argument("--asr", default=None)
    f.add_argument("--route", default="direct", choices=["rules", "direct", "translate"])
    f.add_argument("--model", default=config.DEFAULT_LLM)

    ea = sub.add_parser("eval-asr")
    ea.add_argument("--lang", required=True, choices=["mr", "hi"])
    ea.add_argument("--asr", required=True)
    ea.add_argument("--source", default="recordings", choices=["recordings", "smoke"])
    ea.add_argument("--noisy", action="store_true")
    ea.add_argument("--limit", type=int)

    ex = sub.add_parser("eval-extract")
    ex.add_argument("--lang", required=True, choices=["mr", "hi"])
    ex.add_argument("--route", required=True, choices=["rules", "direct", "translate"])
    ex.add_argument("--model", default=config.DEFAULT_LLM)
    ex.add_argument("--transcripts", help="a run name from eval-asr, for example asr_mr_whisper-small-mr_recordings")
    ex.add_argument("--set", nargs="*", default=["tune", "heldout"])
    ex.add_argument("--limit", type=int)

    sub.add_parser("report")
    args = ap.parse_args(argv)

    if args.cmd == "download":
        from . import download

        download.run(only=args.only, with_tts=not args.no_tts)
    elif args.cmd == "sheet":
        from . import recording

        print(recording.write_sheet())
    elif args.cmd == "import":
        from . import recording

        for p in recording.import_folder(args.folder):
            print(p)
    elif args.cmd == "smoke-audio":
        from . import smoke

        for lang in args.lang:
            print(lang, len(smoke.make(lang)), "files in", config.SMOKE_AUDIO_DIR)
    elif args.cmd == "transcribe":
        from . import audio
        from .asr import backends_for, get_backend

        name = args.asr or backends_for(args.lang)[0]
        res = get_backend(name).transcribe(audio.load(args.audio), args.lang)
        print(json.dumps({"text": res.text, "backend": res.backend, "seconds": res.seconds, "rtf": res.rtf},
                         ensure_ascii=False, indent=2))
    elif args.cmd == "fill":
        from . import audio, pipeline
        from .asr import backends_for, get_backend
        from .evaluate import settings
        from .schema import load_forms

        form = load_forms()[args.form]
        llm = None if args.route == "rules" else _llm(args.model)
        wav = asr = None
        if args.audio:
            asr = get_backend(args.asr or backends_for(args.lang)[0])
            wav = audio.load(args.audio)
        turn = pipeline.run(form, args.lang, wav=wav, text=args.text, asr=asr, route=args.route, llm=llm,
                            today=settings()["today"])
        print("Transcript:", turn.transcript)
        for name, fv in turn.record.fields.items():
            print(f"  {fv.status:<9} {name:<20} {fv.value!s:<24} {fv.note}")
        print("English request:", turn.english)
        for q in turn.questions:
            print("Ask:", q)
        print(f"Connections: {turn.local_connections} to this machine, {turn.blocked_connections} blocked")
        print("Timings:", json.dumps(turn.timings))
    elif args.cmd == "eval-asr":
        from .evaluate import eval_asr

        out = eval_asr(args.lang, args.asr, source=args.source, noisy=args.noisy, limit=args.limit)
        print(json.dumps(out["summary"], indent=2), "\nRAM (MB):", out["meta"]["ram_after_load_mb"])
    elif args.cmd == "eval-extract":
        from .evaluate import eval_extract

        llm = None if args.route == "rules" else _llm(args.model)
        out = eval_extract(args.lang, args.route, llm=llm, transcripts=args.transcripts, sets=tuple(args.set),
                           limit=args.limit, condition="asr" if args.transcripts else "reference")
        print(json.dumps(out["summary"], indent=2))
    elif args.cmd == "report":
        from .evaluate import report

        print(report())


if __name__ == "__main__":
    main()
