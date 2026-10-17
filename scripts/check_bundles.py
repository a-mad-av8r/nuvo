#!/usr/bin/env python3
"""Detect drift in generated bundles, public READMEs, and defensive aliases."""
import json
from pathlib import Path
import tomllib
from prepare import ROOT, PARAGRAPH

def check():
    assertions=0
    for destination in [ROOT/'packaging/npm/nuvo/native', ROOT/'packaging/pypi/nuvo/nuvo/native']:
        expected={Path(name)/filename for name in ['nuvo-core','nuvo-cli'] for filename in ['Cargo.toml','Cargo.lock','README.md','LICENSE','src/lib.rs' if name=='nuvo-core' else 'src/main.rs']}
        assert {p.relative_to(destination) for p in destination.rglob('*') if p.is_file()}==expected,destination
        assertions+=1
        for file in destination.rglob('*'):
            if file.is_file():
                assert file.read_bytes()==(ROOT/'packaging/crates'/file.relative_to(destination)).read_bytes(),file
                assertions+=1
    for file in ROOT.rglob('README.md'):
        if any(p in {'target','build','__pycache__'} or p.endswith('.egg-info') for p in file.parts):continue
        assert PARAGRAPH in file.read_text(),file
        assertions+=1
    for registry in ['npm','pypi']:
        for name in ['nuvo','nuvo-ai','nuvo-cli']:
            path=ROOT/'packaging'/registry/name
            meta=json.loads((path/'package.json').read_text()) if registry=='npm' else tomllib.loads((path/'pyproject.toml').read_text())['project']
            assert meta['version']=='0.1.0' and PARAGRAPH in (path/'README.md').read_text()
            assertions+=1
    for name in ['nuvo-ai','nuvo-cli']:
        meta=json.loads((ROOT/'packaging/npm'/name/'package.json').read_text())
        assert meta['dependencies']=={'nuvo':'0.1.0'} and 'bin' not in meta and 'scripts' not in meta
        assert meta['files']==['README.md','LICENSE']
        py=tomllib.loads((ROOT/'packaging/pypi'/name/'pyproject.toml').read_text())
        assert py['project']['dependencies']==['nuvo==0.1.0'] and py['tool']['setuptools']['packages']==[]
        assertions+=2
    for file in (ROOT/'packaging/crates').glob('*/Cargo.toml'):
        meta=tomllib.loads(file.read_text());assert meta['package']['version']=='0.1.0'
        assert not meta.get('build-dependencies') and not meta.get('dev-dependencies')
        assert set(meta.get('dependencies',{})) <= {'nuvo-core'}
        assertions+=1
    print(json.dumps({'bundle_metadata_assertions':assertions,'result':'passed'}))
    return assertions

if __name__=='__main__':check()
