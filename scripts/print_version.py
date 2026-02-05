try:
    from importlib.metadata import version
    import json
    print(json.dumps({'version': version('ethyca-fides')}))
except Exception:
    import json
    print(json.dumps({'version': 'unknown'}))
