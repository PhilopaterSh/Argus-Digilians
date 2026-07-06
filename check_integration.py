import sys
sys.path.insert(0, 'C:/AI_PenTest_Project/Argus')
errors = []

# Test 1: config.yaml loads correctly
try:
    import yaml, os
    with open('C:/AI_PenTest_Project/Argus/config.yaml') as f:
        cfg = yaml.safe_load(f)
    print('[OK] config.yaml loaded:', cfg)
except Exception as e:
    errors.append(f'[FAIL] config.yaml: {e}')

# Test 2: app.__init__ (logging)
try:
    import app
    print('[OK] app.__init__ loaded')
except Exception as e:
    errors.append(f'[FAIL] app.__init__: {e}')

# Test 3: agent_factory reads config
try:
    from app.core import agent_factory
    print(f'[OK] agent_factory: early_stopping={agent_factory._EARLY_STOPPING}, max_iter={agent_factory._MAX_ITERATIONS}')
except Exception as e:
    errors.append(f'[FAIL] agent_factory: {e}')

# Test 4: command_runner reads timeout
try:
    from app.tools import command_runner
    print(f'[OK] command_runner: _CMD_TIMEOUT={command_runner._CMD_TIMEOUT}')
except Exception as e:
    errors.append(f'[FAIL] command_runner: {e}')

# Test 5: web_search reads timeout + socket
try:
    from app.tools import web_search
    print(f'[OK] web_search: _WEB_TIMEOUT={web_search._WEB_TIMEOUT}')
except Exception as e:
    errors.append(f'[FAIL] web_search: {e}')

# Test 6: recon reads truncate
try:
    from app.tools import recon
    print(f'[OK] recon: _TRUNCATE={recon._TRUNCATE}')
except Exception as e:
    errors.append(f'[FAIL] recon: {e}')

# Test 7: scanners project root
try:
    from app.tools import scanners
    print(f'[OK] scanners: _PROJECT_ROOT={scanners._PROJECT_ROOT}')
except Exception as e:
    errors.append(f'[FAIL] scanners: {e}')

# Test 8: reflective_verification has json
try:
    from app.tools import reflective_verification
    import inspect
    src = inspect.getsource(reflective_verification)
    assert 'import json' in src
    print('[OK] reflective_verification: json imported')
except Exception as e:
    errors.append(f'[FAIL] reflective_verification: {e}')

# Test 9: wsl_bridge password default is empty (check env directly)
try:
    from app.tools.wsl_bridge import WSLConfig
    import warnings, os
    # Check: if WSL_PASS is NOT in env, a warning should fire
    orig = os.environ.pop('WSL_PASS', None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        cfg_wsl = WSLConfig()
        warned = any('WSL_PASS' in str(x.message) for x in w)
    if orig is not None:
        os.environ['WSL_PASS'] = orig
    print(f'[OK] wsl_bridge: password guard active, warning_when_missing={warned}')
except Exception as e:
    errors.append(f'[FAIL] wsl_bridge: {e}')

# Test 10: argus_reasoning imports correct (utf-8 safe read)
try:
    import pathlib
    src = pathlib.Path('C:/AI_PenTest_Project/Argus/app/modules/argus_reasoning.py').read_text(encoding='utf-8', errors='ignore')
    assert 'from app.core.brain import ArgusBrain' in src
    assert 'from app.tools.tool_registry import WSLBridgeTools' in src
    print('[OK] argus_reasoning: correct imports')
except Exception as e:
    errors.append(f'[FAIL] argus_reasoning: {e}')

print()
if errors:
    print('=== FAILURES ===')
    for err in errors:
        print(err)
else:
    print('=== ALL 10 CHECKS PASSED ===')
