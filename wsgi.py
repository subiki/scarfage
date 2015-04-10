def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return ['<!DOCTYPE html><html><meta charset="utf-8"><title>It works',
            "</title><b>It works!</b><br /><br />Fuck yea! "]
