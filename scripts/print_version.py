try:
    import json
    from importlib.metadata import version

    print(json.dumps({"version": version("ethyca-fides")}))
except Exception:
    import json

    print(json.dumps({"version": "unknown"}))
