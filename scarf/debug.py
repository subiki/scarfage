import jsonpickle, json

def dbg(o):
    jstr = jsonpickle.encode(o)
    jstr = json.dumps(json.loads(jstr), sort_keys=True, indent=4, separators=(',', ': '))
    o.json = jstr

    return jstr
