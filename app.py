from .bot import run_bot


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    bot = run_bot()
    return [str(env), str(start_response), bot.owner_id]
