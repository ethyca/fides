try:
    from importlib.metadata import version
    import json
    print(json.dumps({'version': version('ethyca_fides')}))
except Exception:
    import json
    print(json.dumps({'version': 'unknown'}))
