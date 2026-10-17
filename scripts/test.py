#!/usr/bin/env python3
"""Behavior contract, used against source or an isolated installed entrypoint."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def contract(command):
    passed=[]
    with tempfile.TemporaryDirectory(prefix='nuvo-contract-') as directory:
        root=Path(directory)
        env={k:v for k,v in os.environ.items() if not k.startswith('NUVO_')}
        def check(name,args,code,extra=None,expected=None,stderr=None):
            result=subprocess.run([*command,*args],env={**env,**(extra or {})},capture_output=True,text=True,timeout=120)
            assert result.returncode==code,(name,result.returncode,result.stdout,result.stderr)
            if expected is not None:
                for key,value in expected.items():assert json.loads(result.stdout).get(key)==value,(name,result.stdout)
            if stderr:
                assert result.stdout=='',(name,result.stdout)
                assert json.loads(result.stderr)['code']==stderr,(name,result.stderr)
            passed.append(name)
            return result
        result=check('version',['--version'],0,{'NUVO_CONFIG':str(root/'nonexistent')})
        assert result.stdout=='nuvo 0.1.0\n' and result.stderr==''
        check('unconfigured',['doctor'],2,stderr='NUVO_UNCONFIGURED')
        check('provider',['doctor'],0,{'NUVO_PROVIDER':'chosen'},expected={'status':'configured','provider':'chosen','cortex_endpoint':None,'check':'configuration_only'})
        check('endpoint-without-connection',['doctor'],0,{'NUVO_CORTEX_ENDPOINT':'http://127.0.0.1:1/cortex'},expected={'provider':None,'cortex_endpoint':'http://127.0.0.1:1/cortex'})
        config=root/'config';config.write_text('# explicit\nprovider=file\ncortex_endpoint=https://cortex.example.invalid/api\n')
        check('file',['doctor'],0,{'NUVO_CONFIG':str(config)},expected={'provider':'file','cortex_endpoint':'https://cortex.example.invalid/api'})
        check('precedence',['doctor'],0,{'NUVO_CONFIG':str(config),'NUVO_PROVIDER':'override','NUVO_CORTEX_ENDPOINT':''},expected={'provider':'override','cortex_endpoint':None})
        check('clear-both',['doctor'],2,{'NUVO_CONFIG':str(config),'NUVO_PROVIDER':'','NUVO_CORTEX_ENDPOINT':''},stderr='NUVO_UNCONFIGURED')
        check('missing-file',['doctor'],2,{'NUVO_CONFIG':str(root/'missing'),'NUVO_PROVIDER':'chosen'},stderr='NUVO_CONFIGURATION_READ')
        check('empty-path',['doctor'],2,{'NUVO_CONFIG':''},stderr='NUVO_INVALID_CONFIGURATION')
        for name,text in [('duplicate','provider=a\nprovider=b'),('unknown','api_key=secret-value'),('syntax','provider'),('invalid-utf8',None)]:
            if text is None:config.write_bytes(b'\xff')
            else:config.write_text(text)
            result=check(name,['doctor'],2,{'NUVO_CONFIG':str(config)},stderr='NUVO_CONFIGURATION_READ' if text is None else 'NUVO_INVALID_CONFIGURATION')
            assert 'secret-value' not in result.stderr
        for name,endpoint in [('credentials','https://user:secret-value@host'),('query','https://host?token=secret-value'),('scheme','file:///secret-value')]:
            result=check(name,['doctor'],2,{'NUVO_CORTEX_ENDPOINT':endpoint},stderr='NUVO_INVALID_CONFIGURATION')
            assert 'secret-value' not in result.stderr
        check('usage',['not-a-command'],2,stderr='NUVO_USAGE')
        check('extra-argument',['doctor','extra'],2,stderr='NUVO_USAGE')
        result=check('help',['--help'],0);assert 'configuration only' in result.stdout
    return passed

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();print(json.dumps({'passed':contract(args.command)}))
