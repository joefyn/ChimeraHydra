import argparse, json, os
from datetime import datetime, timezone
def _ts(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def _ensure_dir(p): os.makedirs(p, exist_ok=True)
def run_intent(args):
    ts=_ts(); run_id=args.run_id or ts
    out_dir=os.path.join('artifacts', ts, run_id); _ensure_dir(out_dir)
    doc={'run_id':run_id,'goal':args.goal,'DoD':args.dod or '','constraints':args.constraint or [],'risks':args.risk or [],'glossary_keys':args.glossary or []}
    out_path=os.path.join(out_dir,'prompt.audit.json')
    with open(out_path,'w',encoding='utf-8') as f: json.dump(doc,f,indent=2,ensure_ascii=False)
    print(out_path); return 0
def main():
    parser=argparse.ArgumentParser(prog='chimera',description='Chimera CLI')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p_intent=sub.add_parser('intent',help='Emit prompt.audit.json for the given goal')
    p_intent.add_argument('goal')
    p_intent.add_argument('--dod')
    p_intent.add_argument('--constraint',action='append')
    p_intent.add_argument('--risk',action='append')
    p_intent.add_argument('--glossary',action='append')
    p_intent.add_argument('--run-id',dest='run_id')
    p_intent.set_defaults(func=run_intent)
    args=parser.parse_args(); return args.func(args)
if **name**=='**main**':
    raise SystemExit(main())
