"""Generate SDK type declarations from the pinned OpenAPI snapshot (stdlib only)."""
import argparse
import json
from pathlib import Path


def generate(schema, language):
    schemas = schema['components']['schemas']
    def merged(s):
        if '$ref' in s:
            return merged(schemas[s['$ref'].split('/')[-1]])
        if 'allOf' in s:
            result = {'type': 'object', 'properties': {}, 'required': []}
            for part in s['allOf']:
                part = merged(part)
                result['properties'].update(part.get('properties', {}))
                result['required'].extend(part.get('required', []))
            return result
        return s
    def typ(s):
        if '$ref' in s:
            return s['$ref'].split('/')[-1]
        if 'anyOf' in s:
            return ' | '.join(typ(x) for x in s['anyOf'])
        values = s.get('enum', [s['const']] if 'const' in s else None)
        if values is not None:
            if language == 'python':
                return 'Literal[' + ', '.join(repr(v) for v in values) + ']'
            return ' | '.join(json.dumps(v) for v in values)
        t = s.get('type')
        if isinstance(t, list):
            return ' | '.join(typ({**s, 'type': x}) for x in t)
        if t == 'array':
            inner = typ(s.get('items', {}))
            return f'list[{inner}]' if language == 'python' else f'Array<{inner}>'
        if t == 'object':
            return 'dict[str, Any]' if language == 'python' else 'Record<string, unknown>'
        return ({'string':'str','integer':'int','number':'float','boolean':'bool','null':'None'}.get(t, 'Any')
                if language == 'python' else {'string':'string','integer':'number','number':'number','boolean':'boolean','null':'null'}.get(t, 'unknown'))
    lines = (['# Generated from contract/openapi.json; do not edit.', 'from typing import Any, Literal, NotRequired, TypedDict', '']
             if language == 'python' else ['// Generated from contract/openapi.json; do not edit.', ''])
    for name, original in schemas.items():
        s = merged(original)
        props = s.get('properties', {})
        if language == 'python':
            lines.append(f'class {name}(TypedDict):')
            if not props:
                lines.append('    pass')
            for field, definition in props.items():
                value = typ(definition)
                if field not in s.get('required', []):
                    value = f'NotRequired[{value}]'
                lines.append(f'    {field}: {value}')
        else:
            lines.append(f'export interface {name} {{')
            for field, definition in props.items():
                optional = '' if field in s.get('required', []) else '?'
                lines.append(f'  {field}{optional}: {typ(definition)};')
            lines.append('}')
        lines.append('')
    return '\n'.join(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=['python','typescript'], required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / ('src/trustables/types.py' if args.language == 'python' else 'src/types.ts')
    content = generate(json.loads((root/'contract/openapi.json').read_text()), args.language)
    if args.check:
        if target.read_text() != content:
            raise SystemExit('Generated types are stale; run tools/generate_types.py')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
